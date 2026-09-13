"""Authored CLI contract tests; mocked serial output is not firmware evidence."""
import contextlib
import io
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

import trace_deep_arm_jit_ovmf as trace


BUILD = "NXARMJIT: TRACE_LONG_DIAGNOSTIC_BUILD maximum=65536"
SELECTED = "NXARMJIT: TRACE_LONG_DIAGNOSTIC_SELECTED tier=65536"
TIERED = "NXARMJIT: TRACE_TIERED_DIAGNOSTIC maximum=4096"
DEEP = "NXARMJIT: TRACE_DEEP_DIAGNOSTIC_BUILD maximum=16384"
PROVIDER = "NXARMJIT: TRACE_MEMORY_PROVIDER abi=1 mode=m0-only"


class LongDiagnosticTests(unittest.TestCase):
    def arguments(self, folder, options):
        args = ["trace"]
        for name in ("efi", "kernel", "device-tree", "ovmf-code", "ovmf-vars"):
            path = folder / name
            path.write_bytes(b"authored-host-test-input")
            args += ["--" + name, str(path)]
        return args + ["--output", str(folder / "result"), "--tools", str(Path(trace.__file__).parent),
                       "--physical-base", "0x40000000", "--virtual-base", "0xfffffe0000000000",
                       "--memory-size", "0x4000000", "--kernel-physical", "0x42000000",
                       "--allow-incomplete-sptm-prefix", *options]

    def test_invalid_selection_fails_before_helpers_output_or_process(self):
        profile = ["--platform-profile", "nextcore-irq-compat-v1"]
        invalid = [
            ["--long-diagnostic", "--instruction-budget", "65536"],
            ["--long-diagnostic", *profile],
            ["--long-diagnostic", *profile, "--instruction-budget", "16384"],
            ["--long-diagnostic", *profile, "--instruction-budget", "65535"],
            ["--long-diagnostic", *profile, "--instruction-budget", "65537"],
            [*profile, "--instruction-budget", "65536"],
            ["--tiered-diagnostic", *profile, "--instruction-budget", "65536"],
            ["--deep-diagnostic", *profile, "--instruction-budget", "65536"],
            ["--long-diagnostic", "--deep-diagnostic", *profile, "--instruction-budget", "65536"],
            ["--long-diagnostic", "--tiered-diagnostic", *profile, "--instruction-budget", "65536"],
            ["--instruction-budget", "9"],
            [*profile, "--instruction-budget", "65"],
            ["--tiered-diagnostic", *profile, "--instruction-budget", "4097"],
        ]
        for options in invalid:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                with patch.object(trace.sys, "argv", self.arguments(folder, options)), \
                        patch.object(trace, "digest") as digest, \
                        patch.object(trace.subprocess, "Popen") as process, \
                        contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        trace.main()
                    self.assertEqual(error.exception.code, 2)
                    digest.assert_not_called()
                    process.assert_not_called()
                self.assertFalse((folder / "result").exists())

    def run_fixture(self, folder, markers, budget=65536, selector="--long-diagnostic", retired=None, memory=True, rejected=False):
        retired = budget if retired is None else retired
        options = ["--platform-profile", "nextcore-irq-compat-v1", "--instruction-budget", str(budget)]
        if selector:
            options.append(selector)
        fixture = ["NXARMJIT: EFI_ENTRY", *markers, "NXARMJIT: CONFIG_PARSED", "NXARMJIT: KC_VALIDATED",
                   "NXARMJIT: TRACE_STAGING_VERIFIED", "NXARMJIT: TRACE_HANDOFF_UNPROVISIONED",
                   "NXARMJIT: TRACE_ENTER",
                   f"NXARMJIT: TRACE_RETURN status=5 retired={retired} pc=0x42000000 blocks=1 instruction=0x0",
                   "NXARMJIT: TRACE_REGISTERS x0=0x0 x1=0x0 x2=0x0 x3=0x0",
                   "NXARMJIT: TRACE_PLATFORM_STATE profile=1 override=0x0 pending=0 pstate=0x3c5 sp=0x0",
                   "NXARMJIT: TRACE_EXCEPTION_STATE elr=0x0 spsr=0x0 vector=0x0 esr=0x0 handler_executed=false"]
        if memory:
            fixture.append(f"NXARMJIT: TRACE_MEMORY_RESULT abi=1 provider_status=0 guest_far=0x0 last_address=0x42000000 fetch_requests={retired} data_requests=0 completed_data_operations=0")
        fixture += ["NXARMJIT: TRACE_ONLY", "NXARMJIT: ERROR status=ABORTED"]
        if rejected:
            fixture = ["NXARMJIT: EFI_ENTRY", "NXARMJIT: ERROR status=INVALID_PARAMETER"]

        class Process:
            returncode = 0

            def __init__(self, command, **_kwargs):
                serial = next(value[5:] for value in command if value.startswith("file:"))
                Path(serial).write_text("\n".join(fixture) + "\n")

            def poll(self):
                return self.returncode

        with patch.object(trace.sys, "argv", self.arguments(folder, options)), \
                patch.object(trace.subprocess, "Popen", Process), contextlib.redirect_stdout(io.StringIO()):
            status = trace.main()
        receipt = json.loads((folder / "result/report.json").read_text())
        config = plistlib.loads((folder / "result/esp/EFI/OC/config.plist").read_bytes())
        return status, receipt, config["Nextcore"]["Kernel"]["Trace"]

    def test_acknowledgements_and_execution_checks_are_required(self):
        full = [TIERED, DEEP, BUILD, SELECTED, PROVIDER]
        cases = [(full, {}, 0)]
        cases += [([line for line in full if line != missing], {}, 1) for missing in full]
        cases += [([TIERED, DEEP, PROVIDER], {}, 1),
                  ([TIERED, DEEP, BUILD, SELECTED.replace("65536", "16384"), PROVIDER], {}, 1),
                  ([TIERED, DEEP, BUILD.replace("65536", "16384"), SELECTED, PROVIDER], {}, 1),
                  (full, {"retired": 65537}, 1), (full, {"memory": False}, 1),
                  ([], {"rejected": True}, 1)]
        for markers, options, expected in cases:
            with self.subTest(markers=markers, options=options), tempfile.TemporaryDirectory() as temporary:
                status, receipt, config = self.run_fixture(Path(temporary), markers, **options)
                self.assertEqual(status, expected)
                self.assertEqual(config["DiagnosticTier"], "long-65536")
                self.assertEqual(config["InstructionBudget"], 65536)
                self.assertTrue(receipt["long_diagnostic_requested"])
                self.assertEqual(receipt["diagnostic_completed"], expected == 0)
                self.assertEqual(receipt["requested_checks_completed"], expected == 0)
                self.assertFalse(receipt["macos_boot_verified"])

    def test_existing_tiers_do_not_require_long_acknowledgements(self):
        for selector, budget, markers, tier in (
                (None, 64, [], None),
                ("--tiered-diagnostic", 4096, [TIERED], None),
                ("--deep-diagnostic", 16384,
                 [TIERED, DEEP, PROVIDER, "NXARMJIT: TRACE_DEEP_DIAGNOSTIC_SELECTED tier=16384"], "deep-16384")):
            with self.subTest(selector=selector), tempfile.TemporaryDirectory() as temporary:
                status, receipt, config = self.run_fixture(Path(temporary), markers, budget, selector)
                self.assertEqual(status, 0)
                self.assertEqual(config.get("DiagnosticTier"), tier)
                self.assertFalse(receipt["long_diagnostic_requested"])


if __name__ == "__main__":
    unittest.main()
