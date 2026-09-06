"""Unsafe storage metadata must be rejected before a QEMU process is launched."""

import json
from pathlib import Path
import struct
import tempfile
import unittest

from venfire.artifacts import create_manifest, write_manifest, ArtifactInputError
from venfire.storage import StorageSession, load_storage


class StorageBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        bases = []
        for role in ("aux", "root"):
            base = self.root / (role + ".raw")
            base.write_bytes(b"A" * 4096)
            bases.append(base)
            header = bytearray(104)
            header[:4] = b"QFI\xfb"
            struct.pack_into(">I", header, 4, 3)
            struct.pack_into(">Q", header, 24, 4096)
            (self.root / (role + ".qcow2")).write_bytes(header)
        self.session = StorageSession(self.root, create_manifest(bases), 0)

    def test_changed_original_denies_graph(self):
        (self.root / "root.raw").write_bytes(b"B" * 4096)
        with self.assertRaises(RuntimeError):
            self.session.arguments()

    def test_external_paths_encryption_and_wrong_size_are_rejected(self):
        overlay = self.root / "root.qcow2"
        original = overlay.read_bytes()
        for offset, fmt, value in ((8, ">Q", 104), (16, ">I", 12),
                                   (24, ">Q", 8192), (32, ">I", 1),
                                   (72, ">Q", 4), (4, ">I", 2)):
            with self.subTest(offset=offset):
                header = bytearray(original)
                struct.pack_into(fmt, header, offset, value)
                overlay.write_bytes(header)
                with self.assertRaises(ValueError):
                    self.session.arguments()

    def test_overlay_symlink_is_rejected(self):
        overlay = self.root / "root.qcow2"
        overlay.unlink()
        try:
            overlay.symlink_to(self.root / "aux.qcow2")
        except OSError:
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(ArtifactInputError):
            self.session.arguments()

    def test_non_sector_offsets_and_empty_views_are_rejected(self):
        for offset in (-512, 1, 4096, True, "0"):
            with self.subTest(offset=offset):
                session = StorageSession(self.root, self.session.manifest, offset)
                with self.assertRaises(ValueError):
                    session.arguments()

    def test_resume_rechecks_original_and_overlay_headers(self):
        write_manifest(self.session.manifest, self.root / "bases.json")
        (self.root / "session.json").write_text(json.dumps({"schema": 1, "aux_offset": 0}))
        loaded = load_storage(self.root)
        self.assertEqual(loaded.manifest, self.session.manifest)
        (self.root / "aux.qcow2").write_bytes(b"truncated")
        with self.assertRaises(ValueError):
            load_storage(self.root)


if __name__ == "__main__":
    unittest.main()
