#!/usr/bin/env python3
"""Bounded, opt-in incomplete SPTM prefix diagnostic inside x86 OVMF EFI.

This records an actual fault or instruction-budget return; it does not provide
SPTM services, a platform device tree, authentication, or a macOS boot result.
Original-image addresses and instruction words belong in a private output path.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import time
from verify_arm_jit_ovmf import lines, ordered


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("efi", "kernel", "device-tree", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("physical-base", "virtual-base", "memory-size", "kernel-physical"):
        parser.add_argument(f"--{name}", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--instruction-budget", type=int, default=8)
    parser.add_argument("--platform-profile", choices=["nextcore-irq-compat-v1"])
    for name in ("initial-override", "initial-pstate", "vector-base", "irq-level", "fiq-level"):
        parser.add_argument(f"--{name}", type=lambda value: int(value, 0))
    parser.add_argument("--allow-incomplete-sptm-prefix", action="store_true", required=True)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--host-memory-mib", type=int, default=768)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    args = parser.parse_args()
    maximum_budget = 64 if args.platform_profile else 8
    if not 1 <= args.instruction_budget <= maximum_budget:
        parser.error(f"selected diagnostic budget must be 1..{maximum_budget}")
    platform_fields = {"InitialOverride": "initial_override", "InitialPstate": "initial_pstate",
                       "VectorBase": "vector_base", "IrqLevel": "irq_level", "FiqLevel": "fiq_level"}
    platform_options = {key: getattr(args, field) for key, field in platform_fields.items() if getattr(args, field) is not None}
    if platform_options and not args.platform_profile:
        parser.error("platform options require explicit --platform-profile")
    if any(not 0 <= value < 2**64 for value in platform_options.values()):
        parser.error("platform option values must be unsigned 64-bit integers")
    if not 0 < args.timeout <= 600 or not 256 <= args.host_memory_mib <= 4096:
        parser.error("timeout must be (0,600] and host RAM 256..4096 MiB")
    if args.memory_size < 16 * 1024 * 1024 or args.memory_size > 1024**3:
        parser.error("guest RAM must be 16 MiB..1 GiB")
    for field in ("physical_base", "virtual_base", "memory_size", "kernel_physical"):
        value = getattr(args, field)
        if not 0 <= value < 2**64 or value % 16384:
            parser.error(f"{field} must be an aligned 64-bit value")
    args.qemu = shutil.which(args.qemu) or args.qemu
    inputs = []
    for field in ("efi", "kernel", "device_tree", "ovmf_code", "ovmf_vars"):
        path = getattr(args, field).resolve(strict=True)
        if not path.is_file() or "," in str(path):
            parser.error(f"{field} must be a regular path without comma")
        setattr(args, field, path)
        inputs.append(path)
    if args.kernel.stat().st_size > 128 * 1024 * 1024 or not 0 < args.device_tree.stat().st_size <= 1024 * 1024:
        parser.error("kernel or diagnostic DT exceeds firmware input bounds")
    output = args.output.resolve()
    if "," in str(output):
        parser.error("output must not contain comma")
    output.mkdir(parents=True, exist_ok=False)
    before = {str(path): digest(path) for path in inputs}
    boot = output / "esp/EFI/BOOT"
    payload = output / "esp/EFI/NEXTCORE"
    oc = output / "esp/EFI/OC"
    for directory in (boot, payload, oc):
        directory.mkdir(parents=True)
    shutil.copyfile(args.efi, boot / "BOOTX64.EFI")
    shutil.copyfile(args.kernel, payload / "kernel.kc")
    shutil.copyfile(args.device_tree, payload / "diagnostic.dt")
    trace = {
        "HandoffAbi": "unprovisioned-sptm-prefix",
        "PhysicalBase": args.physical_base,
        "VirtualBase": args.virtual_base,
        "MemorySize": args.memory_size,
        "ActualMemorySize": args.memory_size,
        "KernelPhysical": args.kernel_physical,
        "InstructionBudget": args.instruction_budget,
        "DeviceTreePath": "\\EFI\\NEXTCORE\\diagnostic.dt",
    }
    if args.platform_profile:
        trace["PlatformProfile"] = args.platform_profile
        if platform_options:
            trace["Platform"] = platform_options
    config = {"Nextcore": {"Kernel": {
        "Profile": "x86-efi-arm64-trace", "Path": "\\EFI\\NEXTCORE\\kernel.kc",
        "Arguments": "-v", "Trace": trace,
    }}}
    (oc / "config.plist").write_bytes(plistlib.dumps(config))
    variables = output / "vars.fd"
    shutil.copyfile(args.ovmf_vars, variables)
    serial = output / "serial.log"
    command = [args.qemu, "-machine", "q35,accel=tcg,smm=off", "-cpu", "Nehalem",
               "-m", str(args.host_memory_mib), "-smp", "1", "-display", "none",
               "-vga", "std", "-monitor", "none", "-serial", f"file:{serial}",
               "-net", "none", "-no-reboot",
               "-drive", f"if=pflash,format=raw,readonly=on,file={args.ovmf_code}",
               "-drive", f"if=pflash,format=raw,file={variables}",
               "-drive", f"format=raw,file=fat:rw:{output / 'esp'}"]
    (output / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    expected = ["NXARMJIT: EFI_ENTRY", "NXARMJIT: CONFIG_PARSED", "NXARMJIT: KC_VALIDATED",
                "NXARMJIT: TRACE_STAGING_VERIFIED", "NXARMJIT: TRACE_HANDOFF_UNPROVISIONED",
                "NXARMJIT: TRACE_ENTER", "NXARMJIT: TRACE_RETURN", "NXARMJIT: TRACE_ONLY",
                "NXARMJIT: ERROR status=ABORTED"]
    start = time.monotonic()
    failure = None
    process = None
    stopped = False
    try:
        with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            while process.poll() is None and time.monotonic() - start < args.timeout:
                actual = lines(serial)
                if any(line.startswith("NXARMJIT: ERROR") for line in actual):
                    break
                time.sleep(.1)
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        if process is not None and process.poll() is None:
            stopped = True
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    actual = lines(serial)
    returned = next((line for line in actual if line.startswith("NXARMJIT: TRACE_RETURN ")), "")
    match = re.fullmatch(r"NXARMJIT: TRACE_RETURN status=(-?\d+) retired=(\d+) pc=(0x[0-9a-f]+) blocks=(\d+) instruction=(0x[0-9a-f]+)", returned)
    execution = None
    if match:
        execution = dict(zip(("status", "retired", "pc", "compiled_blocks", "fault_instruction"),
                             (int(value, 0) for value in match.groups())))
        registers = next((line for line in actual if line.startswith("NXARMJIT: TRACE_REGISTERS ")), "")
        register_match = re.fullmatch(r"NXARMJIT: TRACE_REGISTERS x0=(0x[0-9a-f]+) x1=(0x[0-9a-f]+) x2=(0x[0-9a-f]+) x3=(0x[0-9a-f]+)", registers)
        execution["registers"] = dict(zip(("x0", "x1", "x2", "x3"), (int(value, 16) for value in register_match.groups()))) if register_match else None
        platform_line = next((line for line in actual if line.startswith("NXARMJIT: TRACE_PLATFORM_STATE ")), "")
        platform_match = re.fullmatch(r"NXARMJIT: TRACE_PLATFORM_STATE profile=(\d+) override=(0x[0-9a-f]+) pending=(\d+) pstate=(0x[0-9a-f]+) sp=(0x[0-9a-f]+)", platform_line)
        execution["platform"] = dict(zip(("profile", "override", "pending", "pstate", "sp"), (int(value, 0) for value in platform_match.groups()))) if platform_match else None
        exception_line = next((line for line in actual if line.startswith("NXARMJIT: TRACE_EXCEPTION_STATE ")), "")
        exception_match = re.fullmatch(r"NXARMJIT: TRACE_EXCEPTION_STATE elr=(0x[0-9a-f]+) spsr=(0x[0-9a-f]+) vector=(0x[0-9a-f]+) esr=(0x[0-9a-f]+) handler_executed=false", exception_line)
        execution["exception"] = dict(zip(("elr", "spsr", "vector", "esr"), (int(value, 16) for value in exception_match.groups()))) if exception_match else None
    after = {str(path): digest(path) for path in inputs}
    copies_unchanged = digest(payload / "kernel.kc") == before[str(args.kernel)] and digest(payload / "diagnostic.dt") == before[str(args.device_tree)]
    completed = (ordered(actual, expected) and execution is not None
                 and execution["retired"] <= args.instruction_budget and execution["registers"] is not None
                 and before == after and copies_unchanged and failure is None)
    if args.platform_profile:
        completed = completed and bool(execution and execution["platform"] and execution["platform"]["profile"] == 1
                                       and execution["exception"] is not None)
    receipt = {
        "schema": "nextcore.x86-efi-arm-trace.v1", "host_architecture": platform.machine(),
        "handoff_abi": "unprovisioned-sptm-prefix", "sptm_args_provided": False,
        "platform_profile": args.platform_profile, "profile_reset_origin": "software_defined" if args.platform_profile else "unprovided",
        "sptm_services_provided": False, "platform_device_tree_provided": False,
        "config": config, "execution": execution,
        "markers": [line for line in actual if line.startswith("NXARMJIT:")],
        "input_sha256_before": before, "input_sha256_after": after,
        "original_inputs_preserved": before == after, "esp_copies_preserved": copies_unchanged,
        "diagnostic_completed": completed,
        "native_execution_observed": bool(execution and execution["retired"] > 0 and execution["compiled_blocks"] > 0),
        "elapsed_seconds": round(time.monotonic() - start, 3), "failure": failure,
        "qemu_exit_code": process.returncode if process else None,
        "stopped_by_harness": stopped, "macos_boot_verified": False, "metal_verified": False,
    }
    (output / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"report": str(output / "report.json"), "diagnostic_completed": completed,
                      "native_execution_observed": receipt["native_execution_observed"], "failure": failure}))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
