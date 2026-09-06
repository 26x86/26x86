#!/usr/bin/env python3
"""Synthetic report verifier controls; no GL context or GPU is created."""
import hashlib
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gl_runner", ROOT / "Tools/run-opengl-provider.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def fixture(visible=False, count=3):
    digest = hashlib.sha256()
    for i in range(count):
        digest.update(RUNNER.pixels(17, i))
    native = dict(schema_version=1, passed=True, requested_frames=count, frames_completed=count, seed=17,
                  width=64, height=48, pipeline_build_count=1, epoch=1, first_sequence=1, last_sequence=count,
                  negative_checks=11, checks=6 * count + 26, all_frames_correlated=True, all_rgba_patterns_verified=True,
                  native_macos_execution=False, windowserver_acceleration_verified=False,
                  display_scanout_verified=False, physical_pci_identity_verified=False,
                  visible_window_requested=visible, row_origin="bottom-left",
                  expected_stream_sha256=digest.hexdigest(), readback_stream_sha256=digest.hexdigest(),
                  device=dict(vendor="SYNTHETIC", renderer="NO GPU", version="3.3", glsl_version="3.30",
                              major=3, minor=3, accelerated_pixel_format=True, software_renderer_rejected=True, core_profile=True),
                  samples=[])
    for i in ([0] if count == 1 else [0, count - 1]):
        native["samples"].append(dict(iteration=i, sequence=i + 1, epoch=1, render_submitted=True,
                                      fence_signaled=True, readback_completed=True, resources_released=True,
                                      swap_completed=visible, scanout_verified=False, swap_interval_known=visible,
                                      swap_interval=1 if visible else 0,
                                      rgba_sha256=hashlib.sha256(RUNNER.pixels(17, i)).hexdigest()))
    return native


class Controls(unittest.TestCase):
    def validate(self, native, visible=False, count=3):
        return RUNNER.validate_native(native, 17, count, visible)

    def test_consistent_fixture(self):
        self.assertEqual(self.validate(fixture()), [])
        self.assertEqual(self.validate(fixture(True), True), [])
        self.assertEqual(self.validate(fixture(count=1), count=1), [])

    def test_summary_mismatch(self):
        for key, value in (("seed", 19), ("first_sequence", 99), ("last_sequence", 101), ("epoch", 2),
                           ("frames_completed", True), ("pipeline_build_count", 2), ("negative_checks", 0),
                           ("all_frames_correlated", False), ("readback_stream_sha256", "0" * 64),
                           ("display_scanout_verified", True), ("row_origin", "top-left")):
            native = fixture(); native[key] = value
            self.assertTrue(self.validate(native), key)
        native = fixture(); native["error"] = "Driver failed"
        self.assertTrue(self.validate(native))

    def test_frame_mutations(self):
        for key, value in (("iteration", 99), ("sequence", 99), ("epoch", 2), ("render_submitted", False),
                           ("fence_signaled", False), ("readback_completed", False), ("resources_released", False),
                           ("swap_completed", True), ("scanout_verified", True), ("rgba_sha256", "0" * 64)):
            native = fixture(); native["samples"][0][key] = value
            self.assertTrue(self.validate(native), key)

    def test_device_and_missing_fields(self):
        for mutate in (lambda r: r.update(samples=[]),
                       lambda r: r["device"].update(accelerated_pixel_format=False),
                       lambda r: r["device"].update(core_profile=False),
                       lambda r: r["device"].update(major=True),
                       lambda r: r["device"].update(major=3, minor=2),
                       lambda r: r.update(device=None)):
            native = fixture(); mutate(native)
            self.assertTrue(self.validate(native))
        self.assertTrue(self.validate([]))

    def test_strict_json(self):
        for text in ('{"passed":true,"passed":false}', '{"x":NaN}', '{"x":Infinity}', '{"x":{"a":1,"a":2}}'):
            with self.assertRaises(ValueError):
                RUNNER.strict_json(text)

    def test_final_source_change_overrides_success_exit(self):
        seen = {}
        def changing_digest(path):
            seen[str(path)] = seen.get(str(path), 0) + 1
            return "changed" if path.name == "OpenGLProvider.cpp" and seen[str(path)] > 1 else "stable"
        with tempfile.TemporaryDirectory(prefix="mellow-gl-report-control-") as directory:
            fake_result = subprocess.CompletedProcess([], 0, stdout="synthetic compiler", stderr="")
            with mock.patch.object(RUNNER.sys, "argv", ["test", "--cxx", "synthetic-cxx", "--out", directory]), \
                 mock.patch.object(RUNNER, "digest", side_effect=changing_digest), \
                 mock.patch.object(RUNNER.subprocess, "run", return_value=fake_result), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(RUNNER.main(), 1)
            report = json.loads((Path(directory) / "opengl-provider.json").read_text())
            self.assertFalse(report["passed"])
            self.assertEqual(report["status"], "FAILED_SOURCE_CHANGED")


if __name__ == "__main__":
    unittest.main()
