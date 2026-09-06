"""Policy-level tests for the macOS-only iBoot(AArch64) personality."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from unittest.mock import patch

from x86.iboot_personality import (
    DEFAULT_RECOVERY_IMAGE,
    IBOOT_MACHINE_TYPE,
    IbootScopeError,
    policy_matrix,
    validate_iboot_scope,
)
from x86.sandbox_config import default_config, validate


class IbootPersonalityTests(unittest.TestCase):
    def test_explicit_matrix_is_macos_only(self) -> None:
        self.assertEqual(
            policy_matrix(),
            [
                {"machine_type": IBOOT_MACHINE_TYPE, "guest_os": "macOS", "supported": True},
                {"machine_type": IBOOT_MACHINE_TYPE, "guest_os": "iOS", "supported": False},
                {"machine_type": IBOOT_MACHINE_TYPE, "guest_os": "iPadOS", "supported": False},
            ],
        )

    def test_macos_targets_and_recovery_scope_are_accepted(self) -> None:
        result = validate_iboot_scope(
            target_major=27,
            recovery_protocol="DFU/IPSW",
            recovery_image_name=DEFAULT_RECOVERY_IMAGE,
        )
        self.assertTrue(result["guest_os_supported"])
        self.assertEqual(result["guest_os"], "macOS")
        self.assertEqual(result["recovery"]["supported_protocols"], ["DFU", "IPSW"])
        self.assertTrue(result["recovery"]["dfu_macos_recovery"])
        self.assertTrue(result["recovery"]["ipsw_macos_recovery"])

    def test_mobile_guest_is_rejected_before_vmapple_input_validation(self) -> None:
        from x86.vmapple import VMappleConfig

        config = VMappleConfig(
            target_major=27,
            qemu="missing-qemu",
            firmware="missing-firmware",
            ibss="missing-ibss",
            aux="missing-aux",
            root="missing-root",
            guest_os="iOS",
            research_only=True,
        )
        with self.assertRaises(IbootScopeError) as raised:
            config.validate()
        self.assertEqual(raised.exception.code, "VF_GUEST_SCOPE_VIOLATION")

    def test_ipados_and_fastboot_are_rejected(self) -> None:
        for guest in ("iOS", "iPadOS"):
            with self.subTest(guest=guest), self.assertRaises(IbootScopeError):
                validate_iboot_scope(guest_os=guest)
        with self.assertRaises(IbootScopeError) as raised:
            validate_iboot_scope(recovery_protocol="Fastboot")
        self.assertEqual(raised.exception.code, "VF_RECOVERY_SCOPE_VIOLATION")

    def test_non_default_local_recovery_image_is_rejected(self) -> None:
        with self.assertRaises(IbootScopeError) as raised:
            validate_iboot_scope(recovery_image_name="ios-restore.ipsw")
        self.assertEqual(raised.exception.code, "VF_RECOVERY_IMAGE_SCOPE_VIOLATION")

    def test_sandbox_config_records_and_enforces_policy(self) -> None:
        config = default_config(27)
        result = validate(config)
        self.assertTrue(result["ok"])
        self.assertEqual(result["machine_type"], IBOOT_MACHINE_TYPE)
        self.assertEqual(result["guest_os_policy"], "macOS-only")
        self.assertEqual(result["recovery"]["default_image_name"], DEFAULT_RECOVERY_IMAGE)

        config["Venfire"]["GuestOS"] = "iPadOS"
        result = validate(config)
        self.assertFalse(result["ok"])
        self.assertTrue(any("VF_GUEST_SCOPE_VIOLATION" in item for item in result["errors"]))

        config = default_config(27)
        config["Venfire"]["MachineType"] = None
        result = validate(config)
        self.assertFalse(result["ok"])
        self.assertTrue(any("VF_MACHINE_PERSONALITY_MISMATCH" in item for item in result["errors"]))

    def test_cli_personality_returns_a_structured_rejection(self) -> None:
        from x86.cli import main

        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = main(["personality", "validate", "--guest-os", "iOS"])
        self.assertEqual(code, 2)
        payload = json.loads(captured.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["policy_error"]["code"], "VF_GUEST_SCOPE_VIOLATION")

    def test_gui_bridge_rejects_mobile_guest_before_worker_spawn(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "sandbox"  # type: ignore[method-assign]
        with patch("x86.gui.bridge.subprocess.Popen") as popen:
            result = bridge.launch_vmapple({"guest_os": "iPadOS", "research_only": True})
        self.assertFalse(result["ok"])
        self.assertEqual(result["policy_error"]["code"], "VF_GUEST_SCOPE_VIOLATION")
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
