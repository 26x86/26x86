#!/usr/bin/env python3
"""Compile and actually load/execute ONLY the repository's own tiny ELF fixture."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    report_path = build / "elf-native-report.json"
    report_path.write_text(json.dumps({"passed": False, "boot_authorized": False}) + "\n")
    source = ROOT / "tests/fixtures/elf_core.c"
    linker = ROOT / "tests/fixtures/elf_core.ld"
    inputs = [source, linker, ROOT / "include/vf_elf.h", ROOT / "src/vf_elf.c", ROOT / "tests/test_elf.c", Path(__file__).resolve()]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    commands = [
        ["clang", "-std=c17", "-ffreestanding", "-fno-stack-protector", "-fno-pic", "-fno-pie", "-mgeneral-regs-only",
         "-mno-red-zone", "-O2", "-c", source, "-o", build / "elf-fixture.o"],
        ["ld.lld", "-static", "-nostdlib", "--build-id=none", "-T", linker, build / "elf-fixture.o", "-o", build / "elf-fixture.elf"],
        ["clang", "-std=c17", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
         "-I", ROOT / "include", ROOT / "src/vf_elf.c", ROOT / "tests/test_elf.c", "-o", build / "test_elf_native"],
    ]
    for command in commands:
        subprocess.run([str(x) for x in command], check=True, timeout=60)
    binary_hash = sha(build / "elf-fixture.elf")
    result = json.loads(subprocess.check_output([str(build / "test_elf_native"), str(build / "elf-fixture.elf")], text=True, timeout=30))
    if {str(p.relative_to(ROOT)): sha(p) for p in inputs} != before or sha(build / "elf-fixture.elf") != binary_hash:
        raise RuntimeError("ELF verifier inputs changed while running")
    if not result.get("passed") or not result.get("own_compiled_native_execution"):
        raise RuntimeError("Own-code native execution did not pass")
    report = {**result, "fixture_sha256": binary_hash, "source_sha256": before,
              "entry_return": 42, "placement": "MAP_FIXED_NOREPLACE at own fixture VA 0x20000000",
              "permissions": "RW+NX copy, then separate RX code / RW+NX data / inaccessible gaps",
              "firmware_calls": False, "macos_boot_verified": False,
              "commands": [[str(x) for x in c] for c in commands]}
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
