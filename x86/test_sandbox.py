"""Artifact and transport boundaries, independent of a full Apple guest."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from x86 import sandbox
from x86.settings import SettingsStore


class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def artifact(self):
        raw = bytearray(1024)
        raw[:2] = b"MZ"
        struct.pack_into("<I", raw, 60, 64)
        raw[64:68] = b"PE\0\0"
        struct.pack_into("<H", raw, 68, 0x8664)
        struct.pack_into("<H", raw, 70, 1)
        struct.pack_into("<H", raw, 84, 240)
        struct.pack_into("<H", raw, 88, 0x20B)
        struct.pack_into("<I", raw, 104, 0x1000)
        struct.pack_into("<II", raw, 144, 0x2000, 512)
        struct.pack_into("<H", raw, 156, 10)
        struct.pack_into("<IIII", raw, 336, 512, 0x1000, 512, 512)
        struct.pack_into("<I", raw, 364, 0x60000020)
        directory = self.root / "sandbox/efi/build"
        directory.mkdir(parents=True)
        binary = directory / "BOOTX64.EFI"
        binary.write_bytes(raw)
        (directory / "build-report.json").write_text(json.dumps({"sha256": hashlib.sha256(raw).hexdigest()}))
        return binary

    def test_missing_artifact_cannot_be_staged(self):
        self.assertFalse(sandbox.status(root=self.root)["stageable"])
        with self.assertRaises(OSError):
            sandbox.prepare(26, str(self.root / "out"), root=self.root)
        self.assertFalse((self.root / "out").exists())

    def test_tampered_artifact_rejected_before_output(self):
        binary = self.artifact()
        binary.write_bytes(binary.read_bytes() + b"tamper")
        self.assertFalse(sandbox.status(root=self.root)["artifact_available"])
        with self.assertRaisesRegex(ValueError, "hash"):
            sandbox.prepare(26, str(self.root / "out"), root=self.root)
        self.assertFalse((self.root / "out").exists())

    def test_wrong_machine_rejected_even_with_matching_hash(self):
        binary = self.artifact()
        raw = bytearray(binary.read_bytes())
        struct.pack_into("<H", raw, 68, 0xAA64)
        binary.write_bytes(raw)
        (binary.parent / "build-report.json").write_text(json.dumps({"sha256": hashlib.sha256(raw).hexdigest()}))
        with self.assertRaisesRegex(ValueError, "x86_64"):
            sandbox.prepare(26, str(self.root / "out"), root=self.root)

    def test_non_executable_header_and_wrong_report_type_are_rejected(self):
        binary = self.artifact()
        raw = bytearray(binary.read_bytes())
        struct.pack_into("<H", raw, 70, 0)
        binary.write_bytes(raw)
        report = binary.parent / "build-report.json"
        report.write_text(json.dumps({"sha256": hashlib.sha256(raw).hexdigest()}))
        self.assertFalse(sandbox.status(root=self.root)["stageable"])
        report.write_text("[]")
        self.assertFalse(sandbox.status(root=self.root)["stageable"])

    def test_staging_never_claims_guest_boot_and_preserves_existing_esp(self):
        binary = self.artifact()
        output = self.root / "out"
        result = sandbox.prepare(27, str(output), root=self.root)
        self.assertTrue(result["ok"])
        self.assertFalse(result["boot_verified"])
        self.assertFalse(result["macos_boot_ready"])
        self.assertEqual((output / "EFI/BOOT/BOOTX64.EFI").read_bytes(), binary.read_bytes())
        with self.assertRaisesRegex(ValueError, "existing EFI"):
            sandbox.prepare(26, str(output), root=self.root)
        self.assertEqual(json.loads((output / "26x86-sandbox.json").read_text(encoding="utf8"))["target_major"], 27)

    def test_invalid_target_cannot_be_coerced(self):
        for value in (True, 25, 26.0, "26.0", 28, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                sandbox.plan(value, root=self.root)

    def test_bridge_mode_blocks_native_mutating_actions(self):
        from x86.gui.bridge import WizardBridge
        store = SettingsStore(self.root / "settings.json")
        with patch("x86.gui.bridge.SettingsStore", return_value=store):
            bridge = WizardBridge()
        self.assertTrue(bridge.set_execution_mode("sandbox")["ok"])
        for action in ("build", "install", "patch", "unpatch", "advanced"):
            with self.subTest(action=action):
                result = bridge.launch_wx_action(action)
                self.assertFalse(result["ok"])
                self.assertIn("Sandbox", result["error"])
        self.assertFalse(bridge.set_execution_mode("qemu")["ok"])
        self.assertEqual(store.read("execution_mode"), "sandbox")
        self.assertTrue(bridge.set_execution_mode("native")["ok"])
        self.assertFalse(bridge.prepare_sandbox(26, str(self.root / "out"))["ok"])


if __name__ == "__main__":
    unittest.main()
