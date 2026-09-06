#!/usr/bin/env python3
"""Create a new GPT/FAT32 regular-file image of the production EFI self-test.

This tool never opens block devices. Requires sgdisk, mkfs.vfat and mtools.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from x86.sandbox import prepare


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inspect_gpt(path: Path) -> dict:
    with path.open("rb") as stream:
        mbr = stream.read(512)
        header = bytearray(stream.read(512))
        if mbr[510:] != b"\x55\xaa" or mbr[450] != 0xEE or header[:8] != b"EFI PART":
            raise ValueError("Missing protective MBR or GPT")
        size, crc = struct.unpack_from("<II", header, 12)
        if not 92 <= size <= 512:
            raise ValueError("Invalid GPT header size")
        struct.pack_into("<I", header, 16, 0)
        if zlib.crc32(header[:size]) != crc:
            raise ValueError("GPT header CRC mismatch")
        table_lba, count, entry_size, table_crc = struct.unpack_from("<QIII", header, 72)
        if count * entry_size > 1024 * 1024 or entry_size < 128:
            raise ValueError("Invalid GPT table bounds")
        stream.seek(table_lba * 512)
        table = stream.read(count * entry_size)
        if zlib.crc32(table) != table_crc:
            raise ValueError("GPT entry CRC mismatch")
        # EFI System Partition GUID in GPT mixed-endian byte representation.
        if table[:16] != bytes.fromhex("28732ac11ff8d211ba4b00a0c93ec93b"):
            raise ValueError("Partition 1 is not an EFI System Partition")
        first, last = struct.unpack_from("<QQ", table, 32)
        if first < 2048 or last < first or (last + 1) * 512 > path.stat().st_size - 33 * 512:
            raise ValueError("ESP exceeds image bounds")
        return {"start_lba": first, "end_lba": last, "sector_size": 512,
                "bytes": (last - first + 1) * 512, "primary_gpt_crc_valid": True}


def build(output: Path, target: int) -> dict:
    output = output.expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Output must be a new directory")
    for tool in ["sgdisk", "mkfs.vfat", "mcopy"]:
        if not shutil.which(tool):
            raise RuntimeError(f"Required tool missing: {tool}")
    # No arbitrary image/device destination argument is exposed.
    output.mkdir(parents=True)
    staged = output / "media-files"
    payload = prepare(target, str(staged), root=ROOT)
    image = output / "26x86-sandbox-selftest.img"
    with image.open("xb") as stream:
        stream.truncate(128 * 1024 * 1024)
    subprocess.run(["sgdisk", "--clear", "--new=1:2048:0", "--typecode=1:ef00",
                    "--change-name=1:26x86 Sandbox self-test", str(image)], check=True, capture_output=True)
    partition = inspect_gpt(image)
    with tempfile.TemporaryDirectory(prefix="26x86-fat-") as tmp:
        fat = Path(tmp) / "esp.fat"
        with fat.open("xb") as stream:
            stream.truncate(partition["bytes"])
        subprocess.run(["mkfs.vfat", "-F", "32", "-S", "512", "-s", "1", "-n", "26X86TEST", str(fat)],
                       check=True, capture_output=True)
        subprocess.run(["mcopy", "-s", "-i", str(fat), *[str(p) for p in sorted(staged.iterdir())], "::/"], check=True)
        readback = Path(tmp) / "BOOTX64.EFI"
        subprocess.run(["mcopy", "-i", str(fat), "::/EFI/BOOT/BOOTX64.EFI", str(readback)], check=True)
        if digest(readback) != payload["sha256"]:
            raise ValueError("FAT filesystem EFI readback hash mismatch")
        with image.open("r+b") as dest, fat.open("rb") as source:
            dest.seek(partition["start_lba"] * 512)
            shutil.copyfileobj(source, dest, 1024 * 1024)
            dest.flush()
            os.fsync(dest.fileno())
        # Verify through the final partition offset, not just the intermediate FAT file.
        readback.unlink()
        subprocess.run(["mcopy", "-i", f"{image}@@{partition['start_lba'] * 512}",
                        "::/EFI/BOOT/BOOTX64.EFI", str(readback)], check=True)
        if digest(readback) != payload["sha256"]:
            raise ValueError("Final GPT image EFI readback hash mismatch")
    gpt_check = subprocess.run(["sgdisk", "--verify", str(image)], check=True, capture_output=True, text=True)
    if "No problems found" not in gpt_check.stdout:
        raise ValueError("GPT verification did not report success")
    image.chmod(0o444)
    report = {"schema": 1, "artifact_kind": "production-efi-jit-self-test-usb-image",
              "image": image.name, "image_bytes": image.stat().st_size, "image_sha256": digest(image),
              "efi_sha256": payload["sha256"], "partition": partition, "filesystem": "FAT32",
              "fallback_path": "EFI/BOOT/BOOTX64.EFI", "readback_verified": True,
              "physical_devices_accessed": False, "macos_boot_verified": False,
              "production_efi": True, "instrumented_test_efi": False, "target_major": target,
              "gpt_verify": gpt_check.stdout.strip()}
    (output / "media-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "README.txt").write_text(
        "26x86 Apple Silicon Sandbox: native EFI CPU/AIC self-test image.\n"
        "This GPT/FAT32 image contains the production EFI, not the QEMU-instrumented test binary.\n"
        "It does not boot macOS or iBoot. No Apple files are included.\n"
        "File-image verification is separate from physical Mac/USB acceptance.\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory, never a device path")
    parser.add_argument("--target", type=int, choices=[26, 27], default=26)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.target), indent=2))
