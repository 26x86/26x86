"""Offline and binary-level checks for the non-Apple VMApple TCG layer."""

from __future__ import annotations

import json
from pathlib import Path
import struct
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


class VMappleTCGTests(unittest.TestCase):
    def test_positive_tcg_observer_markers_cannot_bypass_handoff_gate(self) -> None:
        from x86.vmapple import _apply_iboot_xnu_handoff_gate

        report = {
            "schema": "26x86.vmapple-tcg/1",
            "machine_type": "iBoot(AArch64)",
            "guest_os": "macOS",
            "target_major": 27,
            "input_integrity": False,
            "xnu_executed": True,
            "macos_userspace_reached": True,
            "guest_kernel_major": 27,
            "guest_target_match": True,
            "macos_boot_verified": True,
            "direct_boot": {
                "requested": True,
                "selection": "macos",
                "dfu_entered": False,
                "observation": {
                    "xnu_executed": True,
                    "macos_userspace_reached": True,
                    "guest_kernel_major": 27,
                    "guest_target_match": True,
                    "observed_markers": {
                        "xnu": [{"marker": "Darwin Kernel Version", "byte_offset": 10}],
                        "userspace": [{"marker": "launchd:", "byte_offset": 100}],
                    },
                },
            },
        }
        handoff = _apply_iboot_xnu_handoff_gate(report)
        self.assertFalse(handoff["valid"])
        self.assertFalse(report["macos_boot_verified"])

    def test_command_explicitly_selects_headless_tcg_and_virtual_identity(self) -> None:
        from x86.vmapple import Executable
        from x86.vmapple_tcg import _tcg_command

        class Storage:
            def arguments(self, executable, *, allow_bdif_writes):
                self.allow_bdif_writes = allow_bdif_writes
                return ["-global", "vmapple-bdif.allow-block-writes=on"]

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            firmware = output / "AVPBooter.vmapple2.bin"
            firmware.write_bytes(b"caller-supplied fixture")
            storage = Storage()
            command = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=0x1234),
                storage=storage,
                firmware=firmware,
                output=output,
                memory_mib=4096,
                smp=2,
                display="none",
                allow_bdif_writes=True,
            )
        self.assertIn("vmapple,research-headless=on,research-graphics=off,uuid=4660", command)
        self.assertIn("tcg,thread=single", command)
        self.assertIn("max,pauth=on,pauth-qarma5=on,cntfrq=24000000", command)
        self.assertEqual(command.count("-display"), 1)
        self.assertEqual(storage.allow_bdif_writes, True)
        self.assertIn("vmapple-cfg.soc_name=Apple M1 (Virtual)", command)
        self.assertIn("vmapple-cfg.model=VM0001", command)

    def test_stage2_command_maps_unavailable_optional_rpc_window(self) -> None:
        from x86.vmapple import Executable
        from x86.vmapple_tcg import _tcg_command

        class Storage:
            def arguments(self, executable, *, allow_bdif_writes):
                return []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            firmware = output / "iboot-stage2.bin"
            firmware.write_bytes(b"stage2 fixture")
            command = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=1),
                storage=Storage(),
                firmware=firmware,
                output=output,
                memory_mib=4096,
                smp=2,
                display="none",
                allow_bdif_writes=False,
                firmware_kind="iboot-stage2",
                optional_rpc_unavailable=True,
            )

        self.assertIn("research-stage2=on", command[command.index("-M") + 1])
        self.assertIn("vmapple-cfg.optional-rpc-unavailable=on", command)

    def test_command_uses_one_log_sink_for_execution_and_psci(self) -> None:
        from x86.vmapple import Executable
        from x86.vmapple_tcg import _tcg_command

        class Storage:
            def arguments(self, executable, *, allow_bdif_writes):
                return []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            firmware = output / "AVPBooter.bin"
            firmware.write_bytes(b"firmware")
            debug_trace = output / "qemu.debug.log"
            psci_trace = debug_trace
            command = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=1),
                storage=Storage(),
                firmware=firmware,
                output=output,
                memory_mib=4096,
                smp=2,
                display="none",
                allow_bdif_writes=False,
                debug_trace=debug_trace,
                psci_trace=psci_trace,
            )
            psci_only = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=1), storage=Storage(), firmware=firmware,
                output=output, memory_mib=4096, smp=2, display="none",
                allow_bdif_writes=False, psci_trace=psci_trace,
            )
            with self.assertRaisesRegex(ValueError, "one shared debug/PSCI trace path"):
                _tcg_command(
                    executable=Executable("qemu-system-aarch64"),
                    bundle=SimpleNamespace(uuid=1), storage=Storage(), firmware=firmware,
                    output=output, memory_mib=4096, smp=2, display="none",
                    allow_bdif_writes=False, debug_trace=debug_trace,
                    psci_trace=output / "misleading-separate.trace",
                )

        self.assertEqual(command.count("-D"), 1)
        self.assertEqual(command[command.index("-D") + 1], str(debug_trace))
        trace_index = command.index("-trace")
        self.assertEqual(command[trace_index + 1], "enable=arm_psci_call")
        self.assertIn("guest_errors,unimp,exec", command)
        self.assertEqual(psci_only[psci_only.index("-D") + 1], str(psci_trace))
        self.assertEqual(psci_only[psci_only.index("-d") + 1], "guest_errors,unimp")

    def test_psci_trace_parser_classifies_system_reset_without_boot_promotion(self) -> None:
        from x86.vmapple_tcg import _psci_trace_evidence

        trace = (
            "arm_psci_call: PSCI Call x0=0x0000000084000003 "
            "x1=0x0000000000000001 x2=0x0000000000000002 "
            "x3=0x0000000000000003 cpuid=0x0\n"
            "arm_psci_call: PSCI Call x0=0x00000000c4000009 "
            "x1=0x0000000000000000 x2=0x0000000000000000 "
            "x3=0x0000000000000000 cpuid=0x1\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arm_psci_call.trace"
            path.write_bytes(trace)
            evidence = _psci_trace_evidence(path)

        self.assertEqual(evidence["call_count"], 2)
        self.assertTrue(evidence["guest_reset_requested"])
        self.assertEqual(evidence["calls"][0]["function_id"], "0x84000003")
        self.assertFalse(evidence["calls"][0]["reset_requested"])
        self.assertTrue(evidence["calls"][1]["reset_requested"])
        self.assertIn("no XNU/userspace/macOS promotion", evidence["evidence_policy"])

    def test_trace_samples_are_bounded_without_truncating_original(self) -> None:
        from x86.vmapple_tcg import (
            _MAX_PSCI_TRACE_BYTES,
            _bound_trace_file,
            _psci_trace_evidence,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arm_psci_call.trace"
            path.write_bytes(b"x" * (_MAX_PSCI_TRACE_BYTES + 17))
            evidence = _psci_trace_evidence(path)
            retention = _bound_trace_file(path)
            original_size = path.stat().st_size
            sample_size = sum(Path(item["path"]).stat().st_size for item in retention["samples"])

        self.assertEqual(evidence["trace_bytes"], _MAX_PSCI_TRACE_BYTES + 17)
        self.assertEqual(evidence["trace_bytes_observed"], _MAX_PSCI_TRACE_BYTES)
        self.assertTrue(evidence["trace_truncated"])
        self.assertEqual(original_size, _MAX_PSCI_TRACE_BYTES + 17)
        self.assertEqual(sample_size, _MAX_PSCI_TRACE_BYTES)
        self.assertEqual(retention["trace_bytes"], original_size)
        self.assertEqual(retention["samples"][-1]["offset"], original_size - _MAX_PSCI_TRACE_BYTES // 2)
        self.assertTrue(retention["source_preserved"])

    def test_large_shared_log_keeps_first_last_pc_and_psci_reset_at_tail(self) -> None:
        from x86.vmapple_tcg import (
            _MAX_EXEC_TRACE_BYTES, _MAX_PSCI_TRACE_BYTES,
            _qemu_execution_evidence, _psci_trace_evidence,
        )

        first = b"Trace 0: 0x1 [100000000000/0000000000100000/000004a1/ff020000] \n"
        last = b"Trace 1: 0x2 [100800204408/00000001fc000000/00000671/ff020000] \n"
        reset = (
            b"arm_psci_call: PSCI Call x0=0x84000009 x1=0x0 x2=0x0 x3=0x0 cpuid=0x0\n"
        )
        trace = first + b"padding\n" * (_MAX_EXEC_TRACE_BYTES // 8 + 50) + last + reset
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.debug.log"
            path.write_bytes(trace)
            # A parser that reads the complete file before slicing regresses
            # memory bounds even if its eventual sample size looks correct.
            with patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded trace read")):
                execution = _qemu_execution_evidence(path, firmware_kind="iboot-stage2")
                psci = _psci_trace_evidence(path)

        self.assertEqual(execution["trace_path"], psci["trace_path"])
        for evidence, maximum in ((execution, _MAX_EXEC_TRACE_BYTES), (psci, _MAX_PSCI_TRACE_BYTES)):
            self.assertEqual(evidence["trace_bytes"], len(trace))
            self.assertEqual(evidence["trace_bytes_observed"], maximum)
            self.assertTrue(evidence["trace_truncated"])
            self.assertEqual(evidence["trace_sample_ranges"][-1]["offset"], len(trace) - maximum // 2)
            self.assertIn("sampled lines", evidence["count_scope"])
        self.assertTrue(execution["stage2_execution_observed"])
        self.assertTrue(execution["high_ram_relocation_observed"])
        self.assertEqual(execution["first_guest_pc"], "0x100000")
        self.assertEqual(execution["last_guest_pc"], "0x1fc000000")
        self.assertEqual(execution["first_guest_pc_byte_offset"], 0)
        self.assertEqual(execution["last_guest_pc_byte_offset"], trace.index(last))
        self.assertEqual(execution["translation_block_count"], 2)
        self.assertEqual(psci["call_count"], 1)
        self.assertTrue(psci["guest_reset_requested"])
        self.assertEqual(psci["calls"][0]["byte_offset"], trace.index(reset))
        self.assertIn("no XNU/userspace/macOS promotion", psci["evidence_policy"])

    def test_trace_samples_discard_cut_lines_without_joining_ranges(self) -> None:
        from x86.vmapple_tcg import _trace_lines

        head = b"first\nTrace 0: 0x1 [0/0000000000100000/"
        tail = b"000004a1/ff020000]\nlast\n"
        lines = list(_trace_lines([(0, head), (1000, tail)], 1000 + len(tail)))
        self.assertEqual(lines, [(0, b"first\n"), (1000 + tail.index(b"last"), b"last\n")])

    def test_qemu_stderr_parser_classifies_guest_crash_loaded_only(self) -> None:
        from x86.vmapple_tcg import _qemu_stderr_evidence

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.stderr.log"
            path.write_bytes(b"pvpanic: Guest crash loaded\n")
            evidence = _qemu_stderr_evidence(path)

        self.assertTrue(evidence["guest_crash_loaded_observed"])
        self.assertIn("no XNU/userspace/macOS promotion", evidence["evidence_policy"])

    def test_command_has_one_display_and_preserves_qcow2_and_raw_seed_graph(self) -> None:
        from x86.vmapple import Executable, StorageSession
        from x86.vmapple_tcg import _tcg_command

        def qcow_header(size: int) -> bytes:
            header = bytearray(104)
            header[:4] = b"QFI\xfb"
            struct.pack_into(">I", header, 4, 3)
            struct.pack_into(">I", header, 20, 16)
            struct.pack_into(">Q", header, 24, size)
            return bytes(header)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            output.mkdir()
            aux = root / "aux.raw"
            root_image = root / "root.raw"
            aux_seed = root / "aux-seed.qcow2"
            root_seed = root / "root-seed.raw"
            aux_overlay = root / "aux-overlay.qcow2"
            root_overlay = root / "root-overlay.qcow2"
            firmware = root / "AVPBooter.bin"
            aux.write_bytes(b"A" * (0x200 + 1024))
            root_image.write_bytes(b"R" * 2048)
            aux_seed.write_bytes(qcow_header(1024))
            root_seed.write_bytes(b"S" * 2048)
            aux_overlay.write_bytes(qcow_header(1024))
            root_overlay.write_bytes(qcow_header(2048))
            firmware.write_bytes(b"firmware")
            storage = StorageSession(
                root,
                aux,
                root_image,
                aux_overlay,
                root_overlay,
                0x200,
                aux_seed=aux_seed,
                root_seed=root_seed,
            )
            command = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=0x42),
                storage=storage,
                firmware=firmware,
                output=output,
                memory_mib=4096,
                smp=2,
                display="none",
                allow_bdif_writes=False,
            )

        self.assertEqual(command.count("-display"), 1)
        self.assertEqual(command[command.index("-display") + 1], "none")
        blockdev = [
            json.loads(command[index + 1])
            for index, value in enumerate(command)
            if value == "-blockdev"
        ]
        self.assertEqual({item["node-name"] for item in blockdev}, {
            "x86auxseed", "x86aux", "x86root",
        })
        aux_seed_node = next(item for item in blockdev if item["node-name"] == "x86auxseed")
        aux_node = next(item for item in blockdev if item["node-name"] == "x86aux")
        root_node = next(item for item in blockdev if item["node-name"] == "x86root")
        self.assertTrue(aux_seed_node["read-only"])
        self.assertEqual(aux_seed_node["backing"]["driver"], "raw")
        self.assertEqual(aux_seed_node["backing"]["offset"], 0x200)
        self.assertIn(str(aux), aux_seed_node["backing"]["file"]["filename"])
        self.assertEqual(aux_node["backing"], "x86auxseed")
        self.assertEqual(root_node["backing"]["driver"], "raw")
        self.assertEqual(root_node["backing"]["offset"], 0)
        self.assertIn(str(root_seed), root_node["backing"]["file"]["filename"])

    def test_tcg_parser_exposes_aux_and_root_seed_views(self) -> None:
        from x86.cli import build_parser

        parsed = build_parser().parse_args([
            "vmapple", "run-tcg",
            "--firmware", "/tmp/AVPBooter.bin",
            "--vm-json", "/tmp/macosvm.json",
            "--aux-seed", "/tmp/aux-seed.qcow2",
            "--root-seed", "/tmp/root-seed.raw",
            "--research-only",
        ])
        self.assertEqual(parsed.vmapple_action, "run-tcg")
        self.assertEqual(parsed.aux_seed, "/tmp/aux-seed.qcow2")
        self.assertEqual(parsed.root_seed, "/tmp/root-seed.raw")

    def test_tcg_report_records_source_inputs_and_seed_views(self) -> None:
        from x86.vmapple import _sha256
        from x86.vmapple_tcg import TCGVMappleConfig, run_tcg_macosvm

        class ExitedProcess:
            pid = 1234
            returncode = 0

            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aux = root / "aux.raw"
            root_image = root / "root.raw"
            firmware = root / "AVPBooter.bin"
            vm_json = root / "macosvm.json"
            aux_seed = root / "aux-seed.raw"
            root_seed = root / "root-seed.raw"
            for path, contents in (
                (aux, b"A" * 1024),
                (root_image, b"R" * 2048),
                (firmware, b"firmware"),
                (vm_json, b"{}"),
                (aux_seed, b"S" * 1024),
                (root_seed, b"T" * 2048),
            ):
                path.write_bytes(contents)
            bundle = SimpleNamespace(
                path=vm_json,
                json_sha256=_sha256(vm_json),
                aux=aux,
                root=root_image,
                aux_offset=0,
                uuid=1,
                report=lambda: {"path": str(vm_json)},
            )
            qemu = SimpleNamespace(
                program="qemu-system-aarch64",
                command=lambda *arguments: ["qemu-system-aarch64", *arguments],
            )
            qemu_img = SimpleNamespace(program="qemu-img")
            storage = SimpleNamespace(directory=root / "storage")
            observation = {
                "xnu_executed": False,
                "macos_userspace_reached": False,
                "guest_kernel_major": None,
                "guest_kernel_majors": [],
                "guest_target_match": False,
                "macos_boot_verified": False,
                "installer_ui_visible": False,
                "observed_markers": {"xnu": [], "userspace": [], "installer": []},
                "direct_boot_blocker": "fixture",
                "boot_chain_evidence": None,
            }

            def exited_qemu(*args, **kwargs):
                # The log backend puts both event and exec records at -D.
                (root / "run" / "qemu.debug.log").write_bytes(
                    b"Trace 0: 0x1 [100000000000/0000000000100000/000004a1/ff020000] \n"
                    b"arm_psci_call: PSCI Call x0=0x84000009 x1=0x0 x2=0x0 x3=0x0 cpuid=0x0\n"
                )
                return ExitedProcess()

            with patch.object(
                TCGVMappleConfig,
                "validate",
                return_value=(qemu, qemu_img, firmware, bundle),
            ), patch("x86.vmapple_tcg.probe_tcg_backend", return_value={"tcg": True}), \
                    patch("x86.vmapple_tcg.create_storage", return_value=storage), \
                    patch("x86.vmapple_tcg._tcg_command", return_value=["qemu"]), \
                    patch(
                        "x86.vmapple_tcg.subprocess.run",
                        return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                    ), \
                    patch("x86.vmapple_tcg.subprocess.Popen", side_effect=exited_qemu), \
                    patch("x86.vmapple_tcg._observe_direct_macos_boot", return_value=observation), \
                    patch("x86.vmapple_tcg._apply_iboot_xnu_handoff_gate"):
                report = run_tcg_macosvm(TCGVMappleConfig(
                    target_major=27,
                    qemu=None,
                    qemu_img=None,
                    firmware=str(firmware),
                    vm_json=str(vm_json),
                    output=str(root / "run"),
                    aux_seed=str(aux_seed),
                    root_seed=str(root_seed),
                    duration=0.1,
                    observation_timeout=0.1,
                    research_only=True,
                    firmware_kind="iboot-stage2",
                ))

            expected_aux_seed_path = str(aux_seed.resolve())
            expected_root_seed_path = str(root_seed.resolve())
            expected_aux_seed_bytes = aux_seed.stat().st_size
            expected_root_seed_sha256 = _sha256(root_seed)

        source_inputs = report["source_inputs"]
        self.assertTrue(report["input_integrity"])
        self.assertEqual(source_inputs["aux_seed"]["path"], expected_aux_seed_path)
        self.assertEqual(source_inputs["root_seed"]["path"], expected_root_seed_path)
        self.assertEqual(source_inputs["aux_seed"]["bytes"], expected_aux_seed_bytes)
        self.assertEqual(source_inputs["root_seed"]["sha256"], expected_root_seed_sha256)
        self.assertEqual(report["storage"]["seed_views"], {
            "aux": expected_aux_seed_path,
            "root": expected_root_seed_path,
        })
        self.assertIn("psci_trace_evidence", report)
        self.assertTrue(report["guest_reset_requested"])
        self.assertTrue(report["iboot_stage2_execution_observed"])
        shared_path = report["qemu_logging"]["shared_log_path"]
        self.assertEqual(report["qemu_logging"]["backend"], "log")
        self.assertEqual(report["psci_trace_evidence"]["trace_path"], shared_path)
        self.assertEqual(report["firmware_execution_evidence"]["trace_path"], shared_path)
        self.assertEqual(report["qemu_trace_retention"]["source_path"], shared_path)
        self.assertFalse(report["qemu_stderr_evidence"]["guest_crash_loaded_observed"])
        self.assertFalse(report["xnu_executed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertFalse(report["graphics_acceleration_verified"])

    def test_graphics_request_selects_reims_machine_mode(self) -> None:
        from x86.vmapple import Executable
        from x86.vmapple_tcg import _tcg_command

        class Storage:
            def arguments(self, executable, *, allow_bdif_writes):
                return []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            firmware = output / "AVPBooter.vmapple2.bin"
            firmware.write_bytes(b"caller-supplied fixture")
            command = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=1),
                storage=Storage(),
                firmware=firmware,
                output=output,
                memory_mib=4096,
                smp=2,
                display="none",
                allow_bdif_writes=False,
                research_graphics=True,
            )
        self.assertIn("vmapple,research-headless=on,research-graphics=on,uuid=1", command)

    def test_raw_stage2_request_selects_the_separate_el2_contract(self) -> None:
        from x86.vmapple import Executable
        from x86.vmapple_tcg import _tcg_command

        class Storage:
            def arguments(self, executable, *, allow_bdif_writes):
                return []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            firmware = output / "iboot-stage2.bin"
            firmware.write_bytes(b"caller-supplied fixture")
            command = _tcg_command(
                executable=Executable("qemu-system-aarch64"),
                bundle=SimpleNamespace(uuid=1),
                storage=Storage(),
                firmware=firmware,
                output=output,
                memory_mib=4096,
                smp=1,
                display="none",
                allow_bdif_writes=False,
                firmware_kind="iboot-stage2",
            )
        self.assertTrue(any("research-stage2=on" in item for item in command))

    def test_raw_stage2_trace_records_entry_and_high_ram_relocation(self) -> None:
        from x86.vmapple_tcg import _qemu_execution_evidence

        trace = (
            b"Trace 0: 0x1 [100000000000/0000000000100000/000004a1/ff020000] \n"
            b"Trace 1: 0x2 [100800204408/00000001fc000000/00000671/ff020000] \n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.debug.log"
            path.write_bytes(trace)
            evidence = _qemu_execution_evidence(path, firmware_kind="iboot-stage2")
        self.assertTrue(evidence["stage2_execution_observed"])
        self.assertTrue(evidence["high_ram_relocation_observed"])
        self.assertEqual(evidence["translation_block_count"], 2)
        self.assertFalse(evidence["iboot_panic_range_entry"])

    def test_iboot_panic_range_detected_in_stage2_trace(self) -> None:
        from x86.vmapple_tcg import _qemu_execution_evidence

        trace = (
            b"Trace 0: 0x1 [100000000000/0000000000100000/000004a1/ff020000] \n"
            b"Trace 1: 0x2 [100800204408/0000000070070000/00000671/ff020000] \n"
            b"Trace 1: 0x3 [100800204408/0000000070080000/00000671/ff020000] \n"
            b"Trace 1: 0x2 [100800204408/0000000070070000/00000671/ff020000] \n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.debug.log"
            path.write_bytes(trace)
            evidence = _qemu_execution_evidence(path, firmware_kind="iboot-stage2")
        self.assertTrue(evidence["iboot_panic_range_entry"])
        self.assertIsNotNone(evidence["iboot_panic_classification"])
        self.assertIn("diagnostic", evidence["iboot_panic_classification"])  # type: ignore[index]
        self.assertEqual(evidence["iboot_panic_classification"]["panic_pc"], "0x70070000")

    def test_avpbooter_trace_is_not_raw_stage2_evidence(self) -> None:
        from x86.vmapple_tcg import _qemu_execution_evidence

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.debug.log"
            path.write_bytes(
                b"Trace 0: 0x1 [100000000000/0000000000100000/000004a1/ff020000] \n"
            )
            evidence = _qemu_execution_evidence(path, firmware_kind="avpbooter")
        self.assertFalse(evidence["stage2_execution_observed"])
        self.assertFalse(evidence["trace_present"])

    def test_host_reims_frame_is_not_guest_metal_evidence(self) -> None:
        from x86.vmapple_tcg import _graphics_host_evidence

        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "qemu.stderr.log"
            log.write_bytes(
                b"reims-vgpu-window: first frame presented (1920x1080, 5 swapchain images)\n"
            )
            evidence = _graphics_host_evidence(log)
        self.assertEqual(evidence["backend"], "reims-vgpu")
        self.assertTrue(evidence["host_frame_presented"])
        self.assertFalse(evidence["guest_windowserver_reached"])
        self.assertFalse(evidence["guest_graphics_acceleration_verified"])

    def test_fault_address_classification_maps_to_vmapple_device(self) -> None:
        from x86.vmapple_tcg import _classify_fault_address

        uart = _classify_fault_address(0x2001_0004)
        self.assertEqual(uart["device"], "UART")
        self.assertTrue(uart["in_device"])
        self.assertFalse(uart["in_ram"])
        self.assertEqual(uart["device_offset"], "0x4")

        gic = _classify_fault_address(0x1000_0000)
        self.assertEqual(gic["device"], "GIC")

        ram = _classify_fault_address(0x7000_1000)
        self.assertEqual(ram["device"], "RAM")
        self.assertTrue(ram["in_ram"])
        self.assertEqual(ram["ram_offset"], "0x1000")

        unmapped = _classify_fault_address(0xF000_0000)
        self.assertEqual(unmapped["device"], "unmapped")
        self.assertFalse(unmapped["in_device"])
        self.assertFalse(unmapped["in_ram"])

    def test_iboot_panic_range_classification(self) -> None:
        from x86.vmapple_tcg import _classify_iboot_panic_range

        self.assertIsNone(_classify_iboot_panic_range(0x7000_0000))
        result = _classify_iboot_panic_range(0x7007_0000)
        self.assertIsNotNone(result)
        self.assertIn("panic_pc", result)  # type: ignore[index]
        self.assertIn("diagnostic", result)  # type: ignore[index]

    def test_stderr_evidence_classifies_data_abort_with_device_map(self) -> None:
        from x86.vmapple_tcg import _qemu_stderr_evidence

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.stderr.log"
            path.write_bytes(
                b"some preamble\n"
                b"data abort: pc=0x70070000 FAR=0x20010004 ESR=0x96000046\n"
                b"Guest crash loaded pc=0x70070000\n"
            )
            evidence = _qemu_stderr_evidence(path)

        self.assertTrue(evidence["present"])
        self.assertTrue(evidence["data_abort_observed"])
        self.assertTrue(evidence["guest_crash_loaded_observed"])
        self.assertGreater(len(evidence["fault_addresses"]), 0)  # type: ignore[arg-type]
        diagnostics = evidence["exception_diagnostics"]  # type: ignore[index]
        self.assertGreater(len(diagnostics), 0)
        first = diagnostics[0]
        self.assertEqual(first["type"], "data_abort")
        self.assertEqual(first["device"], "UART")
        self.assertTrue(first["wnr"])

    def test_stderr_evidence_classifies_instruction_abort(self) -> None:
        from x86.vmapple_tcg import _qemu_stderr_evidence

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qemu.stderr.log"
            path.write_bytes(
                b"instruction abort: FAR=0x10000000 ESR=0x82000000\n"
            )
            evidence = _qemu_stderr_evidence(path)

        self.assertTrue(evidence["instruction_abort_observed"])
        self.assertFalse(evidence["data_abort_observed"])
        diagnostics = evidence["exception_diagnostics"]  # type: ignore[index]
        self.assertEqual(diagnostics[0]["type"], "instruction_abort")
        self.assertEqual(diagnostics[0]["device"], "GIC")

    @unittest.skipUnless(Path("/tmp/26x86-vmapple-tcg-series.QqdFYF/build/qemu-system-aarch64").is_file(),
                         "complete local QEMU TCG build is not available")
    def test_complete_qemu_binary_exposes_required_research_contract(self) -> None:
        from x86.vmapple import Executable
        from x86.vmapple_tcg import probe_tcg_backend

        report = probe_tcg_backend(Executable("/tmp/26x86-vmapple-tcg-series.QqdFYF/build/qemu-system-aarch64"))
        self.assertEqual(report["machine"], "vmapple")
        self.assertTrue(report["tcg"])
        self.assertTrue(report["headless"])
        self.assertFalse(report["virtualization_framework"])
        self.assertTrue(report["guest_image_modified"] is False)


if __name__ == "__main__":
    unittest.main()
