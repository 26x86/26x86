"""Tests for the original-preserving macOS 27 IPSW input inventory."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
import zipfile
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_macos27_inputs", PROJECT / "Tools" / "prepare_macos27_inputs.py"
)
assert SPEC is not None and SPEC.loader is not None
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


def _der(tag: int, payload: bytes) -> bytes:
    length = len(payload)
    if length < 128:
        encoded = bytes([length])
    else:
        raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
        encoded = bytes([0x80 | len(raw)]) + raw
    return bytes([tag]) + encoded + payload


def _im4p(kind: bytes, payload: bytes) -> bytes:
    return _der(0x30, _der(0x16, b"IM4P") + _der(0x16, kind) + _der(0x16, b"V") + _der(0x04, payload))


class PrepareMacOS27InputsTests(unittest.TestCase):
    def _ipsw(self, directory: Path) -> Path:
        payload = b"APFS" + bytes(range(32))
        ramdisk = _im4p(b"rdsk", payload)
        devicetree = _im4p(b"dtre", b"tree")
        logo = _im4p(b"logo", b"logo")
        manifest = {
            "BuildIdentities": [{
                "Info": {
                    "DeviceClass": "j274ap",
                    "Variant": "Customer Erase Install (IPSW)",
                },
                "Manifest": {
                    "RestoreRamDisk": {"Info": {"Path": "094-ramdisk.dmg"}},
                    "DeviceTree": {"Info": {"Path": "DeviceTree.j274ap.im4p"}},
                    "RestoreLogo": {"Info": {"Path": "applelogo.im4p"}},
                },
            }],
        }
        path = directory / "fixture.ipsw"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("BuildManifest.plist", plistlib.dumps(manifest))
            archive.writestr("094-ramdisk.dmg", ramdisk)
            archive.writestr("DeviceTree.j274ap.im4p", devicetree)
            archive.writestr("applelogo.im4p", logo)
        return path

    def _ipsw_with_install_targets(self, directory: Path) -> Path:
        devicetree = _im4p(b"dtre", b"tree")
        os_image = b"OS AEA placeholder; do not extract"
        system_restore_image = b"SystemRestoreImage AEA placeholder; do not extract"
        manifest = {
            "BuildIdentities": [
                {
                    "Info": {
                        "DeviceClass": "j274ap",
                        "Variant": "Recovery",
                    },
                    "Manifest": {
                        "OS": {"Info": {"Path": "Restore/not-selected.aea"}},
                    },
                },
                {
                    "Info": {
                        "DeviceClass": "j274ap",
                        "BoardConfig": "J274AP",
                        "Variant": "macOS Customer Erase Install (IPSW)",
                        "BuildVersion": "27A1",
                        "ProductVersion": "27.0",
                    },
                    "Manifest": {
                        "OS": {
                            "Info": {
                                "Path": "Restore/UniversalMac_27.0_27A1_OS.aea",
                                "IsEncrypted": True,
                            },
                        },
                        "SystemRestoreImage": {
                            "Info": {
                                "Path": "Restore/SystemRestoreImage_27A1.aea",
                                "IsEncrypted": True,
                            },
                        },
                        "DeviceTree": {
                            "Info": {"Path": "DeviceTree.j274ap.im4p"},
                        },
                    },
                },
            ],
        }
        path = directory / "install-targets.ipsw"
        with zipfile.ZipFile(
            path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr("BuildManifest.plist", plistlib.dumps(manifest))
            archive.writestr("Restore/not-selected.aea", b"not selected")
            archive.writestr("Restore/UniversalMac_27.0_27A1_OS.aea", os_image)
            archive.writestr("Restore/SystemRestoreImage_27A1.aea", system_restore_image)
            archive.writestr("DeviceTree.j274ap.im4p", devicetree)
        return path

    def test_restore_ramdisk_is_opt_in_and_payload_is_recorded_separately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = self._ipsw(root)
            output = root / "prepared"
            original_argv = __import__("sys").argv
            try:
                __import__("sys").argv = [
                    "prepare_macos27_inputs.py", str(ipsw), "--output", str(output),
                    "--include-restore-ramdisk", "--derive-restore-ramdisk-raw",
                ]
                self.assertEqual(PREPARE.main(), 0)
            finally:
                __import__("sys").argv = original_argv
            receipt = __import__("json").loads((output / "receipt.json").read_text())
            self.assertEqual(receipt["selection"]["variant"], "Customer Erase Install (IPSW)")
            self.assertEqual(
                sorted(item["component"] for item in receipt["signed_inputs"]),
                ["DeviceTree", "RestoreRamDisk"],
            )
            derived = receipt["derived_inputs"]
            self.assertEqual(len(derived), 1)
            self.assertEqual(derived[0]["bytes"], 36)
            self.assertEqual(Path(derived[0]["path"]).read_bytes(), b"APFS" + bytes(range(32)))
            self.assertFalse(derived[0]["signed"])

    def test_default_inventory_does_not_copy_restore_ramdisk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = self._ipsw(root)
            output = root / "prepared"
            original_argv = __import__("sys").argv
            try:
                __import__("sys").argv = [
                    "prepare_macos27_inputs.py", str(ipsw), "--output", str(output),
                ]
                self.assertEqual(PREPARE.main(), 0)
            finally:
                __import__("sys").argv = original_argv
            receipt = __import__("json").loads((output / "receipt.json").read_text())
            self.assertEqual([item["component"] for item in receipt["signed_inputs"]], ["DeviceTree"])
            self.assertEqual(receipt["derived_inputs"], [])

    def test_restore_logo_is_opt_in_and_keeps_signed_role_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = self._ipsw(root)
            output = root / "prepared"
            original_argv = __import__("sys").argv
            try:
                __import__("sys").argv = [
                    "prepare_macos27_inputs.py", str(ipsw), "--output", str(output),
                    "--include-restore-logo",
                ]
                self.assertEqual(PREPARE.main(), 0)
            finally:
                __import__("sys").argv = original_argv
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertEqual(
                [item["component"] for item in receipt["signed_inputs"]],
                ["DeviceTree", "RestoreLogo"],
            )
            logo_record = receipt["signed_inputs"][1]
            self.assertEqual(Path(logo_record["path"]).read_bytes(), _im4p(b"logo", b"logo"))
            self.assertTrue(receipt["policy"]["payloads_are_opaque"])

    def test_install_target_inventory_is_metadata_only_and_uses_selected_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = self._ipsw_with_install_targets(root)
            output = root / "prepared"
            original_argv = __import__("sys").argv
            try:
                __import__("sys").argv = [
                    "prepare_macos27_inputs.py", str(ipsw), "--output", str(output),
                    "--inventory-install-targets",
                ]
                with mock.patch.object(
                    PREPARE, "read_member", wraps=PREPARE.read_member
                ) as read_member:
                    self.assertEqual(PREPARE.main(), 0)
            finally:
                __import__("sys").argv = original_argv

            receipt = json.loads((output / "receipt.json").read_text())
            self.assertEqual(
                receipt["selection"]["install_target_roles"],
                ["OS", "SystemRestoreImage"],
            )
            inventory = {
                item["role"]: item
                for item in receipt["install_target_inventory"]
            }
            self.assertEqual(set(inventory), {"OS", "SystemRestoreImage"})
            with zipfile.ZipFile(ipsw) as archive:
                expected = {
                    "OS": archive.getinfo("Restore/UniversalMac_27.0_27A1_OS.aea"),
                    "SystemRestoreImage": archive.getinfo(
                        "Restore/SystemRestoreImage_27A1.aea"
                    ),
                }
            for role, member in expected.items():
                record = inventory[role]
                self.assertEqual(record["manifest_component"], role)
                self.assertEqual(record["ipsw_path"], member.filename)
                self.assertEqual(record["compressed_bytes"], member.compress_size)
                self.assertEqual(record["uncompressed_bytes"], member.file_size)
                self.assertEqual(record["crc32"], member.CRC)
                self.assertTrue(record["encrypted"])
                self.assertTrue(record["opaque"])
                self.assertFalse(record["extracted"])
                self.assertNotIn("sha256", record)
                self.assertFalse(
                    any(
                        call.args[1] == record["ipsw_path"]
                        for call in read_member.call_args_list
                    )
                )

            self.assertTrue(receipt["policy"]["install_target_inventory_enabled"])
            self.assertFalse(receipt["policy"]["install_target_members_extracted"])
            self.assertEqual(
                [path.name for path in output.iterdir()
                 if "UniversalMac_27.0_27A1_OS" in path.name
                 or "SystemRestoreImage_27A1" in path.name],
                [],
            )

    def test_img4_derivative_keeps_signed_components_and_records_no_acceptance(self) -> None:
        im4p = _im4p(b"ibss", b"signed-iBSS")
        im4m = _der(0x30, _der(0x16, b"IM4M") + b"ticket")
        wrapped = PREPARE.wrap_img4(im4p, im4m)
        self.assertIn(im4p, wrapped)
        self.assertIn(im4m, wrapped)
        suffix = PREPARE.dfu_suffix(wrapped)
        self.assertEqual(len(suffix), 16)
        self.assertEqual(suffix[:12], bytes.fromhex("ffffffffac05000155464410"))
        self.assertIsNone(PREPARE._der_magic(im4p, b"IM4P"))
        self.assertIsNone(PREPARE._der_magic(im4m, b"IM4M"))


if __name__ == "__main__":
    unittest.main()
