#!/usr/bin/env python3
"""Reporting/timeout regression with mocked child processes; no GPU execution."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("opencl_runtime_runner", ROOT / "Tools/run-opencl-runtime.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class CheckpointTests(unittest.TestCase):
    def test_latest_complete_json_survives_other_truncated_slot(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "run.json"
            first = {"complete": False, "passed": False, "requested_iterations": 10000,
                     "verified_iterations": 100, "seed": 5}
            second = {**first, "verified_iterations": 200}
            a = Path(str(path) + ".checkpoint-a.json")
            b = Path(str(path) + ".checkpoint-b.json")
            a.write_text(json.dumps(first))
            b.write_text(json.dumps(second))
            self.assertEqual(RUNNER.last_checkpoint(path, 10000)["verified_iterations"], 200)
            b.write_text('{"complete":false,')
            self.assertEqual(RUNNER.last_checkpoint(path, 10000)["verified_iterations"], 100)

    def test_stale_or_success_claims_are_not_partial_checkpoints(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "run.json"
            a = Path(str(path) + ".checkpoint-a.json")
            base = {"complete": False, "passed": False, "requested_iterations": 10000,
                    "verified_iterations": 100, "seed": 5}
            for changed in ({"passed": True}, {"complete": True}, {"verified_iterations": 10001},
                            {"verified_iterations": -1}, {"requested_iterations": 3}, {"seed": -1}):
                a.write_text(json.dumps({**base, **changed}))
                self.assertIsNone(RUNNER.last_checkpoint(path, 10000))

    def run_mocked_worker(self, behavior):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)

            def child(command, **kwargs):
                if os.name == "nt":
                    self.assertEqual(Path(kwargs["env"]["PATH"].split(os.pathsep)[0]), Path("synthetic-cxx").resolve().parent)
                if "--version" in command:
                    return subprocess.CompletedProcess(command, 0, "synthetic compiler\n", "")
                if "-o" in command:
                    Path(command[command.index("-o") + 1]).write_bytes(b"synthetic non-executable test artifact")
                    return subprocess.CompletedProcess(command, 0, "", "")
                result = Path(command[command.index("--report") + 1])
                seed = int(command[command.index("--seed") + 1])
                if behavior == "timeout":
                    inputs, expected = RUNNER.reference_streams(seed, 100)
                    checkpoint = {"complete": False, "passed": False, "requested_iterations": 10000,
                                  "verified_iterations": 100, "seed": seed, "input_stream_sha256": inputs,
                                  "expected_stream_sha256": expected, "readback_stream_sha256": expected}
                    Path(str(result) + ".checkpoint-a.json").write_text(json.dumps(checkpoint))
                    raise subprocess.TimeoutExpired(command, kwargs["timeout"])
                if behavior == "corrupt":
                    result.write_text('{"incomplete":')
                return subprocess.CompletedProcess(command, 99, "", "synthetic crash")

            argv = ["runner", "--cxx", "synthetic-cxx", "--out", str(output),
                    "--compute", "--iterations", "10000", "--timeout", "180"]
            RUNNER.platform.uname() # Resolve Windows OS subprocess queries outside the child mock.
            with patch.object(sys, "argv", argv), patch.object(RUNNER.subprocess, "run", child), contextlib.redirect_stdout(io.StringIO()):
                self.assertNotEqual(RUNNER.main(), 0)
            return json.loads((output / "opencl-runtime.json").read_text())

    def test_crash_without_report_is_unknown_not_no_gpu(self):
        report = self.run_mocked_worker("missing")
        self.assertIsNone(report["gpu_work_executed"])
        self.assertFalse(report["native_runtime_gpu_compute_pass"])

    def test_corrupt_report_is_unknown_not_no_gpu(self):
        report = self.run_mocked_worker("corrupt")
        self.assertIsNone(report["gpu_work_executed"])
        self.assertFalse(report["native_runtime_gpu_compute_pass"])

    def test_timeout_retains_verified_prefix_but_never_passes(self):
        report = self.run_mocked_worker("timeout")
        self.assertEqual(report["status"], "TIMED_OUT")
        self.assertIsNone(report["gpu_work_executed"])
        self.assertEqual(report["partial_submission_progress"]["verified_iterations"], 100)
        self.assertTrue(report["partial_stream_reference_matches"])
        self.assertFalse(report["native_runtime_gpu_compute_pass"])

    def test_saved_actual_sample_mutations_are_rejected(self):
        # Source-controlled native evidence is optional in source-only packages;
        # current workspace hardware report exercises correlation without GPU rerun.
        locations = [ROOT / "build/opencl-runtime-stress-10000/opencl-runtime.json",
                     ROOT / "validation/native-opencl-runtime-stress-10000.json",
                     ROOT / "validation/native-opencl-runtime.json"]
        paths = [path for path in locations if path.exists()]
        if not paths:
            self.skipTest("No captured native evidence in this checkout")
        saved = json.loads(paths[0].read_text(encoding="utf-8"))
        native = saved["native"]
        count = native["submission_summary"]["requested_iterations"]
        self.assertTrue(RUNNER.validate_native_result(copy.deepcopy(native), 0, count)[0])
        mutations = [
            lambda x: x["runs"][0].update(iteration=999999),
            lambda x: x["runs"][0]["execution"].update(epoch=999999),
            lambda x: x["runs"][0]["execution"].update(sequence=999999),
            lambda x: x["runs"][0]["input"].pop(),
            lambda x: x["runs"][0]["input"].__setitem__(0, 0xFFFFFFFF),
            lambda x: x["runs"][-1]["execution"].update(gpu_end_ns=999999),
            lambda x: x["negative_checks"].update(wrong_reference_rejected=False),
        ]
        for change in mutations:
            modified = copy.deepcopy(native)
            change(modified)
            self.assertFalse(RUNNER.validate_native_result(modified, 0, count)[0])


if __name__ == "__main__":
    unittest.main()
