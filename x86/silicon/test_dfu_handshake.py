"""Unit tests for ``x86.silicon.dfu_handshake``."""

from __future__ import annotations

import json
import unittest

from x86.silicon.dfu_handshake import DfuState, run_dfu_handshake


class DfuHandshakeTest(unittest.TestCase):
    def test_nominal_trace_reaches_complete(self) -> None:
        trace = run_dfu_handshake()
        self.assertTrue(trace.ok)
        self.assertEqual(trace.final_state, DfuState.COMPLETE)
        self.assertGreater(len(trace.transitions), 0)

    def test_fault_injection_stops_before_target_state(self) -> None:
        trace = run_dfu_handshake(inject_failure_at=DfuState.BULK_OUT_READY)
        self.assertFalse(trace.ok)
        self.assertEqual(trace.final_state, DfuState.FAILED)
        reached = {transition.to_state for transition in trace.transitions}
        self.assertIn(DfuState.RESET_PENDING, reached)
        self.assertNotIn(DfuState.IBEC_HANDOFF_GATE, reached)

    def test_fault_injection_at_start_fails_immediately(self) -> None:
        trace = run_dfu_handshake(inject_failure_at=DfuState.DETACHED)
        self.assertFalse(trace.ok)
        self.assertEqual(len(trace.transitions), 1)
        self.assertEqual(trace.transitions[0].to_state, DfuState.FAILED)

    def test_as_dict_is_json_safe(self) -> None:
        trace = run_dfu_handshake()
        json.dumps(trace.as_dict())  # must not raise


if __name__ == "__main__":
    unittest.main()
