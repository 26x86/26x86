"""Fail-closed deployment checks; synthetic Mach-O is a parser fixture only."""
import hashlib
import ast
import logging
import json
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from x86.patch.abstraction import validate_manifest, root_patch_gate


class AbstractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / "adapter.dylib"
        self.raw = struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 6, 1, 8, 0, 0) + struct.pack("<II", 0, 8)
        self.binary.write_bytes(self.raw)
        self.manifest = self.root / "abstraction.json"
        self.data = {"schema":"26x86.abstraction/1", "adapter":"test.unregistered",
            "target":{"macos_major":27,"os_build":"26A5425a","architecture":"x86_64","runtime_abi":"test-abi"},
            "files":[{"path":"adapter.dylib","kind":"dylib","license":"BSD-4-Clause",
                      "source":{"url":"https://example.invalid/source","revision":"a"*40},
                      "sha256":hashlib.sha256(self.raw).hexdigest()}]}
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def validate(self, **kwargs):
        args = dict(target_major=27, os_build="26A5425a", architecture="x86_64")
        args.update(kwargs)
        return validate_manifest(self.manifest, **args)

    def test_valid_files_do_not_authorize_deployment(self):
        result = self.validate()
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["can_apply"])
        self.assertFalse(result["runtime_abi_verified"])
        self.assertFalse(root_patch_gate(self.manifest, target_major=27,
            os_build="26A5425a", architecture="x86_64")["ok"])

    def test_os_update_invalidates_package(self):
        self.assertFalse(self.validate(os_build="26A9999a")["ok"])
        self.assertFalse(self.validate(target_major=26)["ok"])
        self.assertFalse(self.validate(expected_abi="different-abi")["ok"])

    def test_manifest_architecture_cannot_relabel_binary(self):
        self.data["target"]["architecture"] = "arm64"
        self.write()
        self.assertFalse(self.validate(architecture="arm64")["ok"])

    def test_tampered_binary_is_rejected(self):
        self.binary.write_bytes(self.raw + b"tampered")
        self.assertFalse(self.validate()["ok"])

    def test_path_traversal_is_rejected(self):
        for invalid in ("../adapter.dylib", "C:/adapter.dylib", "/adapter.dylib", "dir\\adapter.dylib"):
            with self.subTest(invalid=invalid):
                self.data["files"][0]["path"] = invalid
                self.write()
                self.assertFalse(self.validate()["ok"])

    def test_load_command_bounds_are_checked_even_with_matching_hash(self):
        raw = struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 6, 1, 8, 0, 0) + struct.pack("<II", 0, 64)
        self.binary.write_bytes(raw)
        self.data["files"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.write()
        self.assertFalse(self.validate()["ok"])

    def test_duplicate_json_fields_are_rejected(self):
        self.manifest.write_text('{"schema":"wrong","schema":"26x86.abstraction/1"}', encoding="utf-8")
        self.assertFalse(self.validate()["ok"])

    def test_27_gate_runs_before_legacy_patch_detector(self):
        from x86.patch.root import preflight
        with patch("x86.patch.root.is_macos", return_value=True):
            result = preflight(constants=SimpleNamespace(detected_os=26, detected_os_build="26A5425a"))
        self.assertEqual(result["status"], "abstraction_blocked")
        self.assertFalse(result["can_patch"])

    def test_26_default_gate_preserves_existing_engine(self):
        self.assertTrue(root_patch_gate(None, target_major=26, os_build="25A1", architecture="x86_64")["ok"])

    def test_unknown_future_os_is_not_sent_to_legacy_engine(self):
        self.assertFalse(root_patch_gate(None, target_major=28, os_build="27A1", architecture="x86_64")["ok"])

    def test_direct_patch_entry_stops_before_detection_or_mount(self):
        # Windows cannot import macOS Security.framework. Compile the actual
        # production entry method without importing the platform-only module.
        source = Path(__file__).resolve().parents[2] / "opencore_legacy_patcher/sys_patch/sys_patch.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PatchSysVolume")
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "start_patch")
        namespace = {"logging": logging,
            "HardwarePatchsetDetection": lambda *_: self.fail("Legacy detector must not run")}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
        constants = SimpleNamespace(detected_os=26, detected_os_build="26A5425a", root_patcher_succeeded=True)
        engine = SimpleNamespace(constants=constants,
            _mount_root_vol=lambda: self.fail("Root volume must not be mounted"))
        with self.assertLogs(level="ERROR"):
            self.assertFalse(namespace["start_patch"](engine, interactive=False))
        self.assertFalse(constants.root_patcher_succeeded)

    def test_generic_mac_gui_patch_uses_root_preflight(self):
        from x86.gui.bridge import WizardBridge
        bridge = WizardBridge.__new__(WizardBridge)
        bridge._settings = SimpleNamespace(read=lambda key, default=None: default)
        with patch("x86.gui.bridge.is_macos", return_value=True), \
             patch("x86.patch.root.preflight", return_value={"can_patch":False, "status":"abstraction_blocked",
                 "blockers":["unregistered adapter"]}) as gate:
            report = bridge.launch_wx_action("patch")
        gate.assert_called_once_with()
        self.assertFalse(report["ok"])
        self.assertIn("unregistered adapter", report["error"])


if __name__ == "__main__":
    unittest.main()
