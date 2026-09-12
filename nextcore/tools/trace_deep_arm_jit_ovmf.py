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
import sys


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def parse_trace_video(actual: list[str], requested: bool, physical_base: int, memory_size: int) -> dict:
    """Keep acknowledged framebuffer configuration and successful presentation distinct.

    Missing markers include old EFI consumers that ignore the new selector. These
    never validate requested video even when bounded guest execution completed.
    """
    ready_lines = [line for line in actual if line.startswith("NXARMJIT: TRACE_VIDEO_READY")]
    unavailable = [line for line in actual if line.startswith("NXARMJIT: TRACE_VIDEO_UNAVAILABLE")]
    presented_lines = [line for line in actual if line.startswith("NXARMJIT: TRACE_VIDEO_PRESENTED")]
    geometry = None
    if len(ready_lines) == 1:
        match = re.fullmatch(
            r"NXARMJIT: TRACE_VIDEO_READY width=(\d+) height=(\d+) base=(0x[0-9a-fA-F]+) row_bytes=(\d+)(?: bytes=(\d+))?",
            ready_lines[0])
        if match:
            width, height, base, row_bytes, size = match.groups()
            width, height, row_bytes = int(width), int(height), int(row_bytes)
            base = int(base, 16)
            span = row_bytes * height
            if (0 < width <= 0xffffffff and 0 < height <= 0xffffffff and row_bytes >= width * 4
                    and row_bytes % 4 == 0 and physical_base <= base < 2**64
                    and base + span <= physical_base + memory_size < 2**64
                    and (size is None or int(size) >= span and base + int(size) <= physical_base + memory_size)):
                geometry = {"width": width, "height": height, "base": base, "row_bytes": row_bytes,
                            "visible_span_bytes": span, "allocation_bytes": int(size) if size else None}
    configured = requested and geometry is not None and not unavailable
    presented = (configured and presented_lines == ["NXARMJIT: TRACE_VIDEO_PRESENTED status=SUCCESS"]
                 and actual.index(ready_lines[0]) < actual.index(presented_lines[0]))
    return {"requested": requested, "ready_observed": bool(ready_lines),
            "configuration_validated": configured, "geometry": geometry,
            "unavailable_markers": unavailable, "presented": presented,
            "validated": presented,
            "status": "not-requested" if not requested else "unavailable" if unavailable else
                      "validated" if presented else "presentation-missing-or-invalid" if configured else
                      "ready-missing-or-invalid",
            "physical_display_verified": False, "macos_desktop_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("efi", "kernel", "device-tree", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("physical-base", "virtual-base", "memory-size", "kernel-physical"):
        parser.add_argument(f"--{name}", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--tools", type=Path, required=True, help="canonical authored OVMF helper directory")
    parser.add_argument("--instruction-budget", type=int, default=8)
    diagnostic = parser.add_mutually_exclusive_group()
    diagnostic.add_argument("--deep-diagnostic", action="store_true", help="explicitly select only the deep-16384 tier")
    diagnostic.add_argument("--long-diagnostic", action="store_true", help="explicitly select only the long-65536 tier")
    diagnostic.add_argument("--tiered-diagnostic", action="store_true",
                        help="explicitly require the opt-in tiered EFI build; allows256/1024/4096")
    parser.add_argument("--platform-profile", choices=["nextcore-irq-compat-v1"])
    for name in ("initial-override", "initial-pstate", "vector-base", "irq-level", "fiq-level"):
        parser.add_argument(f"--{name}", type=lambda value: int(value, 0))
    parser.add_argument("--allow-incomplete-sptm-prefix", action="store_true", required=True)
    parser.add_argument("--gop-framebuffer", action="store_true",
                        help="request guest framebuffer setup and require explicit ready/presented evidence")
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--host-memory-mib", type=int, default=768)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    args = parser.parse_args()
    maximum_budget = 64 if args.platform_profile else 8
    if args.tiered_diagnostic and args.platform_profile:
        maximum_budget = 4096
    if args.deep_diagnostic:
        if args.platform_profile != "nextcore-irq-compat-v1" or args.instruction_budget != 16384:
            parser.error("--deep-diagnostic requires the named profile and exact budget16384")
        maximum_budget = 16384
    if args.long_diagnostic:
        if args.platform_profile != "nextcore-irq-compat-v1" or args.instruction_budget != 65536:
            parser.error("--long-diagnostic requires the named profile and exact budget65536")
        maximum_budget = 65536
    if not 1 <= args.instruction_budget <= maximum_budget:
        parser.error(f"selected diagnostic budget must be 1..{maximum_budget}")
    if args.instruction_budget > 64 and args.instruction_budget not in (256, 1024, 4096) and not (args.deep_diagnostic or args.long_diagnostic):
        parser.error("extended diagnostic budget must be256,1024 or4096")
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
    # Mirror Core's CLI-representable platform/placement invariants before
    # loading helpers, creating an ESP, or attempting any process execution.
    physical_end = args.physical_base + args.memory_size
    virtual_end = args.virtual_base + args.memory_size
    if physical_end >= 2**64 or virtual_end >= 2**64:
        parser.error("guest physical/virtual aperture end must fit an unsigned 64-bit integer")
    if not args.physical_base <= args.kernel_physical < physical_end:
        parser.error("kernel-physical must lie inside the guest physical aperture")
    override = platform_options.get("InitialOverride", 0)
    pstate = platform_options.get("InitialPstate", 0x3c5)
    vector = platform_options.get("VectorBase", 0)
    if (override & ~0x00f00000 or ((override >> 20) & 3) not in (0, 2)
            or ((override >> 22) & 3) not in (0, 2)):
        parser.error("initial-override contains unsupported profile bits or field values")
    if pstate & ~0xf00003cf or (pstate & 15) not in (4, 5):
        parser.error("initial-pstate must use supported profile bits and EL1t/EL1h mode")
    if platform_options.get("IrqLevel", 0) > 1 or platform_options.get("FiqLevel", 0) > 1:
        parser.error("irq-level and fiq-level must each be zero or one")
    if vector & 2047 or (vector != 0 and
            (vector < args.physical_base or vector + 2048 >= 2**64 or vector + 2048 > physical_end)):
        parser.error("nonzero vector-base must be 2048-byte aligned with its full span inside guest RAM")
    tools = args.tools.resolve(strict=True)
    tool_sources = [Path(__file__).resolve(), tools / "verify_arm_jit_ovmf.py"]
    tool_before = {str(path): digest(path) for path in tool_sources}
    sys.path.insert(0, str(tools))
    from verify_arm_jit_ovmf import lines, ordered
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
    if args.deep_diagnostic:
        trace["DiagnosticTier"] = "deep-16384"
    if args.long_diagnostic:
        trace["DiagnosticTier"] = "long-65536"
    if args.gop_framebuffer:
        trace["Video"] = "gop-framebuffer"
    if args.platform_profile:
        trace["PlatformProfile"] = args.platform_profile
        if platform_options:
            trace["Platform"] = platform_options
    config = {"Nextcore": {"Kernel": {
        "Profile": "x86-efi-arm64-trace", "Path": "\\EFI\\NEXTCORE\\kernel.kc",
        "Arguments": "-v", "Trace": trace,
    }}}
    (oc / "config.plist").write_bytes(plistlib.dumps(config))
    config_digest = digest(oc / "config.plist")
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
    if execution is not None:
        memory_line = next((line for line in actual if line.startswith("NXARMJIT: TRACE_MEMORY_RESULT ")), "")
        memory_match = re.fullmatch(r"NXARMJIT: TRACE_MEMORY_RESULT abi=(\d+) provider_status=(\d+) guest_far=(0x[0-9a-f]+) last_address=(0x[0-9a-f]+) fetch_requests=(\d+) data_requests=(\d+) completed_data_operations=(\d+)", memory_line)
        execution["memory"] = dict(zip(("abi","provider_status","guest_far","last_address","fetch_requests","data_requests","completed_data_operations"),
            (int(value,0) for value in memory_match.groups()))) if memory_match else None
    after = {str(path): digest(path) for path in inputs}
    tool_after = {str(path): digest(path) for path in tool_sources}
    copies_unchanged = (digest(payload / "kernel.kc") == before[str(args.kernel)]
        and digest(payload / "diagnostic.dt") == before[str(args.device_tree)]
        and digest(boot / "BOOTX64.EFI") == before[str(args.efi)]
        and digest(oc / "config.plist") == config_digest)
    completed = (ordered(actual, expected) and execution is not None
                 and execution["retired"] <= args.instruction_budget and execution["registers"] is not None
                 and before == after and tool_before == tool_after and copies_unchanged and failure is None)
    if args.platform_profile:
        completed = completed and bool(execution and execution["platform"] and execution["platform"]["profile"] == 1
                                       and execution["exception"] is not None)
    tiered_marker = "NXARMJIT: TRACE_TIERED_DIAGNOSTIC maximum=4096" in actual
    if args.tiered_diagnostic:
        completed = completed and tiered_marker
    deep_build = "NXARMJIT: TRACE_DEEP_DIAGNOSTIC_BUILD maximum=16384" in actual
    deep_selected = "NXARMJIT: TRACE_DEEP_DIAGNOSTIC_SELECTED tier=16384" in actual
    if args.deep_diagnostic:
        completed = completed and deep_selected
    long_build = "NXARMJIT: TRACE_LONG_DIAGNOSTIC_BUILD maximum=65536" in actual
    long_selected = "NXARMJIT: TRACE_LONG_DIAGNOSTIC_SELECTED tier=65536" in actual
    if args.long_diagnostic:
        completed = completed and long_build and long_selected
    if args.deep_diagnostic or args.long_diagnostic:
        memory = execution.get("memory") if execution else None
        completed = bool(completed and tiered_marker and deep_build and memory
            and memory["abi"] == 1 and execution["retired"] <= memory["fetch_requests"] <= execution["retired"]+1
            and 0 <= memory["completed_data_operations"] <= memory["data_requests"] <= memory["fetch_requests"]
            and "NXARMJIT: TRACE_MEMORY_PROVIDER abi=1 mode=m0-only" in actual)
    video = parse_trace_video(actual, args.gop_framebuffer, args.physical_base, args.memory_size)
    requested_checks_completed = completed and (not args.gop_framebuffer or video["validated"])
    receipt = {
        "schema": "nextcore.x86-efi-arm-deep-trace.v1", "host_architecture": platform.machine(),
        "handoff_abi": "unprovisioned-sptm-prefix", "sptm_args_provided": False,
        "platform_profile": args.platform_profile, "profile_reset_origin": "software_defined" if args.platform_profile else "unprovided",
        "sptm_services_provided": False, "platform_device_tree_provided": False,
        "config": config, "execution": execution,
        "deep_diagnostic_requested": args.deep_diagnostic,
        "deep_diagnostic_build_observed": deep_build,
        "deep_diagnostic_selected_observed": deep_selected,
        "long_diagnostic_requested": args.long_diagnostic,
        "long_diagnostic_build_observed": long_build,
        "long_diagnostic_selected_observed": long_selected,
        "tool_source_sha256_before": tool_before,
        "tool_source_sha256_after": tool_after,
        "tool_sources_preserved": tool_before == tool_after,
        "tiered_diagnostic_requested": args.tiered_diagnostic,
        "tiered_diagnostic_build_observed": tiered_marker,
        "markers": [line for line in actual if line.startswith("NXARMJIT:")],
        "input_sha256_before": before, "input_sha256_after": after,
        "original_inputs_preserved": before == after, "esp_copies_preserved": copies_unchanged,
        "diagnostic_completed": completed,
        "video_requested": args.gop_framebuffer, "video": video,
        "requested_checks_completed": requested_checks_completed,
        "native_execution_observed": bool(execution and execution["retired"] > 0 and execution["compiled_blocks"] > 0),
        "elapsed_seconds": round(time.monotonic() - start, 3), "failure": failure,
        "qemu_exit_code": process.returncode if process else None,
        "stopped_by_harness": stopped, "macos_boot_verified": False, "metal_verified": False,
    }
    (output / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"report": str(output / "report.json"), "diagnostic_completed": completed,
                      "video_validated": video["validated"], "requested_checks_completed": requested_checks_completed,
                      "native_execution_observed": receipt["native_execution_observed"], "failure": failure}))
    return 0 if requested_checks_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
