#!/usr/bin/env python3
"""Verify explicit cold registers, boot_args readback, budget and feature gate.

All input instructions are independently authored. This is not an SPTM service
or a macOS boot proof. QEMU models an x86 host; the EFI image generates x86 code.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
from build_arm64_handoff_probe import image, sha256


def property_bytes(name: str, value: bytes, template: bool = False) -> bytes:
    return name.encode().ljust(32, b"\0") + struct.pack("<I", len(value) | (0x80000000 if template else 0)) + value.ljust((len(value) + 3) & ~3, b"\0")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi-trace", type=Path, required=True)
    parser.add_argument("--efi-default", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = args.output.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    source = tools / "arm64_sptm_prefix_probe.S"
    thread_source = tools / "arm64_thread_pointer_probe.S"
    inputs = (source, thread_source, args.efi_trace, args.efi_default)
    before = {str(path.resolve()): sha256(path) for path in inputs}
    subprocess.run(["clang", "--target=aarch64-none-elf", "-c", str(source), "-o", str(directory / "probe.o")], check=True)
    subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.text", str(directory / "probe.o"), str(directory / "probe.bin")], check=True)
    kernel = directory / "probe.kc"
    kernel.write_bytes(image((directory / "probe.bin").read_bytes()))
    subprocess.run(["clang", "--target=aarch64-none-elf", "-c", str(thread_source), "-o", str(directory / "thread.o")], check=True)
    subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.text", str(directory / "thread.o"), str(directory / "thread.bin")], check=True)
    thread_kernel = directory / "thread.kc"
    thread_kernel.write_bytes(image((directory / "thread.bin").read_bytes()))
    dt = directory / "diagnostic.dt"
    dt.write_bytes(struct.pack("<II", 1, 1) + property_bytes("name", b"\0")
                   + struct.pack("<II", 3, 0) + property_bytes("name", b"chosen\0")
                   + property_bytes("dram-base", struct.pack("<Q", 0x40000000))
                   + property_bytes("dram-size", struct.pack("<Q", 64 * 1024 * 1024)))
    template_dt = directory / "unresolved-template.dt"
    template_dt.write_bytes(struct.pack("<II", 2, 0) + property_bytes("name", b"\0")
                            + property_bytes("seed", b"provider.seed\0", template=True))
    cases = []
    for name, budget, efi, tree, payload in (("positive", 8, args.efi_trace, dt, kernel), ("budget", 1, args.efi_trace, dt, kernel),
                                  ("feature-gate", 8, args.efi_default, dt, kernel),
                                  ("unresolved-template", 8, args.efi_trace, template_dt, kernel),
                                  ("thread-registers", 8, args.efi_trace, dt, thread_kernel)):
        command = [sys.executable, str(tools / "trace_arm_jit_ovmf.py"), "--efi", str(efi.resolve()),
                   "--kernel", str(payload), "--device-tree", str(tree), "--output", str(directory / name),
                   "--physical-base", "0x40000000", "--virtual-base", "0xfffffe0000000000",
                   "--memory-size", "67108864", "--kernel-physical", "0x42000000",
                   "--instruction-budget", str(budget), "--allow-incomplete-sptm-prefix",
                   "--host-memory-mib", "256", "--timeout", "30"]
        status = subprocess.run(command, check=False).returncode
        report = json.loads((directory / name / "report.json").read_text())
        execution = report["execution"]
        if name in ("feature-gate", "unresolved-template"):
            passed = status == 1 and not report["diagnostic_completed"] and execution is None
            marker = "NXARMJIT: PROVIDERS_PENDING" if name == "feature-gate" else "NXARMJIT: TRACE_DT_UNRESOLVED templates=1 platform_complete=false"
            passed = passed and any(line.startswith(marker) for line in report["markers"])
            passed = passed and not any(line.startswith("NXARMJIT: TRACE_ENTER") for line in report["markers"])
        else:
            passed = status == 0 and report["diagnostic_completed"] and report["native_execution_observed"]
            registers = execution["registers"] if execution else {}
            if name == "positive":
                passed = passed and execution["status"] == 1 and execution["retired"] == 6
                passed = passed and registers["x0"] == 0 and registers["x1"] == registers["x2"] and registers["x3"] == 0x20002
            elif name == "budget":
                passed = passed and execution["status"] == 5 and execution["retired"] == 1
                passed = passed and registers["x0"] == 0 and registers["x2"] == 0 and registers["x3"] == 0x31
            else:
                passed = passed and execution["status"] == 1 and execution["retired"] == 7
                passed = passed and registers["x1"] > 0 and len(set(registers.values())) == 1
        cases.append({"name": name, "passed": bool(passed), "receipt": str(directory / name / "report.json")})
    after = {str(path.resolve()): sha256(path) for path in inputs}
    result = {"schema": "nextcore.authored-sptm-prefix.v1", "cases": cases,
              "input_sha256_before": before, "input_sha256_after": after,
              "passed": all(case["passed"] for case in cases) and before == after,
              "sptm_provided": False, "macos_boot_verified": False, "metal_verified": False}
    (directory / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
