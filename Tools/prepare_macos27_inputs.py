#!/usr/bin/env python3
"""Inventory and extract signed M1 boot inputs from a macOS restore IPSW.

The IPSW and extracted firmware are deliberately treated as opaque signed
inputs.  This tool never decrypts, re-signs, or rewrites an Apple payload.
It records the BuildManifest-selected path, Apple-provided digest metadata,
and local SHA-256 so the guest handoff can reject mismatched inputs.  The
optional install-target inventory reads only ZIP central-directory metadata
for the selected macOS OS/SystemRestoreImage roles; it never extracts their
AEA data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import shutil
import struct
import sys
import zipfile
import zlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_member(zf: zipfile.ZipFile, name: str, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(name) as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    return {
        "ipsw_path": name,
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }


def _der_element(data: bytes, offset: int, limit: int) -> tuple[int, int, int]:
    """Read one bounded, canonical short/high-length DER element."""
    if offset < 0 or offset + 2 > limit:
        raise ValueError("truncated DER element")
    tag = data[offset]
    length = data[offset + 1]
    start = offset + 2
    if tag & 0x1F == 0x1F:
        raise ValueError("high-tag-number DER is unsupported")
    if length & 0x80:
        count = length & 0x7F
        if not 1 <= count <= 4 or start + count > limit or data[start] == 0:
            raise ValueError("invalid DER length")
        length = int.from_bytes(data[start:start + count], "big")
        start += count
        if length < 128:
            raise ValueError("noncanonical DER length")
    end = start + length
    if end > limit:
        raise ValueError("DER element exceeds container")
    return tag, start, end


def im4p_payload(data: bytes) -> tuple[str, bytes]:
    """Return the type and payload from one complete IM4P container.

    The signed container is never rewritten.  A caller may explicitly ask for
    a payload-only derivative (for example the APFS RestoreRamDisk block
    image), but that derivative is recorded separately from the signed input.
    """
    tag, start, end = _der_element(data, 0, len(data))
    if tag != 0x30 or end != len(data):
        raise ValueError("expected one complete IM4P sequence")
    fields: list[tuple[int, int, int]] = []
    position = start
    while position < end:
        fields.append(_der_element(data, position, end))
        position = fields[-1][2]
    if len(fields) < 4:
        raise ValueError("IM4P is missing its type or payload")
    magic, magic_start, magic_end = fields[0]
    if magic != 0x16 or data[magic_start:magic_end] != b"IM4P":
        raise ValueError("expected IM4P magic")
    kind, kind_start, kind_end = fields[1]
    if kind != 0x16 or kind_end - kind_start != 4:
        raise ValueError("IM4P type is not a four-byte string")
    if fields[2][0] != 0x16 or fields[3][0] != 0x04:
        raise ValueError("unexpected IM4P version or payload field")
    return data[kind_start:kind_end].decode("ascii"), data[fields[3][1]:fields[3][2]]


def _der(tag: int, payload: bytes) -> bytes:
    """Encode one bounded DER element for an explicitly recorded derivative."""
    if not 0 <= tag <= 0xFF or tag & 0x1F == 0x1F:
        raise ValueError("unsupported DER tag")
    length = len(payload)
    if length < 0x80:
        encoded_length = bytes([length])
    else:
        raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
        encoded_length = bytes([0x80 | len(raw)]) + raw
    return bytes([tag]) + encoded_length + payload


def _der_magic(data: bytes, magic: bytes) -> None:
    """Validate the outer magic of one complete IM4P/IM4M object."""
    tag, start, end = _der_element(data, 0, len(data))
    if tag != 0x30 or end != len(data):
        raise ValueError("expected one complete DER sequence")
    first_tag, first_start, first_end = _der_element(data, start, end)
    if first_tag != 0x16 or data[first_start:first_end] != magic:
        raise ValueError(f"expected {magic.decode('ascii')} magic")


def wrap_img4(im4p: bytes, im4m: bytes) -> bytes:
    """Wrap unchanged signed IM4P and IM4M objects in a standard IMG4 envelope.

    This is a container-only transformation.  It does not create a signature,
    personalize a ticket, or modify either source object.
    """
    _der_magic(im4p, b"IM4P")
    _der_magic(im4m, b"IM4M")
    return _der(0x30, _der(0x16, b"IMG4") + im4p + _der(0xA0, im4m))


def dfu_suffix(image: bytes) -> bytes:
    """Return Apple's 16-byte DFU suffix for one already-built IMG4 image."""
    suffix = bytes.fromhex("ffffffffac05000155464410")
    return suffix + struct.pack("<I", zlib.crc32(image + suffix) ^ 0xFFFFFFFF)


