"""Offline contract tests for the layered boot/runtime harness."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import tempfile
import unittest


class BootRuntimeHarnessTests(unittest.TestCase):
    def _args(self, output: str) -> Namespace:
        return Namespace(
            output=output,
            target=27,
            qemu=None,
            qemu_img=None,
            firmware=None,
            vm_json=None,
            memory_mib=4096,
            smp=2,
            duration=None,
            observation_timeout=1.0,
            efi_timeout=1.0,
            synthetic_timeout=1.0,
            skip_contracts=True,
            skip_efi=True,
            skip_ovmf=True,
            skip_tcg=False,
            run_synthetic=False,
            require_tcg=False,
            require_macos=False,
        )

    def test_external_input_contract_is_explicit_when_assets_are_missing(self) -> None:
        from Tools.verify_boot_runtime import _external_contract

        with tempfile.TemporaryDirectory() as directory:
            contract = _external_contract(self._args(directory))
        self.assertFalse(contract["runnable"])
        self.assertEqual(set(contract["missing"]), {"qemu", "qemu_img", "firmware", "vm_json"})
        self.assertGreaterEqual(len(contract["requirements"]), 6)
        self.assertTrue(contract["native_m1_requirements"])

    def test_contract_only_run_is_successful_but_macos_stays_blocked(self) -> None:
        from Tools.verify_boot_runtime import verify

        with tempfile.TemporaryDirectory() as directory:
            output = str(Path(directory) / "evidence")
            report = verify(self._args(output))
            saved = Path(output) / "report.json"
            self.assertTrue(saved.is_file())
        self.assertTrue(report["passed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertEqual(report["layer_status"]["macos"], "blocked")
        self.assertIn("firmware", report["external_input_contract"]["missing"])

    def test_require_macos_does_not_get_promoted_by_missing_input(self) -> None:
        from Tools.verify_boot_runtime import verify

        with tempfile.TemporaryDirectory() as directory:
            args = self._args(str(Path(directory) / "evidence"))
            args.require_macos = True
            report = verify(args)
        self.assertFalse(report["passed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertIn("required target-matching macOS boot evidence was not observed", report["errors"])


if __name__ == "__main__":
    unittest.main()
