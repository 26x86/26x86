import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from venfire import artifacts
from venfire.boot import boot_probe, raw_drive


class BootPolicyTests(unittest.TestCase):
    def test_readonly_json_view_preserves_comma_path(self):
        text = raw_drive(Path("disk,withcomma.img"), 0, 16384)
        self.assertIn("readonly=on", text)
        embedded = text.split("file=json:", 1)[1].replace(",,", ",")
        node = json.loads(embedded)
        self.assertEqual(node["offset"], 16384)
        self.assertTrue(node["read-only"])
        self.assertEqual(node["file"]["filename"], "disk,withcomma.img")

    def test_invalid_offset_fails(self):
        for offset in (-1, 1, 511):
            with self.assertRaises(ValueError):
                raw_drive(Path("x"), 0, offset)

    def test_host_check_precedes_backend_and_input_access(self):
        with patch("venfire.boot.authorize_host", side_effect=RuntimeError("denied")), \
                patch("venfire.boot.probe_backend") as backend, \
                patch("venfire.boot.create_manifest") as inputs:
            with self.assertRaisesRegex(RuntimeError, "denied"):
                boot_probe(qemu="not-read", firmware="not-read", aux="not-read", disk="not-read",
                           uuid=0, output="not-created")
            backend.assert_not_called()
            inputs.assert_not_called()


class BootIntegrityTests(unittest.TestCase):
    """No Apple input is used or guest process started by these fixtures."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.inputs = {}
        for name in ("firmware", "aux", "disk", "qemu"):
            path = self.root / (name + ".fixture")
            path.write_bytes(("self-authored test data: " + name).encode())
            self.inputs[name] = str(path)
        self.output = self.root / "evidence"
        report = Mock()
        report.to_dict.return_value = {"eligible": True, "fixture": True}
        authorization = Mock()
        authorization.report = report
        authorization.to_dict.return_value = {"authorized": True, "fixture": True}
        self.host_patch = patch("venfire.boot.authorize_host", return_value=authorization)
        self.backend_patch = patch("venfire.boot.probe_backend", return_value={
            "executable": self.inputs["qemu"], "tcg": True, "vmapple": True,
            "research_headless": True,
        })
        self.host_patch.start()
        self.backend_patch.start()
        self.addCleanup(self.host_patch.stop)
        self.addCleanup(self.backend_patch.stop)

    def run_probe(self):
        return boot_probe(**self.inputs, uuid=0, output=str(self.output), seconds=1)

    def finished_process(self):
        process = Mock()
        process.poll.return_value = 0
        process.returncode = 0
        return process

    def test_original_inputs_and_backend_are_verified_and_never_marked_macos_booted(self):
        initial = {name: Path(path).read_bytes() for name, path in self.inputs.items()}
        with patch("venfire.boot.subprocess.Popen", return_value=self.finished_process()) as spawn:
            report = self.run_probe()
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertEqual(report["input_integrity"]["checked_count"], 4)
        self.assertTrue(report["probe_completed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertEqual(initial, {name: Path(path).read_bytes() for name, path in self.inputs.items()})
        command = spawn.call_args.args[0]
        self.assertNotIn("-semihosting", command)
        self.assertIn("readonly=on", command[command.index("-drive") + 1])
        self.assertEqual(command[command.index("-nic") + 1], "none")
        self.assertIn("cntfrq=24000000", command[command.index("-cpu") + 1])
        self.assertEqual(json.loads((self.output / "result.json").read_text())["input_integrity"], report["input_integrity"])

    def test_backend_failure_is_not_a_completed_probe(self):
        process = self.finished_process()
        process.poll.return_value = 1
        process.returncode = 1
        with patch("venfire.boot.subprocess.Popen", return_value=process):
            report = self.run_probe()
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertFalse(report["probe_completed"])
        self.assertEqual(report["returncode"], 1)
        self.assertFalse(report["macos_boot_verified"])

    def test_prelaunch_change_denies_process_and_records_postcheck(self):
        original_write = artifacts.write_manifest

        def change_after_manifest(manifest, path):
            result = original_write(manifest, path)
            with Path(self.inputs["firmware"]).open("ab") as output:
                output.write(b"changed before launch")
            return result

        with patch("venfire.boot.write_manifest", side_effect=change_after_manifest), \
                patch("venfire.boot.subprocess.Popen") as spawn:
            with self.assertRaises(artifacts.ArtifactIntegrityError):
                self.run_probe()
        spawn.assert_not_called()
        report = json.loads((self.output / "result.json").read_text())
        self.assertFalse(report["input_integrity"]["valid"])
        self.assertFalse(report["probe_completed"])
        self.assertEqual(report["error_type"], "ArtifactIntegrityError")

    def test_spawn_error_still_verifies_inputs_and_records_failure(self):
        with patch("venfire.boot.subprocess.Popen", side_effect=OSError("synthetic spawn failure")):
            with self.assertRaisesRegex(OSError, "synthetic spawn failure"):
                self.run_probe()
        report = json.loads((self.output / "result.json").read_text())
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertFalse(report["probe_completed"])
        self.assertIsNone(report["returncode"])
        self.assertEqual(report["termination"], "error")

    def test_mutation_during_backend_execution_invalidates_result(self):
        def mutate(*args, **kwargs):
            path = Path(self.inputs["disk"])
            data = path.read_bytes()
            path.write_bytes(b"X" + data[1:])
            return self.finished_process()

        with patch("venfire.boot.subprocess.Popen", side_effect=mutate):
            report = self.run_probe()
        self.assertFalse(report["input_integrity"]["valid"])
        self.assertFalse(report["probe_completed"])
        self.assertIn("SHA-256", report["input_integrity"]["issues"][0]["reason"])

    def test_cancellation_terminates_backend_and_preserves_postcheck(self):
        process = self.finished_process()
        process.poll.return_value = None
        with patch("venfire.boot.subprocess.Popen", return_value=process), \
                patch("venfire.boot.time.sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_probe()
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)
        report = json.loads((self.output / "result.json").read_text())
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertEqual(report["error_type"], "KeyboardInterrupt")


if __name__ == "__main__":
    unittest.main()
