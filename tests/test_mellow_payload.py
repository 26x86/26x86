"""Real bundled artifact checks and mutated-package rejection tests."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from x86.mellow.payload import KEXT_SHA256, PayloadError, load_payload


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "payloads/Mellow"


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "Mellow"
        shutil.copytree(PACKAGE, self.path)

    def manifest(self, edit):
        path = self.path / "manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        edit(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def reject(self):
        with self.assertRaises(PayloadError):
            load_payload(self.path)

    def rehash(self, relative):
        data = (self.path / relative).read_bytes()
        self.manifest(lambda m: m["files"].update({relative: {
            "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}}))

    def test_real_bundle_and_engine_dictionary(self):
        payload = load_payload(self.path)
        self.assertEqual(payload.components[0].sha256, KEXT_SHA256)
        self.assertEqual(payload.required_boot_args, ("-mellowdiag",))
        self.assertFalse(payload.capabilities["native_metal"])
        self.assertEqual(payload.patches(), {"Mellow": {"Overwrite Data Volume": {
            "/Library/Extensions": {"Mellow.kext": (self.path / "root").as_posix()}}}})
        self.assertEqual(payload.validate().files, payload.files)

    def test_source_snapshot_all_crossbuild_inputs_match(self):
        proof = json.loads((PACKAGE / "provenance.json").read_text())
        for relative, expected in proof["build_input_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / "vendor/mellow" / relative).read_bytes()).hexdigest(), expected, relative)

    def test_sandbox_is_denied_before_io(self):
        with self.assertRaisesRegex(PayloadError, "Sandbox"):
            load_payload("does-not-exist", mode="apple-silicon-sandbox")

    def test_revalidate_and_patch_cannot_bypass_sandbox(self):
        payload = load_payload(self.path)
        for action in (payload.validate, payload.patches):
            with self.assertRaises(PayloadError):
                action(mode="apple-silicon-sandbox")

    def test_unknown_mode(self):
        with self.assertRaises(PayloadError):
            load_payload(self.path, mode="arm64")

    def test_extra_file(self):
        (self.path / "extra").write_text("extra")
        self.reject()

    def test_missing_file(self):
        (self.path / "LICENSE").unlink()
        self.reject()

    def test_file_hash(self):
        (self.path / "LICENSE").write_text("changed")
        self.reject()

    def test_fresh_validation_at_patch_creation(self):
        payload = load_payload(self.path)
        (self.path / "LICENSE").write_text("changed")
        with self.assertRaises(PayloadError):
            payload.patches()

    def test_inventory_traversal(self):
        for key in ("../escape", "/absolute", "C:/escape", "root\\escape", "root//escape"):
            with self.subTest(key=key):
                self.manifest(lambda m: m["files"].update({key: {"sha256": "0" * 64, "size": 0}}))
                self.reject()

    def test_component_traversal(self):
        self.manifest(lambda m: m["components"][0].update(source="../Mellow.kext"))
        self.reject()

    def test_destination_allowlist(self):
        self.manifest(lambda m: m["components"][0].update(destination="/System/Library/Extensions/Mellow.kext"))
        self.reject()

    def test_duplicate_category(self):
        self.manifest(lambda m: m["components"].append(dict(m["components"][0])))
        self.reject()

    def test_unknown_category(self):
        self.manifest(lambda m: m["components"][0].update(category="apple-driver"))
        self.reject()

    def test_missing_runtime_and_user_driver(self):
        for category, destination in (("runtime", "/Library/Frameworks/Mellow.framework"),
                ("user_driver", "/Library/Application Support/Mellow/Drivers/MellowDriver.bundle")):
            self.manifest(lambda m: m["components"].append({"category": category, "destination": destination,
                "source": "root" + destination, "bundle_id": "com.NiSeullent.Mellow", "version": "0.4.3"}))
            self.reject()

    def test_metadata(self):
        self.manifest(lambda m: m["components"][0].update(bundle_id="com.apple.fake"))
        self.reject()

    def test_acceleration_false_only(self):
        self.manifest(lambda m: m["capabilities"].update(native_metal=True))
        self.reject()

    def test_required_diagnostic_gate(self):
        self.manifest(lambda m: m.update(required_boot_args=["-mellowtglwithgfx"]))
        self.reject()

    def test_macho_wrong_cpu_even_with_updated_inventory(self):
        relative = "root/Library/Extensions/Mellow.kext/Contents/MacOS/Mellow"
        data = bytearray((self.path / relative).read_bytes())
        struct.pack_into("<I", data, 4, 0x0100000c)
        (self.path / relative).write_bytes(data)
        self.rehash(relative)
        self.reject()

    def test_macho_wrong_type_even_with_updated_inventory(self):
        relative = "root/Library/Extensions/Mellow.kext/Contents/MacOS/Mellow"
        data = bytearray((self.path / relative).read_bytes())
        struct.pack_into("<I", data, 12, 1)
        (self.path / relative).write_bytes(data)
        self.rehash(relative)
        self.reject()

    def test_macho_invalid_command_even_with_updated_inventory(self):
        relative = "root/Library/Extensions/Mellow.kext/Contents/MacOS/Mellow"
        data = bytearray((self.path / relative).read_bytes())
        struct.pack_into("<I", data, 36, 0)
        (self.path / relative).write_bytes(data)
        self.rehash(relative)
        self.reject()

    def test_duplicate_json_key(self):
        (self.path / "manifest.json").write_text('{"schema_version":1,"schema_version":1}')
        self.reject()

    def test_extra_kext_plugin_even_with_updated_inventory(self):
        relative = "root/Library/Extensions/Mellow.kext/Contents/PlugIns/extra.kext/Contents/Info.plist"
        path = self.path / relative
        path.parent.mkdir(parents=True)
        path.write_text("extra")
        self.rehash(relative)
        self.reject()

    def test_invalid_json_shape(self):
        (self.path / "manifest.json").write_text("[]")
        self.reject()

    def test_archive_is_not_payload(self):
        archive = self.path / "archive.zip"
        archive.write_bytes(b"PK")
        with self.assertRaises(PayloadError):
            load_payload(archive)

    def test_symlink(self):
        path = self.path / "link"
        try:
            path.symlink_to(self.path / "LICENSE")
        except OSError:
            self.skipTest("Host does not permit unprivileged symlink creation")
        self.reject()


if __name__ == "__main__":
    unittest.main()
