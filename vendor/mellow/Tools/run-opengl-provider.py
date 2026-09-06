#!/usr/bin/env python3
"""Actual Windows WGL driver render acceptance; no macOS/WindowServer claim."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Invalid JSON number: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def pixels(seed, iteration):
    bits = (seed ^ iteration) & 15
    return bytes(channel for y in range(48) for x in range(64) for channel in
                 (255 * ((bits >> (0 if x < 32 else 1)) & 1),
                  255 * ((bits >> (2 if y < 24 else 3)) & 1), 0, 255))


def validate_native(native, seed, count, visible):
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    if type(native) is not dict:
        return ["Native report must be a JSON object"]
    need("error" not in native, "Successful frame report contains an error")
    for key, expected in (("schema_version", 1), ("requested_frames", count), ("frames_completed", count),
                          ("seed", seed), ("width", 64), ("height", 48), ("pipeline_build_count", 1),
                          ("epoch", 1), ("first_sequence", 1), ("last_sequence", count), ("negative_checks", 11)):
        need(type(native.get(key)) is int and native[key] == expected, key + " mismatch")
    for key in ("passed", "all_frames_correlated", "all_rgba_patterns_verified"):
        need(native.get(key) is True, key + " must be true")
    for key in ("native_macos_execution", "windowserver_acceleration_verified", "display_scanout_verified",
                "physical_pci_identity_verified"):
        need(native.get(key) is False, key + " must be false")
    need(native.get("visible_window_requested") is visible, "Visible request mismatch")
    need(native.get("row_origin") == "bottom-left", "Readback row origin mismatch")
    need(type(native.get("checks")) is int and native["checks"] >= 6 * count + 20, "Insufficient assertions")
    device = native.get("device")
    if type(device) is not dict:
        errors.append("Missing device evidence")
    else:
        for key in ("accelerated_pixel_format", "software_renderer_rejected", "core_profile"):
            need(device.get(key) is True, "Device " + key + " missing")
        for key in ("vendor", "renderer", "version", "glsl_version"):
            need(type(device.get(key)) is str and 0 < len(device[key]) < 16384, "Invalid device " + key)
        major, minor = device.get("major"), device.get("minor")
        need(type(major) is int and type(minor) is int and (major > 3 or major == 3 and minor >= 3),
             "Core OpenGL3.3 requirement failed")
    patterns = {i: pixels(seed, i) for i in range(16)}
    expected = hashlib.sha256()
    for i in range(count):
        expected.update(patterns[i % 16])
    need(native.get("expected_stream_sha256") == expected.hexdigest(), "Expected stream mismatch")
    need(native.get("readback_stream_sha256") == expected.hexdigest(), "Actual readback stream mismatch")
    samples = native.get("samples")
    indices = [0] if count == 1 else [0, count - 1]
    if type(samples) is not list or len(samples) != len(indices):
        errors.append("Missing bounded first/last samples")
    else:
        for sample, i in zip(samples, indices):
            if type(sample) is not dict:
                errors.append("Invalid sample object")
                continue
            for key, expected_value in (("iteration", i), ("sequence", i + 1), ("epoch", 1)):
                need(type(sample.get(key)) is int and sample[key] == expected_value, "Sample " + key + " mismatch")
            for key in ("render_submitted", "fence_signaled", "readback_completed", "resources_released"):
                need(sample.get(key) is True, "Sample " + key + " incomplete")
            need(sample.get("swap_completed") is visible and sample.get("scanout_verified") is False, "Swap/scanout scope mismatch")
            need(type(sample.get("swap_interval_known")) is bool and type(sample.get("swap_interval")) is int,
                 "Swap interval types invalid")
            need(sample.get("rgba_sha256") == hashlib.sha256(patterns[i % 16]).hexdigest(), "Sample RGBA mismatch")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--render", action="store_true", help="Explicitly execute actual GPU work")
    parser.add_argument("--visible", action="store_true", help="Show owned animated window and request swaps")
    parser.add_argument("--frames", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    if not args.cxx:
        parser.error("C++17 compiler required")
    if not 1 <= args.frames <= 10000 or not 1 <= args.timeout <= 180:
        parser.error("Frames must be 1-10000; timeout 1-180 seconds")
    if args.visible and not args.render:
        parser.error("--visible requires --render")
    root = Path(__file__).resolve().parents[1]
    args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=True)
    sources = ["Runtime/OpenGLProvider.hpp", "Runtime/OpenGLProvider.cpp", "tests/opengl_provider_tests.cpp",
               "tests/opencl_runtime_sha256.hpp", "Tools/run-opengl-provider.py"]
    report = dict(schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(),
                  scope="native-Windows-WGL-GLSL-driver-offscreen-render-and-optional-swap",
                  os=dict(system=platform.system(), release=platform.release(), version=platform.version()),
                  source_sha256={name: digest(root / name) for name in sources},
                  native_macos_execution=False, windowserver_acceleration_verified=False,
                  display_scanout_verified=False, physical_pci_identity_verified=False,
                  gpu_work_executed=False, passed=False, status="FAILED",
                  requested_frames=args.frames, visible_window_requested=args.visible)
    options = {"env": os.environ.copy()}
    if os.name == "nt":
        compiler = Path(shutil.which(args.cxx) or args.cxx).resolve()
        options["env"]["PATH"] = str(compiler.parent) + os.pathsep + options["env"].get("PATH", "")
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    started = False
    try:
        version = subprocess.run([args.cxx, "--version"], capture_output=True, text=True, timeout=20, **options)
        report["compiler_version"] = version.stdout.strip()
        executable = args.out / ("opengl-provider.exe" if os.name == "nt" else "opengl-provider")
        command = [args.cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   str(root / "Runtime/OpenGLProvider.cpp"), str(root / "tests/opengl_provider_tests.cpp"), "-o", str(executable)]
        if os.name == "nt":
            command += ["-lopengl32", "-lgdi32", "-luser32", "-static-libgcc", "-static-libstdc++"]
        else:
            command += ["-pthread"]
        build = subprocess.run(command, capture_output=True, text=True, timeout=120, **options)
        report["build"] = dict(exit_code=build.returncode, stdout=build.stdout, stderr=build.stderr)
        if build.returncode:
            print(build.stdout + build.stderr, file=sys.stderr)
            return 1
        report["binary_sha256"] = digest(executable)
        if not args.render:
            report["status"] = "BUILT_ONLY"
            return 0
        if os.name != "nt":
            report["status"] = "NOT_AVAILABLE"
            report["error"] = "Actual native OpenGL provider is Windows WGL only"
            return 1
        result_path = args.out / ("native-" + secrets.token_hex(8) + ".json")
        seed = secrets.randbits(32)
        invocation = [str(executable), "--render", "--report", str(result_path), "--seed", str(seed), "--frames", str(args.frames)]
        if args.visible:
            invocation.append("--visible")
        started = True
        worker = subprocess.run(invocation, capture_output=True, text=True, timeout=args.timeout, **options)
        report["worker"] = dict(exit_code=worker.returncode, stdout=worker.stdout, stderr=worker.stderr)
        print(worker.stdout, end="")
        if not result_path.is_file():
            raise ValueError("Worker produced no current report; GPU execution unknown")
        native = strict_json(result_path.read_text(encoding="utf-8"))
        if type(native) is not dict:
            raise ValueError("Worker report must be an object")
        result_path.replace(args.out / "opengl-provider-native.json")
        report["native"] = native
        report["gpu_work_executed"] = True if type(native.get("frames_completed")) is int and native["frames_completed"] > 0 else None
        report["validation_errors"] = validate_native(native, seed, args.frames, args.visible)
        report["source_changed_during_run"] = [name for name in sources if digest(root / name) != report["source_sha256"][name]]
        passed = worker.returncode == 0 and not report["validation_errors"] and not report["source_changed_during_run"]
        report["passed"] = passed
        report["status"] = "PASS_NATIVE_OPENGL_RENDER_SUBSTRATE" if passed else "FAILED"
        return 0 if passed else 1
    except subprocess.TimeoutExpired as failure:
        report.update(status="TIMED_OUT", error=f"Worker/build deadline {failure.timeout} seconds exceeded",
                      gpu_work_executed=None if started else False)
        return 1
    except (OSError, ValueError, KeyError) as failure:
        report["error"] = str(failure)
        if started and "native" not in report:
            report["gpu_work_executed"] = None
        return 1
    finally:
        report["source_changed_during_run"] = [name for name in sources if not (root / name).is_file() or
                                               digest(root / name) != report["source_sha256"][name]]
        if report["source_changed_during_run"]:
            report.update(passed=False, status="FAILED_SOURCE_CHANGED")
        destination = args.out / "opengl-provider.json"
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("Report:", destination)
        if report["source_changed_during_run"]:
            return 1  # Override an earlier return if the final source check changed.


if __name__ == "__main__":
    raise SystemExit(main())
