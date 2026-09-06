"""Validate the OpenCore Sandbox control plane without changing host firmware."""
from __future__ import annotations

import plistlib
import uuid
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .iboot_personality import (
    DEFAULT_RECOVERY_IMAGE,
    IBOOT_MACHINE_TYPE,
    MACOS_GUEST_OS,
    default_scope,
    policy_matrix,
    validate_iboot_scope,
)


def default_config(target_major: int = 26) -> dict[str, Any]:
    if type(target_major) is not int or target_major not in (26, 27):
        raise ValueError("TargetMajor must be 26 or 27")
    return {
        "Venfire": {
            "MachineType": IBOOT_MACHINE_TYPE,
            "GuestOS": MACOS_GUEST_OS,
            "Recovery": {
                "Enabled": False,
                "Protocol": "Auto",
                "LocalRecovery": {"ImageName": DEFAULT_RECOVERY_IMAGE},
            },
        },
        "AppleSiliconSandbox": {
            "Enabled": False, "TargetMajor": target_major,
            "InterruptController": "AIC", "BootProtocol": "iBoot",
            "EnginePath": "\\EFI\\26x86\\Sandbox.efi", "IBootPath": "",
            "Hardware": {"MemorySizeMiB": 4096, "CPUCount": 2, "DeviceProperties": {}},
        },
        "SandboxSMBIOS": {"SystemProductName": "", "SystemSerialNumber": "",
                          "SystemUUID": "", "BoardProduct": ""},
    }


def _efi_path(value: Any) -> bool:
    return (isinstance(value, str) and value.startswith("\\")
            and 1 < len(value) <= 191 and "/" not in value and ":" not in value
            and all(part not in ("", ".", "..") for part in value.split("\\")[1:])
            and all(32 <= ord(c) < 127 for c in value))


