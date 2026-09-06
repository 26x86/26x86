"""Small deterministic checks for the OVMF/QEMU input harness helpers."""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "sandbox/vsk/tools/verify_efi_inputs.py"


def load_harness():
    spec = importlib.util.spec_from_file_location("vsk_efi_harness", HARNESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VskEfiHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness = load_harness()

    def test_resolves_bare_executable_without_a_shell(self):
        name = Path(sys.executable).name
        if shutil.which(name) is None:
            self.skipTest(f"{name} is not available by bare name on PATH")
        resolved = self.harness.resolve_executable(name)
        self.assertTrue(resolved.is_file())

    def test_resolves_explicit_ovmf_file_and_rejects_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "OVMF_CODE.fd"
            image.write_bytes(b"fixture")
            self.assertEqual(self.harness.resolve_file(image, "OVMF code image"), image)
            with self.assertRaises(FileNotFoundError):
                self.harness.resolve_file(root, "OVMF code image")

    def test_records_version_result_for_a_known_runtime(self):
        result = self.harness.qemu_version(Path(sys.executable))
        self.assertTrue(result["ok"])
        self.assertEqual(result["returncode"], 0)
        self.assertIn("Python", result["text"])


if __name__ == "__main__":
    unittest.main()
