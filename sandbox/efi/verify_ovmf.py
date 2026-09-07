#!/usr/bin/env python3
"""Execute the single EFI package under OVMF; QEMU is validation-only."""
import hashlib
import json
import pathlib
import re
import shutil
import struct
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
ALLOCATION_PATTERN = re.compile(
    r"VF: EFI_ALLOCATIONS count=(0x[0-9a-f]+) bytes=(0x[0-9a-f]+)", re.IGNORECASE
)
NORMAL_TRACE = [
    "VF: EFI_ENTRY",
    "VF: EFI_MEMORY_READY",
    "VF: PREOS_CONTEXT_READY",
    "VF: RUST_ENTER",
    "VF: RUST_POLICY_OK",
    "VF: MACHINE_RESET",
    "VF: AARCH64_STATE_READY",
    "VF: VMAPPLE_GRAPH_READY",
    "VF: M1_GRAPH_READY",
    "VF: MACHINE_READY",
    "VF: JIT_ENTER",
    "VF: GUEST_HALT",
    "VF: RUST_RETURN_OK",
    "VF: EFI_RETURN_OK",
]


def ordered(log, markers):
    position = -1
    for marker in markers:
        position = log.find(marker, position + 1)
        if position < 0:
            return False
    return True


def allocation_measurement(log):
    match = ALLOCATION_PATTERN.search(log)
    if not match:
        return None
    return {"count": int(match.group(1), 16), "bytes": int(match.group(2), 16)}


def fixture_words(kind):
    if kind == "normal":
        return [0xd2800140, 0xd1000400, 0xb5ffffe0, 0xd4400000]
    if kind == "undefined-instruction":
        return [0xffffffff]
    if kind == "privileged-instruction":
        return [0xd69f03e0]
    if kind == "system-register-trap":
        return [0xd53be000]
    if kind == "instruction-abort":
        return [0x14000001]
    if kind == "alignment-fault":
        return [0xd2800021, 0xf9000020]
    if kind == "data-abort":
        return [0xd2a00201, 0xf9000020]
    if kind == "budget-exhaustion":
        return [0x14000000]
    return None