def _ticket_member(names: list[str], device_class: str) -> str:
    """Select the non-cryptex restore ticket for the selected board."""
    ticket_name = f"apticket.{device_class.lower()}.im4m"
    candidates = [
        name for name in names
        if name.lower().rsplit("/", 1)[-1] == ticket_name
        and "/restore/macos customer/" in name.lower()
    ]
    if not candidates:
        raise RuntimeError(
            f"IPSW has no macOS Customer apticket for {device_class}: {ticket_name}"
        )
    return sorted(candidates, key=lambda name: ("cryptex1" in name.lower(), name))[0]


def decompress_bvx2(payload: bytes) -> bytes:
    """Decode Apple's BVX2/LZFSE payload without changing the signed input."""
    try:
        import lzfse
    except ImportError as exc:  # pragma: no cover - depends on the host toolchain
        raise RuntimeError(
            "--derive-boot-payloads requires the optional Python 'lzfse' package"
        ) from exc
    if not payload.startswith(b"bvx2"):
        raise ValueError("expected a BVX2/LZFSE IM4P payload")
    return lzfse.decompress(payload)


def manifest_name(names: list[str]) -> str:
    if "BuildManifest.plist" in names:
        return "BuildManifest.plist"
    for name in names:
        if name.lower().rsplit("/", 1)[-1] == "buildmanifest.plist":
            return name
    raise RuntimeError("IPSW has no BuildManifest.plist")


def identity_score(identity: dict, requested: str) -> tuple[int, str]:
    info = identity.get("Info", {})
    device = str(info.get("DeviceClass", ""))
    board = str(info.get("BoardConfig", ""))
    variant = str(info.get("Variant", ""))
    text = f"{device} {board}".lower()
    req = requested.lower()
    score = 0
    if req and req in text:
        score += 100
    if "j274" in text:
        score += 80
    if "macmini9,1" in text:
        score += 40
    if "m1" in text:
        score += 10
    if variant.lower().startswith("macos"):
        score += 200
    return score, text


def _identity_info(identity: dict) -> dict:
    value = identity.get("Info", {})
    return value if isinstance(value, dict) else {}


def _identity_manifest(identity: dict) -> dict:
    value = identity.get("Manifest", {})
    return value if isinstance(value, dict) else {}


def _identity_summary(identity: dict) -> dict[str, object]:
    info = _identity_info(identity)
    return {
        "device_class": info.get("DeviceClass"),
        "board_config": info.get("BoardConfig"),
        "variant": info.get("Variant"),
        "build_version": info.get("BuildVersion"),
        "product_version": info.get("ProductVersion"),
    }


_INSTALL_TARGET_ROLES = {
    "os": "OS",
    "systemrestoreimage": "SystemRestoreImage",
}


def manifest_install_target_paths(identity: dict) -> list[tuple[str, dict]]:
    """Return install-target members referenced by one selected identity.

    ``OS`` and ``SystemRestoreImage`` are manifest roles, not boot payloads to
    extract with this tool.  Keep one record per manifest component so a
    shared ZIP member is still visible under both roles when an IPSW uses the
    same path for both references.
    """
    result = []
    for component, value in _identity_manifest(identity).items():
        role = _INSTALL_TARGET_ROLES.get(str(component).lower())
        if role is None or not isinstance(value, dict):
            continue
        path_info = value.get("Info", {})
        if not isinstance(path_info, dict):
            continue
        path = path_info.get("Path")
        if not isinstance(path, str):
            continue
        result.append((path, {
            **path_info,
            "role": role,
            "manifest_component": component,
        }))
    return result


def _manifest_marks_encrypted(path_info: dict) -> bool:
    return any(
        path_info.get(key) is True
        for key in ("IsEncrypted", "Encrypted")
    )


def zip_member_metadata(
    zf: zipfile.ZipFile, path: str, metadata: dict
) -> dict[str, object]:
    """Record central-directory metadata without opening or extracting a member."""
    member = zf.getinfo(path)
    encrypted = (
        bool(member.flag_bits & 0x1)
        or _manifest_marks_encrypted(metadata)
        or member.filename.lower().endswith(".aea")
    )
    return {
        "role": metadata["role"],
        "manifest_component": metadata["manifest_component"],
        "ipsw_path": member.filename,
        "compressed_bytes": member.compress_size,
        "uncompressed_bytes": member.file_size,
        "crc32": member.CRC,
        "encrypted": encrypted,
        "opaque": True,
        "extracted": False,
    }


