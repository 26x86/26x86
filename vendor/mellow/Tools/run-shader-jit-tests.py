#!/usr/bin/env python3
"""Test typed shader lowering and generated-code CPU references; no GPU access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["Runtime/ShaderJit.cpp", "Runtime/AirDecoder.cpp", "tests/shader_jit_tests.cpp"]
INPUTS = SOURCES + ["Runtime/ShaderJit.hpp", "Runtime/AirDecoder.hpp", "Tools/run-shader-jit-tests.py"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--clang", default=shutil.which("clang"), help="Actual clang for generated OpenCL C syntax checking")
    parser.add_argument("--require-opencl-syntax", action="store_true")
    parser.add_argument("--sanitize", action="store_true", help="Enable actual host ASan and UBSan")
    parser.add_argument("--llvm-as", help="Optional real llvm-as for synthetic AIR bitcode roundtrip")
    parser.add_argument("--llvm-dis", help="Optional real llvm-dis for synthetic AIR bitcode roundtrip")
    parser.add_argument("--out", type=Path, required=True, help="New or empty scratch directory outside this repository")
    args = parser.parse_args()
    if not args.cxx:
        parser.error("Specify an available C++ compiler with --cxx")
    if args.require_opencl_syntax and not args.clang:
        parser.error("--require-opencl-syntax requires an actual clang executable")
    if bool(args.llvm_as) != bool(args.llvm_dis):
        parser.error("Supply both --llvm-as and --llvm-dis for a roundtrip")
    # subprocess runs in the scratch directory: resolve caller-relative tools
    # before changing cwd, and resolve bare commands through the caller PATH.
    for key in ("cxx", "clang", "llvm_as", "llvm_dis"):
        value = getattr(args, key)
        if value:
            resolved = str(Path(value).resolve()) if Path(value).is_file() else shutil.which(value)
            if not resolved:
                parser.error("Compiler/tool is unavailable: " + value)
            setattr(args, key, resolved)
    out = args.out.resolve()
    if out.is_relative_to(ROOT) or ROOT.is_relative_to(out):
        parser.error("Scratch output must not overlap the source repository")
    if args.out.is_symlink() or out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Scratch output must be new or empty and not a symlink")
    # Explicit compiler selection also supplies its companion runtime DLLs.
    env = os.environ.copy()
    if sys.platform == "win32":
        env["PATH"] = str(Path(args.cxx).resolve().parent) + os.pathsep + env.get("PATH", "")
    report = {"schema_version": 1, "status": "FAIL_SHADER_FRONTEND_TESTS", "hardware_execution": False,
              "metal_driver_registered": False, "air_fixture_origin": "synthetic", "sanitizers_enabled": args.sanitize,
              "opencl_driver_jit_tested": False, "opencl_syntax_checked": False, "llvm_roundtrip_tested": False,
              "phases": [], "source_sha256": {}}
    out.mkdir(parents=True, exist_ok=True)

    def run(name, command, timeout=120):
        phase = {"name": name, "command": list(map(str, command))}
        report["phases"].append(phase)
        result = subprocess.run(command, cwd=out, env=env, capture_output=True, text=True, errors="replace", timeout=timeout)
        phase.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        if result.returncode:
            raise ValueError(name + " failed")
        return result

    try:
        report["source_sha256"] = {name: digest(ROOT / name) for name in INPUTS}
        suffix = ".exe" if sys.platform == "win32" else ""
        binary = out / ("shader-jit-tests" + suffix)
        flags = ["-std=c++17", "-O1" if args.sanitize else "-O2", "-Wall", "-Wextra", "-Werror"]
        if args.sanitize:
            flags += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        link = [] if sys.platform == "win32" else ["-ldl"]
        run("compile_frontend_tests", [args.cxx, *flags, *(str(ROOT / name) for name in SOURCES), *link, "-o", str(binary)])
        report["test_executable_sha256"] = digest(binary)
        execution = run("execute_frontend_tests", [str(binary), "--emit-fixtures", str(out)], 60)
        result = json.loads(execution.stdout.strip().splitlines()[-1])
        if (result.get("status") != "PASS_SHADER_FRONTEND_SUBSET" or type(result.get("checks")) is not int or result["checks"] < 2000
                or result.get("hardware_execution") is not False or result.get("air_fixture_origin") != "synthetic"):
            raise ValueError("Missing or contradictory frontend test acceptance")
        report["frontend_result"] = result
        host = out / ("generated-host-tests" + suffix)
        run("compile_generated_cpu_reference", [args.cxx, *flags, "-Wno-unused-variable", str(out / "generated-host-tests.cpp"), "-o", str(host)])
        report["generated_host_executable_sha256"] = digest(host)
        reference = run("execute_generated_cpu_reference", [str(host)], 30)
        ref = json.loads(reference.stdout.strip().splitlines()[-1])
        if ref.get("status") != "PASS_GENERATED_SHADER_CPU_REFERENCE" or type(ref.get("checks")) is not int or ref["checks"] != 72:
            raise ValueError("Missing generated-code CPU reference acceptance")
        report["generated_cpu_reference"] = ref
        if args.clang:
            paths = sorted(out.glob("*.cl"))
            if len(paths) != 9:
                raise ValueError("Unexpected number of generated OpenCL fixtures")
            for path in paths:
                run("opencl_syntax_" + path.stem, [args.clang, "-x", "cl", "-cl-std=CL1.2", "-fsyntax-only", str(path)], 30)
            report["opencl_syntax_checked"] = True
            report["opencl_syntax_fixtures"] = len(paths)
        if args.llvm_as:
            bitcode = out / "synthetic-air-affine.bc"
            decoded = out / "synthetic-air-roundtrip.ll"
            lowered = out / "synthetic-air-roundtrip.cl"
            run("actual_llvm_assemble_synthetic_air", [args.llvm_as, str(out / "synthetic-air-affine.ll"), "-o", str(bitcode)], 30)
            run("actual_llvm_decode_synthetic_air", [args.llvm_dis, str(bitcode), "-o", str(decoded)], 30)
            run("lower_actual_llvm_decoded_synthetic_air", [str(binary), "--lower-air", str(decoded), "air_affine", str(lowered)], 30)
            if lowered.read_bytes() != (out / "air_affine.cl").read_bytes():
                raise ValueError("Synthetic AIR roundtrip changed lowering")
            report["llvm_roundtrip_tested"] = True
            report["synthetic_air_bitcode_sha256"] = digest(bitcode)
        report["generated_fixture_sha256"] = {p.name: digest(p) for p in sorted(out.iterdir()) if p.suffix in {".cl", ".metal", ".ll", ".cpp"}}
        report["status"] = "PASS_SHADER_FRONTEND_AND_HOST_REFERENCE"
    except (OSError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
    finally:
        changed = [name for name, before in report["source_sha256"].items() if not (ROOT / name).is_file() or digest(ROOT / name) != before]
        report["source_changed"] = changed
        if changed:
            report["status"] = "FAIL_SOURCE_CHANGED_DURING_TEST"
        path = out / "shader-jit-tests.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "checks": report.get("frontend_result", {}).get("checks", 0),
                          "cpu_reference_checks": report.get("generated_cpu_reference", {}).get("checks", 0),
                          "hardware_execution": False, "report": str(path)}))
    return 0 if report["status"] == "PASS_SHADER_FRONTEND_AND_HOST_REFERENCE" else 2


if __name__ == "__main__":
    sys.exit(main())
