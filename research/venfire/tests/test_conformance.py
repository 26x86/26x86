import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from venfire.conformance import CASES, GUESTS, parse_serial, run_conformance, verify_guest


def transcript(status="PASS"):
    return "VENFIRE|BEGIN|1\n" + "".join(
        f"VENFIRE|{status}|{name}\n" for name in CASES
    ) + "VENFIRE|DONE|1\n"


class EvidenceParsingTests(unittest.TestCase):
    def test_complete_success_requires_clean_exit(self):
        self.assertTrue(parse_serial(transcript())["passed"])
        self.assertFalse(parse_serial(transcript(), returncode=1)["passed"])
        self.assertFalse(parse_serial(transcript(), timed_out=True)["passed"])

    def test_unsupported_is_not_success(self):
        result = parse_serial(transcript().replace("PASS|pauth_roundtrip", "UNSUPPORTED|pauth_roundtrip"))
        self.assertFalse(result["passed"])
        self.assertEqual(result["cases"][2]["status"], "unsupported")

    def test_incomplete_serial_never_becomes_success(self):
        for serial in ("", "VENFIRE|DONE|1\n", transcript().replace("VENFIRE|DONE|1\n", ""),
                       transcript().replace("VENFIRE|PASS|pauth_wrong_context\n", "")):
            with self.subTest(serial=serial):
                self.assertFalse(parse_serial(serial)["passed"])

    def test_duplicate_and_contradictory_evidence_fail_closed(self):
        duplicate = "VENFIRE|FAIL|pauth_roundtrip\n"
        serial = transcript().replace("VENFIRE|DONE|1", duplicate + "VENFIRE|DONE|1")
        self.assertFalse(parse_serial(serial)["passed"])
        serial = transcript().replace("VENFIRE|BEGIN|1", "VENFIRE|PASS|self_modify\nVENFIRE|BEGIN|1")
        self.assertFalse(parse_serial(serial)["passed"])


class ConformanceSafetyTests(unittest.TestCase):
    def test_bundled_guest_matches_reviewable_source(self):
        for target in ("virt", "vmapple"):
            self.assertTrue(verify_guest(target).is_file())

    def test_mutated_guest_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "guests"
            shutil.copytree(GUESTS, copied)
            (copied / "virt.elf").write_bytes(b"not a 26x86 guest")
            with patch("venfire.conformance.GUESTS", copied):
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    verify_guest("virt")

    def test_timeout_is_bounded_and_finite(self):
        for timeout in (0, -1, 301, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                run_conformance("not-executed", Path("not-created"), timeout=timeout)

    def test_guest_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "guests"
            shutil.copytree(GUESTS, copied)
            (copied / "virt.elf").unlink()
            try:
                (copied / "virt.elf").symlink_to(GUESTS / "virt.elf")
            except (OSError, NotImplementedError):
                self.skipTest("Host does not permit test symlinks")
            with patch("venfire.conformance.GUESTS", copied):
                with self.assertRaisesRegex(ValueError, "Symlink|reparse"):
                    verify_guest("virt")

    def test_existing_output_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory)
            sentinel = existing / "synthetic-aux.bin"
            sentinel.write_bytes(b"preserve existing data")
            with self.assertRaises(FileExistsError):
                run_conformance("not-executed", existing, target="vmapple")
            self.assertEqual(sentinel.read_bytes(), b"preserve existing data")

    def test_generated_drive_paths_escape_commas(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "comma,here"
            fake = subprocess.CompletedProcess([], 0, "fixture backend\n", "")
            executed = subprocess.CompletedProcess([], 1, "", "fixture: no guest execution")
            with patch("venfire.conformance.subprocess.run", side_effect=[fake, executed]):
                report = run_conformance("fixture-qemu", output, target="vmapple")
            drives = [arg for arg in report["command"] if arg.startswith("if=pflash")]
            self.assertEqual(len(drives), 2)
            self.assertTrue(all("comma,,here" in arg and "readonly=on" in arg for arg in drives))
            self.assertFalse(report["passed"])


@unittest.skipUnless(os.environ.get("VENFIRE_TEST_QEMU"), "set VENFIRE_TEST_QEMU for actual TCG execution")
class ActualTCGTests(unittest.TestCase):
    def test_actual_guest_completes_all_required_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_conformance(os.environ["VENFIRE_TEST_QEMU"], Path(directory) / "run")
            self.assertTrue(report["passed"], json.dumps(report, indent=2))
            self.assertFalse(report["macos_boot_verified"])


if __name__ == "__main__":
    unittest.main()
