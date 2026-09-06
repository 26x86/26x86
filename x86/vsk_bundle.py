"""Original VSK v1 bundle producer using cryptography's RFC8032 Ed25519.

The signature authenticates the exact 64-byte header plus 128-byte entries.
Magic is its domain separator. Trust keys and rollback floors are supplied
outside the bundle. No private or public trust key is bundled. A signature is
provenance, never Apple hardware admission or permission to execute a guest.
"""
from __future__ import annotations
import hashlib
import json
import os
import stat
import struct
from pathlib import Path
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from x86.vsk_config import MAX_BYTES as MAX_CONFIG, normalize_config, parse_xml

MAGIC = b"VSK-BUNDLE-v1\0\0\0"
HEADER = struct.Struct("<16sHHHHIIIIQI12s")
ENTRY = struct.Struct("<IIQ32s64sI12s")
MAX_ELF = 64 * 1024 * 1024
MAX_ENTRIES = 66
MAX_MANIFEST = 64 + MAX_ENTRIES * 128
ROLE_CONFIG, ROLE_CORE, ROLE_SERVICE = 1, 2, 3


class BundleError(ValueError):
    pass


def _check_path(path: str | Path, *, exists=True) -> Path:
    path = Path(path).expanduser()
    if ".." in path.parts:
        raise BundleError("Parent traversal in a bundle path")
    path = path.absolute()
    for item in reversed([path, *path.parents]):
        try:
            info = item.lstat()
        except FileNotFoundError:
            if item == path and not exists:
                continue
            raise BundleError("Bundle path or parent does not exist")
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise BundleError("Symlink/reparse points are forbidden in bundle paths")
    return path


def _stamp(info):
    # Windows Python lstat/fstat can expose different legacy ctime meanings
    # (creation vs metadata-change). Stable file ID, size, mtime and digests
    # provide the cross-API binding; POSIX additionally binds change time.
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, (None if os.name == "nt" else info.st_ctime_ns)


