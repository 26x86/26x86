#!/usr/bin/env python3
"""Authored native x86 EFI pair-memory and SP-alignment ABI checks."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prop(name: str, value: bytes) -> bytes:
    return name.encode().ljust(32, b"\0") + struct.pack("<I", len(value)) + value.ljust((len(value) + 3) & ~3, b"\0")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.efi = args.efi.resolve(strict=True)
    args.tools = args.tools.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.tools))
    from build_arm64_handoff_probe import image, PHYSICAL, ENTRY_OFFSET

    source = Path(__file__).resolve().with_name("arm64_pair_probe.S")
    inputs = [args.efi, source, Path(__file__).resolve(), args.tools / "trace_arm_jit_ovmf.py",
              args.tools / "build_arm64_handoff_probe.py"]
    before = {str(p): digest(p) for p in inputs}
    dt = output / "diagnostic.dt"
    dt.write_bytes(struct.pack("<II", 1, 1) + prop("name", b"\0")
                   + struct.pack("<II", 3, 0) + prop("name", b"chosen\0")
                   + prop("dram-base", struct.pack("<Q", 0x40000000))
                   + prop("dram-size", struct.pack("<Q", 67108864)))
    results = []
    # Every fixture uses the same image layout and handoff allocation. The
    # successful case independently captures and restores the initial SP.
    initial_stack = None
    for name, definition in [("pair-readback", None), ("sp-store-fault", "PROBE_SP_STORE"),
                              ("sp-load-fault", "PROBE_SP_LOAD"),
                              ("invalid-writeback-pair", "PROBE_INVALID_PAIR"),
                              ("a0-device-store-fault", "PROBE_DATA_STORE"),
                              ("a0-device-load-fault", "PROBE_DATA_LOAD")]:
        obj, raw, kernel = (output / f"{name}.{suffix}" for suffix in ("o", "bin", "kc"))
        command = ["clang", "--target=aarch64-none-elf", "-c", str(source), "-o", str(obj)]
        if definition:
            command += [f"-D{definition}"]
        subprocess.run(command, check=True)
        subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.text", str(obj), str(raw)], check=True)
        symbols = {}
        for line in subprocess.check_output(["llvm-nm", "-n", str(obj)], text=True).splitlines():
            fields = line.split()
            if len(fields) == 3:
                symbols[fields[2]] = int(fields[0], 16)
        kernel.write_bytes(image(raw.read_bytes()))
        case_output = output / name
        command = [sys.executable, str(args.tools / "trace_arm_jit_ovmf.py"), "--efi", str(args.efi),
                   "--kernel", str(kernel), "--device-tree", str(dt), "--output", str(case_output),
                   "--physical-base", "0x40000000", "--virtual-base", "0xfffffe0000000000",
                   "--memory-size", "67108864", "--kernel-physical", "0x42000000",
                   "--instruction-budget", "64", "--platform-profile", "nextcore-irq-compat-v1",
                   "--allow-incomplete-sptm-prefix", "--host-memory-mib", "256", "--timeout", "30"]
        status = subprocess.run(command, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False).returncode
        receipt = json.loads((case_output / "report.json").read_text())
        execution = receipt.get("execution") or {}
        regs = execution.get("registers") or {}
        platform = execution.get("platform") or {}
        exception = execution.get("exception") or {}
        checks = {"diagnostic_completed": status == 0 and receipt["diagnostic_completed"],
                  "native_executed": receipt["native_execution_observed"],
                  "marker": regs.get("x3") == 0x31,
                  "no_async_vector": exception.get("vector") == 0,
                  "no_pending_lines": platform.get("pending") == 0,
                  "inputs_preserved": receipt["original_inputs_preserved"] and receipt["esp_copies_preserved"]}
        if definition in ("PROBE_DATA_STORE", "PROBE_DATA_LOAD"):
            offset = symbols["probe_fault"]
            word = struct.unpack_from("<I", raw.read_bytes(), offset)[0]
            expected_esr = 0x96000061 if definition == "PROBE_DATA_STORE" else 0x96000021
            checks.update(device_alignment_status=execution.get("status") == 12,
                          device_alignment_syndrome=exception.get("esr") == expected_esr,
                          no_fault_retirement=execution.get("retired") == offset // 4,
                          precise_fault_pc=execution.get("pc") == PHYSICAL + ENTRY_OFFSET + offset,
                          precise_fault_word=execution.get("fault_instruction") == word,
                          full_destinations_preserved=regs.get("x0") == 0xaaaa000000007777 and regs.get("x1") == 0xbbbb000000008888,
                          no_base_writeback=initial_stack is not None and regs.get("x2") == initial_stack + 1,
                          stack_unchanged=initial_stack is not None and platform.get("sp") == initial_stack)
        elif definition == "PROBE_INVALID_PAIR":
            offset = symbols["probe_fault"]
            word = struct.unpack_from("<I", raw.read_bytes(), offset)[0]
            checks.update(undefined_status=execution.get("status") == 8,
                          undefined_syndrome=exception.get("esr") == 0,
                          no_fault_retirement=execution.get("retired") == offset // 4,
                          precise_fault_pc=execution.get("pc") == PHYSICAL + ENTRY_OFFSET + offset,
                          precise_fault_word=execution.get("fault_instruction") == word,
                          registers_unchanged=regs.get("x0") == regs.get("x2") and regs.get("x1") == 0x8888,
                          no_writeback=platform.get("sp") == regs.get("x2"))
        elif definition:
            offset = symbols["probe_fault"]
            word = struct.unpack_from("<I", raw.read_bytes(), offset)[0]
            checks.update(sp_alignment_status=execution.get("status") == 19,
                          sp_alignment_syndrome=exception.get("esr") == ((0x26 << 26) | (1 << 25)),
                          no_fault_retirement=execution.get("retired") == offset // 4,
                          precise_fault_pc=execution.get("pc") == PHYSICAL + ENTRY_OFFSET + offset,
                          precise_fault_word=execution.get("fault_instruction") == word,
                          registers_unchanged=regs.get("x0") == 0x7777 and regs.get("x1") == 0x8888,
                          no_writeback=platform.get("sp") == regs.get("x2", 0) + 8)
        else:
            expected_retired = symbols["probe_success"] // 4 + 1
            checks.update(halt=execution.get("status") == 1,
                          complete_authored_path=execution.get("retired") == expected_retired,
                          value_readback=regs.get("x0") == 0x4444333322221111 and regs.get("x1") == 0x8888777766665555,
                          stack_restored=platform.get("sp") == regs.get("x2"),
                          no_fault_word=execution.get("fault_instruction") == 0)
            if all(checks.values()):
                initial_stack = regs["x2"]
        result = {"name": name, "passed": all(checks.values()), "checks": checks,
                  "status": execution.get("status"), "retired": execution.get("retired"),
                  "compiled_blocks": execution.get("compiled_blocks"), "receipt": str(case_output / "report.json")}
        results.append(result)
        print(json.dumps(result), flush=True)
    after = {str(p): digest(p) for p in inputs}
    report = {"schema": "nextcore.efi-pair-memory.v1", "cases": results,
              "input_sha256_before": before, "input_sha256_after": after,
              "passed": before == after and all(r["passed"] for r in results),
              "far_observed": False, "guest_ram_after_fault_observed": False,
              "sptm_provided": False, "macos_boot_verified": False, "metal_verified": False}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(output / "report.json"), "passed": report["passed"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