def validate(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return {"ok": False, "errors": ["config.plist must contain a dictionary"]}
    sandbox = config.get("AppleSiliconSandbox")
    identity = config.get("SandboxSMBIOS")
    if not isinstance(sandbox, dict) or not isinstance(identity, dict):
        return {"ok": False, "errors": ["AppleSiliconSandbox and SandboxSMBIOS dictionaries are required"]}
    # The OpenCore-compatible tree may contain other Venfire personalities,
    # but this Apple Silicon Sandbox config is wired to iBoot(AArch64).  Keep
    # the scope decision in one pure policy function so it runs before any
    # EFI/USB/guest input is opened by a later layer.
    enabled = sandbox.get("Enabled")
    policy = default_scope(
        target_major=sandbox.get("TargetMajor") if type(sandbox.get("TargetMajor")) is int else None,
        recovery_enabled=False,
    )
    venfire = config.get("Venfire")
    if venfire is not None and not isinstance(venfire, dict):
        errors.append("Venfire must be a dictionary")
    elif isinstance(venfire, dict):
        machine_type = venfire.get("MachineType", IBOOT_MACHINE_TYPE)
        guest_os = venfire.get(
            "GuestOS",
            sandbox.get("GuestOS", MACOS_GUEST_OS),
        )
        recovery = venfire.get("Recovery", {})
        if not isinstance(recovery, dict):
            errors.append("Venfire.Recovery must be a dictionary")
            recovery = {}
        local_recovery = recovery.get("LocalRecovery", {})
        if not isinstance(local_recovery, dict):
            errors.append("Venfire.Recovery.LocalRecovery must be a dictionary")
            local_recovery = {}
        recovery_enabled = recovery.get("Enabled", False)
        if type(recovery_enabled) is not bool:
            errors.append("VF_RECOVERY_CONFIG_INVALID: Venfire.Recovery.Enabled must be a boolean")
        if not isinstance(machine_type, str) or not machine_type.strip():
            errors.append("VF_MACHINE_PERSONALITY_MISMATCH: Venfire.MachineType must be a nonempty string")
            machine_type = IBOOT_MACHINE_TYPE
        if machine_type != IBOOT_MACHINE_TYPE:
            # config.d is also a carrier for future Venfire personalities.  A
            # different personality may remain disabled here, while the
            # Apple Silicon Sandbox itself can only activate iBoot.
            if enabled is True:
                errors.append(
                    "VF_CONFIG_SCOPE_VIOLATION: AppleSiliconSandbox requires iBoot(AArch64)"
                )
            policy = default_scope(
                target_major=sandbox.get("TargetMajor") if type(sandbox.get("TargetMajor")) is int else None,
                recovery_enabled=recovery_enabled is True,
            )
            policy["machine_type"] = machine_type
            policy["personality"] = str(machine_type).split("(", 1)[0] if isinstance(machine_type, str) else "unknown"
            policy["scope_evaluated"] = False
        else:
            try:
                policy = validate_iboot_scope(
                    machine_type,
                    guest_os,
                    recovery_protocol=recovery.get("Protocol", "Auto"),
                    recovery_image_name=local_recovery.get("ImageName", DEFAULT_RECOVERY_IMAGE),
                    recovery_enabled=recovery_enabled,
                    target_major=sandbox.get("TargetMajor"),
                )
            except ValueError as exc:
                code = getattr(exc, "code", "VF_CONFIG_SCOPE_VIOLATION")
                errors.append(f"{code}: {exc}")
    elif enabled is True:
        # No Venfire root is a legacy fragment.  Enabling this Sandbox still
        # implies the fixed iBoot/macOS policy and keeps the result auditable.
        policy = default_scope(target_major=sandbox.get("TargetMajor"), recovery_enabled=False)
    enabled = sandbox.get("Enabled")
    if type(enabled) is not bool:
        errors.append("AppleSiliconSandbox.Enabled must be a boolean")
    if type(sandbox.get("TargetMajor")) is not int or sandbox["TargetMajor"] not in (26, 27):
        errors.append("TargetMajor must be 26 or 27")
    for key, required in (("InterruptController", "AIC"), ("BootProtocol", "iBoot")):
        if sandbox.get(key) != required:
            errors.append(f"{key} must be {required}")
    if not _efi_path(sandbox.get("EnginePath")):
        errors.append("EnginePath must be an absolute EFI-volume path without traversal")
    if enabled or sandbox.get("IBootPath"):
        if not _efi_path(sandbox.get("IBootPath")):
            errors.append("IBootPath must identify the original iBoot asset on the EFI volume")
    hardware = sandbox.get("Hardware")
    if not isinstance(hardware, dict):
        errors.append("Hardware must be a dictionary")
    else:
        for key, low, high in (("MemorySizeMiB", 4096, 1048576), ("CPUCount", 1, 64)):
            value = hardware.get(key)
            if type(value) is not int or not low <= value <= high:
                errors.append(f"Hardware.{key} must be an integer between {low} and {high}")
        properties = hardware.get("DeviceProperties")
        if not isinstance(properties, dict):
            errors.append("Hardware.DeviceProperties must be a device-to-property dictionary")
        else:
            xml_bytes = len('<?xml version="1.0"?><plist version="1.0"><dict></dict></plist>')
            if len(properties) > 4096:
                errors.append("DeviceProperties exceeds the 4096-device limit")
            for device, entries in properties.items():
                if (not isinstance(device, str) or not 1 <= len(device) <= 255
                        or any(not 32 <= ord(c) < 127 for c in device) or not isinstance(entries, dict)):
                    errors.append("DeviceProperties contains an invalid device entry")
                    continue
                xml_bytes += 24 + len(escape(device, {'"': '&quot;', "'": '&apos;'}))
                if len(entries) > 4096:
                    errors.append("DeviceProperties exceeds the 4096-property limit")
                for key, value in entries.items():
                    if (not isinstance(key, str) or not 1 <= len(key) <= 255
                            or any(not 32 <= ord(c) < 127 for c in key) or type(value) not in (bytes, str, int, bool)
                            or (type(value) is int and not 0 <= value <= 0xFFFFFFFFFFFFFFFF)):
                        errors.append(f"Invalid DeviceProperties value: {device}/{key}")
                        continue
                    size = len(value) if isinstance(value, bytes) else len(value.encode("utf-8")) + 1 if isinstance(value, str) else 1 if type(value) is bool else 4 if value <= 0xFFFFFFFF else 8
                    if size > 1048576:
                        errors.append(f"DeviceProperties data exceeds 1 MiB: {device}/{key}")
                    xml_bytes += 24 + len(escape(key, {'"': '&quot;', "'": '&apos;'})) + 4 * ((size + 2) // 3)
            if xml_bytes >= 1048576:
                errors.append("Serialized DeviceProperties exceeds the 1 MiB EFI handoff limit")
    for key in ("SystemProductName", "SystemSerialNumber", "SystemUUID", "BoardProduct"):
        value = identity.get(key)
        if (not isinstance(value, str) or len(value) > (36 if key == "SystemUUID" else 255)
                or any(not 32 <= ord(c) < 127 for c in value) or (enabled and not value)):
            errors.append(f"SandboxSMBIOS.{key} must be a string and is required when enabled")
        elif key == "SystemUUID" and value:
            try:
                if str(uuid.UUID(value)) != value.lower():
                    raise ValueError("Noncanonical UUID")
            except ValueError:
                errors.append("SandboxSMBIOS.SystemUUID is invalid")
    return {"ok": not errors, "errors": errors, "enabled": enabled is True,
            "interrupt_controller": "AIC", "boot_protocol": "iBoot", "boot_verified": False,
            "machine_type": policy["machine_type"], "personality": policy["personality"],
            "guest_os": policy["guest_os"], "guest_os_supported": policy["guest_os_supported"],
            "guest_os_policy": policy["guest_os_policy"],
            "supported_guest_os": policy["supported_guest_os"],
            "unsupported_guest_os": policy["unsupported_guest_os"],
            "recovery": policy["recovery"], "policy_matrix": policy_matrix()}


def read(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if source.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("config.plist exceeds the 4 MiB control-plane limit")
    raw = source.read_bytes()
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("config.plist exceeds the 4 MiB control-plane limit")
    return validate(plistlib.loads(raw))
