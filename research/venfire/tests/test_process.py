"""Actual helper processes validate pipe pressure, limits and termination."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from venfire.process import BoundedProcessError, run_bounded


class BoundedProcessTests(unittest.TestCase):
    def run_python(self, code, **options):
        return run_bounded([sys.executable, "-u", "-c", code], **options)

    def test_binary_streams_are_preserved_and_stdin_is_eof(self):
        result = self.run_python("import sys; assert sys.stdin.buffer.read() == b''; "
            "sys.stdout.buffer.write(bytes(range(256))); sys.stderr.buffer.write(b'err\\x00\\xff')")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, bytes(range(256)))
        self.assertEqual(result.stderr, b"err\x00\xff")

    def test_busy_stderr_does_not_block_quiet_stdout(self):
        result = self.run_python("import os; os.write(2, b'e' * 262144); os.write(1, b'done')",
                                 timeout=5, stderr_limit=262144)
        self.assertEqual(result.stdout, b"done")
        self.assertEqual(result.stderr, b"e" * 262144)
        self.assertEqual(result.returncode, 0)

    def test_both_pipes_beyond_kernel_buffers_are_drained(self):
        result = self.run_python("import os\nfor _ in range(128):\n"
            " os.write(1,b'o'*4096)\n os.write(2,b'e'*4096)",
            timeout=5, stdout_limit=524288, stderr_limit=524288)
        self.assertEqual(result.stdout, b"o" * 524288)
        self.assertEqual(result.stderr, b"e" * 524288)

    def test_each_limit_terminates_writer_and_keeps_bounded_output(self):
        for name, fd in (("stdout", 1), ("stderr", 2)):
            with self.subTest(stream=name):
                with self.assertRaises(BoundedProcessError) as raised:
                    self.run_python("import os,time; os.write(1,b'out'); os.write(2,b'err'); "
                        f"os.write({fd},b'x'*1000000); time.sleep(30)",
                        timeout=5, stdout_limit=1024, stderr_limit=1024)
                error = raised.exception
                self.assertEqual(error.reason, name + "-limit")
                self.assertEqual(len(getattr(error, name)), 1024)
                self.assertLessEqual(len(error.stdout), 1024)
                self.assertLessEqual(len(error.stderr), 1024)
                self.assertTrue(error.stdout.startswith(b"out"))
                self.assertTrue(error.stderr.startswith(b"err"))
                self.assertIsNotNone(error.returncode)
                self.assertLess(error.elapsed, 5)

    def test_exact_and_zero_limits(self):
        result = self.run_python("import os; os.write(1,b'1234')", stdout_limit=4, stderr_limit=0)
        self.assertEqual(result.stdout, b"1234")
        with self.assertRaises(BoundedProcessError) as raised:
            self.run_python("import os; os.write(2,b'!')", stderr_limit=0)
        self.assertEqual(raised.exception.reason, "stderr-limit")
        self.assertEqual(raised.exception.stderr, b"")

    def test_timeout_preserves_diagnostics_and_reaps_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = str(Path(temporary) / "must-not-exist")
            with self.assertRaises(BoundedProcessError) as raised:
                self.run_python("import os,time; os.write(1,b'ready'); os.write(2,b'waiting'); "
                    f"time.sleep(1.5); open({marker!r},'w').write('survived')", timeout=0.5)
            error = raised.exception
            self.assertEqual(error.reason, "timeout")
            self.assertEqual(error.stdout, b"ready")
            self.assertEqual(error.stderr, b"waiting")
            self.assertIsNotNone(error.returncode)
            self.assertLess(error.elapsed, 2)
            time.sleep(1.2)
            self.assertFalse(Path(marker).exists())

    def test_nonzero_exit_is_returned_with_check_returncode(self):
        result = self.run_python("import sys; print('why',file=sys.stderr); sys.exit(17)")
        self.assertEqual(result.returncode, 17)
        self.assertEqual(result.stderr.strip(), b"why")
        with self.assertRaises(subprocess.CalledProcessError) as raised:
            result.check_returncode()
        self.assertEqual(raised.exception.stderr, result.stderr)

    def test_pipe_read_failure_has_reason_and_reaps_child(self):
        with patch("venfire.process._read_ready", side_effect=OSError("fixture read failed")):
            with self.assertRaises(BoundedProcessError) as raised:
                self.run_python("import time; time.sleep(30)")
        self.assertEqual(raised.exception.reason, "pipe-read-error")
        self.assertIn("fixture read failed", str(raised.exception))
        self.assertIsNotNone(raised.exception.returncode)

    def test_invalid_limits_are_rejected_before_spawn(self):
        with patch("venfire.process.subprocess.Popen") as spawn:
            for options in ({"timeout": 0}, {"timeout": float("inf")}, {"timeout": float("nan")},
                            {"timeout": True}, {"stdout_limit": -1}, {"stderr_limit": 1.5},
                            {"stderr_limit": True}):
                with self.subTest(options=options), self.assertRaises(ValueError):
                    run_bounded(["unused"], **options)
            for command in ("shell string", [], b"shell bytes"):
                with self.assertRaises(ValueError):
                    run_bounded(command)
        spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
