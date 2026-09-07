"""Offline contract tests for the iBoot -> XNU evidence boundary."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from x86.iboot_handoff import HandoffContractError, StageStatus, verify_handoff_report


def _direct_report(*, markers: bool = False) -> dict[str, object]:
    observation: dict[str, object] = {
        "xnu_executed": markers,
        "macos_userspace_reached": markers,
        "guest_kernel_major": 27 if markers else None,
        "guest_target_match": markers,
        "observed_markers": {"xnu": [], "userspace": [], "installer": []},
    }
    if markers:
        observation["observed_markers"] = {
            "xnu": [{"marker": "Darwin Kernel Version", "byte_offset": 16}],
            "userspace": [{"marker": "launchd:", "byte_offset": 256}],
            "installer": [],
        }
    return {
        "schema": "26x86.vmapple-gui/1",
        "machine_type": "iBoot(AArch64)",
        "guest_os": "macOS",
        "target_major": 27,
        "input_integrity": True,
        "runtime_started": markers,
        "xnu_executed": markers,
        "macos_boot_verified": markers,
        "direct_boot": {
            "requested": True,
            "selection": "macos",
            "dfu_entered": False,
            "observation": observation,
        },
    }


class IbootHandoffContractTests(unittest.TestCase):
    def test_zero_or_empty_direct_run_is_consistent_but_blocked(self) -> None:
        result = verify_handoff_report(_direct_report())
        self.assertTrue(result["valid"])
        self.assertFalse(result["claims"]["xnu_executed"])
        self.assertFalse(result["claims"]["macos_boot_verified"])
        self.assertTrue(any("Darwin/XNU" in blocker for blocker in result["blockers"]))

    def test_marker_complete_fixture_is_only_contract_evidence(self) -> None:
        result = verify_handoff_report(_direct_report(markers=True), expected_target_major=27)
        self.assertTrue(result["valid"])
        self.assertTrue(result["claims"]["xnu_executed"])
        self.assertTrue(result["claims"]["macos_userspace_reached"])
        self.assertTrue(result["claims"]["macos_boot_verified"])
        self.assertEqual(result["mode"], "direct-macos")
        self.assertTrue(all(stage["status"] == StageStatus.VERIFIED.value for stage in result["stages"]))

    def test_positive_boot_claim_without_markers_is_rejected(self) -> None:
        report = _direct_report()
        report["macos_boot_verified"] = True
        with self.assertRaises(HandoffContractError):
            verify_handoff_report(report)

    def test_markers_without_a_started_guest_are_not_a_boot_claim(self) -> None:
        report = _direct_report(markers=True)
        report["runtime_started"] = False
        report["macos_boot_verified"] = False
        result = verify_handoff_report(report)
        self.assertTrue(result["valid"])
        self.assertFalse(result["claims"]["macos_boot_verified"])
        self.assertIn("runtime", " ".join(result["blockers"]))

    def test_positive_observer_markers_cannot_bypass_input_integrity(self) -> None:
        report = _direct_report(markers=True)
        report["input_integrity"] = False
        with self.assertRaises(HandoffContractError):
            verify_handoff_report(report)

    def test_userspace_marker_before_xnu_cannot_be_called_a_handoff(self) -> None:
        report = _direct_report(markers=True)
        observation = report["direct_boot"]["observation"]
        observation["observed_markers"]["xnu"][0]["byte_offset"] = 256
        observation["observed_markers"]["userspace"][0]["byte_offset"] = 16
        report["macos_boot_verified"] = True
        with self.assertRaises(HandoffContractError):
            verify_handoff_report(report)

    def test_negative_marker_offset_is_not_evidence(self) -> None:
        report = _direct_report(markers=True)
        report["direct_boot"]["observation"]["observed_markers"]["xnu"][0]["byte_offset"] = -1
        report["macos_boot_verified"] = True
        with self.assertRaises(HandoffContractError):
            verify_handoff_report(report)

    def test_positive_signature_claim_requires_guest_acceptance_evidence(self) -> None:
        report = _direct_report()
        report["signature_acceptance_verified"] = True
        report["personalization"] = {"ticket_received": True, "payload_preserved": True}
        with self.assertRaisesRegex(HandoffContractError, "guest acceptance"):
            verify_handoff_report(report)

    def test_recovery_chain_stops_at_xnu_after_bootx(self) -> None:
        report: dict[str, object] = {
            "machine_type": "iBoot(AArch64)",
            "guest_os": "macOS",
            "target_major": 27,
            "recovery_inputs_required": True,
            "input_integrity": True,
            "transition": {"state": "ibec-ready"},
            "dfu_upload": {"transfer_complete": True},
            "ibec_executed": True,
            "stage2_execution_observed": True,
            "stage2": {"observed": True},
            "restore_chain_completed": True,
            "restore_chain": {
                "sequence_sent": True,
                "bootx_acknowledged": True,
                "input_integrity": True,
            },
            "xnu_executed": False,
            "macos_boot_verified": False,
        }
        result = verify_handoff_report(report, require_recovery_chain=True)
        self.assertTrue(result["valid"])
        self.assertEqual(result["mode"], "recovery")
        self.assertEqual(result["stages"][0]["status"], StageStatus.VERIFIED.value)
        self.assertEqual(result["stages"][1]["status"], StageStatus.VERIFIED.value)
        self.assertEqual(result["stages"][2]["status"], StageStatus.VERIFIED.value)
        self.assertEqual(result["stages"][3]["status"], StageStatus.BLOCKED.value)
        self.assertFalse(result["claims"]["macos_boot_verified"])

    def test_report_is_json_safe_and_input_is_not_mutated(self) -> None:
        report = _direct_report()
        before = copy.deepcopy(report)
        json.dumps(verify_handoff_report(report))
        self.assertEqual(report, before)

    def test_cli_fixture_verifier_reads_only_a_saved_report(self) -> None:
        # Keep one filesystem-level test for the offline command wrapper.  The
        # report itself is self-authored and does not represent Apple boot.
        from sandbox.efi.verify_iboot_xnu_handoff import verify_file

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(_direct_report()), encoding="utf-8")
            result = verify_file(path)
        self.assertTrue(result["valid"])
        self.assertFalse(result["claims"]["macos_boot_verified"])


if __name__ == "__main__":
    unittest.main()
