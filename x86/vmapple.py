"""Original-preserving VMApple GUI runner and DFU transition probe.

This module is a 26x86 research control plane, not a macOS image patcher.
Apple firmware and storage inputs are supplied by the caller, verified before
use, and never modified.  The current VMApple backend is expected to run in a
POSIX/WSL environment because its recovery socket is a Unix socket.

The runner deliberately stops when iBSS does not advertise the next recovery
endpoint.  It never fabricates a descriptor, changes an IMG4 signature, or
forces an iBSS-to-iBEC transition.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import base64
import binascii
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import plistlib
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import zlib

from .iboot_personality import (
    DEFAULT_RECOVERY_IMAGE,
    IBOOT_MACHINE_TYPE,
    MACOS_GUEST_OS,
    default_scope,
    validate_iboot_scope,
)
from .boot_picker import (
    BOOT_DELAY_SECONDS,
    DEFAULT_ALT_KEY,
    MACOS_ENTRY_ID,
    RECOVERY_ENTRY_ID,
    validate_boot_picker_config,
)


MAX_FIRMWARE_BYTES = 1 * 1024 * 1024
MAX_DFU_BYTES = 64 * 1024 * 1024
MAX_RECOVERY_BYTES = 512 * 1024 * 1024
MAX_FRAME_BYTES = MAX_RECOVERY_BYTES + 6
DFU_BLOCK_BYTES = 2048
DFU_SUFFIX = bytes.fromhex("ffffffffac05000155464410")
MAX_TRANSITION_ATTEMPTS = 240
MAX_LOG_BYTES = 16 * 1024 * 1024
MAX_VM_JSON_BYTES = 1 * 1024 * 1024
MAX_VM_PLIST_DEPTH = 32
# QEMU's VMApple machine consumes the AUX payload after the 0x4000-byte
# Virtualization.framework metadata prefix.  ``macosvm.json`` points at the
# original, untrimmed ``aux.img``; keeping this offset in the bundle contract
# prevents a normal direct launch from silently presenting the wrong pflash
# view to AVPBooter.
MACOSVM_AUX_METADATA_BYTES = 0x4000
DEFAULT_AVPBOOTER_PATH = Path(
    "/System/Library/Frameworks/Virtualization.framework/Resources/AVPBooter.vmapple2.bin"
)
# ``auto`` is the safe default for a mixed Windows/WSL/Linux/macOS control
# plane.  The actual QEMU backend may expose only ``none``/``dbus`` on a
# headless research build, while a native macOS build normally exposes
# ``cocoa``.  GTK/SDL remain explicit opt-in values for builds that actually
# provide them; selecting a GUI name must never make the runner guess that a
# display server exists.
DISPLAY_BACKENDS = ("auto", "gtk", "sdl", "cocoa", "none", "dbus")
STAGE1_PROMPT = b"Entering iBootStage1 recovery mode, starting command prompt"
STAGE2_PROMPT = b"Entering iBootStage2 recovery mode, starting command prompt"
# Direct macOS boot is a separate path from the DFU/IPSW recovery transport.
# These markers are deliberately conservative: a Darwin banner proves that
# XNU reached the UART, while a userspace marker is required before this
# runner reports a completed macOS boot.  A QEMU exit, a display window, or an
# iBoot acknowledgement alone is never promoted to a macOS claim.
DIRECT_XNU_MARKERS = (b"Darwin Kernel Version", b"Darwin Kernel")
DIRECT_USERSPACE_MARKERS = (b"launchd:", b"launchd ", b"loginwindow", b"WindowServer")
DIRECT_INSTALLER_MARKERS = (b"macOS Utilities", b"Install macOS", b"RecoveryOS")
# These values are the guest-facing VMApple metadata written by the QEMU
# config device.  They are deliberately labelled virtual in every report:
# metadata can make iBoot take the M1 personality path, but it cannot create
# an Apple hardware attestation or prove that the guest is running on an M1.
VIRTUAL_SOC_NAME = "Apple M1 (Virtual)"
VIRTUAL_MODEL = "VM0001"

# qemu-t8030 is used as a device-topology reference only.  It emulates an
# iPhone 11/T8030 and therefore its iOS firmware, device tree and restore
# assumptions must never be presented as a macOS guest implementation.  Keep
# the reference revision explicit so a report can be reproduced without
# silently following a moving branch.
QEMU_T8030_REFERENCE = {
    "name": "qemu-t8030",
    "repository": "https://github.com/TrungNguyen1909/qemu-t8030",
    "wiki": "https://github.com/TrungNguyen1909/qemu-t8030/wiki/Bringing-up-the-emulator",
    "revision": "fd4b0f790903044d90b8a35fcf03758401252063",
    "machine_type": "t8030",
    "guest_scope": "iPhone 11 / iOS",
    "role": "device-topology-reference-only",
}

_APPLE_SILICON_PROFILE = {
    "schema": "26x86.vmapple-apple-silicon/1",
    "profile_id": "vmapple-m1-macos",
    "machine_type": IBOOT_MACHINE_TYPE,
    "guest_os": MACOS_GUEST_OS,
    "guest_os_policy": "macOS-only",
    "target_majors": [26, 27],
    "virtual_identity": {
        "soc_name": VIRTUAL_SOC_NAME,
        "model": VIRTUAL_MODEL,
        "identity_mode": "metadata-only",
        "hardware_attestation_verified": False,
    },
    "interrupt_controller": {
        "sandbox_contract": "AIC",
        "qemu_t8030_reference": "AIC",
        "current_vmapple_qemu": "GICv3",
        "current_vmapple_qemu_status": "baseline-only; AIC backend work remains",
        "gic_compatibility": False,
    },
    # The entries describe the boundary between the reference model and the
    # current project.  They are capability facts, not claims that a missing
    # device is emulated by the current binary.
    "device_topology": [
        {
            "name": "AIC",
            "reference": "apple.aic",
            "native_sandbox": "aic_v1 wired model (partial)",
            "current_vmapple_qemu": "missing; GICv3 baseline",
            "status": "required-gap",
        },
        {
            "name": "Apple ANS/NVMe",
            "reference": "apple.ans",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "VMApple BDIF AUX/root path",
            "status": "reference-only",
        },
        {
            "name": "DART/SART",
            "reference": "apple.dart / apple.sart",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "not exposed in research profile",
            "status": "required-gap",
        },
        {
            "name": "Apple NVRAM",
            "reference": "apple-nvram namespace",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "virtual config/AES path only",
            "status": "macos-validation-required",
        },
        {
            "name": "Apple UART",
            "reference": "apple-uart",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "PL011 compatibility UART",
            "status": "compatibility-only",
        },
        {
            "name": "SMC / watchdog / GPIO / SPI / I2C",
            "reference": "Apple-specific peripheral set",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "generic or absent in research profile",
            "status": "required-gap",
        },
        {
            "name": "USB OTG / Type-C recovery",
            "reference": "apple-otg / apple-typec",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "research chardev recovery transport",
            "status": "protocol-only",
        },
        {
            "name": "m1_fb / xnu_ramfb",
            "reference": "display framebuffer helpers",
            "native_sandbox": "not implemented",
            "current_vmapple_qemu": "PV graphics omitted in research-headless",
            "status": "graphics-gap",
        },
    ],
    "storage": {
        "reference_controller": "Apple ANS/NVMe-like",
        "project_controller": "VMApple BDIF AUX/root",
        "namespace_reference": [
            {"nsid": 1, "nstype": 1, "role": "NVMe data namespace", "status": "reference-only"},
            {"nsid": 5, "nstype": 5, "role": "Apple NVRAM namespace", "status": "reference-only"},
        ],
        "namespace_scope": "T8030/iOS reference command; macOS mapping requires validation",
        "base_images_immutable": True,
        "cow_overlay_required": True,
        "hardware_model_provisioning_receipt_required": True,
    },
    "cpu": {
        "guest_isa": "AArch64",
        "reference_cpu": "Apple A13 / T8030",
        "target_identity": VIRTUAL_SOC_NAME,
        "host_acceleration": "TCG research path",
        "native_minimum": "x86_64 SSE4.1 + SSE4.2",
    },
    "graphics": {
        "reference_devices": ["m1_fb", "xnu_ramfb"],
        "current_research_status": "Apple PV graphics unavailable in TCG research-headless",
        "verified": False,
    },
    "reference": QEMU_T8030_REFERENCE,
    "scope": {
        "supported_guest_os": [MACOS_GUEST_OS],
        "unsupported_guest_os": ["iOS", "iPadOS", "tvOS", "watchOS", "visionOS"],
        "reference_guest_os": ["iOS"],
        "ios_code_imported": False,
    },
    "claims": {
        "apple_hardware_attestation_verified": False,
        "macos_boot_verified": False,
        "installer_ui_verified": False,
    },
    "blockers": [
        "AIC is required by the native Sandbox contract; current VMApple QEMU research mode still exposes GICv3",
        "Apple ANS/DART/SART/SMC device behavior is not validated for macOS",
        "Apple PV graphics and Metal are not available in the current TCG research profile",
        "A hardware-model-matched AUX and an install-target root image are still required",
    ],
}


def apple_silicon_profile() -> dict[str, object]:
    """Return an isolated qemu-t8030-derived Apple Silicon capability profile.

    The deep copy prevents GUI/report callers from mutating the process-wide
    policy.  The profile deliberately records the current GICv3 QEMU gap while
    keeping the EFI Sandbox contract AIC-only.
    """
    return deepcopy(_APPLE_SILICON_PROFILE)

# Storage inspection is deliberately bounded.  It is a read-only diagnostic
# for the VMApple boot boundary; it is not an APFS parser and it never marks a
# file as provisioned merely because it contains non-zero bytes.
STORAGE_SAMPLE_BYTES = 1024 * 1024
STORAGE_ZERO_SCAN_BYTES = 256 * 1024 * 1024
STORAGE_MARKERS = (b"NXSB", b"APSB", b"APFS")


class VMappleError(RuntimeError):
    """A bounded launch or recovery-protocol failure."""


class RecoveryProtocolError(VMappleError):
    """The guest returned a malformed or unsupported recovery response."""


@dataclass(frozen=True)
class Executable:
    """An executable and the way the current host invokes it."""

    program: str
    wrapper: str | None = None

    @property
    def is_wsl(self) -> bool:
        return self.wrapper is not None

    def command(self, *arguments: str) -> list[str]:
        if self.wrapper is None:
            return [self.program, *arguments]
        return [self.wrapper, "--", self.program, *arguments]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular(value: str | Path, label: str, *, limit: int | None = None) -> Path:
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    size = path.stat().st_size
    if limit is not None and size > limit:
        raise ValueError(f"{label} exceeds the {limit} byte limit")
    return path


def _decode_vm_plist(value: object, label: str) -> tuple[object, bytes]:
    """Decode one macosvm base64 binary plist without invoking host tools."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"macosvm.json {label} must be a non-empty base64 string")
    try:
        raw = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as error:
        raise ValueError(f"macosvm.json {label} is not valid base64") from error
    if not raw or len(raw) > MAX_VM_JSON_BYTES:
        raise ValueError(f"macosvm.json {label} payload is empty or too large")
    try:
        document = plistlib.loads(raw)
    except (plistlib.InvalidFileException, ValueError, TypeError) as error:
        raise ValueError(f"macosvm.json {label} is not a binary plist") from error
    return document, raw


def _find_ecid(value: object, depth: int = 0) -> int | None:
    """Find the VM ECID in the decoded machineIdentifier plist."""
    if depth > MAX_VM_PLIST_DEPTH:
        return None
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "ECID":
                if isinstance(child, bool):
                    return None
                if isinstance(child, int):
                    return child if 0 <= child < 2**64 else None
                if isinstance(child, bytes) and 0 < len(child) <= 8:
                    return int.from_bytes(child, "little")
                if isinstance(child, str):
                    try:
                        parsed = int(child, 0)
                    except ValueError:
                        try:
                            parsed = int(child, 10)
                        except ValueError:
                            return None
                    return parsed if 0 <= parsed < 2**64 else None
            found = _find_ecid(child, depth + 1)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for child in value:
            found = _find_ecid(child, depth + 1)
            if found is not None:
                return found
    return None


