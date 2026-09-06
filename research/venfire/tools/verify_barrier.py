#!/usr/bin/env python3
"""Exercise Apple virtio-blk opcode 0x10000 through actual qtest descriptors.

Only locally generated scratch disks are accepted. No guest firmware or guest
code executes. Run on a POSIX host with the pinned, patched aarch64 QEMU build.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from venfire.artifacts import create_manifest, require_intact


APPLE_BARRIER = 0x10000
FLUSH = 4
WRITE = 1
READ = 0
DELAY_NS = 200_000_000
ECAM = 0x3F000000  # Pinned hw/arm/virt.c, highmem=off.
PCI = ECAM + (1 << 15)  # Explicit bus 0, device 1, function 0.
DESC, AVAIL, USED = 0x40010000, 0x40011000, 0x40012000
HEADER, DATA, STATUS = 0x40014000, 0x40015000, 0x40016000
PATTERN = bytes(range(256)) * 2


class VerificationError(RuntimeError):
    pass


def check(condition, message):
    if not condition:
        raise VerificationError(message)


class QTest:
    def __init__(self, process, timeout):
        self.process = process
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout
        self.buffer = b""
        self.commands = 0

    def command(self, command):
        self.process.stdin.write((command + "\n").encode("ascii"))
        self.process.stdin.flush()
        deadline = self.deadline
        self.commands += 1
        while True:
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([self.process.stdout], [], [], max(0, remaining))[0]:
                    raise VerificationError("qtest response timed out: " + command[:100])
                chunk = self.process.stdout.read1(65536)
                if not chunk:
                    raise VerificationError("QEMU closed qtest: " + command[:100])
                self.buffer += chunk
            line, self.buffer = self.buffer.split(b"\n", 1)
            response = line.decode("ascii").strip()
            if response.startswith("IRQ "):
                continue
            check(response == "OK" or response.startswith("OK "), "qtest: " + response)
            return response[2:].strip()

    def read(self, address, size):
        suffix = {1: "b", 2: "w", 4: "l", 8: "q"}[size]
        return int(self.command(f"read{suffix} {address:#x}"), 0)

    def write(self, address, value, size):
        suffix = {1: "b", 2: "w", 4: "l", 8: "q"}[size]
        self.command(f"write{suffix} {address:#x} {value:#x}")

    def memory_write(self, address, data):
        self.command(f"write {address:#x} {len(data)} 0x{data.hex()}")

    def memory_read(self, address, size):
        value = self.command(f"read {address:#x} {size}")
        return bytes.fromhex(value.removeprefix("0x"))


class AppleQueue:
    """Minimal modern PCI split-virtqueue driver, using the published layout."""
    def __init__(self, qtest):
        self.q = qtest
        self.index = 0
        self.pci_id = qtest.read(PCI, 4)
        check(self.pci_id == 0x1A00106B, f"Expected Apple block PCI ID, got {self.pci_id:#x}")
        bars = {}
        next_mmio = 0x10000000
        bar = 0
        while bar < 6:
            address = PCI + 0x10 + bar * 4
            qtest.write(address, 0xFFFFFFFF, 4)
            mask = qtest.read(address, 4)
            if mask == 0:
                bar += 1
                continue
            check(not mask & 1, "Unexpected I/O BAR in modern-only test device")
            is_64 = (mask & 6) == 4
            size = ((~(mask & 0xFFFFFFF0)) & 0xFFFFFFFF) + 1
            check(size and size < 0x01000000, "Unexpected PCI BAR size")
            next_mmio = (next_mmio + size - 1) & ~(size - 1)
            bars[bar] = next_mmio
            qtest.write(address, next_mmio, 4)
            if is_64:
                qtest.write(address + 4, 0, 4)
            next_mmio += size
            bar += 2 if is_64 else 1
        qtest.write(PCI + 4, 6, 2)  # PCI memory decode and bus mastering.
        capabilities = {}
        capability = qtest.read(PCI + 0x34, 1)
        visited = set()
        while capability:
            check(capability not in visited and 0x40 <= capability <= 0xFC,
                  "Invalid PCI capability chain")
            visited.add(capability)
            address = PCI + capability
            if qtest.read(address, 1) == 9:
                kind = qtest.read(address + 3, 1)
                if kind in (1, 2):
                    bar_number = qtest.read(address + 4, 1)
                    check(bar_number in bars, "Virtio capability references unmapped BAR")
                    base = bars[bar_number] + qtest.read(address + 8, 4)
                    capabilities[kind] = (base, qtest.read(address + 16, 4) if kind == 2 else 0)
            capability = qtest.read(address + 1, 1)
        check(1 in capabilities and 2 in capabilities, "Modern virtio capabilities missing")
        self.common = capabilities[1][0]
        self.notify, self.multiplier = capabilities[2]
        c = self.common
        qtest.write(c + 20, 0, 1)
        check(qtest.read(c + 20, 1) == 0, "Device reset failed")
        qtest.write(c + 20, 1, 1)
        qtest.write(c + 20, 3, 1)
        qtest.write(c, 0, 4)
        low = qtest.read(c + 4, 4)
        qtest.write(c, 1, 4)
        high = qtest.read(c + 4, 4)
        check(low & (1 << 9) and high & 1, "FLUSH and VERSION_1 must be offered")
        self.offered_features = low | (high << 32)
        qtest.write(c + 8, 0, 4)
        qtest.write(c + 12, 1 << 9, 4)  # FLUSH; no indirect/event-index/packed rings.
        qtest.write(c + 8, 1, 4)
        qtest.write(c + 12, 1, 4)  # VERSION_1.
        qtest.write(c + 20, 11, 1)
        check(qtest.read(c + 20, 1) & 8, "Feature negotiation failed")
        qtest.write(c + 22, 0, 2)
        check(qtest.read(c + 24, 2) >= 16, "Virtqueue is too small")
        qtest.write(c + 24, 16, 2)
        qtest.write(c + 26, 0xFFFF, 2)
        qtest.command(f"memset {DESC:#x} 0x3000 0")
        for offset, address in ((32, DESC), (40, AVAIL), (48, USED)):
            qtest.write(c + offset, address & 0xFFFFFFFF, 4)
            qtest.write(c + offset + 4, address >> 32, 4)
        self.notify += qtest.read(c + 30, 2) * self.multiplier
        qtest.write(c + 28, 1, 2)
        qtest.write(c + 20, 15, 1)
        check(qtest.read(c + 20, 1) == 15, "Driver start failed")

    def request(self, opcode):
        q = self.q
        q.memory_write(HEADER, struct.pack("<IIQ", opcode, 0, 0))
        q.write(STATUS, 0xFF, 1)
        descriptors = [(HEADER, 16, 1, 1)]
        if opcode in (READ, WRITE):
            q.memory_write(DATA, PATTERN if opcode == WRITE else bytes(512))
            descriptors.append((DATA, 512, 3 if opcode == READ else 1, 2))
        descriptors.append((STATUS, 1, 2, 0))
        q.memory_write(DESC, b"".join(struct.pack("<QIHH", *d) for d in descriptors))
        q.write(AVAIL + 4 + 2 * (self.index % 16), 0, 2)
        self.index += 1
        q.write(AVAIL + 2, self.index, 2)
        started = time.monotonic()
        q.write(self.notify, 0, 2)
        initial_status = q.read(STATUS, 1)
        deadline = q.deadline
        while q.read(USED + 2, 2) != self.index:
            if time.monotonic() >= deadline:
                raise VerificationError(f"Opcode {opcode:#x} did not complete")
            time.sleep(0.001)
        elapsed = time.monotonic() - started
        element = q.memory_read(USED + 4 + 8 * ((self.index - 1) % 16), 8)
        head, length = struct.unpack("<II", element)
        check(head == 0 and length == (513 if opcode == READ else 1),
              f"Invalid used descriptor for opcode {opcode:#x}: {head}, {length}")
        result = {"opcode": f"0x{opcode:x}", "status": q.read(STATUS, 1),
                  "initial_status": initial_status, "completion_seconds": elapsed,
                  "used_index": self.index, "used_length": length}
        if opcode == READ:
            check(q.memory_read(DATA, 512) == PATTERN, "Guest readback differs from written pattern")
        return result


@contextmanager
def emulator(command, directory, timeout):
    log_path = directory / "qemu-stderr.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
        try:
            yield QTest(process, timeout)
        except (OSError, VerificationError) as exc:
            log.flush()
            diagnostic = log_path.read_text(errors="replace")[-4000:]
            raise VerificationError(f"{exc}\nQEMU stderr: {diagnostic}") from exc
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
        check(process.returncode in (0, -signal.SIGTERM),
              f"QEMU exited unexpectedly with status {process.returncode}")


def run_case(qemu, directory, timeout, *, name, opcode, error, delay):
    directory.mkdir()
    disk = directory / "synthetic.raw"
    disk.write_bytes(bytes(1024 * 1024))
    debug = {"driver": "blkdebug", "image": {"driver": "file", "filename": str(disk),
             "cache": {"no-flush": False}}}
    if delay or error:
        debug["inject-error"] = [{"event": "flush_to_disk", "iotype": "flush",
                                  "errno": error, "once": False, "immediately": False,
                                  "delay-ns": DELAY_NS if delay else 0}]
    block = {"driver": "raw", "node-name": "test", "cache": {"no-flush": False}, "file": debug}
    view = ("json:" + json.dumps({"driver": "raw", "file": "test"},
                                 separators=(",", ":"))).replace(",", ",,")
    command = [qemu, "-machine", "virt,highmem=off", "-accel", "qtest", "-m", "64M",
               "-display", "none", "-nodefaults", "-monitor", "none", "-serial", "none",
               "-qtest", "stdio", "-qtest-log", "/dev/null",
               "-blockdev", json.dumps(block, separators=(",", ":")),
               "-drive", "if=none,id=testdisk,cache=writeback,werror=report,file=" + view,
               "-device", "vmapple-virtio-blk-pci,variant=root,drive=testdisk,addr=1,"
                          "num-queues=1,disable-legacy=on"]
    with emulator(command, directory, timeout) as q:
        queue = AppleQueue(q)
        written = queue.request(WRITE)
        check(written["status"] == 0, f"{name}: initial write failed")
        flushed = queue.request(opcode)
        check(flushed["status"] == (1 if error else 0), f"{name}: wrong flush status: {flushed}")
        if delay:
            check(flushed["completion_seconds"] >= DELAY_NS / 1e9 * 0.9,
                  f"{name}: request completed before delayed flush could finish")
        read = queue.request(READ)
        check(read["status"] == 0, f"{name}: read failed")
        unsupported = queue.request(0x20000)
        check(unsupported["status"] == 2, f"{name}: unsupported opcode was not rejected")
        check(q.read(USED + 2, 2) == 4, f"{name}: duplicate or missing completion")
        result = {"name": name, "passed": True, "pci_id": f"0x{queue.pci_id:08x}",
                  "offered_features": f"0x{queue.offered_features:x}",
                  "injected_flush_errno": error, "injected_delay_ns": DELAY_NS if delay else 0,
                  "requests": [written, flushed, read, unsupported], "qtest_commands": q.commands}
    data = disk.read_bytes()
    check(data[:512] == PATTERN and data[512:] == bytes(len(data) - 512),
          f"{name}: synthetic disk contents changed unexpectedly")
    result["synthetic_disk_sha256"] = hashlib.sha256(data).hexdigest()
    return result


def verify(qemu, timeout=10.0):
    check(sys.platform != "win32", "Run this qtest verifier on Linux/WSL or another POSIX host")
    check(math.isfinite(timeout) and 1 <= timeout <= 30, "timeout must be between 1 and 30 seconds")
    executable = shutil.which(qemu)
    check(executable is not None, "QEMU executable was not found")
    manifest = create_manifest([executable])
    executable = manifest.artifacts[0].path
    result = {"schema_version": 1, "layer": "QEMU PCI virtio-blk device model",
              "apple_opcode": "0x10000", "synthetic_disks_only": True,
              "guest_code_executed": False, "qemu": manifest.to_dict(), "cases": []}
    try:
        with tempfile.TemporaryDirectory(prefix="venfire-barrier-") as temp:
            root = Path(temp)
            cases = [("apple_flush", APPLE_BARRIER, 0, False),
                     ("apple_delayed_flush", APPLE_BARRIER, 0, True),
                     ("apple_flush_eio", APPLE_BARRIER, 5, True),
                     ("standard_flush_control", FLUSH, 0, True),
                     ("standard_flush_eio_control", FLUSH, 5, True)]
            for name, opcode, error, delay in cases:
                require_intact(manifest)
                result["cases"].append(run_case(executable, root / name, timeout,
                                                name=name, opcode=opcode, error=error, delay=delay))
    finally:
        require_intact(manifest)
    result["passed"] = True
    result["not_established"] = ["Apple driver ABI interoperability", "full or multiqueue ordering fence",
                                 "host power-loss persistence", "macOS boot"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.output.exists():
            raise ValueError("Output must be a new file")
        result = verify(args.qemu, args.timeout)
        content = json.dumps(result, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as output:
                output.write(content)
        print(content, end="")
        return 0
    except (OSError, ValueError, VerificationError, subprocess.SubprocessError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
