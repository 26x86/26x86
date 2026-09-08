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

STUB = """--- !tapi-tbd
tbd-version: 4
targets: [ x86_64-macos ]
install-name: '/usr/lib/libSystem.B.dylib'
current-version: 1.0.0
compatibility-version: 1.0.0
exports:
  - targets: [ x86_64-macos ]
    symbols: [ _printf, _fflush, _dlopen, _dlsym, _alarm, _usleep ]
...
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--linker", default="/usr/lib/llvm-18/bin/ld64.lld")
    parser.add_argument("--objdump", default="/usr/lib/llvm-18/bin/llvm-objdump")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().with_name("metal_compute_probe.c")
    stub = output / "libSystem.tbd"
    report = {
        "schema": "nextcore.guest-metal-probe.build.v1",
        "source_sha256_before": None,
        "commands": [], "guest_executed": False, "guest_metal_verified": False,
    }
    started = time.monotonic()
    try:
        report["source_sha256_before"] = digest(source)
        stub.write_text(STUB, encoding="utf-8")
        report["link_stub_sha256"] = digest(stub)
        clang = shutil.which(args.clang)
        linker = shutil.which(args.linker)
        objdump = shutil.which(args.objdump)
        if not all((clang, linker, objdump)):
            raise RuntimeError("Clang, Darwin LLD and llvm-objdump are required")
        obj = output / "nxmetal.o"
        binary = output / "nxmetal"
        commands = [
            ("compile", [clang, "-target", "x86_64-apple-macos26", "-std=c11",
                         "-ffreestanding", "-fno-stack-protector", "-fno-builtin",
                         "-Wall", "-Wextra", "-Werror", "-O2", "-c", str(source), "-o", str(obj)]),
            ("link", [linker, "-arch", "x86_64", "-platform_version", "macos", "26.0", "26.0",
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
        magic, cpu, _, kind, ncmds, command_bytes, flags, _ = struct.unpack_from("<8I", data)
        if (magic, cpu, kind) != (0xFEEDFACF, 0x01000007, 2) or not flags & 0x200000:
            raise RuntimeError("unexpected Mach-O executable profile")
        pos = 32
        signature = None
        for _ in range(ncmds):
            cmd, size = struct.unpack_from("<II", data, pos)
            if size < 8 or pos + size > 32 + command_bytes:
                raise RuntimeError("invalid load-command range")
            if cmd == 0x1D:
                offset, length = struct.unpack_from("<II", data, pos + 8)
                if not length or offset + length > len(data):
                    raise RuntimeError("invalid code-signature range")
                signature = {"file_offset": offset, "bytes": length}
            pos += size
        if pos != 32 + command_bytes or signature is None:
            raise RuntimeError("missing signature or command boundary")
        report.update(
            build_passed=True, macho_x86_64_pie_verified=True,
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
