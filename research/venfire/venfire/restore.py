"""Standard restore-role IMG4 containers, with immutable executable/data payloads.

Role mappings follow pinned idevicerestore img4.c. The four-byte IM4P type is
container metadata; no payload, ticket, signature check, or guest code is patched.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import time

from .artifacts import create_manifest, read_regular, require_intact, verify_manifest
from .recovery import MAX_RECOVERY_IMAGE, RecoveryStallError, RecoveryTransport


ROLE_TAGS = {
    "RestoreKernelCache": (b"krnl", b"rkrn"),
    "RestoreDeviceTree": (b"dtre", b"rdtr"),
    "RestoreTrustCache": (b"trst", b"rtsc"),
    "RestoreLogo": (b"logo", b"rlgo"),
    "RestoreRamDisk": (b"rdsk", b"rdsk"),
}
STANDARD_RESTORE_BOOT_ARGS = "rd=md0 nand-enable-reformat=1 -progress -restore"
BOOT_ARGS_ENV_VAR = "VENFIRE_RESTORE_BOOT_ARGS"


def resolve_boot_args():
    """Effective boot-args for setenv; env override keeps the standard default."""
    args = os.environ.get(BOOT_ARGS_ENV_VAR, STANDARD_RESTORE_BOOT_ARGS)
    if not isinstance(args, str):
        raise ValueError("Restore boot-args must be 1..254 printable ASCII")
    try:
        raw = args.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("Restore boot-args must be 1..254 printable ASCII")
    if not 0 < len(raw) < 255 or any(v < 32 or v > 126 for v in raw):
        raise ValueError("Restore boot-args must be 1..254 printable ASCII")
    return args


def _element(data, offset, limit):
    if offset < 0 or offset + 2 > limit:
        raise ValueError("Truncated DER element")
    tag, length = data[offset], data[offset + 1]
    start = offset + 2
    if tag & 31 == 31:
        raise ValueError("Unexpected high-tag-number DER element")
    if length & 128:
        count = length & 127
        if not 1 <= count <= 4 or start + count > limit or data[start] == 0:
            raise ValueError("Invalid DER length")
        length = int.from_bytes(data[start:start + count], "big")
        start += count
        if length < 128:
            raise ValueError("Noncanonical DER length")
    if start + length > limit:
        raise ValueError("DER element exceeds container")
    return tag, start, start + length


def _im4p_fields(data):
    tag, start, end = _element(data, 0, len(data))
    if tag != 0x30 or end != len(data):
        raise ValueError("Expected exactly one complete IM4P sequence")
    fields = []
    position = start
    for _ in range(4):
        fields.append(_element(data, position, end))
        position = fields[-1][2]
    magic, kind, version, payload = fields
    if (magic[0] != 0x16 or data[magic[1]:magic[2]] != b"IM4P"
            or kind[0] != 0x16 or kind[2] - kind[1] != 4
            or version[0] != 0x16 or payload[0] != 4):
        raise ValueError("Unexpected IM4P field types")
    return kind[1:3], payload[1:3]


def _read_bounded(path, maximum):
    with read_regular(path) as source:
        size = os.fstat(source.fileno()).st_size
        if not 0 < size <= maximum:
            raise ValueError("Restore input is empty or exceeds its bound")
        data = source.read(size)
        if len(data) != size or source.read(1):
            raise ValueError("Restore input changed size")
    if not data or len(data) > maximum:
        raise ValueError("Restore input is empty or exceeds its bound")
    return data


def _stream_im4p_fields(source, size):
    def element(offset, limit):
        if offset < 0 or offset + 2 > limit:
            raise ValueError("Truncated DER element")
        source.seek(offset)
        header = source.read(2)
        if len(header) != 2 or header[0] & 31 == 31:
            raise ValueError("Invalid DER header")
        tag, length = header
        start = offset + 2
        if length & 128:
            count = length & 127
            if not 1 <= count <= 4 or start + count > limit:
                raise ValueError("Invalid DER length")
            encoded = source.read(count)
            if len(encoded) != count or encoded[0] == 0:
                raise ValueError("Invalid DER length")
            length = int.from_bytes(encoded, "big")
            start += count
            if length < 128:
                raise ValueError("Noncanonical DER length")
        if start + length > limit:
            raise ValueError("DER element exceeds container")
        return tag, start, start + length
    tag, start, end = element(0, size)
    if tag != 0x30 or end != size:
        raise ValueError("Expected one complete IM4P sequence")
    magic = element(start, end)
    source.seek(magic[1])
    if magic[0] != 0x16 or magic[2] - magic[1] != 4 or source.read(4) != b"IM4P":
        raise ValueError("Expected IM4P magic")
    kind = element(magic[2], end)
    version = element(kind[2], end)
    payload = element(version[2], end)
    if kind[0] != 0x16 or kind[2] - kind[1] != 4 or version[0] != 0x16 or payload[0] != 4:
        raise ValueError("Unexpected IM4P field types")
    return kind[1:3], payload[1:3]


def _role_chunks(source, size, kind, required):
    source.seek(0)
    offset = 0
    while offset < size:
        block = source.read(min(1024 * 1024, size - offset))
        if not block:
            raise ValueError("Restore input became shorter")
        a, b = max(offset, kind[0]), min(offset + len(block), kind[1])
        normalized = block
        if a < b:
            normalized = block[:a - offset] + required[a - kind[0]:b - kind[0]] + block[b - offset:]
        yield offset, block, normalized
        offset += len(block)
    if source.read(1):
        raise ValueError("Restore input became longer")


def prepare_role_container(source, role, expected_digest, output):
    """Create a new standard role container and prove only its type changed."""
    if role not in ROLE_TAGS:
        raise ValueError("Unsupported restore role")
    algorithm = {20: "sha1", 32: "sha256", 48: "sha384"}.get(len(expected_digest))
    if not algorithm:
        raise ValueError("Unsupported official manifest digest")
    manifest = create_manifest([source])
    try:
        require_intact(manifest)
        size = manifest.artifacts[0].size_bytes
        if not 0 < size <= MAX_RECOVERY_IMAGE:
            raise ValueError("Restore input exceeds its bound")
        permitted, required = ROLE_TAGS[role]
        raw_digest, normalized_digest = hashlib.sha256(), hashlib.new(algorithm)
        prepared_digest, before_hash, after_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
        with read_regular(source) as stream:
            kind, payload = _stream_im4p_fields(stream, size)
            stream.seek(kind[0])
            actual = stream.read(4)
            if actual not in (permitted, required):
                raise ValueError("Original component has an unexpected IM4P type")
            for offset, original, prepared in _role_chunks(stream, size, kind, required):
                raw_digest.update(original)
                normalized_digest.update(prepared)
                prepared_digest.update(prepared)
                a, b = max(offset, payload[0]), min(offset + len(original), payload[1])
                if a < b:
                    before_hash.update(original[a - offset:b - offset])
                    after_hash.update(prepared[a - offset:b - offset])
            before, after = before_hash.hexdigest(), after_hash.hexdigest()
            if raw_digest.hexdigest() != manifest.artifacts[0].sha256 or before != after:
                raise ValueError("Original input or OCTET payload changed")
            if normalized_digest.digest() != expected_digest:
                raise ValueError("Prepared restore role does not match the official manifest digest")
            written_digest = hashlib.sha256()
            with Path(output).open("xb") as target:
                for _, _, prepared in _role_chunks(stream, size, kind, required):
                    target.write(prepared)
                    written_digest.update(prepared)
            if written_digest.digest() != prepared_digest.digest():
                raise ValueError("Restore input changed during output generation")
        return {"role": role, "source_sha256": manifest.artifacts[0].sha256,
                "prepared_sha256": prepared_digest.hexdigest(),
                "size_bytes": size, "type_offset": kind[0], "type_length": 4,
                "original_type": actual.decode("ascii"), "restore_type": required.decode("ascii"),
                "metadata_changed": actual != required, "outside_type_bytes_unchanged": True,
                "payload_offset": payload[0], "payload_size": payload[1] - payload[0],
                "original_octet_sha256": before, "prepared_octet_sha256": after,
                "official_digest_algorithm": algorithm, "official_digest": expected_digest.hex(),
                "official_digest_matches": True}
    finally:
        require_intact(manifest)


def _header(tag, size):
    if size < 128:
        return bytes((tag, size))
    encoded = size.to_bytes((size.bit_length() + 7) // 8, "big")
    return bytes((tag, 0x80 | len(encoded))) + encoded


def wrap_role_container(prepared, ticket, output):
    """Wrap validated bytes with an actual Apple IM4M, preserving both exactly."""
    manifest = create_manifest([prepared, ticket])
    try:
        require_intact(manifest)
        payload_size = manifest.artifacts[0].size_bytes
        if not 0 < payload_size <= MAX_RECOVERY_IMAGE:
            raise ValueError("Restore input exceeds its bound")
        signature = _read_bounded(ticket, 4 * 1024 * 1024)
        tag, start, end = _element(signature, 0, len(signature))
        magic_tag, a, b = _element(signature, start, end)
        if tag != 0x30 or end != len(signature) or magic_tag != 0x16 or signature[a:b] != b"IM4M":
            raise ValueError("Expected exactly one original Apple IM4M ticket")
        magic = b"\x16\x04IMG4"
        signature_header = _header(0xa0, len(signature))
        header = _header(0x30, len(magic) + payload_size + len(signature_header) + len(signature))
        copied = hashlib.sha256()
        with read_regular(prepared) as source:
            _stream_im4p_fields(source, payload_size)
            source.seek(0)
            with Path(output).open("xb") as target:
                target.write(header + magic)
                remaining = payload_size
                while remaining:
                    block = source.read(min(1024 * 1024, remaining))
                    if not block:
                        raise ValueError("Restore input became shorter")
                    target.write(block)
                    copied.update(block)
                    remaining -= len(block)
                if source.read(1) or copied.hexdigest() != manifest.artifacts[0].sha256:
                    raise ValueError("Restore input changed during wrapping")
                target.write(signature_header + signature)
        record = create_manifest([output]).artifacts[0]
        return {"sha256": record.sha256, "size_bytes": record.size_bytes,
                "im4p_preserved": True, "ticket_preserved": True,
                "ticket_sha256": manifest.artifacts[1].sha256,
                "guest_acceptance_verified": False}
    finally:
        require_intact(manifest)


def run_stage(socket_path, images, *, total_timeout=600, timeout=10):
    """Send a prepared standard restore sequence; boot success needs guest logs.

    images maps each required role to {path, sha256}. Caller must authorize the
    host and provide provenance/TSS/metadata receipts for the prepared images.
    """
    required = {"RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache"}
    if not required <= images.keys() or images.keys() - ROLE_TAGS.keys():
        raise ValueError("Missing required or unsupported restore image roles")
    if not 0 < total_timeout <= 3600:
        raise ValueError("Invalid restore deadline")
    deadline = time.monotonic() + total_timeout
    inputs = create_manifest([entry["path"] for entry in images.values()])
    by_path = {str(Path(a.path)): a.sha256 for a in inputs.artifacts}
    for entry in images.values():
        if by_path[str(Path(entry["path"]).absolute())] != entry["sha256"]:
            raise ValueError("Restore image differs from its personalization receipt")
    report = {"schema": 1, "steps": [], "commands": [], "error": None,
              "sequence_sent": False, "macos_boot_verified": False, "xnu_boot_verified": False}
    interruption = None
    try:
        require_intact(inputs)
        with RecoveryTransport(socket_path, timeout) as transport:
            report["configuration"] = transport.configure_recovery(deadline=deadline)

            def command(text, request=0):
                transport.send_command(text, request=request, deadline=deadline)
                report["commands"].append({"command": text, "request": request, "acknowledged": True})

            def upload(role):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Restore overall deadline expired")
                entry = images[role]
                result = transport.send_recovery_file(entry["path"], total_timeout=remaining,
                                                       expected_sha256=entry["sha256"])
                report["steps"].append({"role": role, "upload": result})

            if "RestoreLogo" in images:
                upload("RestoreLogo")
                command("setpicture 4")
                command("bgcolor 0 0 0")
            upload("RestoreTrustCache")
            command("firmware")
            upload("RestoreRamDisk")
            command("ramdisk")
            if deadline - time.monotonic() < 2:
                raise TimeoutError("Restore ramdisk delay exceeds the remaining deadline")
            time.sleep(2)
            upload("RestoreDeviceTree")
            command("devicetree")
            upload("RestoreKernelCache")
            # recovery.c emits this notification but does not inspect its
            # result. Preserve a real STALL explicitly; never fabricate ACK.
            try:
                transport.control(0x21, 1, deadline=deadline)
                report["preboot_notification"] = {"acknowledged": True}
            except RecoveryStallError as exc:
                report["preboot_notification"] = {"acknowledged": False,
                    "guest_stall_hex": exc.response_hex,
                    "handling": "notification result unused by upstream recovery.c"}
            boot_args = resolve_boot_args()
            report["boot_args"] = boot_args
            command("setenv boot-args " + boot_args)
            command("bootx", request=1)
            report["sequence_sent"] = True
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        if hasattr(exc, "report"):
            report["partial_upload"] = exc.report
        if hasattr(exc, "recovery_report"):
            report["partial_upload"] = exc.recovery_report
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            interruption = exc
    finally:
        report["input_integrity"] = verify_manifest(inputs).to_dict()
    if interruption is not None:
        interruption.restore_report = report
        raise interruption
    return report
