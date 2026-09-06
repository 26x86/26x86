#!/usr/bin/env python3
"""Negative tests for evidence gates; synthetic events never represent a GPU run."""
import argparse
import hashlib
import importlib.util
import json
import os
import plistlib
import struct
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "Tools" / filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


metal = module("metal_runner", "metal-run.py")
abi = module("abi_inventory", "abi-inventory.py")
offline = module("offline_compiler", "metal-offline-compile.py")


def fixture():
    # Evaluator-only fixture, intentionally not saved as native probe evidence.
    nonce = 1531
    inputs, poison, expected = metal.challenge_vectors(nonce, 4096)
    input_hash, poison_hash, expected_hash = map(metal.words_sha256, (inputs, poison, expected))
    events = [
        {"stage": "target_correlated", "physical_vendor": 0x8086, "physical_device": 0x7D41, "physical_bdf": 0x1000,
         "visible_vendor": 0x8086, "visible_device": 0x9A49, "physical_identity_source": "pci-config-before-spoof",
         "unique_metal_registry_match": True, "device_name": "Intel Graphics"},
        {"stage": "challenge_initialized", "nonce": nonce, "count": 4096, "input_sha256": input_hash,
         "initial_output_sha256": poison_hash, "expected_output_sha256": expected_hash,
         "initial_nonce_witness": nonce ^ 0xDEADBEEF, "expected_nonce_witness": nonce ^ 0x7D410003,
         "acceptance_input_first_four": [1, 2, 3, 4], "acceptance_output_first_four": [10, 17, 24, 31]},
        {"stage": "compute_output_passed", "nonce": nonce, "count": 4096, "mismatches": 0,
         "actual_first_four": [10, 17, 24, 31], "expected_first_four": [10, 17, 24, 31],
         "output_sha256": expected_hash, "expected_output_sha256": expected_hash, "output_changed": True,
         "nonce_witness": nonce ^ 0x7D410003, "expected_nonce_witness": nonce ^ 0x7D410003,
         "queue_registry_id": "1234", "command_registry_id": "1234",
         "gpu_start_time": 100.0, "gpu_end_time": 100.001, "gpu_timing_recorded": True},
        {"stage": "render_output_passed", "pixels": 16, "mismatches": 0, "expected_rgba": [255, 0, 0, 255],
         "actual_first_rgba": [255, 0, 0, 255], "readback_sha256": metal.EXPECTED_RENDER_SHA256,
         "expected_readback_sha256": metal.EXPECTED_RENDER_SHA256, "command_registry_id": "1234",
         "gpu_start_time": 100.002, "gpu_end_time": 100.003, "gpu_timing_recorded": True},
        {"stage": "completed", "compute_output_passed": True, "render_output_passed": True,
         "physical_identity_correlated": True, "small_target_metal_probe_passed": True, "cpu_fallback_used": False,
         "full_metal_conformance_verified": False, "windowserver_presentation_verified": False,
         "hardware_irq_fence_verified": False, "stress_acceptance_verified": False,
         "evidence_scope": "public Metal compute and offscreen render only"},
    ]
    return [dict(event, schema_version=3, registry_id="1234") for event in events]


