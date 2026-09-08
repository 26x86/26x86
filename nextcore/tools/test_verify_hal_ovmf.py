"""Focused protocol and supervisor regressions; no macOS runtime claims."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest

import verify_hal_ovmf as hal


def checksum(data, index):
    data[index] = 0
    data[index] = (-sum(data)) & 255
    return bytes(data)


def sdt(signature, payload=b""):
    data = bytearray(36 + len(payload))
    data[:4] = signature.encode()
    struct.pack_into("<I", data, 4, len(data))
    data[8] = 1
    data[36:] = payload
    return checksum(data, 9)


def fixture():
    addresses = [0x3000, 0x4000, 0x5000, 0x6000]
    rsdp = bytearray(36)
    rsdp[:8] = b"RSD PTR "
    rsdp[15] = 2
    struct.pack_into("<I", rsdp, 20, 36)
    struct.pack_into("<Q", rsdp, 24, 0x2000)
    rsdp[8] = (-sum(rsdp[:20])) & 255
    rsdp = checksum(rsdp, 32)
    root = sdt("XSDT", b"".join(struct.pack("<Q", address) for address in addresses))
    tables = [("RSDP", 0x1000, rsdp), ("XSDT", 0x2000, root)]
    tables.extend((sig, addr, sdt(sig)) for sig, addr in zip(("FACP", "APIC", "HPET", "MCFG"), addresses))
    pci = bytearray(64)
    struct.pack_into("<HH", pci, 0, 0x8086, 0x1234)
    pci[11] = 6
    return tables, bytes(pci)


def wire(tables=None, pci=None):
    defaults = fixture()
    tables = tables or defaults[0]
    pci = pci or defaults[1]
    lines = hal.CHAIN + ["NXHAL: RSDP addr=0x1000 len=36 rev=2 rsdt=0x0 xsdt=0x2000"]
    for index, (signature, address, data) in enumerate(tables):
        lines.append(f"NXHAL: TABLE sig={signature} addr={address:#x} len={len(data)} csum=true")
        lines.extend("NXHAL: DATA " + data[i:i+64].hex() for i in range(0, len(data), 64))
        if index == 1:
            lines.append("NXHAL: XSDT count=4")
    lines += ["NXHAL: PCI b=0 d=0 f=0 vend=0x8086 dev=0x1234 class=0x06 sub=0x00 pif=0x00 rev=0x00",
              "NXHAL: PCIDATA " + pci.hex(), "NXHAL: DONE tables=5 pci=1"]
    return ("\r\n".join(lines) + "\r\n").encode()


def receipt(exit_code=0):
    return dict(cleanup_complete=True, process_group_remaining=False, stopped_by_harness=False,
                timed_out=False, returncode=exit_code, natural_returncode=exit_code)


class ProtocolTests(unittest.TestCase):
    def reject(self, data, reason=None):
        with self.assertRaisesRegex(hal.InvalidEvidence, reason or ".+"):
            hal.parse_serial(data)

    def test_complete_wire_preserves_exact_bytes(self):
        tables, pci = fixture()
        parsed = hal.parse_serial(wire())
        self.assertEqual([r["data"] for r in parsed["tables"]], [t[2] for t in tables])
        self.assertEqual(parsed["pci"][0]["data"], pci)

    def test_bad_hex(self):
        self.reject(wire().replace(b"NXHAL: DATA 52", b"NXHAL: DATA zz", 1), "hex")

    def test_truncated_data(self):
        self.reject(wire().replace(b"NXHAL: DATA 5253442050545220", b"NXHAL: DATA 52534420505452", 1), "chunk")

    def test_missing_chunk(self):
        lines = wire().splitlines()
        del lines[10]
        self.reject(b"\n".join(lines), "truncated")

    def test_done_count_forged(self):
        self.reject(wire().replace(b"DONE tables=5 pci=1", b"DONE tables=6 pci=1"), "count")

    def test_root_count_forged(self):
        self.reject(wire().replace(b"XSDT count=4", b"XSDT count=5"), "count")

    def test_chain_order(self):
        self.reject(wire().replace(b"NEXTCORE: CONFIG_PARSED", b"NEXTCORE: IMAGE_START", 1), "order")

    def test_read_guards_required(self):
        self.reject(wire().replace(b"NXHAL: READ_GUARDS_OK\r\n", b""), "chain")

    def test_no_done(self):
        self.reject(wire().replace(b"NXHAL: DONE tables=5 pci=1\r\n", b""), "missing")

    def test_skip_never_success(self):
        self.reject(wire().replace(b"NXHAL: PCI b=", b"NXHAL: SKIP addr=0x1234 reason=HDR_READ\r\nNXHAL: PCI b="), "skip")

    def test_duplicate_address(self):
        self.reject(wire().replace(b"sig=APIC addr=0x4000", b"sig=APIC addr=0x3000"), "duplicate")

    def test_duplicate_bdf(self):
        data = wire()
        start = data.index(b"NXHAL: PCI b=")
        end = data.index(b"NXHAL: DONE")
        self.reject(data[:end] + data[start:end] + data[end:], "duplicate")

    def test_pointer_mismatch_with_valid_checksum(self):
        tables, pci = fixture()
        root = bytearray(tables[1][2])
        struct.pack_into("<Q", root, 36, 0x7000)
        tables[1] = ("XSDT", 0x2000, checksum(root, 9))
        self.reject(wire(tables, pci), "pointer")

    def test_rsdp_root_mismatch(self):
        self.reject(wire().replace(b"sig=XSDT addr=0x2000", b"sig=XSDT addr=0x2500"), "pointer")

    def test_declared_length_cannot_hide_trailing_bytes(self):
        tables, pci = fixture()
        table = bytearray(tables[2][2])
        struct.pack_into("<I", table, 4, 35)
        tables[2] = ("FACP", 0x3000, checksum(table, 9))
        self.reject(wire(tables, pci), "declared")

    def test_raw_checksum_independently_checked(self):
        self.reject(wire().replace(b"464143502400000001", b"464143502400000002", 1), "checksum")

    def test_pci_metadata_mismatch(self):
        self.reject(wire().replace(b"vend=0x8086", b"vend=0x1234"), "metadata")

    def test_rust_parser_checksum_rejection(self):
        record = hal.parse_serial(wire())["tables"][2]
        with self.assertRaisesRegex(hal.InvalidEvidence, "parser rejected"):
            hal.validate_parser_result(record, receipt(2), "")

    def test_parser_requires_single_json_object(self):
        record = hal.parse_serial(wire())["tables"][0]
        for stdout in ("[]", "{}", '{"valid":true}\n{}', '{"valid":false}'):
            with self.subTest(stdout=stdout), self.assertRaises(hal.InvalidEvidence):
                hal.validate_parser_result(record, receipt(), stdout)

    def test_bridge_cannot_claim_type0_decode(self):
        record = {"kind": "PCI", "header_type": 1}
        with self.assertRaisesRegex(hal.InvalidEvidence, "falsely"):
            hal.validate_parser_result(record, receipt(), '{"valid":true}')
        self.assertFalse(hal.validate_parser_result(record, receipt(1), "", "inspect_firmware: unsupported PCI header layout (only Type 0 is decoded)")["decoded"])

    def test_inspector_wrong_kind_or_checksum_not_success(self):
        record = hal.parse_serial(wire())["tables"][2]
        for result in ({"kind": "PCI", "length": 1, "checksum_ok": False},
                       {"kind": "SDT", "length": 36, "checksum_ok": False}):
            with self.subTest(result=result), self.assertRaises(hal.InvalidEvidence):
                hal.validate_parser_result(record, receipt(), json.dumps(result))

    def test_bridge_crash_is_not_unsupported(self):
        record = {"kind": "PCI", "header_type": 1}
        for code in (-11, 2, 127):
            with self.subTest(code=code), self.assertRaises(hal.InvalidEvidence):
                hal.validate_parser_result(record, receipt(code), "")

    def validate_typed(self, signature, body, summary):
        data = sdt(signature, body)
        record = dict(kind="SDT", signature=signature, length=len(data), data=data)
        result = dict(kind="SDT", signature=signature, length=len(data), revision=1, checksum_ok=True, summary=summary)
        return hal.validate_parser_result(record, receipt(), json.dumps(result))

    def test_facp_summary_values_bound_to_raw(self):
        valid = dict(dsdt=0, x_dsdt=0, smi_cmd=0, acpi_enable=0)
        self.assertTrue(self.validate_typed("FACP", bytes(112), valid)["decoded"])
        for summary in ({"anything": True}, dict(valid, dsdt=1), dict(valid, acpi_enable=False)):
            with self.subTest(summary=summary), self.assertRaises(hal.InvalidEvidence):
                self.validate_typed("FACP", bytes(112), summary)

    def test_mcfg_summary_count_bound_to_raw(self):
        self.assertTrue(self.validate_typed("MCFG", bytes(24), {"segment_groups": 1})["decoded"])
        for summary in ({"anything": True}, {"segment_groups": 2}, {"segment_groups": True}):
            with self.subTest(summary=summary), self.assertRaises(hal.InvalidEvidence):
                self.validate_typed("MCFG", bytes(24), summary)

    def test_apic_summary_schema_and_consistent_counts(self):
        valid = dict(lapic=0, ioapic=0, interrupt_override=0, nmi=0, lapic_address_override=0,
                     other=0, total_entries=0, local_apic_address=0, flags=0)
        self.assertTrue(self.validate_typed("APIC", bytes(8), valid)["decoded"])
        for summary in ({"anything": True}, dict(valid, total_entries=1), dict(valid, flags=1), dict(valid, nmi=False)):
            with self.subTest(summary=summary), self.assertRaises(hal.InvalidEvidence):
                self.validate_typed("APIC", bytes(8), summary)

    def test_natural_debug_exit_required(self):
        hal.validate_execution(receipt(67))
        for change in ({"returncode": 0}, {"natural_returncode": None}, {"stopped_by_harness": True},
                       {"timed_out": True}, {"cleanup_complete": False}, {"process_group_remaining": True}):
            value = receipt(67)
            value.update(change)
            with self.subTest(change=change), self.assertRaises(hal.InvalidEvidence):
                hal.validate_execution(value)


@unittest.skipUnless(sys.platform == "linux", "Linux process-group supervision")
class SupervisorTests(unittest.TestCase):
    def setUp(self):
        hal.enable_subreaper()

    def execute(self, script, timeout=1):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            return hal.run_bounded([sys.executable, "-c", script], directory / "out", directory / "err", time.monotonic() + timeout)

    def test_natural_exit_is_not_harness_termination(self):
        result = self.execute("raise SystemExit(67)")
        hal.validate_execution(result)

    def test_timeout_sigterm_ignoring_child_reaped(self):
        result = self.execute("import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)")
        self.assertTrue(result["timed_out"])
        self.assertTrue(result["cleanup_complete"])
        self.assertFalse(result["process_group_remaining"])
        self.assertLess(result["elapsed_seconds"], 1.1)

    def test_leader_exit_does_not_hide_live_descendant(self):
        result = self.execute("import os,time,signal; child=os.fork(); signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60) if child==0 else None; os._exit(67)")
        self.assertTrue(result["stopped_by_harness"])
        self.assertTrue(result["cleanup_complete"])
        self.assertFalse(result["process_group_remaining"])
        with self.assertRaises(hal.InvalidEvidence):
            hal.validate_execution(result)

    def test_setsid_child_term_ignore_is_killed_and_reaped(self):
        result = self.execute("import os,time,signal; child=os.fork(); os.setsid() if child==0 else None; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60) if child==0 else time.sleep(.1); os._exit(67)")
        self.assertTrue(result["stopped_by_harness"])
        self.assertTrue(result["cleanup_complete"])
        self.assertTrue(result["adopted_children"])
        self.assertEqual(result["adopted_children_remaining"], [])
        self.assertLess(result["elapsed_seconds"], 1.1)
        with self.assertRaises(hal.InvalidEvidence):
            hal.validate_execution(result)


if __name__ == "__main__":
    unittest.main()
