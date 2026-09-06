#!/usr/bin/env python3
"""Read-only acquisition of local Apple archive members; never boots or patches.

7-Zip is used for ISO/HFS/DMG extraction. Unencrypted PBZX/XZ + YAA OTA
payload extraction uses Python's standard library. Archive inputs are opened
read-only; extracted files are created exclusively and SHA-256 receipts are
written beside them. Encryption and update-delta application are unsupported.
YAA format evidence: blacktop/ipsw pkg/ota/yaa/yaa.go and pkg/ota/pbzx.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile


def digest_file(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def fingerprint(path: Path) -> dict:
    st = path.stat()
    return {"path": str(path.resolve()), "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def sevenzip(explicit: str | None) -> str:
    for candidate in (explicit, shutil.which("7z"), "C:/Program Files/7-Zip/7z.exe"):
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise ValueError("7-Zip executable not found; supply --sevenzip")


def inventory(archive: Path, executable: str, kind: str | None) -> list[dict]:
    command = [executable, "l", "-slt", "-sccUTF-8"]
    if kind:
        command.append("-t" + kind)
    command.append(str(archive.resolve()))
    result = subprocess.run(command, capture_output=True, timeout=180)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace"))
    records = []
    active = None
    started = False
    for line in result.stdout.decode("utf-8").splitlines():
        if line == "----------":
            started = True
        if not started or " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        if key == "Path":
            if active:
                records.append(active)
            active = {key: value}
        elif active is not None:
            active[key] = value
    if active:
        records.append(active)
    return records


def receipt(output: Path, data: dict) -> dict:
    result = {"schema": "venfire.apple-asset.v1", **data,
              "output": str(output.resolve()), "size": output.stat().st_size,
              "sha256": digest_file(output), "apple_signature_verified": False,
              "guest_execution": False, "input_modification": False}
    with output.with_name(output.name + ".receipt.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return result


def extract_archive(archive: Path, member: str, output: Path,
                    executable: str, kind: str | None) -> dict:
    before = fingerprint(archive)
    entries = [x for x in inventory(archive, executable, kind)
               if x["Path"].replace("\\", "/") == member.replace("\\", "/")]
    if len(entries) != 1 or entries[0].get("Folder") == "+":
        raise ValueError("Member must identify exactly one regular archive file")
    entry = entries[0]
    if entry.get("Symbolic Link") or entry.get("Mode", "").startswith("l"):
        raise ValueError("Symbolic links are not asset files")
    expected = int(entry["Size"])
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [executable, "x", "-so", "-spd"]
    if kind:
        command.append("-t" + kind)
    command += [str(archive.resolve()), entry["Path"]]
    with output.open("xb") as target:
        result = subprocess.run(command, stdout=target, stderr=subprocess.PIPE, timeout=1800)
    if result.returncode or output.stat().st_size != expected:
        raise ValueError(f"Extraction failed or size mismatch; partial output retained: {output}")
    if fingerprint(archive) != before:
        raise ValueError("Source archive changed during extraction")
    return receipt(output, {"method": "7zip-exact-member", "source": before,
                            "member": entry["Path"], "archive_type": kind,
                            "size_from_archive_metadata": expected})


def read_exact(stream, size: int) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("Truncated archive")
    return data


def decode_pbzx(data: bytes, max_size: int = 2 * 1024 * 1024 * 1024) -> bytes:
    stream = io.BytesIO(data)
    if read_exact(stream, 4) != b"pbzx":
        raise ValueError("Not unencrypted PBZX; encrypted/delta inputs are unsupported")
    block_size = struct.unpack(">Q", read_exact(stream, 8))[0]
    if not 0 < block_size <= 64 * 1024 * 1024:
        raise ValueError("Unsupported PBZX block size")
    output = bytearray()
    while stream.tell() < len(data):
        inflated, stored = struct.unpack(">QQ", read_exact(stream, 16))
        if inflated > block_size or stored > 64 * 1024 * 1024:
            raise ValueError("PBZX block exceeds supported bound")
        block = read_exact(stream, stored)
        decoded = lzma.decompress(block) if block.startswith(b"\xfd7zXZ\x00") else block
        if len(decoded) != inflated:
            raise ValueError("PBZX decompressed length mismatch")
        if len(output) + len(decoded) > max_size:
            raise ValueError("PBZX uncompressed size exceeds limit")
        output.extend(decoded)
    return bytes(output)


def yaa_fields(header: bytes) -> dict:
    stream = io.BytesIO(header)
    fields = {}
    sizes = {"1": 1, "2": 2, "4": 4, "8": 8, "A": 2, "B": 4, "C": 8,
             "S": 8, "T": 12, "H": 32}
    while stream.tell() < len(header):
        tag = read_exact(stream, 4).decode("ascii")
        key, kind = tag[:3], tag[3]
        if kind == "P":
            size = struct.unpack("<H", read_exact(stream, 2))[0]
            value = read_exact(stream, size).decode("utf-8")
        elif kind in sizes:
            raw = read_exact(stream, sizes[kind])
            value = raw if kind in "STH" else int.from_bytes(raw, "little")
        else:
            raise ValueError(f"Unsupported YAA field encoding: {tag}")
        if key in fields:
            raise ValueError(f"Duplicate YAA field: {key}")
        fields[key] = value
    return fields


def yaa_extract(data: bytes, wanted: str) -> tuple[bytes, dict] | None:
    """Extract only complete regular-file data; never apply YOP update patches."""
    stream = io.BytesIO(data)
    while stream.tell() < len(data):
        offset = stream.tell()
        if read_exact(stream, 4) not in (b"YAA1", b"AA01"):
            raise ValueError(f"Invalid YAA magic at {offset}")
        header_size = struct.unpack("<H", read_exact(stream, 2))[0]
        if header_size < 6:
            raise ValueError("Invalid YAA header length")
        fields = yaa_fields(read_exact(stream, header_size - 6))
        size = fields.get("DAT", fields.get("SIZ", 0))
        entry_type = fields.get("TYP")
        content_offset = stream.tell()
        if entry_type == ord("F"):
            if fields.get("YOP") not in (None, ord("E")):
                raise ValueError("Delta-file application is not supported")
            if fields.get("PAT") == wanted:
                value = read_exact(stream, size)
                if fields.get("SH2") and hashlib.sha256(value).digest() != fields["SH2"]:
                    raise ValueError("YAA file SHA-256 mismatch")
                return value, {"yaa_header_offset": offset,
                               "yaa_content_offset": content_offset,
                               "yaa_header_size": header_size,
                               "yaa_content_size": size,
                               "yaa_sha256_present": "SH2" in fields}
            skip = size + fields.get("YEC", 0)
        elif entry_type == ord("M"):
            # Preserve the boundary: this extractor does not apply update operations.
            skip = size
        else:
            skip = 0
        skip += fields.get("XAT", 0)
        if stream.tell() + skip > len(data):
            raise ValueError("YAA entry exceeds payload")
        stream.seek(skip, 1)
    return None


def extract_ota(archive: Path, payload: str, wanted: str, output: Path) -> dict:
    before = fingerprint(archive)
    with zipfile.ZipFile(archive) as container:
        info = container.getinfo(payload)
        if info.file_size > 1024 * 1024 * 1024:
            raise ValueError("Payload exceeds 1 GiB compressed limit")
        packed = container.read(info)  # zipfile verifies the member's CRC32.
    decoded = decode_pbzx(packed)
    match = yaa_extract(decoded, wanted)
    if match is None:
        raise ValueError("Regular file is absent from the selected YAA payload")
    value, evidence = match
    if fingerprint(archive) != before:
        raise ValueError("Source ZIP changed during extraction")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as target:
        target.write(value)
    return receipt(output, {"method": "zip-crc-pbzx-xz-yaa-regular-file",
                            "source": before, "zip_member": payload, "member": wanted,
                            "zip_member_crc32": f"{info.CRC:08x}",
                            "zip_member_sha256": hashlib.sha256(packed).hexdigest(),
                            "decoded_payload_sha256": hashlib.sha256(decoded).hexdigest(),
                            **evidence})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inventory", "extract"):
        child = sub.add_parser(command)
        child.add_argument("archive", type=Path)
        child.add_argument("--sevenzip")
        child.add_argument("--type", choices=("HFS", "Iso", "Dmg", "APFS", "zip"))
        if command == "inventory":
            child.add_argument("--pattern", default="AVPBooter|Virtualization|SharedSupport|vma2")
        else:
            child.add_argument("--member", required=True)
            child.add_argument("--output", required=True, type=Path)
    child = sub.add_parser("extract-ota")
    child.add_argument("archive", type=Path)
    child.add_argument("--payload", required=True)
    child.add_argument("--member", required=True)
    child.add_argument("--output", required=True, type=Path)
    child = sub.add_parser("hash")
    child.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "inventory":
            records = inventory(args.archive, sevenzip(args.sevenzip), args.type)
            result = {"source": fingerprint(args.archive), "entry_count": len(records),
                      "matches": [r for r in records if re.search(args.pattern, r["Path"], re.I)]}
        elif args.command == "extract":
            result = extract_archive(args.archive, args.member, args.output,
                                     sevenzip(args.sevenzip), args.type)
        elif args.command == "extract-ota":
            result = extract_ota(args.archive, args.payload, args.member, args.output)
        else:
            result = {**fingerprint(args.file), "sha256": digest_file(args.file)}
    except (OSError, ValueError, KeyError, lzma.LZMAError, zipfile.BadZipFile,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
