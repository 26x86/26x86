#!/usr/bin/env python3
"""Build synthetic ICD lifecycle tests; no installed OpenCL runtime is loaded."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()
    if not args.cxx:
        parser.error("C++17 compiler required")
    root = Path(__file__).resolve().parents[1]
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    source_names = ["Runtime/OpenCLAbi.hpp", "Runtime/OpenCLProvider.hpp", "Runtime/OpenCLProvider.cpp",
                    "Runtime/PlatformRuntime.hpp", "Runtime/PlatformRuntime.cpp",
                    "tests/opencl_runtime_regression.cpp", "Tools/run-opencl-runtime-regressions.py"]
    report = {"scope": "synthetic-ICD-provider-lifecycle-only", "gpu_work_executed": False,
              "passed": False, "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                                  for name in source_names}}
    binary = args.out / ("opencl-runtime-regressions.exe" if os.name == "nt" else "opencl-runtime-regressions")
    command = [args.cxx, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic", "-DMELLOW_OPENCL_TESTING",
               str(root / "Runtime/PlatformRuntime.cpp"), str(root / "Runtime/OpenCLProvider.cpp"),
               str(root / "tests/opencl_runtime_regression.cpp"), "-o", str(binary)]
    if os.name == "nt":
        command.extend(["-static-libgcc", "-static-libstdc++"])
    elif sys.platform != "darwin":
        command.append("-ldl")
    if args.sanitize:
        command.extend(["-fsanitize=address,undefined", "-fno-omit-frame-pointer"])
    try:
        for name, invocation in (("build", command), ("test", [str(binary)])):
            run = subprocess.run(invocation, capture_output=True, text=True, timeout=120 if name == "build" else 30)
            report[name] = {"exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
            print(run.stdout + run.stderr, end="")
            if run.returncode:
                return 1
        report["passed"] = True
        return 0
    except (OSError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
        return 1
    finally:
        (args.out / "opencl-runtime-regressions.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
