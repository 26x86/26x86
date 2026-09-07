import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("efi_build", ROOT / "sandbox/efi/build.py")
efi_build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(efi_build)


class EfiMeasurementTests(unittest.TestCase):
    def test_lld_map_sections_are_measured_in_hex(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "image.map"
            path.write_text(
                " 0001:00000000 00000020H .text CODE\n"
                " 0002:00000000 00000008H .rdata DATA\n"
                " 0003:00000000 00000010H .bss DATA\n",
                encoding="utf-8",
            )
            measured = efi_build.map_section_measurements(path)
            self.assertEqual(measured[".text"]["bytes"], 0x20)
            self.assertEqual(measured[".rdata"]["bytes"], 8)
            self.assertEqual(sum(item["bytes"] for item in measured.values()), 0x38)

    def test_footprint_marks_unknown_baseline_without_inventing_growth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            image = root / "BOOTX64.EFI"
            image.write_bytes(b"x" * 37)
            map_file = root / "BOOTX64.EFI.map"
            map_file.write_text(" 0001:00000000 00000010H .text CODE\n", encoding="utf-8")
            result = efi_build.footprint_measurement(image, map_file, {})
            self.assertEqual(result["linked_efi_bytes"], 37)
            self.assertEqual(result["growth_bytes"], "unknown")
            self.assertEqual(result["section_total_bytes"], 16)


if __name__ == "__main__":
    unittest.main()
