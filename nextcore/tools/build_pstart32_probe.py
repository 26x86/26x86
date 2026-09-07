#!/usr/bin/env python3
"""Build an independently authored IA-32 probe in a thin x86_64 Mach-O container.

The linked entry is intentionally 32-bit code for the explicitly selected
pstart32 test ABI. The x86_64 container alone does not establish execution mode.
No Apple code or assets are read. Output is a fresh directory, never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

MARKER = b"NEXTCORE_AUTHORED_PSTART32_PROBE_V1"
VA_BASE = 0xFFFFFF8000000000
ENTRY_PA = 0x101000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def segment(name: bytes, vmaddr: int, vmsize: int, fileoff: int, filesize: int, prot: int) -> bytes:
    return struct.pack("<II16sQQQQIIII", 0x19, 72, name, vmaddr, vmsize, fileoff, filesize, prot, prot, 0, 0)


def build_probe(output: Path, assembler: str = "as", linker: str = "ld") -> dict:
    source = Path(__file__).with_name("pstart32_probe.S").resolve(strict=True)
    assembler = shutil.which(assembler) or assembler
    linker = shutil.which(linker) or linker
    source_before = sha256(source)
    versions = {
        name: subprocess.run([tool, "--version"], check=True, capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
        for name, tool in (("assembler", assembler), ("linker", linker))
    }
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    obj, binary = output / "probe.o", output / "probe.bin"
    commands = [
        [assembler, "--32", "-o", str(obj), str(source)],
        [linker, "-m", "elf_i386", "-Ttext", hex(ENTRY_PA), "-e", "_start", "--oformat", "binary", "-o", str(binary), str(obj)],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    code = binary.read_bytes()
    if not code or len(code) > 4096 or code.count(MARKER) != 1:
        raise ValueError("authored probe must fit one page and contain exactly one identity marker")
    # LC_UNIXTHREAD: one x86_THREAD_STATE64 (21 u64 registers), RIP at index 16.
    thread = bytearray(struct.pack("<IIII", 5, 184, 4, 42) + bytes(168))
    struct.pack_into("<Q", thread, 144, VA_BASE + ENTRY_PA)
    commands_blob = b"".join([
        segment(b"__HIB", VA_BASE + 0x100000, 0x2000, 0, 0x2000, 5),
        segment(b"__DATA", VA_BASE + 0x300000, 0x2000, 0x2000, 0x1000, 3),
        bytes(thread),
    ])
    header = struct.pack("<IIIIIIII", 0xFEEDFACF, 0x01000007, 3, 2, 3, len(commands_blob), 1, 0)
    image = bytearray(0x3000)
    image[:len(header + commands_blob)] = header + commands_blob
    image[0x1000:0x1000 + len(code)] = code
    image[0x2000:0x3000] = bytes((index * 17 + 3) & 255 for index in range(4096))
    macho = output / "probe.macho"
    macho.write_bytes(image)
    if sha256(source) != source_before:
        raise RuntimeError("probe source changed during assembly")
    receipt = {
        "schema": "nextcore.authored-pstart32-fixture.v1",
        "source": str(source), "source_sha256": source_before,
        "image": str(macho), "image_sha256": sha256(macho),
        "object_sha256": sha256(obj), "code_sha256": sha256(binary),
        "code_bytes": len(code), "image_bytes": len(image),
        "entry_physical": ENTRY_PA, "entry_virtual": VA_BASE + ENTRY_PA,
        "identity": MARKER.decode(), "commands": commands, "versions": versions,
        "apple_assets_used": False, "xnu_executed": False,
    }
    (output / "fixture.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assembler", default="as")
    parser.add_argument("--linker", default="ld")
    args = parser.parse_args()
    print(json.dumps(build_probe(args.output, args.assembler, args.linker), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
