import contextlib
import io
import json
import plistlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from venfire.media import inspect_restore
from venfire.cli import main


class RestoreInspectionTests(unittest.TestCase):
    def test_real_metadata_and_no_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "test.ipsw"
            manifest = {"ProductVersion": "test-only", "ProductBuildVersion": "fixture",
                        "BuildIdentities": [{"Info": {"DeviceClass": "fixture"},
                                             "Manifest": {"KernelCache": {"Info": {
                                                 "Path": "kernelcache.fixture"}}}}]}
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("BuildManifest.plist", plistlib.dumps(manifest))
                archive.writestr("kernelcache.fixture", b"NOT AN APPLE KERNEL")
            original = path.read_bytes()
            report = inspect_restore(path, hash_archive=True)
            self.assertEqual(report["product_version"], "test-only")
            self.assertTrue(report["identities"][0]["components"][0]["present_in_archive"])
            self.assertFalse(report["signature_verified"])
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).resolve().iterdir()), [path])

    def test_missing_manifest_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "test.ipsw"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("unrelated", b"x")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                inspect_restore(path)

    def test_unsafe_component_reported_without_extracting(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "test.ipsw"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("BuildManifest.plist", plistlib.dumps({
                    "BuildIdentities": [{"Manifest": {"X": {"Info": {"Path": "../x"}}}}]}))
            report = inspect_restore(path)
            self.assertFalse(report["identities"][0]["components"][0]["safe_relative_path"])

    def test_malformed_nested_plist_types_fail_cleanly(self):
        cases = [
            {"BuildIdentities": "not-array"},
            {"BuildIdentities": [b"not-mapping"]},
            {"BuildIdentities": [{"Info": []}]},
            {"BuildIdentities": [{"Info": {"DeviceClass": b"not-text"}}]},
            {"BuildIdentities": [{"Manifest": []}]},
            {"BuildIdentities": [{"Manifest": {"X": []}}]},
            {"BuildIdentities": [{"Manifest": {"X": {"Info": []}}}]},
            {"BuildIdentities": [{"Manifest": {"X": {"Info": {"Path": 1}}}}]},
            {"SupportedProductTypes": "not-array"},
            {"SupportedProductTypes": [b"not-text"]},
            {"ProductVersion": b"not-text"},
            {"ProductBuildVersion": 42},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "malformed.ipsw"
            for manifest in cases:
                with self.subTest(manifest=manifest):
                    with zipfile.ZipFile(path, "w") as archive:
                        archive.writestr("BuildManifest.plist", plistlib.dumps(manifest))
                    with self.assertRaises(ValueError):
                        inspect_restore(path)
                    captured = io.StringIO()
                    with contextlib.redirect_stdout(captured):
                        code = main(["inspect-restore", str(path)])
                    self.assertEqual(code, 1)
                    self.assertEqual(json.loads(captured.getvalue())["command"], "inspect-restore")

    def test_invalid_archive_and_xml_return_cli_json_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "bad.ipsw"
            payloads = (b"this is not a ZIP", b"<?xml version='1.0'?><plist><dict><key>truncated")
            for index, payload in enumerate(payloads):
                with self.subTest(index=index):
                    if index == 0:
                        path.write_bytes(payload)
                    else:
                        with zipfile.ZipFile(path, "w") as archive:
                            archive.writestr("BuildManifest.plist", payload)
                    before = path.read_bytes()
                    captured = io.StringIO()
                    with contextlib.redirect_stdout(captured):
                        code = main(["inspect-restore", str(path)])
                    self.assertEqual(code, 1)
                    self.assertIn("error", json.loads(captured.getvalue()))
                    self.assertEqual(path.read_bytes(), before)

    def test_symlink_archive_is_rejected_without_resolving(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            original = root / "original.ipsw"
            with zipfile.ZipFile(original, "w") as archive:
                archive.writestr("BuildManifest.plist", plistlib.dumps({}))
            link = root / "alias.ipsw"
            try:
                link.symlink_to(original)
            except OSError:
                self.skipTest("Symlink creation unavailable")
            with self.assertRaisesRegex(ValueError, "Symlink"):
                inspect_restore(link)

    def test_corrupt_deflate_stream_returns_cli_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "bad-deflate.ipsw"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("BuildManifest.plist", plistlib.dumps({"ProductVersion": "fixture"}))
                entry = archive.getinfo("BuildManifest.plist")
            damaged = bytearray(path.read_bytes())
            offset = entry.header_offset + 30 + len(entry.filename.encode()) + len(entry.extra)
            damaged[offset:offset + 2] = b"\xff\xff"
            path.write_bytes(damaged)
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                code = main(["inspect-restore", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("archive cannot be read", json.loads(captured.getvalue())["error"])


if __name__ == "__main__":
    unittest.main()
