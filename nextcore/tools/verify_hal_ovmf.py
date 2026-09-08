#!/usr/bin/env python3
"""Verify fresh BOOTX64 -> NXHAL OVMF bytes using the native Rust HAL inspector.

Linux only for execution (process groups and adopted-child reaping). This proves
OVMF collection and host parsing, never XNU, native hardware, or macOS execution.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import struct
import subprocess
import sys
import time

MAX_LOG = 2 * 1024 * 1024
CHAIN = ["NEXTCORE: EFI_ENTRY", "NEXTCORE: CONFIG_PARSED", "NEXTCORE: IMAGE_START",
         "NXHAL: EFI_ENTRY", "NXHAL: READ_GUARDS_OK"]
REQUIRED_TABLES = {"FACP", "APIC", "HPET", "MCFG"}
FALSE_CLAIMS = dict(xnu_executed=False, userspace_verified=False,
                    macos_boot_verified=False, metal_verified=False,
                    native_hardware_verified=False)


class InvalidEvidence(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)


def remaining(deadline):
    value = deadline - time.monotonic()
    if value <= 0:
        raise TimeoutError("total deadline exhausted")
    return value


def read_bounded(path, maximum=MAX_LOG, deadline=None):
    if deadline is not None:
        remaining(deadline)
    with Path(path).open("rb") as stream:
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, f"file exceeds {maximum} byte cap: {path}")
    if deadline is not None:
        remaining(deadline)
    return data


def sha256(path, deadline=None):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            if deadline is not None:
                remaining(deadline)
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
    os.replace(temporary, path)


def parse_serial(raw):
    """Decode the exact NXHAL wire protocol; reject partial/ambiguous evidence."""
    require(len(raw) <= MAX_LOG, "serial exceeds cap")
    text = raw.decode("utf-8", errors="strict")
    lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).splitlines()
    records, pci, seen_addresses, seen_bdf = [], [], set(), set()
    chain_index, summary, root_count, done, active = 0, None, None, None, None
    stage = "chain"

    def finish():
        nonlocal active
        if active is None:
            return
        require(len(active["data"]) == active["length"], "truncated record")
        active["data"] = bytes(active["data"])
        active = None

    for line in lines:
        if line in CHAIN:
            require(chain_index < len(CHAIN) and line == CHAIN[chain_index], "chain marker order/duplicate")
            chain_index += 1
            if chain_index == len(CHAIN):
                stage = "summary"
            continue
        if line.startswith("NEXTCORE:"):
            require(not any(word in line for word in ("ERROR", "INVALID", "IMAGE_RETURN")), "parent loader failure")
            continue
        if not line.startswith("NXHAL:"):
            continue
        require(chain_index == len(CHAIN), "NXHAL data before chain markers")
        require(done is None, "NXHAL record after DONE")
        if line.startswith(("NXHAL: DATA ", "NXHAL: PCIDATA ")):
            prefix = "NXHAL: PCIDATA " if line.startswith("NXHAL: PCIDATA ") else "NXHAL: DATA "
            require(active is not None and (active["kind"] == "PCI") == ("PCIDATA" in prefix), "orphan or mismatched DATA")
            encoded = line[len(prefix):]
            require(bool(re.fullmatch(r"[0-9a-fA-F]+", encoded)) and len(encoded) % 2 == 0, "invalid hex")
            data = bytes.fromhex(encoded)
            needed = active["length"] - len(active["data"])
            require(len(data) == min(64, needed) and needed > 0, "wrong DATA chunk length")
            active["data"].extend(data)
            continue
        finish()
        match = re.fullmatch(r"NXHAL: RSDP addr=(0x[0-9a-f]+) len=(\d+) rev=(\d+) rsdt=(0x[0-9a-f]+) xsdt=(0x[0-9a-f]+)", line)
        if match:
            require(stage == "summary", "RSDP summary order/duplicate")
            summary = dict(zip(("address", "length", "revision", "rsdt", "xsdt"), (int(v, 0) if v.startswith("0x") else int(v) for v in match.groups())))
            stage = "rsdp"
            continue
        match = re.fullmatch(r"NXHAL: TABLE sig=([A-Za-z0-9_ ]{4}) addr=(0x[0-9a-f]+) len=(\d+) csum=(true|false)", line)
        if match:
            sig, address, length, checksum = match.groups()
            address, length = int(address, 16), int(length)
            require(stage in ("rsdp", "root", "tables"), "TABLE order")
            require((stage != "rsdp" or sig == "RSDP") and (stage != "root" or sig in ("XSDT", "RSDT")), "RSDP/root order")
            require(stage != "tables" or sig not in ("RSDP", "XSDT", "RSDT"), "unexpected second root")
            require(address > 0 and address + length <= 0x100000000 and address not in seen_addresses, "invalid/duplicate table address")
            require((length == 20 or 36 <= length <= 64) if sig == "RSDP" else 36 <= length <= (4096 if sig in ("RSDT", "XSDT") else 16384), "table length cap")
            require(checksum == "true", "collector checksum failure")
            require(len(records) < 34, "table count cap")
            seen_addresses.add(address)
            active = {"kind": "RSDP" if sig == "RSDP" else "SDT", "signature": sig, "address": address, "length": length, "data": bytearray()}
            records.append(active)
            stage = "root" if stage == "rsdp" else "count" if stage == "root" else stage
            continue
        match = re.fullmatch(r"NXHAL: (XSDT|RSDT) count=(\d+)", line)
        if match:
            require(stage == "count" and records[-1]["signature"] == match[1], "root count order/type")
            root_count = int(match[2])
            require(0 < root_count <= 32, "root count cap")
            stage = "tables"
            continue
        match = re.fullmatch(r"NXHAL: PCI b=(\d+) d=(\d+) f=(\d+) vend=(0x[0-9a-f]+) dev=(0x[0-9a-f]+) class=(0x[0-9a-f]+) sub=(0x[0-9a-f]+) pif=(0x[0-9a-f]+) rev=(0x[0-9a-f]+)", line)
        if match:
            require(stage in ("tables", "pci"), "PCI order")
            fields = [int(v, 0) if v.startswith("0x") else int(v) for v in match.groups()]
            bus, device, function = fields[:3]
            bdf = (bus, device, function)
            require(bus == 0 and 0 <= device < 32 and 0 <= function < 8 and bdf not in seen_bdf, "invalid/duplicate BDF")
            require(len(pci) < 256, "PCI count cap")
            seen_bdf.add(bdf)
            active = dict(zip(("bus", "device", "function", "vendor_id", "device_id", "class", "subclass", "prog_if", "revision"), fields))
            active.update(kind="PCI", length=64, data=bytearray())
            pci.append(active)
            stage = "pci"
            continue
        match = re.fullmatch(r"NXHAL: DONE tables=(\d+) pci=(\d+)", line)
        if match:
            require(stage == "pci", "DONE before complete ACPI/PCI dump")
            done = {"tables": int(match[1]), "pci": int(match[2])}
            continue
        raise InvalidEvidence(f"unknown/error/skip NXHAL record: {line[:200]}")
    finish()
    require(done is not None and summary is not None and root_count is not None, "missing DONE/summary/count")
    require(done["tables"] == len(records) - 1 and done["pci"] == len(pci), "DONE count mismatch")
    require(root_count == len(records) - 2, "root record count mismatch")
    rsdp, root = records[:2]
    for record in records:
        data = record["data"]
        require(sum(data) % 256 == 0, "raw checksum mismatch")
        if record["kind"] == "SDT":
            require(data[:4] == record["signature"].encode("ascii"), "raw SDT signature mismatch")
            require(struct.unpack_from("<I", data, 4)[0] == len(data), "declared SDT length mismatch")
    data = rsdp["data"]
    require(data[:8] == b"RSD PTR " and sum(data[:20]) % 256 == 0, "raw RSDP mismatch")
    revision, rsdt = data[15], struct.unpack_from("<I", data, 16)[0]
    require((revision < 2 and len(data) == 20) or (revision >= 2 and len(data) >= 36), "RSDP revision/length mismatch")
    xsdt = struct.unpack_from("<Q", data, 24)[0] if revision >= 2 else 0
    if revision >= 2:
        require(struct.unpack_from("<I", data, 20)[0] == len(data), "declared RSDP length mismatch")
    require(summary == dict(address=rsdp["address"], length=len(data), revision=revision, rsdt=rsdt, xsdt=xsdt), "RSDP metadata mismatch")
    require(root["address"] == (xsdt or rsdt) and root["signature"] == ("XSDT" if xsdt else "RSDT"), "RSDP/root pointer mismatch")
    width = 8 if xsdt else 4
    entries = root["data"][36:]
    require(len(entries) % width == 0 and len(entries) // width == root_count, "root entry width/count mismatch")
    addresses = [int.from_bytes(entries[i:i + width], "little") for i in range(0, len(entries), width)]
    require(addresses == [r["address"] for r in records[2:]], "root child pointer/order mismatch")
    require(REQUIRED_TABLES <= {r["signature"] for r in records}, "required FACP/APIC/HPET/MCFG missing")
    for record in pci:
        d = record["data"]
        expected = [int.from_bytes(d[:2], "little"), int.from_bytes(d[2:4], "little"), d[11], d[10], d[9], d[8]]
        require(expected == [record[k] for k in ("vendor_id", "device_id", "class", "subclass", "prog_if", "revision")], "PCI metadata mismatch")
        require(record["vendor_id"] != 0xffff, "absent PCI function")
        record["header_type"] = d[14] & 0x7f
        require(record["header_type"] in (0, 1, 2), "unknown PCI header type")
    require(any(r["header_type"] == 0 for r in pci), "no Type 0 PCI header")
    return {"tables": records, "pci": pci, "done": done, "chain_markers": CHAIN + [f"NXHAL: DONE tables={done['tables']} pci={done['pci']}"]}


def enable_subreaper():
    require(sys.platform == "linux", "execution requires Linux process groups")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER")


def group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def child_limits():
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_LOG, MAX_LOG))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def process_identity(pid):
    try:
        # starttime (stat field 22) distinguishes a recycled PID.
        stat = read_bounded(Path(f"/proc/{pid}/stat"), 16384).decode()
        return (pid, int(stat[stat.rfind(")") + 2:].split()[19]))
    except FileNotFoundError:
        return None


def direct_children():
    data = read_bounded(Path(f"/proc/self/task/{os.getpid()}/children"), 65536)
    identities = set()
    for raw_pid in data.split():
        identity = process_identity(int(raw_pid))
        if identity is not None:
            identities.add(identity)
    return identities


def run_bounded(command, stdout_path, stderr_path, deadline, limit=None):
    """Reserve cleanup inside the deadline, including orphaned group children."""
    remaining(deadline)
    end = min(deadline, time.monotonic() + limit) if limit else deadline
    cleanup_reserve = min(2.0, max(0.1, (end - time.monotonic()) * 0.25))
    work_end = end - cleanup_reserve
    started = time.monotonic()
    stopped, timed_out, group_remaining, cleanup_complete = False, False, False, False
    returncode = None
    baseline_children = direct_children()
    adopted_children, signalled_children = set(), set()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True, preexec_fn=child_limits)
        try:
            while process.poll() is None:
                if time.monotonic() >= work_end:
                    timed_out = True
                    break
                time.sleep(min(0.02, max(0, work_end - time.monotonic())))
            returncode = process.poll()
        finally:
            # Wait/reap the leader before reaping adopted members of its group.
            if group_exists(process.pid):
                stopped = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            grace_end = min(end - 0.05, time.monotonic() + cleanup_reserve / 3)
            killed = False
            while True:
                process.poll()
                # A grandchild may call setsid() and leave the process group.
                # This sequential harness owns newly adopted direct children;
                # preserve pre-existing children and check each PID's starttime.
                adopted_children.update(identity for identity in direct_children()
                                        if identity not in baseline_children and identity[0] != process.pid)
                for identity in adopted_children:
                    pid, _ = identity
                    if process_identity(pid) != identity:
                        continue
                    if identity not in signalled_children:
                        stopped = True
                        try:
                            os.kill(pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        signalled_children.add(identity)
                    try:
                        os.waitpid(pid, os.WNOHANG)
                    except ChildProcessError:
                        pass
                if process.returncode is not None:
                    while True:
                        try:
                            pid, _ = os.waitpid(-process.pid, os.WNOHANG)
                        except ChildProcessError:
                            break
                        if pid == 0:
                            break
                group_remaining = group_exists(process.pid)
                adopted_remaining = [identity for identity in adopted_children if process_identity(identity[0]) == identity]
                if not group_remaining and not adopted_remaining:
                    cleanup_complete = process.returncode is not None
                    break
                now = time.monotonic()
                if now >= grace_end and not killed:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    killed = True
                if now >= grace_end:
                    for identity in adopted_remaining:
                        if process_identity(identity[0]) == identity:
                            try:
                                os.kill(identity[0], signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                if now >= end:
                    break
                time.sleep(min(0.01, max(0, end - now)))
    return {"command": [str(v) for v in command], "pid": process.pid,
            "returncode": process.returncode, "natural_returncode": returncode,
            "stopped_by_harness": stopped, "timed_out": timed_out,
            "cleanup_complete": cleanup_complete, "process_group_remaining": group_remaining,
            "adopted_children": [{"pid": pid, "starttime": starttime} for pid, starttime in sorted(adopted_children)],
            "adopted_children_remaining": [{"pid": pid, "starttime": starttime} for pid, starttime in adopted_remaining],
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "stdout_path": str(stdout_path), "stderr_path": str(stderr_path)}


def validate_execution(receipt, expected_exit=67):
    require(receipt["cleanup_complete"] and not receipt["process_group_remaining"], "process cleanup incomplete")
    require(not receipt.get("adopted_children_remaining"), "adopted descendant cleanup incomplete")
    require(not receipt["stopped_by_harness"] and not receipt["timed_out"], "harness stopped process")
    require(receipt["returncode"] == expected_exit and receipt["natural_returncode"] == expected_exit, "unnatural/wrong exit")


def validate_parser_result(record, receipt, stdout, stderr=""):
    validate_execution(receipt, receipt["returncode"])
    unsupported = record["kind"] == "PCI" and record["header_type"] in (1, 2)
    if unsupported:
        require(receipt["returncode"] != 0, "bridge/CardBus falsely decoded as Type 0")
        require(receipt["returncode"] == 1 and not stdout.strip() and "unsupported PCI header layout (only Type 0 is decoded)" in stderr,
                "unsupported PCI requires explicit normal CLI rejection")
        return {"decoded": False, "unsupported": True, "reason": f"PCI header type {record['header_type']} is outside PciDevice decode"}
    require(receipt["returncode"] == 0, "Rust HAL parser rejected raw bytes")
    try:
        result = json.loads(stdout)
    except (ValueError, UnicodeDecodeError) as error:
        raise InvalidEvidence("inspector did not return a single JSON object") from error
    require(isinstance(result, dict) and bool(result), "inspector JSON must be a nonempty object")
    require(result.get("decoded", True) is True and result.get("valid", True) is True, "inspector reports invalid/undecoded bytes")
    require(result.get("kind") == record["kind"] and type(result.get("length")) is int and result["length"] == record["length"], "inspector kind/length mismatch")
    data = record["data"]
    if record["kind"] in ("RSDP", "SDT"):
        require(result.get("checksum_ok") is True, "inspector checksum not verified")
        summary = result.get("summary")
        if record["kind"] == "RSDP":
            expected = dict(revision=data[15], rsdt_address=int.from_bytes(data[16:20], "little"),
                            xsdt_address=int.from_bytes(data[24:32], "little") if data[15] >= 2 else 0)
            require(isinstance(summary, dict) and all(type(summary.get(k)) is int and summary[k] == v for k, v in expected.items()), "inspector RSDP pointer mismatch")
        else:
            require(result.get("signature") == record["signature"] and type(result.get("revision")) is int and result["revision"] == data[8], "inspector SDT signature/revision mismatch")
            if record["signature"] in ("XSDT", "RSDT"):
                width = 8 if record["signature"] == "XSDT" else 4
                addresses = [int.from_bytes(data[i:i + width], "little") for i in range(36, len(data), width)]
                require(isinstance(summary, dict) and type(summary.get("entry_count")) is int and summary["entry_count"] == len(addresses)
                        and summary.get("addresses") == addresses and all(type(v) is int for v in summary["addresses"]), "inspector root address mismatch")
            elif record["signature"] in ("FACP", "APIC", "MCFG"):
                require(isinstance(summary, dict) and bool(summary), "inspector typed SDT summary missing")
                if record["signature"] == "FACP":
                    require(len(data) >= 53, "inspector FACP field bounds")
                    expected = {"dsdt": int.from_bytes(data[40:44], "little"),
                                "x_dsdt": int.from_bytes(data[140:148], "little") if len(data) >= 148 else 0,
                                "smi_cmd": int.from_bytes(data[48:52], "little"), "acpi_enable": data[52]}
                    require(all(type(summary.get(k)) is int and summary[k] == v for k, v in expected.items()), "inspector FACP fields mismatch")
                elif record["signature"] == "MCFG":
                    require(len(data) >= 44 and (len(data) - 44) % 16 == 0, "inspector MCFG record bounds")
                    require(type(summary.get("segment_groups")) is int and summary["segment_groups"] == (len(data) - 44) // 16, "inspector MCFG count mismatch")
                else:
                    categories = ("lapic", "ioapic", "interrupt_override", "nmi", "lapic_address_override", "other")
                    keys = categories + ("total_entries", "local_apic_address", "flags")
                    require(len(data) >= 44 and all(type(summary.get(k)) is int and summary[k] >= 0 for k in keys), "inspector APIC summary schema")
                    require(summary["local_apic_address"] == int.from_bytes(data[36:40], "little")
                            and summary["flags"] == int.from_bytes(data[40:44], "little"), "inspector APIC header mismatch")
                    require(summary["total_entries"] == sum(summary[k] for k in categories)
                            and summary["total_entries"] <= (len(data) - 44) // 2, "inspector APIC count mismatch")
            else:
                require(summary is None, "generic SDT must not claim device-specific decoding")
    else:
        expected = {"header_type": data[14] & 0x7f, "vendor_id": int.from_bytes(data[:2], "little"),
                    "device_id": int.from_bytes(data[2:4], "little"), "revision": data[8], "class_code": data[11],
                    "subclass": data[10], "prog_if": data[9], "subsystem_vendor_id": int.from_bytes(data[44:46], "little"),
                    "subsystem_device_id": int.from_bytes(data[46:48], "little")}
        require(all(type(result.get(k)) is int and result[k] == v for k, v in expected.items()), "inspector PCI decoded fields mismatch")
        require(result.get("multifunction") is bool(data[14] & 0x80), "inspector PCI multifunction mismatch")
    return {"decoded": True, "unsupported": False, "result": result}


def inspect_records(parsed, inspector, output, deadline, receipts):
    directory = output / "raw"
    directory.mkdir()
    for index, record in enumerate(parsed["tables"] + parsed["pci"]):
        stem = f"{index:03d}-" + (record.get("signature") or f"PCI-{record['bus']:02x}-{record['device']:02x}-{record['function']}")
        binary = directory / (stem + ".bin")
        binary.write_bytes(record["data"])
        item = {k: v for k, v in record.items() if k != "data"}
        item.update(raw_path=str(binary), raw_sha256=sha256(binary, deadline), decoded=False)
        receipts.append(item)
        command = [str(inspector), record["kind"], str(binary)]
        execution = run_bounded(command, directory / (stem + ".stdout.log"), directory / (stem + ".stderr.log"), deadline, limit=3)
        item["execution"] = execution
        item["stdout"] = read_bounded(execution["stdout_path"], deadline=deadline).decode("utf-8", errors="replace")
        item["stderr"] = read_bounded(execution["stderr_path"], deadline=deadline).decode("utf-8", errors="replace")
        item.update(validate_parser_result(record, execution, item["stdout"], item["stderr"]))


def build_config():
    return plistlib.dumps({"Misc": {"Entries": [{"Enabled": True, "Path": "\\EFI\\NEXTCORE\\NXHAL.EFI", "Arguments": ""}]}}, fmt=plistlib.FMT_XML)


def run(args):
    started = time.monotonic()
    deadline = started + args.timeout
    enable_subreaper()
    output = args.output.resolve()
    require("," not in str(output), "output path cannot contain comma")
    fields = ("efi", "hal", "inspector", "ovmf_code", "ovmf_vars")
    paths = {}
    for field in fields:
        path = getattr(args, field).resolve(strict=True)
        require(path.is_file() and "," not in str(path), f"{field} must be a regular file without comma")
        require(path.stat().st_size <= 256 * 1024 * 1024, f"{field} exceeds input size cap")
        paths[field] = path
    require(not output.exists(), "output must be fresh")
    output.mkdir(parents=True)
    report = {"schema": "nextcore-hal-ovmf-v1", "passed": False, "layer": "OVMF UEFI collection -> host HAL parser",
              "timeout_seconds": args.timeout, "inputs": {}, "copies": {}, "parser_receipts": [], **FALSE_CLAIMS}
    failure = None
    try:
        for field, path in paths.items():
            report["inputs"][field] = {"path": str(path), "sha256_before": sha256(path, deadline)}
        esp = output / "esp"
        for directory in (esp / "EFI/BOOT", esp / "EFI/NEXTCORE", esp / "EFI/OC"):
            directory.mkdir(parents=True)
        destinations = {"efi": esp / "EFI/BOOT/BOOTX64.EFI", "hal": esp / "EFI/NEXTCORE/NXHAL.EFI", "ovmf_vars": output / "vars.fd"}
        for field, destination in destinations.items():
            remaining(deadline)
            shutil.copyfile(paths[field], destination)
            copied_hash = sha256(destination, deadline)
            require(copied_hash == report["inputs"][field]["sha256_before"], f"{field} copy mismatch")
            report["copies"][field] = {"path": str(destination), "sha256_before": copied_hash}
        (esp / "EFI/OC/config.plist").write_bytes(build_config())
        serial = output / "serial.log"
        command = [args.qemu, "-machine", "q35,accel=tcg,smm=off", "-cpu", "Nehalem", "-m", "256", "-smp", "1",
                   "-display", "none", "-monitor", "none", "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
                   "-device", "isa-debug-exit,iobase=0xf4,iosize=0x04",
                   "-drive", f"if=pflash,format=raw,readonly=on,file={paths['ovmf_code']}",
                   "-drive", f"if=pflash,format=raw,file={destinations['ovmf_vars']}",
                   "-drive", f"format=raw,file=fat:rw:{esp}"]
        atomic_json(output / "command.json", command)
        # Leave bounded time for parser calls, integrity checks and report publication.
        qemu_deadline = deadline - min(10.0, remaining(deadline) * 0.25)
        report["qemu"] = run_bounded(command, output / "stdout.log", output / "stderr.log", qemu_deadline)
        validate_execution(report["qemu"])
        raw = read_bounded(serial, deadline=deadline)
        report["serial"] = {"path": str(serial), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        parsed = parse_serial(raw)
        report["dump"] = {"done": parsed["done"], "chain_markers": parsed["chain_markers"], "pointer_graph_verified": True}
        inspect_records(parsed, paths["inspector"], output, deadline - min(2.0, remaining(deadline) * 0.1), report["parser_receipts"])
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        for field, evidence in report["inputs"].items():
            try:
                evidence["sha256_after"] = sha256(paths[field], deadline)
                evidence["unchanged"] = evidence["sha256_after"] == evidence["sha256_before"]
            except Exception as error:
                evidence.update(unchanged=False, error=str(error))
        for field, evidence in report["copies"].items():
            try:
                evidence["sha256_after"] = sha256(evidence["path"], deadline)
                evidence["unchanged"] = evidence["sha256_after"] == evidence["sha256_before"]
            except Exception as error:
                evidence.update(unchanged=False, error=str(error))
        report["inputs_unchanged"] = len(report["inputs"]) == len(fields) and all(v.get("unchanged") for v in report["inputs"].values())
        report["copied_images_unchanged"] = all(report["copies"].get(k, {}).get("unchanged") for k in ("efi", "hal"))
        report["elapsed_seconds"] = round(time.monotonic() - started, 4)
        report["deadline_exceeded"] = time.monotonic() > deadline
        report["failure"] = failure
        report["passed"] = not failure and report["inputs_unchanged"] and report["copied_images_unchanged"] and not report["deadline_exceeded"]
        atomic_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("efi", "hal", "inspector", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if not 0 < args.timeout <= 120:
        parser.error("--timeout must be in (0, 120] seconds including cleanup")
    args.qemu = shutil.which(args.qemu) or args.qemu
    try:
        report = run(args)
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"passed": report["passed"], "failure": report["failure"], "report": str(args.output.resolve() / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
