"""Deterministic tests for the two-second Alt/Option boot picker."""

from __future__ import annotations

import unittest

from x86.boot_picker import (
    BOOT_DELAY_SECONDS,
    BootPickerError,
    BootPickerSession,
    default_boot_picker_config,
    validate_boot_picker_config,
)


class BootPickerTests(unittest.TestCase):
    def test_default_policy_exposes_macos_and_recovery(self) -> None:
        policy = default_boot_picker_config(target_major=27)
        self.assertTrue(policy["enabled"])
        self.assertEqual(policy["delay_seconds"], BOOT_DELAY_SECONDS)
        self.assertEqual(policy["alt_key"], "Alt")
        self.assertEqual([entry["id"] for entry in policy["entries"]], ["macos", "recovery"])
        self.assertEqual(policy["entries"][1]["recovery_image_name"], "_default.ipsw")

    def test_alt_within_window_shows_picker_and_recovery_can_be_selected(self) -> None:
        session = BootPickerSession(target_major=27)
        armed = session.start(now=100.0)
        self.assertEqual(armed["state"], "armed")
        self.assertEqual(armed["remaining_seconds"], 2.0)

        shown = session.key_event("Option", now=101.0)
        self.assertEqual(shown["state"], "picker")
        self.assertTrue(shown["picker_visible"])
        self.assertEqual(shown["trigger"], "alt")

        moved = session.key_event("ArrowDown", now=101.1)
        self.assertEqual(moved["selected_entry"], "recovery")
        selected = session.key_event("Enter", now=101.2)
        self.assertEqual(selected["state"], "selected")
        self.assertEqual(selected["selection"], "recovery")
        self.assertEqual(selected["trigger"], "alt-enter")

    def test_timeout_selects_normal_macos_and_closes_hotkey_window(self) -> None:
        session = BootPickerSession(target_major=26)
        session.start(now=20.0)
        expired = session.tick(now=20.0 + BOOT_DELAY_SECONDS)
        self.assertEqual(expired["state"], "default")
        self.assertEqual(expired["selection"], "macos")
        self.assertEqual(expired["trigger"], "timeout")
        after = session.key_event("Alt", now=22.1)
        self.assertEqual(after["state"], "default")
        self.assertFalse(after["picker_visible"])

    def test_pointer_selection_requires_a_visible_picker(self) -> None:
        session = BootPickerSession()
        with self.assertRaisesRegex(BootPickerError, "picker to be visible"):
            session.select("recovery", now=0.0)
        session.start(now=0.0)
        session.key_event("Alt", now=0.01)
        selected = session.select("recovery", now=0.02)
        self.assertEqual(selected["selection"], "recovery")
        self.assertEqual(selected["trigger"], "alt-pointer")

    def test_policy_rejects_non_two_second_or_non_alt_configuration(self) -> None:
        with self.assertRaisesRegex(BootPickerError, "fixed at 2"):
            validate_boot_picker_config(delay_seconds=1)
        with self.assertRaisesRegex(BootPickerError, "Alt or Option"):
            validate_boot_picker_config(alt_key="F12")
        with self.assertRaisesRegex(BootPickerError, "Recovery entry"):
            validate_boot_picker_config(recovery_enabled=False)


if __name__ == "__main__":
    unittest.main()
