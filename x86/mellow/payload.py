"""Verified Mellow distribution inputs; never mounts, installs, or loads code."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import stat
import struct
from types import MappingProxyType
from typing import Mapping


SOURCE_COMMIT = "72f3df08ff05c20bdbbada7723009b88f6ccd25e"
KEXT_SHA256 = "6932453a484ac62fb46f19b78f4a6424cef8ba907a3abe655b051bf03daed3c7"
INFO_SHA256 = "f90a8c842cf5d381c2b3d76fee93d11ff99af703f22852333602b23f1a516ec5"
DESTINATIONS = MappingProxyType({
    "kext": "/Library/Extensions/Mellow.kext",
    "user_driver": "/Library/Application Support/Mellow/Drivers/MellowDriver.bundle",
    "runtime": "/Library/Frameworks/Mellow.framework",
})


class PayloadError(ValueError):
    """Invalid, unavailable, or disallowed payload; no mutation was performed."""


@dataclass(frozen=True)
class PayloadFile:
    relative_path: str
    path: Path
    sha256: str
    size: int


@dataclass(frozen=True)
class Component:
    category: str
    source: Path
    destination: str
    bundle_id: str
    version: str
    executable: Path
    sha256: str


@dataclass(frozen=True)
class ValidatedPayload:
    root: Path
    source_commit: str
    components: tuple[Component, ...]
    files: tuple[PayloadFile, ...]
    required_boot_args: tuple[str, ...]
    capabilities: Mapping[str, bool]

    def validate(self, *, mode: str = "x86") -> "ValidatedPayload":
        return load_payload(self.root, mode=mode)

    def patches(self, patch_type=None, *, mode: str = "x86") -> dict:
        """Build existing-engine data-volume entries after fresh byte validation.

        The default key equals the existing PatchType StrEnum value without
        importing macOS hardware detection. A caller may pass PatchType too.
        The engine appends destination directory/name to this source prefix.
        """
        current = self.validate(mode=mode)
        method = "Overwrite Data Volume" if patch_type is None else patch_type.OVERWRITE_DATA_VOLUME
        entries = {}
        for component in current.components:
            destination = PurePosixPath(component.destination)
            entries.setdefault(str(destination.parent), {})[destination.name] = (
                current.root / "root").as_posix()
        return {"Mellow": {method: entries}}


def _relative(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise PayloadError("Invalid relative payload path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise PayloadError("Payload traversal/absolute path rejected")
    return value


def _no_links(path: Path) -> None:
    info = path.lstat()
    # Windows junctions/reparse points must not bypass the symlink check.
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise PayloadError("Payload symlink/reparse point rejected")


def _json_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PayloadError("Duplicate manifest key")
        result[key] = value
    return result


def _macho(path: Path, allowed_types: tuple[int, ...]) -> None:
    data = path.read_bytes()
    if len(data) < 32:
        raise PayloadError("Missing/truncated Mach-O executable")
    magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from("<8I", data)
    if magic != 0xFEEDFACF or cpu != 0x01000007 or subtype != 3 or kind not in allowed_types:
        raise PayloadError("Expected genuine x86_64 Mach-O of the component file type")
    if count == 0 or count > 4096 or size > len(data) - 32:
        raise PayloadError("Invalid Mach-O load command bounds")
    cursor = 32
    for _ in range(count):
        if cursor + 8 > 32 + size:
            raise PayloadError("Truncated Mach-O load command")
        command, length = struct.unpack_from("<II", data, cursor)
        if length < 8 or length % 8 or cursor + length > 32 + size:
            raise PayloadError("Invalid Mach-O load command length")
        cursor += length
    if cursor != 32 + size:
        raise PayloadError("Mach-O command size mismatch")


def load_payload(directory, *, mode: str = "x86") -> ValidatedPayload:
    """Read an extracted, exact-inventory package. Archives are not accepted.

    The current pinned native payload is intentionally unavailable in Sandbox.
    No Apple graphics bundle or accelerated capability is synthesized.
    """
    if mode != "x86":
        if mode == "apple-silicon-sandbox":
            raise PayloadError("Native Mellow payloads are forbidden in Apple Silicon Sandbox Mode")
        raise PayloadError("Unknown execution mode")
    try:
        return _load(directory)
    except PayloadError:
        raise
    except (OSError, ValueError, TypeError, KeyError, plistlib.InvalidFileException) as error:
        raise PayloadError(f"Invalid Mellow payload: {error}") from error


def _load(directory) -> ValidatedPayload:
    requested = Path(directory).absolute()
    for ancestor in (requested, *requested.parents):
        _no_links(ancestor)
    root = requested.resolve(strict=True)
    if not root.is_dir():
        raise PayloadError("Expected extracted payload directory")
    disk_files = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            _no_links(path)
            relative = path.relative_to(root).as_posix()
            _relative(relative)
            if path.is_file():
                disk_files[relative] = path
            elif not path.is_dir():
                raise PayloadError("Non-regular payload entry")
    manifest_path = disk_files.pop("manifest.json", None)
    if manifest_path is None or manifest_path.stat().st_size > 1024 * 1024:
        raise PayloadError("Missing/oversized manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_json_no_duplicates)
    if not isinstance(manifest, dict):
        raise PayloadError("Manifest must be an object")
    if manifest.get("schema_version") != 1 or manifest.get("source_commit") != SOURCE_COMMIT:
        raise PayloadError("Unsupported manifest schema/source commit")
    if manifest.get("required_boot_args") != ["-mellowdiag"]:
        raise PayloadError("This kext package requires diagnostic-only -mellowdiag")
    expected_caps = {"native_metal": False, "gpu_submission": False, "windowserver_acceleration": False}
    if manifest.get("capabilities") != expected_caps or any(type(v) is not bool for v in manifest["capabilities"].values()):
        raise PayloadError("Unsupported acceleration capability claim")
    inventory = manifest.get("files")
    if not isinstance(inventory, dict) or not inventory:
        raise PayloadError("Missing file inventory")
    if set(inventory) != set(disk_files):
        raise PayloadError("Payload inventory mismatch (missing or extra file)")
    verified = []
    for relative, record in inventory.items():
        _relative(relative)
        if not isinstance(record, dict) or set(record) != {"sha256", "size"}:
            raise PayloadError("Invalid file record")
        if not re.fullmatch(r"[0-9a-f]{64}", record.get("sha256", "")) or type(record.get("size")) is not int:
            raise PayloadError("Invalid file digest/size")
        data = disk_files[relative].read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != record["size"] or digest != record["sha256"]:
            raise PayloadError("Payload hash/size mismatch: " + relative)
        verified.append(PayloadFile(relative, disk_files[relative], digest, len(data)))
    declarations = manifest.get("components")
    if not isinstance(declarations, list) or not declarations:
        raise PayloadError("Missing component declarations")
    components, categories = [], set()
    for item in declarations:
        if not isinstance(item, dict):
            raise PayloadError("Component must be an object")
        category = item["category"]
        if not isinstance(category, str) or category not in DESTINATIONS or category in categories:
            raise PayloadError("Unknown/duplicate component category")
        categories.add(category)
        destination = DESTINATIONS[category]
        if item["destination"] != destination or item["source"] != "root" + destination:
            raise PayloadError("Component source/destination not allowlisted")
        source = root / _relative(item["source"])
        info_path = source / "Contents/Info.plist"
        info = plistlib.loads(info_path.read_bytes())
        executable_name = _relative(info["CFBundleExecutable"])
        if "/" in executable_name:
            raise PayloadError("Invalid bundle executable name")
        executable = source / "Contents/MacOS" / executable_name
        if info["CFBundleIdentifier"] != item["bundle_id"] or info["CFBundleVersion"] != item["version"]:
            raise PayloadError("Bundle metadata mismatch")
        _macho(executable, {"kext": (11,), "user_driver": (8,), "runtime": (6, 8)}[category])
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        if category == "kext":
            bundle_files = {name for name in disk_files if name.startswith(item["source"] + "/")}
            expected_bundle_files = {item["source"] + suffix for suffix in (
                "/Contents/Info.plist", "/Contents/MacOS/Mellow")}
            if bundle_files != expected_bundle_files:
                raise PayloadError("Unexpected file/plugin in pinned kext bundle")
            if (item["bundle_id"] != "com.NiSeullent.Mellow" or item["version"] != "0.4.3"
                    or info.get("CFBundlePackageType") != "KEXT" or digest != KEXT_SHA256
                    or hashlib.sha256(info_path.read_bytes()).hexdigest() != INFO_SHA256):
                raise PayloadError("Kext does not match pinned diagnostic build")
        else:
            # A file-type header alone cannot establish a working Darwin driver.
            raise PayloadError("No verified runtime/user-driver artifact is released by this source pin")
        components.append(Component(category, source, destination, item["bundle_id"], item["version"], executable, digest))
    allowed_roots = ["root" + component.destination + "/" for component in components]
    for relative in disk_files:
        if relative.startswith("root/") and not any(relative.startswith(prefix) for prefix in allowed_roots):
            raise PayloadError("Unclaimed installable file")
    return ValidatedPayload(root, SOURCE_COMMIT, tuple(components), tuple(verified),
                            tuple(manifest["required_boot_args"]), MappingProxyType(expected_caps))
