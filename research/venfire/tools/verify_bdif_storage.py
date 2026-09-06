#!/usr/bin/env python3
"""Exercise BDIF writes against own COW fixtures; no Apple guest executes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from venfire.artifacts import create_manifest, require_intact
from venfire.storage import prepare_storage
from verify_barrier import check, emulator

DESC, HEADER, DATA, STATUS = 0x70001000, 0x70002000, 0x70003000, 0x70004000
PATTERN = bytes(range(256)) * 2


def _verify(qemu, output, checks):
    with tempfile.TemporaryDirectory(prefix="venfire-bdif-storage-") as temporary:
        root = Path(temporary)
        firmware = root / "own.bin"
        firmware.write_bytes(b"26x86 halted qtest fixture")
        bases = []
        for role in ("aux", "root"):
            path = root / (role + ".raw")
            with path.open("xb") as stream:
                stream.truncate(64 << 20)
            bases.append(path)
        manifest = create_manifest([firmware, *bases])
        session = prepare_storage(aux=bases[0], disk=bases[1], directory=root / "state")

        def record(name, value):
            checks.append({"name": name, "passed": bool(value)})
            check(value, name)

        for run, mode in enumerate(("disabled", "readonly", "enabled", "restart", "flush-error")):
            case = output / mode
            case.mkdir()
            arguments = session.arguments(allow_bdif_writes=mode in ("enabled", "restart", "flush-error"))
            if mode == "readonly":
                arguments += ["-global", "vmapple-bdif.allow-block-writes=on"]
            if mode == "flush-error":
                for i in range(len(arguments) - 1):
                    if arguments[i] == "-blockdev":
                        graph = json.loads(arguments[i + 1])
                        name = graph.pop("node-name")
                        graph = {"driver": "blkdebug", "node-name": name, "image": graph,
                            "inject-error": [{"event": "flush_to_disk", "iotype": "flush",
                                              "errno": 5, "once": False, "immediately": False}]}
                        arguments[i + 1] = json.dumps(graph, separators=(",", ":"))
            command = [qemu, "-M", "vmapple,research-headless=on", "-accel", "tcg",
                "-cpu", "max,pauth=on,pauth-qarma5=on", "-m", "4G", "-smp", "2",
                "-bios", str(firmware), "-S", "-display", "none", "-serial", "none",
                "-monitor", "none", "-nic", "none", "-qtest", "stdio",
                "-qtest-log", "/dev/null", "-trace", "enable=bdif_vblk*", *arguments]
            (case / "command.json").write_text(json.dumps(command, indent=2) + "\n")
            with emulator(command, case, 30) as q:
                def request(device, *, flags=0x10001, sector=1, data_address=DATA, length=512, return_length=1):
                    q.memory_write(HEADER, struct.pack("<IIQ", int(flags == 0x10001), 0, sector))
                    q.memory_write(DATA, PATTERN)
                    q.memory_write(STATUS, b"\xfe")
                    desc = (struct.pack("<QII", HEADER, 16, 1)
                            + struct.pack("<QII", data_address, length, flags)
                            + struct.pack("<QII", STATUS, return_length, 2))
                    q.memory_write(DESC, desc)
                    q.write(0x30000408 + device, DESC, 8)
                    return q.memory_read(STATUS, 1)

                for device, role in ((0, "root"), (0x10000, "aux")):
                    if mode in ("disabled", "readonly"):
                        record(mode + " rejects " + role + " write", request(device) == b"\x01")
                        record(mode + " retains " + role + " data",
                            request(device, flags=0x30001) == b"\x00" and q.memory_read(DATA, 512) == bytes(512))
                    elif mode == "enabled":
                        record(role + " write completes", request(device) == b"\x00")
                        record(role + " guest readback", request(device, flags=0x30001) == b"\x00"
                            and q.memory_read(DATA, 512) == PATTERN)
                    elif mode == "restart":
                        record(role + " persists across restart", request(device, flags=0x30001) == b"\x00"
                            and q.memory_read(DATA, 512) == PATTERN)
                    else:
                        record(role + " flush EIO returns failure", request(device) == b"\x01")
                if mode == "enabled":
                    record("out-of-range write fails", request(0, sector=(64 << 20) // 512) == b"\x01")
                    record("unmapped DMA fails", request(0, data_address=0x5000000000) == b"\x01")
                    record("unknown flags fail", request(0, flags=0x50001) == b"\x01")
                    record("oversized length fails", request(0, length=(128 << 20) + 1) == b"\x01")
                    record("invalid status descriptor is not written", request(0, return_length=0) == b"\xfe")
            require_intact(manifest)
        record("all original base bytes preserved", require_intact(manifest).valid)
    report = {"schema": 1, "passed": all(x["passed"] for x in checks), "checks": checks,
              "backend_sha256": hashlib.sha256(Path(qemu).read_bytes()).hexdigest(),
              "macos_boot_verified": False, "physical_usb_boot_verified": False}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def verify(qemu, output):
    output = Path(output).absolute()
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    try:
        return _verify(qemu, output, checks)
    except BaseException as exc:
        report = {"schema": 1, "passed": False, "checks": checks,
                  "error_type": type(exc).__name__, "error": str(exc)[:4096],
                  "macos_boot_verified": False, "physical_usb_boot_verified": False}
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.qemu, args.output), indent=2))
