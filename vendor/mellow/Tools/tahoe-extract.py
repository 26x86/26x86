#!/usr/bin/env python3
"""Extract only pinned Tahoe 25G83 ABI inputs from the local BaseSystem image.

No download, installation, mounting, patching, or execution of Apple binaries.
The image hash must match the image already checked by the recovery workflow.
This tool independently checks hashes, not the Apple chunklist signature.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

IMAGE_BYTES = 960530321
IMAGE_SHA256 = "edddd0d5869caaa12e29e6996a04f11590280580976a119dbd42c24fa62fe18e"
PREFIX = "macOS Base System/System/Library/"
FILES = {
    "CoreServices/SystemVersion.plist": (603, "6151cb883e5b48d43a33d4d41956405a1cd502e0c8622319388d943e2cb804a1"),
    "dyld/dyld_shared_cache_x86_64": (760791040, "e5f4c3ff1cd2d985d6c3d370aa34a22034f6f815bcc4a2f0a044093e39e7dceb"),
    "dyld/dyld_shared_cache_x86_64.01": (232357888, "9db68bbe532a4d99babc588767b67ba58942e14c2b74f1082bad857f74e9b377"),
    "Extensions/IOAcceleratorFamily2.kext/Contents/Info.plist": (2391, "a538a844e004051d469d19e76b192b7676cc1953a9e0a8bfd22e930f39abc318"),
    "KernelCollections/BaseSystemKernelExtensions.kc": (22282240, "60d3f43f1a23847aa8b60b7c57153fd93d20d0653c116d14da4875f09e5d2f04"),
    "KernelCollections/BaseSystemKernelExtensions.kc.bundles": (3482, "692c3ae5907e152a653e7841d8476fce45bfb9dae5756ba7df451cf38cc8ff5b"),
    "KernelCollections/BaseSystemKernelExtensions.kc.elides": (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "KernelCollections/BootKernelExtensions.kc": (67584000, "c80161fa3065883753fc285339281361a8469cbb6fb27653c88e2a22eb4807a4"),
    "KernelCollections/BootKernelExtensions.kc.elides": (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pinned(path, size, sha):
    return path.is_file() and path.stat().st_size == size and digest(path) == sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seven-zip", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    image, output, executable = args.image.resolve(), args.output.resolve(), args.seven_zip.resolve()
    if not pinned(image, IMAGE_BYTES, IMAGE_SHA256):
        raise ValueError("Input is not the pinned Tahoe 25G83 recovery image")
    output.mkdir(parents=True, exist_ok=True)
    paths = [(PREFIX + name, size, sha) for name, (size, sha) in FILES.items()]
    missing = []
    for name, size, sha in paths:
        target = output / name
        if not target.resolve().is_relative_to(output):
            raise ValueError("Extraction target resolves outside output directory")
        if target.exists() and not pinned(target, size, sha):
            raise ValueError("Existing extraction differs; choose a fresh output directory: " + name)
        if not target.exists():
            missing.append(name)
    report = {"scope": "pinned input/extraction hashes; no independent signature verification or runtime test",
              "image": str(image), "image_sha256": IMAGE_SHA256,
              "image_bytes": IMAGE_BYTES, "output": str(output), "extracted_now": missing,
              "apple_chunklist_signature_verified_by_this_tool": False}
    if missing:
        result = subprocess.run([str(executable), "x", "-y", "-o" + str(output), str(image), *missing],
                                capture_output=True, text=True, timeout=600)
        report["seven_zip_returncode"] = result.returncode
        report["seven_zip_stdout"] = result.stdout
        report["seven_zip_stderr"] = result.stderr
        # 7-Zip may report the known HFS tail warning. Only exact pinned output
        # hashes may accept warning status; fatal statuses always fail.
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr + result.stdout)
    for name, size, sha in paths:
        if not pinned(output / name, size, sha):
            raise ValueError("Extracted file differs from pinned image contents: " + name)
    report["files"] = [{"path": name, "bytes": size, "sha256": sha} for name, size, sha in paths]
    report["all_pinned_hashes_match"] = True
    report_path = args.report or output.parent / "tahoe-extraction-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"image_hash_matches": True, "verified_files": len(paths),
                      "extracted_now": len(missing), "report": str(report_path)}, indent=2))


if __name__ == "__main__":
    main()