class EvidenceGateTests(unittest.TestCase):
    def test_complete_synthetic_fixture_only_tests_parser(self):
        self.assertTrue(metal.evaluate_events(fixture(), "1234")[0])

    def test_known_offscreen_hash_is_independently_reconstructed(self):
        readback = bytearray([0xA5] * (256 * 4))
        for row in range(4):
            for column in range(4):
                offset = row * 256 + column * 4
                readback[offset:offset + 4] = bytes((255, 0, 0, 255))
        self.assertEqual(hashlib.sha256(readback).hexdigest(), metal.EXPECTED_RENDER_SHA256)

    def test_enumeration_cannot_pass(self):
        self.assertFalse(metal.evaluate_events(fixture())[0])

    def test_fault_injection(self):
        faults = [(0, "physical_device", 0x9A49), (0, "physical_bdf", 0), (0, "physical_vendor", 0),
                  (0, "visible_vendor", 0), (0, "visible_device", 0x1234), (0, "unique_metal_registry_match", False),
                  (0, "device_name", "SwiftShader"), (0, "physical_identity_source", "injected"),
                  (1, "nonce", 0), (1, "nonce", True), (1, "input_sha256", "zz" * 32),
                  (1, "initial_output_sha256", "0" * 64), (1, "expected_output_sha256", "0" * 64),
                  (1, "acceptance_output_first_four", [10, 17, 24, 30]),
                  (2, "nonce", 0), (2, "count", 4095), (2, "mismatches", 1),
                  (2, "actual_first_four", [10, 17, 24, 30]), (2, "output_sha256", "2" * 64),
                  (2, "nonce_witness", 0), (2, "command_registry_id", "5678"),
                  (2, "gpu_start_time", 0.0), (2, "gpu_timing_recorded", False),
                  (3, "pixels", 15), (3, "mismatches", 1), (3, "actual_first_rgba", [0, 0, 255, 255]),
                  (3, "readback_sha256", "4" * 64), (3, "command_registry_id", "5678"),
                  (3, "gpu_end_time", 0.0),
                  (4, "compute_output_passed", False), (4, "render_output_passed", False),
                  (4, "physical_identity_correlated", False), (4, "cpu_fallback_used", True),
                  (4, "small_target_metal_probe_passed", False),
                  (4, "full_metal_conformance_verified", True), (4, "windowserver_presentation_verified", True),
                  (4, "hardware_irq_fence_verified", True),
                  (4, "stress_acceptance_verified", True)]
        for index, key, value in faults:
            with self.subTest(index=index, key=key, value=value):
                events = fixture()
                events[index][key] = value
                self.assertFalse(metal.evaluate_events(events, "1234")[0])

    def test_each_stage_registry_and_schema(self):
        for index in range(5):
            for key, value in [("registry_id", "5678"), ("schema_version", 1)]:
                with self.subTest(index=index, key=key):
                    events = fixture()
                    events[index][key] = value
                    self.assertFalse(metal.evaluate_events(events, "1234")[0])

    def test_partial_duplicate_reordered_and_failed(self):
        events = fixture()
        cases = [events[:-1], events + [events[-1]], list(reversed(events)),
                 events + [{"stage": "failed"}], events + [{"stage": "unrecognized_trailer"}], [None], None]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.assertFalse(metal.evaluate_events(candidate, "1234")[0])

    def test_invalid_registry(self):
        for value in ("garbage", "0", "-1", str(2 ** 64)):
            self.assertFalse(metal.evaluate_events(fixture(), value)[0])


class MachOInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        binary = Path(os.environ.get("MELLOW_KEXT_BINARY",
                      str(ROOT / "build/Release/Mellow.kext/Contents/MacOS/Mellow")))
        cls.data = binary.read_bytes()

    def test_real_crossbuilt_kext_inventory_not_abi_pass(self):
        result = abi.macho_inventory(self.data)
        self.assertEqual(result["filetype"], 11)
        self.assertGreater(len(result["imports"]), 100)
        self.assertFalse(result["private_abi_verified"])

    def test_truncated_and_invalid_load_commands_rejected(self):
        corrupt = bytearray(self.data)
        struct.pack_into("<I", corrupt, 36, 0xFFFFFFF8)
        for data in (b"", self.data[:31], bytes(corrupt), b"\xca\xfe\xba\xbe\0\0\0\0"):
            with self.subTest(length=len(data)):
                with self.assertRaises((ValueError, struct.error)):
                    abi.macho_inventory(data)

    def test_malformed_plist_and_executable_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "Mock.kext"
            contents = bundle / "Contents"
            contents.mkdir(parents=True)
            for info in ([], {"CFBundleExecutable": "../outside"}, {"CFBundleExecutable": "Mock", "OSBundleLibraries": []}):
                (contents / "Info.plist").write_bytes(plistlib.dumps(info))
                with self.assertRaises(ValueError):
                    abi.inventory_bundle(bundle)

    def test_missing_dependency_and_complete_fixture_stay_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = abi.create_report([root])
            self.assertFalse(missing["required_artifacts_present"])
            for role, (name, required) in abi.COMPONENTS.items():
                if not required:
                    continue
                contents = root / name / "Contents"
                (contents / "MacOS").mkdir(parents=True)
                # Synthetic role fixture, never installed/executed: adjust its
                # header solely for the parser test; actual kext is unchanged.
                data = bytearray(self.data)
                kind = 11 if name.endswith(".kext") else (6 if name.endswith(".framework") else 8)
                struct.pack_into("<I", data, 12, kind)
                (contents / "MacOS/Mock").write_bytes(data)
                (contents / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "Mock",
                    "CFBundleIdentifier": "fixture." + role, "CFBundleVersion": "1.0",
                    "OSBundleLibraries": {"fixture.unavailable": "2.0"}}))
            complete = abi.create_report([root])
            self.assertTrue(complete["required_artifacts_present"])
            self.assertEqual(complete["gate"], "BLOCKED")
            self.assertFalse(complete["metal_available"])
            self.assertFalse(complete["private_abi_verified"])
            self.assertTrue(all(not item["provider_paths"] for item in complete["bundle_dependency_evidence"]))


class IntelContainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = (ROOT / "compiler-evidence/mellow_evidence_mtl.bin").read_bytes()

    def test_actual_intel_compiler_output(self):
        result = offline.inspect_zebin(self.data)
        self.assertEqual(result["machine"], 205)
        self.assertGreater(result["machine_code_bytes"], 100)
        self.assertEqual(result["intelgt_compatibility_notes"][6], 0x03118000)
        self.assertFalse(result["instructions_executed"])
        self.assertFalse(result["runtime_relocations_applied"])

    def test_wrong_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "product configuration"):
            offline.inspect_zebin(self.data, 0xDEADBEEF)

    def test_corrupt_machine_and_section_bounds(self):
        wrong_machine = bytearray(self.data)
        struct.pack_into("<H", wrong_machine, 18, 62)
        wrong_bounds = bytearray(self.data)
        struct.pack_into("<Q", wrong_bounds, 40, len(self.data) + 1)
        for data in (b"", self.data[:63], self.data[:-1], bytes(wrong_machine), bytes(wrong_bounds)):
            with self.subTest(length=len(data)):
                with self.assertRaises((ValueError, struct.error)):
                    offline.inspect_zebin(data)

    def test_corrupt_relocation_or_notes_rejected(self):
        parsed = offline.inspect_zebin(self.data)
        for name in (".rel.text.mellow_evidence", ".note.intelgt.compat"):
            section = next(item for item in parsed["sections"] if item["name"] == name)
            corrupted = bytearray(self.data)
            struct.pack_into("<Q", corrupted, section["offset"], 0xFFFFFFFFFFFFFFFF)
            with self.assertRaises((ValueError, struct.error)):
                offline.inspect_zebin(corrupted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    class CountingResult(unittest.TextTestResult):
        subcases = 0
        def addSubTest(self, test, subtest, outcome):
            self.subcases += 1
            super().addSubTest(test, subtest, outcome)
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2, resultclass=CountingResult).run(suite)
    if args.report:
        inputs = [Path(__file__), ROOT / "Tools/metal-run.py", ROOT / "Tools/abi-inventory.py",
                  ROOT / "Tools/metal-offline-compile.py", ROOT / "compiler-evidence/mellow_evidence_mtl.bin",
                  ROOT / "build/Release/Mellow.kext/Contents/MacOS/Mellow"]
        report = {"passed": result.wasSuccessful(), "test_methods": result.testsRun, "subcases": result.subcases,
                  "gpu_execution_tested": False, "native_swift_compilation_tested": False,
                  "scope": "host-side parser/evidence rejection tests, including actual offline Intel and Mach-O containers",
                  "input_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
