#!/usr/bin/env python3
"""Cross-build the authored guest probe; never claim guest runtime success."""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import time
from pathlib import Path

PROFILES = {
    "tahoe-x86_64": {"arch": "x86_64", "major": 26, "cpu": 0x01000007, "subtype": 3},
    "golden-gate-arm64": {"arch": "arm64", "major": 27, "cpu": 0x0100000C, "subtype": 0},
}

STUB = """--- !tapi-tbd
tbd-version: 4
targets: [ {arch}-macos ]
install-name: '/usr/lib/libSystem.B.dylib'
current-version: 1.0.0
compatibility-version: 1.0.0
exports:
  - targets: [ {arch}-macos ]
    symbols: [ _printf, _fflush, _dlopen, _dlsym, _alarm, _usleep ]
...
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect_profile(data, profile):
    """Validate the actual linker output against the requested ABI/OS target."""
    if len(data) < 32:
        raise ValueError("truncated Mach-O header")
    magic, cpu, subtype, kind, ncmds, command_bytes, flags, _ = struct.unpack_from("<8I", data)
    # Require the exact ordinary ABI subtype, including capability bits. An
    # arm64e binary is not evidence for the ordinary arm64 profile.
    if (magic, cpu, subtype, kind) != (0xFEEDFACF, profile["cpu"], profile["subtype"], 2) or not flags & 0x200000:
        raise ValueError("unexpected Mach-O executable profile")
    end = 32 + command_bytes
    if end > len(data) or ncmds > command_bytes // 8:
        raise ValueError("invalid load-command table")
    pos, signature, build_version = 32, None, None
    for _ in range(ncmds):
        if pos + 8 > end:
            raise ValueError("truncated load command")
        cmd, size = struct.unpack_from("<II", data, pos)
        if size < 8 or size % 8 or pos + size > end:
            raise ValueError("invalid load-command range")
        if cmd == 0x1D:
            if size != 16 or signature is not None:
                raise ValueError("invalid or duplicate code-signature command")
            offset, length = struct.unpack_from("<II", data, pos + 8)
            if not length or offset < end or offset + length > len(data):
                raise ValueError("invalid code-signature range")
            signature = {"file_offset": offset, "bytes": length}
        if cmd == 0x32:
            if size < 24 or build_version is not None:
                raise ValueError("invalid or duplicate build-version command")
            platform, minimum, sdk, tools = struct.unpack_from("<4I", data, pos + 8)
            expected = profile["major"] << 16
            if size != 24 + tools * 8 or (platform, minimum, sdk) != (1, expected, expected):
                raise ValueError("unexpected macOS build-version profile")
            build_version = {"platform": platform, "minimum_os": minimum, "sdk": sdk}
        pos += size
    if pos != end or signature is None or build_version is None:
        raise ValueError("missing signature, build version or command boundary")
    return signature, build_version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target", choices=PROFILES, default="tahoe-x86_64")
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--linker", default="/usr/lib/llvm-18/bin/ld64.lld")
    parser.add_argument("--objdump", default="/usr/lib/llvm-18/bin/llvm-objdump")
    args = parser.parse_args()
    profile = PROFILES[args.target]
    arch, major = profile["arch"], profile["major"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().with_name("metal_compute_probe.c")
    stub = output / "libSystem.tbd"
    report = {
        "schema": "nextcore.guest-metal-probe.build.v1",
        "target": args.target, "architecture": arch, "macos_major": major,
        "source_sha256_before": None,
        "commands": [], "guest_executed": False, "guest_metal_verified": False,
    }
    started = time.monotonic()
    try:
        report["source_sha256_before"] = digest(source)
        stub.write_text(STUB.format(arch=arch), encoding="utf-8")
        report["link_stub_sha256"] = digest(stub)
        clang = shutil.which(args.clang)
        linker = shutil.which(args.linker)
        objdump = shutil.which(args.objdump)
        if not all((clang, linker, objdump)):
            raise RuntimeError("Clang, Darwin LLD and llvm-objdump are required")
        obj = output / "nxmetal.o"
        binary = output / "nxmetal"
        commands = [
            ("compile", [clang, "-target", f"{arch}-apple-macos{major}", "-std=c11",
                         "-ffreestanding", "-fno-stack-protector", "-fno-builtin",
                         "-Wall", "-Wextra", "-Werror", "-O2", "-c", str(source), "-o", str(obj)]),
            ("link", [linker, "-arch", arch, "-platform_version", "macos", f"{major}.0", f"{major}.0",
                      "-adhoc_codesign", "-fixup_chains", "-e", "_main", "-o", str(binary), str(obj), str(stub)]),
            ("inspect", [objdump, "--macho", "--private-headers", str(binary)]),
        ]
        for name, command in commands:
            tick = time.monotonic()
            stdout = output / (name + ".stdout.txt")
            stderr = output / (name + ".stderr.txt")
            step = {"name": name, "argv": command, "exit_code": None, "timed_out": False}
            report["commands"].append(step)
            try:
                result = subprocess.run(command, capture_output=True, timeout=45, stdin=subprocess.DEVNULL)
                stdout.write_bytes(result.stdout)
                stderr.write_bytes(result.stderr)
                step["exit_code"] = result.returncode
            except subprocess.TimeoutExpired as error:
                # subprocess.run has killed and reaped its direct child before
                # raising. Keep the attempted command and all partial output.
                step["timed_out"] = True
                stdout.write_bytes(error.stdout or b"")
                stderr.write_bytes(error.stderr or b"")
            finally:
                step["elapsed_seconds"] = time.monotonic() - tick
                if stdout.exists():
                    step["stdout_sha256"] = digest(stdout)
                if stderr.exists():
                    step["stderr_sha256"] = digest(stderr)
            if step["timed_out"] or step["exit_code"] != 0:
                raise RuntimeError(name + " failed; see saved stderr")
        data = binary.read_bytes()
        signature, build_version = inspect_profile(data, profile)
        report.update(
            build_passed=True, macho_profile_verified=True,
            macho_x86_64_pie_verified=arch == "x86_64",
            macho_arm64_pie_verified=arch == "arm64",
            macho_build_version=build_version,
            embedded_code_signature_present=signature,
            binary_sha256=digest(binary), binary_bytes=len(data),
            binary=str(binary),
        )
    except Exception as error:
        report.update(build_passed=False, error=str(error))
    finally:
        try:
            report["source_sha256_after"] = digest(source)
            report["source_unchanged"] = (
                report["source_sha256_before"] is not None
                and report["source_sha256_before"] == report["source_sha256_after"]
            )
        except OSError as error:
            report["source_sha256_after"] = None
            report["source_unchanged"] = False
            report["source_hash_error"] = str(error)
        if not report["source_unchanged"]:
            report["build_passed"] = False
        report["elapsed_seconds"] = time.monotonic() - started
        temporary = output / "build-receipt.json.tmp"
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        temporary.replace(output / "build-receipt.json")
        print(json.dumps(report))
    return 0 if report.get("build_passed") and report["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
