"""Offline checks for the visible VMApple research control plane."""

from __future__ import annotations

import struct
import tempfile
import unittest
import os
import base64
import json
import hashlib
import plistlib
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

    def test_storage_inspection_identifies_zero_fixture_without_writing(self) -> None:
        from x86.vmapple import inspect_storage

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.raw"
            disk = root / "root.raw"
            aux.write_bytes(b"\0" * 4096)
            disk.write_bytes(b"\0" * 8192)
            before = (aux.read_bytes(), disk.read_bytes())
            report = inspect_storage(aux=aux, root=disk)
            self.assertEqual(report["provisioning_status"], "unprovisioned-zero")
            self.assertFalse(report["provisioned"])
            self.assertFalse(report["installer_ui_possible"])
            self.assertTrue(report["installer_ui_verified"] is False)
            self.assertEqual((aux.read_bytes(), disk.read_bytes()), before)
            self.assertIn("AUX", report["blockers"][0])

    def test_storage_inspection_keeps_nonzero_storage_unverified(self) -> None:
        from x86.vmapple import inspect_storage

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.raw"
            disk = root / "root.raw"
            aux.write_bytes(b"A" * 4096)
            disk.write_bytes(b"\0" * 32 + b"NXSB" + b"B" * 4060)
            report = inspect_storage(aux=aux, root=disk)
            self.assertIsNone(report["provisioned"])
            self.assertEqual(report["provisioning_status"], "unverified")
            self.assertIn("NXSB", report["markers"])
            self.assertIsNone(report["installer_ui_possible"])

    def test_macosvm_json_resolves_ecid_and_storage_atomically(self) -> None:
        from x86.vmapple import VMappleConfig, load_macosvm_configuration

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.img"
            disk = root / "disk.img"
            aux.write_bytes(b"A" * (0x4000 + 4096))
            disk.write_bytes(b"R" * 8192)
            machine_id = base64.b64encode(
                plistlib.dumps({"ECID": 0x1234}, fmt=plistlib.FMT_BINARY)
            ).decode("ascii")
            hardware_model = base64.b64encode(
                plistlib.dumps({"hardware": b"m1"}, fmt=plistlib.FMT_BINARY)
            ).decode("ascii")
            vm_json = root / "macosvm.json"
            vm_json.write_text(json.dumps({
                "machineId": machine_id,
                "hardwareModel": hardware_model,
                "storage": [
                    {"type": "aux", "file": "aux.img"},
                    {"type": "disk", "file": "disk.img"},
                ],
            }))
            bundle = load_macosvm_configuration(vm_json)
            self.assertEqual(bundle.uuid, 0x1234)
            self.assertEqual(bundle.aux, aux.resolve())
            self.assertEqual(bundle.root, disk.resolve())
            config = VMappleConfig(
                target_major=27, qemu="qemu", qemu_img="qemu-img", firmware="firmware",
                ibss="", aux="", root="", vm_json=str(vm_json), research_only=True,
                boot_selection="macos",
            )
            resolved, receipt = config.resolve_vm_configuration()
            self.assertEqual(resolved.uuid, 0x1234)
            self.assertEqual(resolved.aux, str(aux.resolve()))
            self.assertEqual(resolved.root, str(disk.resolve()))
            self.assertEqual(resolved.aux_offset, 0x4000)
            self.assertEqual(receipt["uuid"], 0x1234)
            self.assertEqual(receipt["aux_offset"], 0x4000)
            self.assertEqual(receipt["json_sha256"], hashlib.sha256(vm_json.read_bytes()).hexdigest())

    def test_macosvm_storage_inspection_applies_read_only_aux_trim(self) -> None:
        from x86.vmapple import inspect_macosvm_storage

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.img"
            disk = root / "disk.img"
            aux.write_bytes(b"M" * (0x4000 + 4096))
            disk.write_bytes(b"R" * 8192)
            encode = lambda value: base64.b64encode(
                plistlib.dumps(value, fmt=plistlib.FMT_BINARY)
            ).decode("ascii")
            vm_json = root / "macosvm.json"
            vm_json.write_text(json.dumps({
                "machineId": encode({"ECID": 9}),
                "hardwareModel": encode({"hardware": b"m1"}),
                "storage": [
                    {"type": "disk", "file": "disk.img", "readOnly": False},
                    {"type": "aux", "file": "aux.img", "readOnly": False},
                ],
            }))
            before = (aux.read_bytes(), disk.read_bytes())
            report = inspect_macosvm_storage(vm_json)
            self.assertEqual(report["aux"]["view_offset"], 0x4000)
            self.assertEqual(report["vm_bundle"]["aux_offset"], 0x4000)
            self.assertEqual((aux.read_bytes(), disk.read_bytes()), before)

    def test_macosvm_json_rejects_mismatched_manual_uuid_or_disk(self) -> None:
        from x86.vmapple import VMappleConfig

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.img"
            disk = root / "disk.img"
            other = root / "other.img"
            for path in (aux, disk, other):
                path.write_bytes(b"x" * 4096)
            encode = lambda value: base64.b64encode(
                plistlib.dumps(value, fmt=plistlib.FMT_BINARY)
            ).decode("ascii")
            vm_json = root / "macosvm.json"
            vm_json.write_text(json.dumps({
                "machineId": encode({"ECID": 7}),
                "hardwareModel": encode({"hardware": b"m1"}),
                "storage": [
                    {"type": "aux", "file": "aux.img"},
                    {"type": "disk", "file": "disk.img"},
                ],
            }))
            with self.assertRaisesRegex(ValueError, "uuid conflicts"):
                VMappleConfig(
                    target_major=27, qemu="qemu", qemu_img="qemu-img", firmware="firmware",
                    ibss="", aux="", root="", vm_json=str(vm_json), uuid=8,
                    research_only=True, boot_selection="macos",
                ).resolve_vm_configuration()
            with self.assertRaisesRegex(ValueError, "root conflicts"):
                VMappleConfig(
                    target_major=27, qemu="qemu", qemu_img="qemu-img", firmware="firmware",
                    ibss="", aux="", root=str(other), vm_json=str(vm_json),
                    research_only=True, boot_selection="macos",
                ).resolve_vm_configuration()
            with self.assertRaisesRegex(ValueError, "AUX offset conflicts"):
                VMappleConfig(
                    target_major=27, qemu="qemu", qemu_img="qemu-img", firmware="firmware",
                    ibss="", aux="", root="", vm_json=str(vm_json), aux_offset=512,
                    research_only=True, boot_selection="macos",
                ).resolve_vm_configuration()

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

    def test_cli_parser_exposes_read_only_storage_inspection(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "inspect-storage", "--aux", "aux.raw", "--root", "root.raw",
            "--aux-offset", "0x200",
        ])
        self.assertEqual(parsed.vmapple_action, "inspect-storage")
        self.assertEqual(parsed.aux_offset, 0x200)

    def test_cli_parser_accepts_macosvm_json_for_direct_run(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "run", "--research-only", "--boot-selection", "macos",
            "--vm-json", "/tmp/macosvm.json",
        ])
        self.assertEqual(parsed.vm_json, "/tmp/macosvm.json")

    def test_apple_silicon_profile_keeps_t8030_as_macOS_safe_reference(self) -> None:
        from x86.vmapple import apple_silicon_profile

        profile = apple_silicon_profile()
        self.assertEqual(profile["schema"], "26x86.vmapple-apple-silicon/1")
        self.assertEqual(profile["machine_type"], "iBoot(AArch64)")
        self.assertEqual(profile["guest_os"], "macOS")
        self.assertEqual(profile["reference"]["name"], "qemu-t8030")
        self.assertEqual(profile["reference"]["guest_scope"], "iPhone 11 / iOS")
        self.assertEqual(profile["interrupt_controller"]["sandbox_contract"], "AIC")
        self.assertEqual(profile["interrupt_controller"]["current_vmapple_qemu"], "GICv3")
        self.assertFalse(profile["scope"]["ios_code_imported"])
        self.assertEqual(profile["scope"]["supported_guest_os"], ["macOS"])
        self.assertIn("iOS", profile["scope"]["unsupported_guest_os"])
        self.assertFalse(profile["claims"]["macos_boot_verified"])

    def test_apple_silicon_profile_returns_independent_data(self) -> None:
        from x86.vmapple import apple_silicon_profile

        first = apple_silicon_profile()
        first["device_topology"][0]["status"] = "mutated"
        second = apple_silicon_profile()
        self.assertEqual(second["device_topology"][0]["status"], "required-gap")

    def test_cli_parser_exposes_apple_silicon_capabilities(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args(["vmapple", "capabilities"])
        self.assertEqual(parsed.command, "vmapple")
        self.assertEqual(parsed.vmapple_action, "capabilities")

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

    def test_direct_macos_command_can_select_native_hvf_on_arm_mac(self) -> None:
        from x86.vmapple import Executable, VMappleConfig, _command_for

        class EmptyStorage:
            def arguments(self, executable, **kwargs):
                return []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "AVPBooter.bin"
            firmware.write_bytes(b"firmware")
            config = VMappleConfig(
                target_major=27, qemu="qemu", firmware=str(firmware), ibss="",
                aux="aux", root="root", output=str(root), research_only=True,
                boot_selection="macos",
            )
            with patch("x86.vmapple._direct_macos_hvf_host", return_value=True):
                command = _command_for(config, Executable("qemu-system-aarch64"), EmptyStorage(),
                                       "/tmp/vmapple.sock", root)
        self.assertIn("vmapple,uuid=0", command)
        self.assertIn("hvf", command)
        self.assertIn("host", command)
        self.assertNotIn("research-headless=on", command)
        self.assertNotIn("vmapple-bdif.usbdev=vusb", command)
        self.assertFalse(any(item.startswith("socket,id=vusb") for item in command))

    def test_direct_macos_observer_requires_xnu_and_userspace_evidence(self) -> None:
        from x86.vmapple import _observe_direct_macos_boot

        class ExitedProcess:
            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as directory:
            serial = Path(directory) / "serial.log"
            serial.write_bytes(
                b"iBoot direct entry\n"
                b"Darwin Kernel Version 27.0: root device\n"
                b"launchd: completed\nWindowServer ready\n"
            )
            result = _observe_direct_macos_boot(serial, 1.0, ExitedProcess())
        self.assertTrue(result["xnu_executed"])
        self.assertTrue(result["macos_userspace_reached"])
        self.assertTrue(result["macos_boot_verified"])
        self.assertIsNone(result["direct_boot_blocker"])
        self.assertGreaterEqual(len(result["observed_markers"]["xnu"]), 1)
        self.assertGreaterEqual(len(result["observed_markers"]["userspace"]), 1)

    def test_direct_macos_observer_keeps_missing_xnu_fail_closed(self) -> None:
        from x86.vmapple import _observe_direct_macos_boot

        class ExitedProcess:
            def poll(self):
                return 1

        with tempfile.TemporaryDirectory() as directory:
            serial = Path(directory) / "serial.log"
            serial.write_bytes(b"AVPBooter started\n")
            result = _observe_direct_macos_boot(serial, 1.0, ExitedProcess())
        self.assertFalse(result["xnu_executed"])
        self.assertFalse(result["macos_boot_verified"])
        self.assertIn("Darwin/XNU", result["direct_boot_blocker"])

    def test_direct_macos_validation_does_not_require_ibss(self) -> None:
        from x86.vmapple import Executable, MACOS_ENTRY_ID, VMappleConfig

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "AVPBooter.bin"
            aux = root / "aux.raw"
            disk = root / "root.raw"
            firmware.write_bytes(b"firmware")
            aux.write_bytes(b"A" * 512)
            disk.write_bytes(b"R" * 512)
            with patch(
                "x86.vmapple._resolve_executable",
                side_effect=[Executable("qemu-system-aarch64"), Executable("qemu-img")],
            ):
                config = VMappleConfig(
                    target_major=27,
                    qemu=None,
                    firmware=str(firmware),
                    ibss="",
                    aux=str(aux),
                    root=str(disk),
                    research_only=True,
                    boot_selection=MACOS_ENTRY_ID,
                )
                qemu, qemu_img, paths = config.validate()
        self.assertEqual(qemu.program, "qemu-system-aarch64")
        self.assertEqual(qemu_img.program, "qemu-img")
        self.assertNotIn("ibss", paths)

    def test_direct_macos_rejects_recovery_personalization(self) -> None:
        from x86.vmapple import VMappleConfig, MACOS_ENTRY_ID

        config = VMappleConfig(
            target_major=27,
            qemu=None,
            firmware="missing",
            ibss="missing",
            aux="missing",
            root="missing",
            research_only=True,
            boot_selection=MACOS_ENTRY_ID,
            live_personalize=True,
        )
        with self.assertRaisesRegex(ValueError, "recovery-only"):
            config.validate()

    def test_direct_macos_host_report_never_confuses_tcg_with_hvf(self) -> None:
        from x86.vmapple import direct_macos_host_report

        report = direct_macos_host_report()
        self.assertIn("apple_silicon_macos", report)
        self.assertTrue(report["hvf_required"])
        if not report["apple_silicon_macos"]:
            self.assertFalse(report["direct_macos_ready"])
            self.assertTrue(report["blockers"])

    def test_auto_display_is_headless_on_non_native_host(self) -> None:
        from x86.vmapple import _effective_display_backend

        with patch("x86.vmapple._direct_macos_hvf_host", return_value=False):
            self.assertEqual(
                _effective_display_backend("auto", direct_macos=True, available=["none", "dbus"]),
                "none",
            )

    def test_auto_display_prefers_cocoa_on_native_arm_mac(self) -> None:
        from x86.vmapple import _effective_display_backend

        with patch("x86.vmapple._direct_macos_hvf_host", return_value=True):
            self.assertEqual(
                _effective_display_backend("auto", direct_macos=True, available=["cocoa", "none"]),
                "cocoa",
            )

    def test_unpatched_qemu_command_omits_unknown_bdif_write_property(self) -> None:
        from x86.vmapple import Executable, VMappleConfig, _command_for

        class EmptyStorage:
            def arguments(self, executable, **kwargs):
                self.kwargs = kwargs
                return []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "AVPBooter.bin"
            firmware.write_bytes(b"firmware")
            storage = EmptyStorage()
            config = VMappleConfig(
                target_major=27,
                qemu="qemu",
                firmware=str(firmware),
                ibss="",
                aux="aux",
                root="root",
                output=str(root),
                research_only=True,
                boot_selection="macos",
                display="auto",
            )
            command = _command_for(
                config,
                Executable("qemu-system-aarch64"),
                storage,
                "/tmp/vmapple.sock",
                root,
                bdif_block_writes=False,
            )
        self.assertFalse(storage.kwargs["allow_bdif_writes"])
        self.assertNotIn("vmapple-bdif.allow-block-writes=on", command)
        self.assertIn("none", command)

    def test_bridge_rejects_native_mode_and_unsafe_launch(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "native"  # type: ignore[method-assign]
        result = bridge.launch_vmapple({"research_only": True})
        self.assertFalse(result["ok"])
        self.assertIn("Sandbox", result["error"])

    def test_bridge_storage_preflight_is_read_only(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.raw"
            disk = root / "root.raw"
            aux.write_bytes(b"\0" * 4096)
            disk.write_bytes(b"\0" * 4096)
            result = bridge.inspect_vmapple_storage({"aux": str(aux), "root": str(disk)})
        self.assertTrue(result["ok"])
        self.assertEqual(result["provisioning_status"], "unprovisioned-zero")

    def test_bridge_storage_preflight_accepts_macosvm_bundle(self) -> None:
        from x86.gui.bridge import WizardBridge

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.img"
            disk = root / "disk.img"
            aux.write_bytes(b"A" * (0x4000 + 4096))
            disk.write_bytes(b"R" * 4096)
            encode = lambda value: base64.b64encode(
                plistlib.dumps(value, fmt=plistlib.FMT_BINARY)
            ).decode("ascii")
            vm_json = root / "macosvm.json"
            vm_json.write_text(json.dumps({
                "machineId": encode({"ECID": 11}),
                "hardwareModel": encode({"hardware": b"m1"}),
                "storage": [
                    {"type": "aux", "file": "aux.img"},
                    {"type": "disk", "file": "disk.img"},
                ],
            }))
            result = WizardBridge().inspect_vmapple_storage({"vm_json": str(vm_json)})
        self.assertTrue(result["ok"])
        self.assertEqual(result["aux"]["view_offset"], 0x4000)

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

    def test_bridge_direct_macos_worker_does_not_require_ibss(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "sandbox"  # type: ignore[method-assign]
        config = {
            "qemu": "C:/tools/qemu-system-aarch64.exe",
            "qemu_img": "C:/tools/qemu-img.exe",
            "firmware": "C:/assets/AVPBooter.bin",
            "aux": "C:/assets/aux.raw",
            "root": "C:/assets/root.raw",
            "output": "C:/runs/vmapple-direct",
            "target_major": 27,
            "display": "gtk",
            "research_only": True,
            "boot_selection": "macos",
        }
        fake_process = type("Process", (), {"pid": 2345})()
        with patch("x86.gui.bridge.is_windows", return_value=False), patch(
            "x86.gui.bridge.subprocess.Popen", return_value=fake_process
        ) as popen:
            result = bridge.launch_vmapple(config)
        self.assertTrue(result["ok"])
        command = popen.call_args.args[0]
        self.assertIn("--boot-selection", command)
        self.assertIn("macos", command)
        self.assertNotIn("--ibss", command)

    def test_bridge_direct_macos_worker_accepts_vm_json_without_manual_storage(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "sandbox"  # type: ignore[method-assign]
        config = {
            "qemu": "C:/tools/qemu-system-aarch64.exe",
            "qemu_img": "C:/tools/qemu-img.exe",
            "firmware": "C:/assets/AVPBooter.bin",
            "vm_json": "C:/assets/macosvm.json",
            "output": "C:/runs/vmapple-direct",
            "target_major": 27,
            "display": "gtk",
            "research_only": True,
            "boot_selection": "macos",
        }
        fake_process = type("Process", (), {"pid": 3456})()
        with patch("x86.gui.bridge.is_windows", return_value=False), patch(
            "x86.gui.bridge.subprocess.Popen", return_value=fake_process
        ) as popen:
            result = bridge.launch_vmapple(config)
        self.assertTrue(result["ok"])
        command = popen.call_args.args[0]
        self.assertIn("--vm-json", command)
        self.assertNotIn("--aux", command)
        self.assertNotIn("--root", command)

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
