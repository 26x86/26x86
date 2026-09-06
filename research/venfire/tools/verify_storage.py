#!/usr/bin/env python3
"""Exercise the real VMApple block graph using only freshly authored test bytes."""

import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from venfire.storage import prepare_storage, load_storage


class Monitor:
    def __init__(self, path, process):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(10)
        for _ in range(200):
            try:
                self.socket.connect(str(path))
                break
            except (FileNotFoundError, ConnectionRefusedError):
                if process.poll() is not None:
                    raise RuntimeError("QEMU exited before QMP became available")
                time.sleep(0.05)
        else:
            raise RuntimeError("QMP startup timeout")
        self.stream = self.socket.makefile("rwb", buffering=0)
        greeting = json.loads(self.stream.readline())
        if "QMP" not in greeting:
            raise RuntimeError("Missing QMP greeting")
        self.call("qmp_capabilities")

    def call(self, name, arguments=None):
        request = {"execute": name}
        if arguments is not None:
            request["arguments"] = arguments
        self.stream.write(json.dumps(request).encode() + b"\n")
        while True:
            line = self.stream.readline()
            if not line:
                raise RuntimeError("QMP disconnected")
            response = json.loads(line)
            if "error" in response:
                raise RuntimeError(str(response["error"]))
            if "return" in response:
                return response["return"]

    def io(self, device, command, *, expect_denied=False):
        response = self.call("human-monitor-command", {"command-line": f'qemu-io {device} "{command}"'})
        if expect_denied:
            if not response or "read-only" not in response.lower():
                raise RuntimeError("Read-only pflash unexpectedly allowed a write: " + response)
        elif response:
            raise RuntimeError("qemu-io failed: " + response)

    def close(self):
        self.stream.close()
        self.socket.close()


def verify(qemu, output, qemu_img="qemu-img", qemu_io="qemu-io"):
    output = Path(output).absolute()
    output.mkdir(parents=True, exist_ok=False)
    checks = {}
    with tempfile.TemporaryDirectory(prefix="venfire-storage-") as temporary:
        directory = Path(temporary)
        aux, root = directory / "aux, base.raw", directory / "root, base.raw"
        aux.write_bytes(b"X" * 16384 + b"A" * (1024 * 1024))
        root.write_bytes(b"A" * (1024 * 1024))
        originals = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (aux, root)}
        session = prepare_storage(aux=aux, disk=root, directory=directory / "state",
                                  qemu_img=qemu_img, aux_offset=16384)
        checks["created_two_cow_images"] = True
        for run in range(2):
            if run:
                session = load_storage(directory / "state")
            command = [qemu, "-M", "vmapple,research-headless=on", "-cpu", "max,pauth=on,pauth-qarma5=on",
                       "-accel", "tcg", "-m", "4G", "-bios", str(PROJECT / "guests/vmapple.bin"),
                       "-S", "-display", "none", "-serial", "none", "-monitor", "none", "-nic", "none",
                       "-qmp", f"unix:{directory / 'qmp.sock'},server=on,wait=off", *session.arguments()]
            (output / f"command-{run}.json").write_text(json.dumps(command, indent=2) + "\n")
            with (output / f"qemu-{run}.log").open("xb") as log:
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log)
                monitor = None
                try:
                    monitor = Monitor(directory / "qmp.sock", process)
                    blocks = monitor.call("query-block")
                    (output / f"blocks-{run}.json").write_text(json.dumps(blocks, indent=2) + "\n")
                    devices = {item["device"]: item.get("inserted", {}) for item in blocks}
                    for index, role in enumerate(("aux", "root")):
                        flash, disk = devices[f"pflash{index}"], devices[role + "disk"]
                        if not flash["ro"] or disk["ro"] or flash["children"] != disk["children"]:
                            raise RuntimeError("Boot/runtime views do not share expected COW node and permissions")
                        monitor.io(role + "disk", f"read -P {('0x41' if not run else '0x5a')} 0 512")
                        if not run:
                            monitor.io(role + "disk", "write -P 0x5a 0 512")
                            monitor.io(role + "disk", "flush")
                        monitor.io(f"pflash{index}", "read -P 0x5a 0 512")
                    if not run:
                        monitor.io("pflash1", "write -P 0x22 0 512", expect_denied=True)
                        denied = subprocess.run([qemu_io, "-f", "qcow2", "-c", "write -P 0x22 0 512",
                                                 str(session.directory / "root.qcow2")],
                                                capture_output=True, text=True, timeout=10)
                        (output / "second-writer.log").write_text(denied.stdout + denied.stderr)
                        if denied.returncode == 0 or "lock" not in (denied.stdout + denied.stderr).lower():
                            raise RuntimeError("Concurrent overlay writer was not excluded by file locking")
                        checks["concurrent_writer_rejected"] = True
                        checks["pflash_write_rejected"] = True
                    checks["restart_preserves_guest_writes" if run else "shared_boot_runtime_readback"] = True
                    monitor.call("quit")
                    process.wait(timeout=10)
                    if process.returncode != 0:
                        raise RuntimeError("QEMU shutdown failed")
                finally:
                    if monitor:
                        monitor.close()
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
            (directory / "qmp.sock").unlink(missing_ok=True)
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != digest for path, digest in originals.items()):
            raise RuntimeError("An original base image changed")
        checks["base_bytes_intact"] = True
        report = {"schema": 1, "checks": checks, "passed": all(checks.values()),
                  "macos_boot_verified": False, "guest_filesystem_durability_verified": False,
                  "scope": "Self-authored data, paused VMApple machine and QMP block I/O; no Apple guest runs."}
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--output", required=True)
    options = parser.parse_args()
    print(json.dumps(verify(options.qemu, options.output), indent=2))
