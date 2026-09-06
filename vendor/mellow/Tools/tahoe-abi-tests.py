#!/usr/bin/env python3
"""Malformed-input and real-target static ABI tests; no kernel loading."""
import argparse
import copy
import importlib.util
import json
import pathlib
import plistlib
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("tahoe_abi", pathlib.Path(__file__).with_name("tahoe-abi.py"))
abi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(abi)


class BoundsTests(unittest.TestCase):
    def test_range_arithmetic(self):
        for offset, size in [(-1, 0), (0, -1), (4, 0), (1, 3), (2 ** 64, 1)]:
            with self.subTest(offset=offset, size=size), self.assertRaises(ValueError):
                abi.check(b"123", offset, size)
        abi.check(b"123", 3, 0)

    def test_string_bounds(self):
        for data, offset, limit in [(b"ABC", 0, 3), (b"ABC\0", 0, 3), (b"\0", 1, 1), (b"\0", -1, 1)]:
            with self.subTest(data=data, offset=offset), self.assertRaises(ValueError):
                abi.string(data, offset, limit)

    def test_macho_header_and_command_overrun(self):
        header = struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 11, 1, 8, 0, 0)
        self.assertEqual(abi.commands(header + struct.pack("<II", 0, 8))[0][3], 11)
        for data in [b"", header, header + struct.pack("<II", 0, 0), header + struct.pack("<II", 0, 16),
                     struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 11, 100, 8, 0, 0) + b"\0" * 8]:
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                abi.commands(data)

    def test_universal_slice_rejection(self):
        for data in [b"\xca\xfe\xba\xbe\0\0\0\0", b"\xca\xfe\xba\xbe\0\0\0\x01" + b"\xff" * 20]:
            with self.assertRaises(ValueError):
                abi.thin_x86(data)

    def test_uleb_overflow(self):
        for data in [b"", b"\x80", b"\xff" * 10 + b"\0", b"\x80" * 9 + b"\x02"]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                abi.uleb(data, 0)

    def test_export_trie_valid_and_corrupt(self):
        self.assertEqual(abi.export_trie(b"\0\x01_a\0\x06\x02\0\x01\0"), {"_a": {"flags": 0, "address_offset": 1}})
        for data in [b"", b"\0\x01_a\0\0", b"\0\x01_a\0\x7f", b"\0\x01_a", b"\x7f\0"]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                abi.export_trie(data)

    def test_version_order(self):
        ordered = ["1.0d0", "1.0a1", "1.0b1", "1.0fc1", "1.0", "1.0.1", "2.0"]
        self.assertEqual([abi.version(v) for v in ordered], sorted(abi.version(v) for v in ordered))
        for value in [None, "1.2.3.4", "1.beta", "../1", ""]:
            with self.assertRaises(ValueError):
                abi.version(value)

    def test_dyld_header_mapping_and_suffix_bounds(self):
        data = bytearray(1024)
        data[:16] = b"dyld_v1  x86_64\0"
        struct.pack_into("<II", data, 16, 552, 1)
        struct.pack_into("<3Q2I", data, 552, 0x1000, 1024, 0, 5, 5)
        struct.pack_into("<II", data, 448, 640, 1)
        struct.pack_into("<3Q2I", data, 640, 0x1000, 0, 0, 680, 0)
        data[680:695] = b"/fixture.dylib\0\0"
        self.assertEqual(abi.cache_index(data)["images"][0]["path"], "/fixture.dylib")
        for offset, fmt, value in [(16, "<I", 100), (20, "<I", 65), (452, "<I", 1000000),
                                   (664, "<I", 5000), (560, "<Q", 2048)]:
            corrupted = bytearray(data)
            struct.pack_into(fmt, corrupted, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                abi.cache_index(corrupted)
        corrupted = bytearray(data)
        struct.pack_into("<II", corrupted, 392, 720, 1)
        corrupted[744:748] = b"../\0"
        with self.assertRaises(ValueError):
            abi.cache_index(corrupted)

    def test_fileset_duplicate_and_out_of_range_entry(self):
        def collection(offset, duplicate=False):
            entry = struct.pack("<IIQQII", 0x80000035, 40, 0x1000, offset, 32, 0) + b"fixture\0"
            cmds = entry * (2 if duplicate else 1)
            header = struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 12, 2 if duplicate else 1, len(cmds), 0, 0)
            body = header + cmds
            body += b"\0" * (4096 - len(body))
            body += struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 11, 1, 8, 0, 0) + struct.pack("<II", 0, 8)
            return body
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "fixture.kc"
            path.write_bytes(collection(4096))
            self.assertIn("fixture", abi.read_kc(path)["images"])
            for data in [collection(4096, True), collection(2 ** 63)]:
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    abi.read_kc(path)


