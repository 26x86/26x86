#!/usr/bin/env python3
"""Check experimental unavailable RPC MMIO using generated qtest bytes only.

No guest instructions execute. Accepted doorbells never complete an RPC and
must preserve request/payload bytes. This does not establish Apple RPC fidelity.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from venfire.artifacts import create_manifest, require_intact
from verify_barrier import VerificationError, check, emulator

DOORBELL = 0x4FFFF8
REQUEST, PAYLOAD = 0x70001000, 0x70002000
RAM_END = 0x170000000  # 4 GiB RAM begins at pinned VMApple 0x70000000.


def run_case(qemu, directory, timeout, enabled):
    directory.mkdir()
    firmware = directory / "own-halted-fixture.bin"
    firmware.write_bytes(b"26x86 QTEST\0\0\0")
    disks = []
    for name, size in (("aux", 64 << 20), ("root", 128 << 20)):
        disk = directory / (name + ".raw")
        with disk.open("xb") as stream:
            stream.truncate(size)
        disks.append(disk)
    manifest = create_manifest([firmware, *disks])
    trace = directory / "rpc.trace"
    command = [qemu, "-M", "vmapple,research-headless=on,uuid=0", "-accel",
               "tcg,thread=single", "-cpu", "max,pauth=on,pauth-qarma5=on",
               "-m", "4G", "-smp", "2", "-bios", str(firmware), "-S",
               "-display", "none", "-monitor", "none", "-serial", "none",
               "-nic", "none", "-no-reboot", "-qtest", "stdio",
               "-qtest-log", "/dev/null", "-trace",
               f"enable=vmapple_optional_rpc_*,file={trace}"]
    if enabled:
        command += ["-global", "vmapple-cfg.optional-rpc-unavailable=on"]
    for index, disk in enumerate(disks):
        view = "json:" + json.dumps({"driver": "raw", "read-only": True,
                                     "file": {"driver": "file", "filename": str(disk)}},
                                    separators=(",", ":"))
        command += ["-drive", f"if=pflash,index={index},readonly=on,file=" +
                    view.replace(",", ",,")]
    checks = []

    def record(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        check(condition, name)

    try:
        require_intact(manifest)
        with emulator(command, directory, timeout) as q:
            payload = bytes(range(256))
            request = struct.pack("<IIQQ", 0x10001, 2, PAYLOAD, 0x500000)
            guard = b"\xa5" * 64
            q.memory_write(REQUEST - len(guard), guard + request + guard)
            q.memory_write(PAYLOAD, payload)
            q.write(DOORBELL, REQUEST, 8)
            record("request and adjacent guards unchanged",
                   q.memory_read(REQUEST - len(guard), len(request) + 2 * len(guard)) ==
                   guard + request + guard)
            record("payload unchanged", q.memory_read(PAYLOAD, len(payload)) == payload)
            record("completion remains original zero", q.read(REQUEST + 3, 1) == 0)
            if enabled:
                for name, header, opcode in (("unknown opcode", 0x10001, 3),
                                              ("unknown version", 0x10002, 2),
                                              ("already completed", 0x1010001, 2)):
                    invalid = struct.pack("<IIQQ", header, opcode, PAYLOAD, 0x500000)
                    q.memory_write(REQUEST, invalid)
                    q.write(DOORBELL, REQUEST, 8)
                    record(name + " request preserved", q.memory_read(REQUEST, 24) == invalid)
                q.memory_write(REQUEST, request)
                for name, address in (("MMIO self pointer", DOORBELL),
                                      ("firmware RAM pointer", 0x100000),
                                      ("legacy config RAM pointer", 0x400000),
                                      ("unmapped pointer", 0x600000),
                                      ("overflow pointer", 0xFFFFFFFFFFFFFFF8),
                                      ("partial RAM range", RAM_END - 8)):
                    q.write(DOORBELL, address, 8)
                    record(name + " preserves owned data",
                           q.memory_read(REQUEST, 24) == request and
                           q.memory_read(PAYLOAD, len(payload)) == payload)
                for name, offset, size in (("wrong offset", -8, 8),
                                           ("narrow store", 0, 4),
                                           ("unaligned store", -1, 8)):
                    q.write(DOORBELL + offset, REQUEST, size)
                    record(name + " preserves request", q.memory_read(REQUEST, 24) == request)
                q.read(DOORBELL, 8)
                record("unsupported read preserves request", q.memory_read(REQUEST, 24) == request)
                # Recovery can retry after rejected traffic without queued state.
                q.write(DOORBELL, REQUEST, 8)
                record("retry remains unavailable", q.memory_read(REQUEST, 24) == request)
            commands = q.commands
        lines = trace.read_text(errors="strict").splitlines()
        requests = [line for line in lines if "vmapple_optional_rpc_request " in line]
        rejects = [line for line in lines if "vmapple_optional_rpc_reject " in line]
        if enabled:
            record("five exact bounded request snapshots", len(requests) == 5)
            record("all snapshots explicitly preserve completion",
                   all("completion=unchanged" in line for line in requests))
            for reason in ("unknown-request", "not-ram", "unmapped", "access", "read"):
                record(reason + " rejected in device trace",
                       any("reason=" + reason in line for line in rejects))
        else:
            record("default off invokes no optional RPC callbacks", not requests and not rejects)
        return {"enabled": enabled, "checks": checks, "qtest_commands": commands,
                "request_trace": requests, "rejection_trace": rejects,
                "generated_inputs_unchanged": True}
    finally:
        require_intact(manifest)


def verify(qemu, timeout=15.0):
    check(sys.platform != "win32", "Run this verifier on Linux/WSL")
    check(math.isfinite(timeout) and 1 <= timeout <= 30, "timeout must be 1..30 seconds")
    executable = shutil.which(qemu)
    check(executable is not None, "QEMU executable not found")
    manifest = create_manifest([executable])
    try:
        require_intact(manifest)
        with tempfile.TemporaryDirectory(prefix="venfire-optional-rpc-") as temp:
            cases = [run_case(manifest.artifacts[0].path, Path(temp) / name, timeout, enabled)
                     for name, enabled in (("default-off", False), ("explicit-on", True))]
    finally:
        require_intact(manifest)
    return {"schema_version": 1, "layer": "QEMU optional RPC MMIO and bounded read-only DMA",
            "passed": True, "cases": cases, "guest_code_executed": False,
            "apple_assets_used": False, "request_completed": False,
            "qemu_sha256": manifest.artifacts[0].sha256,
            "not_established": ["Apple exact optional RPC device fidelity",
                                "Apple firmware fallback", "macOS boot"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.output.exists():
            raise ValueError("Output must be a new file")
        result = verify(args.qemu, args.timeout)
        text = json.dumps(result, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
        print(text, end="")
        return 0
    except (OSError, ValueError, VerificationError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
