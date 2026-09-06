"""CLI evidence must survive failures and user interruption of an upload."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from venfire import cli


class RecoveryCLITests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "upload.json"
        self.argv = ["dfu-upload", "--socket", "unused-fixture-socket", "--image", "unused.img4",
                     "--sha256", "0" * 64, "--output", str(self.output)]
        self.authorization = {"fixture": "authorized for isolated CLI regression only"}

    def execute_failure(self, failure):
        with patch.object(cli, "authorize_host", return_value=SimpleNamespace(to_dict=lambda: self.authorization)), \
             patch("venfire.recovery.send_dfu_file", side_effect=failure), redirect_stdout(io.StringIO()) as emitted:
            result = cli.main(self.argv)
        return result, emitted.getvalue()

    def test_keyboard_interrupt_preserves_partial_json_and_is_reraised(self):
        interrupted = KeyboardInterrupt()
        interrupted.recovery_report = {"schema": 1, "transfer_complete": False,
            "bytes_sent": 4096, "blocks_sent": 2, "macos_boot_verified": False}
        with self.assertRaises(KeyboardInterrupt) as raised:
            self.execute_failure(interrupted)
        self.assertIs(raised.exception, interrupted)
        report = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(report["bytes_sent"], 4096)
        self.assertEqual(report["blocks_sent"], 2)
        self.assertFalse(report["transfer_complete"])
        self.assertEqual(report["host_authorization"], self.authorization)
        self.assertIn("KeyboardInterrupt", report["error"])

    def test_socket_failure_has_fresh_json_and_nonzero_result(self):
        result, emitted = self.execute_failure(ConnectionRefusedError("fixture socket refused"))
        self.assertEqual(result, 1)
        report = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertFalse(report["transfer_complete"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertEqual(report["host_authorization"], self.authorization)
        self.assertIn("ConnectionRefusedError", report["error"])
        self.assertIn("fixture socket refused", json.loads(emitted)["error"])

    def test_existing_evidence_is_never_overwritten_or_upload_started(self):
        self.output.write_bytes(b"existing evidence")
        with patch.object(cli, "authorize_host", return_value=SimpleNamespace(to_dict=lambda: self.authorization)), \
             patch("venfire.recovery.send_dfu_file") as send, redirect_stdout(io.StringIO()):
            result = cli.main(self.argv)
        self.assertEqual(result, 1)
        self.assertEqual(self.output.read_bytes(), b"existing evidence")
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
