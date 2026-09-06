"""Tests for the explicit real VMApple adapter without starting QEMU."""

from __future__ import annotations

import unittest
from unittest.mock import patch


class RealAdapterTest(unittest.TestCase):
    def test_adapter_selects_direct_contract_and_no_recovery_inputs(self) -> None:
        from x86.silicon.real import run_direct_macos

        captured = {}

        def fake_run(config):
            captured["config"] = config
            return {"macos_boot_verified": False, "error": "fixture"}

        with patch("x86.vmapple.run", side_effect=fake_run):
            report = run_direct_macos(
                target_os=27,
                qemu="qemu",
                qemu_img="qemu-img",
                firmware="AVPBooter.bin",
                aux="aux.raw",
                root="root.raw",
                output="out",
                research_only=True,
            )
        config = captured["config"]
        self.assertEqual(config.boot_selection, "macos")
        self.assertFalse(config.live_personalize)
        self.assertFalse(config.restore_chain)
        self.assertEqual(config.ibss, "")
        self.assertEqual(report["layer"].split(" -> ", 1)[0], "Apple Silicon user-space VMApple runner")


if __name__ == "__main__":
    unittest.main()
