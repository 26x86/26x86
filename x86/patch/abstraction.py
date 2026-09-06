"""Read-only validation of build-specific 26x86 abstraction binary packages.

An abstraction package supplies native adapters for an explicitly named ABI. It
does not translate an ARM64 kernel into an x86_64 kernel. Validation here proves
file identity and the declared deployment target, not that an adapter works.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import struct
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "26x86.abstraction/1"
CPU_TYPES = {"x86_64": 0x01000007, "arm64": 0x0100000C}
FILE_TYPES = {"kext": 11, "dylib": 6}
MAX_MANIFEST = 1024 * 1024
MAX_BINARY = 256 * 1024 * 1024
# Adapters enter this registry only after their real integration and validation
# exist. An untrusted manifest cannot register an executable root patch adapter.
REGISTERED_ADAPTERS: dict[str, Any] = {}


def _object_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"Duplicate manifest field: {key}")
        result[key] = value
    return result


def _read_binary(path: Path, architecture: str, kind: str) -> tuple[str, int]:
    size = path.stat().st_size
    if size < 32 or size > MAX_BINARY:
        raise ValueError(f"Invalid binary size: {path.name}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        header = stream.read(32)
        digest.update(header)
        magic, cpu, _, filetype, ncmds, sizeofcmds, _, _ = struct.unpack("<8I", header)
        if magic != 0xFEEDFACF:
            raise ValueError("Abstraction native binaries must be thin little-endian Mach-O 64")
        if cpu != CPU_TYPES[architecture]:
            raise ValueError(f"Mach-O CPU does not match target {architecture}")
        if filetype != FILE_TYPES[kind]:
            raise ValueError(f"Mach-O file type does not match {kind}")
        if not 1 <= ncmds <= 4096 or sizeofcmds < ncmds * 8 or sizeofcmds > size - 32:
            raise ValueError("Invalid Mach-O load-command bounds")
        commands = stream.read(sizeofcmds)
        digest.update(commands)
        offset = 0
        for _ in range(ncmds):
            if offset + 8 > len(commands):
                raise ValueError("Truncated Mach-O load command")
            _, command_size = struct.unpack_from("<II", commands, offset)
            if command_size < 8 or command_size % 8 or offset + command_size > len(commands):
                raise ValueError("Invalid Mach-O load command size")
            offset += command_size
        if offset != sizeofcmds:
            raise ValueError("Mach-O load commands do not consume declared size")
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if path.stat().st_size != size:
        raise ValueError("Binary changed during validation")
    return digest.hexdigest(), size


def validate_manifest(manifest_path: str | Path, *, target_major: int,
                      os_build: str, architecture: str,
                      expected_abi: str | None = None) -> dict[str, Any]:
    """Validate a local package without importing or executing its contents."""
    result: dict[str, Any] = {"ok": False, "can_apply": False,
                             "hardware_verified": False, "errors": [], "files": []}
    try:
        if isinstance(target_major, bool) or target_major not in (26, 27):
            raise ValueError("Abstraction packages target macOS 26 or 27")
        if architecture not in CPU_TYPES or not isinstance(os_build, str) or not os_build:
            raise ValueError("An observed architecture and exact macOS build are required")
        source = Path(manifest_path).expanduser()
        if source.is_symlink() or not source.is_file():
            raise ValueError("Manifest must be a regular local file")
        if source.stat().st_size > MAX_MANIFEST:
            raise ValueError("Manifest exceeds size limit")
        raw = source.read_bytes()
        if len(raw) > MAX_MANIFEST:
            raise ValueError("Manifest exceeds size limit")
        manifest = json.loads(raw, object_pairs_hook=_object_pairs)
        if manifest.get("schema") != SCHEMA:
            raise ValueError("Unknown abstraction manifest schema")
        target = manifest["target"]
        if target.get("macos_major") != target_major or isinstance(target.get("macos_major"), bool):
            raise ValueError("macOS major does not match the installed target")
        if target.get("os_build") != os_build:
            raise ValueError("Exact macOS build mismatch; update requires a matching package")
        if target.get("architecture") != architecture:
            raise ValueError("Declared architecture does not match the running kernel")
        abi = target.get("runtime_abi")
        if not isinstance(abi, str) or not abi or len(abi) > 256:
            raise ValueError("A bounded runtime ABI identifier is required")
        if expected_abi is not None and abi != expected_abi:
            raise ValueError("Runtime ABI does not match the selected adapter")
        adapter = manifest.get("adapter")
        if not isinstance(adapter, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", adapter):
            raise ValueError("Invalid adapter identifier")
        files = manifest["files"]
        if not isinstance(files, list) or not 1 <= len(files) <= 64:
            raise ValueError("Package requires between 1 and 64 native binaries")
        root = source.resolve().parent
        seen = set()
        for item in files:
            relative = item["path"]
            if not isinstance(relative, str) or "\\" in relative or ":" in relative:
                raise ValueError("Binary paths must use relative POSIX components")
            rel = PurePosixPath(relative)
            if not relative or rel.is_absolute() or ".." in rel.parts or "." in relative.split("/"):
                raise ValueError("Binary path escapes the package")
            if relative.casefold() in seen:
                raise ValueError("Duplicate binary path")
            seen.add(relative.casefold())
            candidate = root.joinpath(*rel.parts)
            cursor = root
            for part in rel.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise ValueError("Package paths must not contain symlinks")
            if not candidate.resolve().is_relative_to(root) or not candidate.is_file():
                raise ValueError("Binary is outside the package or missing")
            if item.get("kind") not in FILE_TYPES:
                raise ValueError("Only native kext and dylib abstraction binaries are accepted")
            provenance = item["source"]
            if not re.fullmatch(r"https://[^\s]+", provenance.get("url", "")):
                raise ValueError("Source provenance requires an HTTPS URL")
            if not re.fullmatch(r"[0-9a-f]{40,64}", provenance.get("revision", "")):
                raise ValueError("Source provenance requires an immutable revision")
            if not isinstance(item.get("license"), str) or not item["license"].strip():
                raise ValueError("Each binary requires its own license identifier")
            expected_hash = item["sha256"]
            if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                raise ValueError("Invalid binary SHA-256")
            actual, size = _read_binary(candidate, architecture, item["kind"])
            if actual != expected_hash:
                raise ValueError(f"Binary SHA-256 mismatch: {relative}")
            result["files"].append({"path": relative, "sha256": actual, "size": size,
                                    "kind": item["kind"], "architecture": architecture})
        result.update(ok=True, schema=SCHEMA, manifest_sha256=hashlib.sha256(raw).hexdigest(),
                      manifest_path=str(source.resolve()), adapter=adapter, target=target,
                      runtime_abi_verified=expected_abi is not None,
                      adapter_registered=adapter in REGISTERED_ADAPTERS,
                      status="validated_files_only")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, struct.error) as exc:
        result["errors"].append(str(exc))
    return result


def root_patch_gate(manifest_path: str | Path | None, *, target_major: int,
                    os_build: str, architecture: str) -> dict[str, Any]:
    """Keep unsupported Darwin 26 adapters out of the legacy root patch engine."""
    if target_major not in (26, 27):
        return {"ok": False, "required": True, "can_apply": False,
                "errors": ["No abstraction deployment contract exists for this macOS version."]}
    if manifest_path is None:
        return {"ok": target_major != 27, "required": target_major == 27,
                "errors": (["macOS 27 requires an exact-build abstraction package and a registered native adapter."]
                           if target_major == 27 else []), "can_apply": False}
    report = validate_manifest(manifest_path, target_major=target_major,
                               os_build=os_build, architecture=architecture)
    if report["ok"]:
        report["ok"] = False
        report["errors"].append("Package files validated; no verified root patch adapter is registered for this package.")
    return report


def deployment_gate(constants, manifest_path: str | Path | None = None) -> dict[str, Any]:
    """Shared CLI/GUI/direct-engine boundary, before any payload/root mounts.

    Future adapters must dispatch through a verified adapter implementation;
    registering a manifest name must never fall through to the legacy engine.
    """
    selected = manifest_path if manifest_path is not None else getattr(constants, "abstraction_manifest", None)
    if constants.detected_os < 26 and selected is None:
        return {"ok": True, "required": False, "errors": [], "can_apply": False}
    machine = platform.machine().lower()
    architecture = {"amd64": "x86_64", "aarch64": "arm64"}.get(machine, machine)
    return root_patch_gate(selected, target_major=constants.detected_os + 1,
                           os_build=constants.detected_os_build, architecture=architecture)
