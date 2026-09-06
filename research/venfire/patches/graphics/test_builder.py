"""Input/path regression tests; no compiler, guest, disk device or network runs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('venfire_optional_graphics_builder',
                                             PROJECT / 'tools/build_graphics_backend.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InputTests(unittest.TestCase):
    def test_malformed_lock_types_are_rejected(self):
        original = builder.regular_bytes
        for malformed in ([], {'schema': True}, {'schema': 1, 'core_patches': []},
                          {'schema': 1, 'core_patches': {'example.patch': 8}}):
            with self.subTest(malformed=malformed):
                def read(path):
                    return json.dumps(malformed).encode() if path.name == 'lock.json' else original(path)
                with patch.object(builder, 'regular_bytes', side_effect=read):
                    with self.assertRaises(ValueError):
                        builder.load_inputs()

    def test_current_reviewed_inputs_and_separate_series(self):
        lock, snapshots = builder.load_inputs()
        self.assertEqual(lock['core_patches']['0003-vmapple-recovery-usb.patch'],
                         '29faaa21e284e82fb3e7848574730627c9c7d55f60a5a2e8bdb3310bad4acd0c')
        self.assertEqual(len(lock['imported_files']), 6)
        self.assertNotIn('graphics', (PROJECT / 'patches/series').read_text())
        self.assertTrue(all(name in snapshots for name in (
            'probes/mapper_handoff.S', 'probes/air_compute.rs', 'probes/verify.py')))

    def test_tampered_patch_is_rejected_before_build(self):
        original = builder.regular_bytes
        def read(path):
            value = original(path)
            return value + b'\nchanged' if path.name == '0002-reims-current-arm-vcpu.patch' else value
        with patch.object(builder, 'regular_bytes', side_effect=read):
            with self.assertRaisesRegex(ValueError, 'Reviewed input changed'):
                builder.load_inputs()

    def test_unlisted_default_patch_is_rejected(self):
        original = builder.regular_bytes
        def read(path):
            value = original(path)
            return value + b'extra.patch\n' if path == PROJECT / 'patches/series' else value
        with patch.object(builder, 'regular_bytes', side_effect=read):
            with self.assertRaisesRegex(ValueError, 'Core series differs'):
                builder.load_inputs()

    def test_missing_fresh_directory_is_not_created_by_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'new' / 'nested'
            self.assertEqual(builder.checked_directory(path, exists=False), path)
            self.assertFalse(path.exists())

    def test_parent_traversal_and_regular_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'file'
            path.write_bytes(b'fixture')
            with self.assertRaises(ValueError):
                builder.checked_directory(path, exists=False)
            with self.assertRaisesRegex(ValueError, 'Parent traversal'):
                builder.checked_directory(root / 'x' / '..' / 'new', exists=False)

    def test_symlink_ancestor_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / 'real'
            real.mkdir()
            link = root / 'link'
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError:
                self.skipTest('Symlink creation is unavailable to the test account')
            with self.assertRaisesRegex(ValueError, 'link or non-directory'):
                builder.checked_directory(link / 'new', exists=False)


if __name__ == '__main__':
    unittest.main()
