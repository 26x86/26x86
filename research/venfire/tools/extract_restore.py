#!/usr/bin/env python3
"""Extract original restore components for one identity; never alter guest code.

Only manifest-listed regular ZIP members are copied. ZIP CRC and manifest
digests are checked, and the full source archive is hashed before and after.
No extraction path comes directly from a shell command or archive permission.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import stat
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from venfire.artifacts import create_manifest, read_regular, require_intact, verify_manifest
from venfire.media import _read_build_manifest

MAX_MEMBER = 64 * 1024**3
MAX_TOTAL = 96 * 1024**3
RESERVED_OUTPUTS = {"buildmanifest.plist", "selected-identity.plist", "extraction.json"}


def extract_restore(source, output, *, device_class="vma2macosap",
                    variant="Customer Erase Install (IPSW)", components=None):
    original = create_manifest([source])
    directory = Path(output).absolute()
    # Resolve all parent components through the same no-symlink input policy
    # once a normal fresh directory is created; reject links before writes.
    for parent in (directory, *directory.parents):
        if parent.is_symlink() or (parent.exists() and
                getattr(parent.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Extraction destination cannot traverse links/reparse points")
    report = {"schema": 1, "complete": False, "source": original.to_dict(), "components": [],
              "device_class": device_class, "variant": variant,
              "macos_boot_verified": False, "signature_validity_verified": False}
    with read_regular(source) as stream, zipfile.ZipFile(stream) as archive:
        manifest, _ = _read_build_manifest(archive)
        identities = [item for item in manifest.get("BuildIdentities", [])
                      if item.get("Info", {}).get("DeviceClass") == device_class
                      and item.get("Info", {}).get("Variant") == variant]
        if len(identities) != 1:
            raise ValueError("Exactly one restore identity must match")
        identity = identities[0]
        selected = set(components) if components is not None else set(identity["Manifest"])
        if not selected or not selected.issubset(identity["Manifest"]):
            raise ValueError("Select existing restore identity components")
        entries = {}
        for entry in archive.infolist():
            entries.setdefault(entry.filename, []).append(entry)
        records = {}
        for name in sorted(selected):
            component = identity["Manifest"][name]
            path = component.get("Info", {}).get("Path")
            if not isinstance(path, str) or not path or any(c in path for c in ("\\", ":", "\0")):
                raise ValueError("Component has an unsafe archive path")
            relative = PurePosixPath(path)
            if relative.is_absolute() or ".." in relative.parts or str(relative) != path:
                raise ValueError("Component path is not canonical and relative")
            if relative.parts[0].casefold() in RESERVED_OUTPUTS:
                raise ValueError("Component path conflicts with reserved extraction metadata")
            matches = entries.get(path, [])
            if len(matches) != 1:
                raise ValueError("Missing or duplicate component archive member")
            entry = matches[0]
            mode = entry.external_attr >> 16
            if (entry.is_dir() or (stat.S_IFMT(mode) not in (0, stat.S_IFREG))
                    or entry.flag_bits & 1 or not 0 < entry.file_size <= MAX_MEMBER):
                raise ValueError("Component must be an unencrypted bounded regular file")
            digest = component.get("Digest")
            if not isinstance(digest, bytes) or len(digest) not in (20, 32, 48):
                raise ValueError("Component requires a supported original manifest digest")
            if path in records:
                if records[path]["digest"] != digest:
                    raise ValueError("Aliased component digests disagree")
                records[path]["names"].append(name)
            else:
                records[path] = dict(entry=entry, digest=digest, names=[name])
        if sum(item["entry"].file_size for item in records.values()) > MAX_TOTAL:
            raise ValueError("Aggregate restore extraction exceeds bound")
        directory.mkdir(parents=True, exist_ok=False)
        directory.chmod(0o700)
        try:
            with (directory / "BuildManifest.plist").open("xb") as copied_manifest:
                copied_manifest.write(archive.read("BuildManifest.plist"))
            with (directory / "selected-identity.plist").open("xb") as selected_identity:
                selected_identity.write(plistlib.dumps(identity))
            report.update(version=manifest.get("ProductVersion"), build=manifest.get("ProductBuildVersion"))
            require_intact(original)
            for path, item in records.items():
                target = directory.joinpath(*PurePosixPath(path).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                algorithm = {20: "sha1", 32: "sha256", 48: "sha384"}[len(item["digest"])]
                manifest_hash, sha256 = hashlib.new(algorithm), hashlib.sha256()
                size = 0
                with archive.open(item["entry"]) as member, target.open("xb") as copied:
                    for chunk in iter(lambda: member.read(8 * 1024**2), b""):
                        size += len(chunk)
                        if size > item["entry"].file_size:
                            raise ValueError("ZIP member expanded beyond its declared size")
                        copied.write(chunk)
                        manifest_hash.update(chunk)
                        sha256.update(chunk)
                if size != item["entry"].file_size or manifest_hash.digest() != item["digest"]:
                    raise ValueError("Original component digest mismatch: " + path)
                report["components"].append(dict(names=item["names"], path=path, size=size,
                    sha256=sha256.hexdigest(), manifest_algorithm=algorithm, manifest_digest_matched=True))
            require_intact(original)
            report["complete"] = True
        finally:
            report["input_integrity"] = verify_manifest(original).to_dict()
            if not report["input_integrity"]["valid"]:
                report["complete"] = False
            with (directory / "extraction.json").open("x", encoding="utf-8") as evidence:
                evidence.write(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--device-class", default="vma2macosap")
    parser.add_argument("--variant", default="Customer Erase Install (IPSW)")
    parser.add_argument("--component", action="append")
    args = parser.parse_args()
    report = extract_restore(args.source, args.output, device_class=args.device_class,
                             variant=args.variant, components=args.component)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
