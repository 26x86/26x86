"""Unit tests for ``x86.silicon.mock_host``."""

from __future__ import annotations

import unittest

from x86.silicon.mock_host import HOSTS, evaluate_host, run_mock_host_matrix


class MockHostTest(unittest.TestCase):
    def test_every_fixture_evaluates_ok(self) -> None:
        for host in HOSTS:
            with self.subTest(host=host.host_id):
                result = evaluate_host(host)
                self.assertTrue(result.ok, msg=f"{host.host_id}: {result.detail}")

    def test_nominal_host_completes_dfu(self) -> None:
        nominal = next(host for host in HOSTS if host.inject_dfu_failure_at is None)
        result = evaluate_host(nominal)
        self.assertTrue(result.dfu_ok)

    def test_fault_injected_host_reports_dfu_failure(self) -> None:
        faulted = next(host for host in HOSTS if host.inject_dfu_failure_at is not None)
        result = evaluate_host(faulted)
        self.assertFalse(result.dfu_ok)

    def test_every_fixture_still_blocks_at_documented_boundary(self) -> None:
        for host in HOSTS:
            with self.subTest(host=host.host_id):
                result = evaluate_host(host)
                self.assertEqual(result.blocked_at, "macos_guest_abi_boundary")

    def test_run_mock_host_matrix_shape(self) -> None:
        payload = run_mock_host_matrix()
        self.assertEqual(payload["hosts"], len(HOSTS))
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["results"]), len(HOSTS))


if __name__ == "__main__":
    unittest.main()
