"""Failure receipts must survive missing source reads and compiler timeouts."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_metal_probe as builder


class BuildReceiptFailures(unittest.TestCase):
    def test_post_hash_failure_still_records_compile_failure(self):
        original = builder.digest
        calls = 0

        def fail_post_source(path):
            nonlocal calls
            if path.name == "metal_compute_probe.c":
                calls += 1
                if calls == 2:
                    raise OSError("authored source read failure")
            return original(path)

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "build"
            with patch("sys.argv", ["probe", "--output", str(output)]), \
                 patch.object(builder.shutil, "which", return_value="/authored/compiler"), \
                 patch.object(builder, "digest", side_effect=fail_post_source), \
                 patch.object(builder.subprocess, "run", return_value=subprocess.CompletedProcess([], 7, b"", b"compile failure")), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(builder.main(), 1)
            receipt = json.loads((output / "build-receipt.json").read_text())
            self.assertFalse(receipt["build_passed"])
            self.assertFalse(receipt["source_unchanged"])
            self.assertIsNone(receipt["source_sha256_after"])
            self.assertIn("source read failure", receipt["source_hash_error"])
            self.assertEqual(receipt["commands"][0]["exit_code"], 7)
            self.assertEqual((output / "compile.stderr.txt").read_bytes(), b"compile failure")

    def test_timeout_records_argv_and_partial_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "build"
            with patch("sys.argv", ["probe", "--output", str(output)]), \
                 patch.object(builder.shutil, "which", return_value="/authored/compiler"), \
                 patch.object(builder.subprocess, "run", side_effect=subprocess.TimeoutExpired("authored", 45, output=b"partial out", stderr=b"partial err")), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(builder.main(), 1)
            receipt = json.loads((output / "build-receipt.json").read_text())
            self.assertFalse(receipt["build_passed"])
            self.assertFalse(receipt["guest_executed"])
            self.assertEqual(len(receipt["commands"]), 1)
            command = receipt["commands"][0]
            self.assertEqual(command["argv"][0], "/authored/compiler")
            self.assertTrue(command["timed_out"])
            self.assertIsNone(command["exit_code"])
            self.assertEqual((output / "compile.stdout.txt").read_bytes(), b"partial out")
            self.assertEqual((output / "compile.stderr.txt").read_bytes(), b"partial err")


if __name__ == "__main__":
    unittest.main()
