"""A verifier crash must not become a successful provider bypass control."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "nextcore/artifacts/arm-memory-provider-20260909"
RUNNER = ROOT / "nextcore/tools/verify_arm_memory_provider_ovmf.py"


class BypassReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("memory_provider_runner", RUNNER)
        cls.runner = importlib.util.module_from_spec(spec)
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec.loader.exec_module(cls.runner)
        finally:
            sys.dont_write_bytecode = previous
        cls.sources = [FIXTURES / name for name in (
            "bypass-negative.json", "bypass-execution.json", "serial/bypass.log")]
        cls.original_bytes = [path.read_bytes() for path in cls.sources]
        cls.valid_receipt = json.loads(cls.original_bytes[0])
        cls.execution = json.loads(cls.original_bytes[1])["execution"]

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nextcore-bypass-receipt-")
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        (self.output / "bypass").mkdir()
        for source, destination in zip(self.sources, (
                "bypass-negative.json", "bypass/report.json", "bypass/serial.log")):
            shutil.copyfile(source, self.output / destination)

    def tearDown(self):
        self.assertEqual([path.read_bytes() for path in self.sources], self.original_bytes)

    def validate(self):
        return self.runner.validate_bypass_rejection(self.output, self.execution)

    def test_captured_actual_direct_bypass_is_accepted(self):
        self.assertIsNone(self.validate())

    def test_exit_one_without_receipt_is_rejected(self):
        (self.output / "bypass-negative.json").unlink()
        with self.assertRaises(OSError):
            self.validate()

    def test_exit_one_with_corrupt_receipt_is_rejected(self):
        (self.output / "bypass-negative.json").write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.validate()

    def test_other_failures_cannot_substitute_for_provider_rejection(self):
        missing = object()
        mutations = [
            ("wrong_schema", ("schema",), "other"),
            ("wrong_case", ("cases", 0, "name"), "half-signed"),
            ("unrelated_failure", ("cases", 0, "checks", "inputs_preserved"), False),
            ("missing_check", ("cases", 0, "checks", "provider_abi"), missing),
            ("non_boolean", ("cases", 0, "checks", "provider_abi"), 0),
            ("wrong_execution", ("cases", 0, "execution", "registers", "x0"), 130),
            ("wrong_serial", ("cases", 0, "serial_sha256"), "0" * 64),
            ("wrong_report", ("cases", 0, "report_sha256"), "0" * 64),
            ("provider_present", ("cases", 0, "observed"), {"provider_status": 0}),
            ("claimed_success", ("passed",), True),
        ]
        for name, path, value in mutations:
            with self.subTest(name=name):
                receipt = copy.deepcopy(self.valid_receipt)
                target = receipt
                for key in path[:-1]:
                    target = target[key]
                if value is missing:
                    del target[path[-1]]
                else:
                    target[path[-1]] = value
                (self.output / "bypass-negative.json").write_text(
                    json.dumps(receipt), encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    self.validate()


if __name__ == "__main__":
    unittest.main()
