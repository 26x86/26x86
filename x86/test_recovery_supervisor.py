"""Authored host-process fixtures only: no VM, QEMU, TSS, or network runs."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from unittest import mock

from . import recovery_supervisor as supervisor


def request_args(root: Path) -> list[str]:
    args = []
    for key in supervisor.PATH_OPTIONS:
        args.extend(["--" + key.replace("_", "-"), str(root / key)])
    args.extend(["--target", "27", "--memory-mib", "4096", "--smp", "2",
                 "--transition-timeout", "20", "--restore-timeout", "30",
                 "--duration", "10", "--total-timeout", "60"])
    return args


class ContractTests(unittest.TestCase):
    def test_exact_worker_arguments_and_environment(self):
        request = supervisor.parse_request(request_args(Path("/space quote' \\\"")))
        argv = supervisor.worker_argv(request)
        expected = [sys.executable, "-m", "x86", "vmapple", "run"]
        for key in (
            "target", "qemu", "qemu_img", "firmware", "vm_json", "build_manifest",
            "tss_helper", "original_ibss", "original_ibec", "restore_role_dir",
            "memory_mib", "smp", "transition_timeout", "restore_timeout", "duration", "output",
        ):
            expected.extend(["--" + key.replace("_", "-"), str(getattr(request, key))])
        expected.extend([
            "--boot-selection", "recovery", "--no-boot-picker", "--display", "none",
            "--live-personalize", "--restore-chain", "--research-only", "--json",
        ])
        self.assertEqual(argv, expected)
        self.assertNotIn("--total-timeout", argv)
        self.assertNotIn("--ibec", argv)
        request.optional_rpc_unavailable = True
        self.assertEqual(supervisor.worker_argv(request), expected + ["--optional-rpc-unavailable"])
        inherited = {name: "private-value-must-not-escape" for name in supervisor.REMOVED_ENVIRONMENT}
        inherited.update(PATH="/usr/bin", OTHER="preserve")
        env, receipt = supervisor.worker_environment(inherited)
        self.assertEqual(env, {"PATH": "/usr/bin", "OTHER": "preserve"})
        self.assertNotIn("private-value", json.dumps(receipt))
        self.assertEqual(receipt["effective"]["restore_boot_args"], supervisor.RESTORE_BOOT_ARGS)
        # Explicit regression list: do not silently inherit newly removed AUX inputs.
        self.assertTrue({"X86_VMAPLE_AUX_SEED", "X86_VMAPLE_ROOT_SEED",
                         "X86_VMAPLE_IBSS", "X86_VMAPLE_IBEC",
                         "VENFIRE_RESTORE_BOOT_ARGS", "VENFIRE_EXTRA_TRACE"}
                        .issubset(supervisor.REMOVED_ENVIRONMENT))

    def test_cli_ranges_and_errors_always_json(self):
        valid = request_args(Path("/fixture"))
        for flag, value in (("--total-timeout", "29"), ("--total-timeout", "nan"),
                            ("--duration", "55"), ("--cleanup-grace", "31"),
                            ("--smp", "33"), ("--transition-timeout", "inf"),
                            ("--transition-timeout", "301"), ("--restore-timeout", "0.5")):
            with self.subTest(flag=flag, value=value):
                args = list(valid)
                if flag in args:
                    args[args.index(flag) + 1] = value
                else:
                    args.extend([flag, value])
                with self.assertRaises(ValueError):
                    supervisor.parse_request(args)
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            self.assertEqual(supervisor.main(["--bad-private-argument"]), 0)
        envelope = json.loads(output.getvalue())
        self.assertEqual(envelope["schema"], supervisor.SCHEMA)
        self.assertFalse(envelope["boot"]["macos_boot_verified"])
        self.assertNotIn("private-argument", output.getvalue())

    def test_raw_launch_partial_invalid_identity_and_oversize(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name)
            path = output / "launch.json"
            path.write_bytes(b'{"schema":')
            raw = supervisor.read_launch(output, 27, time.monotonic() + 5)
            self.assertFalse(raw["complete"])
            self.assertEqual(raw["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertIsNone(raw["raw"])
            report = {"schema": supervisor.RAW_SCHEMA, "target_major": 26,
                      "machine_type": "iBoot(AArch64)", "personality": "iBoot",
                      "guest_os": "macOS", "boot_mode": "recovery", "output": str(output),
                      "runtime_started": True, "xnu_executed": True,
                      "guest_panic": {"observed": "false"},
                      "dfu_upload": {"transfer_complete": True}}
            path.write_text(json.dumps(report))
            raw = supervisor.read_launch(output, 27, time.monotonic() + 5)
            self.assertTrue(raw["complete"])
            self.assertFalse(raw["identity_valid"])
            self.assertFalse(supervisor.recovery_progress(raw)["runtime_started"])
            report["target_major"] = 27
            path.write_text(json.dumps(report))
            raw = supervisor.read_launch(output, 27, time.monotonic() + 5)
            self.assertTrue(raw["identity_valid"])
            self.assertFalse(supervisor.recovery_progress(raw)["dfu_upload_completed"])
            # Mapping seam: actual PID correlation is exercised in Linux tests.
            raw["runtime_pid_observed"] = True
            self.assertTrue(supervisor.recovery_progress(raw)["dfu_upload_completed"])
            self.assertFalse(supervisor.recovery_progress(raw)["firmware_panic_observed"])
            path.write_bytes(b" " * (supervisor.CAPTURE_LIMIT + 1))
            raw = supervisor.read_launch(output, 27, time.monotonic() + 5)
            self.assertFalse(raw["complete"])
            self.assertFalse(raw["hash_complete"])
            self.assertIsNone(raw["raw"])

    def test_nonfinite_json_and_envelope_expansion_fail_closed(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name)
            (output / "launch.json").write_bytes(b'{"bad":NaN}')
            self.assertFalse(supervisor.read_launch(output, 27, time.monotonic() + 5)["complete"])
        envelope = supervisor.empty_envelope()
        envelope["launch_report"].update(raw={"large": "\uffff" * 1500000}, complete=True)
        encoded = supervisor.serialize_envelope(envelope)
        self.assertLessEqual(len(encoded), supervisor.ENVELOPE_LIMIT)
        parsed = json.loads(encoded)
        self.assertIsNone(parsed["launch_report"]["raw"])
        self.assertFalse(parsed["launch_report"]["complete"])
        envelope = supervisor.empty_envelope()
        envelope["launch_report"]["raw"] = {"string": "\ud800"}
        self.assertIn("\\ud800", supervisor.serialize_envelope(envelope))

    def test_runtime_pid_mismatch_and_duplicate_roles_do_not_promote(self):
        launch = {"identity_valid": True, "raw": {
            "runtime_started": True, "pid": 1235,
            "restore_chain": {"steps": [
                {"role": "RestoreLogo", "upload": {"transfer_complete": True}},
                {"role": "RestoreLogo", "upload": {"transfer_complete": True}},
                {"role": "RestoreRamDisk", "upload": {"transfer_complete": False}},
                {"role": "unknown", "upload": {"transfer_complete": True}}, {}]}}}
        worker = {"pid": 1234, "process_inventory_complete": True,
                  "observed_processes": [{"pid": 999, "starttime": 20, "session": 1234}]}
        supervisor.correlate_runtime(launch, worker)
        self.assertFalse(launch["runtime_pid_observed"])
        self.assertFalse(supervisor.recovery_progress(launch)["runtime_started"])
        worker["observed_processes"][0]["pid"] = 1235
        supervisor.correlate_runtime(launch, worker)
        self.assertTrue(launch["runtime_pid_observed"])
        self.assertEqual(supervisor.recovery_progress(launch)["restore_role_step_count"], 1)
        worker["observed_processes"].append({"pid": 1235, "starttime": 30, "session": 1234})
        supervisor.correlate_runtime(launch, worker)
        self.assertFalse(launch["runtime_pid_observed"])

    def test_unstarted_runtime_cannot_claim_recovery_progress(self):
        launch = {"identity_valid": True, "runtime_pid_observed": True, "raw": {
            "runtime_started": False, "dfu_upload": {"transfer_complete": True},
            "stage2": {"observed": True}, "restore_chain": {"bootx_acknowledged": True}}}
        progress = supervisor.recovery_progress(launch)
        self.assertFalse(progress["dfu_upload_completed"])
        self.assertFalse(progress["stage2_prompt_observed"])
        self.assertFalse(progress["bootx_acknowledged"])


@unittest.skipUnless(sys.platform == "linux", "Linux session/pidfd ownership tests")
class LinuxSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env = dict(os.environ)

    def run_script(self, script, *, output=None, timeout=1.5, grace=0.6, cancel=None):
        return supervisor.run_owned(
            [sys.executable, "-c", textwrap.dedent(script)], env=self.env,
            output=output, total_timeout=timeout, cleanup_grace=grace,
            cancel=cancel or supervisor.Cancellation())

    def fixture_request(self):
        bundle = self.root / "bundle"
        bundle.mkdir()
        roles = self.root / "roles"
        roles.mkdir()
        for name in supervisor.REQUIRED_ROLES:
            (roles / name).write_bytes(b"authored role")
        for name in ("aux.bin", "root.bin"):
            (bundle / name).write_bytes(b"authored storage")
        vm_json = bundle / "vm.json"
        vm_json.write_text(json.dumps({
            "machineId": "fixture", "hardwareModel": "fixture",
            "storage": [{"type": "aux", "file": "aux.bin"},
                        {"type": "disk", "file": "root.bin"}],
        }))
        source = self.root / "input.bin"
        source.write_bytes(b"authored unchanged source")
        values = {key: str(source) for key in supervisor.PATH_OPTIONS}
        values.update(qemu=sys.executable, qemu_img=sys.executable, tss_helper=sys.executable,
                      vm_json=str(vm_json), restore_role_dir=str(roles),
                      output=str(self.root / "output"), target=27, memory_mib=4096, smp=2,
                      transition_timeout=20.0, restore_timeout=30.0, duration=10.0,
                      total_timeout=1.5, cleanup_grace=0.6, optional_rpc_unavailable=False)
        # Internal seam shortens only supervisor time for authored workers.
        return argparse.Namespace(**values), source

    def test_timeout_and_bounded_capture(self):
        result, stdout, stderr = self.run_script("""
            import os, time
            os.write(1, b'x' * (4*1024*1024 + 32768))
            os.write(2, b'error')
            time.sleep(20)
        """)
        self.assertTrue(result["deadline_exceeded"])
        self.assertTrue(result["cleanup"]["complete"], result)
        self.assertLess(result["elapsed_seconds"], 1.9)
        self.assertEqual(len(stdout.data), supervisor.CAPTURE_LIMIT)
        self.assertEqual(stdout.observed, supervisor.CAPTURE_LIMIT + 32768)
        self.assertEqual(stdout.digest.hexdigest(), hashlib.sha256(b"x" * stdout.observed).hexdigest())
        output = self.root / "logs"
        receipt = supervisor._save_capture(stdout, output, "stdout.log", time.monotonic() + 5)
        self.assertTrue(receipt["truncated"])
        self.assertFalse(receipt["complete"])
        self.assertEqual(receipt["bytes_saved"], supervisor.CAPTURE_LIMIT)
        second = supervisor._save_capture(stderr, output, "stdout.log", time.monotonic() + 5)
        self.assertTrue(second["storage_error"])
        self.assertEqual((output / "stdout.log").stat().st_size, supervisor.CAPTURE_LIMIT)

    def test_leader_exits_first_different_group_term_ignoring_child(self):
        result, stdout, _ = self.run_script("""
            import os, signal, time
            read_fd, write_fd = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(read_fd)
                os.setpgid(0, 0)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                os.write(write_fd, b'ready')
                os.close(write_fd)
                time.sleep(20)
                os._exit(0)
            os.close(write_fd)
            os.read(read_fd, 5)
            print(child, flush=True)
            os._exit(0)
        """)
        child = int(stdout.data)
        self.assertEqual(result["returncode"], 0)
        self.assertTrue(result["cleanup"]["complete"], result)
        self.assertEqual(result["cleanup"]["remaining_pids"], [])
        self.assertIsNone(supervisor.process_identity(child))
        self.assertLess(result["elapsed_seconds"], 1.0)

    def test_early_stop_before_final_worker_phase(self):
        output = self.root / "output"
        cancel = supervisor.Cancellation()
        def stop():
            until = time.monotonic() + 3
            while not output.exists() and time.monotonic() < until:
                time.sleep(0.01)
            (output / "stop").touch()
        thread = threading.Thread(target=stop)
        thread.start()
        result, _, _ = self.run_script(f"""
            from pathlib import Path
            import time
            Path({str(output)!r}).mkdir()
            time.sleep(20)
        """, output=output, cancel=cancel)
        thread.join(timeout=1)
        self.assertTrue(cancel.requested)
        self.assertEqual(cancel.reason, "stop-file")
        self.assertTrue(result["cleanup"]["complete"])
        self.assertFalse(result["deadline_exceeded"])

    def test_exit_zero_is_not_boot_and_manifest_mutation_is_false(self):
        request, source = self.fixture_request()
        script = f"""
            import json, subprocess, sys, time
            from pathlib import Path
            output = Path({request.output!r})
            output.mkdir()
            child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(0.25)'])
            child.wait()
            Path({str(source)!r}).write_bytes(b'changed authored source')
            raw = {{'schema': {supervisor.RAW_SCHEMA!r}, 'target_major': 27,
                   'output': str(output), 'machine_type': 'iBoot(AArch64)',
                   'personality': 'iBoot', 'guest_os': 'macOS', 'boot_mode': 'recovery',
                   'runtime_started': True, 'pid': child.pid, 'xnu_executed': True,
                   'macos_boot_verified': True, 'guest_kernel_major': 27,
                   'dfu_upload': {{'transfer_complete': True}},
                   'transition': {{'state': 'ibec-ready'}},
                   'stage2': {{'stage2_serial_started': True, 'observed': True}},
                   'restore_chain': {{'sequence_sent': True, 'bootx_acknowledged': True,
                                      'steps': [{{'role': role, 'upload': {{'transfer_complete': True}}}}
                                                for role in ['RestoreLogo', 'RestoreTrustCache',
                                                             'RestoreRamDisk', 'RestoreDeviceTree',
                                                             'RestoreKernelCache']]}},
                   'guest_panic': {{'observed': True}}}}
            (output / 'launch.json').write_text(json.dumps(raw))
            print('{{"worker_exit":0}}')
        """
        with mock.patch.object(supervisor, "worker_argv", return_value=[sys.executable, "-c", textwrap.dedent(script)]):
            envelope = supervisor.supervise(request)
        self.assertEqual(envelope["worker"]["returncode"], 0, envelope)
        self.assertFalse(envelope["boot"]["macos_boot_verified"])
        self.assertFalse(envelope["boot"]["xnu_executed"])
        self.assertIsNone(envelope["boot"]["guest_kernel_major"])
        self.assertFalse(envelope["input_integrity"]["unchanged"])
        self.assertTrue(envelope["cleanup"]["complete"])
        self.assertTrue(envelope["launch_report"]["complete"])
        self.assertTrue(envelope["launch_report"]["runtime_pid_observed"])
        self.assertTrue(envelope["worker_stdout"]["complete"])
        progress = envelope["recovery_progress"]
        self.assertTrue(progress["stage2_banner_observed"])
        self.assertTrue(progress["stage2_prompt_observed"])
        self.assertEqual(progress["restore_role_step_count"], 5)
        self.assertTrue(progress["bootx_acknowledged"])

    def test_valid_partial_error_report_and_unchanged_sources(self):
        request, _source = self.fixture_request()
        script = f"""
            import json, sys
            from pathlib import Path
            output = Path({request.output!r}); output.mkdir()
            (output / 'launch.json').write_text(json.dumps({{
                'schema': {supervisor.RAW_SCHEMA!r}, 'target_major': 27,
                'error': 'authored early error', 'runtime_started': False}}))
            print('{{"ok": false}}'); sys.exit(3)
        """
        with mock.patch.object(supervisor, "worker_argv", return_value=[sys.executable, "-c", textwrap.dedent(script)]):
            envelope = supervisor.supervise(request)
        self.assertEqual(envelope["worker"]["returncode"], 3)
        self.assertTrue(envelope["cleanup"]["complete"])
        self.assertTrue(envelope["input_integrity"]["unchanged"], envelope)
        self.assertEqual(envelope["launch_report"]["raw"]["error"], "authored early error")
        self.assertFalse(envelope["launch_report"]["identity_valid"])

    def test_hash_timeout_is_unknown_not_success(self):
        values, complete = supervisor.hash_inputs(
            [{"path": str(self.root / "not-read")}], time.monotonic() - 1,
            self.env, supervisor.Cancellation())
        self.assertFalse(complete)
        self.assertIsNone(values[0]["sha256"])

    def test_preexisting_output_and_output_inside_bundle_rejected(self):
        request, _source = self.fixture_request()
        Path(request.output).mkdir()
        with self.assertRaises(ValueError):
            supervisor.resolve_inputs(request)
        request.output = str(Path(request.vm_json).parent / "new-session")
        with self.assertRaises(ValueError):
            supervisor.resolve_inputs(request)

    def test_symlink_or_fifo_launch_is_not_followed(self):
        output = self.root / "output"
        output.mkdir()
        secret = self.root / "private-other-input"
        secret.write_bytes(b'{"must-not-read":true}')
        launch = output / "launch.json"
        launch.symlink_to(secret)
        self.assertIsNone(supervisor.read_launch(output, 27, time.monotonic() + 1)["sha256"])
        launch.unlink()
        os.mkfifo(launch)
        started = time.monotonic()
        self.assertFalse(supervisor.read_launch(output, 27, started + 1)["complete"])
        self.assertLess(time.monotonic() - started, 0.2)

    def test_no_unrelated_pid_signalling_or_reaping(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        try:
            identity = supervisor.process_identity(unrelated.pid)
            fake = supervisor.ProcessIdentity(identity.pid, identity.starttime + 1, identity.session)
            self.assertFalse(supervisor.signal_member(fake, signal.SIGKILL))
            result, _, _ = self.run_script("print('authored')")
            self.assertTrue(result["cleanup"]["complete"])
            self.assertIsNone(unrelated.poll())
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=3)

    def test_non_ascii_and_parenthesis_process_name_is_opaque(self):
        result, _, _ = self.run_script("""
            import ctypes, time
            ctypes.CDLL(None).prctl(15, '검사 ) worker'.encode(), 0, 0, 0)
            time.sleep(20)
        """)
        self.assertTrue(result["cleanup"]["scan_complete"])
        self.assertTrue(result["cleanup"]["complete"], result)
        self.assertIsNone(supervisor.process_identity(result["pid"]))

    def test_main_handlers_cleanup_term_int_hup(self):
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            with self.subTest(signum=signum):
                ready = self.root / ("ready-" + str(signum))
                # Call the production main and its signal handlers, replacing only
                # expensive preflight and the command with an authored worker.
                worker = f"import os,time;open({str(ready)!r},'w').write(str(os.getpid()));time.sleep(20)"
                script = f"""
                    import json, sys
                    from x86 import recovery_supervisor as s
                    def fixture_supervise(request, *, cancel):
                        result, out, err = s.run_owned(
                            [sys.executable, '-c', {worker!r}], env=dict(s.os.environ),
                            output=None, total_timeout=3, cleanup_grace=0.6, cancel=cancel)
                        envelope = s.empty_envelope()
                        envelope.update(worker=result, cleanup=result['cleanup'], cancel=vars(cancel))
                        return envelope
                    s.supervise = fixture_supervise
                    s.main({request_args(self.root)!r})
                """
                process = subprocess.Popen([sys.executable, "-c", textwrap.dedent(script)],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    until = time.monotonic() + 3
                    while not ready.exists() and process.poll() is None and time.monotonic() < until:
                        time.sleep(0.01)
                    self.assertTrue(ready.exists())
                    pid = int(ready.read_text())
                    process.send_signal(signum)
                    stdout, stderr = process.communicate(timeout=4)
                    self.assertEqual(process.returncode, 0, stderr)
                    envelope = json.loads(stdout)
                    self.assertEqual(envelope["cancel"]["signal"], signum)
                    self.assertTrue(envelope["cleanup"]["complete"], envelope)
                    self.assertIsNone(supervisor.process_identity(pid))
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.communicate(timeout=2)


if __name__ == "__main__":
    unittest.main()