def run_case(case):
    with tempfile.TemporaryDirectory(prefix="26x86-efi-") as tmp:
        root = pathlib.Path(tmp)
        boot = root / "esp" / "EFI" / "BOOT"
        boot.mkdir(parents=True)
        shutil.copyfile(ROOT / "build" / "TESTX64.EFI", boot / "BOOTX64.EFI")
        words = fixture_words(case["guest"])
        if words is not None:
            guest = root / "esp" / "EFI" / "26x86" / "guest.a64"
            guest.parent.mkdir()
            guest.write_bytes(struct.pack("<" + "I" * len(words), *words))
        shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", root / "vars.fd")
        command = [
            "qemu-system-x86_64", "-machine", "q35,accel=tcg", "-cpu", case["cpu"], "-m", "512",
            "-smp", "1", "-display", "none", "-serial", "none", "-monitor", "none",
            "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
            "-drive", f"if=pflash,format=raw,file={root / 'vars.fd'}",
            "-drive", f"format=raw,file=fat:rw:{root / 'esp'}",
            "-debugcon", f"file:{root / 'debug.log'}", "-device",
            "isa-debug-exit,iobase=0xf4,iosize=0x04", "-net", "none", "-no-reboot",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
        log = (root / "debug.log").read_text(errors="replace")
    measured = allocation_measurement(log)
    passed = completed.returncode == case["exit"]
    if case["kind"] == "normal":
        passed = passed and ordered(log, NORMAL_TRACE)
        passed = passed and "VF: EFI_RETURN_ERROR" not in log
        if case["guest"] is None:
            passed = passed and "JIT SELFTEST PASS" in log
        else:
            passed = passed and "GUEST HALT: own-code A64 guest completed." in log
        passed = passed and measured == {"count": 3, "bytes": 0x25000}
    elif case["kind"] == "guest-failure":
        failure_trace = [
            "VF: EFI_ENTRY", "VF: EFI_MEMORY_READY", "VF: PREOS_CONTEXT_READY", "VF: RUST_ENTER",
            "VF: RUST_POLICY_OK", "VF: MACHINE_RESET", "VF: AARCH64_STATE_READY",
            "VF: VMAPPLE_GRAPH_READY", "VF: M1_GRAPH_READY", "VF: MACHINE_READY", "VF: JIT_ENTER", case["stop_marker"],
            case["preos_marker"], "VF: EFI_RETURN_ERROR",
        ]
        passed = passed and ordered(log, failure_trace)
        passed = passed and "VF: GUEST_HALT" not in log and "VF: RUST_RETURN_OK" not in log
        passed = passed and "VF: EFI_RETURN_OK" not in log
        passed = passed and measured == {"count": 3, "bytes": 0x25000}
    else:
        passed = passed and "UNSUPPORTED CPU" in log and "VF: RUST_ENTER" not in log
    return {
        "name": case["name"],
        "cpu_model": case["cpu"],
        "guest_case": case["guest"] or "built-in-golden",
        "qemu_exit": completed.returncode,
        "expected_qemu_exit": case["exit"],
        "boot_services_allocations": measured,
        "passed": passed,
        "log": log,
        "stderr": completed.stderr,
    }


def main():
    cases = [
        {"name": "built-in-golden-halt", "kind": "normal", "cpu": "Nehalem", "guest": None, "exit": 33},
        {"name": "external-own-code-halt", "kind": "normal", "cpu": "Nehalem", "guest": "normal", "exit": 33},
        {
            "name": "undefined-aarch64-instruction", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "undefined-instruction", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=UNDEFINED_INSTRUCTION",
            "preos_marker": "VF: PREOS_FAIL code=UNSUPPORTED",
        },
        {
            "name": "el0-privileged-instruction", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "privileged-instruction", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=PRIVILEGE_FAULT",
            "preos_marker": "VF: PREOS_FAIL code=UNSUPPORTED",
        },
        {
            "name": "el0-system-register-trap", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "system-register-trap", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=SYSTEM_REGISTER_TRAP",
            "preos_marker": "VF: PREOS_FAIL code=UNSUPPORTED",
        },
        {
            "name": "guest-instruction-abort", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "instruction-abort", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=INSTRUCTION_ABORT",
            "preos_marker": "VF: PREOS_FAIL code=JIT",
        },
        {
            "name": "guest-alignment-fault", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "alignment-fault", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=ALIGNMENT_FAULT",
            "preos_marker": "VF: PREOS_FAIL code=UNSUPPORTED",
        },
        {
            "name": "guest-data-abort", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "data-abort", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=DATA_ABORT",
            "preos_marker": "VF: PREOS_FAIL code=JIT",
        },
        {
            "name": "bounded-loop-budget-exhaustion", "kind": "guest-failure", "cpu": "Nehalem",
            "guest": "budget-exhaustion", "exit": 35,
            "stop_marker": "VF: GUEST_STOP reason=BUDGET_EXHAUSTED",
            "preos_marker": "VF: PREOS_FAIL code=BUDGET",
        },
        {"name": "pre-sse4-host-rejection", "kind": "host-rejection", "cpu": "Conroe", "guest": None, "exit": 37},
    ]
    results = [run_case(case) for case in cases]
    report = {
        "schema": 2,
        "passed": all(result["passed"] for result in results),
        "cpu_model": "Nehalem",
        "avx_available": False,
        "boot_environment": "OVMF UEFI (no Linux guest, no product QEMU runtime dependency)",
        "instrumented_artifact_sha256": hashlib.sha256((ROOT / "build" / "TESTX64.EFI").read_bytes()).hexdigest(),
        "production_artifact_sha256": hashlib.sha256((ROOT / "build" / "BOOTX64.EFI").read_bytes()).hexdigest(),
        "layer_status": {
            "firmware_efi": "passed" if all(result["passed"] for result in results) else "failed",
            "rust_preos": "passed" if all(result["passed"] for result in results[:-1]) else "failed",
            "aarch64_jit": "passed" if all(result["passed"] for result in results[:-1]) else "failed",
            "native_machine": "partial: synchronized M1-only T8103 contract graph plus Phase-2 VfMachine/VMApple descriptor; Apple physical MMIO/register evidence is not claimed",
            "apple_boot_chain": "not attempted",
            "macos": "not attempted",
        },
        "macos_boot_verified": False,
        "physical_m1_compatibility": False,
        "physical_mac_verified": False,
        "cases": results,
    }
    (ROOT / "build" / "ovmf-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
