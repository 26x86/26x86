import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import stat
import tempfile
import unittest
import warnings
import zipfile


spec = importlib.util.spec_from_file_location("extract_restore", Path(__file__).resolve().parents[1] / "tools" / "extract_restore.py")
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


class ExtractRestoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source, self.output = self.root / "test.zip", self.root / "extracted"
        self.payload = b"self-authored component, no Apple bytes" * 40

    def build(self, *, path="Firmware/test.fixture", mismatch=False, duplicate=False, symlink=False):
        digest = hashlib.sha384(self.payload if not mismatch else b"wrong").digest()
        component = {"Info": {"Path": path}, "Digest": digest}
        identity = {"Info": {"DeviceClass": "vma2macosap", "Variant": "Customer Erase Install (IPSW)"},
                    "Manifest": {"First": component, "Alias": component}}
        manifest = {"BuildIdentities": [identity], "ProductVersion": "TEST", "ProductBuildVersion": "SELF-AUTHORED"}
        with zipfile.ZipFile(self.source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("BuildManifest.plist", plistlib.dumps(manifest))
            entry = zipfile.ZipInfo(path)
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16 if symlink else (stat.S_IFREG | 0o600) << 16
            archive.writestr(entry, self.payload)
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr(entry, self.payload)

    def test_alias_copied_once_and_source_unchanged(self):
        self.build()
        original = self.source.read_bytes()
        result = extractor.extract_restore(self.source, self.output)
        self.assertTrue(result["complete"])
        self.assertTrue(result["input_integrity"]["valid"])
        self.assertFalse(result["macos_boot_verified"])
        self.assertEqual(len(result["components"]), 1)
        self.assertEqual(set(result["components"][0]["names"]), {"First", "Alias"})
        self.assertEqual((self.output / "Firmware/test.fixture").read_bytes(), self.payload)
        self.assertEqual(self.source.read_bytes(), original)

    def test_traversal_rejected_before_any_output_creation(self):
        self.build(path="../outside.fixture")
        with self.assertRaisesRegex(ValueError, "relative"):
            extractor.extract_restore(self.source, self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.root / "outside.fixture").exists())

    def test_duplicate_or_symlink_members_are_rejected(self):
        for option in ("duplicate", "symlink"):
            with self.subTest(option=option):
                self.build(**{option: True})
                with self.assertRaises(ValueError):
                    extractor.extract_restore(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_manifest_digest_mismatch_is_reported_as_incomplete(self):
        self.build(mismatch=True)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            extractor.extract_restore(self.source, self.output)
        report = json.loads((self.output / "extraction.json").read_text())
        self.assertFalse(report["complete"])
        self.assertTrue(report["input_integrity"]["valid"])

    def test_existing_output_is_never_overwritten(self):
        self.build()
        self.output.mkdir()
        sentinel = self.output / "BuildManifest.plist"
        sentinel.write_bytes(b"existing bytes")
        with self.assertRaises(FileExistsError):
            extractor.extract_restore(self.source, self.output)
        self.assertEqual(sentinel.read_bytes(), b"existing bytes")

    def test_missing_selection_never_creates_output(self):
        self.build()
        with self.assertRaisesRegex(ValueError, "existing"):
            extractor.extract_restore(self.source, self.output, components=["Missing"])
        self.assertFalse(self.output.exists())

    def test_evidence_and_metadata_names_cannot_overwrite_original_components(self):
        for path in ("extraction.json", "EXTRACTION.JSON", "extraction.json/child",
                     "selected-identity.plist", "BuildManifest.plist/child"):
            with self.subTest(path=path):
                self.build(path=path)
                with self.assertRaisesRegex(ValueError, "reserved"):
                    extractor.extract_restore(self.source, self.output)
                self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
