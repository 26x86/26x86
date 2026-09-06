#!/usr/bin/env python3
"""Compile and execute the real port with simulated MMIO/DMA, without GPU access."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "Drivers/PortedXe"
EXPECTED_STATUS = "PASS_PORTED_XE_ALGORITHMS_SIMULATED_BOUNDARIES"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_provenance():
    manifest = json.loads((PORT / "provenance.json").read_text(encoding="utf-8"))
    if manifest.get("revision") != "0d9ff90a5422cc7509258aaaba1e7481df4d332a":
        raise ValueError("Unexpected upstream source revision")
    root = (PORT / "upstream").resolve()
    for entry in manifest["files"]:
        source = root / entry["path"]
        if not source.resolve().is_relative_to(root) or source.is_symlink():
            raise ValueError("Invalid provenance path")
        if source.stat().st_size != entry["bytes"] or sha256(source) != entry["sha256"]:
            raise ValueError("Upstream source hash/size mismatch: " + entry["path"])
    copied = (PORT / "XePteAlgorithms.inc").read_text(encoding="utf-8")
    for function in manifest["ported_functions"]:
        source = (root / function["file"]).read_text(encoding="utf-8").splitlines()
        original = "\n".join(source[function["start_line"] - 1:function["end_line"]])
        match = re.search(r"^static u64 " + re.escape(function["function"]) + r"\([^)]*\)\s*\{.*?^\}", copied, re.M | re.S)
        if not match or match[0] != original or hashlib.sha256(original.encode()).hexdigest() != function["source_fragment_sha256"]:
            raise ValueError("Ported function differs from recorded upstream source: " + function["function"])
    return {"revision": manifest["revision"], "source_files_checked": len(manifest["files"]), "verbatim_functions_checked": len(manifest["ported_functions"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--out", type=Path, required=True, help="New scratch directory outside the source repository")
    parser.add_argument("--static", action="store_true", help="Request a static host executable for a compatible Linux guest")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.is_relative_to(ROOT) or ROOT.is_relative_to(out):
        parser.error("Scratch output must not overlap the source repository")
    if args.out.is_symlink() or out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Scratch output must be new or empty and not a symlink")
    if not args.cxx:
        parser.error("C++ compiler unavailable; specify --cxx")
    report = {"schema_version": 1, "status": "FAIL", "layer": "portable Xe driver algorithms with simulated boundary tests",
              "hardware_execution": False, "darwin_driver_loaded": False, "metal_tested": False,
              "real_source_port": True, "mmio_dma_boundary": "simulated", "compile_performed": False}
    out.mkdir(parents=True, exist_ok=True)
    try:
        report["provenance"] = verify_provenance()
        binary = out / ("ported-xe-tests.exe" if sys.platform == "win32" else "ported-xe-tests")
        command = [args.cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror"]
        if args.static:
            command.append("-static")
        sources = [PORT / "XePageTable.cpp", ROOT / "tests/ported_xe_test.cpp"]
        command.extend([*(str(path) for path in sources), "-o", str(binary)])
        report["source_sha256"] = {path.relative_to(ROOT).as_posix(): sha256(path) for path in [*sources, PORT / "XePageTable.hpp", PORT / "XePteAlgorithms.inc", PORT / "provenance.json", Path(__file__).resolve()]}
        compilation = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        report["compile_performed"] = True
        report["compile"] = {"command": command, "returncode": compilation.returncode, "stdout": compilation.stdout, "stderr": compilation.stderr}
        if compilation.returncode:
            raise ValueError("Host compilation failed")
        report["executable_sha256"] = sha256(binary)
        execution = subprocess.run([str(binary)], cwd=out, capture_output=True, text=True, timeout=30)
        report["execution"] = {"returncode": execution.returncode, "stdout": execution.stdout, "stderr": execution.stderr}
        if execution.returncode:
            raise ValueError("Host test process failed")
        result = json.loads(execution.stdout.strip().splitlines()[-1])
        if result.get("status") != EXPECTED_STATUS or not isinstance(result.get("checks"), int) or result["checks"] <= 0 or result.get("hardware_execution") is not False or result.get("simulated_mmio_dma") is not True:
            raise ValueError("Missing or contradictory acceptance result")
        report["result"] = result
        report["status"] = EXPECTED_STATUS
    except (OSError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
    (out / "ported-xe-tests.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": report.get("result", {}).get("checks", 0), "hardware_execution": False, "report": str(out / "ported-xe-tests.json")}))
    return 0 if report["status"] == EXPECTED_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
