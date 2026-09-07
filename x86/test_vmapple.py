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

    def test_storage_seed_view_is_selected_as_read_only_guest_backing(self) -> None:
        from x86.vmapple import Executable, StorageSession

        def qcow_header(size: int) -> bytes:
            header = bytearray(104)
            header[:4] = b"QFI\xfb"
            struct.pack_into(">I", header, 4, 3)
            struct.pack_into(">Q", header, 24, size)
            struct.pack_into(">I", header, 20, 16)
            return bytes(header)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.raw"
            disk = root / "root.raw"
            aux_seed = root / "aux-seed.raw"
            root_seed = root / "root-seed.raw"
            aux_overlay = root / "aux.qcow2"
            root_overlay = root / "root.qcow2"
            aux.write_bytes(b"A" * 1024)
            disk.write_bytes(b"R" * 2048)
            aux_seed.write_bytes(b"S" * 1024)
            root_seed.write_bytes(b"T" * 2048)
            aux_overlay.write_bytes(qcow_header(1024))
            root_overlay.write_bytes(qcow_header(2048))
            session = StorageSession(
                root, aux, disk, aux_overlay, root_overlay, 0,
                aux_seed=aux_seed, root_seed=root_seed,
            )
            arguments = session.arguments(Executable("qemu-system-aarch64"), allow_bdif_writes=False)
            blockdev = [arguments[index + 1] for index, value in enumerate(arguments) if value == "-blockdev"]
            self.assertEqual(len(blockdev), 2)
            self.assertTrue(all(str(seed) in item for seed, item in ((aux_seed, blockdev[0]), (root_seed, blockdev[1]))))
            self.assertTrue(all('"offset":0' in item for item in blockdev))

    def test_cli_parser_exposes_storage_seed_views(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "run", "--research-only",
            "--aux-seed", "/tmp/aux-seed.raw",
            "--root-seed", "/tmp/root-seed.raw",
        ])
        self.assertEqual(parsed.aux_seed, "/tmp/aux-seed.raw")
        self.assertEqual(parsed.root_seed, "/tmp/root-seed.raw")

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

    def test_macosvm_provision_command_is_argv_only(self) -> None:
        from x86.vmapple import Executable, macosvm_provision_command

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = root / "GoldenGate.ipsw"
            output = root / "vm"
            ipsw.write_bytes(b"caller supplied IPSW")
            output.mkdir()
            command = macosvm_provision_command(
                Executable("/usr/local/bin/macosvm"),
                ipsw=ipsw,
                output=output,
                disk_size="64g",
            )
        self.assertEqual(command, [
            "/usr/local/bin/macosvm",
            "--disk", f"{output / 'disk.img'},size=64g",
            "--aux", str(output / "aux.img"),
            "--restore", str(ipsw),
            str(output / "macosvm.json"),
        ])
        self.assertNotIn("shell", command)

        for invalid in ("0g", "32", "5p", "4097g"):
            with self.subTest(invalid=invalid):
                with tempfile.TemporaryDirectory() as invalid_directory:
                    invalid_root = Path(invalid_directory)
                    invalid_ipsw = invalid_root / "GoldenGate.ipsw"
                    invalid_output = invalid_root / "vm"
                    invalid_ipsw.write_bytes(b"caller supplied IPSW")
                    invalid_output.mkdir()
                    with self.assertRaises(ValueError):
                        macosvm_provision_command(
                            Executable("/usr/local/bin/macosvm"),
                            ipsw=invalid_ipsw,
                            output=invalid_output,
                            disk_size=invalid,
                        )

    def test_macosvm_provision_is_host_gated_without_creating_output(self) -> None:
        from x86.vmapple import provision_macosvm

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = root / "GoldenGate.ipsw"
            output = root / "vm"
            ipsw.write_bytes(b"caller supplied IPSW")
            with patch(
                "x86.vmapple.direct_macos_host_report",
                return_value={"apple_silicon_macos": False},
            ):
                with self.assertRaisesRegex(ValueError, "Apple-Silicon macOS"):
                    provision_macosvm(
                        macosvm="/bin/echo", ipsw=ipsw, output=output,
                    )
            self.assertFalse(output.exists())

            output.mkdir()
            with patch(
                "x86.vmapple.direct_macos_host_report",
                return_value={
                    "apple_silicon_macos": True,
                    "default_avpbooter_present": True,
                },
            ):
                with self.assertRaisesRegex(ValueError, "must be new"):
                    provision_macosvm(
                        macosvm="/bin/echo", ipsw=ipsw, output=output,
                    )

    def test_macosvm_provision_runs_new_bundle_and_writes_receipt(self) -> None:
        from x86.vmapple import provision_macosvm

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = root / "GoldenGate.ipsw"
            macosvm = root / "macosvm"
            output = root / "vm"
            ipsw.write_bytes(b"caller supplied IPSW")
            macosvm.write_text(
                "#!/usr/bin/env python3\n"
                "import base64, json, pathlib, plistlib, sys\n"
                "args = sys.argv[1:]\n"
                "aux = pathlib.Path(args[args.index('--aux') + 1])\n"
                "disk = pathlib.Path(args[args.index('--disk') + 1].split(',')[0])\n"
                "vm_json = pathlib.Path(args[-1])\n"
                "aux.write_bytes(b'A' * (0x4000 + 512))\n"
                "disk.write_bytes(b'R' * 512)\n"
                "enc = lambda value: base64.b64encode(plistlib.dumps(value, fmt=plistlib.FMT_BINARY)).decode('ascii')\n"
                "vm_json.write_text(json.dumps({'machineId': enc({'ECID': 42}), 'hardwareModel': enc({'hardware': b'm1'}), 'storage': [{'type': 'aux', 'file': str(aux)}, {'type': 'disk', 'file': str(disk)}]}))\n"
            )
            macosvm.chmod(0o755)
            host = {
                "apple_silicon_macos": True,
                "default_avpbooter_present": True,
                "direct_macos_ready": True,
            }
            with patch("x86.vmapple.direct_macos_host_report", return_value=host):
                report = provision_macosvm(
                    macosvm=macosvm,
                    ipsw=ipsw,
                    output=output,
                    disk_size="1g",
                    timeout=30,
                )
            self.assertTrue(report["provisioning_completed"])
            self.assertEqual(report["vm_bundle"]["uuid"], 42)
            self.assertTrue((output / "provision-report.json").is_file())
            self.assertTrue((output / "macosvm.stdout.log").is_file())
            self.assertTrue((output / "macosvm.stderr.log").is_file())

    def test_macosvm_provision_rejects_ipsw_mutation(self) -> None:
        from x86.vmapple import provision_macosvm

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipsw = root / "GoldenGate.ipsw"
            macosvm = root / "macosvm"
            output = root / "vm"
            ipsw.write_bytes(b"caller supplied IPSW")
            macosvm.write_text(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "import sys\n"
                "Path(sys.argv[sys.argv.index('--restore') + 1]).write_bytes(b'mutated')\n"
            )
            macosvm.chmod(0o755)
            with patch(
                "x86.vmapple.direct_macos_host_report",
                return_value={
                    "apple_silicon_macos": True,
                    "default_avpbooter_present": True,
                },
            ):
                with self.assertRaisesRegex(ValueError, "changed during provisioning"):
                    provision_macosvm(macosvm=macosvm, ipsw=ipsw, output=output)
            self.assertTrue(output.is_dir())
            self.assertFalse((output / "provision-report.json").exists())

    def test_native_macosvm_command_is_ephemeral_and_argv_only(self) -> None:
        from x86.vmapple import Executable, macosvm_run_command

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vm_json = root / "macosvm.json"
            vm_json.write_text("{}")
            pid_file = root / "macosvm.pid"
            command = macosvm_run_command(
                Executable("/usr/local/bin/macosvm"),
                vm_json=vm_json,
                pid_file=pid_file,
                gui=True,
            )
        self.assertEqual(command, [
            "/usr/local/bin/macosvm", "--ephemeral", "--gui", "--pid-file",
            str(pid_file), str(vm_json),
        ])
        self.assertNotIn("shell", command)

    def test_native_macosvm_is_host_gated_before_output_creation(self) -> None:
        from x86.vmapple import run_macosvm_native

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vm_json = root / "macosvm.json"
            with patch(
                "x86.vmapple.native_macosvm_host_report",
                return_value={"apple_silicon_macos": False},
            ):
                with self.assertRaisesRegex(ValueError, "Apple-Silicon macOS"):
                    run_macosvm_native(
                        macosvm="/bin/echo",
                        vm_json=vm_json,
                        output=root / "native-run",
                        research_only=True,
                    )
            self.assertFalse((root / "native-run").exists())

    def test_native_macosvm_rejects_guest_newer_than_host(self) -> None:
        from x86.vmapple import run_macosvm_native

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "x86.vmapple.native_macosvm_host_report",
                return_value={
                    "apple_silicon_macos": True,
                    "macos_major": 26,
                },
            ):
                with self.assertRaisesRegex(ValueError, "host macOS major >= 27"):
                    run_macosvm_native(
                        macosvm="/usr/local/bin/macosvm",
                        vm_json=root / "macosvm.json",
                        output=root / "native-run",
                        target_major=27,
                        research_only=True,
                    )
            self.assertFalse((root / "native-run").exists())

    def test_native_macosvm_launch_records_boot_markers_and_input_integrity(self) -> None:
        from x86.vmapple import run_macosvm_native

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
                "machineId": encode({"ECID": 99}),
                "hardwareModel": encode({"hardware": b"m1"}),
                "storage": [
                    {"type": "aux", "file": "aux.img"},
                    {"type": "disk", "file": "disk.img"},
                ],
            }))
            macosvm = root / "macosvm"
            macosvm.write_text(
                "#!/usr/bin/env python3\n"
                "import os, pathlib, sys, time\n"
                "pid = pathlib.Path(sys.argv[sys.argv.index('--pid-file') + 1])\n"
                "pid.write_text(str(os.getpid()))\n"
                "print('Darwin Kernel Version 27.0', flush=True)\n"
                "print('launchd: userspace ready', flush=True)\n"
                "time.sleep(0.05)\n"
            )
            macosvm.chmod(0o755)
            with patch(
                "x86.vmapple.native_macosvm_host_report",
                return_value={
                    "apple_silicon_macos": True,
                    "native_macosvm_ready": True,
                },
            ):
                report = run_macosvm_native(
                    macosvm=macosvm,
                    vm_json=vm_json,
                    output=root / "native-run",
                    duration=2.0,
                    observation_timeout=2.0,
                    research_only=True,
                )
            self.assertTrue(report["native_runtime_started"])
            self.assertTrue(report["pid_file_observed"])
            self.assertTrue(report["xnu_executed"])
            self.assertTrue(report["macos_userspace_reached"])
            self.assertEqual(report["guest_kernel_major"], 27)
            self.assertTrue(report["guest_target_match"])
            self.assertTrue(report["macos_boot_verified"])
            self.assertTrue(report["input_integrity"])
            self.assertIsNone(report["error"])
            self.assertTrue((root / "native-run" / "macosvm.log").is_file())
            self.assertEqual(aux.read_bytes(), b"A" * (0x4000 + 4096))
            self.assertEqual(disk.read_bytes(), b"R" * 4096)

    def test_cli_parser_exposes_native_macosvm_run(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "run-native", "--research-only", "--vm-json", "/tmp/macosvm.json",
            "--duration", "120", "--observation-timeout", "90", "--gui",
        ])
        self.assertEqual(parsed.vmapple_action, "run-native")
        self.assertEqual(parsed.vm_json, "/tmp/macosvm.json")
        self.assertEqual(parsed.duration, 120.0)
        self.assertEqual(parsed.observation_timeout, 90.0)
        self.assertTrue(parsed.gui)
        self.assertTrue(parsed.research_only)

    def test_cli_parser_exposes_macosvm_provisioning(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "provision", "--ipsw", "/tmp/GoldenGate.ipsw",
            "--output", "/tmp/golden-vm", "--disk-size", "64g",
            "--timeout", "120", "--json",
        ])
        self.assertEqual(parsed.vmapple_action, "provision")
        self.assertEqual(parsed.ipsw, "/tmp/GoldenGate.ipsw")
        self.assertEqual(parsed.output, "/tmp/golden-vm")
        self.assertEqual(parsed.disk_size, "64g")
        self.assertEqual(parsed.timeout, 120.0)
        self.assertTrue(parsed.json)

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
        self.assertEqual(profile["direct_boot_engines"]["qemu_vmapple_max_documented_guest_major"], 12)
        self.assertIn("native_macosvm", profile["direct_boot_engines"])

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

    def test_qemu_command_explicitly_enables_research_graphics(self) -> None:
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
                research_graphics=True,
            )
            command = _command_for(
                config, Executable("qemu-system-aarch64"), EmptyStorage(),
                "/tmp/vmapple.sock", root,
            )
        self.assertIn("vmapple,research-headless=on,research-graphics=on,uuid=0", command)

    def test_qemu_command_can_explicitly_enable_stage2_contract(self) -> None:
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
                research_stage2=True,
            )
            command = _command_for(
                config, Executable("qemu-system-aarch64"), EmptyStorage(),
                "/tmp/vmapple.sock", root,
            )
        self.assertTrue(any("research-headless=on,research-stage2=on,uuid=0" in item for item in command))

    def test_stage2_serial_start_is_execution_evidence_before_panic(self) -> None:
        from x86.vmapple import IBOOT_PANIC_MARKER, STAGE2_PROMPT, _wait_serial_marker

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "serial.log"
            path.write_bytes(
                b"======== Start of iBootStage2 serial output. ========\n"
                + IBOOT_PANIC_MARKER
                + b" test\n"
            )
            result = _wait_serial_marker(path, STAGE2_PROMPT, 1)
        self.assertFalse(result["observed"])
        self.assertTrue(result["panic_observed"])
        self.assertTrue(result["stage2_serial_started"])
        self.assertEqual(result["stage2_serial_start_byte_offset"], 0)

    def test_live_recovery_command_keeps_initial_el1_contract(self) -> None:
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
                live_personalize=True,
            )
            command = _command_for(
                config, Executable("qemu-system-aarch64"), EmptyStorage(),
                "/tmp/vmapple.sock", root,
            )
        self.assertIn("vmapple,research-headless=on,uuid=0", command)
        self.assertFalse(any("research-stage2=on" in item for item in command))

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

    def test_direct_macos_observer_requires_requested_kernel_major(self) -> None:
        from x86.vmapple import _observe_direct_macos_boot

        class ExitedProcess:
            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as directory:
            serial = Path(directory) / "serial.log"
            serial.write_bytes(
                b"Darwin Kernel Version 26.0: root device\n"
                b"launchd: completed\n"
            )
            result = _observe_direct_macos_boot(
                serial, 1.0, ExitedProcess(), expected_kernel_major=27
            )
        self.assertTrue(result["xnu_executed"])
        self.assertTrue(result["macos_userspace_reached"])
        self.assertFalse(result["guest_target_match"])
        self.assertFalse(result["macos_boot_verified"])
        self.assertEqual(result["guest_kernel_majors"], [26])
        self.assertIn("does not match", result["direct_boot_blocker"])

    def test_direct_macos_observer_accepts_long_native_timeout_bound(self) -> None:
        from x86.vmapple import _observe_direct_macos_boot

        class ExitedProcess:
            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as directory:
            serial = Path(directory) / "serial.log"
            serial.write_bytes(b"AVPBooter started\n")
            result = _observe_direct_macos_boot(
                serial, 3601.0, ExitedProcess(), expected_kernel_major=27
            )
        self.assertFalse(result["macos_boot_verified"])
        self.assertIn("Darwin/XNU", result["direct_boot_blocker"])

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
            ), patch("x86.vmapple.QEMU_VMAPPLE_MAX_MACOS_GUEST_MAJOR", 27):
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

    def test_qemu_direct_latest_guest_fails_closed_to_native_macosvm(self) -> None:
        from x86.vmapple import VMappleConfig

        config = VMappleConfig(
            target_major=27,
            qemu="missing",
            firmware="missing",
            ibss="",
            aux="missing",
            root="missing",
            research_only=True,
            boot_selection="macos",
        )
        with self.assertRaisesRegex(ValueError, "run-native"):
            config.validate()

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

    def test_bridge_native_macosvm_worker_uses_native_engine(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        bridge._settings.read = lambda key, default=None: "sandbox"  # type: ignore[method-assign]
        config = {
            "engine": "native-macosvm",
            "macosvm": "/usr/local/bin/macosvm",
            "vm_json": "/Users/test/goldengate/macosvm.json",
            "output": "/Users/test/runs/native",
            "target_major": 27,
            "boot_selection": "macos",
            "boot_picker_trigger": "alt-enter",
            "boot_picker_enabled": True,
            "boot_delay": 2.0,
            "research_only": True,
        }
        fake_process = type("Process", (), {"pid": 4567})()
        with patch(
            "x86.vmapple.native_macosvm_host_report",
            return_value={"apple_silicon_macos": True},
        ), patch("x86.gui.bridge.subprocess.Popen", return_value=fake_process) as popen:
            result = bridge.launch_vmapple(config)
        self.assertTrue(result["ok"])
        self.assertEqual(result["worker"], "native-macosvm")
        command = popen.call_args.args[0]
        self.assertIn("run-native", command)
        self.assertIn("--macosvm", command)
        self.assertIn("/usr/local/bin/macosvm", command)
        self.assertIn("--vm-json", command)
        self.assertIn("/Users/test/goldengate/macosvm.json", command)
        self.assertNotIn("--qemu", command)

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
