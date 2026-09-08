#!/usr/bin/env python3
"""Authored GPT/APFS -> NXAPFS OVMF gate; no original Apple input required."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import socket
import struct
import sys
import threading
import time
import uuid
import zlib

import verify_hal_ovmf as bounded

BLOCK = 4096
PARTITION_BYTES = 1024 * 1024
MAX_FILE = 64 * 1024 * 1024
MAX_SERIAL = 2 * 1024 * 1024
CASES = ("inspect", "start-driver", "app-reject", "nx-checksum", "jsdr-checksum", "multiple", "filesystems-no-binding")
APFS_GUID = uuid.UUID("7c3457ef-0000-11aa-aa11-00306543ecac")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checksum(block):
    """Independent weighted-sum form, rather than the Rust running recurrence."""
    words = struct.unpack(f"<{(len(block) - 8) // 4}I", block[8:])
    modulus = 0xFFFFFFFF
    first = sum(words) % modulus
    second = sum((len(words) - i) * word for i, word in enumerate(words)) % modulus
    low = modulus - (first + second) % modulus
    high = modulus - (first + low) % modulus
    return low | high << 32


def seal(block):
    struct.pack_into("<Q", block, 0, checksum(block))


def authored_driver(application):
    require(4096 < len(application) < PARTITION_BYTES // 2, "authored child size outside fixture bounds")
    require(application[:2] == b"MZ", "authored child must be PE")
    pe = struct.unpack_from("<I", application, 0x3C)[0]
    require(pe + 94 <= len(application), "PE optional header truncated")
    require(application[pe:pe + 4] == b"PE\0\0", "PE signature")
    require(struct.unpack_from("<H", application, pe + 4)[0] == 0x8664, "AMD64 fixture required")
    require(struct.unpack_from("<H", application, pe + 24)[0] == 0x20B, "PE32+ fixture required")
    offset = pe + 24 + 68
    require(struct.unpack_from("<H", application, offset)[0] == 10, "fixture source must be EFI application")
    copy = bytearray(application)
    struct.pack_into("<H", copy, offset, 11)
    changes = [{"offset": i, "before": a, "after": b}
               for i, (a, b) in enumerate(zip(application, copy)) if a != b]
    require(changes == [{"offset": offset, "before": 10, "after": 11}], "unexpected PE changes")
    return bytes(copy), changes


def apfs_partition(payload, corrupt=None):
    require(BLOCK < len(payload) < PARTITION_BYTES // 2, "payload size")
    image = bytearray(PARTITION_BYTES)
    nx = bytearray(BLOCK)
    struct.pack_into("<QQII", nx, 8, 1, 1, 1, 0)
    struct.pack_into("<IIQ", nx, 32, 0x4253584E, BLOCK, PARTITION_BYTES // BLOCK)
    struct.pack_into("<Q", nx, 64, 2)
    nx[72:88] = uuid.UUID("b3abda5e-78bf-408c-972d-58067f8e6d02").bytes
    struct.pack_into("<q", nx, 1272, 1)
    seal(nx)
    jsdr = bytearray(BLOCK)
    struct.pack_into("<QQII", jsdr, 8, 1, 1, 0x40000014, 0)
    struct.pack_into("<IIII", jsdr, 32, 0x5244534A, 1, len(payload), 2)
    second_count = (len(payload) - BLOCK + BLOCK - 1) // BLOCK
    struct.pack_into("<qQqQ", jsdr, 176, 3, 1, 7, second_count)
    seal(jsdr)
    if corrupt == "nx-checksum":
        nx[1000] ^= 1
    if corrupt == "jsdr-checksum":
        jsdr[1000] ^= 1
    image[:BLOCK] = nx
    image[BLOCK:2 * BLOCK] = jsdr
    image[3 * BLOCK:4 * BLOCK] = payload[:BLOCK]
    image[7 * BLOCK:(7 + second_count) * BLOCK] = b"\xA5" * (second_count * BLOCK)
    image[7 * BLOCK:7 * BLOCK + len(payload) - BLOCK] = payload[BLOCK:]
    return bytes(image)


def gpt_disk(partition, count=1, esp=None):
    require(len(partition) == PARTITION_BYTES and count in (1, 2), "fixture geometry")
    require(esp is None or len(esp) == 32 * 1024 * 1024, "ESP fixture size")
    sectors = 81920 if esp is not None else 16384
    image = bytearray(sectors * 512)
    image[446 + 4] = 0xEE
    struct.pack_into("<II", image, 446 + 8, 1, sectors - 1)
    image[510:512] = b"\x55\xAA"
    entries = bytearray(128 * 128)
    if esp is not None:
        entries[:16] = uuid.UUID("c12a7328-f81f-11d2-ba4b-00a0c93ec93b").bytes_le
        entries[16:32] = uuid.UUID(int=99).bytes_le
        struct.pack_into("<QQQ", entries, 32, 2048, 67583, 0)
        image[2048 * 512:67584 * 512] = esp
    for index in range(count):
        start = (69632 if esp is not None else 2048) + index * 4096
        offset = (index + (esp is not None)) * 128
        entries[offset:offset + 16] = APFS_GUID.bytes_le
        entries[offset + 16:offset + 32] = uuid.UUID(int=index + 100).bytes_le
        struct.pack_into("<QQQ", entries, offset + 32, start, start + 2047, 0)
        name = f"NextCore authored {index}".encode("utf-16le")
        entries[offset + 56:offset + 56 + len(name)] = name
        image[start * 512:(start + 2048) * 512] = partition
    entry_crc = zlib.crc32(entries)
    for current, backup, array_lba in ((1, sectors - 1, 2), (sectors - 1, 1, sectors - 33)):
        header = bytearray(512)
        struct.pack_into("<8sIIIIQQQQ16sQIII", header, 0, b"EFI PART", 0x10000, 92, 0, 0,
                         current, backup, 34, sectors - 34, uuid.UUID(int=42).bytes_le,
                         array_lba, 128, 128, entry_crc)
        struct.pack_into("<I", header, 16, zlib.crc32(header[:92]))
        image[current * 512:(current + 1) * 512] = header
        image[array_lba * 512:array_lba * 512 + len(entries)] = entries
    return bytes(image)


def expected_markers(case, size):
    status = {"inspect": "SUCCESS", "start-driver": "NOT_FOUND", "app-reject": "UNSUPPORTED",
              "nx-checksum": "VOLUME_CORRUPTED", "jsdr-checksum": "VOLUME_CORRUPTED",
              "multiple": "NO_MAPPING", "filesystems-no-binding": "NOT_FOUND"}[case]
    markers = ["NXAPFS: EFI_ENTRY"]
    if case in ("inspect", "start-driver", "app-reject", "filesystems-no-binding"):
        markers.append(f"NXAPFS: EXTRACT_OK bytes={size} block_size=4096 extents=2 readback=true")
    if case == "inspect":
        markers.append("NXAPFS: INSPECT_ONLY driver_started=false")
    elif case in ("start-driver", "filesystems-no-binding"):
        markers += ["NXAPFS: DRIVER_START", "NXTEST: EFI_ENTRY", "NXTEST: OPTIONS_EMPTY",
                    "NXAPFS: DRIVER_RETURN status=SUCCESS", "NXAPFS: DRIVER_RESIDENT",
                    "NXAPFS: CONNECT status=NOT_FOUND"]
    elif case == "app-reject":
        markers.append("NXAPFS: NOT_BOOT_DRIVER cleanup=SUCCESS")
    elif case in ("nx-checksum", "jsdr-checksum"):
        jumpstart = "true" if case == "jsdr-checksum" else "false"
        markers.append(f"NXAPFS: EXTRACT_ERROR reason=BadChecksum {{ jumpstart: {jumpstart} }}")
    markers.append(f"NXAPFS: RESULT status={status}")
    return markers, status


def validate_serial(raw, case, size):
    require(len(raw) <= MAX_SERIAL, "serial exceeds cap")
    lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw.decode("utf-8", "strict")).splitlines()
    markers, status = expected_markers(case, size)
    actual = [line for line in lines if line.startswith(("NXAPFS:", "NXTEST:"))]
    require(actual == markers, f"unexpected child marker sequence: {actual!r}")
    parent = ["NEXTCORE: EFI_ENTRY", "NEXTCORE: CONFIG_PARSED", "NEXTCORE: IMAGE_LOAD_BEGIN",
              "NEXTCORE: IMAGE_START", f"NEXTCORE: IMAGE_RETURN status={status}"]
    positions = []
    for marker in parent:
        require(lines.count(marker) == 1, f"missing/duplicated parent marker {marker}")
        positions.append(lines.index(marker))
    require(positions == sorted(positions), "parent marker order")
    require(positions[3] < lines.index(markers[0]) < lines.index(markers[-1]) < positions[4],
            "child markers outside parent call")
    require(not any("NEXTCORE: IMAGE_CLEANUP_ERROR" in line for line in lines), "parent cleanup failure")
    return {"markers": actual, "parent_markers": parent, "expected_status": status,
            "driver_entered": case in ("start-driver", "filesystems-no-binding"), "filesystem_connected": False}


def validate_execution(receipt, qmp):
    require(receipt.get("natural_returncode") == 0, "QEMU did not naturally exit zero")
    require(receipt.get("cleanup_complete") is True, "QEMU cleanup incomplete")
    require(receipt.get("stopped_by_harness") is False, "QEMU required forced stop")
    require(receipt.get("timed_out") is False, "QEMU timed out")
    require(receipt.get("process_group_remaining") is False and not receipt.get("adopted_children_remaining"),
            "QEMU descendants remain")
    require(receipt.get("returncode") == 0, "QEMU final return code differs")
    require(qmp.get("quit_acknowledged") is True and not qmp.get("error"), "QMP quit not acknowledged")


def post_hashes(paths, before, deadline, report):
    """Never allow a late read failure to suppress the caller's atomic receipt."""
    after, failures = {}, {}
    for name, path in paths.items():
        try:
            after[name] = bounded.sha256(path, deadline)
        except Exception as error:
            failures[name] = f"{type(error).__name__}: {error}"
    report["hashes_after"] = after
    report["post_hash_errors"] = failures
    report["originals_unchanged"] = not failures and after == before


