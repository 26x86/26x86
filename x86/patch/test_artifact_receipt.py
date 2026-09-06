"""Receipt binding tests use local synthetic bytes; no Apple payload generation."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from x86.patch.artifact_receipt import create_receipt, verify_receipt


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = self.root / "test.pkg"
        self.payload.write_bytes(b"synthetic package identity fixture")
        self.license = self.root / "LICENSE.txt"
        self.license.write_text("synthetic test license", encoding="utf-8")
        self.compiler = self.root / "compiler"
        self.compiler.write_bytes(b"synthetic compiler identity fixture")
        self.receipt = self.root / "receipt.json"
        self.target = dict(macos_major=27, os_build="26A5425a", architecture="x86_64", runtime_abi="fixture-abi")

    def make(self, role="root-support-package"):
        with patch("x86.patch.artifact_receipt.subprocess.check_output",
                   side_effect=["a"*40, "https://example.invalid/source", ""]):
            data = create_receipt(self.payload, source_repo=self.root, role=role,
                license_file=self.license, compiler_file=self.compiler if role == "gpu-compiler-abi" else None, **self.target)
        self.receipt.write_text(json.dumps(data), encoding="utf-8")
        return data

    def verify(self, **overrides):
        target = {**self.target, **overrides}
        return verify_receipt(self.receipt, self.payload, license_file=self.license, **target)

    def test_identity_is_not_deployment_permission(self):
        self.make()
        report = self.verify()
        self.assertTrue(report["ok"], report)
        self.assertFalse(report["can_apply"])
        self.assertFalse(report["compatibility_verified"])

    def test_os_and_abi_changes_reject_receipt(self):
        self.make()
        self.assertFalse(self.verify(os_build="26A9000a")["ok"])
        self.assertFalse(self.verify(runtime_abi="wrong")["ok"])
        self.assertFalse(self.verify(architecture="arm64")["ok"])

    def test_artifact_or_license_change_rejected(self):
        self.make()
        self.payload.write_bytes(b"changed")
        self.assertFalse(self.verify()["ok"])
        self.make()
        self.license.write_text("changed", encoding="utf-8")
        self.assertFalse(self.verify()["ok"])

    def test_gpu_compiler_binary_is_mandatory_and_bound(self):
        self.make("gpu-compiler-abi")
        self.assertFalse(self.verify()["ok"])
        self.assertTrue(self.verify(compiler_file=self.compiler)["ok"])
        self.compiler.write_bytes(b"changed compiler")
        self.assertFalse(self.verify(compiler_file=self.compiler)["ok"])

    def test_version_label_cannot_relabel_an_old_build(self):
        with self.assertRaises(ValueError):
            create_receipt(self.payload, source_repo=self.root, role="root-support-package",
                license_file=self.license, **{**self.target, "os_build":"25A354"})


if __name__ == "__main__":
    unittest.main()
