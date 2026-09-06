"""Offline checks for the visible VMApple research control plane."""

from __future__ import annotations

import struct
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch
import zlib


class VMappleOfflineTest(unittest.TestCase):
    def test_dfu_suffix_crc_is_deterministic(self) -> None:
        from x86.vmapple import DFU_SUFFIX

        image = b"test-iBSS"
        checksum = zlib.crc32(image + DFU_SUFFIX) ^ 0xFFFFFFFF
        suffix = DFU_SUFFIX + struct.pack("<I", checksum)
        self.assertEqual(len(DFU_SUFFIX), 12)
        self.assertEqual(struct.unpack("<I", suffix[-4:])[0], checksum)

    def test_config_requires_explicit_research_flag(self) -> None:
        from x86.vmapple import VMappleConfig

        config = VMappleConfig(
            target_major=27,
            qemu=None,
            firmware="missing",
            ibss="missing",
            aux="missing",
            root="missing",
            research_only=False,
        )
        with self.assertRaisesRegex(ValueError, r"research[-_]only"):
            config.validate()

    def test_config_rejects_boolean_or_non_finite_timeouts(self) -> None:
        from x86.vmapple import VMappleConfig

        cases = (
            {"transition_timeout": True},
            {"transition_timeout": float("nan")},
            {"duration": False},
            {"duration": float("inf")},
            {"restore_timeout": True},
            {"restore_timeout": float("nan")},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                config = VMappleConfig(
                    target_major=27,
                    qemu=None,
                    firmware="missing",
                    ibss="missing",
                    aux="missing",
                    root="missing",
                    research_only=True,
                    **overrides,
                )
                with self.assertRaisesRegex(ValueError, "timeout|Duration"):
                    config.validate()

    def test_input_integrity_rehashes_files(self) -> None:
        from x86.vmapple import _inputs_intact, _sha256

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.bin"
            path.write_bytes(b"immutable")
            inputs = {"ibss": {"path": str(path), "sha256": _sha256(path)}}
            self.assertTrue(_inputs_intact(inputs))
            path.write_bytes(b"changed")
            self.assertFalse(_inputs_intact(inputs))

    def test_probe_keeps_iBEC_endpoint_when_DFU_controls_stall(self) -> None:
        from x86.vmapple import RecoveryProtocolError, RecoveryTransport

        device = bytes.fromhex("1201000200000040ac052712000002030401")
        configuration = bytes.fromhex(
            "0902190001010580fa0904000000fe01000007050402000200"
        )
        transport = object.__new__(RecoveryTransport)

        def descriptor(kind: int, index: int = 0, length: int = 255) -> bytes:
            if kind == 1:
                return device
            return configuration if length > 9 else configuration[:9]

        transport.descriptor = descriptor  # type: ignore[method-assign]
        transport.control = lambda *args, **kwargs: b""  # type: ignore[method-assign]
        transport.dfu_state = lambda: (_ for _ in ()).throw(  # type: ignore[method-assign]
            RecoveryProtocolError("DFU control request stalled")
        )
        result = transport.probe()
        self.assertEqual(result["bulk_out_endpoint"], 4)
        self.assertEqual(result["configuration_value"], 1)
        self.assertIsNone(result["dfu_state"])
        self.assertIn("dfu_control_error", result)

    def test_cli_parser_exposes_research_only_run(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args(["vmapple", "run", "--research-only"])
        self.assertEqual(parsed.command, "vmapple")
        self.assertEqual(parsed.vmapple_action, "run")
        self.assertTrue(parsed.research_only)

    def test_cli_parser_exposes_boot_picker_selection(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "run", "--research-only",
            "--boot-selection", "recovery",
            "--boot-delay", "2",
            "--boot-picker-trigger", "alt-enter",
        ])
        self.assertEqual(parsed.boot_selection, "recovery")
        self.assertEqual(parsed.boot_delay, 2.0)
        self.assertEqual(parsed.boot_picker_trigger, "alt-enter")
        self.assertTrue(parsed.boot_picker_enabled)

    def test_qemu_command_pins_virtual_m1_metadata(self) -> None:
        from x86.vmapple import Executable, VIRTUAL_MODEL, VIRTUAL_SOC_NAME, VMappleConfig, _command_for

        class EmptyStorage:
            def arguments(self, executable):
                return []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "AVPBooter.bin"
            firmware.write_bytes(b"firmware")
            output = root / "output"
            output.mkdir()
            config = VMappleConfig(
                target_major=27, qemu="qemu", firmware=str(firmware), ibss="",
                aux="aux", root="root", output=str(output), research_only=True,
            )
            command = _command_for(config, Executable("qemu-system-aarch64"), EmptyStorage(),
                                   "/tmp/vmapple.sock", output)
        self.assertIn(f"vmapple-cfg.soc_name={VIRTUAL_SOC_NAME}", command)
        self.assertIn(f"vmapple-cfg.model={VIRTUAL_MODEL}", command)
        self.assertNotIn("vmapple-cfg.optional-rpc-unavailable=on", command)

    def test_qemu_command_only_enables_optional_rpc_when_requested(self) -> None:
        from x86.vmapple import Executable, VMappleConfig, _command_for

        class EmptyStorage:
            def arguments(self, executable):
                return []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "AVPBooter.bin"
            firmware.write_bytes(b"firmware")
            config = VMappleConfig(
                target_major=27, qemu="qemu", firmware=str(firmware), ibss="",
                aux="aux", root="root", output=str(root), research_only=True,
                optional_rpc_unavailable=True,
            )
            command = _command_for(config, Executable("qemu-system-aarch64"), EmptyStorage(),
                                   "/tmp/vmapple.sock", root)
        self.assertIn("vmapple-cfg.optional-rpc-unavailable=on", command)
        self.assertTrue(any("enable=vmapple_optional_rpc_*,file=" in item for item in command))

    def test_bridge_rejects_native_mode_and_unsafe_launch(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "native"  # type: ignore[method-assign]
        result = bridge.launch_vmapple({"research_only": True})
        self.assertFalse(result["ok"])
        self.assertIn("Sandbox", result["error"])

    def test_bridge_spawns_shell_free_native_worker(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "sandbox"  # type: ignore[method-assign]
        config = {
            "qemu": "C:/tools/qemu-system-aarch64.exe",
            "qemu_img": "C:/tools/qemu-img.exe",
            "firmware": "C:/assets/AVPBooter.bin",
            "ibss": "C:/assets/iBSS.img4",
            "ibec": "",
            "aux": "C:/assets/aux.raw",
            "root": "C:/assets/root.raw",
            "output": "C:/runs/vmapple",
            "target_major": 27,
            "display": "gtk",
            "research_only": True,
        }
        fake_process = type("Process", (), {"pid": 1234})()
        with patch("x86.gui.bridge.is_windows", return_value=False), patch(
            "x86.gui.bridge.subprocess.Popen", return_value=fake_process
        ) as popen:
            result = bridge.launch_vmapple(config)
        self.assertTrue(result["ok"])
        self.assertEqual(result["pid"], 1234)
        command = popen.call_args.args[0]
        self.assertNotIn("bash", command)
        self.assertIn("--research-only", command)
        self.assertIn("--display", command)
        self.assertIn("gtk", command)
        self.assertIn("--boot-selection", command)
        self.assertIn("recovery", command)
        self.assertIn("--boot-delay", command)
        self.assertIn("2.0", command)
        self.assertIn("--boot-picker-trigger", command)
        self.assertIn("runner-default-recovery", command)

    def test_bridge_reexecs_linux_qemu_in_wslg(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows bridge path conversion")
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "sandbox"  # type: ignore[method-assign]
        config = {
            "qemu": "/home/developer/qemu-system-aarch64",
            "qemu_img": "/usr/bin/qemu-img",
            "firmware": "C:/assets/AVPBooter.bin",
            "ibss": "C:/assets/iBSS.img4",
            "aux": "C:/assets/aux.raw",
            "root": "C:/assets/root.raw",
            "output": "C:/runs/vmapple-wsl",
            "target_major": 27,
            "display": "gtk",
            "research_only": True,
        }
        fake_process = type("Process", (), {"pid": 5678})()
        with patch("x86.gui.bridge.is_windows", return_value=True), patch(
            "x86.gui.bridge.shutil.which", return_value="wsl.exe"
        ), patch("x86.gui.bridge.subprocess.Popen", return_value=fake_process) as popen:
            result = bridge.launch_vmapple(config)
        self.assertTrue(result["ok"])
        self.assertEqual(result["worker"], "wsl")
        command = popen.call_args.args[0]
        self.assertEqual(command[0], "wsl.exe")
        self.assertIn("--cd", command)
        self.assertIn("--exec", command)
        self.assertIn("python3", command)
        self.assertIn("/mnt/c/assets/iBSS.img4", command)
        self.assertNotIn("bash", command)


if __name__ == "__main__":
    unittest.main()