def limits():
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE, MAX_FILE))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def command(cmd, out, label, deadline, receipts):
    attempted = {"command": [str(arg) for arg in cmd], "label": label}
    receipts.append(attempted)
    result = bounded.run_bounded([str(arg) for arg in cmd], out / f"{label}.stdout",
                                 out / f"{label}.stderr", deadline)
    attempted.update(result)
    require(result["natural_returncode"] == 0 and result["cleanup_complete"]
            and not result["stopped_by_harness"], f"command failed: {label}")


def qmp_finish(path, serial, terminal, deadline, stop, receipt):
    try:
        while not path.exists():
            require(time.monotonic() < deadline and not stop.is_set(), "QMP socket did not appear")
            stop.wait(0.03)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1)
            client.connect(str(path))
            stream = client.makefile("rwb", buffering=0)
            def message():
                raw = stream.readline(65537)
                require(0 < len(raw) <= 65536, "QMP EOF/oversize")
                return json.loads(raw)
            require("QMP" in message(), "QMP greeting missing")
            def execute(name):
                stream.write(json.dumps({"execute": name, "id": name}).encode() + b"\n")
                while time.monotonic() < deadline:
                    item = message()
                    receipt.setdefault("responses", []).append(item)
                    if item.get("id") == name:
                        require("return" in item and "error" not in item, f"QMP rejected {name}")
                        return
                raise TimeoutError("QMP response deadline")
            execute("qmp_capabilities")
            while time.monotonic() < deadline and not stop.is_set():
                raw = bounded.read_bounded(serial, MAX_SERIAL) if serial.exists() else b""
                complete = any(line.startswith(terminal) and re.fullmatch(
                    rb"NEXTCORE: IMAGE_RETURN status=[A-Z_]+\r?", line)
                    for line in raw.split(b"\n")[:-1])
                if complete:
                    execute("quit")
                    receipt["quit_acknowledged"] = True
                    return
                stop.wait(0.03)
            raise TimeoutError("parent completion marker deadline")
    except Exception as error:
        receipt["error"] = f"{type(error).__name__}: {error}"


