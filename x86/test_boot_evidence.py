"""Tests for conservative iBoot/XNU/userspace UART evidence."""

from __future__ import annotations

import unittest


class BootEvidenceTests(unittest.TestCase):
    def test_full_chain_requires_real_markers_and_target_match(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        data = (
            b"Supervisor iBootStage2 for vma2\n"
            b"Entering iBootStage2 recovery mode, starting command prompt\n"
            b"Darwin Kernel Version 27.0.0: root:xnu\n"
            b"launchd: started\n"
        )
        report = parse_uart_evidence(data, expected_kernel_major=27)
        self.assertTrue(report["iboot_stage2_verified"])
        self.assertTrue(report["iboot_to_xnu_handoff_verified"])
        self.assertTrue(report["xnu_executed"])
        self.assertTrue(report["macos_userspace_reached"])
        self.assertTrue(report["macos_boot_verified"])
        self.assertEqual(report["observed_markers"]["iboot_stage2"][0]["byte_offset"], 0)

    def test_iBoot_ack_or_process_exit_cannot_become_boot_evidence(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        report = parse_uart_evidence(b"ACK\nQEMU exited with code 0\niBoot-7459.141.1\n")
        self.assertFalse(report["iboot_executed"])
        self.assertFalse(report["xnu_executed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertIn("iBoot Stage1/Stage2", report["direct_boot_blocker"])

    def test_xnu_without_userspace_stays_incomplete(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        report = parse_uart_evidence(
            b"Supervisor iBootStage2\nDarwin Kernel Version 26.1.0: root:xnu\n",
            expected_kernel_major=26,
        )
        self.assertTrue(report["xnu_executed"])
        self.assertFalse(report["macos_userspace_reached"])
        self.assertFalse(report["macos_boot_verified"])

    def test_stage2_serial_banner_counts_as_execution_but_not_handoff(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        report = parse_uart_evidence(
            b"======== Start of iBootStage2 serial output. ========\n"
            b"iBoot Panic: : 9dd7a41e3b2bbad:221\n"
        )
        self.assertTrue(report["iboot_executed"])
        self.assertTrue(report["iboot_stage2_verified"])
        self.assertFalse(report["iboot_to_xnu_handoff_verified"])
        self.assertFalse(report["xnu_executed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertIn("no Darwin/XNU", report["direct_boot_blocker"])

    def test_target_mismatch_is_not_silently_accepted(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        report = parse_uart_evidence(
            b"Supervisor iBootStage2\nDarwin Kernel Version 26.1.0: root:xnu\nlaunchd: started\n",
            expected_kernel_major=27,
        )
        self.assertFalse(report["guest_target_match"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertIn("mismatch", report["direct_boot_blocker"])

    def test_userspace_marker_before_xnu_is_not_a_handoff(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        report = parse_uart_evidence(
            b"Supervisor iBootStage2\nlaunchd: stale text\n"
            b"Darwin Kernel Version 27.1.0: root:xnu\n",
            expected_kernel_major=27,
        )
        self.assertFalse(report["xnu_to_userspace_handoff_verified"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertIn("preceded", report["direct_boot_blocker"])

    def test_invalid_target_is_rejected(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        with self.assertRaises(ValueError):
            parse_uart_evidence(b"", expected_kernel_major=0)

    def test_windowserver_alone_is_not_acceleration(self) -> None:
        from x86.boot_evidence import parse_graphics_evidence

        report = parse_graphics_evidence(b"WindowServer started\nsoftware renderer\n")
        self.assertTrue(report["windowserver_reached"])
        self.assertFalse(report["graphics_acceleration_verified"])
        self.assertIn("accelerator provider", report["blocker"])

    def test_graphics_requires_provider_and_metal_device(self) -> None:
        from x86.boot_evidence import parse_graphics_evidence

        report = parse_graphics_evidence(
            b"WindowServer started\nIOAccelerator: AGX\n"
        )
        self.assertFalse(report["graphics_acceleration_verified"])
        self.assertIn("Metal device", report["blocker"])

    def test_graphics_gate_and_presented_frame(self) -> None:
        from x86.boot_evidence import parse_uart_evidence

        report = parse_uart_evidence(
            b"Supervisor iBootStage2\nDarwin Kernel Version 27.0.0: root:xnu\n"
            b"launchd: started\nWindowServer started\n"
            b"AppleGPUWrangler: attached\nMTLDevice: Apple GPU\n"
            b"CAMetalLayer drawable: framebuffer presented\n",
            expected_kernel_major=27,
        )
        self.assertTrue(report["graphics"]["graphics_acceleration_verified"])
        self.assertTrue(report["graphics"]["rendered_frame_verified"])


if __name__ == "__main__":
    unittest.main()
