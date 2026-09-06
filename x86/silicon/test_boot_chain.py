"""Unit tests for ``x86.silicon.boot_chain``."""

from __future__ import annotations

import unittest
from dataclasses import replace

from x86.silicon.boot_chain import (
    StageStatus,
    assert_never_claims_real_boot,
    simulate_boot_chain,
)


class BootChainTest(unittest.TestCase):
    def test_simulate_boot_chain_stops_at_documented_boundary(self) -> None:
        result = simulate_boot_chain(target_os=26)
        self.assertEqual(result.blocked_at, "macos_guest_abi_boundary")

    def test_xnu_stage_is_always_skipped(self) -> None:
        result = simulate_boot_chain(target_os=26)
        xnu_stage = next(stage for stage in result.stages if stage.id == "xnu_boot")
        self.assertEqual(xnu_stage.status, StageStatus.SKIPPED)

    def test_never_claims_real_boot_passes_on_real_data(self) -> None:
        result = simulate_boot_chain(target_os=26)
        assert_never_claims_real_boot(result)  # must not raise

    def test_guard_raises_if_xnu_stage_is_tampered_to_pass(self) -> None:
        result = simulate_boot_chain(target_os=26)
        tampered_stages = tuple(
            replace(stage, status=StageStatus.PASS) if stage.id == "xnu_boot" else stage
            for stage in result.stages
        )
        tampered = replace(result, stages=tampered_stages)
        with self.assertRaises(RuntimeError):
            assert_never_claims_real_boot(tampered)

    def test_guard_raises_if_abi_boundary_is_tampered_to_pass(self) -> None:
        result = simulate_boot_chain(target_os=26)
        tampered_stages = tuple(
            replace(stage, status=StageStatus.PASS) if stage.id == "macos_guest_abi_boundary" else stage
            for stage in result.stages
        )
        tampered = replace(result, stages=tampered_stages)
        with self.assertRaises(RuntimeError):
            assert_never_claims_real_boot(tampered)

    def test_as_dict_is_json_safe(self) -> None:
        import json

        result = simulate_boot_chain(target_os=26)
        json.dumps(result.as_dict())  # must not raise


if __name__ == "__main__":
    unittest.main()
