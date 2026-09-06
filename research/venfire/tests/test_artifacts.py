import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from venfire import artifacts


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        # macOS /var and /tmp may themselves be symlinks; fixtures deliberately
        # pass direct physical paths, just as immutable-input callers must.
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "original-input.bin"
        self.payload = bytes(range(256)) * 200
        self.source.write_bytes(self.payload)

    def test_hash_manifest_roundtrip_does_not_modify_source(self):
        initial = self.source.stat()
        manifest = artifacts.create_manifest([self.source], kind="restore")
        record = manifest.artifacts[0]
        self.assertEqual(record.sha256, hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(record.size_bytes, len(self.payload))
        self.assertEqual(record.path, str(self.source))
        output = self.root / "inputs.json"
        self.assertEqual(artifacts.write_manifest(manifest, output), output)
        loaded = artifacts.load_manifest(output)
        self.assertEqual(manifest, loaded)
        self.assertTrue(artifacts.require_intact(loaded).valid)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertEqual(self.source.stat().st_mtime_ns, initial.st_mtime_ns)
        self.assertEqual(set(self.root.iterdir()), {self.source, output})

    def test_same_size_corruption_is_detected(self):
        manifest = artifacts.create_manifest([self.source])
        self.source.write_bytes(b"X" + self.payload[1:])
        report = artifacts.verify_manifest(manifest)
        self.assertFalse(report.valid)
        self.assertEqual(report.issues[0].reason, "SHA-256 differs from manifest")
        with self.assertRaises(artifacts.ArtifactIntegrityError):
            artifacts.require_intact(manifest)

    def test_truncation_and_missing_file_are_detected(self):
        manifest = artifacts.create_manifest([self.source])
        self.source.write_bytes(b"truncated")
        self.assertIn("byte length", artifacts.verify_manifest(manifest).issues[0].reason)
        self.source.unlink()
        report = artifacts.verify_manifest(manifest)
        self.assertFalse(report.valid)
        self.assertEqual(report.checked_count, 1)
        self.assertEqual(report.issues[0].reason, "FileNotFoundError")

    def test_change_while_hashing_is_rejected(self):
        original_sha256 = hashlib.sha256
        source = self.source

        class MutatingDigest:
            def __init__(self):
                self.digest = original_sha256()
                self.changed = False

            def update(self, chunk):
                self.digest.update(chunk)
                if not self.changed:
                    self.changed = True
                    with source.open("ab") as output:
                        output.write(b"changed during read")

            def hexdigest(self):
                return self.digest.hexdigest()

        with patch.object(artifacts.hashlib, "sha256", MutatingDigest):
            with self.assertRaises(artifacts.ArtifactChangedError):
                artifacts.hash_artifact(self.source)

    def test_directory_is_rejected_before_read(self):
        with self.assertRaises(artifacts.ArtifactInputError):
            artifacts.hash_artifact(self.root)

    def test_read_regular_checks_identity_even_when_consumer_raises(self):
        with self.assertRaises(artifacts.ArtifactChangedError):
            with artifacts.read_regular(self.source) as stream:
                self.assertEqual(stream.read(2), self.payload[:2])
                with self.source.open("ab") as output:
                    output.write(b"modified")
                raise RuntimeError("consumer failed")
        with self.assertRaisesRegex(RuntimeError, "consumer failed"):
            with artifacts.read_regular(self.source):
                raise RuntimeError("consumer failed")

    @unittest.skipUnless(os.name == "posix", "POSIX special file")
    def test_device_and_fifo_are_rejected_without_blocking(self):
        with self.assertRaises(artifacts.ArtifactInputError):
            artifacts.hash_artifact("/dev/null")
        fifo = self.root / "pipe"
        os.mkfifo(fifo)
        with self.assertRaises(artifacts.ArtifactInputError):
            artifacts.hash_artifact(fifo)

    def make_symlink(self, destination, target, *, directory=False):
        try:
            destination.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {type(exc).__name__}")

    def test_file_symlink_is_rejected(self):
        link = self.root / "alias.bin"
        self.make_symlink(link, self.source)
        with self.assertRaises(artifacts.ArtifactInputError):
            artifacts.hash_artifact(link)

    def test_parent_symlink_is_rejected(self):
        real = self.root / "real"
        real.mkdir()
        (real / "file.bin").write_bytes(b"data")
        linked = self.root / "linked"
        self.make_symlink(linked, real, directory=True)
        with self.assertRaises(artifacts.ArtifactInputError):
            artifacts.hash_artifact(linked / "file.bin")

    def test_parent_traversal_is_rejected_before_normalization(self):
        with self.assertRaises(artifacts.ArtifactInputError):
            artifacts.hash_artifact(self.root / "unused" / ".." / self.source.name)

    def test_manifest_never_overwrites_input_or_existing_output(self):
        manifest = artifacts.create_manifest([self.source])
        with self.assertRaises(artifacts.ManifestError):
            artifacts.write_manifest(manifest, self.source)
        self.assertEqual(self.source.read_bytes(), self.payload)
        output = self.root / "exists.json"
        output.write_bytes(b"already exists")
        with self.assertRaises(FileExistsError):
            artifacts.write_manifest(manifest, output)
        self.assertEqual(output.read_bytes(), b"already exists")

    def test_empty_single_string_or_duplicate_input_list_is_rejected(self):
        for paths in ([], str(self.source), [self.source, self.source]):
            with self.subTest(paths=paths):
                with self.assertRaises(artifacts.ArtifactInputError):
                    artifacts.create_manifest(paths)

    def test_schema_and_digest_validation(self):
        baseline = artifacts.create_manifest([self.source]).to_dict()
        cases = []
        for field, value in (("schema_version", True), ("algorithm", "md5"), ("created_at", "2026-09-06"), ("extra", 1)):
            data = json.loads(json.dumps(baseline))
            data[field] = value
            cases.append(data)
        for field, value in (("sha256", "0" * 63), ("size_bytes", True), ("size_bytes", -1), ("path", "relative.bin"), ("kind", "../restore")):
            data = json.loads(json.dumps(baseline))
            data["artifacts"][0][field] = value
            cases.append(data)
        data = json.loads(json.dumps(baseline))
        data["artifacts"].append(data["artifacts"][0])
        cases.append(data)
        manifest_path = self.root / "invalid.json"
        for data in cases:
            with self.subTest(data=data):
                manifest_path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(artifacts.ManifestError):
                    artifacts.load_manifest(manifest_path)

    def test_duplicate_json_keys_and_oversized_manifest_rejected(self):
        output = self.root / "bad.json"
        output.write_text('{"schema_version": 1, "schema_version": 2}', encoding="utf-8")
        with self.assertRaises(artifacts.ManifestError):
            artifacts.load_manifest(output)
        output.write_bytes(b" " * (4 * 1024 * 1024 + 1))
        with self.assertRaises(artifacts.ManifestError):
            artifacts.load_manifest(output)

    @unittest.skipUnless(os.name == "nt", "Windows path namespace")
    def test_unc_device_namespace_and_alternate_streams_rejected(self):
        for path in (r"\\server\share\file", r"\\.\PhysicalDrive0", str(self.source) + ":stream"):
            with self.subTest(path=path):
                with self.assertRaises(artifacts.ArtifactInputError):
                    artifacts.hash_artifact(path)


if __name__ == "__main__":
    unittest.main()