def _read(path, limit):
    path = _check_path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= limit:
        raise BundleError("Bundle input must be a nonempty bounded regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if _stamp(opened) != _stamp(before):
            raise BundleError("Bundle input identity changed before reading")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    _check_path(path)
    if len(raw) != before.st_size or _stamp(after) != _stamp(before) or _stamp(path.lstat()) != _stamp(before):
        raise BundleError("Bundle input changed during reading")
    return path, raw, _stamp(before)


def validate_elf(raw: bytes) -> dict:
    """Mirror vf_elf's static x86_64, 4-KiB page load contract without execution."""
    def bounded(offset, size):
        return offset <= len(raw) and size <= len(raw) - offset
    def power2(value):
        return not value or not value & (value - 1)
    def canonical(value):
        return value <= 0x00007FFFFFFFFFFF or value >= 0xFFFF800000000000
    maximum = (1 << 64) - 1
    if not 64 <= len(raw) <= MAX_ELF or raw[:16] != b"\x7fELF\x02\x01\x01" + bytes(9):
        raise BundleError("Expected bounded ELF64 LE v1 with System V ABI and zero padding")
    fields = struct.unpack_from("<HHIQQQIHHHHHH", raw, 16)
    kind, machine, version, entry, phoff, shoff, eflags, ehsize, phsize, phcount, shsize, shcount, shstr = fields
    if (kind, machine, version, eflags, ehsize, phsize) != (2, 62, 1, 0, 64, 56) or not 1 <= phcount <= 64:
        raise BundleError("Expected static ET_EXEC x86_64 ELF with bounded program headers")
    if phoff < 64 or phoff & 7 or not bounded(phoff, phcount * 56):
        raise BundleError("ELF program headers exceed bounds or alignment")
    if shoff:
        if not 1 <= shcount <= 4096 or shstr >= shcount or shsize != 64:
            raise BundleError("Invalid ELF section table")
        if shoff < 64 or shoff & 7 or not bounded(shoff, shcount * 64):
            raise BundleError("ELF section table exceeds bounds or alignment")
        if shoff < phoff + phcount * 56 and phoff < shoff + shcount * 64:
            raise BundleError("ELF header tables overlap")
        for index in range(shcount):
            _, stype, flags, _, offset, size, _, _, align, _ = struct.unpack_from("<IIQQQQIIQQ", raw, shoff + index * 64)
            if stype in (4, 9, 19, 6, 11) or flags & 0x400:
                raise BundleError("ELF relocation, dynamic and TLS sections are unsupported")
            if not power2(align) or not bounded(offset, 0 if stype == 8 else size):
                raise BundleError("ELF section exceeds bounds or alignment")
    elif shcount or shstr or shsize:
        raise BundleError("ELF section metadata has no section table")
    if not entry or not canonical(entry):
        raise BundleError("ELF entry must be nonzero and 48-bit canonical")
    ranges, previous, executable_entry = [], None, False
    for index in range(phcount):
        ptype, flags, offset, virtual, _, filesz, memsz, align = struct.unpack_from("<IIQQQQQQ", raw, phoff + index * 56)
        if ptype == 0:
            continue
        if ptype != 1:
            if ptype == 0x6474E551:
                if flags & ~7 or flags & 1 or filesz or memsz:
                    raise BundleError("Unsupported executable or nonempty ELF stack header")
            elif ptype == 6:
                if flags != 4 or offset != phoff or filesz != phcount * 56 or memsz != filesz:
                    raise BundleError("Invalid ELF PHDR metadata")
            else:
                raise BundleError("Unsupported ELF program header semantics")
            if not bounded(offset, filesz) or not power2(align):
                raise BundleError("ELF metadata exceeds bounds or alignment")
            continue
        if len(ranges) == 16 or flags & ~7 or not flags & 4 or flags & 3 == 3:
            raise BundleError("Invalid ELF PT_LOAD count or permissions")
        if not memsz or filesz > memsz or not bounded(offset, filesz) or memsz - 1 > maximum - virtual:
            raise BundleError("ELF load segment exceeds bounds")
        last = virtual + memsz - 1
        if not virtual or not canonical(virtual) or not canonical(last) or virtual >> 47 != last >> 47:
            raise BundleError("ELF load range is not in one canonical address half")
        if (not power2(align) or (align > 1 and virtual % align != offset % align)
                or virtual % 4096 != offset % 4096):
            raise BundleError("Invalid ELF segment or page alignment")
        if last > maximum - 4096:
            raise BundleError("ELF page range overflows")
        page, end = virtual & ~4095, (last | 4095) + 1
        if any(page < other_end and other_page < end for other_page, other_end in ranges):
            raise BundleError("Overlapping ELF load pages")
        if previous is not None and virtual < previous:
            raise BundleError("ELF load segments are not in address order")
        previous = virtual
        ranges.append((page, end))
        if flags & 1 and virtual <= entry < virtual + filesz:
            executable_entry = True
    if not ranges or not executable_entry or max(end for _, end in ranges) - min(start for start, _ in ranges) > MAX_ELF:
        raise BundleError("ELF requires bounded contiguous image memory and a file-backed executable entry")
    return {"format":"ELF64", "architecture":"x86_64", "entry":entry,
            "load_segments":len(ranges), "execution_verified":False}


def _filename(role, instance):
    if role == ROLE_CONFIG and instance == 0:
        return "config.plist"
    if role == ROLE_CORE and instance == 0:
        return "core.elf"
    if role == ROLE_SERVICE and type(instance) is int and 1 <= instance <= 64:
        return f"cell-{instance}.elf"
    raise BundleError("Invalid role or service instance")


def _target_epoch(target_major, release_epoch):
    if type(target_major) is not int or target_major not in (26, 27):
        raise BundleError("Target major must be 26 or 27")
    if type(release_epoch) is not int or not 1 <= release_epoch <= (1 << 64) - 1:
        raise BundleError("Explicit nonzero uint64 release epoch required")


def _digests(raw):
    return hashlib.sha256(raw).digest(), hashlib.sha512(raw).digest()


def parse_manifest(raw: bytes, *, expected_target: int, minimum_release_epoch: int):
    _target_epoch(expected_target, minimum_release_epoch)
    if not 64 <= len(raw) <= MAX_MANIFEST:
        raise BundleError("Invalid manifest length")
    magic, version, hsize, esize, algorithm, size, count, flags, reserved, epoch, target, padding = HEADER.unpack_from(raw)
    if (magic != MAGIC or (version, hsize, esize, algorithm) != (1,64,128,1)
            or size != len(raw) or not 3 <= count <= MAX_ENTRIES or size != 64 + count*128
            or flags or reserved or padding != bytes(12)):
        raise BundleError("Invalid manifest header or reserved fields")
    if target != expected_target or not epoch or epoch < minimum_release_epoch:
        raise BundleError("Manifest target mismatch or release epoch below trusted floor")
    entries, prior = [], (0,0)
    for index in range(count):
        role, instance, length, sha256, sha512, flags, padding = ENTRY.unpack_from(raw, 64 + index*128)
        name = _filename(role,instance)
        if (role,instance) <= prior or flags or padding != bytes(12):
            raise BundleError("Unsorted/duplicate manifest entry or reserved fields")
        limit = MAX_CONFIG if role == ROLE_CONFIG else MAX_ELF
        if not 0 < length <= limit:
            raise BundleError("Manifest blob length outside bounds")
        entries.append({"role":role,"instance":instance,"name":name,"size":length,
                        "sha256":sha256,"sha512":sha512})
        prior = role,instance
    if entries[0]["role"] != ROLE_CONFIG or entries[1]["role"] != ROLE_CORE or entries[2]["role"] != ROLE_SERVICE:
        raise BundleError("Bundle requires one config, one core and at least one service")
    return {"target_major":target,"release_epoch":epoch,"entries":entries}


def verify_bundle(directory, *, trusted_public_key: bytes, expected_target: int,
                  minimum_release_epoch: int, profiles=None) -> dict:
    """Use an external trust key/floor; never accept a key supplied by a bundle."""
    directory = _check_path(directory)
    if not directory.is_dir() or type(trusted_public_key) is not bytes or len(trusted_public_key) != 32:
        raise BundleError("External raw32 trusted public key and bundle directory required")
    _, manifest, _ = _read(directory / "manifest.vfb", MAX_MANIFEST)
    _, signature, _ = _read(directory / "manifest.sig", 64)
    if len(signature) != 64:
        raise BundleError("Ed25519 signature must be exactly 64 bytes")
    try:
        Ed25519PublicKey.from_public_bytes(trusted_public_key).verify(signature, manifest)
    except (InvalidSignature, ValueError):
        raise BundleError("Bundle signature failed against external trust key") from None
    parsed = parse_manifest(manifest, expected_target=expected_target, minimum_release_epoch=minimum_release_epoch)
    expected_names = {"manifest.vfb", "manifest.sig", "bundle-report.json", *[e["name"] for e in parsed["entries"]]}
    if any(path.name not in expected_names for path in directory.iterdir()):
        raise BundleError("Unexpected file in bundle directory")
    records = []
    for entry in parsed["entries"]:
        _, raw, _ = _read(directory / entry["name"], MAX_CONFIG if entry["role"] == ROLE_CONFIG else MAX_ELF)
        if len(raw) != entry["size"] or _digests(raw) != (entry["sha256"],entry["sha512"]):
            raise BundleError("Bundle payload digest/length mismatch")
        if entry["role"] == ROLE_CONFIG:
            config = normalize_config(parse_xml(raw), profiles=profiles)
            if config["Guest"]["ProfileID"] != "arm64-conformance-v1":
                build = profiles[config["Guest"]["ProfileID"]]["BuildID"]
                if int(build[:2])+1 != expected_target:
                    raise BundleError("Guest profile build does not match bundle target")
        else:
            validate_elf(raw)
        records.append({"role":entry["role"],"instance":entry["instance"],"name":entry["name"],
                        "size":len(raw),"sha256":entry["sha256"].hex(),"sha512":entry["sha512"].hex()})
    return {"schema":"26x86.vsk-bundle-report/1", "signature_verified":True,
        "trusted_public_key_sha256":hashlib.sha256(trusted_public_key).hexdigest(),
        "manifest_sha256":hashlib.sha256(manifest).hexdigest(), "entries":records,
        "target_major":parsed["target_major"],"release_epoch":parsed["release_epoch"],
        "minimum_release_epoch":minimum_release_epoch,"rollback_floor_source":"caller",
        "boot_authorized":False,"hardware_verified":False,"guest_execution_verified":False}


def create_bundle(config, core, services: Mapping[int, str | Path], output, *,
                  private_key: Ed25519PrivateKey, target_major: int, release_epoch: int,
                  profiles=None) -> dict:
    """Create a new flat bundle; inputs remain untouched, private key stays external."""
    _target_epoch(target_major, release_epoch)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise BundleError("An explicit Ed25519 private key object is required")
    if not isinstance(services, Mapping) or not 1 <= len(services) <= 64:
        raise BundleError("One to 64 explicitly indexed service ELF inputs are required")
    for instance in services:
        _filename(ROLE_SERVICE,instance)
    target = _check_path(output, exists=False)
    if target.exists():
        raise BundleError("Output directory already exists")
    inputs = [(ROLE_CONFIG,0,config),(ROLE_CORE,0,core)] + [(ROLE_SERVICE,i,services[i]) for i in sorted(services)]
    records, aliases = [], set()
    for role, instance, source in inputs:
        path, raw, stamp = _read(source, MAX_CONFIG if role == ROLE_CONFIG else MAX_ELF)
        if stamp[:2] in aliases:
            raise BundleError("Duplicate/hardlinked bundle inputs are forbidden")
        aliases.add(stamp[:2])
        if role == ROLE_CONFIG:
            normalize_config(parse_xml(raw), profiles=profiles)
        else:
            validate_elf(raw)
        records.append((role,instance,path,stamp,len(raw),*_digests(raw)))
    manifest = HEADER.pack(MAGIC,1,64,128,1,64+len(records)*128,len(records),0,0,release_epoch,target_major,bytes(12))
    manifest += b"".join(ENTRY.pack(role,instance,size,sha256,sha512,0,bytes(12)) for role,instance,_,_,size,sha256,sha512 in records)
    signature = private_key.sign(manifest)
    public = private_key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    # Exclusive directory creation never replaces an existing ESP/output. The
    # signature is written last, after every input and copied payload check.
    target.mkdir()
    try:
        for role,instance,path,stamp,size,sha256,sha512 in records:
            _, raw, now = _read(path, MAX_CONFIG if role == ROLE_CONFIG else MAX_ELF)
            if stamp != now or size != len(raw) or (sha256,sha512) != _digests(raw):
                raise BundleError("Bundle input changed between validation and staging")
            _write_new(target / _filename(role,instance),raw)
        _write_new(target / "manifest.vfb",manifest)
        _write_new(target / "manifest.sig",signature)
        report = verify_bundle(target,trusted_public_key=public,expected_target=target_major,
                               minimum_release_epoch=release_epoch,profiles=profiles)
        _write_new(target / "bundle-report.json",(json.dumps(report,indent=2)+"\n").encode("utf-8"))
        return report
    except Exception:
        # Revoke the only signature created by this call. Preserve the new
        # incomplete directory for diagnosis; never recursively remove paths.
        try:
            _check_path(target)
            (target / "manifest.sig").unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _write_new(path, raw):
    _check_path(path,exists=False)
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    _, staged, _ = _read(path,len(raw))
    if staged != raw:
        raise BundleError("Staged bytes differ from validated input")


def load_private_key(path) -> Ed25519PrivateKey:
    """Explicit raw32 Ed25519 seed file; never return it in a report."""
    _, raw, _ = _read(path,32)
    if len(raw) != 32:
        raise BundleError("Private key must be a raw 32-byte Ed25519 seed")
    return Ed25519PrivateKey.from_private_bytes(raw)
