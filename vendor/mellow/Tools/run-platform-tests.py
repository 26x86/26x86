#!/usr/bin/env python3
"""Compile and execute portable runtime policy tests; never reports GPU PASS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
from datetime import datetime, timezone


def execute(compiler, root, output, sanitize):
    output.mkdir(parents=True, exist_ok=True)
    binary = output / ("platform-tests.exe" if os.name == "nt" else "platform-tests")
    files = ["Runtime/PlatformRuntime.hpp", "Runtime/PlatformRuntime.cpp",
             "tests/platform_runtime_test.cpp", "Tools/run-platform-tests.py"]
    report = {
        "schema_version": 1,
        "evidence_scope": "software-policy-only-synthetic-adapters",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "physical_gpu_executed": False,
        "metal_conformance_tested": False,
        "compiler": compiler,
        "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                          for name in files},
        "sanitizers": ["address", "undefined"] if sanitize else [],
        "build": None,
        "test": None,
        "status": "FAIL",
    }
    try:
        version = subprocess.run([compiler, "--version"], capture_output=True,
                                 text=True, check=False, timeout=20)
        report["compiler_version"] = version.stdout.strip()
        command = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   "-fno-exceptions", "-fno-rtti",
                   str(root / "Runtime/PlatformRuntime.cpp"),
                   str(root / "tests/platform_runtime_test.cpp"), "-o", str(binary)]
        if sanitize:
            command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        build = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        report["build"] = {"exit_code": build.returncode,
                           "stdout": build.stdout, "stderr": build.stderr}
        if build.returncode:
            print(build.stdout + build.stderr, file=sys.stderr)
            return build.returncode
        test = subprocess.run([str(binary)], capture_output=True, text=True, check=False, timeout=60)
        report["test"] = {"exit_code": test.returncode,
                          "stdout": test.stdout, "stderr": test.stderr}
        print(test.stdout, end="")
        print(test.stderr, end="", file=sys.stderr)
        if test.returncode == 0:
            report["status"] = "PASS_SOFTWARE_POLICY_ONLY"
        return test.returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
        print(str(error), file=sys.stderr)
        return 1
    finally:
        destination = output / "platform-tests.json"
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", "--compiler", dest="compiler", default=os.environ.get("CXX", ""))
    parser.add_argument("--out", type=Path, help="Retain binary and platform-tests.json in this directory")
    parser.add_argument("--sanitize", action="store_true",
                        help="Enable address/undefined sanitizers on a supported host compiler")
    args = parser.parse_args()
    compiler = args.compiler or shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        parser.error("C++17 compiler required; on Windows run this script inside WSL")
    root = Path(__file__).resolve().parents[1]
    if args.out:
        return execute(compiler, root, args.out.resolve(), args.sanitize)
    with tempfile.TemporaryDirectory(prefix="mellow-platform-") as temp:
        return execute(compiler, root, Path(temp), args.sanitize)


if __name__ == "__main__":
    raise SystemExit(main())
