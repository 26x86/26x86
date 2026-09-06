"""Read restore metadata in place. Never extract, decrypt, patch, or sign files."""

from __future__ import annotations

import hashlib
import lzma
import os
import plistlib
from pathlib import Path, PurePosixPath
import zipfile
import zlib
from xml.parsers.expat import ExpatError

from .artifacts import read_regular

MAX_MANIFEST = 32 * 1024 * 1024


def _mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a dictionary")
    return value


def _optional_text(mapping: dict, key: str, label: str) -> str | None:
    if key not in mapping:
        return None
    value = mapping[key]
    if not isinstance(value, str):
        raise ValueError(f"{label}.{key} must be text")
    return value


def _read_build_manifest(archive: zipfile.ZipFile) -> tuple[dict, set[str]]:
    entries = archive.infolist()
    matches = [entry for entry in entries if entry.filename == "BuildManifest.plist"]
    if len(matches) != 1:
        raise ValueError("Archive must contain exactly one root BuildManifest.plist")
    item = matches[0]
    if item.file_size > MAX_MANIFEST:
        raise ValueError("BuildManifest exceeds the 32 MiB inspection limit")
    with archive.open(item) as member:
        contents = member.read(MAX_MANIFEST + 1)
    if len(contents) > MAX_MANIFEST:
        raise ValueError("BuildManifest exceeds inspection limit")
    try:
        manifest = plistlib.loads(contents)
    except (ValueError, TypeError, OverflowError, RecursionError, ExpatError, plistlib.InvalidFileException) as exc:
        raise ValueError("BuildManifest is not a valid plist") from exc
    return _mapping(manifest, "BuildManifest"), {entry.filename for entry in entries}


def inspect_restore(path: str | Path, *, hash_archive: bool = False) -> dict:
    source = Path(path).absolute()
    # Pass the original path so normalization never hides a symlink/.. input.
    with read_regular(path) as stream:
        size = os.fstat(stream.fileno()).st_size
        try:
            with zipfile.ZipFile(stream) as archive:
                manifest, names = _read_build_manifest(archive)
        except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, NotImplementedError,
                EOFError, zlib.error, lzma.LZMAError) as exc:
            raise ValueError(f"Restore archive cannot be read ({type(exc).__name__})") from exc
        raw_identities = manifest.get("BuildIdentities", [])
        if not isinstance(raw_identities, list):
            raise ValueError("BuildIdentities must be an array")
        products = manifest.get("SupportedProductTypes", [])
        if not isinstance(products, list) or not all(isinstance(item, str) for item in products):
            raise ValueError("SupportedProductTypes must be an array of text identifiers")
        product_version = _optional_text(manifest, "ProductVersion", "BuildManifest")
        build_version = _optional_text(manifest, "ProductBuildVersion", "BuildManifest")
        identities = []
        for identity in raw_identities:
            identity = _mapping(identity, "Build identity")
            info = _mapping(identity.get("Info", {}), "Build identity Info")
            component_map = _mapping(identity.get("Manifest", {}), "Build identity Manifest")
            components = []
            for name, component in component_map.items():
                if not isinstance(name, str):
                    raise ValueError("Component name must be text")
                component = _mapping(component, "Component")
                component_info = _mapping(component.get("Info", {}), "Component Info")
                relative = _optional_text(component_info, "Path", "Component Info")
                if relative is None:
                    continue
                relative_path = PurePosixPath(relative)
                safe = (bool(relative_path.parts)
                        and not relative_path.is_absolute()
                        and ".." not in relative_path.parts
                        and "\\" not in relative and ":" not in relative
                        and "\x00" not in relative)
                components.append({"name": name, "path": relative,
                                   "safe_relative_path": safe,
                                   "present_in_archive": relative in names})
            identities.append({"device_class": _optional_text(info, "DeviceClass", "Build identity Info"),
                               "variant": _optional_text(info, "Variant", "Build identity Info"),
                               "restore_behavior": _optional_text(info, "RestoreBehavior", "Build identity Info"),
                               "components": components})
        digest = None
        if hash_archive:
            stream.seek(0)
            hasher = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(block)
            digest = hasher.hexdigest()
    return {"schema": 1, "path": str(source), "size": size,
            "sha256": digest, "product_version": product_version,
            "product_build_version": build_version,
            "supported_product_types": products,
            "identities": identities, "modified": False,
            "signature_verified": False, "boot_compatibility": "not established"}
