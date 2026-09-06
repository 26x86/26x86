#!/usr/bin/env python3
"""Freestanding root-policy objects plus ASan/UBSan UNIT execution. No EFI image."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
REQUIRED_SOURCES = {"vf_boot.c", "vf_dmar.c", "vf_policy.c", "vf_bundle.c", "vf_elf.c", "vf_runtime.c", "vf_efi.c"}
REQUIRED_TESTS = {"test_boot.c", "test_dmar.c", "test_policy.c", "test_cpu.c", "test_bundle.c", "test_elf.c", "test_efi.c"}
CRYPTO_SOURCES = ("monocypher/monocypher.c", "monocypher/monocypher-ed25519.c",
                  "bearssl/sha2small.c", "bearssl/dec32be.c", "bearssl/enc32be.c")


def run(args):
    return subprocess.check_output([str(a) for a in args], text=True,
                                   stderr=subprocess.STDOUT, timeout=120)


def input_hashes():
    inputs = [Path(__file__).resolve(), *(ROOT / "include").glob("*.h"),
              *(ROOT / "src").glob("*.c"), *(ROOT / "tests").glob("*.c"),
              *(p for p in (ROOT / "crypto").rglob("*") if p.is_file())]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(inputs)}


def crypto_sources():
    receipt = json.loads((ROOT / 'crypto/UPSTREAM.json').read_text())
    for name, details in receipt['files'].items():
        path = ROOT / 'crypto' / name
        if path.resolve().is_relative_to((ROOT / 'crypto').resolve()) is False:
            raise RuntimeError('Crypto provenance path escapes source directory')
        if hashlib.sha256(path.read_bytes()).hexdigest() != details['sha256']:
            raise RuntimeError('Crypto upstream file hash changed: ' + name)
    result = [ROOT / 'crypto' / name for name in CRYPTO_SOURCES]
    if not all(path.is_file() for path in result):
        raise RuntimeError('Required pinned crypto source is missing')
    return result


def main():
    BUILD.mkdir(exist_ok=True)
    report_path = BUILD / "report.json"
    # Never leave an earlier passing receipt for a failed new build.
    report_path.write_text(json.dumps({"passed": False, "boot_authorized": False}) + "\n")
    sources = sorted((ROOT / "src").glob("*.c"))
    test_sources = sorted((ROOT / "tests").glob("test_*.c"))
    if not REQUIRED_SOURCES.issubset({path.name for path in sources}):
        raise RuntimeError("Required VSK policy/boot/DMAR source is missing")
    if not REQUIRED_TESTS.issubset({path.name for path in test_sources}):
        raise RuntimeError("Required VSK policy/boot/DMAR test suite is missing")
    sources += crypto_sources()
    before_hashes = input_hashes()
    flags = ["-std=c17", "-Wall", "-Wextra", "-Werror", "-I", ROOT / "include"]
    objects = []
    for source in sources:
        obj = BUILD / (source.stem + ".o")
        run(["clang", *flags, "-O2", "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
             "-mno-red-zone", "-mgeneral-regs-only", "-mno-avx", "-mno-avx2", "-c", source, "-o", obj])
        # Omit wrapped raw-byte lines: otherwise a trailing hexadecimal 'ff'
        # can be mistaken for an FPU mnemonic by a text scanner.
        disassembly = run(["objdump", "-d", "--no-show-raw-insn", obj])
        if re.search(r"%(?:xmm|ymm|zmm|mm)[0-9]+|%st(?:\(|\b)", disassembly):
            raise RuntimeError(f"SIMD/FPU instructions in root object {source.name}")
        # Also reject implicit FPU/SIMD state instructions with no register
        # operand (e.g. fninit or vzeroupper), missed by a register-only scan.
        mnemonics = re.findall(r"^\s*[0-9a-f]+:\s+([a-z][a-z0-9]*)\b", disassembly, re.M)
        if any(name.startswith("f") or name in {"emms", "vzeroupper", "vzeroall"} for name in mnemonics):
            raise RuntimeError(f"Implicit SIMD/FPU instructions in root object {source.name}")
        (BUILD / (source.stem + ".disassembly.txt")).write_text(disassembly)
        objects.append(obj)
    # Resolve cross-module helpers and check no libc/allocator calls leak into root.
    combined = BUILD / "vsk-policy.o"
    run(["ld", "-r", *objects, "-o", combined])
    unresolved = run(["nm", "-u", combined]).strip()
    if unresolved:
        raise RuntimeError("Unresolved freestanding dependencies: " + unresolved)
    # Compile sanitizer objects once; relink each suite against the same inputs.
    # This avoids rebuilding the crypto implementations for every test binary.
    sanitized = []
    for source in sources:
        obj = BUILD / (source.stem + '.asan.o')
        run(["clang", *flags, "-O1", "-g", "-fno-omit-frame-pointer",
             "-fsanitize=address,undefined", "-fno-builtin", "-c", source, "-o", obj])
        sanitized.append(obj)
    tests = []
    for test in test_sources:
        exe = BUILD / test.stem
        run(["clang", *flags, "-O1", "-g", "-fno-omit-frame-pointer",
             "-fsanitize=address,undefined", *sanitized, test, "-o", exe])
        output = run([exe])
        (BUILD / (test.stem + ".log")).write_text(output)
        result = json.loads(output)
        if result.get("passed") is not True:
            raise RuntimeError(f"Test failed: {test.name}")
        tests.append(result)
    if input_hashes() != before_hashes:
        raise RuntimeError("VSK build inputs changed while compiling/testing; receipt rejected")
    report = {
        "schema": "26x86.vsk-unit/1", "spec": "VF-SPEC-001/0.1", "passed": True,
        "validation_level": "UNIT", "boot_authorized": False, "hardware_verified": False,
        "macos_boot_verified": False, "efi_image_built": False,
        "root_general_registers_only": True, "undefined_symbols": [],
        "sanitizers": ["address", "undefined"], "tests": tests,
        "compiler": run(["clang", "--version"]).splitlines()[0],
        "source_sha256": before_hashes,
        "root_policy_object_bytes": combined.stat().st_size,
        "root_policy_object_sha256": hashlib.sha256(combined.read_bytes()).hexdigest(),
        "note": "Relocatable policy object size is not a linked kernel or resident-memory measurement.",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
