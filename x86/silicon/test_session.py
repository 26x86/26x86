"""Unit tests for ``x86.silicon.session`` — the single most important safety check
in this package: no fixture, in any configuration, may ever report a real boot."""

from __future__ import annotations

import json
import unittest

from x86.silicon.mock_host import HOSTS
from x86.silicon.session import run_install_session


class InstallSessionTest(unittest.TestCase):
    def test_default_session_targets_golden_gate(self) -> None:
        result = run_install_session()
        self.assertEqual(result.target_os_name, "Golden Gate")

    def test_safety_fields_are_fixed_on_default_session(self) -> None:
        result = run_install_session()
        self.assertIs(result.simulated, True)
        self.assertIs(result.real_boot_verified, False)
        self.assertIs(result.xnu_executed, False)

    def test_safety_fields_are_fixed_across_every_fixture_host(self) -> None:
        for host in HOSTS:
            with self.subTest(host=host.host_id):
                result = run_install_session(
                    target_os=host.target_os_kernel,
                    inject_dfu_failure_at=host.inject_dfu_failure_at,
                    host_label=host.label,
                )
                self.assertIs(result.simulated, True)
                self.assertIs(result.real_boot_verified, False)
                self.assertIs(result.xnu_executed, False)

    def test_safety_fields_are_not_constructor_overridable(self) -> None:
        result = run_install_session()
        with self.assertRaises(AttributeError):
            result.simulated = False  # type: ignore[misc]

    def test_as_dict_is_json_safe_and_carries_safety_fields(self) -> None:
        payload = run_install_session().as_dict()
        json.dumps(payload)  # must not raise
        self.assertIs(payload["simulated"], True)
        self.assertIs(payload["real_boot_verified"], False)
        self.assertIs(payload["xnu_executed"], False)


if __name__ == "__main__":
    unittest.main()