@dataclass(frozen=True)
class MacOSVMConfiguration:
    """Validated, read-only inputs from a Virtualization.framework VM JSON."""

    path: Path
    uuid: int
    aux: Path
    root: Path
    aux_offset: int
    hardware_model_sha256: str
    machine_id_sha256: str
    json_sha256: str

    def report(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "uuid": self.uuid,
            "aux": str(self.aux),
            "root": str(self.root),
            "aux_offset": self.aux_offset,
            "aux_view": "original aux.img with Virtualization.framework metadata prefix skipped",
            "hardware_model_sha256": self.hardware_model_sha256,
            "machine_id_sha256": self.machine_id_sha256,
            "json_sha256": self.json_sha256,
            "inputs_read_only": True,
            "source": "macosvm.json storage/machineId/hardwareModel",
        }


def load_macosvm_configuration(value: str | Path) -> MacOSVMConfiguration:
    """Load and validate the macosvm JSON contract used by VMApple.

    The function never writes the JSON or its referenced images.  It resolves
    exactly one AUX and one root disk, decodes the ECID from the binary plist
    machine identifier, and requires the hardware model blob to be present.
    """
    path = _regular(value, "macosvm.json", limit=MAX_VM_JSON_BYTES)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"macosvm.json cannot be parsed: {path}") from error
    if not isinstance(document, dict):
        raise ValueError("macosvm.json root must be an object")
    machine_id, machine_id_raw = _decode_vm_plist(document.get("machineId"), "machineId")
    hardware_model, hardware_model_raw = _decode_vm_plist(
        document.get("hardwareModel"), "hardwareModel"
    )
    uuid = _find_ecid(machine_id)
    if uuid is None:
        raise ValueError("macosvm.json machineId does not contain a valid ECID")
    if not isinstance(hardware_model, (dict, list, tuple)):
        raise ValueError("macosvm.json hardwareModel plist has an unexpected shape")
    storage = document.get("storage")
    if not isinstance(storage, list):
        raise ValueError("macosvm.json storage must be an array")
    aux_paths: list[Path] = []
    root_paths: list[Path] = []
    for entry in storage:
        if not isinstance(entry, dict) or not isinstance(entry.get("type"), str):
            raise ValueError("macosvm.json storage entries must contain a type")
        file_name = entry.get("file")
        if not isinstance(file_name, str) or not file_name.strip():
            raise ValueError("macosvm.json storage entries must contain a file")
        image = (path.parent / file_name).resolve(strict=True)
        if not image.is_file():
            raise ValueError(f"macosvm.json storage path is not a regular file: {image}")
        if entry["type"] == "aux":
            aux_paths.append(image)
        elif entry["type"] == "disk":
            root_paths.append(image)
    if len(aux_paths) != 1 or len(root_paths) != 1:
        raise ValueError(
            "macosvm.json must contain exactly one aux and one disk storage entry"
        )
    return MacOSVMConfiguration(
        path=path,
        uuid=uuid,
        aux=aux_paths[0],
        root=root_paths[0],
        aux_offset=MACOSVM_AUX_METADATA_BYTES,
        hardware_model_sha256=hashlib.sha256(hardware_model_raw).hexdigest(),
        machine_id_sha256=hashlib.sha256(machine_id_raw).hexdigest(),
        json_sha256=_sha256(path),
    )


def _to_wsl_path(path: Path) -> str:
    """Convert a Windows path to a path visible from WSL."""
    text = str(path)
    if os.name != "nt":
        return text
    if len(text) >= 2 and text[1] == ":":
        tail = text[2:].replace("\\", "/")
        return f"/mnt/{text[0].lower()}{tail}"
    return text.replace("\\", "/")


def _resolve_executable(value: str | Path | None, default: str, label: str) -> Executable:
    raw = str(value or os.environ.get(default) or "").strip()
    if not raw:
        raw = shutil.which(label) or ""
    if not raw:
        raise ValueError(f"{label} was not found; set {default}")

    # VMApple's private backend is a Linux binary.  A Windows GUI may pass its
    # WSL path to the bridge, which launches the full runner inside WSL.
    if os.name == "nt" and raw.startswith("/"):
        wrapper = shutil.which("wsl.exe")
        if wrapper is None:
            raise ValueError("A WSL VMApple executable was supplied but wsl.exe is unavailable")
        probe = subprocess.run([wrapper, "--", raw, "--version"], capture_output=True,
                               text=True, timeout=10, check=False)
        if probe.returncode != 0:
            raise ValueError(f"{label} cannot be executed through WSL: {probe.stderr.strip()}")
        return Executable(raw, wrapper)

    candidate = Path(raw).expanduser()
    if candidate.parent == Path("."):
        located = shutil.which(raw)
        if located is None:
            raise ValueError(f"{label} was not found on PATH: {raw}")
        candidate = Path(located)
    candidate = candidate.resolve(strict=True)
    if not candidate.is_file():
        raise ValueError(f"{label} must be a regular file: {candidate}")
    return Executable(str(candidate))


def _guest_path(path: Path, executable: Executable) -> str:
    return _to_wsl_path(path) if executable.is_wsl else str(path)


def _direct_macos_hvf_host() -> bool:
    """Return whether the host can use QEMU's native VMApple HVF path."""
    return platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}


def direct_macos_host_report() -> dict[str, object]:
    """Describe the host-side requirements for the real macOS entry.

    The normal VMApple path is an Apple-Silicon/macOS + HVF path.  Linux/x86
    TCG remains useful for the separately-scoped recovery protocol, but it is
    not a substitute for the ARM-only Golden Gate entry and is never promoted
    to a direct-boot claim.
    """
    system = platform.system()
    machine = platform.machine().lower()
    native_hvf = _direct_macos_hvf_host()
    blockers: list[str] = []
    if not native_hvf:
        blockers.append(
            "Direct macOS requires an Apple-Silicon macOS host with QEMU HVF; "
            "the current host is recovery/TCG-only."
        )
    firmware = DEFAULT_AVPBOOTER_PATH if native_hvf else None
    if firmware is not None and not firmware.is_file():
        blockers.append(f"Virtualization.framework AVPBooter is missing: {firmware}")
    return {
        "system": system,
        "architecture": machine,
        "apple_silicon_macos": native_hvf,
        "hvf_required": True,
        "native_hvf_selected": native_hvf,
        "default_avpbooter": str(firmware) if firmware is not None else None,
        "default_avpbooter_present": bool(firmware and firmware.is_file()),
        "blockers": blockers,
        "direct_macos_ready": not blockers,
    }