class EligibilityTests(unittest.TestCase):
    def fixture(self):
        definition = {"value": 123, "n_type": 15, "external": True, "private_external": False}
        collection = {"images": {"com.apple.kernel": {"definitions": {"_real": definition}}}, "metadata": {},
            "symbol_sets": {"SymbolsSets": [{"CFBundleIdentifier": "com.apple.kpi.fixture", "CFBundleVersion": "2.0",
                "OSBundleCompatibleVersion": "1.0", "Symbols": [{"SymbolName": "_alias", "AliasTarget": "_real"}]}]}}
        lilu_info = {"CFBundleIdentifier": "fixture.lilu", "CFBundleVersion": "1.7.2", "OSBundleCompatibleVersion": "1.2.0"}
        lilu = {"definitions": {"_plugin": definition}}
        mellow = {"imports": ["_alias", "_plugin"]}
        info = {"CFBundleVersion": "test", "OSBundleLibraries": {"com.apple.kpi.fixture": "1.0", "fixture.lilu": "1.6.4"}}
        return [collection], lilu, lilu_info, mellow, info

    def test_whitelist_alias_and_declared_provider(self):
        result = abi.resolve_imports(*self.fixture())
        self.assertTrue(result["all_imports_statically_eligible"])
        self.assertFalse(result["runtime_loaded"])
        self.assertFalse(result["metal_verified"])

    def test_missing_alias_target_rejected(self):
        args = self.fixture()
        args[0][0]["images"]["com.apple.kernel"]["definitions"].clear()
        self.assertEqual(abi.resolve_imports(*args)["unmatched"], ["_alias"])

    def test_present_kernel_name_without_whitelist_rejected(self):
        args = self.fixture()
        args[3]["imports"] = ["_real"]
        self.assertEqual(abi.resolve_imports(*args)["unmatched"], ["_real"])

    def test_missing_declaration_rejected(self):
        args = self.fixture()
        del args[4]["OSBundleLibraries"]["fixture.lilu"]
        self.assertEqual(abi.resolve_imports(*args)["unmatched"], ["_plugin"])

    def test_private_external_rejected(self):
        args = self.fixture()
        args[1]["definitions"]["_plugin"]["private_external"] = True
        self.assertIn("_plugin", abi.resolve_imports(*args)["unmatched"])

    def test_version_outside_compatibility_interval(self):
        for value in ["0.9", "3.0", "bad"]:
            args = self.fixture()
            args[4]["OSBundleLibraries"]["com.apple.kpi.fixture"] = value
            self.assertIn("_alias", abi.resolve_imports(*args)["unmatched"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real-report", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    class CountResult(unittest.TextTestResult):
        subcases = 0
        def addSubTest(self, test, subtest, outcome):
            self.subcases += 1
            super().addSubTest(test, subtest, outcome)
    result = unittest.TextTestRunner(verbosity=2, resultclass=CountResult).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    report = {"passed": result.wasSuccessful(), "test_methods": result.testsRun, "subcases": result.subcases,
              "runtime_link_load_or_metal_tested": False}
    if args.real_report:
        actual = json.loads(args.real_report.read_text())
        report["real_report_static_import_count"] = actual["import_count"]
        report["real_report_static_matched_count"] = actual["matched_count"]
        report["real_report_no_runtime_claim"] = actual["runtime_loaded"] is False and actual["metal_verified"] is False
        report["passed"] &= actual["all_imports_statically_eligible"] and report["real_report_no_runtime_claim"]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)
