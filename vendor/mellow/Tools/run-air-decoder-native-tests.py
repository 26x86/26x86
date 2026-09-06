#!/usr/bin/env python3
"""Build/run actual LLVM C API concurrent lifetime tests with explicit local LLVM.

No downloads or GPU calls. The fixed positive fixture is synthetic bitcode.
Deadlines and bounded output supervise ordinary failures; this is not a sandbox.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MAX_LOG = 256 * 1024


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def execute(command, base, label, timeout):
    stdout, stderr = base / (label + ".stdout"), base / (label + ".stderr")
    with stdout.open("xb") as out, stderr.open("xb") as err:
        process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + timeout
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    raise RuntimeError(label + " deadline exceeded")
                if stdout.stat().st_size > MAX_LOG or stderr.stat().st_size > MAX_LOG:
                    raise RuntimeError(label + " output exceeds limit")
                time.sleep(0.01)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    for path in (stdout, stderr):
        if path.stat().st_size > MAX_LOG:
            raise RuntimeError(label + " output exceeds limit")
    return process.returncode, stdout.read_text(encoding="utf-8")


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate result key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-library", type=Path, required=True)
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    library = args.llvm_library.resolve(strict=True)
    compiler_name = shutil.which(args.compiler)
    if not compiler_name:
        parser.error("compiler not found")
    compiler = Path(compiler_name).resolve(strict=True)
    output = args.output_dir.resolve()
    if output.exists():
        parser.error("output directory must be new")
    output.mkdir(parents=True)
    sources = [ROOT / "Runtime/AirDecoder.cpp", ROOT / "Runtime/AirDecoder.hpp",
               ROOT / "tests/air_decoder_native_tests.cpp", Path(__file__).resolve()]
    fixture = ROOT / "tests/fixtures/air/synthetic-uint-affine.bc"
    tracked = sources + [fixture, compiler, library]
    before = {str(path): digest(path) for path in tracked}
    report = {"schema_version": 1, "status": "FAIL", "gpu_executed": False,
              "shader_lowered": False, "apple_compiler_origin_authenticated": False,
              "fixture_origin": "synthetic", "inputs_sha256_before": before}
    try:
        binary = output / ("air-decoder-native-tests.exe" if os.name == "nt" else "air-decoder-native-tests")
        command = [str(compiler), "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pthread",
                   "-I" + str(ROOT / "Runtime"), str(sources[0]), str(sources[2]), "-o", str(binary)]
        if sys.platform.startswith("linux"):
            command.append("-ldl")
        report["build_command"] = command
        code, _ = execute(command, output, "build", 120)
        report["build_returncode"] = code
        if code != 0:
            raise RuntimeError("native decoder test build failed")
        binary_hash = digest(binary)
        command = [str(binary), str(fixture), str(library)]
        report["run_command"] = command
        code, stdout = execute(command, output, "run", 30)
        report["run_returncode"] = code
        result = json.loads(stdout, object_pairs_hook=unique)
        expected = {"status": "PASS_LLVM_C_DECODER_LIFETIME", "threads": 4, "checks": 256, "failures": 0,
                    "gpu_executed": False, "shader_lowered": False, "apple_compiler_origin_authenticated": False}
        if code != 0 or result != expected or any(type(result[k]) is not type(v) for k, v in expected.items()):
            raise RuntimeError("native decoder execution/protocol mismatch")
        report["inputs_sha256_after"] = {str(path): digest(path) for path in tracked}
        report["binary_sha256_before"] = binary_hash
        report["binary_sha256_after"] = digest(binary)
        if report["inputs_sha256_after"] != before or binary_hash != report["binary_sha256_after"]:
            raise RuntimeError("recorded execution inputs changed")
        report.update(status=expected["status"], native_result=result)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        report["error"] = str(exc)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "gpu_executed": False, "report": str(output / "report.json")}))
    return 0 if report["status"] == "PASS_LLVM_C_DECODER_LIFETIME" else 2


if __name__ == "__main__":
    raise SystemExit(main())
