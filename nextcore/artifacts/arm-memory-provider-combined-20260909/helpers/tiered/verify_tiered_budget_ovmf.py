#!/usr/bin/env python3
"""Verify the opt-in 256-instruction x86 EFI diagnostic and rejection bounds."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys


def property_bytes(name, value):
    return (
        name.encode().ljust(32, b"\0")
        + struct.pack("<I", len(value))
        + value.ljust((len(value) + 3) & ~3, b"\0")
    )


def run(command, log):
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    log.write_text(result.stdout + result.stderr)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--efi", type=Path, required=True)
    parser.add_argument("--default-efi", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tools = args.tools.resolve(strict=True)
    source = Path(__file__).resolve().parent
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(tools))
    from build_arm64_handoff_probe import image

    obj, raw = output / "loop.o", output / "loop.bin"
    kernel, dt = output / "loop.kc", output / "diagnostic.dt"
    subprocess.run(
        ["clang", "--target=aarch64-none-elf", "-c",
         str(source / "tiered_budget_probe.S"), "-o", str(obj)],
        check=True,
    )
    subprocess.run(
        ["llvm-objcopy", "-O", "binary", "--only-section=.text", str(obj), str(raw)],
        check=True,
    )
    kernel.write_bytes(image(raw.read_bytes()))
    dt.write_bytes(
        struct.pack("<II", 1, 1) + property_bytes("name", b"\0")
        + struct.pack("<II", 3, 0) + property_bytes("name", b"chosen\0")
        + property_bytes("dram-base", struct.pack("<Q", 0x40000000))
        + property_bytes("dram-size", struct.pack("<Q", 67108864))
    )
    # All inputs are independently authored. These physical coordinates have
    # no relationship to any original OS image.
    base = [
        sys.executable, str(tools / "trace_arm_jit_ovmf.py"),
        "--kernel", str(kernel), "--device-tree", str(dt),
        "--physical-base", "0x40000000",
        "--virtual-base", "0xfffffe0000000000",
        "--memory-size", "67108864", "--kernel-physical", "0x42000000",
        "--allow-incomplete-sptm-prefix", "--host-memory-mib", "256",
        "--timeout", "30",
    ]
    cases = []
    rejected = [
        ("default256", 256, True, False),
        ("unsupported65", 65, True, True),
        ("unsupported512", 512, True, True),
        ("excess4097", 4097, True, True),
        ("absent9", 9, False, True),
        ("absent256", 256, False, True),
    ]
    for name, budget, profile, extended in rejected:
        command = base + ["--efi", str(args.efi), "--output", str(output / name),
                          "--instruction-budget", str(budget)]
        if profile:
            command += ["--platform-profile", "nextcore-irq-compat-v1"]
        if extended:
            command += ["--tiered-diagnostic"]
        code = run(command, output / (name + ".log"))
        cases.append({"name": name, "passed": code == 2 and not (output / name).exists(),
                      "returncode": code})

    for name, efi, accept in [
        ("tiered256", args.efi, True),
        ("default-firmware256", args.default_efi, False),
    ]:
        command = base + [
            "--efi", str(efi), "--output", str(output / name),
            "--instruction-budget", "256",
            "--platform-profile", "nextcore-irq-compat-v1", "--tiered-diagnostic",
        ]
        code = run(command, output / (name + ".log"))
        receipt = output / name / "report.json"
        if not receipt.is_file():
            cases.append({"name": name, "passed": False,
                          "error": "Firmware tool produced no receipt", "returncode": code})
            continue
        result = json.loads(receipt.read_text())
        execution = result.get("execution") or {}
        registers = execution.get("registers") or {}
        exception = execution.get("exception") or {}
        if accept:
            checks = {
                "exit": code == 0,
                "completed": result["diagnostic_completed"],
                "build_marker": result["tiered_diagnostic_build_observed"],
                "budget": execution.get("status") == 5,
                "exact_retirement": execution.get("retired") == 256,
                "loop_readback": registers.get("x0") == 128
                    and registers.get("x2") == 0 and registers.get("x3") == 0x29,
                "native_blocks": execution.get("compiled_blocks", 0) > 0,
                "no_fault_word": execution.get("fault_instruction") == 0,
                "no_exception": exception.get("esr") == 0 and exception.get("vector") == 0,
                "inputs": result["original_inputs_preserved"] and result["esp_copies_preserved"],
            }
        else:
            checks = {
                "exit": code == 1,
                "config_rejected": any("TRACE_CONFIG_INVALID" in x for x in result["markers"]),
                "no_guest_entry": not any("TRACE_ENTER " in x for x in result["markers"]),
                "no_execution": result["execution"] is None,
                "inputs": result["original_inputs_preserved"] and result["esp_copies_preserved"],
            }
        cases.append({"name": name, "passed": all(checks.values()), "checks": checks,
                      "status": execution.get("status"), "retired": execution.get("retired"),
                      "compiled_blocks": execution.get("compiled_blocks")})

    report = {
        "schema": "nextcore.tiered-efi-budget.v1",
        "passed": all(case["passed"] for case in cases),
        "cases": cases,
        "efi_sha256": hashlib.sha256(args.efi.read_bytes()).hexdigest(),
        "default_efi_sha256": hashlib.sha256(args.default_efi.read_bytes()).hexdigest(),
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [Path(__file__), source / "tiered_budget_probe.S",
                         tools / "trace_arm_jit_ovmf.py"]
        },
        "macos_boot_verified": False,
        "metal_verified": False,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
