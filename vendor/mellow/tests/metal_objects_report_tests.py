#!/usr/bin/env python3
"""Synthetic report controls only; these tests never execute a GPU."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("object_runner", ROOT / "Tools/run-metal-objects.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def synthetic_result(count=3):
    seed = 17
    def event(sequence, oracle=False):
        return dict(epoch=1, sequence=sequence, gpu_start=sequence * 100,
                    gpu_end=sequence * 100 + 10, submission_attempted=True, submitted=True,
                    execution_completed=True, runtime_planned=not oracle,
                    event_ownership_verified=True, profiling_verified=True, resources_released=True,
                    results_verified=oracle, runtime_completion_accepted=False)
    inputs, outputs = RUNNER.expected_streams(seed, count)
    result = dict(schema_version=1, passed=True, portable_mellow_object_api=True,
                  native_driver_pipeline_compiled_once=True, ordered_two_encoder_result_verified=True,
                  all_dispatches_correlated=True, all_dispatches_no_oracle=True,
                  apple_metal_abi_registered=False, system_mtl_device_registered=False, macos_tested=False,
                  physical_pci_identity_verified=False, runtime_requires_expected_answer=False,
                  seed=seed, requested_iterations=count, verified_iterations=count,
                  pipeline_build_count=1, first_sequence=2, last_sequence=count + 1, epoch=1,
                  negative_checks=13, checks=count * 16 + 60, source_kind="msl", entry="mellow_objects",
                  input_stream_sha256=inputs, expected_stream_sha256=outputs, readback_stream_sha256=outputs,
                  bootstrap=event(1, True), samples=[], ordered_events=[event(count + 2), event(count + 3)])
    for iteration in ([0] if count == 1 else [0, count - 1]):
        values = [(seed ^ ((i + iteration * 263) * 0x9E3779B9)) & 0xFFFF for i in range(256)]
        result["samples"].append(dict(iteration=iteration, event=event(iteration + 2),
                                      input=values, output=[value * 7 + 3 for value in values]))
    return result


class ReportControls(unittest.TestCase):
    def accepted(self, value, count=3):
        return RUNNER.validate_native_result(value, 17, count, "msl", "mellow_objects")

    def test_consistent_synthetic_fixture(self):
        self.assertEqual(self.accepted(synthetic_result()), [])
        self.assertEqual(self.accepted(synthetic_result(1), 1), [])

    def test_summary_identity_mutations(self):
        for field, value in [("seed", 18), ("epoch", 2), ("first_sequence", 99),
                             ("last_sequence", 101), ("source_kind", "air-text"),
                             ("pipeline_build_count", 2), ("negative_checks", 0),
                             ("all_dispatches_correlated", False), ("all_dispatches_no_oracle", False),
                             ("native_driver_pipeline_compiled_once", 1), ("seed", True),
                             ("checks", 0), ("readback_stream_sha256", "0" * 64)]:
            with self.subTest(field=field, value=value):
                result = synthetic_result()
                result[field] = value
                self.assertTrue(self.accepted(result))

    def test_missing_or_mismatched_samples(self):
        for mutate in (lambda r: r.update(samples=[]),
                       lambda r: r["samples"][0].update(input=[]),
                       lambda r: r["samples"][0].update(output=[]),
                       lambda r: r["samples"][0].update(iteration=99),
                       lambda r: r["samples"][0]["event"].update(epoch=99),
                       lambda r: r["samples"][0]["event"].update(sequence=99),
                       lambda r: r["samples"][0]["output"].__setitem__(0, 0),
                       lambda r: r["samples"][0].update(event=None)):
            result = synthetic_result()
            mutate(result)
            self.assertTrue(self.accepted(result))

    def test_event_flag_mutations(self):
        for position in ("bootstrap", "sample", "ordered"):
            for key in ("submitted", "submission_attempted", "execution_completed", "runtime_planned",
                        "event_ownership_verified", "profiling_verified", "resources_released",
                        "results_verified", "runtime_completion_accepted"):
                result = synthetic_result()
                event = (result["bootstrap"] if position == "bootstrap" else
                         result["samples"][0]["event"] if position == "sample" else result["ordered_events"][0])
                event[key] = not event[key]
                self.assertTrue(self.accepted(result), (position, key))

    def test_ordering_and_malformed_types(self):
        for mutate in (lambda r: r.update(ordered_events=[]),
                       lambda r: r["ordered_events"][0].update(sequence=3),
                       lambda r: r["ordered_events"][1].update(gpu_start=1),
                       lambda r: r["bootstrap"].update(gpu_end="110"),
                       lambda r: r["bootstrap"].update(epoch=True)):
            result = synthetic_result()
            mutate(result)
            self.assertTrue(self.accepted(result))
        self.assertTrue(self.accepted([]))

    def test_strict_json(self):
        for text in ('{"passed":true,"passed":false}', '{"a":NaN}', '{"a":Infinity}',
                     '{"a":{"x":1,"x":2}}'):
            with self.assertRaises(ValueError):
                RUNNER.load_strict_json(text)


if __name__ == "__main__":
    unittest.main()
