"""Unit tests for ``x86.silicon.validation`` gate steps."""

from __future__ import annotations

import unittest

from x86.silicon.validation import (
    run_all,
    run_gates,
    step_boot_chain_never_claims_real_boot,
    step_dfu_handshake_default_trace,
    step_install_session_labels,
    step_mock_host_matrix,
)


class ValidationStepsTest(unittest.TestCase):
    def test_each_gate_ok(self) -> None:
        for fn in (
            step_boot_chain_never_claims_real_boot,
            step_dfu_handshake_default_trace,
            step_mock_host_matrix,
            step_install_session_labels,
        ):
            with self.subTest(step=fn.__name__):
                result = fn()
                self.assertTrue(result.ok, msg=f"{result.name}: {result.error or result.detail}")

    def test_run_gates_all(self) -> None:
        results = run_gates()
        self.assertEqual(len(results), 4)
        self.assertTrue(all(result.ok for result in results))

    def test_run_all_gates_only_shape(self) -> None:
        payload = run_all(run_unittests=False)
        self.assertTrue(payload["gates_ok"])
        self.assertIn("host", payload)
        self.assertIn("note", payload)


if __name__ == "__main__":
    unittest.main()
