"""Portable TCG VMApple launch path.

This module is the non-Apple host layer for the ARM-only macOS entry.  It uses
the pinned QEMU VMApple device model built by ``Tools/build_vmapple_tcg.py``;
it never asks for Virtualization.framework, HVF, an Apple CPU, or a guest-image
rewrite.  The guest firmware, AUX image, and root image remain caller-owned
read-only inputs and QEMU receives only copy-on-write overlays.

The engine is intentionally separate from the historical DFU/recovery runner
and from the native ``macosvm`` worker.  A TCG process starting is not a macOS
boot claim: XNU and userspace UART markers are still required by the same
evidence gate used by the native path.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import platform
import re
import subprocess
import time
from typing import Any

from .vmapple import (
    MACOSVM_MAX_RUN_TIMEOUT,
    MAX_FIRMWARE_BYTES,
    MAX_VM_JSON_BYTES,
    StorageSession,
    VIRTUAL_MODEL,
    VIRTUAL_SOC_NAME,
    _effective_display_backend,
    _guest_path,
    _inputs_intact,
    _new_directory,
    _observe_direct_macos_boot,
    _regular,
    _sha256,
    _write_report,
    create_storage,
    load_macosvm_configuration,
    _resolve_executable,
    _apply_iboot_xnu_handoff_gate,
)


_REIMS_FRAME_RE = re.compile(
    rb"reims-vgpu-window: first frame presented \((\d+)x(\d+), (\d+) swapchain images\)"
)
_QEMU_TRACE_PC_RE = re.compile(rb"^Trace \d+: .* \[[0-9a-fA-F]+/([0-9a-fA-F]{16})/")
_PSCI_TRACE_RE = re.compile(
    r"arm_psci_call.*?x0=0x([0-9a-fA-F]+).*?x1=0x([0-9a-fA-F]+)"
    r".*?x2=0x([0-9a-fA-F]+).*?x3=0x([0-9a-fA-F]+)"
    r".*?cpuid=0x([0-9a-fA-F]+)",
    re.IGNORECASE,
)
_FIRMWARE_BASE = 0x00100000
_HIGH_RAM_ALIAS_BASE = 0x1FC000000
_MAX_PSCI_TRACE_BYTES = 1024 * 1024
_MAX_EXEC_TRACE_BYTES = 4 * 1024 * 1024
_PSCI_SYSTEM_RESET_IDS = frozenset((0x84000009, 0xC4000009))

_VMAPPLE_DEVICE_MAP: tuple[tuple[str, int, int], ...] = (
    ("GIC", 0x1000_0000, 0x0041_0000),
    ("UART", 0x2001_0000, 0x0001_0000),
    ("RTC", 0x2005_0000, 0x0000_1000),
    ("GPIO", 0x2006_0000, 0x0000_1000),
    ("PVPANIC", 0x2007_0000, 0x0000_0002),
    ("BDIF", 0x3000_0000, 0x0020_0000),
    ("Display", 0x3020_0000, 0x0001_0000),
    ("DisplayCtl", 0x3021_0000, 0x0001_0000),
    ("AES", 0x3022_0000, 0x0000_4000),
    ("AESCtl", 0x3023_0000, 0x0000_4000),
    ("PcieEcam", 0x4000_0000, 0x1000_0000),
    ("PcieMmio", 0x5000_0000, 0x1FFF_0000),
)
_VMAPPLE_RAM_BASE = 0x7000_0000

_IBOOT_PANIC_LOW = 0x7006F0B4
_IBOOT_PANIC_HIGH = 0x7008EBFC

_QEMU_DATA_ABORT_RE = re.compile(
    rb"data abort.*?FAR=0x([0-9a-fA-F]+).*?ESR=0x([0-9a-fA-F]+)",
    re.IGNORECASE | re.DOTALL,
)
_QEMU_INSTRUCTION_ABORT_RE = re.compile(
    rb"instruction abort.*?FAR=0x([0-9a-fA-F]+)",
    re.IGNORECASE | re.DOTALL,
)
_QEMU_GUEST_CRASH_RE = re.compile(
    rb"Guest crash loaded.*?pc=0x([0-9a-fA-F]+)",
    re.IGNORECASE | re.DOTALL,
)


def _read_trace_windows(path: Path, maximum: int) -> tuple[int, list[tuple[int, bytes]]]:
    """Read at most maximum bytes, keeping independent original head/tail ranges."""
    if maximum < 2:
        raise ValueError("trace sample limit must be at least two bytes")
    with path.open("rb") as source:
        source.seek(0, 2)
        total = source.tell()
        source.seek(0)
        if total <= maximum:
            return total, [(0, source.read(maximum))]
        head_bytes = maximum // 2
        head = source.read(head_bytes)
        tail_offset = total - (maximum - head_bytes)
        source.seek(tail_offset)
        return total, [(0, head), (tail_offset, source.read(maximum - head_bytes))]


def _trace_sample_metadata(total: int, windows: list[tuple[int, bytes]]) -> dict[str, object]:
    observed = sum(len(data) for _, data in windows)
    return {
        "trace_present": True,
        "trace_bytes": total,
        "trace_bytes_observed": observed,
        "trace_truncated": total > observed,
        "trace_sample_ranges": [{"offset": offset, "bytes": len(data)} for offset, data in windows],
        "count_scope": "complete sampled lines; head/tail only when trace_truncated is true",
    }


def _trace_lines(windows: list[tuple[int, bytes]], total: int):
    """Do not join a cut head line to a tail line or parse a cut tail prefix."""
    for offset, data in windows:
        for index, line in enumerate(data.splitlines(keepends=True)):
            end = offset + len(line)
            complete_start = offset == 0 or index > 0
            complete_end = line.endswith(b"\n") or end == total
            if complete_start and complete_end:
                yield offset, line
            offset = end


def _psci_trace_evidence(path: Path) -> dict[str, object]:
    """Parse the bounded text trace emitted by QEMU's arm_psci_call event.

    This is a diagnostic from the shared QEMU log. A PSCI call is not a boot-stage or
    userspace marker, and SYSTEM_RESET is reported as a guest request rather
    than as evidence that QEMU or macOS completed a reset.
    """
    result: dict[str, object] = {
        "trace_path": str(path),
        "trace_present": False,
        "trace_bytes": 0,
        "trace_bytes_observed": 0,
        "trace_truncated": False,
        "calls": [],
        "call_count": 0,
        "guest_reset_requested": False,
        "evidence_policy": "PSCI trace diagnostic only; no XNU/userspace/macOS promotion",
    }
    try:
        total_bytes, windows = _read_trace_windows(path, _MAX_PSCI_TRACE_BYTES)
    except OSError as error:
        result["read_error"] = f"{type(error).__name__}: {error}"
        return result
    result.update(_trace_sample_metadata(total_bytes, windows))
    calls: list[dict[str, object]] = []
    for offset, line in _trace_lines(windows, total_bytes):
        match = _PSCI_TRACE_RE.search(line.decode("utf-8", errors="replace"))
        if match is None:
            continue
        function_id = int(match.group(1), 16)
        calls.append({
            "byte_offset": offset,
            "function_id": f"0x{function_id:x}",
            "x0": f"0x{function_id:016x}",
            "x1": f"0x{int(match.group(2), 16):016x}",
            "x2": f"0x{int(match.group(3), 16):016x}",
            "x3": f"0x{int(match.group(4), 16):016x}",
            "cpuid": f"0x{int(match.group(5), 16):x}",
            "reset_requested": function_id in _PSCI_SYSTEM_RESET_IDS,
        })
    result["calls"] = calls
    result["call_count"] = len(calls)
    result["guest_reset_requested"] = any(item["reset_requested"] for item in calls)
    return result


def _classify_fault_address(address: int) -> dict[str, object]:
    """Classify a fault address against the VMApple device map."""
    for name, base, size in _VMAPPLE_DEVICE_MAP:
        if base <= address < base + size:
            return {
                "device": name,
                "device_base": f"0x{base:08x}",
                "device_offset": f"0x{address - base:x}",
                "in_device": True,
                "in_ram": False,
            }
    if _VMAPPLE_RAM_BASE <= address < _VMAPPLE_RAM_BASE + 0x4000_0000:
        return {
            "device": "RAM",
            "ram_offset": f"0x{address - _VMAPPLE_RAM_BASE:x}",
            "in_device": False,
            "in_ram": True,
        }
    return {
        "device": "unmapped",
        "in_device": False,
        "in_ram": False,
    }


def _classify_iboot_panic_range(pc: int) -> dict[str, object] | None:
    """Return diagnostic if a guest PC falls within the known iBoot panic range."""
    if not (_IBOOT_PANIC_LOW <= pc <= _IBOOT_PANIC_HIGH):
        return None
    offset = pc - _VMAPPLE_RAM_BASE
    return {
        "panic_pc": f"0x{pc:08x}",
        "firmware_offset": f"0x{offset:x}",
        "range": f"0x{_IBOOT_PANIC_LOW:08x}-0x{_IBOOT_PANIC_HIGH:08x}",
        "diagnostic": "iBoot panic in known range; check exception type and FAR",
    }


def _qemu_stderr_evidence(path: Path) -> dict[str, object]:
    """Record the QEMU crash-loaded diagnostic and exception patterns."""
    result: dict[str, object] = {
        "path": str(path),
        "present": False,
        "bytes": 0,
        "guest_crash_loaded_observed": False,
        "data_abort_observed": False,
        "instruction_abort_observed": False,
        "fault_addresses": [],
        "exception_diagnostics": [],
        "evidence_policy": "QEMU stderr diagnostic only; no XNU/userspace/macOS promotion",
    }
    try:
        data = path.read_bytes()
    except OSError as error:
        result["read_error"] = f"{type(error).__name__}: {error}"
        return result
    result.update({
        "present": True,
        "bytes": len(data),
        "guest_crash_loaded_observed": b"Guest crash loaded" in data,
    })
    bounded = data[-2 * 1024 * 1024:]
    fault_addresses: list[str] = []
    diagnostics: list[dict[str, object]] = []
    for match in _QEMU_DATA_ABORT_RE.finditer(bounded):
        far = int(match.group(1), 16)
        esr = int(match.group(2), 16)
        fault_addresses.append(f"0x{far:x}")
        diag: dict[str, object] = {
            "type": "data_abort",
            "far": f"0x{far:08x}",
            "esr": f"0x{esr:08x}",
            "wnr": bool(esr & (1 << 6)),
        }
        diag.update(_classify_fault_address(far))
        diagnostics.append(diag)
    if fault_addresses:
        result["data_abort_observed"] = True
    for match in _QEMU_INSTRUCTION_ABORT_RE.finditer(bounded):
        far = int(match.group(1), 16)
        fault_addresses.append(f"0x{far:x}")
        diag = {
            "type": "instruction_abort",
            "far": f"0x{far:08x}",
        }
        diag.update(_classify_fault_address(far))
        diagnostics.append(diag)
    if any(d["type"] == "instruction_abort" for d in diagnostics):
        result["instruction_abort_observed"] = True
    result["fault_addresses"] = fault_addresses
    result["exception_diagnostics"] = diagnostics
    return result


def _bound_trace_file(path: Path, maximum: int = _MAX_PSCI_TRACE_BYTES) -> dict[str, object]:
    """Retain bounded diagnostic samples without destroying the original trace."""
    result: dict[str, object] = {"source_path": str(path), "source_preserved": True, "samples": []}
    try:
        total, windows = _read_trace_windows(path, maximum)
        result.update(_trace_sample_metadata(total, windows))
        samples = []
        for index, (offset, data) in enumerate(windows):
            sample = path
            if total > maximum:
                suffix = ".sample-head" if index == 0 else ".sample-tail"
                sample = path.with_name(path.name + suffix)
                sample.write_bytes(data)
            samples.append({"path": str(sample), "offset": offset, "bytes": len(data)})
        result["samples"] = samples
    except OSError as error:
        result["sample_error"] = f"{type(error).__name__}: {error}"
    return result


def _graphics_host_evidence(path: Path) -> dict[str, object]:
    """Parse QEMU/Reims host output without turning it into guest proof.

    Reims is a synthetic PV research device.  A host-side swapchain frame
    demonstrates that the selected backend initialized, but it says nothing
    about iBoot, XNU, WindowServer, AGX, or the guest Metal ABI.
    """
    result: dict[str, object] = {
        "backend": "none",
        "host_frame_presented": False,
        "frame_width": None,
        "frame_height": None,
        "swapchain_images": None,
        "guest_windowserver_reached": False,
        "guest_metal_accelerator_verified": False,
        "guest_metal_device_verified": False,
        "guest_graphics_acceleration_verified": False,
        "evidence_policy": "QEMU host output only; no guest WindowServer/Metal promotion",
    }
    try:
        data = path.read_bytes()
    except OSError as error:
        result["read_error"] = f"{type(error).__name__}: {error}"
        return result
    # Keep the parser bounded even if a debug QEMU run produces a large log.
    data = data[-1024 * 1024:]
    match = _REIMS_FRAME_RE.search(data)
    if match is not None:
        result.update({
            "backend": "reims-vgpu",
            "host_frame_presented": True,
            "frame_width": int(match.group(1)),
            "frame_height": int(match.group(2)),
            "swapchain_images": int(match.group(3)),
        })
    return result


def _qemu_execution_evidence(path: Path, *, firmware_kind: str) -> dict[str, object]:
    """Classify a bounded QEMU TCG trace without promoting it to XNU proof."""
    result: dict[str, object] = {
        "trace_path": str(path),
        "trace_present": False,
        "trace_bytes": 0,
        "trace_bytes_observed": 0,
        "trace_truncated": False,
        "translation_block_count": 0,
        "distinct_guest_pcs": 0,
        "first_guest_pc": None,
        "last_guest_pc": None,
        "firmware_kind": firmware_kind,
        "stage2_execution_observed": False,
        "high_ram_relocation_observed": False,
        "iboot_panic_range_entry": False,
        "iboot_panic_classification": None,
        "evidence_policy": "QEMU TCG execution trace only; no UART/XNU/userspace promotion",
    }
    if firmware_kind != "iboot-stage2":
        result["evidence_policy"] = (
            "AVPBooter input; QEMU trace is diagnostic only and is not used as iBoot proof"
        )
        return result
    try:
        total_bytes, windows = _read_trace_windows(path, _MAX_EXEC_TRACE_BYTES)
    except OSError as error:
        result["read_error"] = f"{type(error).__name__}: {error}"
        return result
    result.update(_trace_sample_metadata(total_bytes, windows))
    pcs: list[int] = []
    pc_offsets: list[int] = []
    for offset, line in _trace_lines(windows, total_bytes):
        match = _QEMU_TRACE_PC_RE.match(line)
        if match is not None:
            pcs.append(int(match.group(1), 16))
            pc_offsets.append(offset)
    distinct = list(dict.fromkeys(pcs))
    result.update({
        "translation_block_count": len(pcs),
        "distinct_guest_pcs": len(distinct),
        "first_guest_pc": f"0x{pcs[0]:x}" if pcs else None,
        "last_guest_pc": f"0x{pcs[-1]:x}" if pcs else None,
        "first_guest_pc_byte_offset": pc_offsets[0] if pc_offsets else None,
        "last_guest_pc_byte_offset": pc_offsets[-1] if pc_offsets else None,
        "stage2_execution_observed": any(
            _FIRMWARE_BASE <= pc < _FIRMWARE_BASE + MAX_FIRMWARE_BYTES for pc in pcs
        ),
        "high_ram_relocation_observed": any(
            _HIGH_RAM_ALIAS_BASE <= pc < _HIGH_RAM_ALIAS_BASE + 0x20000000 for pc in pcs
        ),
        "iboot_panic_range_entry": any(
            _IBOOT_PANIC_LOW <= pc <= _IBOOT_PANIC_HIGH for pc in pcs
        ),
    })
    if result["iboot_panic_range_entry"]:
        last_in_range = next(pc for pc in reversed(pcs) if _IBOOT_PANIC_LOW <= pc <= _IBOOT_PANIC_HIGH)
        result["iboot_panic_classification"] = _classify_iboot_panic_range(last_in_range)
    return result


def probe_tcg_backend(executable: Any, *, research_graphics: bool = False) -> dict[str, object]:
    """Probe the exact QEMU binary without treating help output as boot evidence."""
    version = subprocess.run(
        executable.command("--version"), capture_output=True, text=True, timeout=30, check=False
    )
    machines = subprocess.run(
        executable.command("-machine", "help"), capture_output=True, text=True, timeout=30, check=False
    )
    accelerators = subprocess.run(
        executable.command("-accel", "help"), capture_output=True, text=True, timeout=30, check=False
    )
    devices = subprocess.run(
        executable.command("-device", "help"), capture_output=True, text=True, timeout=30, check=False
    )
    machine_help = subprocess.run(
        executable.command("-machine", "vmapple,help"), capture_output=True, text=True, timeout=30, check=False
    )
    bdif_help = subprocess.run(
        executable.command("-device", "vmapple-bdif,help"), capture_output=True, text=True, timeout=30, check=False
    )
    if any(item.returncode for item in (version, machines, accelerators, devices, machine_help, bdif_help)):
        raise ValueError("TCG VMApple capability probe failed")
    machine_names = {
        line.split()[0] for line in machines.stdout.splitlines() if line.strip() and line.split()
    }
    if "vmapple" not in machine_names:
        raise ValueError("QEMU does not expose the VMApple machine; build the pinned TCG binary")
    accelerator_names = set(accelerators.stdout.split())
    if "tcg" not in accelerator_names:
        raise ValueError("QEMU VMApple build does not expose TCG")
    if "research-headless" not in machine_help.stdout:
        raise ValueError("QEMU VMApple build does not expose explicit research-headless mode")
    if research_graphics and "research-graphics" not in machine_help.stdout:
        raise ValueError("QEMU VMApple build does not expose explicit research-graphics mode")
    device_text = devices.stdout + devices.stderr
    if "vmapple-virtio-blk-pci" not in device_text:
        raise ValueError("QEMU VMApple build does not expose its storage device")
    if "allow-block-writes" not in (bdif_help.stdout + bdif_help.stderr):
        raise ValueError("QEMU VMApple build does not expose the BDIF write gate")
    if research_graphics and "reims-vgpu-pci" not in device_text:
        raise ValueError("QEMU VMApple graphics build does not expose the Reims vGPU device")
    version_lines = (version.stdout or version.stderr).splitlines()
    return {
        "engine": "qemu-vmapple-tcg",
        "executable": executable.program,
        "version": version_lines[0] if version_lines else "",
        "machine": "vmapple",
        "tcg": True,
        "hvf": False,
        "virtualization_framework": False,
        "apple_hardware": False,
        "headless": True,
        "research_graphics": research_graphics,
        "graphics_backend": "reims-vgpu (host Vulkan/Metal selected by QEMU build)"
        if research_graphics else "none",
        "storage_device": "vmapple-virtio-blk-pci",
        "guest_image_modified": False,
    }


def _tcg_command(
    *,
    executable: Any,
    bundle: Any,
    storage: StorageSession,
    firmware: Path,
    output: Path,
    memory_mib: int,
    smp: int,
    display: str,
    allow_bdif_writes: bool,
    research_graphics: bool = False,
    firmware_kind: str = "avpbooter",
    optional_rpc_unavailable: bool = False,
    debug_trace: Path | None = None,
    psci_trace: Path | None = None,
) -> list[str]:
    serial = _guest_path(output / "serial.log", executable)
    machine = (
        f"vmapple,research-headless=on,research-graphics={'on' if research_graphics else 'off'},"
        f"uuid={bundle.uuid}"
    )
    if firmware_kind == "iboot-stage2":
        machine += ",research-stage2=on"
    arguments: list[str] = [
        "-M", machine,
        "-accel", "tcg,thread=single",
        "-cpu", "max,pauth=on,pauth-qarma5=on,cntfrq=24000000",
        "-m", f"{memory_mib}M",
        "-smp", str(smp),
        "-bios", _guest_path(firmware, executable),
        "-global", f"vmapple-cfg.soc_name={VIRTUAL_SOC_NAME}",
        "-global", f"vmapple-cfg.model={VIRTUAL_MODEL}",
    ]
    if optional_rpc_unavailable:
        arguments.extend([
            "-global", "vmapple-cfg.optional-rpc-unavailable=on",
        ])
    storage_arguments = storage.arguments(
        executable, allow_bdif_writes=allow_bdif_writes
    )
    arguments.extend(storage_arguments)
    # StorageSession owns only the block graph.  Keep process-level options in
    # this single tail so the generated QEMU command contains one -display.
    arguments.extend([
        "-display", display,
        "-monitor", "none",
        "-serial", f"file:{serial}",
        "-nic", "none",
        "-no-reboot",
    ])
    # The pinned QEMU uses the log trace backend. trace/control.c's
    # trace_init_file() makes -trace file= override the global -D sink:
    # https://gitlab.com/qemu-project/qemu/-/blob/master/trace/control.c
    # Use one -D destination and enable PSCI without a second file option.
    if debug_trace is not None and psci_trace is not None and debug_trace != psci_trace:
        raise ValueError("QEMU log backend requires one shared debug/PSCI trace path")
    log_trace = debug_trace if debug_trace is not None else psci_trace
    if debug_trace is None:
        arguments.extend(["-d", "guest_errors,unimp"])
    else:
        arguments.extend(["-d", "guest_errors,unimp,exec"])
    if log_trace is not None:
        arguments.extend(["-D", _guest_path(log_trace, executable)])
    if psci_trace is not None:
        arguments.extend(["-trace", "enable=arm_psci_call"])
    return executable.command(*arguments)


@dataclass(frozen=True)
class TCGVMappleConfig:
    target_major: int
    qemu: str | None
    qemu_img: str | None
    firmware: str
    vm_json: str
    output: str | None = None
    # Optional materialized raw storage views from a previous run.  The TCG
    # session still creates fresh qcow2 overlays above these read-only seeds.
    aux_seed: str | None = None
    root_seed: str | None = None
    memory_mib: int = 4096
    smp: int = 2
    display: str = "none"
    duration: float | None = None
    observation_timeout: float = 600.0
    research_only: bool = False
    research_graphics: bool = False
    firmware_kind: str = "avpbooter"
    optional_rpc_unavailable: bool = False

    def validate(self) -> tuple[Any, Any, Path, Any]:
        if self.target_major not in (26, 27):
            raise ValueError("TCG VMApple target must be macOS 26 or 27")
        if self.research_only is not True:
            raise ValueError("TCG VMApple launch requires the explicit --research-only flag")
        if self.firmware_kind not in ("avpbooter", "iboot-stage2"):
            raise ValueError("TCG VMApple firmware kind must be avpbooter or iboot-stage2")
        if type(self.optional_rpc_unavailable) is not bool:
            raise ValueError("TCG VMApple optional_rpc_unavailable must be a boolean")
        if self.display not in ("none", "auto", "dbus"):
            raise ValueError("TCG VMApple display must be none, auto, or dbus")
        if type(self.memory_mib) is not int or not 512 <= self.memory_mib <= 1024 * 1024:
            raise ValueError("TCG VMApple memory must be between 512 MiB and 1 TiB")
        if type(self.smp) is not int or not 1 <= self.smp <= 32:
            raise ValueError("TCG VMApple SMP must be between 1 and 32 CPUs")
        for label, value, maximum in (
            ("observation timeout", self.observation_timeout, MACOSVM_MAX_RUN_TIMEOUT),
            ("duration", self.duration, MACOSVM_MAX_RUN_TIMEOUT),
        ):
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"TCG VMApple {label} must be numeric")
            if not 0 < float(value) <= maximum:
                raise ValueError(f"TCG VMApple {label} must be between 0 and {int(maximum)} seconds")
        qemu = _resolve_executable(self.qemu, "X86_VMAPLE_QEMU", "qemu-system-aarch64")
        qemu_img = _resolve_executable(self.qemu_img, "X86_VMAPLE_QEMU_IMG", "qemu-img")
        firmware_label = (
            "raw iBoot Stage2 firmware" if self.firmware_kind == "iboot-stage2"
            else "AVPBooter firmware"
        )
        firmware = _regular(self.firmware, firmware_label, limit=MAX_FIRMWARE_BYTES)
        vm_json = _regular(self.vm_json, "macosvm.json", limit=MAX_VM_JSON_BYTES)
        bundle = load_macosvm_configuration(vm_json)
        return qemu, qemu_img, firmware, bundle


def run_tcg_macosvm(config: TCGVMappleConfig) -> dict[str, object]:
    """Run an unchanged VMApple bundle through software AArch64 emulation."""
    qemu, qemu_img, firmware, bundle = config.validate()
    aux_seed = _regular(config.aux_seed, "AUX seed view") if config.aux_seed else None
    root_seed = _regular(config.root_seed, "root seed view") if config.root_seed else None
    capabilities = probe_tcg_backend(qemu, research_graphics=config.research_graphics)
    output = _new_directory(config.output)
    source_inputs = {
        "vm_json": {
            "path": str(bundle.path),
            "bytes": bundle.path.stat().st_size,
            "sha256": bundle.json_sha256,
        },
        "aux": {
            "path": str(bundle.aux),
            "bytes": bundle.aux.stat().st_size,
            "sha256": _sha256(bundle.aux),
        },
        "root": {
            "path": str(bundle.root),
            "bytes": bundle.root.stat().st_size,
            "sha256": _sha256(bundle.root),
        },
        "firmware": {
            "path": str(firmware),
            "bytes": firmware.stat().st_size,
            "sha256": _sha256(firmware),
            "kind": config.firmware_kind,
        },
    }
    for name, seed in (("aux_seed", aux_seed), ("root_seed", root_seed)):
        if seed is not None:
            source_inputs[name] = {
                "path": str(seed),
                "bytes": seed.stat().st_size,
                "sha256": _sha256(seed),
            }
    report: dict[str, object] = {
        "schema": "26x86.vmapple-tcg/1",
        "layer": (
            "non-Apple host -> QEMU TCG -> AArch64 VMApple -> "
            f"{config.firmware_kind} -> macOS"
        ),
        "engine": "qemu-vmapple-tcg",
        "machine_type": "iBoot(AArch64)",
        "guest_os": "macOS",
        "target_major": config.target_major,
        "firmware_kind": config.firmware_kind,
        "host": {"system": platform.system(), "architecture": platform.machine()},
        "capabilities": capabilities,
        "source_inputs": source_inputs,
        "research_graphics_requested": config.research_graphics,
        "graphics_host_evidence": None,
        "firmware_execution_evidence": None,
        "graphics_acceleration_verified": False,
        "vm_bundle": bundle.report(),
        "input_integrity": False,
        "guest_inputs_modified": False,
        "native_runtime_started": False,
        "xnu_executed": False,
        "macos_userspace_reached": False,
        "guest_target_match": False,
        "macos_boot_verified": False,
        "iboot_executed": False,
        "iboot_stage1_verified": False,
        "iboot_stage2_verified": False,
        "iboot_stage2_execution_observed": False,
        "iboot_high_ram_relocation_observed": False,
        "iboot_panic_range_entry": False,
        "iboot_panic_classification": None,
        "iboot_to_xnu_handoff_verified": False,
        "xnu_to_userspace_handoff_verified": False,
        "full_iboot_xnu_userspace_chain_verified": False,
        "boot_chain_evidence": None,
        "tcg_runtime_started": False,
        "installer_ui_verified": False,
        "installation_verified": False,
        "observed_markers": {"xnu": [], "userspace": [], "installer": []},
        "psci_trace_evidence": None,
        "guest_reset_requested": False,
        "qemu_stderr_evidence": None,
        "termination": None,
        "error": None,
    }
    process: subprocess.Popen[bytes] | None = None
    log_trace = output / "qemu.debug.log"
    report["qemu_logging"] = {
        "backend": "log",
        "shared_log_path": str(log_trace),
        "execution_trace_enabled": config.firmware_kind == "iboot-stage2",
        "psci_event": "arm_psci_call",
        "sink_option": "-D; -trace enables events without file=",
    }
    started = time.monotonic()
    run_timeout = float(config.duration if config.duration is not None else config.observation_timeout)
    if config.firmware_kind == "iboot-stage2" and config.duration is None:
        # Raw Stage2 runs are trace probes. Do not leave a busy guest alive for
        # the normal six-hundred-second UART observation window.
        run_timeout = min(run_timeout, 60.0)
    try:
        storage = create_storage(
            aux=bundle.aux,
            root=bundle.root,
            directory=output,
            qemu_img=qemu_img,
            aux_offset=bundle.aux_offset,
            aux_seed=aux_seed,
            root_seed=root_seed,
        )
        # The upstream storage device is read-only at BDIF command level.  A
        # custom build may advertise a write gate, but absence is safe and is
        # recorded rather than guessed.
        device_help = subprocess.run(
            qemu.command("-device", "vmapple-bdif,help"),
            capture_output=True, text=True, timeout=30, check=False,
        )
        allow_writes = "allow-block-writes" in (device_help.stdout + device_help.stderr)
        display = _effective_display_backend(
            config.display, direct_macos=False, available=("none", "dbus")
        )
        debug_trace = log_trace if config.firmware_kind == "iboot-stage2" else None
        command = _tcg_command(
            executable=qemu,
            bundle=bundle,
            storage=storage,
            firmware=firmware,
            output=output,
            memory_mib=config.memory_mib,
            smp=config.smp,
            display=display,
            allow_bdif_writes=allow_writes,
            research_graphics=config.research_graphics,
            firmware_kind=config.firmware_kind,
            optional_rpc_unavailable=config.optional_rpc_unavailable,
            debug_trace=debug_trace,
            psci_trace=log_trace,
        )
        report["storage"] = {
            "aux_offset": bundle.aux_offset,
            "base_images_read_only": True,
            "overlay_directory": str(storage.directory),
            "allow_bdif_writes": allow_writes,
            "seed_views": {
                "aux": str(aux_seed) if aux_seed is not None else None,
                "root": str(root_seed) if root_seed is not None else None,
            },
        }
        report["command"] = command
        (output / "launch.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        stdout = (output / "qemu.stdout.log").open("wb")
        stderr = (output / "qemu.stderr.log").open("wb")
        try:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            report["native_runtime_started"] = True
            report["tcg_runtime_started"] = True
            report["pid"] = process.pid
            serial = output / "serial.log"
            while not serial.exists() and process.poll() is None:
                if time.monotonic() - started > min(run_timeout, 30.0):
                    break
                time.sleep(0.05)
            remaining = max(0.1, min(
                float(config.observation_timeout),
                run_timeout - (time.monotonic() - started),
            ))
            observation = _observe_direct_macos_boot(
                serial,
                remaining,
                process,
                expected_kernel_major=config.target_major,
            )
            report.update({
                "xnu_executed": bool(observation["xnu_executed"]),
                "macos_userspace_reached": bool(observation["macos_userspace_reached"]),
                "guest_kernel_major": observation["guest_kernel_major"],
                "guest_kernel_majors": observation["guest_kernel_majors"],
                "guest_target_match": bool(observation["guest_target_match"]),
                "macos_boot_verified": bool(observation["macos_boot_verified"]),
                "installer_ui_verified": bool(observation["installer_ui_visible"]),
                "observed_markers": observation["observed_markers"],
                "blocker": observation["direct_boot_blocker"],
                "boot_chain_evidence": observation.get("boot_chain_evidence"),
                "iboot_executed": bool(observation.get("boot_chain_evidence", {}).get("iboot_executed"))
                if isinstance(observation.get("boot_chain_evidence"), dict) else False,
                "iboot_stage1_verified": bool(observation.get("boot_chain_evidence", {}).get("iboot_stage1_verified"))
                if isinstance(observation.get("boot_chain_evidence"), dict) else False,
                "iboot_stage2_verified": bool(observation.get("boot_chain_evidence", {}).get("iboot_stage2_verified"))
                if isinstance(observation.get("boot_chain_evidence"), dict) else False,
                "iboot_to_xnu_handoff_verified": bool(observation.get("boot_chain_evidence", {}).get("iboot_to_xnu_handoff_verified"))
                if isinstance(observation.get("boot_chain_evidence"), dict) else False,
                "xnu_to_userspace_handoff_verified": bool(observation.get("boot_chain_evidence", {}).get("xnu_to_userspace_handoff_verified"))
                if isinstance(observation.get("boot_chain_evidence"), dict) else False,
            })
            deadline = started + run_timeout
            if process.poll() is None:
                if not observation["macos_boot_verified"]:
                    report["termination"] = (
                        "iboot-stage2-evidence-timeout"
                        if config.firmware_kind == "iboot-stage2"
                        else "tcg-boot-evidence-timeout"
                    )
                    process.terminate()
                else:
                    while process.poll() is None and time.monotonic() < deadline:
                        if (output / "stop").exists():
                            report["termination"] = "stop_file"
                            process.terminate()
                            break
                        time.sleep(0.1)
                    if process.poll() is None:
                        report["termination"] = "time_budget"
                        process.terminate()
        finally:
            stdout.close()
            stderr.close()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = f"{type(error).__name__}: {error}"
        report["blocker"] = report["error"]
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if report["termination"] is None and process is not None:
            report["termination"] = "guest_exit"
        report["returncode"] = process.returncode if process is not None else None
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["input_integrity"] = _inputs_intact(source_inputs)
        report["graphics_host_evidence"] = _graphics_host_evidence(output / "qemu.stderr.log")
        report["psci_trace_evidence"] = _psci_trace_evidence(log_trace)
        psci_evidence = report["psci_trace_evidence"]
        if isinstance(psci_evidence, dict):
            report["guest_reset_requested"] = (
                psci_evidence.get("guest_reset_requested") is True
            )
        report["qemu_stderr_evidence"] = _qemu_stderr_evidence(
            output / "qemu.stderr.log"
        )
        report["firmware_execution_evidence"] = _qemu_execution_evidence(
            log_trace, firmware_kind=config.firmware_kind
        )
        report["qemu_trace_retention"] = _bound_trace_file(log_trace)
        execution_evidence = report["firmware_execution_evidence"]
        if isinstance(execution_evidence, dict):
            report["iboot_stage2_execution_observed"] = (
                execution_evidence.get("stage2_execution_observed") is True
            )
            report["iboot_high_ram_relocation_observed"] = (
                execution_evidence.get("high_ram_relocation_observed") is True
            )
            report["iboot_panic_range_entry"] = (
                execution_evidence.get("iboot_panic_range_entry") is True
            )
            report["iboot_panic_classification"] = (
                execution_evidence.get("iboot_panic_classification")
            )
        # Reuse the same causal handoff gate as the native runner.  The TCG
        # process and its UART observer are not allowed to publish a positive
        # macOS claim without the immutable-input check and the marker order
        # verifier accepting one direct AVPBooter observation.
        report["direct_boot"] = {
            "requested": True,
            "selection": "macos",
            "dfu_entered": False,
            "observation": {
                "xnu_executed": report.get("xnu_executed") is True,
                "macos_userspace_reached": report.get("macos_userspace_reached") is True,
                "guest_kernel_major": report.get("guest_kernel_major"),
                "guest_target_match": report.get("guest_target_match") is True,
                "observed_markers": report.get("observed_markers", {}),
                "boot_chain_evidence": report.get("boot_chain_evidence"),
            },
        }
        _apply_iboot_xnu_handoff_gate(report)
        chain = report.get("boot_chain_evidence")
        report["full_iboot_xnu_userspace_chain_verified"] = bool(
            isinstance(chain, dict)
            and chain.get("iboot_to_xnu_handoff_verified") is True
            and chain.get("xnu_to_userspace_handoff_verified") is True
            and chain.get("xnu_executed") is True
            and chain.get("macos_userspace_reached") is True
            and chain.get("guest_target_match") is True
        )
        _write_report(output, report)
    return report
