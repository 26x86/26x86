"""Negative evidence mutations and independently authored format checks."""
import json
from pathlib import Path
import struct
import tempfile
import time
import unittest
from unittest.mock import patch
import zlib

import verify_apfs_jumpstart as gate


def application():
    data = bytearray(10001)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<H", data, 132, 0x8664)
    struct.pack_into("<H", data, 152, 0x20B)
    struct.pack_into("<H", data, 220, 10)
    return bytes(data)


def serial(case="inspect"):
    markers, status = gate.expected_markers(case, 10001)
    return ("\n".join(["NEXTCORE: EFI_ENTRY", "NEXTCORE: CONFIG_PARSED",
                         "NEXTCORE: IMAGE_LOAD_BEGIN", "NEXTCORE: IMAGE_START"]
                        + markers + [f"NEXTCORE: IMAGE_RETURN status={status}"]) + "\n").encode()


class FixtureTests(unittest.TestCase):
    def test_driver_changes_only_authored_subsystem(self):
        source = application()
        copy, changes = gate.authored_driver(source)
        self.assertEqual(changes, [{"offset": 220, "before": 10, "after": 11}])
        self.assertEqual(copy[:220] + copy[222:], source[:220] + source[222:])
        with self.assertRaises(ValueError):
            gate.authored_driver(copy)

    def test_discontiguous_exact_payload_and_padding(self):
        payload = bytes((i * 17) % 256 for i in range(10001))
        image = gate.apfs_partition(payload)
        restored = image[3 * 4096:4 * 4096] + image[7 * 4096:7 * 4096 + len(payload) - 4096]
        self.assertEqual(restored, payload)
        self.assertEqual(image[7 * 4096 + len(payload) - 4096], 0xA5)
        self.assertEqual(struct.unpack_from("<q", image, 1272)[0], 1)
        self.assertEqual(struct.unpack_from("<qQqQ", image, 4096 + 176), (3, 1, 7, 2))

    def test_metadata_checksums_and_independent_residue(self):
        image = gate.apfs_partition(application())
        for block in (image[:4096], image[4096:8192]):
            first = second = 0
            words = list(struct.unpack("<1022I", block[8:])) + list(struct.unpack("<2I", block[:8]))
            for word in words:
                first = (first + word) % 0xFFFFFFFF
                second = (second + first) % 0xFFFFFFFF
            self.assertEqual((first, second), (0, 0))
        for case, offset in (("nx-checksum", 0), ("jsdr-checksum", 4096)):
            changed = gate.apfs_partition(application(), case)[offset:offset + 4096]
            self.assertNotEqual(gate.checksum(changed), struct.unpack_from("<Q", changed)[0])

    def test_primary_backup_gpt_crc_and_ambiguity(self):
        disk = gate.gpt_disk(gate.apfs_partition(application()), 2)
        for lba in (1, len(disk) // 512 - 1):
            header = bytearray(disk[lba * 512:lba * 512 + 92])
            expected = struct.unpack_from("<I", header, 16)[0]
            struct.pack_into("<I", header, 16, 0)
            self.assertEqual(zlib.crc32(header), expected)
            entry_lba = struct.unpack_from("<Q", header, 72)[0]
            entries = disk[entry_lba * 512:entry_lba * 512 + 16384]
            self.assertEqual(zlib.crc32(entries), struct.unpack_from("<I", header, 88)[0])
            self.assertEqual(entries[:16], gate.APFS_GUID.bytes_le)
            self.assertEqual(entries[128:144], gate.APFS_GUID.bytes_le)


class GateTests(unittest.TestCase):
    def test_all_expected_outcomes_are_separate(self):
        for case in gate.CASES:
            result = gate.validate_serial(serial(case), case, 10001)
            self.assertEqual(result["driver_entered"], case in ("start-driver", "filesystems-no-binding"))
            self.assertFalse(result["filesystem_connected"])

    def test_marker_duplicates_missing_and_order_rejected(self):
        raw = serial("start-driver")
        mutations = [raw.replace(b"NXTEST: EFI_ENTRY\n", b""),
                     raw.replace(b"NXTEST: EFI_ENTRY\n", b"NXTEST: EFI_ENTRY\n" * 2),
                     raw.replace(b"NXAPFS: DRIVER_START\nNXTEST: EFI_ENTRY", b"NXTEST: EFI_ENTRY\nNXAPFS: DRIVER_START"),
                     raw.replace(b"readback=true", b"readback=false"),
                     raw.replace(b"bytes=10001", b"bytes=9999"),
                     raw.replace(b"NXAPFS: CONNECT status=NOT_FOUND", b"NXAPFS: CONNECT status=SUCCESS")]
        for changed in mutations:
            with self.subTest(changed=changed[-160:]), self.assertRaises(ValueError):
                gate.validate_serial(changed, "start-driver", 10001)

    def test_child_execution_in_default_mode_rejected(self):
        raw = serial().replace(b"NXAPFS: RESULT", b"NXTEST: EFI_ENTRY\nNXAPFS: RESULT")
        with self.assertRaises(ValueError):
            gate.validate_serial(raw, "inspect", 10001)

    def test_unnatural_exit_and_unreaped_children_rejected(self):
        good = {"natural_returncode": 0, "returncode": 0, "cleanup_complete": True,
                "stopped_by_harness": False, "timed_out": False, "process_group_remaining": False,
                "adopted_children_remaining": []}
        qmp = {"quit_acknowledged": True}
        gate.validate_execution(good, qmp)
        for delta in ({"natural_returncode": -25}, {"natural_returncode": None},
                      {"returncode": 1}, {"cleanup_complete": False}, {"stopped_by_harness": True},
                      {"process_group_remaining": True}, {"adopted_children_remaining": [{"pid": 1}]}):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                gate.validate_execution(good | delta, qmp)
        with self.assertRaises(ValueError):
            gate.validate_execution(good, {"quit_acknowledged": False})

    def test_post_hash_failure_still_writes_receipt(self):
        for failure in (TimeoutError("deadline exhausted"), OSError("read failed")):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                report = {"passed": False}
                path = Path(directory) / "report.json"
                with patch.object(gate.bounded, "sha256", side_effect=failure):
                    gate.post_hashes({"efi": Path("efi")}, {"efi": "expected"}, time.monotonic(), report)
                gate.bounded.atomic_json(path, report)
                saved = json.loads(path.read_text())
                self.assertFalse(saved["originals_unchanged"])
                self.assertIn("efi", saved["post_hash_errors"])


if __name__ == "__main__":
    unittest.main()
