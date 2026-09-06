"""Actual CLI process rejects unsafe configurations without writes or boot rights."""
import json
import os
import plistlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class VskCliTests(unittest.TestCase):
    def invoke(self, path):
        completed = subprocess.run([sys.executable, "-m", "x86", "vsk", "--config", str(path)],
                                   cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        return completed.returncode, json.loads(completed.stdout)

    def test_conformance_is_not_boot_authority(self):
        path = ROOT / "sandbox/vsk/config/example.plist"
        before = path.read_bytes()
        code, result = self.invoke(path)
        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])
        self.assertIs(result["boot_authorized"], False)
        self.assertEqual(path.read_bytes(), before)

    def test_incomplete_golden_gate_profile_is_rejected(self):
        code, result = self.invoke(ROOT / "sandbox/vsk/config/golden-gate.template.plist")
        self.assertEqual(code, 2, result)
        self.assertFalse(result["ok"])
        self.assertFalse(result["boot_authorized"])

    def test_duplicate_and_nonexistent_input_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.plist"
            for body in (b'<plist version="1.0"><dict><key>A</key><true/><key>A</key><false/></dict></plist>',
                         b'<!DOCTYPE plist [<!ENTITY x "AppleIntelOnly">]><plist version="1.0"><string>&x;</string></plist>'):
                path.write_bytes(body)
                code, result = self.invoke(path)
                self.assertEqual(code, 2, result)
                self.assertFalse(result["boot_authorized"])
            path.unlink()
            code, result = self.invoke(path)
            self.assertEqual(code, 2, result)
            self.assertFalse(result["boot_authorized"])

    def test_windows_legacy_stdout_encoding_preserves_unicode_json(self):
        config = plistlib.loads((ROOT / "sandbox/vsk/config/example.plist").read_bytes())
        config["Storage"][0]["DeviceSerial"] = "합성-장치-시험"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "설정.plist"
            path.write_bytes(plistlib.dumps(config))
            result = subprocess.run([sys.executable, "-m", "x86", "vsk", "--config", str(path)],
                cwd=ROOT, capture_output=True, env={**os.environ, "PYTHONIOENCODING":"cp949"})
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(payload["config"]["Storage"][0]["DeviceSerial"], "합성-장치-시험")
        self.assertFalse(payload["boot_authorized"])


if __name__ == "__main__":
    unittest.main()