def _available_display_backends(executable: Executable) -> list[str]:
    """Return display backends advertised by this exact QEMU binary.

    QEMU's ``-display help`` is a capability listing, not runtime evidence.
    A failed help probe therefore yields an empty list and is recorded by the
    caller; it does not make a firmware boot claim or silently select GTK.
    """
    try:
        result = subprocess.run(
            executable.command("-display", "help"),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode:
        return []
    backends: list[str] = []
    for line in result.stdout.splitlines():
        value = line.strip().split(None, 1)[0] if line.strip() else ""
        if value and value not in backends and value in DISPLAY_BACKENDS[1:]:
            backends.append(value)
    return backends


def _effective_display_backend(
    requested: str,
    *,
    direct_macos: bool,
    available: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Resolve the portable ``auto`` display request without probing a guest.

    Native Apple-Silicon macOS prefers Cocoa.  Every non-native/research
    launch prefers headless output because it is valid on WSL and on QEMU
    builds with no GTK/SDL support.  If capability output is available, pick a
    backend actually advertised by this binary; otherwise keep the platform
    default and let QEMU produce an explicit error for an invalid build.
    """
    if requested != "auto":
        return requested
    candidates = ("cocoa", "none") if direct_macos and _direct_macos_hvf_host() else ("none", "dbus")
    advertised = set(available or ())
    if advertised:
        for candidate in candidates:
            if candidate in advertised:
                return candidate
    return candidates[0]


def probe_backend(executable: Executable, *, direct_macos: bool = False) -> dict[str, object]:
    """Require VMApple without treating capability help as boot evidence.

    Recovery remains pinned to the bounded TCG research backend.  A direct
    macOS selection on an Apple-Silicon macOS host is allowed to use HVF and
    the backend's normal PV graphics path; every other host stays on the
    explicit research-headless TCG path.
    """
    version = subprocess.run(executable.command("--version"), capture_output=True,
                             text=True, timeout=15, check=False)
    machines = subprocess.run(executable.command("-machine", "help"), capture_output=True,
                              text=True, timeout=15, check=False)
    accelerators = subprocess.run(executable.command("-accel", "help"), capture_output=True,
                                  text=True, timeout=15, check=False)
    if version.returncode or machines.returncode or accelerators.returncode:
        raise ValueError("QEMU capability probe failed")
    machine_names = {line.split()[0] for line in machines.stdout.splitlines() if line.strip()}
    if "vmapple" not in machine_names:
        raise ValueError("QEMU must expose vmapple")
    accelerator_names = set(accelerators.stdout.split())
    if not direct_macos and "tcg" not in accelerator_names:
        raise ValueError("QEMU recovery backend must expose TCG")
    if direct_macos and _direct_macos_hvf_host() and "hvf" not in accelerator_names:
        raise ValueError("Direct macOS boot on Apple Silicon requires QEMU HVF")
    research = subprocess.run(executable.command("-machine", "vmapple,help"),
                              capture_output=True, text=True, timeout=15, check=False)
    if research.returncode:
        raise ValueError("QEMU VMApple backend capability probe failed")
    if not direct_macos and "research-headless" not in research.stdout:
        raise ValueError("QEMU VMApple recovery backend does not advertise research-headless")
    research_headless = "research-headless" in research.stdout
    research_graphics = "research-graphics" in research.stdout
    bdif = subprocess.run(executable.command("-device", "vmapple-bdif,help"),
                          capture_output=True, text=True, timeout=15, check=False)
    bdif_block_writes = bool(
        bdif.returncode == 0 and "allow-block-writes" in (bdif.stdout + bdif.stderr)
    )
    display_backends = _available_display_backends(executable)
    first_line = (version.stdout or version.stderr).splitlines()
    return {
        "executable": executable.program,
        "version": first_line[0] if first_line else "",
        "vmapple": True,
        "tcg": "tcg" in accelerator_names,
        "hvf": "hvf" in accelerator_names,
        "direct_macos": direct_macos,
        "native_hvf_selected": bool(direct_macos and _direct_macos_hvf_host()),
        "direct_host": direct_macos_host_report() if direct_macos else None,
        "research_headless": research_headless,
        "research_graphics": research_graphics,
        "bdif_block_writes": bdif_block_writes,
        "display_backends": display_backends,
        "display_backend_requested": "auto",
        "display_backend_effective": _effective_display_backend(
            "auto", direct_macos=direct_macos, available=display_backends
        ),
        "virtual_soc_name": VIRTUAL_SOC_NAME,
        "virtual_model": VIRTUAL_MODEL,
        "virtual_identity_mode": "metadata-only",
        "hardware_attestation_verified": False,
        "macos_boot_verified": False,
        "soc_profile": apple_silicon_profile(),
    }


def _qcow_size(path: Path) -> int:
    with path.open("rb") as source:
        header = source.read(104)
    if len(header) != 104 or header[:4] != b"QFI\xfb":
        raise ValueError(f"Invalid qcow2 overlay header: {path}")
    version, backing_offset, backing_size = struct.unpack_from(">IQI", header, 4)
    virtual_size, crypt = struct.unpack_from(">QI", header, 24)
    incompatible = struct.unpack_from(">Q", header, 72)[0]
    if (version != 3 or backing_offset or backing_size or crypt or incompatible & ~1
            or virtual_size <= 0 or virtual_size % 512):
        raise ValueError("Overlay must be qcow2 v3, unencrypted, and have no external backing path")
    return virtual_size


def _storage_window(stream, offset: int, length: int) -> bytes:
    stream.seek(offset)
    data = stream.read(length)
    if len(data) != length:
        raise ValueError("Storage input ended while reading a diagnostic window")
    return data


def _inspect_storage_file(value: str | Path, label: str, *, offset: int = 0) -> dict[str, object]:
    """Inspect a raw AUX/root view without writing or trusting its contents.

    A zero-filled fixture is a useful protocol test, but it cannot provide the
    hardware-model-bound AUX metadata or an APFS install target that iBoot
    expects.  The marker scan below is only a hint; an APFS marker does not
    establish Apple provenance, a matching VM hardware model, or bootability.
    """
    path = _regular(value, label)
    if type(offset) is not int or offset < 0 or offset % 512:
        raise ValueError("Storage view offset must be a nonnegative 512-byte multiple")
    before = path.stat()
    view_size = before.st_size - offset
    if view_size <= 0 or view_size % 512:
        raise ValueError(f"{label} must expose a nonempty 512-byte view")

    sample_size = min(view_size, STORAGE_SAMPLE_BYTES)
    suffix_offset = offset + max(0, view_size - sample_size)
    zero_scan_size = min(view_size, STORAGE_ZERO_SCAN_BYTES)
    zero_scanned = 0
    zero_nonzero_bytes = 0
    prefix = b""
    suffix = b""
    with path.open("rb") as stream:
        prefix = _storage_window(stream, offset, sample_size)
        if suffix_offset != offset:
            suffix = _storage_window(stream, suffix_offset, sample_size)
        stream.seek(offset)
        while zero_scanned < zero_scan_size:
            chunk = stream.read(min(1024 * 1024, zero_scan_size - zero_scanned))
            if not chunk:
                raise ValueError(f"{label} ended during the zero-content scan")
            zero_scanned += len(chunk)
            # ``bytes.count`` runs in the C implementation and keeps the
            # bounded preflight cheap even for the largest scan window.
            zero_nonzero_bytes += len(chunk) - chunk.count(0)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ):
        raise ValueError(f"{label} changed during read-only inspection")

    marker_offsets: dict[str, list[int]] = {}
    windows = ((offset, prefix), (suffix_offset, suffix))
    for marker in STORAGE_MARKERS:
        locations: list[int] = []
        for base, window in windows:
            start = 0
            while len(locations) < 8:
                found = window.find(marker, start)
                if found < 0:
                    break
                absolute = base + found
                if absolute not in locations:
                    locations.append(absolute)
                start = found + 1
        if locations:
            marker_offsets[marker.decode("ascii")] = sorted(locations)

    scan_complete = zero_scanned == view_size
    all_zero: bool | None = None
    if scan_complete:
        all_zero = zero_nonzero_bytes == 0
    return {
        "path": str(path),
        "size_bytes": before.st_size,
        "view_offset": offset,
        "view_bytes": view_size,
        "sample_bytes": sample_size,
        "sample_prefix_nonzero_bytes": len(prefix) - prefix.count(0),
        "sample_suffix_nonzero_bytes": len(suffix) - suffix.count(0),
        "zero_scan_bytes": zero_scanned,
        "zero_scan_complete": scan_complete,
        "zero_scan_nonzero_bytes": zero_nonzero_bytes,
        "all_zero": all_zero,
        "markers": marker_offsets,
        "read_only": True,
    }


def inspect_storage(*, aux: str | Path, root: str | Path, aux_offset: int = 0) -> dict[str, object]:
    """Return a bounded, read-only readiness report for AUX and root images.

    ``provisioned`` is never inferred from a byte signature.  It is false for
    a definite zero fixture and otherwise remains ``None`` until a
    hardware-model-matched provisioning receipt is supplied by a supported
    Apple virtualization host.  This keeps the report useful without turning
    a heuristic into an installer or boot claim.
    """
    aux_report = _inspect_storage_file(aux, "AUX base image", offset=aux_offset)
    root_report = _inspect_storage_file(root, "root base image")
    reports = (aux_report, root_report)
    zero_roles = [
        role for role, report in (("aux", aux_report), ("root", root_report))
        if report.get("all_zero") is True
    ]
    incomplete_roles = [
        role for role, report in (("aux", aux_report), ("root", root_report))
        if report.get("all_zero") is None
    ]
    markers = sorted({marker for report in reports for marker in report["markers"]})
    blockers: list[str] = []
    if "aux" in zero_roles:
        blockers.append("AUX view is zero-filled and has no hardware-model initialization")
    if "root" in zero_roles:
        blockers.append("root view is zero-filled and contains no install target")
    if incomplete_roles:
        blockers.append("zero scan is bounded for: " + ", ".join(incomplete_roles))
    if not markers:
        blockers.append("no known APFS marker was found in sampled windows; provisioning remains unverified")
    if len(zero_roles) == 2:
        provisioning_status = "unprovisioned-zero"
        provisioned: bool | None = False
        installer_possible: bool | None = False
    elif zero_roles:
        provisioning_status = "partially-unprovisioned"
        provisioned: bool | None = False
        installer_possible: bool | None = False
    elif incomplete_roles:
        provisioning_status = "unverified-bounded-scan"
        provisioned = None
        installer_possible = None
    else:
        provisioning_status = "unverified"
        provisioned = None
        installer_possible = None
    return {
        "schema": "26x86.vmapple-storage/1",
        "aux": aux_report,
        "root": root_report,
        "markers": markers,
        "zero_roles": zero_roles,
        "bounded_scan_roles": incomplete_roles,
        "provisioned": provisioned,
        "provisioning_status": provisioning_status,
        "installer_ui_possible": installer_possible,
        "installer_ui_verified": False,
        "base_images_read_only": True,
        "blockers": blockers,
        "note": (
            "AUX must be initialized for the exact VM hardware model and the root image must contain "
            "an install target. Byte markers alone cannot establish either condition."
        ),
    }


def inspect_macosvm_storage(value: str | Path) -> dict[str, object]:
    """Inspect the exact read-only storage view described by ``macosvm.json``.

    ``macosvm.json`` references the original AUX file, so this helper applies
    QEMU's documented metadata trim as a view offset without creating a
    trimmed copy or modifying either input image.
    """
    bundle = load_macosvm_configuration(value)
    report = inspect_storage(
        aux=bundle.aux,
        root=bundle.root,
        aux_offset=bundle.aux_offset,
    )
    report["vm_bundle"] = bundle.report()
    report["aux_offset_source"] = "macosvm.json documented metadata trim"
    return report


@dataclass(frozen=True)
class StorageSession:
    directory: Path
    aux_base: Path
    root_base: Path
    aux_overlay: Path
    root_overlay: Path
    aux_offset: int

    def arguments(self, executable: Executable, *, allow_bdif_writes: bool = True) -> list[str]:
        """Build an explicit immutable-base + qcow2-writable graph.

        The optional BDIF property exists only in the project write-enabled
        QEMU patch.  The upstream VMApple device is read-only at the BDIF
        command layer, so omitting the property is still a valid read/boot
        experiment and, crucially, avoids passing an unknown ``-global`` to an
        otherwise usable upstream binary.
        """
        if type(allow_bdif_writes) is not bool:
            raise ValueError("allow_bdif_writes must be an explicit boolean")
        aux_size = self.aux_base.stat().st_size - self.aux_offset
        root_size = self.root_base.stat().st_size
        if aux_size <= 0 or root_size <= 0 or aux_size % 512 or root_size % 512:
            raise ValueError("AUX view and root base must be nonempty 512-byte multiples")
        if _qcow_size(self.aux_overlay) != aux_size or _qcow_size(self.root_overlay) != root_size:
            raise ValueError("COW overlay size does not match its immutable base view")

        result: list[str] = []
        if allow_bdif_writes:
            result.extend(["-global", "vmapple-bdif.allow-block-writes=on"])
        for index, (role, base, overlay, size) in enumerate((
            ("aux", self.aux_base, self.aux_overlay, aux_size),
            ("root", self.root_base, self.root_overlay, root_size),
        )):
            # Block node names follow QEMU's identifier grammar (alphanumeric,
            # dot, and hyphen; underscores are rejected before graph parsing).
            # QEMU additionally requires the first character to be alphabetic.
            node_name = "x86" + role
            backing = {
                "driver": "raw",
                "read-only": True,
                "offset": self.aux_offset if role == "aux" else 0,
                "file": {"driver": "file", "filename": _guest_path(base, executable),
                         "read-only": True},
            }
            node = {
                "driver": "qcow2",
                "node-name": node_name,
                "read-only": False,
                "file": {"driver": "file", "filename": _guest_path(overlay, executable)},
                "backing": backing,
            }
            result.extend(["-blockdev", json.dumps(node, separators=(",", ":"))])
            view = "json:" + json.dumps({"driver": "raw", "file": node_name},
                                         separators=(",", ":"))
            # QemuOpts uses doubled commas inside a value.
            result.extend([
                "-drive", f"if=pflash,index={index},readonly=off,file={view.replace(',', ',,')}",
                "-drive", f"if=none,id={role}disk,werror=report,rerror=report,"
                           f"cache=writeback,file={view.replace(',', ',,')}",
                "-device", f"vmapple-virtio-blk-pci,variant={role},drive={role}disk,share-rw=on",
            ])
        return result


def _new_directory(value: str | Path | None) -> Path:
    if value:
        destination = Path(value).expanduser().absolute()
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Output directory must be new: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir()
        return destination
    parent = Path(os.environ.get("X86_VMAPLE_OUTPUT_ROOT", tempfile.gettempdir())).expanduser()
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="26x86-vmapple-", dir=parent))


def create_storage(*, aux: Path, root: Path, directory: Path,
                   qemu_img: Executable, aux_offset: int) -> StorageSession:
    if type(aux_offset) is not int or aux_offset < 0 or aux_offset % 512:
        raise ValueError("AUX offset must be a nonnegative multiple of 512")
    aux_size = aux.stat().st_size - aux_offset
    root_size = root.stat().st_size
    if aux_size <= 0 or root_size <= 0 or aux_size % 512 or root_size % 512:
        raise ValueError("AUX/root inputs must expose nonempty 512-byte views")
    storage = directory / "storage"
    storage.mkdir()
    overlays = (storage / "aux.qcow2", storage / "root.qcow2")
    for overlay, size in zip(overlays, (aux_size, root_size)):
        completed = subprocess.run(
            qemu_img.command("create", "-f", "qcow2", "-o", "compat=1.1,lazy_refcounts=off",
                             _guest_path(overlay, qemu_img), str(size)),
            capture_output=True, text=True, timeout=30, check=False,
        )
        if completed.returncode:
            raise ValueError(f"qemu-img failed to create {overlay.name}: {completed.stderr.strip()}")
        if _qcow_size(overlay) != size:
            raise ValueError(f"qemu-img created an unexpected {overlay.name} size")
    metadata = {
        "schema": 1,
        "base_images_read_only": True,
        "writes": "separate qcow2 overlays",
        "aux_offset": aux_offset,
        "bases": {
            "aux": {"path": str(aux), "bytes": aux.stat().st_size, "sha256": _sha256(aux)},
            "root": {"path": str(root), "bytes": root.stat().st_size, "sha256": _sha256(root)},
        },
        "macos_boot_verified": False,
    }
    (storage / "session.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return StorageSession(directory, aux, root, overlays[0], overlays[1], aux_offset)


class RecoveryTransport:
    """Small host transport for the observed VMApple USB chardev framing."""

    def __init__(self, socket_path: str, timeout: float = 5.0):
        if not hasattr(socket, "AF_UNIX"):
            raise ValueError("VMApple recovery requires Unix sockets; run it inside WSL/Linux")
        if not 0 < timeout <= 60:
            raise ValueError("Recovery socket timeout must be between 0 and 60 seconds")
        self.path = socket_path
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout
        try:
            self.socket.connect(socket_path)
        except BaseException:
            self.socket.close()
            raise

    def __enter__(self) -> "RecoveryTransport":
        return self

    def __exit__(self, *_: object) -> None:
        self.socket.close()

    def _read_exact(self, count: int) -> bytes:
        data = bytearray()
        while len(data) < count:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Recovery socket deadline exceeded")
            self.socket.settimeout(remaining)
            chunk = self.socket.recv(count - len(data))
            if not chunk:
                raise RecoveryProtocolError("Recovery socket closed mid-frame")
            data.extend(chunk)
        return bytes(data)

    def _receive(self, expected_type: int, endpoint: int = 0) -> bytes:
        size = struct.unpack("<I", self._read_exact(4))[0]
        if not 2 <= size <= MAX_FRAME_BYTES:
            raise RecoveryProtocolError("Invalid recovery frame length")
        response = self._read_exact(size)
        if response == bytes((2, endpoint)):
            raise RecoveryProtocolError(f"Guest USB endpoint stalled: {response.hex()}")
        if len(response) < 2 or response[0] != expected_type or response[1] != endpoint:
            raise RecoveryProtocolError("Guest reported an unexpected transfer type or endpoint")
        return response[2:]

    def _send(self, transfer_type: int, data: bytes, endpoint: int = 0) -> None:
        packet = struct.pack("<iBB", len(data), endpoint, transfer_type) + data
        if len(packet) > MAX_FRAME_BYTES:
            raise ValueError("Recovery packet exceeds the transport bound")
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Recovery socket deadline exceeded")
        self.socket.settimeout(remaining)
        self.socket.sendall(struct.pack("<I", len(packet)) + packet)

    def control(self, request_type: int, request: int, value: int = 0, index: int = 0,
                *, length: int = 0, data: bytes = b"", deadline: float | None = None) -> bytes:
        fields = (request_type, request, value, index, length)
        if not all(type(item) is int for item in fields):
            raise ValueError("USB setup fields must be integers")
        if not (0 <= request_type <= 255 and 0 <= request <= 255
                and 0 <= value <= 65535 and 0 <= index <= 65535
                and 0 <= length <= 65535):
            raise ValueError("USB setup field out of range")
        incoming = bool(request_type & 0x80)
        if (incoming and data) or (not incoming and length != len(data)):
            raise ValueError("USB direction and data phase disagree")
        setup = struct.pack("<BBHHH", request_type, request, value, index, length)
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            if isinstance(deadline, bool) or not isinstance(deadline, (int, float)):
                raise ValueError("USB transfer deadline must be a monotonic timestamp")
            self.deadline = min(self.deadline, float(deadline))
        self._send(1, setup + data)
        payload = self._receive(1)
        if incoming and len(payload) > length:
            raise RecoveryProtocolError("Guest returned more USB data than requested")
        if not incoming and payload:
            raise RecoveryProtocolError("Unexpected payload on USB OUT completion")
        return payload

    def descriptor(self, kind: int, index: int = 0, length: int = 255,
                   language: int | None = None, *, deadline: float | None = None) -> bytes:
        language_id = (0x409 if kind == 3 else 0) if language is None else language
        return self.control(0x80, 6, kind << 8 | index, language_id,
                            length=length, deadline=deadline)

    def dfu_state(self, *, deadline: float | None = None) -> int:
        data = self.control(0xA1, 5, length=1, deadline=deadline)
        if len(data) != 1 or data[0] > 10:
            raise RecoveryProtocolError("DFU GETSTATE did not return one valid byte")
        return data[0]

    def dfu_status(self, *, deadline: float | None = None) -> dict[str, int | str]:
        data = self.control(0xA1, 3, length=6, deadline=deadline)
        if len(data) != 6 or data[0] > 15 or data[4] > 10:
            raise RecoveryProtocolError("DFU GETSTATUS did not return six valid bytes")
        return {"raw": data.hex(), "status": data[0],
                "poll_timeout_ms": int.from_bytes(data[1:4], "little"),
                "state": data[4], "string_index": data[5]}

    def _wait_state(self, target: int, transient: set[int], deadline: float,
                    records: list[dict[str, int | str]]) -> None:
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("DFU state deadline exceeded")
            status = self.dfu_status()
            records.append(status)
            if status["status"]:
                raise RecoveryProtocolError(f"Guest DFU error {status['status']}")
            if status["state"] == target:
                return
            if status["state"] not in transient:
                raise RecoveryProtocolError(f"Unexpected DFU state {status['state']}; expected {target}")
            time.sleep(min(max(float(status["poll_timeout_ms"]) / 1000, 0.001), 0.25))

    def usb_reset(self, *, deadline: float | None = None) -> None:
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        self._send(2, b"")
        if self._receive(4):
            raise RecoveryProtocolError("USB reset acknowledgement contained a payload")

    def bulk_out(self, data: bytes, endpoint: int = 4, *, deadline: float | None = None) -> None:
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        self._send(1, data, endpoint)
        if self._receive(1, endpoint):
            raise RecoveryProtocolError("Bulk OUT acknowledgement contained a payload")

    def bulk_in(self, endpoint: int = 0x81, *, deadline: float | None = None) -> bytes:
        """Request one queued USB IN transfer without fabricating a response."""
        if type(endpoint) is not int or not 0x81 <= endpoint <= 0x8F:
            raise ValueError("USB bulk IN endpoint must be in the 0x81..0x8f range")
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        self._send(1, b"", endpoint)
        return self._receive(1, endpoint)

    def send_command(self, command: str, *, request: int = 0,
                     deadline: float | None = None) -> bytes:
        """Send an iBoot command; the ACK is transport evidence only."""
        if not isinstance(command, str) or not 0 < len(command) < 256:
            raise ValueError("iBoot command must contain 1..255 bytes")
        encoded = command.encode("ascii")
        if any(value < 32 or value > 126 for value in encoded):
            raise ValueError("iBoot command must be printable ASCII")
        return self.control(0x40, request, length=len(encoded) + 1,
                            data=encoded + b"\0", deadline=deadline)

    def configure_recovery(self, *, deadline: float | None = None) -> dict[str, object]:
        """Select a genuine Apple recovery configuration and endpoint 4."""
        device = self.descriptor(1, length=18, deadline=deadline)
        if (len(device) != 18 or device[:2] != b"\x12\x01"
                or device[8:10] != b"\xac\x05"
                or not 0x1280 <= int.from_bytes(device[10:12], "little") <= 0x1283):
            raise RecoveryProtocolError("Expected an actual Apple iBEC recovery device")
        header = self.descriptor(2, length=9, deadline=deadline)
        if len(header) != 9 or header[:2] != b"\x09\x02":
            raise RecoveryProtocolError("Missing recovery configuration header")
        length = int.from_bytes(header[2:4], "little")
        if not 9 <= length <= 4096:
            raise RecoveryProtocolError("Recovery configuration length is out of bounds")
        configuration = self.descriptor(2, length=length, deadline=deadline)
        if len(configuration) != length or configuration[:9] != header:
            raise RecoveryProtocolError("Recovery configuration descriptor is inconsistent")
        endpoint: int | None = None
        offset = 0
        while offset < length:
            size = configuration[offset]
            if size < 2 or offset + size > length:
                raise RecoveryProtocolError("Invalid recovery USB descriptor structure")
            item = configuration[offset:offset + size]
            if item[1] == 5 and size >= 7 and item[2] == 4 and item[3] & 3 == 2:
                endpoint = item[2]
            offset += size
        if endpoint != 4:
            raise RecoveryProtocolError("Recovery bulk OUT endpoint 4 was not advertised")
        self.control(0x00, 9, value=configuration[5], deadline=deadline)
        return {"device_descriptor_hex": device.hex(),
                "configuration_hex": configuration.hex(),
                "configuration_value": configuration[5],
                "bulk_out_endpoint": endpoint}

    def send_dfu_file(self, path: Path, *, expected_sha256: str | None = None,
                      total_timeout: float = 300, reset: bool = True) -> dict[str, object]:
        image = path.read_bytes()
        if not 0 < len(image) <= MAX_DFU_BYTES:
            raise ValueError("iBSS input must be between 1 byte and 64 MiB")
        digest = hashlib.sha256(image).hexdigest()
        if expected_sha256 and digest != expected_sha256.lower():
            raise ValueError("iBSS SHA-256 does not match the requested artifact")
        suffix = DFU_SUFFIX + struct.pack("<I", zlib.crc32(image + DFU_SUFFIX) ^ 0xFFFFFFFF)
        wire = image + suffix
        deadline = time.monotonic() + total_timeout
        report: dict[str, object] = {
            "schema": 1, "image_path": str(path), "image_size": len(image),
            "image_sha256": digest, "dfu_suffix_hex": suffix.hex(), "bytes_sent": 0,
            "image_bytes_sent": 0, "blocks": [], "manifest_statuses": [],
            "transfer_complete": False, "usb_reset_acknowledged": False,
            "guest_responses_preserved": True, "signature_acceptance_verified": False,
            "macos_boot_verified": False, "input_integrity": False, "error": None,
        }
        try:
            initial = self.dfu_state()
            report["initial_state"] = initial
            if initial != 2:
                raise RecoveryProtocolError(f"DFU upload requires IDLE state 2; got {initial}")
            for number, offset in enumerate(range(0, len(wire), DFU_BLOCK_BYTES)):
                block = wire[offset:offset + DFU_BLOCK_BYTES]
                self.control(0x21, 1, value=number, length=len(block), data=block)
                report["bytes_sent"] = int(report["bytes_sent"]) + len(block)
                report["image_bytes_sent"] = min(int(report["bytes_sent"]), len(image))
                entry: dict[str, object] = {"number": number, "size": len(block), "statuses": []}
                cast_blocks = report["blocks"]
                assert isinstance(cast_blocks, list)
                cast_blocks.append(entry)
                self._wait_state(5, {3, 4}, deadline, entry["statuses"])  # type: ignore[arg-type]
            self.control(0x21, 1, value=len(report["blocks"]))  # type: ignore[arg-type]
            self._wait_state(8, {6, 7}, deadline, report["manifest_statuses"])  # type: ignore[arg-type]
            report["final_state"] = self.dfu_state()
            if report["final_state"] != 8:
                raise RecoveryProtocolError("DFU state changed before USB reset")
            report["transfer_complete"] = True
            if reset:
                self.usb_reset()
                report["usb_reset_acknowledged"] = True
        except BaseException as error:
            report["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            report["input_integrity"] = _sha256(path) == digest
            if not report["input_integrity"]:
                report["error"] = "iBSS source changed during upload"
        return report

    def probe(self) -> dict[str, object]:
        device = self.descriptor(1, length=18)
        if len(device) != 18 or device[:2] != b"\x12\x01":
            raise RecoveryProtocolError("Missing complete USB device descriptor")
        vendor, product = struct.unpack_from("<HH", device, 8)
        header = self.descriptor(2, length=9)
        if len(header) != 9 or header[:2] != b"\x09\x02":
            raise RecoveryProtocolError("Missing USB configuration header")
        length = int.from_bytes(header[2:4], "little")
        if not 9 <= length <= 4096:
            raise RecoveryProtocolError("USB configuration length is out of bounds")
        configuration = self.descriptor(2, length=length)
        if len(configuration) != length or configuration[:9] != header:
            raise RecoveryProtocolError("USB configuration descriptor is inconsistent")
        endpoint: int | None = None
        offset = 0
        while offset < length:
            size = configuration[offset]
            if size < 2 or offset + size > length:
                raise RecoveryProtocolError("Invalid USB descriptor structure")
            item = configuration[offset:offset + size]
            if item[1] == 5 and size >= 7 and item[2] == 4 and item[3] & 3 == 2:
                endpoint = item[2]
            offset += size
        dfu_state_value: int | None = None
        dfu_status_value: dict[str, int | str] | None = None
        dfu_control_error: str | None = None
        try:
            dfu_state_value = self.dfu_state()
            dfu_status_value = self.dfu_status()
        except (RecoveryProtocolError, OSError, TimeoutError) as error:
            # iBEC is a recovery interface, not necessarily a DFU class
            # interface. Keep the descriptor evidence and make this optional
            # control failure explicit instead of hiding a bulk endpoint.
            dfu_control_error = f"{type(error).__name__}: {error}"
        result = {
            "usb_vendor": f"{vendor:04x}", "usb_product": f"{product:04x}",
            "device_descriptor_hex": device.hex(),
            "configuration_hex": configuration.hex(),
            "configuration_value": configuration[5],
            "bulk_out_endpoint": endpoint,
            "dfu_state": dfu_state_value,
            "dfu_status": dfu_status_value,
        }
        if dfu_control_error:
            result["dfu_control_error"] = dfu_control_error
        return result

    def send_recovery_file(self, path: Path, *, total_timeout: float = 300,
                           expected_sha256: str | None = None) -> dict[str, object]:
        image = path.read_bytes()
        if not 0 < len(image) <= MAX_RECOVERY_BYTES:
            raise ValueError("iBEC input must be between 1 byte and 512 MiB")
        digest = hashlib.sha256(image).hexdigest()
        if expected_sha256 is not None and digest != expected_sha256.lower():
            raise ValueError("Recovery image SHA-256 does not match the expected generated artifact")
        deadline = time.monotonic() + total_timeout
        report: dict[str, object] = {
            "schema": 1, "image_path": str(path), "image_size": len(image),
            "image_sha256": digest, "bytes_sent": 0, "blocks": [],
            "transfer_complete": False, "signature_acceptance_verified": False,
            "macos_boot_verified": False, "input_integrity": False, "error": None,
        }
        try:
            self.control(0x41, 0)
            for offset in range(0, len(image), 0x8000):
                if time.monotonic() >= deadline:
                    raise TimeoutError("iBEC upload deadline exceeded")
                block = image[offset:offset + 0x8000]
                self.bulk_out(block)
                report["bytes_sent"] = int(report["bytes_sent"]) + len(block)
                report["blocks"].append({"offset": offset, "size": len(block), "acknowledged": True})
            if len(image) % 512 == 0:
                self.bulk_out(b"")
                report["zero_length_packet"] = True
            report["transfer_complete"] = True
        except BaseException as error:
            report["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            report["input_integrity"] = _sha256(path) == digest
            if not report["input_integrity"]:
                report["error"] = "iBEC source changed during upload"
        return report


def _wait_for_socket(socket_path: str, process: subprocess.Popen[bytes], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise VMappleError(f"QEMU exited before the recovery socket appeared: {process.returncode}")
        if Path(socket_path).exists():
            return
        time.sleep(0.05)
    raise TimeoutError(f"Recovery socket did not appear: {socket_path}")


def _inputs_intact(inputs: object) -> bool:
    """Re-hash caller inputs without ever opening them for writing."""
    if not isinstance(inputs, dict) or not inputs:
        return False
    for item in inputs.values():
        if not isinstance(item, dict):
            return False
        path_value = item.get("path")
        expected = item.get("sha256")
        if not isinstance(path_value, str) or not isinstance(expected, str):
            return False
        try:
            path = Path(path_value)
            if not path.is_file() or _sha256(path) != expected.lower():
                return False
        except (OSError, ValueError):
            return False
    return True


def _write_report(output: Path, report: dict[str, object]) -> None:
    """Persist a UTF-8 report atomically enough for GUI readers."""
    temporary = output / "launch.json.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output / "launch.json")


def _probe_transition(socket_path: str, timeout: float) -> dict[str, object]:
    """Poll real descriptors after reset; never synthesize a next-stage device."""
    deadline = time.monotonic() + timeout
    attempts: list[dict[str, object]] = []
    last: dict[str, object] | None = None
    # The old 240-attempt cap made a nominal five-minute timeout end after
    # roughly 24 seconds.  Keep the historical minimum for fast tests, but
    # let a caller-supplied deadline actually bound the observation window.
    attempt_limit = max(MAX_TRANSITION_ATTEMPTS, int(timeout / 0.1) + 1)
    while time.monotonic() < deadline and len(attempts) < attempt_limit:
        try:
            with RecoveryTransport(socket_path, timeout=min(2.0, max(deadline - time.monotonic(), 0.1))) as transport:
                last = transport.probe()
                if last.get("bulk_out_endpoint") == 4:
                    value = last.get("configuration_value")
                    if not isinstance(value, int) or not 0 <= value <= 255:
                        raise RecoveryProtocolError("Recovery configuration value is missing")
                    # iBEC exposes a bulk recovery interface rather than a
                    # DFU class interface; select its real configuration
                    # before any endpoint transfer.
                    transport.control(0x00, 9, value=value)
                    last["configuration_selected"] = True
            attempts.append(last)
            if last.get("bulk_out_endpoint") == 4:
                return {"state": "ibec-ready", "attempts": attempts, "last": last,
                        "forced_transition": False}
        except (OSError, TimeoutError, RecoveryProtocolError) as error:
            attempts.append({"error": f"{type(error).__name__}: {error}"})
        time.sleep(0.1)
    return {
        "state": "transition-blocked",
        "attempts": attempts[-MAX_TRANSITION_ATTEMPTS:],
        "last": last,
        "forced_transition": False,
        "reason": "iBSS remained in DFU or the recovery endpoint was not advertised",
    }


def _read_log_tail(path: Path) -> tuple[int, bytes]:
    """Read a bounded UART tail and return its absolute file offset."""
    size = path.stat().st_size
    start = max(0, size - MAX_LOG_BYTES)
    with path.open("rb") as stream:
        stream.seek(start)
        return start, stream.read(MAX_LOG_BYTES)


def _wait_serial_marker(path: Path, marker: bytes, timeout: float,
                        process: subprocess.Popen[bytes] | None = None) -> dict[str, object]:
    """Observe a real UART marker without treating it as a macOS boot claim."""
    if not 0 < timeout <= 3600:
        raise ValueError("UART marker timeout must be between 0 and 3600 seconds")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            # UART logs can grow without bound while a guest is alive.  The
            # marker is emitted near the transition, so retaining only the
            # bounded tail gives the same evidence without repeatedly loading
            # an unbounded file into the runner.
            start, data = _read_log_tail(path)
        except OSError:
            start = 0
            data = b""
        position = data.find(marker)
        if position >= 0:
            return {"observed": True, "marker": marker.decode("ascii"),
                    "byte_offset": start + position}
        if process is not None and process.poll() is not None:
            break
        time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
    return {"observed": False, "marker": marker.decode("ascii"),
            "reason": "UART marker was not observed before the guest exited or deadline"}


def _observe_direct_macos_boot(
    path: Path,
    timeout: float,
    process: subprocess.Popen[bytes] | None = None,
) -> dict[str, object]:
    """Observe the direct AVPBooter -> XNU -> macOS userspace boundary.

    This is intentionally a UART observer rather than a synthetic boot
    success hook.  The current VMApple QEMU research backend may expose only a
    serial channel, and macOS may not print every marker on every build.  The
    report therefore keeps each observed marker and byte offset, and only
    raises ``macos_boot_verified`` after both an XNU and a userspace marker are
    present in the same run.
    """
    if not 0 < timeout <= 3600:
        raise ValueError("Direct macOS observation timeout must be between 0 and 3600 seconds")
    categories = (
        ("xnu", DIRECT_XNU_MARKERS),
        ("userspace", DIRECT_USERSPACE_MARKERS),
        ("installer", DIRECT_INSTALLER_MARKERS),
    )
    observed: dict[str, list[dict[str, object]]] = {name: [] for name, _ in categories}
    seen_offsets: set[tuple[str, int]] = set()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            start, data = _read_log_tail(path)
        except OSError:
            start, data = 0, b""
        for category, markers in categories:
            for marker in markers:
                position = data.find(marker)
                if position < 0:
                    continue
                absolute = start + position
                key = (category, absolute)
                if key in seen_offsets:
                    continue
                seen_offsets.add(key)
                observed[category].append({
                    "marker": marker.decode("ascii"),
                    "byte_offset": absolute,
                })
        if observed["xnu"] and observed["userspace"]:
            break
        if process is not None and process.poll() is not None:
            break
        time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))

    xnu_executed = bool(observed["xnu"])
    userspace_reached = bool(observed["userspace"])
    macos_boot_verified = xnu_executed and userspace_reached
    if macos_boot_verified:
        blocker = None
    elif not xnu_executed:
        blocker = "Direct macOS path did not emit a Darwin/XNU UART marker"
    elif not userspace_reached:
        blocker = "XNU UART evidence was observed, but macOS userspace did not reach launchd/loginwindow/WindowServer"
    else:  # defensive branch for future marker policy changes
        blocker = "Direct macOS boot evidence was incomplete"
    return {
        "xnu_executed": xnu_executed,
        "macos_userspace_reached": userspace_reached,
        "macos_boot_verified": macos_boot_verified,
        "installer_ui_visible": bool(observed["installer"]),
        # Reaching userspace is not proof that a Golden Gate installation was
        # performed; an installation receipt or an explicit installer UI
        # observation is required for that separate claim.
        "installation_verified": False,
        "observed_markers": observed,
        "direct_boot_blocker": blocker,
        "observation_timeout_seconds": timeout,
    }


def _command_for(config: "VMappleConfig", executable: Executable, storage: StorageSession,
                 socket_path: str, output: Path, *,
                 bdif_block_writes: bool = True,
                 display_backend: str | None = None) -> list[str]:
    guest_firmware = _guest_path(config.firmware, executable)
    guest_serial = _guest_path(output / "serial.log", executable)
    guest_trace = _guest_path(output / "transport.log", executable)
    use_hvf = config.boot_selection == MACOS_ENTRY_ID and _direct_macos_hvf_host()
    machine = f"vmapple,uuid={config.uuid}"
    accelerator = "hvf" if use_hvf else "tcg,thread=single"
    cpu = "host" if use_hvf else "max,pauth=on,pauth-qarma5=on,cntfrq=24000000"
    if not use_hvf:
        machine = f"vmapple,research-headless=on,uuid={config.uuid}"
    direct_macos = config.boot_selection == MACOS_ENTRY_ID
    effective_display = display_backend or _effective_display_backend(
        config.display, direct_macos=direct_macos
    )
    args: list[str] = [
        "-M", machine,
        "-accel", accelerator,
        "-cpu", cpu,
        "-m", f"{config.memory_mib}M", "-smp", str(config.smp),
        "-bios", guest_firmware,
        # Pin the guest-facing M1 identity explicitly instead of relying only
        # on QEMU's defaults.  This is a metadata selection for iBoot probing,
        # not a claim that the host is Apple silicon.
        "-global", f"vmapple-cfg.soc_name={VIRTUAL_SOC_NAME}",
        "-global", f"vmapple-cfg.model={VIRTUAL_MODEL}",
    ]
    try:
        storage_arguments = storage.arguments(
            executable, allow_bdif_writes=bdif_block_writes
        )
    except TypeError as error:
        # Keep small third-party/test storage adapters source-compatible
        # with the pre-capability API.  The project StorageSession above
        # always accepts the keyword, so a genuine storage failure is not
        # hidden here.
        if "allow_bdif_writes" not in str(error):
            raise
        storage_arguments = storage.arguments(executable)
    args.extend(storage_arguments)
    args.extend([
        "-display", effective_display, "-monitor", "none",
        "-serial", f"file:{guest_serial}", "-nic", "none", "-no-reboot",
        "-d", "guest_errors,unimp",
    ])
    if not direct_macos:
        # Recovery alone owns the USB chardev.  Direct AVPBooter entry must
        # expose the same device graph as the documented normal VMApple
        # launch; attaching a DFU socket here can change the BDIF config that
        # iBoot sees before it ever reads the installed guest disk.
        args.extend([
            "-chardev", f"socket,id=vusb,path={socket_path},server=on,wait=off",
            "-global", "vmapple-bdif.usbdev=vusb",
            # This switch is an explicit negative-capability experiment.  It
            # is deliberately absent from the normal path because the
            # original iBSS faults when the optional region is advertised as
            # unavailable.
            "-trace", f"enable=bdif_*,file={guest_trace}",
        ])
    if config.optional_rpc_unavailable and not direct_macos:
        args.extend([
            "-global", "vmapple-cfg.optional-rpc-unavailable=on",
            # QEMU's trace parser treats commas as option separators, so the
            # optional pattern must use its own -trace option.
            "-trace", f"enable=vmapple_optional_rpc_*,file={guest_trace}",
        ])
    return executable.command(*args)


@dataclass(frozen=True)
class VMappleConfig:
    target_major: int
    qemu: str | None
    firmware: str
    ibss: str
    aux: str
    root: str
    output: str | None = None
    vm_json: str | None = None
    ibec: str | None = None
    qemu_img: str | None = None
    display: str = "auto"
    uuid: int = 0
    aux_offset: int = 0
    memory_mib: int = 4096
    smp: int = 2
    transition_timeout: float = 300.0
    duration: float | None = None
    research_only: bool = False
    build_manifest: str | None = None
    tss_helper: str | None = None
    original_ibss: str | None = None
    original_ibec: str | None = None
    live_personalize: bool = False
    optional_rpc_unavailable: bool = False
    restore_chain: bool = False
    restore_role_dir: str | None = None
    restore_timeout: float = 900.0
    machine_type: str = IBOOT_MACHINE_TYPE
    guest_os: str = MACOS_GUEST_OS
    recovery_protocol: str = "DFU/IPSW"
    recovery_image_name: str = DEFAULT_RECOVERY_IMAGE
    boot_picker_enabled: bool = True
    boot_delay_seconds: float = BOOT_DELAY_SECONDS
    boot_selection: str = RECOVERY_ENTRY_ID
    boot_picker_trigger: str = "runner-default-recovery"

    def resolve_vm_configuration(self) -> tuple["VMappleConfig", dict[str, object] | None]:
        """Resolve one macosvm.json atomically before QEMU capability probing."""
        if not self.vm_json:
            return self, None
        bundle = load_macosvm_configuration(self.vm_json)

        # The JSON contract identifies the original aux.img, not the trimmed
        # pflash view used by QEMU.  A non-zero caller value is accepted only
        # when it agrees with the documented metadata prefix; silently using a
        # different offset would bind the ECID to the wrong guest storage.
        if self.aux_offset not in (0, bundle.aux_offset):
            raise ValueError(
                "AUX offset conflicts with macosvm.json; expected "
                f"0x{bundle.aux_offset:x} for the untrimmed aux.img"
            )

        def compatible_path(label: str, explicit: str, bundled: Path) -> str:
            if explicit:
                try:
                    candidate = Path(explicit).expanduser().resolve(strict=True)
                except OSError as error:
                    raise ValueError(f"{label} path cannot be resolved") from error
                if candidate != bundled:
                    raise ValueError(
                        f"{label} conflicts with macosvm.json; refusing to mix VM inputs"
                    )
            return str(bundled)

        if self.uuid and self.uuid != bundle.uuid:
            raise ValueError(
                f"uuid conflicts with macosvm.json ECID ({self.uuid} != {bundle.uuid})"
            )
        resolved = replace(
            self,
            uuid=bundle.uuid,
            aux=compatible_path("AUX", self.aux, bundle.aux),
            root=compatible_path("root", self.root, bundle.root),
            aux_offset=bundle.aux_offset,
            vm_json=None,
        )
        return resolved, bundle.report()

    def validate(self) -> tuple[Executable, Executable, dict[str, Path]]:
        if self.vm_json:
            resolved, _ = self.resolve_vm_configuration()
            return resolved.validate()
        # Scope is checked before resolving executables or opening any caller
        # supplied firmware/storage input.  An iOS/iPadOS request therefore
        # cannot reach the DFU uploader even when all paths are valid.
        validate_iboot_scope(
            self.machine_type,
            self.guest_os,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
            recovery_enabled=True,
            target_major=self.target_major,
        )
        picker = validate_boot_picker_config(
            enabled=self.boot_picker_enabled,
            delay_seconds=self.boot_delay_seconds,
            alt_key=DEFAULT_ALT_KEY,
            show_picker_on_alt=True,
            target_major=self.target_major,
            recovery_enabled=True,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
        )
        if type(self.boot_picker_enabled) is not bool:
            raise ValueError("VMApple boot_picker_enabled must be a boolean")
        if self.boot_selection not in (MACOS_ENTRY_ID, RECOVERY_ENTRY_ID):
            raise ValueError("VMApple boot selection must be macos or recovery")
        if not isinstance(self.boot_picker_trigger, str) or not self.boot_picker_trigger.strip():
            raise ValueError("VMApple boot picker trigger must be a nonempty string")
        if self.boot_picker_enabled and self.boot_selection == RECOVERY_ENTRY_ID and not picker.get("recovery_entry_enabled"):
            raise ValueError("VMApple Recovery entry is disabled")
        if self.target_major not in (26, 27):
            raise ValueError("VMApple target must be macOS 26 or 27")
        if not self.research_only:
            raise ValueError("VMApple launch requires the explicit --research-only flag")
        if self.display not in DISPLAY_BACKENDS:
            raise ValueError("VMApple display must be auto, GTK, SDL, Cocoa, none, or dbus")
        if type(self.uuid) is not int or not 0 <= self.uuid < 2**64:
            raise ValueError("VMApple uuid must fit an unsigned 64-bit integer")
        if type(self.aux_offset) is not int or self.aux_offset < 0 or self.aux_offset % 512:
            raise ValueError("AUX offset must be a nonnegative 512-byte multiple")
        if type(self.memory_mib) is not int or not 512 <= self.memory_mib <= 1024 * 1024:
            raise ValueError("VMApple memory must be between 512 MiB and 1 TiB")
        if type(self.smp) is not int or not 1 <= self.smp <= 32:
            raise ValueError("VMApple SMP must be between 1 and 32 CPUs")
        if (
            isinstance(self.transition_timeout, bool)
            or not isinstance(self.transition_timeout, (int, float))
            or not math.isfinite(float(self.transition_timeout))
            or not 0 < self.transition_timeout <= 3600
        ):
            raise ValueError("Transition timeout must be between 0 and 3600 seconds")
        if (
            self.duration is not None
            and (
                isinstance(self.duration, bool)
                or not isinstance(self.duration, (int, float))
                or not math.isfinite(float(self.duration))
                or not 0 < self.duration <= 86400
            )
        ):
            raise ValueError("Duration must be between 0 and 86400 seconds")
        if type(self.live_personalize) is not bool:
            raise ValueError("VMApple live_personalize must be a boolean")
        if type(self.optional_rpc_unavailable) is not bool:
            raise ValueError("VMApple optional_rpc_unavailable must be a boolean")
        if type(self.restore_chain) is not bool:
            raise ValueError("VMApple restore_chain must be a boolean")
        if self.boot_selection == MACOS_ENTRY_ID and self.live_personalize:
            raise ValueError("Live TSS personalization is a recovery-only operation; direct macOS boot uses the provisioned guest inputs")
        if self.boot_selection == MACOS_ENTRY_ID and self.restore_chain:
            raise ValueError("The restore-role chain is recovery-only; select macOS direct boot without --restore-chain")
        if (
            isinstance(self.restore_timeout, bool)
            or not isinstance(self.restore_timeout, (int, float))
            or not math.isfinite(float(self.restore_timeout))
            or not 0 < self.restore_timeout <= 3600
        ):
            raise ValueError("Restore timeout must be between 0 and 3600 seconds")
        qemu = _resolve_executable(self.qemu, "X86_VMAPLE_QEMU", "qemu-system-aarch64")
        qemu_img = _resolve_executable(self.qemu_img, "X86_VMAPLE_QEMU_IMG", "qemu-img")
        firmware_value = self.firmware
        if not firmware_value and self.boot_selection == MACOS_ENTRY_ID:
            discovered = direct_macos_host_report().get("default_avpbooter")
            if isinstance(discovered, str) and discovered:
                firmware_value = discovered
        if not firmware_value:
            raise ValueError(
                "AVPBooter firmware path is required; native Apple-Silicon macOS "
                "can omit it only when the system Virtualization.framework path is present"
            )
        paths = {
            "firmware": _regular(firmware_value, "AVPBooter firmware", limit=MAX_FIRMWARE_BYTES),
            "aux": _regular(self.aux, "AUX base image"),
            "root": _regular(self.root, "root base image"),
        }
        # Direct macOS boot starts AVPBooter against the provisioned AUX/root
        # pair and does not enter the DFU uploader.  iBSS/iBEC are therefore
        # required only for the recovery selection (or for live recovery
        # personalization, which supplies the original images separately).
        needs_recovery_inputs = self.boot_selection == RECOVERY_ENTRY_ID
        if not self.live_personalize and needs_recovery_inputs:
            paths["ibss"] = _regular(self.ibss, "personalized iBSS", limit=MAX_DFU_BYTES)
            if self.ibec:
                paths["ibec"] = _regular(self.ibec, "personalized iBEC", limit=MAX_RECOVERY_BYTES)
        elif not self.live_personalize and self.ibss:
            # An optional legacy path is accepted for diagnostics, but the
            # direct path never uploads it.  Keep it in the input receipt only
            # when the caller explicitly supplies it.
            paths["legacy_ibss"] = _regular(self.ibss, "legacy iBSS", limit=MAX_DFU_BYTES)
        if self.ibec and self.live_personalize:
            paths["legacy_ibec"] = _regular(self.ibec, "legacy iBEC", limit=MAX_RECOVERY_BYTES)
        if self.live_personalize:
            if not self.build_manifest or not self.tss_helper:
                raise ValueError("Live personalization requires BuildManifest and TSS request helper")
            if not self.original_ibss:
                raise ValueError("Live personalization requires the unchanged original iBSS IM4P")
            if not self.original_ibec:
                raise ValueError("Live personalization requires the unchanged original iBEC IM4P")
            paths["build_manifest"] = _regular(self.build_manifest, "BuildManifest", limit=32 * 1024 * 1024)
            paths["tss_helper"] = _regular(self.tss_helper, "TSS request helper", limit=16 * 1024 * 1024)
            paths["original_ibss"] = _regular(self.original_ibss, "original iBSS", limit=MAX_DFU_BYTES)
            paths["original_ibec"] = _regular(self.original_ibec, "original iBEC", limit=MAX_RECOVERY_BYTES)
        if self.restore_chain:
            if not self.live_personalize:
                raise ValueError("Restore chain requires --live-personalize so the accepted iBEC ticket is available")
            if not self.restore_role_dir:
                raise ValueError("Restore chain requires a restore role directory")
            role_dir = Path(self.restore_role_dir).expanduser().resolve(strict=True)
            if not role_dir.is_dir():
                raise ValueError(f"Restore role path must be a directory: {role_dir}")
            for role in ("RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache"):
                paths["restore_" + role] = _regular(
                    role_dir / (role + ".im4p"), "restore " + role, limit=MAX_RECOVERY_BYTES
                )
            optional_logo = role_dir / "RestoreLogo.im4p"
            if optional_logo.exists():
                paths["restore_RestoreLogo"] = _regular(optional_logo, "restore RestoreLogo", limit=MAX_RECOVERY_BYTES)
        if qemu.is_wsl and os.name == "nt":
            raise ValueError("Run the VMApple worker inside WSL; the GUI bridge performs this re-exec")
        return qemu, qemu_img, paths

    def personality_report(self) -> dict[str, object]:
        """Return the validated iBoot/macOS policy metadata for reports."""
        personality = validate_iboot_scope(
            self.machine_type,
            self.guest_os,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
            recovery_enabled=True,
            target_major=self.target_major,
        )
        personality["boot_picker"] = validate_boot_picker_config(
            enabled=self.boot_picker_enabled,
            delay_seconds=self.boot_delay_seconds,
            alt_key=DEFAULT_ALT_KEY,
            show_picker_on_alt=True,
            target_major=self.target_major,
            recovery_enabled=True,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
        )
        personality["boot_picker"]["selection"] = self.boot_selection
        trigger = self.boot_picker_trigger.strip() if isinstance(self.boot_picker_trigger, str) else ""
        personality["boot_picker"]["selection_source"] = trigger
        personality["boot_picker"]["hotkey_event_observed"] = trigger.startswith("alt-")
        personality["boot_picker"]["delay_enforced"] = self.boot_picker_enabled
        return personality


def run(config: VMappleConfig) -> dict[str, object]:
    """Start VMApple and drive the selected direct-macOS or recovery path.

    Direct mode starts AVPBooter against the caller's provisioned AUX/root
    pair and observes XNU/userspace UART markers.  Recovery live mode supplies
    an unchanged BuildManifest/iBSS/iBEC and a request encoder; Apple TSS
    tickets are generated into a fresh output directory and the original
    payload bytes are wrapped without edits.  No marker or transport
    acknowledgement is promoted to an installation claim.
    """
    config, vm_bundle = config.resolve_vm_configuration()
    personality = config.personality_report()
    qemu, qemu_img, paths = config.validate()
    backend = probe_backend(qemu, direct_macos=config.boot_selection == MACOS_ENTRY_ID)
    # Inspect the caller-supplied bases before QEMU starts.  This is a
    # read-only diagnostic: the runner still permits a zero fixture for a
    # recovery-protocol experiment, but records that it cannot be an install
    # target so a later iBoot panic is not misread as an installer failure.
    storage_diagnostics = inspect_storage(
        aux=paths["aux"], root=paths["root"], aux_offset=config.aux_offset
    )
    output = _new_directory(config.output)
    storage: StorageSession | None = None
    process: subprocess.Popen[bytes] | None = None
    report: dict[str, object] | None = None
    started = time.monotonic()
    socket_path = f"/tmp/26x86-vmapple-{output.name}.sock"
    try:
        try:
            Path(socket_path).unlink()
        except FileNotFoundError:
            pass
        storage = create_storage(aux=paths["aux"], root=paths["root"], directory=output,
                                 qemu_img=qemu_img, aux_offset=config.aux_offset)
        effective_display = _effective_display_backend(
            config.display,
            direct_macos=config.boot_selection == MACOS_ENTRY_ID,
            available=backend.get("display_backends") if isinstance(backend.get("display_backends"), list) else None,
        )
        command = _command_for(
            config,
            qemu,
            storage,
            socket_path,
            output,
            bdif_block_writes=bool(backend.get("bdif_block_writes")),
            display_backend=effective_display,
        )
        inputs = {name: {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)}
                  for name, path in paths.items()}
        if isinstance(vm_bundle, dict):
            bundle_path = vm_bundle.get("path")
            bundle_digest = vm_bundle.get("json_sha256")
            if isinstance(bundle_path, str) and isinstance(bundle_digest, str):
                bundle_file = Path(bundle_path)
                inputs["macosvm_json"] = {
                    "path": bundle_path,
                    "bytes": bundle_file.stat().st_size,
                    "sha256": bundle_digest,
                }
        report = {
            "schema": "26x86.vmapple-gui/1", "target_major": config.target_major,
            "target_name": "Tahoe" if config.target_major == 26 else "Golden Gate",
            "machine_type": personality["machine_type"],
            "personality": personality["personality"],
            "guest_os": personality["guest_os"],
            "guest_os_supported": personality["guest_os_supported"],
            "guest_os_policy": personality["guest_os_policy"],
            "supported_guest_os": personality["supported_guest_os"],
            "unsupported_guest_os": personality["unsupported_guest_os"],
            "policy_matrix": personality["policy_matrix"],
            "recovery_scope": personality["recovery"],
            "boot_picker": personality["boot_picker"],
            "boot_mode": "direct-macos" if config.boot_selection == MACOS_ENTRY_ID else "recovery",
            "direct_boot_requested": config.boot_selection == MACOS_ENTRY_ID,
            "recovery_inputs_required": config.boot_selection == RECOVERY_ENTRY_ID,
            "validation_level": (
                "DIRECT-MACOS-BOOT" if config.boot_selection == MACOS_ENTRY_ID else "RECOVERY-PROTOCOL"
            ),
            "display_backend_requested": config.display,
            "display_backend": effective_display,
            "graphics_device_enabled": bool(backend.get("native_hvf_selected")),
            "virtual_soc_name": VIRTUAL_SOC_NAME,
            "virtual_model": VIRTUAL_MODEL,
            "virtual_identity_mode": "metadata-only",
            "hardware_attestation_verified": False,
            "soc_profile": apple_silicon_profile(),
            "research_only": True, "developer_host_bypass": True,
            "distribution_status": "NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT",
            "restore_chain_requested": config.restore_chain,
            "restore_chain_completed": False,
            "host": {"system": platform.system(), "architecture": platform.machine(),
                     "physical_mac_verified": False},
            "direct_macos_host": direct_macos_host_report(),
            "vm_bundle": vm_bundle,
            "backend": backend, "command": command, "inputs": inputs,
            "output": str(output),
            "cow_storage": True, "storage_session": str(storage.directory / "storage"),
            "storage_diagnostics": storage_diagnostics,
            "forced_transition": False, "signature_acceptance_verified": False,
            "personalization_mode": "live-tss" if config.live_personalize else "caller-supplied",
            "installer_modified": False, "ibec_executed": False,
            "xnu_executed": False, "macos_boot_verified": False,
            "installer_ui_visible": False, "installation_verified": False,
            "physical_mac_verified": False, "termination": None, "returncode": None,
            "duration_seconds": None, "input_integrity": False, "error": None,
        }
        _write_report(output, report)
        stdout = (output / "qemu.stdout.log").open("xb")
        stderr = (output / "qemu.stderr.log").open("xb")
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
        finally:
            stdout.close()
            stderr.close()
        report["pid"] = process.pid
        _write_report(output, report)
        if config.boot_selection == RECOVERY_ENTRY_ID:
            _wait_for_socket(socket_path, process, 30)
        else:
            # The direct macOS entry does not consume the recovery USB
            # transport.  Do not make its startup contingent on a recovery
            # socket; only ensure that QEMU did not exit immediately.
            time.sleep(0.2)
            if process.poll() is not None:
                raise VMappleError(
                    f"QEMU exited before direct macOS observation began: {process.returncode}"
                )
        # The gate starts when QEMU has exposed its recovery socket, which is
        # the first point at which the guest is powered and input can be
        # observed by this runner.  The GUI picker records the real Alt event
        # separately; this bounded sleep enforces the same two-second policy
        # before any DFU transfer is attempted.
        if config.boot_picker_enabled:
            report["boot_picker"]["gate_started_monotonic"] = round(time.monotonic() - started, 3)  # type: ignore[index]
            time.sleep(config.boot_delay_seconds)
            report["boot_picker"]["gate_released_monotonic"] = round(time.monotonic() - started, 3)  # type: ignore[index]
        report["boot_picker"]["gate_released"] = True  # type: ignore[index]
        _write_report(output, report)
        if config.boot_selection == MACOS_ENTRY_ID:
            # Direct boot must not enter the DFU/IPSW path.  AVPBooter owns the
            # normal macOS entry and reads the caller's provisioned AUX/root
            # pair; this runner only observes the UART boundary and keeps the
            # process alive after a successful userspace marker so a visible
            # GUI can remain available.
            observation_timeout = min(
                config.transition_timeout,
                config.duration if config.duration is not None else config.transition_timeout,
            )
            direct = _observe_direct_macos_boot(
                output / "serial.log", observation_timeout, process
            )
            report.update({
                "direct_boot": {
                    "requested": True,
                    "selection": MACOS_ENTRY_ID,
                    "dfu_entered": False,
                    "recovery_transport_used": False,
                    "observation": direct,
                },
                "xnu_executed": bool(direct["xnu_executed"]),
                "macos_boot_verified": bool(direct["macos_boot_verified"]),
                "installer_ui_visible": bool(direct["installer_ui_visible"]),
                "installation_verified": bool(direct["installation_verified"]),
            })
            storage_blockers = storage_diagnostics.get("blockers", [])
            if not isinstance(storage_blockers, list):
                storage_blockers = []
            blocker = direct.get("direct_boot_blocker")
            if not isinstance(blocker, str):
                blocker = ""
            if storage_diagnostics.get("provisioning_status") in (
                "unprovisioned-zero", "partially-unprovisioned"
            ):
                storage_note = (
                    " Storage preflight found a zero-filled AUX/root fixture; a "
                    "hardware-model-matched provisioned storage pair is required."
                )
                blocker += storage_note
            if not blocker:
                blocker = None
            stage_reached = (
                "macOS userspace" if direct["macos_boot_verified"] else
                "XNU kernel" if direct["xnu_executed"] else
                "AVPBooter direct entry"
            )
            report["golden_gate_installation"] = {
                "stage_reached": stage_reached,
                "boot_mode": "direct-macos",
                "signature_acceptance_verified": False,
                "ibec_executed": False,
                "stage2_execution_observed": False,
                "xnu_executed": bool(direct["xnu_executed"]),
                "macos_boot_verified": bool(direct["macos_boot_verified"]),
                "installer_ui_visible": bool(direct["installer_ui_visible"]),
                "installation_verified": False,
                "blocker": blocker,
                "storage_provisioning_status": storage_diagnostics.get("provisioning_status"),
                "storage_blockers": storage_blockers,
                "observed_markers": direct["observed_markers"],
            }
            _write_report(output, report)

            # A missing direct-boot marker is a bounded blocker, not a reason
            # to leave an invisible research process running indefinitely.
            if not direct["macos_boot_verified"] and process.poll() is None:
                report["termination"] = "direct-boot-evidence-timeout"
                process.terminate()
            deadline = time.monotonic() + config.duration if config.duration is not None else None
            while process.poll() is None:
                if deadline is not None and time.monotonic() >= deadline:
                    report["termination"] = "time_budget"
                    process.terminate()
                    break
                if (output / "stop").exists():
                    report["termination"] = "stop_file"
                    process.terminate()
                    break
                time.sleep(0.1)
            if process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            report["returncode"] = process.returncode
            if report.get("termination") is None:
                report["termination"] = "guest_exit"
            try:
                log_start, log_data = _read_log_tail(output / "serial.log")
            except OSError:
                log_start, log_data = 0, b""
            panic_position = log_data.rfind(b"iBoot Panic:")
            report["guest_panic"] = {
                "observed": panic_position >= 0,
                "marker": "iBoot Panic:",
                **({"byte_offset": log_start + panic_position} if panic_position >= 0 else {}),
            }
            report["duration_seconds"] = round(time.monotonic() - started, 3)
            report["input_integrity"] = _inputs_intact(report.get("inputs"))
            if not report["input_integrity"]:
                report["error"] = "One or more caller-supplied inputs changed during the run"
            elif not direct["macos_boot_verified"]:
                report["error"] = (
                    "Direct macOS boot evidence was not verified: "
                    + (blocker or "XNU and macOS userspace UART markers were incomplete")
                )
            _write_report(output, report)
            return report
        if config.live_personalize:
            from .vmapple_personalization import personalize_firmware

            personalization = output / "personalization"
            personalization.mkdir(mode=0o700)
            ibss_personalization = personalize_firmware(
                socket_path=socket_path,
                build_manifest=paths["build_manifest"],
                firmware=paths["original_ibss"],
                component="iBSS",
                helper=paths["tss_helper"],
                output=personalization / "ibss",
                developer_host_bypass=True,
                deadline=time.monotonic() + config.transition_timeout,
            )
            report["personalization"] = {"ibss": ibss_personalization}
            ibss_path = Path(ibss_personalization["output"])
        else:
            ibss_path = paths["ibss"]

        with RecoveryTransport(socket_path, timeout=10) as transport:
            initial = transport.probe()
            report["initial_device"] = initial
            dfu = transport.send_dfu_file(ibss_path, reset=True,
                                          expected_sha256=(_sha256(ibss_path) if config.live_personalize else None))
        report["dfu_upload"] = dfu
        transition = _probe_transition(socket_path, config.transition_timeout)
        report["transition"] = transition
        if transition.get("state") == "ibec-ready" and config.live_personalize:
            from .vmapple_personalization import personalize_firmware

            ibec_personalization = personalize_firmware(
                socket_path=socket_path,
                build_manifest=paths["build_manifest"],
                firmware=paths["original_ibec"],
                component="iBEC",
                helper=paths["tss_helper"],
                output=output / "personalization" / "ibec",
                developer_host_bypass=True,
                include_restore_policy=True,
                deadline=time.monotonic() + config.transition_timeout,
            )
            report.setdefault("personalization", {})["ibec"] = ibec_personalization
            policy = ibec_personalization.get("restore_policy", {})
            if (ibec_personalization.get("ticket_received") is not True
                    or ibec_personalization.get("payload_preserved") is not True
                    or policy.get("ticket_received") is not True):
                raise VMappleError("Live iBEC or bound LocalPolicy personalization did not complete")
            recovery_deadline = time.monotonic() + config.transition_timeout
            with RecoveryTransport(socket_path, timeout=10) as transport:
                report["ibec_configuration"] = transport.configure_recovery(deadline=recovery_deadline)
                policy_path = Path(ibec_personalization["output"]).parent / "restore-policy" / "RestoreLocalPolicy.personalized.img4"
                report["policy_upload"] = transport.send_recovery_file(
                    policy_path,
                    total_timeout=max(1.0, recovery_deadline - time.monotonic()),
                    expected_sha256=policy.get("sha256"),
                )
                transport.send_command("lpolrestore", deadline=recovery_deadline)
                report["lpolrestore_acknowledged"] = True
                report["ibec_upload"] = transport.send_recovery_file(
                    Path(ibec_personalization["output"]),
                    total_timeout=max(1.0, recovery_deadline - time.monotonic()),
                    expected_sha256=ibec_personalization.get("personalized_sha256"),
                )
                transport.send_command("go", request=1, deadline=recovery_deadline)
                report["go_acknowledged"] = True
            report["ibec_upload_attempted"] = True
            stage2 = _wait_serial_marker(output / "serial.log", STAGE2_PROMPT,
                                         min(config.transition_timeout, 300.0), process)
            report["stage2"] = stage2
            report["ibec_executed"] = bool(stage2.get("observed"))
            report["stage2_execution_observed"] = bool(stage2.get("observed"))
            if not stage2.get("observed"):
                report["transition_blocker"] = "iBEC go completed but Stage2 UART marker was not observed"
                if config.restore_chain:
                    report["restore_chain"] = {
                        "schema": "26x86.vmapple-restore/1",
                        "sequence_sent": False,
                        "bootx_acknowledged": False,
                        "input_integrity": True,
                        "error": "Stage2 UART marker was not observed",
                    }
            elif config.restore_chain:
                # Stage2 is the first point at which the standard macOS
                # restore-role protocol is available.  The role files are
                # normalized against BuildManifest and wrapped with the same
                # accepted iBEC IM4M; no new ticket or installer mutation is
                # introduced here.
                from .vmapple_restore import RestoreChainError, run_restore_sequence

                ticket_path = (
                    Path(report["personalization"]["ibec"]["output"]).parent
                    / "apple-ticket.private.im4m"
                )
                role_sources = {
                    role: paths["restore_" + role]
                    for role in ("RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache")
                }
                optional_logo = paths.get("restore_RestoreLogo")
                if optional_logo is not None:
                    role_sources["RestoreLogo"] = optional_logo
                try:
                    restore_report = run_restore_sequence(
                        socket_path=socket_path,
                        build_manifest=paths["build_manifest"],
                        role_sources=role_sources,
                        ticket=ticket_path,
                        output=output / "restore",
                        total_timeout=config.restore_timeout,
                    )
                except RestoreChainError as exc:
                    # Keep the structured partial report even when a guest
                    # stalls or panics; this is a bounded evidence boundary,
                    # not a reason to claim a boot.
                    restore_report = getattr(exc, "report", None)
                    if not isinstance(restore_report, dict):
                        restore_report = {"error": str(exc), "sequence_sent": False}
                report["restore_chain"] = restore_report
                report["restore_chain_completed"] = bool(
                    isinstance(restore_report, dict)
                    and restore_report.get("sequence_sent") is True
                    and restore_report.get("input_integrity") is True
                )
                report["restore_chain_stage"] = (
                    "bootx-sent" if report["restore_chain_completed"] else "restore-chain-failed"
                )
        elif transition.get("state") == "ibec-ready" and "ibec" in paths:
            report["ibec_upload_attempted"] = True
            with RecoveryTransport(socket_path, timeout=10) as transport:
                report["ibec_upload"] = transport.send_recovery_file(paths["ibec"])
            # Upload acknowledgement is not proof that iBEC was accepted or executed.
            report["ibec_executed"] = False
        elif transition.get("state") != "ibec-ready":
            report["ibec_upload_attempted"] = False
            report["transition_blocker"] = "iBSS did not advertise bulk OUT endpoint 4"
        else:
            report["ibec_upload_attempted"] = False
            report["transition_blocker"] = "No iBEC input was supplied"
        _write_report(output, report)

        deadline = time.monotonic() + config.duration if config.duration is not None else None
        while process.poll() is None:
            if deadline is not None and time.monotonic() >= deadline:
                report["termination"] = "time_budget"
                process.terminate()
                break
            if (output / "stop").exists():
                report["termination"] = "stop_file"
                process.terminate()
                break
            time.sleep(0.1)
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        report["returncode"] = process.returncode
        if report.get("termination") is None:
            report["termination"] = "guest_exit"
        # A restore transport can acknowledge every role and the bootx command
        # while iBoot still panics before XNU.  Capture that real UART boundary
        # after the process has stopped so the report cannot imply that a
        # successful transport sequence rendered the installer UI.
        try:
            log_start, log_data = _read_log_tail(output / "serial.log")
        except OSError:
            log_start, log_data = 0, b""
        panic_position = log_data.rfind(b"iBoot Panic:")
        if panic_position >= 0:
            report["guest_panic"] = {
                "observed": True,
                "marker": "iBoot Panic:",
                "byte_offset": log_start + panic_position,
            }
            if report.get("restore_chain_completed"):
                report["restore_chain_stage"] = "post-bootx-panic"
                restore_report = report.get("restore_chain")
                if isinstance(restore_report, dict):
                    restore_report["post_bootx_panic"] = True
            elif report.get("stage2_execution_observed"):
                report["transition_blocker"] = "Stage2 guest panic before XNU"
        else:
            report["guest_panic"] = {"observed": False, "marker": "iBoot Panic:"}
        storage_blockers = storage_diagnostics.get("blockers", [])
        if not isinstance(storage_blockers, list):
            storage_blockers = []
        if report.get("guest_panic", {}).get("observed"):
            stage_reached = "bootx acknowledged / iBoot Panic"
            blocker = (
                "After the complete restore-role transport and bootx acknowledgement, "
                "iBoot emitted a panic before XNU or any macOS UI."
            )
        elif report.get("stage2_execution_observed"):
            stage_reached = "iBootStage2 prompt"
            blocker = "The guest did not reach XNU or a macOS UI within the observed run."
        elif report.get("ibec_executed"):
            stage_reached = "iBEC executed"
            blocker = "Stage2/XNU and the macOS UI were not observed."
        elif report.get("transition", {}).get("state") == "ibec-ready":
            stage_reached = "iBEC endpoint advertised"
            blocker = "iBEC execution and the macOS UI were not observed."
        else:
            stage_reached = "iBSS/DFU boundary"
            blocker = "The iBEC endpoint or a later guest stage was not observed."
        if storage_diagnostics.get("provisioning_status") in (
            "unprovisioned-zero", "partially-unprovisioned"
        ):
            blocker += " Storage preflight found a zero-filled AUX/root fixture; a hardware-model-matched provisioned storage pair is required for installation."
        report["golden_gate_installation"] = {
            "stage_reached": stage_reached,
            "signature_acceptance_verified": False,
            "ibec_executed": bool(report.get("ibec_executed")),
            "stage2_execution_observed": bool(report.get("stage2_execution_observed")),
            "xnu_executed": False,
            "macos_boot_verified": False,
            "installer_ui_visible": False,
            "installation_verified": False,
            "blocker": blocker,
            "storage_provisioning_status": storage_diagnostics.get("provisioning_status"),
            "storage_blockers": storage_blockers,
        }
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["input_integrity"] = _inputs_intact(report.get("inputs"))
        if not report["input_integrity"]:
            report["error"] = "One or more caller-supplied inputs changed during the run"
        _write_report(output, report)
        return report
    except BaseException as error:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if report is None:
            report = {
                "schema": "26x86.vmapple-gui/1", "target_major": config.target_major,
                "target_name": "Tahoe" if config.target_major == 26 else "Golden Gate",
                "machine_type": personality["machine_type"],
                "personality": personality["personality"],
                "guest_os": personality["guest_os"],
                "guest_os_supported": personality["guest_os_supported"],
                "guest_os_policy": personality["guest_os_policy"],
                "policy_matrix": personality["policy_matrix"],
                "recovery_scope": personality["recovery"],
                "boot_picker": personality["boot_picker"],
                "validation_level": "RECOVERY-PROTOCOL",
                "display_backend_requested": config.display,
                "display_backend": _effective_display_backend(
                    config.display,
                    direct_macos=config.boot_selection == MACOS_ENTRY_ID,
                ),
                "virtual_soc_name": VIRTUAL_SOC_NAME,
                "virtual_model": VIRTUAL_MODEL,
                "virtual_identity_mode": "metadata-only",
                "hardware_attestation_verified": False,
                "vm_bundle": vm_bundle,
                "forced_transition": False, "signature_acceptance_verified": False,
                "macos_boot_verified": False, "physical_mac_verified": False,
            }
        report["error"] = f"{type(error).__name__}: {error}"
        report["termination"] = report.get("termination") or "error"
        report["returncode"] = process.returncode if process is not None else None
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["input_integrity"] = _inputs_intact(report.get("inputs"))
        _write_report(output, report)
        if config.boot_selection == MACOS_ENTRY_ID:
            # Direct mode is an observable boot attempt, so return its
            # structured evidence even when QEMU exits before the UART
            # observer starts.  The CLI still returns a non-zero status when
            # ``error`` is present, but callers receive the exact blocker and
            # output directory instead of a lossy exception-only message.
            report.setdefault("direct_boot", {
                "requested": True,
                "selection": MACOS_ENTRY_ID,
                "dfu_entered": False,
                "recovery_transport_used": False,
                "observation": {
                    "xnu_executed": False,
                    "macos_userspace_reached": False,
                    "macos_boot_verified": False,
                    "installer_ui_visible": False,
                    "installation_verified": False,
                    "observed_markers": {"xnu": [], "userspace": [], "installer": []},
                    "direct_boot_blocker": f"Direct macOS QEMU start failed: {type(error).__name__}: {error}",
                },
            })
            report.setdefault("golden_gate_installation", {
                "stage_reached": "direct macOS launch",
                "boot_mode": "direct-macos",
                "signature_acceptance_verified": False,
                "ibec_executed": False,
                "stage2_execution_observed": False,
                "xnu_executed": False,
                "macos_boot_verified": False,
                "installer_ui_visible": False,
                "installation_verified": False,
                "blocker": f"Direct macOS QEMU start failed: {type(error).__name__}: {error}",
                "storage_provisioning_status": storage_diagnostics.get("provisioning_status"),
                "storage_blockers": storage_diagnostics.get("blockers", []),
            })
            _write_report(output, report)
            return report
        raise
    finally:
        try:
            Path(socket_path).unlink()
        except FileNotFoundError:
            pass


def configured_from_environment() -> dict[str, object]:
    """Return GUI-safe availability information without launching a guest."""
    host = direct_macos_host_report()
    default_firmware = host.get("default_avpbooter")
    firmware_env = os.environ.get("X86_VMAPLE_AVPBOOTER", "")
    if not firmware_env and isinstance(default_firmware, str):
        firmware_env = default_firmware
    values = {
        "qemu": os.environ.get("X86_VMAPLE_QEMU", ""),
        "firmware": firmware_env,
        "vm_json": os.environ.get("X86_VMAPLE_JSON", ""),
        "ibss": os.environ.get("X86_VMAPLE_IBSS", ""),
        "ibec": os.environ.get("X86_VMAPLE_IBEC", ""),
        "aux": os.environ.get("X86_VMAPLE_AUX", ""),
        "root": os.environ.get("X86_VMAPLE_ROOT", ""),
        "qemu_img": os.environ.get("X86_VMAPLE_QEMU_IMG", ""),
        "output": os.environ.get("X86_VMAPLE_OUTPUT", ""),
        "build_manifest": os.environ.get("X86_VMAPLE_BUILD_MANIFEST", ""),
        "tss_helper": os.environ.get("X86_VMAPLE_TSS_HELPER", ""),
        "original_ibss": os.environ.get("X86_VMAPLE_ORIGINAL_IBSS", ""),
        "original_ibec": os.environ.get("X86_VMAPLE_ORIGINAL_IBEC", ""),
        "restore_role_dir": os.environ.get("X86_VMAPLE_RESTORE_ROLE_DIR", ""),
    }
    base_required = ("qemu", "firmware", "qemu_img")
    present = {name: bool(value) for name, value in values.items()}
    storage_configured = present["vm_json"] or (present["aux"] and present["root"])
    legacy_configured = all(present[name] for name in (*base_required, "ibss")) and storage_configured
    direct_configured = all(present[name] for name in base_required) and storage_configured
    live_required = (*base_required, "build_manifest", "tss_helper", "original_ibss", "original_ibec")
    live_configured = all(present[name] for name in live_required) and storage_configured
    boot_picker = validate_boot_picker_config(target_major=27)
    boot_picker["selection"] = RECOVERY_ENTRY_ID
    boot_picker["selection_source"] = "runner-default-recovery"
    boot_picker["hotkey_event_observed"] = False
    boot_picker["delay_enforced"] = True
    return {
        "ok": True, "research_only_required": True, "display_backend": "auto",
        "display_backend_effective": _effective_display_backend(
            "auto", direct_macos=host.get("apple_silicon_macos") is True
        ),
        "machine_type": IBOOT_MACHINE_TYPE, "personality": "iBoot",
        "guest_os": MACOS_GUEST_OS, "guest_os_supported": True,
        "guest_os_policy": "macOS-only", "supported_guest_os": [MACOS_GUEST_OS],
        "unsupported_guest_os": ["iOS", "iPadOS", "tvOS", "watchOS", "visionOS"],
        "policy_matrix": default_scope(recovery_enabled=True)["policy_matrix"],
        "recovery_scope": default_scope(recovery_enabled=True)["recovery"],
        "boot_picker": boot_picker,
        "direct_macos_host": host,
        "soc_profile": apple_silicon_profile(),
        # Either an explicitly personalized legacy input or the preferred
        # live-TSS set is usable.  The GUI defaults to live mode and exposes
        # this distinction instead of claiming that a partial path is ready.
        "configured": live_configured or legacy_configured or direct_configured, "fields": present,
        "legacy_configured": legacy_configured,
        "direct_macos_configured": direct_configured,
        "live_personalization_configured": live_configured,
        "personalization_default": "live-tss",
        "values": values, "macos_boot_verified": False,
        "note": "Paths or macosvm.json are caller-supplied. The GUI never bundles Apple firmware or writes an existing ESP.",
    }
