#!/usr/bin/env python3
"""Build/test opt-in portable Mellow objects and supported MSL/AIR-text compute.

No Apple Objective-C Metal ABI is implemented by this executable. It uses the
actual native OpenCL provider and compares GPU output in the test, independently
of normal runtime execution (which requires no supplied expected answer).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import struct
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_streams(seed, count):
    inputs, expected = hashlib.sha256(), hashlib.sha256()
    for iteration in range(count):
        values = [(seed ^ ((i + iteration * 263) * 0x9E3779B9)) & 0xFFFF for i in range(256)]
        inputs.update(struct.pack("<256I", *values))
        expected.update(struct.pack("<256I", *[value * 7 + 3 for value in values]))
    return inputs.hexdigest(), expected.hexdigest()

def load_strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def validate_native_result(native, seed, count, input_kind, entry):
    """Consistency/oracle checks of current native worker data, not attestation."""
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    def integer(value, minimum=0):
        return type(value) is int and minimum <= value <= 0xFFFFFFFFFFFFFFFF
    def event(value, sequence, oracle=False, previous_end=0):
        if type(value) is not dict:
            errors.append("Missing event object")
            return 0
        for key in ("submission_attempted", "submitted", "execution_completed",
                    "event_ownership_verified", "profiling_verified", "resources_released"):
            need(value.get(key) is True, "Event " + key + " must be true")
        need(value.get("runtime_planned") is (not oracle), "Event planning scope mismatch")
        need(value.get("results_verified") is oracle, "Event oracle evidence mismatch")
        need(value.get("runtime_completion_accepted") is False, "Unexpected evidence-mode completion")
        need(type(value.get("epoch")) is int and value["epoch"] == 1, "Event epoch must match bootstrap")
        need(type(value.get("sequence")) is int and value["sequence"] == sequence, "Event sequence mismatch")
        start, end = value.get("gpu_start"), value.get("gpu_end")
        if integer(start, 1) and integer(end, 1):
            need(end > start and start >= previous_end, "Event timestamp order mismatch")
            return end
        errors.append("Invalid event timestamps")
        return 0
    if type(native) is not dict:
        return ["Native result must be an object"]
    for key in ("passed", "portable_mellow_object_api", "native_driver_pipeline_compiled_once",
                "ordered_two_encoder_result_verified", "all_dispatches_correlated", "all_dispatches_no_oracle"):
        need(native.get(key) is True, key + " must be true")
    for key in ("apple_metal_abi_registered", "system_mtl_device_registered", "macos_tested",
                "physical_pci_identity_verified", "runtime_requires_expected_answer"):
        need(native.get(key) is False, key + " must be false for this test")
    for key, expected in (("schema_version", 1), ("seed", seed), ("requested_iterations", count),
                          ("verified_iterations", count), ("pipeline_build_count", 1),
                          ("first_sequence", 2), ("last_sequence", count + 1), ("epoch", 1),
                          ("negative_checks", 13)):
        need(type(native.get(key)) is int and native[key] == expected, key + " mismatch")
    need(integer(native.get("checks"), count * 16 + 40), "Insufficient test checks")
    need(native.get("source_kind") == input_kind and native.get("entry") == entry, "Input identity mismatch")
    inputs, expected = expected_streams(seed, count)
    for key, value in (("input_stream_sha256", inputs), ("expected_stream_sha256", expected),
                       ("readback_stream_sha256", expected)):
        need(native.get(key) == value, key + " mismatch")
    previous_end = event(native.get("bootstrap"), 1, oracle=True)
    samples = native.get("samples")
    indices = [0] if count == 1 else [0, count - 1]
    if type(samples) is not list or len(samples) != len(indices):
        errors.append("Missing bounded first/last samples")
    else:
        for sample, iteration in zip(samples, indices):
            if type(sample) is not dict:
                errors.append("Malformed sample")
                continue
            need(type(sample.get("iteration")) is int and sample["iteration"] == iteration, "Sample iteration mismatch")
            values = [(seed ^ ((i + iteration * 263) * 0x9E3779B9)) & 0xFFFF for i in range(256)]
            for key, expected_values in (("input", values), ("output", [value * 7 + 3 for value in values])):
                actual = sample.get(key)
                need(type(actual) is list and len(actual) == 256 and
                     all(type(value) is int for value in actual) and actual == expected_values, "Sample " + key + " mismatch")
            previous_end = event(sample.get("event"), iteration + 2, previous_end=previous_end)
    ordered = native.get("ordered_events")
    if type(ordered) is not list or len(ordered) != 2:
        errors.append("Missing ordered encoder events")
    else:
        for i, value in enumerate(ordered):
            previous_end = event(value, count + 2 + i, previous_end=previous_end)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compute", action="store_true")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=60)
    shader_input = parser.add_mutually_exclusive_group()
    shader_input.add_argument("--air-text", type=Path, help="AIR LLVM text; origin is not authenticated")
    shader_input.add_argument("--air-bitcode", type=Path, help="AIR-shaped bitcode decoded by actual LLVM library")
    parser.add_argument("--llvm-library", type=Path, help="Explicit trusted LLVM C API library, never auto-installed")
    parser.add_argument("--fixture-origin", choices=("synthetic", "unattested"), default="unattested",
                        help="Caller-labelled provenance, never proof of Apple compiler output")
    parser.add_argument("--entry", default="mellow_objects")
    args = parser.parse_args()
    if not args.cxx:
        parser.error("Native C++17 compiler required")
    if not 1 <= args.iterations <= 10000 or not 1 <= args.timeout <= 180:
        parser.error("iterations must be 1-10000 and timeout 1-180 seconds")
    fixture = args.air_text or args.air_bitcode
    if fixture and not fixture.is_file():
        parser.error("AIR fixture file does not exist")
    if args.air_bitcode and (not args.llvm_library or not args.llvm_library.is_file()):
        parser.error("--air-bitcode requires an existing --llvm-library")
    input_kind = "air-bitcode" if args.air_bitcode else ("air-text" if args.air_text else "msl")
    root = Path(__file__).resolve().parents[1]
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    executable = args.out / ("metal-objects.exe" if os.name == "nt" else "metal-objects")
    sources = ["Runtime/PlatformRuntime.hpp", "Runtime/PlatformRuntime.cpp", "Runtime/OpenCLAbi.hpp",
               "Runtime/OpenCLProvider.hpp", "Runtime/OpenCLProvider.cpp", "Runtime/MetalObjects.hpp",
               "Runtime/MetalObjects.cpp", "Runtime/ShaderJit.hpp", "Runtime/ShaderJit.cpp",
               "Runtime/AirDecoder.hpp", "Runtime/AirDecoder.cpp",
               "tests/metal_objects_tests.cpp", "tests/opencl_runtime_sha256.hpp", "Tools/run-metal-objects.py"]
    report = {
        "schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "portable-Mellow-object-API-translated-subset-native-OpenCL-GPU",
        "os": {"system": platform.system(), "release": platform.release(), "version": platform.version(), "machine": platform.machine()},
        "source_sha256": {name: digest(root / name) for name in sources},
        "apple_metal_abi_registered": False, "system_mtl_device_registered": False,
        "native_macos_execution": False, "gpu_work_executed": False,
        "passed": False, "status": "FAILED", "requested_iterations": args.iterations,
    }
    input_pins = {}
    if fixture:
        input_pins["fixture"] = {"path": str(fixture.resolve()), "sha256": digest(fixture)}
        report["fixture_origin"] = args.fixture_origin
        report["fixture_origin_is_caller_label"] = True
    if args.air_bitcode:
        input_pins["llvm_library"] = {"path": str(args.llvm_library.resolve()), "sha256": digest(args.llvm_library)}
    report["input_pins"] = input_pins
    report["source_kind"] = input_kind
    report["apple_compiler_output_verified"] = False
    child_env = os.environ.copy()
    options = {"env": child_env}
    if os.name == "nt":
        compiler = Path(shutil.which(args.cxx) or args.cxx).resolve()
        child_env["PATH"] = str(compiler.parent) + os.pathsep + child_env.get("PATH", "")
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    worker_started = False
    try:
        version = subprocess.run([args.cxx, "--version"], capture_output=True, text=True, timeout=20, **options)
        report["compiler_version"] = version.stdout.strip()
        units = ["Runtime/PlatformRuntime.cpp", "Runtime/OpenCLProvider.cpp", "Runtime/ShaderJit.cpp",
                 "Runtime/AirDecoder.cpp", "Runtime/MetalObjects.cpp", "tests/metal_objects_tests.cpp"]
        command = [args.cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   *[str(root / source) for source in units], "-o", str(executable)]
        if os.name == "nt":
            command.extend(["-static-libgcc", "-static-libstdc++"])
        elif sys.platform != "darwin":
            command.append("-ldl")
        build = subprocess.run(command, capture_output=True, text=True, timeout=120, **options)
        report["build"] = {"exit_code": build.returncode, "stdout": build.stdout, "stderr": build.stderr}
        if build.returncode:
            print(build.stdout + build.stderr, file=sys.stderr)
            return 1
        report["binary_sha256"] = digest(executable)
        if not args.compute:
            report["status"] = "BUILT_ONLY"
            return 0
        run_path = args.out / ("native-" + secrets.token_hex(8) + ".json")
        seed = secrets.randbits(32)
        invocation = [str(executable), "--compute", "--report", str(run_path), "--seed", str(seed),
                      "--iterations", str(args.iterations), "--entry", args.entry]
        if args.air_text:
            invocation.extend(["--air-text", str(args.air_text.resolve())])
        elif args.air_bitcode:
            invocation.extend(["--air-bitcode", str(args.air_bitcode.resolve()), "--llvm-library", str(args.llvm_library.resolve())])
        worker_started = True
        worker = subprocess.run(invocation, capture_output=True, text=True, timeout=args.timeout, **options)
        report["worker"] = {"exit_code": worker.returncode, "stdout": worker.stdout, "stderr": worker.stderr}
        print(worker.stdout, end="")
        if not run_path.exists():
            report["gpu_work_executed"] = None
            report["error"] = "Worker produced no current result"
            return 1
        native = load_strict_json(run_path.read_text(encoding="utf-8"))
        if type(native) is not dict:
            raise ValueError("Native result must be a JSON object")
        run_path.replace(args.out / "metal-objects-native.json")
        report["native"] = native
        report["gpu_work_executed"] = True if type(native.get("verified_iterations")) is int and native["verified_iterations"] > 0 else None
        inputs, expected = expected_streams(seed, args.iterations)
        report["independent_reference"] = {"input_sha256": inputs, "expected_readback_sha256": expected}
        report["validation_errors"] = validate_native_result(native, seed, args.iterations, input_kind, args.entry)
        report["source_changed_during_run"] = [name for name in sources if digest(root / name) != report["source_sha256"][name]]
        report["inputs_changed_during_run"] = [name for name, pin in input_pins.items() if digest(Path(pin["path"])) != pin["sha256"]]
        passed = (worker.returncode == 0 and not report["validation_errors"] and
                  not report["source_changed_during_run"] and not report["inputs_changed_during_run"])
        report["passed"] = passed
        report["status"] = "PASS_PORTABLE_OBJECTS_SHADER_GPU_SUBSET" if passed else "FAILED"
        return 0 if passed else 1
    except subprocess.TimeoutExpired as error:
        report.update(status="TIMED_OUT", error=f"Worker/compiler deadline {error.timeout} seconds exceeded",
                      gpu_work_executed=None if worker_started else False)
        return 1
    except (OSError, ValueError, KeyError) as error:
        report["error"] = str(error)
        if worker_started and "native" not in report:
            report["gpu_work_executed"] = None
        return 1
    finally:
        report["source_changed_during_run"] = [
            name for name in sources if not (root / name).is_file() or digest(root / name) != report["source_sha256"][name]]
        report["inputs_changed_during_run"] = [
            name for name, pin in input_pins.items() if not Path(pin["path"]).is_file() or digest(Path(pin["path"])) != pin["sha256"]]
        if report["source_changed_during_run"] or report["inputs_changed_during_run"]:
            report["passed"] = False
            report["status"] = "FAILED_INPUT_OR_SOURCE_CHANGED"
        destination = args.out / "metal-objects.json"
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("Report:", destination)


if __name__ == "__main__":
    raise SystemExit(main())
