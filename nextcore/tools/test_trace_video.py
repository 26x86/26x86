"""Authored host receipts only; these tests do not run firmware or prove display."""
import contextlib
import io
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

import trace_deep_arm_jit_ovmf as trace

BASE = 0x40000000
SIZE = 0x4000000
READY = "NXARMJIT: TRACE_VIDEO_READY width=640 height=480 base=0x42000000 row_bytes=2560"
PRESENTED = "NXARMJIT: TRACE_VIDEO_PRESENTED status=SUCCESS"


class VideoReceiptTests(unittest.TestCase):
    def test_ready_and_presented_are_independent_from_request_and_each_other(self):
        self.assertEqual(trace.parse_trace_video([], False, BASE, SIZE)["status"], "not-requested")
        self.assertFalse(trace.parse_trace_video([], True, BASE, SIZE)["validated"])
        self.assertFalse(trace.parse_trace_video([PRESENTED], True, BASE, SIZE)["validated"])
        ready = trace.parse_trace_video([READY], True, BASE, SIZE)
        self.assertTrue(ready["configuration_validated"])
        self.assertFalse(ready["presented"])
        valid = trace.parse_trace_video([READY + " bytes=1228800", PRESENTED], True, BASE, SIZE)
        self.assertTrue(valid["validated"])
        self.assertEqual(valid["geometry"]["visible_span_bytes"], 1228800)
        self.assertFalse(valid["physical_display_verified"])

    def test_unavailable_duplicate_or_malformed_markers_never_validate(self):
        for markers in ([READY, PRESENTED, "NXARMJIT: TRACE_VIDEO_UNAVAILABLE error=BLIT"],
                        [READY, READY, PRESENTED], [READY, PRESENTED, PRESENTED], [PRESENTED, READY],
                        [READY, PRESENTED.replace("SUCCESS", "ERROR")]):
            self.assertFalse(trace.parse_trace_video(markers, True, BASE, SIZE)["validated"])
        for invalid in (READY.replace("width=640", "width=0"), READY.replace("row_bytes=2560", "row_bytes=2559"),
                        READY.replace("0x42000000", "0x44000000"), READY + " bytes=1",
                        READY + " bytes=18446744073709551615", READY.replace("height=480", "height=4294967296")):
            self.assertFalse(trace.parse_trace_video([invalid, PRESENTED], True, BASE, SIZE)["validated"])

    def test_cli_writes_opt_in_and_keeps_completed_execution_when_old_efi_ignores_it(self):
        for requested, markers, expected_status in ((False, [], 0), (True, [], 1),
                (True, [READY], 1), (True, [READY, PRESENTED], 0),
                (True, ["NXARMJIT: TRACE_VIDEO_UNAVAILABLE error=NO_GOP"], 1)):
            with self.subTest(requested=requested, markers=markers), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                inputs = {name: folder / name for name in ("efi", "kernel", "device-tree", "ovmf-code", "ovmf-vars")}
                for path in inputs.values():
                    path.write_bytes(b"authored-host-test-input")
                output = folder / "result"
                args = ["trace"]
                for name, path in inputs.items():
                    args += ["--" + name, str(path)]
                args += ["--output", str(output), "--tools", str(Path(trace.__file__).parent),
                         "--physical-base", hex(BASE), "--virtual-base", "0xfffffe0000000000",
                         "--memory-size", str(SIZE), "--kernel-physical", "0x42000000",
                         "--allow-incomplete-sptm-prefix"]
                if requested:
                    args.append("--gop-framebuffer")
                fixture = ["NXARMJIT: EFI_ENTRY", "NXARMJIT: CONFIG_PARSED", "NXARMJIT: KC_VALIDATED",
                           "NXARMJIT: TRACE_STAGING_VERIFIED", "NXARMJIT: TRACE_HANDOFF_UNPROVISIONED",
                           *markers, "NXARMJIT: TRACE_ENTER",
                           "NXARMJIT: TRACE_RETURN status=1 retired=1 pc=0x42000004 blocks=1 instruction=0x0",
                           "NXARMJIT: TRACE_REGISTERS x0=0x0 x1=0x0 x2=0x0 x3=0x0",
                           "NXARMJIT: TRACE_ONLY", "NXARMJIT: ERROR status=ABORTED"]

                class Process:
                    returncode = 0

                    def __init__(self, command, **_kwargs):
                        serial = next(value[5:] for value in command if value.startswith("file:"))
                        Path(serial).write_text("\n".join(fixture) + "\n")

                    def poll(self):
                        return self.returncode

                with patch.object(trace.sys, "argv", args), patch.object(trace.subprocess, "Popen", Process), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(trace.main(), expected_status)
                config = plistlib.loads((output / "esp/EFI/OC/config.plist").read_bytes())
                actual = config["Nextcore"]["Kernel"]["Trace"]
                self.assertEqual(actual.get("Video"), "gop-framebuffer" if requested else None)
                receipt = json.loads((output / "report.json").read_text())
                self.assertTrue(receipt["diagnostic_completed"])
                self.assertEqual(receipt["video_requested"], requested)
                self.assertEqual(receipt["requested_checks_completed"], expected_status == 0)
                self.assertFalse(receipt["macos_boot_verified"])


if __name__ == "__main__":
    unittest.main()
