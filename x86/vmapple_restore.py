"""Original-preserving iBootStage2 restore sequence for the VMApple runner.

This module operates after a real Stage2 UART marker.  Restore-role IM4P files
are checked against the official BuildManifest, normalized into a fresh output
directory, wrapped with the already-issued iBEC IM4M ticket, and transferred
over the observed recovery endpoint.  The source role files, installer and
IPSW are never opened for writing.

An acknowledged ``bootx`` command is transport evidence only.  Kernel,
Recovery UI and installer success must be established from subsequent guest
UART/graphics evidence and are therefore left false by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import time
from typing import Any

from .vmapple import (
    MAX_RECOVERY_BYTES,
    RecoveryProtocolError,
    RecoveryTransport,
    _regular,
    _sha256,
)
from .vmapple_personalization import _der, _der_content


ROLE_TAGS: dict[str, tuple[bytes, bytes]] = {
    "RestoreKernelCache": (b"krnl", b"rkrn"),
    "RestoreDeviceTree": (b"dtre", b"rdtr"),
    "RestoreTrustCache": (b"trst", b"rtsc"),
    "RestoreLogo": (b"logo", b"rlgo"),
    "RestoreRamDisk": (b"rdsk", b"rdsk"),
}
REQUIRED_ROLES = (
    "RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache",
)
STANDARD_BOOT_ARGS = "rd=md0 nand-enable-reformat=1 -progress -restore"
BOOT_ARGS_ENV_VAR = "VENFIRE_RESTORE_BOOT_ARGS"


def resolve_boot_args():
    """Effective boot-args for setenv; env override keeps the standard default."""
    args = os.environ.get(BOOT_ARGS_ENV_VAR, STANDARD_BOOT_ARGS)
    if not isinstance(args, str):
        raise ValueError("Restore boot-args must be 1..254 printable ASCII")
    try:
        raw = args.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("Restore boot-args must be 1..254 printable ASCII")
    if not 0 < len(raw) < 255 or any(v < 32 or v > 126 for v in raw):
        raise ValueError("Restore boot-args must be 1..254 printable ASCII")
    return args
MAX_MANIFEST_BYTES = 32 * 1024 * 1024


class RestoreChainError(RuntimeError):
    """The original-preserving restore chain could not complete."""

    def __init__(self, message: str, report: dict[str, Any]):
        self.report = report
        super().__init__(message)


def _element(data: bytes, offset: int, limit: int) -> tuple[int, int, int]:
    if offset < 0 or offset + 2 > limit:
        raise ValueError("Truncated DER element")
    tag, length = data[offset], data[offset + 1]
    start = offset + 2
    if tag & 0x1F == 0x1F:
        raise ValueError("Unexpected high-tag-number DER element")
    if length & 0x80:
        count = length & 0x7F
        if not 1 <= count <= 4 or start + count > limit or data[start] == 0:
            raise ValueError("Invalid DER length")
        length = int.from_bytes(data[start:start + count], "big")
        start += count
        if length < 128:
            raise ValueError("Noncanonical DER length")
    end = start + length
    if end > limit:
        raise ValueError("DER element exceeds container")
    return tag, start, end


def _im4p_spans(data: bytes) -> tuple[tuple[int, int], tuple[int, int], bytes]:
    tag, start, end = _element(data, 0, len(data))
    if tag != 0x30 or end != len(data):
        raise ValueError("Expected one complete IM4P sequence")
    fields: list[tuple[int, int, int]] = []
    position = start
    while position < end:
        fields.append(_element(data, position, end))
        position = fields[-1][2]
    if len(fields) < 4:
        raise ValueError("IM4P is missing its type or payload")
    magic, _, _ = fields[0]
    if magic != 0x16 or data[fields[0][1]:fields[0][2]] != b"IM4P":
        raise ValueError("Expected IM4P magic")
    kind, kind_start, kind_end = fields[1]
    if kind != 0x16 or kind_end - kind_start != 4:
        raise ValueError("IM4P type is not a four-byte string")
    if fields[2][0] != 0x16 or fields[3][0] != 0x04:
        raise ValueError("Unexpected IM4P version or payload field")
    payload = data[fields[3][1]:fields[3][2]]
    return (kind_start, kind_end), (fields[3][1], fields[3][2]), payload


def _read_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = _regular(path, "BuildManifest", limit=MAX_MANIFEST_BYTES)
    try:
        manifest = plistlib.loads(manifest_path.read_bytes())
    except (ValueError, TypeError, OverflowError, plistlib.InvalidFileException) as exc:
        raise ValueError("BuildManifest is not a valid plist") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("BuildIdentities"), list):
        raise ValueError("BuildManifest must contain BuildIdentities")
    return manifest


def _restore_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    identities = [
        item for item in manifest["BuildIdentities"]
        if isinstance(item, dict)
        and isinstance(item.get("Info"), dict)
        and item["Info"].get("DeviceClass") == "vma2macosap"
        and item["Info"].get("Variant") == "Customer Erase Install (IPSW)"
    ]
    if len(identities) != 1:
        raise ValueError("Expected exactly one official vma2macosap erase identity")
    return identities[0]


def _digest_algorithm(digest: bytes) -> str:
    algorithm = {20: "sha1", 32: "sha256", 48: "sha384"}.get(len(digest))
    if algorithm is None:
        raise ValueError("Unsupported official restore-role digest")
    return algorithm


def normalize_role(source: str | Path, role: str, expected_digest: bytes,
                   destination: Path) -> dict[str, Any]:
    """Copy one role and change only the IM4P type metadata when required."""
    if role not in ROLE_TAGS:
        raise ValueError("Unsupported restore role: " + role)
    source_path = _regular(source, role, limit=MAX_RECOVERY_BYTES)
    raw = source_path.read_bytes()
    kind_span, payload_span, payload = _im4p_spans(raw)
    permitted, required = ROLE_TAGS[role]
    actual = raw[kind_span[0]:kind_span[1]]
    if actual not in (permitted, required):
        raise ValueError(f"{role} has unexpected IM4P type {actual!r}")
    normalized = raw if actual == required else raw[:kind_span[0]] + required + raw[kind_span[1]:]
    algorithm = _digest_algorithm(expected_digest)
    if hashlib.new(algorithm, normalized).digest() != expected_digest:
        raise ValueError(f"{role} does not match the official BuildManifest digest")
    if normalized[payload_span[0]:payload_span[1]] != payload:
        raise ValueError(f"{role} payload changed while normalizing metadata")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as target:
        target.write(normalized)
    return {
        "role": role,
        "source": str(source_path),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "prepared_sha256": hashlib.sha256(normalized).hexdigest(),
        "size_bytes": len(normalized),
        "original_type": actual.decode("ascii"),
        "restore_type": required.decode("ascii"),
        "metadata_changed": actual != required,
        "payload_preserved": True,
        "official_digest_algorithm": algorithm,
        "official_digest": expected_digest.hex(),
    }


def wrap_role(prepared: str | Path, ticket: str | Path, destination: Path) -> dict[str, Any]:
    """Wrap unchanged prepared IM4P and IM4M bytes in an IMG4 container."""
    prepared_path = _regular(prepared, "prepared restore role", limit=MAX_RECOVERY_BYTES)
    ticket_path = _regular(ticket, "accepted iBEC IM4M", limit=4 * 1024 * 1024)
    payload = prepared_path.read_bytes()
    signature = ticket_path.read_bytes()
    _der_content(payload, b"IM4P")
    _der_content(signature, b"IM4M")
    wrapped = _der(0x30, _der(0x16, b"IMG4") + payload + _der(0xA0, signature))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as target:
        target.write(wrapped)
    return {
        "path": str(destination),
        "sha256": hashlib.sha256(wrapped).hexdigest(),
        "size_bytes": len(wrapped),
        "im4p_preserved": payload in wrapped,
        "ticket_preserved": signature in wrapped,
        "ticket_sha256": hashlib.sha256(signature).hexdigest(),
        "guest_acceptance_verified": False,
    }


def _source_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        records.append({"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    return records


def _sources_intact(records: list[dict[str, Any]]) -> bool:
    for record in records:
        path = Path(record["path"])
        try:
            if (not path.is_file() or path.stat().st_size != record["bytes"]
                    or _sha256(path) != record["sha256"]):
                return False
        except OSError:
            return False
    return True


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Restore chain deadline expired")
    return remaining


def _compact_upload(result: dict[str, Any]) -> dict[str, Any]:
    blocks = result.pop("blocks", [])
    result["blocks_acknowledged"] = len(blocks) if isinstance(blocks, list) else None
    return result


def run_restore_sequence(*, socket_path: str, build_manifest: str | Path,
                         role_sources: dict[str, str | Path], ticket: str | Path,
                         output: str | Path, total_timeout: float = 900.0,
                         transport_holders: list[object] | None = None,
                         extra_commands: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """Prepare and send the standard macOS restore sequence after Stage2."""
    if not 0 < total_timeout <= 3600:
        raise ValueError("Restore timeout must be between 0 and 3600 seconds")
    missing = [role for role in REQUIRED_ROLES if role not in role_sources]
    unsupported = set(role_sources) - set(ROLE_TAGS)
    if missing or unsupported:
        raise ValueError("Restore roles missing or unsupported: " + ", ".join(missing or sorted(unsupported)))
    manifest_path = _regular(build_manifest, "BuildManifest", limit=MAX_MANIFEST_BYTES)
    ticket_path = _regular(ticket, "accepted iBEC IM4M", limit=4 * 1024 * 1024)
    manifest = _read_manifest(manifest_path)
    identity = _restore_identity(manifest)
    sources = _source_records([manifest_path, ticket_path,
                               *[_regular(role_sources[role], role, limit=MAX_RECOVERY_BYTES)
                                 for role in role_sources]])
    directory = Path(output).expanduser().absolute()
    if directory.exists() or directory.is_symlink():
        raise ValueError("Restore output directory must be new")
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    prepared_dir = directory / "prepared"
    images_dir = directory / "images"
    prepared_dir.mkdir(mode=0o700)
    images_dir.mkdir(mode=0o700)
    report: dict[str, Any] = {
        "schema": "26x86.vmapple-restore/1",
        "roles": {},
        "steps": [],
        "commands": [],
        "sequence_sent": False,
        "bootx_acknowledged": False,
        "guest_acceptance_verified": False,
        "xnu_executed": False,
        "macos_boot_verified": False,
        "installer_ui_visible": False,
        "input_integrity": False,
        "error": None,
    }
    output_files: list[Path] = []
    failure: BaseException | None = None
    try:
        for role, source in role_sources.items():
            entry = identity.get("Manifest", {}).get(role, {})
            digest = entry.get("Digest") if isinstance(entry, dict) else None
            if not isinstance(digest, bytes):
                raise ValueError("BuildManifest is missing the digest for " + role)
            prepared = prepared_dir / (role + ".im4p")
            normalized = normalize_role(source, role, digest, prepared)
            output_files.append(prepared)
            wrapped = images_dir / (role + ".img4")
            wrapped_proof = wrap_role(prepared, ticket_path, wrapped)
            output_files.append(wrapped)
            report["roles"][role] = {"normalized": normalized, "wrapped": wrapped_proof}

        deadline = time.monotonic() + total_timeout
        transport = RecoveryTransport(socket_path, timeout=min(10.0, _remaining(deadline)))
        transport.__enter__()
        keep_transport = False
        try:
            configuration = transport.configure_recovery(deadline=deadline)
            report["configuration"] = configuration

            def command(text: str, request: int = 0) -> None:
                transport.send_command(text, request=request, deadline=deadline)
                report["commands"].append({"command": text, "request": request, "acknowledged": True})

            def upload(role: str) -> None:
                image = report["roles"][role]["wrapped"]
                result = transport.send_recovery_file(
                    Path(image["path"]), total_timeout=_remaining(deadline),
                    expected_sha256=image["sha256"],
                )
                report["steps"].append({"role": role, "upload": _compact_upload(result)})

            if "RestoreLogo" in role_sources:
                upload("RestoreLogo")
                command("setpicture 4")
                command("bgcolor 0 0 0")
            upload("RestoreTrustCache")
            command("firmware")
            upload("RestoreRamDisk")
            command("ramdisk")
            time.sleep(min(2.0, _remaining(deadline)))
            upload("RestoreDeviceTree")
            command("devicetree")
            upload("RestoreKernelCache")
            # idevicerestore sends a DFU class notification after the kernel
            # image.  iBEC may deliberately STALL this request because the
            # notification result is unused by the upstream restore path.
            # Preserve that real response as evidence; only the exact 0200
            # endpoint STALL is tolerated, and no success byte is synthesized.
            try:
                transport.control(0x21, 1, deadline=deadline)
                report["preboot_notification"] = {"acknowledged": True}
            except RecoveryProtocolError as exc:
                if str(exc) != "Guest USB endpoint stalled: 0200":
                    raise
                report["preboot_notification"] = {
                    "acknowledged": False,
                    "guest_stall_hex": "0200",
                    "handling": "notification result unused by restore protocol",
                }
            for extra in extra_commands or ():
                if not isinstance(extra, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 _=.+-]*", extra):
                    raise ValueError("Restore extra command must match [A-Za-z][A-Za-z0-9 _=.+-]*")
                try:
                    transport.send_command(extra, request=0, deadline=deadline)
                    report["commands"].append({"command": extra, "request": 0, "acknowledged": True})
                except RecoveryProtocolError as exc:
                    report["commands"].append({"command": extra, "request": 0, "acknowledged": False,
                                               "error": str(exc)[:256]})
            command("setenv boot-args " + resolve_boot_args())
            command("bootx", request=1)
            report["sequence_sent"] = True
            report["bootx_acknowledged"] = True
            if transport_holders is not None:
                transport_holders.append(transport)
                keep_transport = True
        finally:
            if not keep_transport:
                transport.__exit__(None, None, None)
    except BaseException as exc:
        failure = exc
        report["error"] = f"{type(exc).__name__}: {exc}"[:2048]
    finally:
        report["input_integrity"] = _sources_intact(sources)
        if not report["input_integrity"]:
            report["sequence_sent"] = False
            report["error"] = "One or more restore inputs changed during the run"
            for path in output_files:
                path.unlink(missing_ok=True)
        report["output"] = str(directory)
        (directory / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failure is not None:
        raise RestoreChainError(report["error"], report) from failure
    if not report["input_integrity"]:
        raise RestoreChainError(report["error"], report)
    return report


__all__ = [
    "REQUIRED_ROLES", "ROLE_TAGS", "RestoreChainError", "normalize_role",
    "run_restore_sequence", "wrap_role",
]
