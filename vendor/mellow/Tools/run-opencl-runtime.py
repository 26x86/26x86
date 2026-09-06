#!/usr/bin/env python3
"""Build the native Mellow OpenCL provider and optionally test its real GPU path.

OpenCL C input only. No Metal/JIT, Linux driver port or macOS support is inferred
from a Windows host test. All native GPU operations run in a deadline worker.
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


def words_digest(values):
    return hashlib.sha256(struct.pack(f"<{len(values)}I", *values)).hexdigest()


def reference_streams(seed, iterations):
    inputs, expected = hashlib.sha256(), hashlib.sha256()
    for iteration in range(iterations):
        values = [(seed ^ ((index + iteration * 263) * 0x9E3779B9)) & 0xFFFF for index in range(256)]
        inputs.update(struct.pack("<256I", *values))
        expected.update(struct.pack("<256I", *[value * 7 + 3 for value in values]))
    return inputs.hexdigest(), expected.hexdigest()


def last_checkpoint(run_path, iterations):
    if run_path is None:
        return None
    valid = []
    for suffix in (".checkpoint-a.json", ".checkpoint-b.json"):
        try:
            candidate = json.loads(Path(str(run_path) + suffix).read_text(encoding="utf-8"))
            if (candidate.get("passed") is False and candidate.get("complete") is False and
                    candidate.get("requested_iterations") == iterations and
                    isinstance(candidate.get("verified_iterations"), int) and
                    isinstance(candidate.get("seed"), int) and 0 <= candidate["seed"] <= 0xFFFFFFFF and
                    0 <= candidate["verified_iterations"] <= iterations):
                valid.append(candidate)
        except (OSError, ValueError):
            pass
    return max(valid, key=lambda value: value["verified_iterations"]) if valid else None


def validate_native_result(native, worker_exit, iterations):
    """Validate correlated samples/summary and recompute every reference input."""
    reasons = []
    independent = {}

    def require(condition, message):
        if not condition:
            reasons.append(message)

    def integer(value, lower=0):
        return type(value) is int and value >= lower

    try:
        require(worker_exit == 0 and native.get("passed") is True and native.get("initialized") is True,
                "Worker did not complete successfully")
        require(native.get("native_cpp_provider") is True and native.get("input_language") == "OpenCL C 1.2",
                "Unexpected provider/input scope")
        require(native.get("metal_tested") is False and native.get("mellow_jit_used") is False and
                native.get("default_metal_route_rejected") is True, "Metal scope/gating differs")
        seed = native["seed"]
        summary, runs, bootstrap = native["submission_summary"], native["runs"], native["bootstrap"]
        count, epoch = summary["verified_iterations"], summary["epoch"]
        first, last = summary["first_sequence"], summary["last_sequence"]
        if not (integer(seed) and seed <= 0xFFFFFFFF and integer(count) and count <= iterations and
                integer(epoch, 1) and integer(first, 1) and integer(last, 1)):
            return False, {}, ["Invalid summary or seed integer fields"]
        require(summary.get("requested_iterations") == iterations and count == iterations and
                summary.get("elements_per_iteration") == 256 and last - first == count - 1,
                "Requested/verified count or sequence span differs")
        require(summary.get("all_runtime_and_readback_checks_passed") is True and
                summary.get("same_queue_device_epoch_verified") is True, "Runtime checks not fully verified")
        input_hash, expected_hash = reference_streams(seed, count)
        independent = {
            "verified_iterations": count, "input_stream_sha256": input_hash,
            "expected_stream_sha256": expected_hash,
            "native_inputs_match": summary.get("input_stream_sha256") == input_hash,
            "native_expected_match": summary.get("expected_stream_sha256") == expected_hash,
            "gpu_readback_stream_matches": summary.get("readback_stream_sha256") == expected_hash,
        }
        require(all(independent[key] for key in ("native_inputs_match", "native_expected_match", "gpu_readback_stream_matches")),
                "Full stream hashes do not match independent reference")
        require(bootstrap.get("submitted") is True and bootstrap.get("event_ownership_verified") is True and
                bootstrap.get("results_verified") is True and bootstrap.get("profiling_verified") is True and
                bootstrap.get("resources_released") is True, "Bootstrap evidence incomplete")
        require(bootstrap.get("epoch") == epoch and integer(bootstrap.get("sequence"), 1) and
                bootstrap["sequence"] + 1 == first, "Bootstrap/positive epoch or sequence differs")
        require(bootstrap.get("output") == [(index * 13 + 1) * 7 + 3 for index in range(256)],
                "Bootstrap readback differs from witness")
        indices = list(range(iterations)) if iterations <= 3 else [0, iterations - 1]
        require(native.get("runs_sampling") == ("all" if iterations <= 3 else "first-and-last"),
                "Unexpected sample selection")
        if not isinstance(runs, list) or len(runs) != len(indices):
            return False, independent, reasons + ["Sample count differs"]
        previous_end = bootstrap.get("gpu_end_ns")
        require(integer(bootstrap.get("gpu_start_ns"), 1) and integer(previous_end, 1) and
                bootstrap["gpu_start_ns"] < previous_end, "Bootstrap profiling interval invalid")
        for run, index in zip(runs, indices):
            outcome = run["execution"]
            values = [(seed ^ ((item + index * 263) * 0x9E3779B9)) & 0xFFFF for item in range(256)]
            expected = [value * 7 + 3 for value in values]
            require(run.get("iteration") == index and type(run.get("iteration")) is int,
                    "Sample iteration differs")
            require(run.get("input") == values and run.get("expected") == expected and outcome.get("output") == expected,
                    "Sample 256-word buffers differ from seed/reference")
            require(outcome.get("epoch") == epoch and outcome.get("sequence") == first + index,
                    "Sample epoch/sequence differs from summary")
            require(all(outcome.get(key) is True for key in ("submission_attempted", "submitted", "event_ownership_verified",
                        "results_verified", "profiling_verified", "runtime_planned", "runtime_completion_accepted", "resources_released")),
                    "Sample did not pass every provider/runtime check")
            require(all(outcome.get(key) == 0 for key in ("plan_status", "arm_status", "observe_status")),
                    "Sample status codes do not indicate acceptance")
            start, end = outcome.get("gpu_start_ns"), outcome.get("gpu_end_ns")
            valid_time = integer(start, 1) and integer(end, 1) and start < end and integer(previous_end, 1) and start >= previous_end
            require(valid_time, "Sample profiling interval/order invalid")
            previous_end = end
            run["input_sha256"] = words_digest(values)
            run["expected_sha256"] = words_digest(expected)
            run["readback_sha256"] = words_digest(outcome["output"])
            run["readback_equals_expected"] = outcome["output"] == expected
            run["independent_formula_verified"] = run["input"] == values and run["expected"] == expected
        require(summary.get("first_gpu_start_ns") == runs[0]["execution"]["gpu_start_ns"] and
                summary.get("last_gpu_end_ns") == runs[-1]["execution"]["gpu_end_ns"],
                "Summary/sample GPU timestamp endpoints differ")
        negatives = native.get("negative_checks", {})
        require(all(negatives.get(key) is True for key in ("invalid_source_rejected", "oversized_input_rejected",
                    "wrong_reference_rejected", "invalidated_session_rejected")), "Negative API checks incomplete")
    except (KeyError, TypeError, ValueError, struct.error, AttributeError) as error:
        reasons.append("Malformed native evidence: " + str(error))
    return not reasons, independent, reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compute", action="store_true", help="Execute fixed small native-provider GPU acceptance workloads")
    parser.add_argument("--gpu-index", type=int, default=0)
    parser.add_argument("--iterations", type=int, default=3, help="Positive GPU submissions, 1-10000; over 3 explicitly requests stress")
    parser.add_argument("--timeout", type=int, default=45, help="Worker deadline: 1-120 seconds, or up to 180 with explicit stress")
    args = parser.parse_args()
    if not args.cxx:
        parser.error("A native host C++17 compiler is required")
    if args.gpu_index < 0 or not 1 <= args.iterations <= 10000 or not 1 <= args.timeout <= (180 if args.iterations > 3 else 120):
        parser.error("GPU index must be nonnegative, iterations 1-10000; timeout max120 (max180 for iterations>3)")
    root = Path(__file__).resolve().parents[1]
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    executable = args.out / ("opencl-runtime.exe" if os.name == "nt" else "opencl-runtime")
    native_path = args.out / "opencl-runtime-native.json"
    report_path = args.out / "opencl-runtime.json"
    sources = ["Runtime/PlatformRuntime.hpp", "Runtime/PlatformRuntime.cpp", "Runtime/OpenCLAbi.hpp",
               "Runtime/OpenCLProvider.hpp", "Runtime/OpenCLProvider.cpp",
               "tests/opencl_runtime_hardware.cpp", "tests/opencl_runtime_sha256.hpp", "Tools/run-opencl-runtime.py"]
    report = {
        "schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "native-MellowRuntime-host-OpenCL-C-provider-only",
        "os": {"system": platform.system(), "release": platform.release(), "version": platform.version(),
               "machine": platform.machine()},
        "source_sha256": {name: digest(root / name) for name in sources},
        "compute_requested": args.compute, "gpu_work_executed": False,
        "native_runtime_gpu_compute_pass": False, "metal_tested": False,
        "mellow_jit_used": False, "linux_driver_port_loaded": False,
        "status": "FAILED", "worker_deadline_seconds": args.timeout,
        "requested_iterations": args.iterations,
    }
    child_env = os.environ.copy()
    options = {"env": child_env}
    if os.name == "nt":
        # MinGW-built executables may still need libwinpthread-1.dll even with
        # static libgcc/libstdc++. Resolve it from the explicitly selected
        # toolchain, without relying on the caller's PATH or bundling a DLL.
        resolved_compiler = shutil.which(args.cxx) or args.cxx
        compiler_bin = str(Path(resolved_compiler).resolve().parent)
        child_env["PATH"] = compiler_bin + os.pathsep + child_env.get("PATH", "")
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
        report["windows_child_compiler_bin_prepended"] = True
    run_path = None
    worker_started = False
    try:
        version = subprocess.run([args.cxx, "--version"], capture_output=True, text=True, timeout=20, **options)
        report["compiler_version"] = version.stdout.strip()
        command = [args.cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   str(root / "Runtime/PlatformRuntime.cpp"), str(root / "Runtime/OpenCLProvider.cpp"),
                   str(root / "tests/opencl_runtime_hardware.cpp"), "-o", str(executable)]
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
            print("BUILT_ONLY: specify --compute for an explicit bounded GPU test")
            return 0
        # A new worker report path prevents a failed run from reusing old PASS.
        run_path = args.out / ("native-run-" + secrets.token_hex(8) + ".json")
        run_command = [str(executable), "--compute", "--report", str(run_path),
                       "--seed", str(secrets.randbits(32)), "--gpu-index", str(args.gpu_index),
                       "--iterations", str(args.iterations)]
        worker_started = True
        worker = subprocess.run(run_command, capture_output=True, text=True, timeout=args.timeout, **options)
        report["worker"] = {"exit_code": worker.returncode, "stdout": worker.stdout, "stderr": worker.stderr}
        print(worker.stdout, end="")
        if not run_path.exists():
            report["gpu_work_executed"] = None
            report["error"] = "Worker did not produce a current report"
            return 1
        native = json.loads(run_path.read_text(encoding="utf-8"))
        run_path.replace(native_path)
        report["native"] = native
        report["gpu_work_executed"] = native.get("bootstrap", {}).get("submitted", False)
        success, independent, reasons = validate_native_result(native, worker.returncode, args.iterations)
        report["independent_stream_reference"] = independent
        report["evidence_validation_errors"] = reasons
        report["native_runtime_gpu_compute_pass"] = success
        report["status"] = "PASS_NATIVE_OPENCL_RUNTIME_ONLY" if success else "FAILED"
        report["source_changed_during_run"] = [name for name in sources if digest(root / name) != report["source_sha256"][name]]
        if report["source_changed_during_run"]:
            report["status"] = "SOURCE_CHANGED_DURING_RUN"
            report["native_runtime_gpu_compute_pass"] = False
            return 1
        return 0 if success else 1
    except subprocess.TimeoutExpired as error:
        report["status"] = "TIMED_OUT"
        report["gpu_work_executed"] = None if worker_started else False
        report["error"] = f"Child process exceeded {error.timeout} seconds and was terminated; execution state may be incomplete"
        return 1
    except (OSError, ValueError, KeyError) as error:
        if worker_started and "native" not in report:
            report["gpu_work_executed"] = None
        report["error"] = str(error)
        return 1
    finally:
        if worker_started and report["status"] != "PASS_NATIVE_OPENCL_RUNTIME_ONLY":
            checkpoint = last_checkpoint(run_path, args.iterations)
            if checkpoint is not None:
                report["partial_submission_progress"] = checkpoint
                verified_count = checkpoint["verified_iterations"]
                partial_input, partial_expected = reference_streams(checkpoint["seed"], verified_count)
                report["partial_stream_reference_matches"] = (
                    checkpoint.get("input_stream_sha256") == partial_input and
                    checkpoint.get("expected_stream_sha256") == partial_expected and
                    checkpoint.get("readback_stream_sha256") == partial_expected)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Report: {report_path}")


if __name__ == "__main__":
    raise SystemExit(main())
