#!/usr/bin/env python3
"""Decode actual bitcode if requested, then run the native typed shader lowering.

This is the source/IR-to-OpenCL-C stage, not a claim that Metal or a GPU ran.
Use Tools/run-metal-objects.py for compilation and GPU execution via MellowMTL.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

from mellow_air import AirError, MAX_LOG, bounded_read, disassemble, sha256


def lower(data: bytes, kind: str, entry: str, translator: Path,
          llvm_dis: Path | None = None, *, timeout: float = 30.0) -> dict:
    if kind not in ("msl", "air-text", "air"):
        raise AirError("unknown shader input format")
    if not entry or len(entry) > 1024 or "\0" in entry:
        raise AirError("invalid entry")
    if not 0 < timeout <= 60:
        raise AirError("invalid translator timeout")
    metadata = {"input_sha256": sha256(data), "input_kind": kind,
                "gpu_executed": False, "apple_metal_abi_implemented": False}
    if kind == "air":
        if llvm_dis is None:
            raise AirError("AIR bitcode requires an explicit llvm-dis")
        text, decoded = disassemble(data, llvm_dis, entry=entry)
        metadata["decoder"] = decoded
        data = text.encode("utf-8")
        kind = "air-text"
    if len(data) > 65536:
        raise AirError("shader lowering input exceeds 64 KiB")
    executable = translator.resolve(strict=True)
    before = sha256(executable.read_bytes())
    with tempfile.TemporaryDirectory(prefix="mellow-shader-") as directory:
        input_file = Path(directory) / "input.txt"
        input_file.write_bytes(data)
        # The selected translator is a locally built bounded C++ tool. No shell
        # or arbitrary compiler options are taken from shader input.
        out_path, err_path = Path(directory) / "output.json", Path(directory) / "stderr.txt"
        with out_path.open("wb") as out_file, err_path.open("wb") as err_file:
            process = subprocess.Popen([str(executable), kind, str(input_file), entry],
                                       cwd=directory, stdin=subprocess.DEVNULL, stdout=out_file, stderr=err_file)
            try:
                deadline = time.monotonic() + timeout
                while process.poll() is None:
                    if time.monotonic() >= deadline:
                        raise AirError("shader translator timed out")
                    if out_path.stat().st_size > MAX_LOG or err_path.stat().st_size > MAX_LOG:
                        raise AirError("shader translator output exceeds byte limit")
                    time.sleep(0.01)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
        stdout = bounded_read(out_path, MAX_LOG)
        bounded_read(err_path, MAX_LOG)
        if sha256(executable.read_bytes()) != before or input_file.read_bytes() != data:
            raise AirError("translator or input changed during lowering")
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise AirError("duplicate translator report key")
                result[key] = value
            return result
        def invalid_constant(value):
            raise AirError("invalid JSON constant: " + value)
        report = json.loads(stdout, object_pairs_hook=unique, parse_constant=invalid_constant)
    except (ValueError, UnicodeError) as exc:
        raise AirError("invalid shader translator result") from exc
    if not isinstance(report, dict) or type(report.get("schema_version")) is not int or report["schema_version"] != 1 or report.get("gpu_executed") is not False:
        raise AirError("invalid translator scope/schema")
    if set(report) != {"schema_version", "status", "gpu_executed", "input", "entry", "opencl_source", "diagnostics"}:
        raise AirError("unknown translator report fields")
    if report.get("input") != kind or not isinstance(report.get("entry"), str):
        raise AirError("translator result does not match input format")
    if not isinstance(report.get("diagnostics"), list) or any(not isinstance(x, str) for x in report["diagnostics"]):
        raise AirError("invalid translator diagnostics")
    status = report.get("status")
    if status == "LOWERED_OPENCL_C_ONLY":
        if process.returncode != 0 or report["entry"] != entry or not isinstance(report.get("opencl_source"), str) or not report["opencl_source"]:
            raise AirError("contradictory successful shader result")
    elif status == "REJECTED":
        if process.returncode != 2 or report.get("opencl_source") != "":
            raise AirError("contradictory rejected shader result")
    else:
        raise AirError("unknown shader result status")
    report.update(metadata, translator_sha256=before)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("msl", "air-text", "air"), required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--translator", type=Path, required=True)
    parser.add_argument("--llvm-dis", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error("report must be a new path")
    try:
        report = lower(bounded_read(args.input), args.format, args.entry, args.translator, args.llvm_dis)
    except (AirError, OSError, subprocess.TimeoutExpired) as exc:
        report = {"schema_version": 1, "status": "FAIL", "error": str(exc), "gpu_executed": False}
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "gpu_executed": False}))
    return 0 if report["status"] == "LOWERED_OPENCL_C_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
