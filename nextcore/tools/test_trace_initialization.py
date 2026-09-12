"""Authored initialization-tier CLI tests; no firmware or original input is run."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import test_trace_long as long
import trace_deep_arm_jit_ovmf as trace
import verify_ubfm_consumer_ovmf as fixture


BUDGET = 67108864
BUILD = "NXARMJIT: TRACE_INITIALIZATION_DIAGNOSTIC_BUILD maximum=67108864"
SELECTED = "NXARMJIT: TRACE_INITIALIZATION_DIAGNOSTIC_SELECTED tier=67108864"


class InitializationTests(unittest.TestCase):
    def test_preflight_preserves_old_limits_and_requires_exact_opt_in(self):
        profile = ["--platform-profile", "nextcore-irq-compat-v1"]
        valid = ["--initialization-diagnostic", *profile, "--instruction-budget", str(BUDGET)]
        cases = [["--initialization-diagnostic", "--instruction-budget", str(BUDGET)],
                 ["--initialization-diagnostic", *profile],
                 [*profile, "--instruction-budget", str(BUDGET)], valid + ["--timeout", "601"]]
        for value in (65536, BUDGET - 1, BUDGET + 1):
            cases.append(["--initialization-diagnostic", *profile, "--instruction-budget", str(value)])
        for old in ("--tiered-diagnostic", "--deep-diagnostic", "--long-diagnostic"):
            cases += [valid + [old], [old, *profile, "--instruction-budget", str(BUDGET)]]
        helper = long.LongDiagnosticTests()
        for options in cases:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                with patch.object(trace.sys, "argv", helper.arguments(folder, options)), \
                        patch.object(trace, "digest") as digest, patch.object(trace.subprocess, "Popen") as process, \
                        contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        trace.main()
                    self.assertEqual(error.exception.code, 2)
                    digest.assert_not_called()
                    process.assert_not_called()
                self.assertFalse((folder / "result").exists())

    def test_exact_and_inherited_acknowledgements_are_required(self):
        full = [long.TIERED, long.DEEP, long.BUILD, BUILD, SELECTED, long.PROVIDER]
        cases = [(full, {}, 0)]
        cases += [([line for line in full if line != absent], {}, 1) for absent in full]
        cases += [(full[:-2] + [SELECTED.replace(str(BUDGET), "65536"), long.PROVIDER], {}, 1),
                  (full, {"retired": BUDGET + 1}, 1), (full, {"memory": False}, 1),
                  ([], {"rejected": True}, 1)]
        helper = long.LongDiagnosticTests()
        for markers, options, expected in cases:
            with self.subTest(markers=markers, options=options), tempfile.TemporaryDirectory() as temporary:
                status, receipt, config = helper.run_fixture(Path(temporary), markers, BUDGET,
                    "--initialization-diagnostic", **options)
                self.assertEqual(status, expected)
                self.assertEqual(config["DiagnosticTier"], "initialization-67108864")
                self.assertEqual(config["InstructionBudget"], BUDGET)
                self.assertTrue(receipt["initialization_diagnostic_requested"])
                self.assertEqual(receipt["diagnostic_completed"], expected == 0)
                self.assertFalse(receipt["long_diagnostic_requested"])
                self.assertFalse(receipt["macos_boot_verified"])

    def test_authored_bfm_wrapper_budget_deadline_and_exact_retirement(self):
        for retired, expected in ((BUDGET, 0), (BUDGET - 1, 1)):
            with self.subTest(retired=retired), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                efi = folder / "authored.efi"
                efi.write_bytes(b"mock EFI, not executable")
                output = folder / "result"
                calls = []

                def run(command, **kwargs):
                    calls.append((command, kwargs))
                    if command[0] == "llvm-objcopy":
                        Path(command[-1]).write_bytes(b"\x1f\x20\x03\xd5")
                    if "--initialization-diagnostic" in command:
                        firmware = Path(command[command.index("--output") + 1])
                        firmware.mkdir()
                        report = {"diagnostic_completed": True, "original_inputs_preserved": True,
                                  "esp_copies_preserved": True,
                                  "markers": ["NXARMJIT: TRACE_ENTER x1=0x42008000 x2=0x0"],
                                  "execution": {"status": 5, "retired": retired,
                                      "pc": fixture.PHYSICAL + fixture.ENTRY_OFFSET + 48,
                                      "registers": {"x0": 0x3412, "x1": 0x42008000, "x2": 0x34f00f, "x3": 0xcd00},
                                      "memory": {"provider_status": 0, "fetch_requests": BUDGET,
                                                 "data_requests": 0, "completed_data_operations": 0}}}
                        (firmware / "report.json").write_text(json.dumps(report))
                    return subprocess.CompletedProcess(command, 0, "", "")

                args = ["fixture", "--efi", str(efi), "--output", str(output),
                        "--instruction-family", "bitfield-merge", "--initialization-diagnostic"]
                with patch.object(fixture.sys, "argv", args), patch.object(fixture.subprocess, "run", run), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(fixture.main(), expected)
                command, kwargs = calls[-1]
                self.assertEqual(command[command.index("--instruction-budget") + 1], str(BUDGET))
                self.assertEqual(command[command.index("--timeout") + 1], "600")
                self.assertEqual(kwargs["timeout"], 620)
                self.assertNotIn("--long-diagnostic", command)
                self.assertEqual((output / "probe.S").read_text(), fixture.BITFIELD_MERGE_ASSEMBLY)
                receipt = json.loads((output / "receipt.json").read_text())
                self.assertTrue(receipt["initialization_diagnostic_requested"])
                self.assertEqual(receipt["passed"], expected == 0)
                self.assertFalse(receipt["original_images_used"])


if __name__ == "__main__":
    unittest.main()
