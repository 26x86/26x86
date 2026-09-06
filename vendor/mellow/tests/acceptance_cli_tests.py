"""Negative evidence and scope tests; no GPU backend is exercised here."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Userspace'))
import mellow_acceptance as acceptance


class EvidenceTests(unittest.TestCase):
    def good(self):
        return dict(terminal=True, status=4, target_probe_passed=True,
                    native_metal_executed=True, output_matches=True, output_changed=True,
                    device_chain_matches=True, gpu_timing_recorded=True,
                    nonce_witness_matches=True, public_metal_target_compute_verified=True)

    def test_each_missing_evidence_fails(self):
        for field in self.good():
            with self.subTest(field=field):
                result = self.good()
                result.pop(field)
                self.assertFalse(acceptance.accepts(result))

    def test_cpu_fallback_and_unchanged_buffer_fail(self):
        for field in ('native_metal_executed', 'output_changed', 'device_chain_matches'):
            result = self.good()
            result[field] = False
            self.assertFalse(acceptance.accepts(result))

    def test_timeout_cannot_be_late_success(self):
        result = self.good()
        result['timed_out'] = True
        self.assertFalse(acceptance.accepts(result))

    def test_host_completion_does_not_claim_os_counters(self):
        self.assertTrue(acceptance.accepts(self.good()))
        report = acceptance.summary(10000, 10000, 0, 0)
        self.assertTrue(report['target_compute_stress_passed'])
        self.assertIsNone(report['gpu_resets'])
        self.assertIsNone(report['gpu_page_faults'])
        self.assertFalse(report['hardware_irq_fence_verified'])
        self.assertFalse(report['mellow_7d41_metal_acceleration_pass'])

    def test_partial_or_errors_cannot_pass_stress(self):
        for args in ((10000, 9999, 0, 0), (10000, 10000, 1, 0),
                     (10000, 10000, 0, 1), (4, 4, 0, 0)):
            self.assertFalse(acceptance.summary(*args)['target_compute_stress_passed'])


if __name__ == '__main__':
    unittest.main()
