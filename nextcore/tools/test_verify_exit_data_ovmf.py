"""Regression gates for observations already captured from authored OVMF runs."""
import json
from pathlib import Path
import signal
import tempfile
import time
import unittest

import verify_exit_data_ovmf as harness
from verify_hal_ovmf import InvalidEvidence


def receipt():
    return dict(cleanup_complete=True, process_group_remaining=False, adopted_children_remaining=[],
                natural_returncode=None, returncode=0, stopped_by_harness=True, timed_out=True)


class ExitDataHarnessTests(unittest.TestCase):
    def test_intended_bounded_stop_is_allowed(self):
        for code in (0, -signal.SIGTERM, -signal.SIGKILL):
            value = receipt()
            value["returncode"] = code
            harness.validate_qemu_observation(value)

    def test_natural_zero_exit_is_allowed(self):
        value = receipt()
        value.update(natural_returncode=0, stopped_by_harness=False, timed_out=False)
        harness.validate_qemu_observation(value)

    def test_natural_crash_or_nonzero_cannot_pass(self):
        for code in (-25, -11, 1, 67):
            value = receipt()
            value.update(natural_returncode=code, returncode=code, stopped_by_harness=False, timed_out=False)
            with self.subTest(code=code), self.assertRaises(InvalidEvidence):
                harness.validate_qemu_observation(value)

    def test_stop_race_cannot_hide_sigxfsz(self):
        value = receipt()
        value["returncode"] = -25
        with self.assertRaises(InvalidEvidence):
            harness.validate_qemu_observation(value)

    def test_unexpected_cleanup_stop_is_not_planned_stop(self):
        value = receipt()
        value["timed_out"] = False
        with self.assertRaises(InvalidEvidence):
            harness.validate_qemu_observation(value)

    def test_expired_hash_deadline_still_publishes_failed_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source = output / "input.bin"
            source.write_bytes(b"immutable test input")
            before = {str(source): harness.sha256(source)}
            report = {"cases": [{"passed": True} for _ in harness.cases()]}
            harness.finalize_report(report, before, time.monotonic() - 1, output, time.monotonic(), 1)
            stored = json.loads((output / "report.json").read_text())
            self.assertFalse(stored["passed"])
            self.assertFalse(stored["original_inputs_preserved"])
            self.assertTrue(stored["deadline_exceeded"])
            self.assertIn("TimeoutError", stored["input_hash_observation_errors"][str(source)])
            self.assertFalse((output / "report.json.tmp").exists())

    def test_failed_hash_read_still_publishes_failed_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source = output / "missing-input.bin"
            report = {"cases": [{"passed": True} for _ in harness.cases()]}
            harness.finalize_report(report, {str(source): "0" * 64}, time.monotonic() + 10, output, time.monotonic(), 1)
            stored = json.loads((output / "report.json").read_text())
            self.assertFalse(stored["passed"])
            self.assertFalse(stored["original_inputs_preserved"])
            self.assertIn("FileNotFoundError", stored["input_hash_observation_errors"][str(source)])


if __name__ == "__main__":
    unittest.main()
