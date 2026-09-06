#!/usr/bin/env python3
"""CPU-only consistency/corruption controls; synthetic pixels are never GPU evidence."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_runner", ROOT / "Tools/run-render-objects.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def synthetic_pixels(seed=17):
    # Independent barycentric construction of an ideal triangle at pixel centers.
    # It is a test fixture for the verifier, not the native rendering implementation.
    px, py, pz, pw = RUNNER.parameters(seed, 0)
    a, b, c = [((x + px + 1) * 32, (1 - y - py) * 24) for x, y in
               ((-.72, -.52), (.58, -.32), (-.18, .72))]
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    result = bytearray()
    for y in range(48):
        for x in range(64):
            u = ((b[1] - c[1]) * (x + .5 - c[0]) + (c[0] - b[0]) * (y + .5 - c[1])) / denominator
            v = ((c[1] - a[1]) * (x + .5 - c[0]) + (a[0] - c[0]) * (y + .5 - c[1])) / denominator
            if u >= 0 and v >= 0 and u + v <= 1:
                result.extend((round((x + .5) * pw * 255), round((y + .5) * pw * 255), round(pz * 255), 255))
            else:
                result.extend((0, 0, 0, 0))
    return result


def native_fixture(raw):
    sha = hashlib.sha256(raw).hexdigest()
    return dict(schema_version=1, passed=True, seed=17, requested_frames=1, frames_completed=1,
                width=64, height=48, first_sequence=1, last_sequence=1, epoch=1, pipeline_build_count=1,
                msl_stages_translated=2, native_program_compilations=1, portable_mellow_object_api=True,
                all_frame_completions_correlated=True, apple_metal_abi_registered=False,
                native_macos_execution=False, windowserver_acceleration_verified=False,
                display_scanout_verified=False, runtime_received_pixel_oracle=False,
                visible_requested=False, row_origin="top-left", negative_checks=sorted(RUNNER.NEGATIVES), checks=100,
                raw_stream_sha256=sha,
                device=dict(vendor="SYNTHETIC", renderer="NO GPU", version="3.3", glsl_version="3.30",
                            major=3, minor=3, accelerated_pixel_format=True, core_profile=True, software_renderer_rejected=True),
                samples=[dict(iteration=0, sequence=1, texture_sequence=1, epoch=1, render_submitted=True,
                              fence_signaled=True, readback_completed=True, resources_released=True,
                              swap_completed=False, scanout_verified=False, rgba_sha256=sha)])


class Controls(unittest.TestCase):
    def verify(self, raw, seed=17):
        with tempfile.TemporaryDirectory(prefix="mellow-render-pixel-control-") as directory:
            path = Path(directory) / "synthetic.rgba"; path.write_bytes(raw)
            return RUNNER.verify_stream(path, seed, 1)

    def test_independent_ideal_triangle(self):
        result = self.verify(synthetic_pixels())
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["pixels_verified"], 3072)
        self.assertGreater(result["minimum_foreground_per_frame"], 500)

    def test_clear_and_flipped_rows_are_not_render_passes(self):
        self.assertFalse(self.verify(bytes(RUNNER.FRAME_BYTES))["passed"])
        raw = synthetic_pixels()
        flipped = b"".join(raw[y * 256:(y + 1) * 256] for y in reversed(range(48)))
        self.assertFalse(self.verify(flipped)["passed"])
        self.assertFalse(self.verify(raw[:-4])["passed"])

    def test_interior_tolerance_is_one_rgb_unit(self):
        raw = synthetic_pixels()
        index = next(i for i in range(3072) if RUNNER.pixel_contract(17, 0, i % 64, i // 64)[0] == "inside")
        at = index * 4
        one = bytearray(raw); one[at] += 1
        self.assertTrue(self.verify(one)["passed"])
        two = bytearray(raw); two[at] += 2
        self.assertFalse(self.verify(two)["passed"])
        alpha = bytearray(raw); alpha[at + 3] = 254
        self.assertFalse(self.verify(alpha)["passed"])

    def test_boundary_accepts_only_clear_or_triangle(self):
        found = None
        for seed in range(64):
            _, edges, tolerance = RUNNER.triangle(seed, 0)
            for y in range(48):
                for x in range(64):
                    minimum = min(a * (x + .5) + b * (y + .5) + c for a, b, c in edges)
                    if -tolerance <= minimum <= tolerance:
                        found = seed, x, y
                        break
                if found:
                    break
            if found:
                break
        self.assertIsNotNone(found)
        seed, x, y = found
        raw = synthetic_pixels(seed)
        at = (y * 64 + x) * 4
        clear = bytearray(raw); clear[at:at + 4] = b"\0\0\0\0"
        self.assertTrue(self.verify(clear, seed)["passed"])
        triangle = bytearray(raw); triangle[at:at + 4] = bytes(RUNNER.pixel_contract(seed, 0, x, y)[1])
        self.assertTrue(self.verify(triangle, seed)["passed"])
        wrong = bytearray(raw); wrong[at:at + 4] = b"\x80\x80\x80\x80"
        self.assertFalse(self.verify(wrong, seed)["passed"])
        outside = bytearray(raw); outside[0:4] = bytes(RUNNER.pixel_contract(seed, 0, 0, 0)[1])
        self.assertFalse(self.verify(outside, seed)["passed"])

    def test_native_metadata_and_samples(self):
        raw = synthetic_pixels()
        with tempfile.TemporaryDirectory(prefix="mellow-render-report-control-") as directory:
            path = Path(directory) / "synthetic.rgba"; path.write_bytes(raw)
            native = native_fixture(raw)
            self.assertEqual(RUNNER.validate_native(native, 17, 1, False, path), [])
            mutations = [
                lambda r: r.update(seed=99), lambda r: r.update(epoch=99),
                lambda r: r.update(first_sequence=99), lambda r: r.update(pipeline_build_count=2),
                lambda r: r.update(msl_stages_translated=0), lambda r: r.update(negative_checks=[]),
                lambda r: r.update(error="Conflicting error"), lambda r: r.update(frames_completed=True),
                lambda r: r.update(samples=[]), lambda r: r["samples"][0].update(texture_sequence=99),
                lambda r: r["samples"][0].update(fence_signaled=False),
                lambda r: r["samples"][0].update(swap_completed=True),
                lambda r: r["samples"][0].update(readback_completed=False),
                lambda r: r["samples"][0].update(resources_released=False),
                lambda r: r["samples"][0].update(rgba_sha256="0" * 64),
                lambda r: r["device"].update(accelerated_pixel_format=False),
            ]
            for mutate in mutations:
                changed = copy.deepcopy(native); mutate(changed)
                self.assertTrue(RUNNER.validate_native(changed, 17, 1, False, path))

    def test_strict_json(self):
        for text in ('{"passed":true,"passed":false}', '{"x":NaN}', '{"x":Infinity}', '{"x":{"k":1,"k":2}}'):
            with self.assertRaises(ValueError):
                RUNNER.strict_json(text)

    def test_final_source_change_overrides_success_exit(self):
        seen = {}
        def changing_digest(path):
            seen[str(path)] = seen.get(str(path), 0) + 1
            return "changed" if path.name == "RenderObjects.cpp" and seen[str(path)] > 1 else "stable"
        with tempfile.TemporaryDirectory(prefix="mellow-render-source-control-") as directory:
            fake = subprocess.CompletedProcess([], 0, stdout="synthetic compiler", stderr="")
            with mock.patch.object(RUNNER.sys, "argv", ["test", "--cxx", "synthetic-cxx", "--out", directory]), \
                 mock.patch.object(RUNNER, "digest", side_effect=changing_digest), \
                 mock.patch.object(RUNNER.subprocess, "run", return_value=fake), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(RUNNER.main(), 1)
            report = json.loads((Path(directory) / "render-objects.json").read_text())
            self.assertFalse(report["passed"])
            self.assertEqual(report["status"], "FAILED_SOURCE_CHANGED")


if __name__ == "__main__":
    unittest.main()
