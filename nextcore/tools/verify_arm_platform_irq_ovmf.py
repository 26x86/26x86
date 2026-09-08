#!/usr/bin/env python3
"""Verify actual x86 EFI provider and interrupt-vector state with authored ARM.

Interrupt returns commit guest vector/ELR/SPSR state. No handler instructions
are claimed to execute, and no Apple reset state or macOS boot is asserted.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
from build_arm64_handoff_probe import ENTRY_OFFSET, PHYSICAL, image, sha256


def prop(name: str, value: bytes) -> bytes:
    return name.encode().ljust(32, b"\0") + struct.pack("<I", len(value)) + value.ljust((len(value) + 3) & ~3, b"\0")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    source = tools / "arm64_platform_irq_probe.S"
    args.efi = args.efi.resolve(strict=True)
    inputs = [source, args.efi, Path(__file__).resolve(), tools / "trace_arm_jit_ovmf.py"]
    before = {str(path): sha256(path) for path in inputs}
    variants = {"readback": [], "invalid": ["PROBE_INVALID_WRITE"], "pending": ["PROBE_PENDING"],
                "unmask": ["PROBE_PENDING", "PROBE_UNMASK"], "irq": ["PROBE_DAIF_IRQ"], "fiq": ["PROBE_DAIF_FIQ"]}
    images = {}
    for variant, definitions in variants.items():
        obj, raw, kernel = (output / f"{variant}.{suffix}" for suffix in ("o", "bin", "kc"))
        subprocess.run(["clang", "--target=aarch64-none-elf", *[f"-D{name}" for name in definitions], "-c", str(source), "-o", str(obj)], check=True)
        subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.text", str(obj), str(raw)], check=True)
        kernel.write_bytes(image(raw.read_bytes()))
        images[variant] = kernel
    tree = output / "diagnostic.dt"
    tree.write_bytes(struct.pack("<II", 1, 1) + prop("name", b"\0")
                     + struct.pack("<II", 3, 0) + prop("name", b"chosen\0")
                     + prop("dram-base", struct.pack("<Q", 0x40000000))
                     + prop("dram-size", struct.pack("<Q", 67108864)))
    vector = 0x40020000
    entry = PHYSICAL + ENTRY_OFFSET
    # Expected state derives from the authored instruction order and public
    # exception vector offsets, not from the runtime implementation output.
    cases = [
        dict(name="readback", variant="readback", profile=True, override=0, pstate=0x3c5, irq=0, fiq=0, status=1, retired=6, final_override=0xa00000),
        dict(name="absent-provider", variant="readback", profile=False, override=0, pstate=0x3c5, irq=0, fiq=0, status=13, retired=1, final_override=0),
        dict(name="unsupported-field", variant="invalid", profile=True, override=0xa00000, pstate=0x3c5, irq=0, fiq=0, status=13, retired=2, final_override=0xa00000),
        dict(name="masked-levels", variant="pending", profile=True, override=0xa00000, pstate=0x3c5, irq=1, fiq=1, status=1, retired=4, final_override=0xa00000),
        dict(name="override-release-irq-el1t", variant="unmask", profile=True, override=0xa00000, pstate=0x3c4, irq=1, fiq=0, status=15, retired=4, final_override=0, vector=vector+0x80, spsr=0x304),
        dict(name="override-release-fiq-el1h", variant="unmask", profile=True, override=0xa00000, pstate=0x3c5, irq=1, fiq=1, status=18, retired=4, final_override=0, vector=vector+0x300, spsr=0x305),
        dict(name="daif-irq-only", variant="irq", profile=True, override=0, pstate=0x3c5, irq=1, fiq=1, status=15, retired=2, final_override=0, vector=vector+0x280, spsr=0x345),
        dict(name="daif-fiq-only", variant="fiq", profile=True, override=0, pstate=0x3c5, irq=1, fiq=1, status=18, retired=2, final_override=0, vector=vector+0x300, spsr=0x385),
    ]
    results = []
    for case in cases:
        command = [sys.executable, str(tools / "trace_arm_jit_ovmf.py"), "--efi", str(args.efi),
                   "--kernel", str(images[case["variant"]]), "--device-tree", str(tree),
                   "--output", str(output / case["name"]), "--physical-base", "0x40000000",
                   "--virtual-base", "0xfffffe0000000000", "--memory-size", "67108864",
                   "--kernel-physical", "0x42000000", "--instruction-budget", "8",
                   "--allow-incomplete-sptm-prefix", "--host-memory-mib", "256", "--timeout", "30"]
        if case["profile"]:
            command += ["--platform-profile", "nextcore-irq-compat-v1", "--vector-base", str(vector),
                        "--initial-override", str(case["override"]), "--initial-pstate", str(case["pstate"]),
                        "--irq-level", str(case["irq"]), "--fiq-level", str(case["fiq"])]
        status = subprocess.run(command, check=False).returncode
        receipt = json.loads((output / case["name"] / "report.json").read_text())
        execution = receipt["execution"] or {}
        platform = execution.get("platform") or {}
        exception = execution.get("exception") or {}
        registers = execution.get("registers") or {}
        checks = {
            "diagnostic_completed": status == 0 and receipt["diagnostic_completed"],
            "native_executed": receipt["native_execution_observed"],
            "status": execution.get("status") == case["status"],
            "retired": execution.get("retired") == case["retired"],
            "profile": platform.get("profile") == int(case["profile"]),
            "override": platform.get("override") == case["final_override"],
            "pending_preserved": platform.get("pending") == case["irq"] + 2 * case["fiq"],
            "marker_register": registers.get("x3") == 0x31,
            "esr_not_written": exception.get("esr") == 0 if "vector" in case else True,
        }
        if "vector" in case:
            checks.update(vector=execution.get("pc") == case["vector"] == exception.get("vector"),
                          saved_pc=exception.get("elr") == entry + case["retired"] * 4,
                          saved_pstate=exception.get("spsr") == case["spsr"],
                          entered_el1h_masked=platform.get("pstate") == 0x3c5,
                          no_fault_word=execution.get("fault_instruction") == 0)
        else:
            checks["no_async_vector"] = exception.get("vector") == 0
        if case["name"] == "readback":
            checks["provider_readback"] = registers.get("x2") == 0 and registers.get("x1") == 0xa00000
        if case["variant"] in ("pending", "unmask"):
            checks["masked_value_readback"] = registers.get("x2") == 0xa00000
        if case["status"] == 13:
            checks["fault_pc"] = execution.get("pc") == entry + case["retired"] * 4
            checks["fault_word_present"] = execution.get("fault_instruction", 0) != 0
        result = {"name": case["name"], "passed": all(checks.values()), "checks": checks,
                  "receipt": str(output / case["name"] / "report.json"), "handler_executed": False}
        results.append(result)
        print(json.dumps(result), flush=True)
    after = {str(path): sha256(path) for path in inputs}
    result = {"schema": "nextcore.efi-platform-irq.v1", "cases": results,
              "input_sha256_before": before, "input_sha256_after": after,
              "passed": before == after and all(case["passed"] for case in results),
              "profile_reset_origin": "software_defined", "handler_executed": False,
              "sptm_provided": False, "macos_boot_verified": False, "metal_verified": False}
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"report": str(output / "report.json"), "passed": result["passed"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
