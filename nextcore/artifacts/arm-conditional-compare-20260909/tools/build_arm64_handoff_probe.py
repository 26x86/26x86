#!/usr/bin/env python3
"""Build an authored ARM64 MH_FILESET fixture without reading vendor assets."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

MARKER = b"NEXTCORE_AUTHORED_ARM64_HANDOFF_V1"
PAGE = 16384
VIRTUAL = 0xFFFFFE0002000000
PHYSICAL = 0x42000000
ENTRY_OFFSET = PAGE + 1024

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def segment(name: bytes, offset: int, memory: int, size: int, protection: int) -> bytes:
    return struct.pack("<II16sQQQQIIII", 0x19, 72, name, VIRTUAL + offset, memory, offset, size, protection, protection, 0, 0)

def image(code: bytes, subtype: int = 0) -> bytes:
    thread = bytearray(struct.pack("<IIII", 5, 288, 6, 68) + bytes(272))
    struct.pack_into("<Q", thread, 272, VIRTUAL + ENTRY_OFFSET)
    name = b"fixture.kernel\0"
    member = bytearray(48)
    struct.pack_into("<IIQQII", member, 0, 0x80000035, 48, VIRTUAL + PAGE, PAGE, 32, 0)
    member[32:32 + len(name)] = name
    def header(kind: int, commands: list[bytes]) -> bytes:
        payload = b"".join(commands)
        return struct.pack("<IIIIIIII", 0xFEEDFACF, 0x0100000C, subtype, kind, len(commands), len(payload), 0, 0) + payload
    outer = header(12, [segment(b"__TEXT", 0, PAGE, PAGE, 1), segment(b"__CODE", PAGE, PAGE, PAGE, 5),
                        segment(b"__DATA", 2 * PAGE, PAGE, PAGE // 2, 3), bytes(thread), bytes(member)])
    child = header(2, [segment(b"__TEXT", PAGE, PAGE, PAGE, 5), segment(b"__DATA", 2 * PAGE, PAGE, PAGE // 2, 3)])
    result = bytearray(2 * PAGE + PAGE // 2)
    result[:len(outer)] = outer
    result[PAGE:PAGE + len(child)] = child
    result[ENTRY_OFFSET:ENTRY_OFFSET + len(code)] = code
    result[2 * PAGE:] = bytes((i * 17 + 3) & 255 for i in range(PAGE // 2))
    return bytes(result)

def build_probe(output: Path, clang: str = "clang", linker: str = "ld.lld") -> dict:
    source = Path(__file__).with_name("arm64_handoff_probe.S").resolve(strict=True)
    before = sha256(source)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    clang, linker = shutil.which(clang) or clang, shutil.which(linker) or linker
    obj, binary = output / "probe.o", output / "probe.bin"
    commands = [[clang, "--target=aarch64-none-elf", "-c", str(source), "-o", str(obj)],
                [linker, "-Ttext", hex(PHYSICAL + ENTRY_OFFSET), "-e", "_start", "--oformat=binary", str(obj), "-o", str(binary)]]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    code = binary.read_bytes()
    if not code or len(code) > PAGE - 1024 or code.count(MARKER) != 1:
        raise ValueError("invalid authored payload extent/identity")
    fixture = output / "probe.kc"
    fixture.write_bytes(image(code))
    if sha256(source) != before:
        raise RuntimeError("assembly source changed during build")
    receipt = {"schema": "nextcore.authored-arm64-handoff-fixture.v1", "source_sha256": before,
               "image": str(fixture), "image_sha256": sha256(fixture), "code_sha256": sha256(binary),
               "code_bytes": len(code), "entry_physical": PHYSICAL + ENTRY_OFFSET,
               "commands": commands, "apple_assets_used": False, "xnu_executed": False}
    (output / "fixture.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--linker", default="ld.lld")
    args = parser.parse_args()
    print(json.dumps(build_probe(args.output, args.clang, args.linker), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
