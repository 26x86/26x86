"""Validate the OpenCore Sandbox control plane without changing host firmware."""
from __future__ import annotations

import plistlib
import uuid
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


def default_config(target_major: int = 26) -> dict[str, Any]:
    if type(target_major) is not int or target_major not in (26, 27):
        raise ValueError("TargetMajor must be 26 or 27")
    return {
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
            "interrupt_controller": "AIC", "boot_protocol": "iBoot", "boot_verified": False}


def read(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if source.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("config.plist exceeds the 4 MiB control-plane limit")
    raw = source.read_bytes()
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("config.plist exceeds the 4 MiB control-plane limit")
    return validate(plistlib.loads(raw))
