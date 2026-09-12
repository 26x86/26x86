"""Authored fragmented-UART tests; no original kernel input is accessed."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import trace_deep_arm_jit_ovmf as trace


class TerminalTests(unittest.TestCase):
    def test_only_complete_lf_terminated_error_rows_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            serial = Path(temporary) / "serial.log"
            self.assertFalse(trace.terminal_error_complete(serial))
            for fragment in (b"", b"NXARMJIT: ERROR", b"NXARMJIT: ERROR status=",
                             b"NXARMJIT: ERROR status=ABORTED", b"NXARMJIT: ERROR status=ABORTED\r",
                             b"NXARMJIT: ERROR\n", b"NXARMJIT: ERROR status=\n",
                             b"NXARMJIT: ERROR status=\r\n", b"other\nNXARMJIT: ERROR status=ABORTED",
                             b"prefix NXARMJIT: ERROR status=ABORTED\n"):
                with self.subTest(fragment=fragment):
                    serial.write_bytes(fragment)
                    self.assertFalse(trace.terminal_error_complete(serial))
            for complete in (b"NXARMJIT: ERROR status=ABORTED\n",
                             b"NXARMJIT: ERROR status=INVALID_PARAMETER\r\n",
                             b"other\r\nNXARMJIT: ERROR status=ABORTED\r\npartial",
                             b"\x1b[31mNXARMJIT: ERROR status=ABORTED\x1b[0m\r\n"):
                with self.subTest(complete=complete):
                    serial.write_bytes(complete)
                    self.assertTrue(trace.terminal_error_complete(serial))

    def test_cli_waits_for_staged_status_and_lf_before_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            args = ["trace"]
            for name in ("efi", "kernel", "device-tree", "ovmf-code", "ovmf-vars"):
                path = folder / name
                path.write_bytes(b"authored-input")
                args += ["--" + name, str(path)]
            args += ["--output", str(folder / "result"), "--tools", str(Path(trace.__file__).parent),
                     "--physical-base", "0x40000000", "--virtual-base", "0xfffffe0000000000",
                     "--memory-size", "0x4000000", "--kernel-physical", "0x42000000",
                     "--allow-incomplete-sptm-prefix"]
            fixture = ["NXARMJIT: EFI_ENTRY", "NXARMJIT: CONFIG_PARSED", "NXARMJIT: KC_VALIDATED",
                       "NXARMJIT: TRACE_STAGING_VERIFIED", "NXARMJIT: TRACE_HANDOFF_UNPROVISIONED",
                       "NXARMJIT: TRACE_ENTER",
                       "NXARMJIT: TRACE_RETURN status=5 retired=8 pc=0x42000000 blocks=1 instruction=0x0",
                       "NXARMJIT: TRACE_REGISTERS x0=0x0 x1=0x0 x2=0x0 x3=0x0",
                       "NXARMJIT: TRACE_ONLY"]
            stages = [b"ABORTED", b"\r", b"\n"]
            events = []

            class Process:
                returncode = None

                def __init__(self, command, **_kwargs):
                    self.serial = Path(next(value[5:] for value in command if value.startswith("file:")))
                    self.serial.write_bytes(("\r\n".join(fixture) + "\r\nNXARMJIT: ERROR status=").encode())

                def poll(self):
                    return self.returncode

                def terminate(self):
                    events.append("terminate")
                    self.returncode = -15

                def wait(self, timeout):
                    events.append("wait")
                    return self.returncode

            def advance(_seconds):
                events.append("write")
                with (folder / "result/serial.log").open("ab") as stream:
                    stream.write(stages.pop(0))

            with patch.object(trace.sys, "argv", args), patch.object(trace.subprocess, "Popen", Process), \
                    patch.object(trace.time, "sleep", advance), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(trace.main(), 0)
            self.assertEqual(stages, [])
            self.assertEqual(events, ["write", "write", "write", "terminate", "wait"])
            receipt = json.loads((folder / "result/report.json").read_text())
            self.assertTrue(receipt["diagnostic_completed"])
            self.assertTrue(receipt["stopped_by_harness"])
            self.assertIsNone(receipt["failure"])
            self.assertEqual(receipt["markers"][-1], "NXARMJIT: ERROR status=ABORTED")
            self.assertFalse(receipt["macos_boot_verified"])


if __name__ == "__main__":
    unittest.main()