def _has_component(identity: dict, component: str) -> bool:
    wanted = component.lower()
    return any(
        isinstance(name, str) and name.lower() == wanted
        for name in _identity_manifest(identity)
    )


def select_identity(
    identities: list[dict], requested: str, *, include_restore_ramdisk: bool = False
) -> dict:
    """Select the requested installed-macOS M1 identity."""
    # The root BuildManifest contains several identities with the same device
    # class.  The macOS identity is the one whose variant starts with
    # ``macOS``.  Restore identities are selected separately below so adding a
    # recovery payload cannot silently replace the installed-macOS firmware
    # selection.
    candidates = [
        item for item in identities
        if str(_identity_info(item).get("Variant", "")).lower().startswith("macos")
    ]
    return max(candidates or identities, key=lambda item: identity_score(item, requested))


def select_restore_loader_identity(
    identities: list[dict], requested: str, selected: dict
) -> dict:
    """Find the same-device restore identity containing signed Stage1 loaders.

    The installed macOS identity normally exposes iBoot/iBootData but not the
    LLB/iBSS/iBEC entries used by Apple's AVPBooter restore handoff.  Keep that
    distinction explicit in the receipt and only accept a loader identity
    matching the selected device/board/build where those fields are present.
    """
    selected_info = _identity_info(selected)
    candidates = []
    for identity in identities:
        manifest = _identity_manifest(identity)
        if not all(_has_component(identity, component) for component in ("LLB", "iBSS", "iBEC")):
            continue
        info = _identity_info(identity)
        compatible = True
        for field in ("DeviceClass", "BoardConfig", "BuildVersion", "ProductVersion"):
            expected = selected_info.get(field)
            actual = info.get(field)
            if expected is not None and actual is not None and expected != actual:
                compatible = False
        if not compatible:
            continue
        score, text = identity_score(identity, requested)
        variant = str(info.get("Variant", "")).lower()
        # Prefer the non-upgrade IPSW restore identity.  The manifest itself
        # remains the authority; this only disambiguates duplicate entries.
        if "customer erase install" in variant:
            score += 30
        if "restore" in variant:
            score += 10
        candidates.append((score, text, identity))
    if not candidates:
        raise RuntimeError(
            "no same-device BuildIdentity containing signed LLB/iBSS/iBEC loaders"
        )
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def manifest_paths(
    identity: dict,
    *,
    include_restore_ramdisk: bool = False,
    include_restore_trust_cache: bool = False,
    include_restore_logo: bool = False,
    include_restore_loaders: bool = False,
) -> list[tuple[str, dict]]:
    result = []
    seen = set()
    for component, value in identity.get("Manifest", {}).items():
        if not isinstance(value, dict):
            continue
        path_info = value.get("Info", {})
        path = path_info.get("Path")
        if not isinstance(path, str):
            continue
        key = component.lower()
        boot_component = "iboot" in key or "kernel" in key or "devicetree" in key
        loader_component = include_restore_loaders and key in {"llb", "ibss", "ibec"}
        restore_component = include_restore_ramdisk and key == "restoreramdisk"
        trust_cache_component = include_restore_trust_cache and key == "restoretrustcache"
        logo_component = include_restore_logo and key == "restorelogo"
        if boot_component or loader_component or restore_component or trust_cache_component or logo_component:
            if path in seen:
                continue
            seen.add(path)
            result.append((path, {"component": component, **path_info}))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ipsw", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="j274")
    parser.add_argument("--source-sha256")
    parser.add_argument(
        "--include-restore-ramdisk",
        action="store_true",
        help="also extract the selected BuildManifest RestoreRamDisk IM4P",
    )
    parser.add_argument(
        "--include-restore-trust-cache",
        action="store_true",
        help="also extract the selected BuildManifest RestoreTrustCache IM4P",
    )
    parser.add_argument(
        "--include-restore-logo",
        action="store_true",
        help="also extract the selected BuildManifest RestoreLogo IM4P",
    )
    parser.add_argument(
        "--derive-restore-ramdisk-raw",
        action="store_true",
        help="write the RestoreRamDisk IM4P payload as a separate APFS/raw derivative",
    )
    parser.add_argument(
        "--include-restore-loaders",
        action="store_true",
        help=(
            "also extract same-device signed LLB/iBSS/iBEC from the matching "
            "Customer Erase Install BuildIdentity"
        ),
    )
    parser.add_argument(
        "--derive-boot-payloads",
        action="store_true",
        help=(
            "also decode signed boot IM4P BVX2/LZFSE payloads into separate "
            "raw derivatives; requires the optional Python lzfse package"
        ),
    )
    parser.add_argument(
        "--include-apple-ticket",
        action="store_true",
        help=(
            "extract the board-matched Apple macOS Customer IM4M ticket from "
            "the IPSW and record it separately from BuildManifest components"
        ),
    )
    parser.add_argument(
        "--inventory-install-targets",
        "--inventory-install-images",
        dest="inventory_install_targets",
        action="store_true",
        help=(
            "record ZIP metadata for the selected macOS OS and "
            "SystemRestoreImage members without extracting them"
        ),
    )
    parser.add_argument(
        "--derive-ibss-img4",
        action="store_true",
        help=(
            "wrap the unchanged signed iBSS IM4P with the extracted IM4M "
            "ticket and add an IMG4 plus DFU-suffix derivative"
        ),
    )
    parser.add_argument(
        "--avpbooter",
        type=Path,
        help=(
            "record an AVPBooter.vmapple2.bin extracted from the decrypted "
            "macOS OS APFS; the file is copied nowhere and is never modified"
        ),
    )
    parser.add_argument(
        "--avpbooter-research",
        type=Path,
        help=(
            "record the optional AVPBooter.vresearch1.bin extracted from the "
            "same macOS OS APFS"
        ),
    )
    args = parser.parse_args()

    if args.derive_restore_ramdisk_raw:
        args.include_restore_ramdisk = True
    if args.derive_ibss_img4:
        args.include_apple_ticket = True

    ipsw = args.ipsw.resolve()
    output = args.output.resolve()
    if not ipsw.is_file():
        raise SystemExit(f"missing IPSW: {ipsw}")
    host_inputs = []
    for label, value in (
        ("AVPBooter.vmapple2.bin", args.avpbooter),
        ("AVPBooter.vresearch1.bin", args.avpbooter_research),
    ):
        if value is None:
            continue
        host_path = value.resolve()
        if not host_path.is_file():
            raise SystemExit(f"missing host firmware: {host_path}")
        host_inputs.append({
            "kind": label,
            "path": str(host_path),
            "bytes": host_path.stat().st_size,
            "sha256": sha256_file(host_path),
            "source": "decrypted macOS 27 OS APFS extracted from the supplied IPSW",
            "opaque": True,
            "mutated": False,
        })
    output.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ipsw) as zf:
        names = zf.namelist()
        build_manifest = manifest_name(names)
        with zf.open(build_manifest) as source:
            manifest = plistlib.load(source)
        identities = manifest.get("BuildIdentities", [])
        if not identities:
            raise SystemExit("BuildManifest.plist has no BuildIdentities")
        selected = select_identity(
            identities, args.device, include_restore_ramdisk=args.include_restore_ramdisk
        )
        score, identity_text = identity_score(selected, args.device)
        if score < 80:
            raise SystemExit(
                f"no M1/J274 BuildIdentity selected; best score={score} text={identity_text}"
            )

        loader_identity = None
        if args.include_restore_loaders:
            loader_identity = select_restore_loader_identity(identities, args.device, selected)

        install_target_paths = []
        if args.inventory_install_targets:
            install_target_paths = manifest_install_target_paths(selected)

        selected_paths = [
            (path, {**metadata, "identity_role": "macos"})
            for path, metadata in manifest_paths(
                selected,
                include_restore_ramdisk=args.include_restore_ramdisk,
                include_restore_trust_cache=args.include_restore_trust_cache,
                include_restore_logo=args.include_restore_logo,
            )
        ]
        if loader_identity is not None:
            if args.include_restore_loaders:
                selected_paths.extend(
                    (path, {**metadata, "identity_role": "restore-loader"})
                    for path, metadata in manifest_paths(
                        loader_identity,
                        include_restore_loaders=True,
                        include_restore_ramdisk=args.include_restore_ramdisk,
                        include_restore_trust_cache=args.include_restore_trust_cache,
                        include_restore_logo=args.include_restore_logo,
                    )
                    if metadata.get("component", "").lower() in {
                        "llb", "ibss", "ibec", "restoreramdisk", "restoretrustcache", "restorelogo"
                    }
                )
            if args.include_restore_ramdisk and not any(
                metadata.get("component") == "RestoreRamDisk"
                for _, metadata in selected_paths
            ):
                selected_paths.extend(
                    (path, {**metadata, "identity_role": "restore-loader"})
                    for path, metadata in manifest_paths(
                        loader_identity,
                        include_restore_ramdisk=True,
                        include_restore_trust_cache=args.include_restore_trust_cache,
                        include_restore_logo=args.include_restore_logo,
                    )
                    if metadata.get("component") in {"RestoreRamDisk", "RestoreTrustCache", "RestoreLogo"}
                )
        # A macOS identity and its matching restore-loader identity can point
        # at the same signed member (notably RestoreLogo).  Extract one
        # immutable copy while retaining the first, more direct role record.
        unique_paths = []
        seen_paths = set()
        for path, metadata in selected_paths:
            if path in seen_paths:
                continue
            seen_paths.add(path)
            unique_paths.append((path, metadata))
        selected_paths = unique_paths
        available = set(names)
        missing = [path for path, _ in selected_paths if path not in available]
        missing.extend(
            path for path, _ in install_target_paths if path not in available
        )
        if missing:
            raise SystemExit("manifest paths missing from IPSW: " + ", ".join(missing))

        install_target_inventory = [
            zip_member_metadata(zf, path, metadata)
            for path, metadata in install_target_paths
        ]
        extracted = []
        derived = []
        apple_manifests = []
        derived_keys: set[str] = set()
        for index, (path, metadata) in enumerate(selected_paths):
            safe_name = path.replace("/", "_")
            destination = output / f"{index:02d}-{safe_name}"
            record = read_member(zf, path, destination)
            component = metadata.pop("component")
            identity_role = metadata.pop("identity_role")
            record["component"] = component
            record["identity_role"] = identity_role
            record["apple_info"] = metadata
            extracted.append(record)

            if args.derive_boot_payloads and component in {
                "LLB", "iBEC", "iBSS", "iBoot", "iBootData", "DeviceTree", "KernelCache"
            } and component not in derived_keys:
                kind, compressed_payload = im4p_payload(destination.read_bytes())
                raw_destination = output / f"{component}.payload.raw"
                raw_destination.write_bytes(decompress_bvx2(compressed_payload))
                derived.append({
                    "kind": f"{component}-payload",
                    "im4p_type": kind,
                    "source_path": str(destination),
                    "source_ipsw_path": path,
                    "path": str(raw_destination),
                    "bytes": raw_destination.stat().st_size,
                    "sha256": sha256_file(raw_destination),
                    "signed": False,
                    "payload_preserved": True,
                    "transformation": "IM4P BVX2/LZFSE payload extraction; no decryption or resigning",
                })
                derived_keys.add(component)

            if args.derive_restore_ramdisk_raw and component == "RestoreRamDisk":
                kind, payload = im4p_payload(destination.read_bytes())
                if kind != "rdsk":
                    raise SystemExit(
                        f"RestoreRamDisk has unexpected IM4P type {kind!r}; refusing derivative"
                    )
                raw_destination = output / "RestoreRamDisk.payload.raw"
                raw_destination.write_bytes(payload)
                derived.append({
                    "kind": "RestoreRamDisk-payload",
                    "source_path": str(destination),
                    "source_ipsw_path": path,
                    "path": str(raw_destination),
                    "bytes": raw_destination.stat().st_size,
                    "sha256": sha256_file(raw_destination),
                    "signed": False,
                    "payload_preserved": True,
                    "transformation": "IM4P payload extraction; no decryption or resigning",
                    })

        ticket_record = None
        if args.include_apple_ticket:
            device_class = str(_identity_info(selected).get("DeviceClass") or args.device)
            ticket_member = _ticket_member(names, device_class)
            ticket_destination = output / f"apticket.{device_class}.im4m"
            ticket_record = read_member(zf, ticket_member, ticket_destination)
            _der_magic(ticket_destination.read_bytes(), b"IM4M")
            ticket_record.update({
                "kind": "AppleRestoreTicket",
                "format": "IM4M",
                "device_class": device_class,
                "identity_role": "macos-ticket",
                "opaque": True,
                "mutated": False,
            })
            apple_manifests.append(ticket_record)

        if args.derive_ibss_img4:
            if ticket_record is None:
                raise SystemExit("iBSS IMG4 derivation requires an Apple IM4M ticket")
            ibss_record = next(
                (
                    item for item in extracted
                    if item.get("component", "").lower() == "ibss"
                    and item.get("identity_role") == "restore-loader"
                ),
                None,
            )
            if ibss_record is None:
                raise SystemExit("iBSS IMG4 derivation requires a signed restore-loader iBSS")
            ibss_path = Path(ibss_record["path"])
            ibss_bytes = ibss_path.read_bytes()
            ticket_path = Path(ticket_record["path"])
            ticket_bytes = ticket_path.read_bytes()
            img4 = wrap_img4(ibss_bytes, ticket_bytes)
            img4_destination = output / f"iBSS.{args.device}.RELEASE.img4"
            img4_destination.write_bytes(img4)
            derived.append({
                "kind": "iBSS-IMG4",
                "path": str(img4_destination),
                "bytes": len(img4),
                "sha256": sha256_file(img4_destination),
                "source_path": str(ibss_path),
                "source_ipsw_path": ibss_record["ipsw_path"],
                "source_sha256": ibss_record["sha256"],
                "ticket_path": str(ticket_path),
                "ticket_sha256": ticket_record["sha256"],
                "signed": False,
                "opaque_signed_components": True,
                "payload_preserved": True,
                "signature_reissued": False,
                "guest_acceptance_verified": False,
                "transformation": "IMG4 envelope around unchanged IM4P and IM4M; no resigning",
            })
            dfu = img4 + dfu_suffix(img4)
            dfu_destination = output / f"iBSS.{args.device}.RELEASE.img4.dfu"
            dfu_destination.write_bytes(dfu)
            derived.append({
                "kind": "iBSS-IMG4-DFU",
                "path": str(dfu_destination),
                "bytes": len(dfu),
                "sha256": sha256_file(dfu_destination),
                "source_path": str(img4_destination),
                "source_sha256": sha256_file(img4_destination),
                "dfu_suffix_bytes": len(dfu) - len(img4),
                "dfu_suffix_hex": dfu_suffix(img4).hex(),
                "signed": False,
                "opaque_signed_components": True,
                "payload_preserved": True,
                "signature_reissued": False,
                "guest_acceptance_verified": False,
                "transformation": "standard DFU suffix appended to IMG4 derivative",
            })

        manifest_record = read_member(zf, build_manifest, output / "BuildManifest.plist")

    receipt = {
        "schema": "26x86.macos27-signed-inputs/1",
        "source": {
            "path": str(ipsw),
            "bytes": ipsw.stat().st_size,
        "sha256": args.source_sha256 or sha256_file(ipsw),
        },
        "build_manifest": manifest_record,
        "host_inputs": host_inputs,
        "apple_manifests": apple_manifests,
        "install_target_inventory": install_target_inventory,
        "selection": {
            "requested_device": args.device,
            "score": score,
            "device_class": selected.get("Info", {}).get("DeviceClass"),
            "board_config": selected.get("Info", {}).get("BoardConfig"),
            "variant": selected.get("Info", {}).get("Variant"),
            "build_version": selected.get("Info", {}).get("BuildVersion"),
            "product_version": selected.get("Info", {}).get("ProductVersion"),
            "install_target_roles": [
                item["role"] for item in install_target_inventory
            ],
            "loader_identity": (
                _identity_summary(loader_identity)
                if args.include_restore_loaders and loader_identity is not None
                else None
            ),
            "restore_ramdisk_identity": (
                _identity_summary(loader_identity)
                if args.include_restore_ramdisk and loader_identity is not None
                else None
            ),
        },
        "signed_inputs": extracted,
        "derived_inputs": derived,
        "policy": {
            "payloads_are_opaque": True,
            "decrypted": False,
            "resigned": False,
            "input_mutated": False,
            "ready_for_handoff_validation": True,
            "ready_for_guest_execution": False,
            "derived_payloads_present": bool(derived),
            "restore_loaders_present": bool(
                args.include_restore_loaders and loader_identity is not None
            ),
            "host_firmware_present": bool(host_inputs),
            "apple_ticket_present": bool(apple_manifests),
            "ibss_img4_derivatives_present": bool(args.derive_ibss_img4),
            "install_target_inventory_enabled": args.inventory_install_targets,
            "install_target_members_extracted": False,
        },
    }
    receipt_path = output / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, plistlib.InvalidFileException, zipfile.BadZipFile) as exc:
        print(f"prepare_macos27_inputs: {exc}", file=sys.stderr)
        raise SystemExit(1)