def run_case(args, case, inputs, application, driver, output):
    output.mkdir()
    start = time.monotonic()
    # Preparation has its own short budget; guest execution/cleanup is <=30 s.
    deadline = start + 25
    report = {"case": case, "passed": False, "commands": [], "qmp": {},
              "hardware_tested": False, "apfs_mounted": False, "macos_booted": False, "metal_verified": False}
    paths = dict(inputs)
    before = {}
    try:
        payload = application if case == "app-reject" else driver
        fixture = output / "authored-gpt-apfs.raw"
        esp = output / "esp.img"
        with esp.open("wb") as stream:
            stream.truncate(32 * 1024 * 1024)
        command([args.mkfs, "-F", "16", esp], output, "mkfs", deadline, report["commands"])
        command([args.mmd, "-i", esp, "::/EFI", "::/EFI/BOOT", "::/EFI/OC"], output, "mmd", deadline, report["commands"])
        config = output / "config.plist"
        config.write_bytes(plistlib.dumps({"Misc": {"Boot": {"ShowPicker": False}, "Entries": [
            {"Enabled": True, "Name": "NextCore APFS probe", "Path": "\\EFI\\OC\\NXAPFS.efi",
             "Arguments": "--inspect-filesystems" if case == "filesystems-no-binding" else
                          "--start-driver" if case in ("start-driver", "app-reject") else ""}]}}))
        expected_files = {"BOOTX64": (inputs["efi"], "::/EFI/BOOT/BOOTX64.efi"),
                          "NXAPFS": (inputs["probe"], "::/EFI/OC/NXAPFS.efi"),
                          "config": (config, "::/EFI/OC/config.plist")}
        for name, (source, target) in expected_files.items():
            command([args.mcopy, "-i", esp, source, target], output, f"copy-{name}", deadline, report["commands"])
        paths["esp"] = esp
        paths["config"] = config
        fixture.write_bytes(gpt_disk(apfs_partition(payload, case), 2 if case == "multiple" else 1,
                                     bounded.read_bounded(esp, MAX_FILE)))
        paths["fixture"] = fixture
        overlays = {}
        for name, base in (("disk", fixture),):
            overlay = output / f"{name}.qcow2"
            command([args.qemu_img, "create", "-f", "qcow2", "-F", "raw", "-b", base, overlay],
                    output, f"overlay-{name}", deadline, report["commands"])
            overlays[name] = overlay
        variables = output / "vars.fd"
        shutil.copyfile(inputs["ovmf_vars"], variables)
        report["fresh_vars_initial_sha256"] = bounded.sha256(variables, deadline)
        require(report["fresh_vars_initial_sha256"] == bounded.sha256(inputs["ovmf_vars"], deadline), "vars copy mismatch")
        before = {key: bounded.sha256(path, deadline) for key, path in paths.items()}
        report["hashes_before"] = before
        qmp = output / "qmp.sock"
        require(len(str(qmp).encode()) < 104, "output path too long for QMP socket")
        serial = output / "serial.log"
        cmd = [str(inputs["qemu"]), "-machine", "q35,accel=tcg", "-cpu", "qemu64", "-m", "512",
               "-smp", "1", "-display", "none", "-monitor", "none", "-no-reboot", "-net", "none",
               "-drive", f"if=pflash,format=raw,readonly=on,file={inputs['ovmf_code']}",
               "-drive", f"if=pflash,format=raw,file={variables}",
               "-drive", f"if=none,id=disk,format=qcow2,file={overlays['disk']}",
               "-device", "ide-hd,drive=disk,bus=ide.0,bootindex=1", "-serial", f"file:{serial}",
               "-qmp", f"unix:{qmp},server=on,wait=off"]
        report["command"] = cmd
        bounded.atomic_json(output / "command.json", cmd)
        guest_deadline = time.monotonic() + args.timeout
        _, status = expected_markers(case, len(payload))
        stop = threading.Event()
        worker = threading.Thread(target=qmp_finish, args=(qmp, serial,
            b"NEXTCORE: IMAGE_RETURN status=", guest_deadline - 3, stop, report["qmp"]))
        worker.start()
        try:
            report["execution"] = bounded.run_bounded(cmd, output / "qemu.stdout", output / "qemu.stderr", guest_deadline)
        finally:
            stop.set()
            worker.join(1.2)
            require(not worker.is_alive(), "QMP worker cleanup incomplete")
        validate_execution(report["execution"], report["qmp"])
        report["serial_validation"] = validate_serial(bounded.read_bounded(serial, MAX_SERIAL), case, len(payload))
        readback_deadline = time.monotonic() + 10
        # Read the actual guest-visible ESP, including any COW writes.
        guest_disk = output / "guest-disk.raw"
        command([args.qemu_img, "convert", "-f", "qcow2", "-O", "raw", overlays["disk"], guest_disk],
                output, "guest-esp", readback_deadline, report["commands"])
        report["guest_disk_sha256"] = bounded.sha256(guest_disk, readback_deadline)
        require(report["guest_disk_sha256"] == before["fixture"], "guest changed authored disk")
        guest_esp = output / "guest-esp.raw"
        with guest_disk.open("rb") as stream:
            stream.seek(2048 * 512)
            guest_esp.write_bytes(stream.read(32 * 1024 * 1024))
        report["esp_readback"] = {}
        for name, (source, target) in expected_files.items():
            readback = output / f"readback-{name}.bin"
            command([args.mcopy, "-i", guest_esp, target, readback], output, f"readback-{name}", readback_deadline, report["commands"])
            value = bounded.sha256(readback, readback_deadline)
            require(value == bounded.sha256(source, readback_deadline), f"ESP {name} readback mismatch")
            report["esp_readback"][name] = value
        report["passed"] = True
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        post_hashes(paths, before, time.monotonic() + 10, report)
        report["passed"] = report["passed"] and report["originals_unchanged"]
        report["output_hashes"] = {}
        receipt_deadline = time.monotonic() + 5
        for name in ("serial.log", "qemu.stdout", "qemu.stderr", "vars.fd", "disk.qcow2"):
            path = output / name
            try:
                if path.exists():
                    report["output_hashes"][name] = bounded.sha256(path, receipt_deadline)
            except Exception as error:
                report.setdefault("output_hash_errors", {})[name] = f"{type(error).__name__}: {error}"
                report["passed"] = False
        report["elapsed_seconds"] = round(time.monotonic() - start, 4)
        bounded.atomic_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("efi", "probe", "child", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-system-x86_64"))
    parser.add_argument("--qemu-img", default="/usr/bin/qemu-img")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--mkfs", default="/usr/sbin/mkfs.vfat")
    parser.add_argument("--mmd", default="/usr/bin/mmd")
    parser.add_argument("--mcopy", default="/usr/bin/mcopy")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--case", choices=CASES, action="append")
    args = parser.parse_args()
    require(sys.platform == "linux", "run under Linux/WSL")
    require(8 <= args.timeout <= 30, "per-guest budget must be 8..30 seconds")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    bounded.enable_subreaper()
    bounded.child_limits = limits
    report = {"passed": False, "cases": [], "argv": sys.argv, "fixture_provenance": "independently authored only"}
    try:
        inputs = {name: getattr(args, name).resolve(strict=True)
                  for name in ("efi", "probe", "child", "ovmf_code", "ovmf_vars", "qemu")}
        for name in ("qemu_img", "mkfs", "mmd", "mcopy"):
            inputs[name] = Path(getattr(args, name)).resolve(strict=True)
        inputs["harness"] = Path(__file__).resolve()
        inputs["process_helper"] = Path(bounded.__file__).resolve()
        application = bounded.read_bounded(inputs["child"], PARTITION_BYTES // 2)
        driver, changes = authored_driver(application)
        (output / "authored-boot-driver.efi").write_bytes(driver)
        report["driver_copy"] = {"original_sha256": digest(application), "copy_sha256": digest(driver), "changes": changes}
        for case in args.case or CASES:
            result = run_case(args, case, inputs, application, driver, output / case)
            report["cases"].append({"case": case, "passed": result["passed"], "report": f"{case}/report.json"})
            print(json.dumps(report["cases"][-1]), flush=True)
        report["passed"] = all(item["passed"] for item in report["cases"])
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        bounded.atomic_json(output / "report.json", report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
