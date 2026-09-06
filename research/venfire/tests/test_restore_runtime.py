"""Exercise the real session watcher with a nonexecuting backend fixture."""
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from venfire import boot


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.paths = {}
        for name in ("firmware", "aux", "disk", "qemu"):
            path = self.root / name
            path.write_bytes(b"self-authored fixture")
            self.paths[name] = str(path)
        self.output = self.root / "run"
        self.process = Mock(returncode=None)
        self.process.poll.side_effect = lambda: self.process.returncode
        self.process.terminate.side_effect = lambda: setattr(self.process, "returncode", -15)
        self.process.wait.side_effect = lambda **_: self.process.returncode
        self.spawn_options = None
        self.backend = {"executable": self.paths["qemu"], "tcg": True, "vmapple": True,
                        "research_headless": True, "bdif_block_writes": True, "research_graphics": True}

    def run_action(self, action, graphics="auto"):
        host = Mock()
        host.report.to_dict.return_value = {"fixture": True}
        host.to_dict.return_value = {"fixture": True}
        storage = Mock(directory=self.root / "storage")
        storage.arguments.return_value = []
        def spawn(*args, **kwargs):
            self.spawn_options = kwargs
            self.command = args[0]
            return self.process
        with patch.object(boot, "authorize_host", return_value=host), \
                patch.object(boot, "probe_backend", return_value=self.backend), \
                patch.object(boot.subprocess, "Popen", side_effect=spawn):
            return boot._run_boot(**self.paths, uuid=0, output=self.output, seconds=1, aux_offset=0,
                developer_host_bypass=False, storage=storage, recovery_socket=str(self.root / "r.sock"),
                runtime_action=action, graphics=graphics)

    def assert_reaped(self):
        self.process.terminate.assert_called_once()
        self.process.wait.assert_called_once_with(timeout=5)
        self.assertFalse(any(item.name == "venfire-session-watchdog" for item in threading.enumerate()))

    def test_action_runs_once_and_available_gpu_is_selected(self):
        calls = []
        def action(**kwargs):
            calls.append(kwargs["serial_log"])
            kwargs["check_running"]()
            return {"chain_completed": True, "macos_boot_verified": False}
        report = self.run_action(action)
        self.assertEqual(calls, [self.output / "serial.log"])
        self.assertTrue(report["runtime_action_completed"])
        self.assertTrue(report["graphics_device_enabled"])
        self.assertIn("research-graphics=on", self.command[self.command.index("-M") + 1])
        self.assertFalse(report["macos_boot_verified"])
        self.assert_reaped()

    def test_explicit_graphics_off_retains_headless_device_fixture(self):
        report = self.run_action(lambda **_: {}, graphics="off")
        self.assertFalse(report["graphics_device_enabled"])
        self.assertNotIn("research-graphics=on", self.command[self.command.index("-M") + 1])
        self.assert_reaped()

    def test_explicit_missing_graphics_fails_before_spawn(self):
        self.backend["research_graphics"] = False
        with self.assertRaisesRegex(ValueError, "GPU device is unavailable"):
            self.run_action(lambda **_: {}, graphics="on")
        self.assertIsNone(self.spawn_options)

    def test_cancellation_reaps_backend_and_joins_watcher(self):
        def action(**_):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.run_action(action)
        self.assert_reaped()
        report = json.loads((self.output / "result.json").read_text())
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertFalse(report["runtime_action_completed"])

    def test_log_limit_is_enforced_while_action_is_running(self):
        def action(**kwargs):
            self.spawn_options["stdout"].write(bytes(1025))
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                kwargs["check_running"]()
                time.sleep(0.01)
            self.fail("watcher did not stop backend")
        with patch.object(boot, "MAX_LOG_BYTES", 1024), self.assertRaisesRegex(RuntimeError, "log_limit"):
            self.run_action(action)
        self.assert_reaped()
        report = json.loads((self.output / "result.json").read_text())
        self.assertEqual(report["watchdog_stop"], "log_limit")
        self.assertFalse(report["session_completed"])


if __name__ == "__main__":
    unittest.main()
