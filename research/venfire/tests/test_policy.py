"""Profile injection here is a fixture; there is no deployed profile override."""

import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from venfire.host import HostEligibilityError, HostEvidence, HostReport
from venfire import policy


def host_report(*, apple=False, intel=True, avx2=True, x86_64=True, vm=False):
    evidence = (
        HostEvidence("x86_64", x86_64, "x86_64 required"),
        HostEvidence("intel_cpu", intel, "Intel required"),
        HostEvidence("avx2", avx2, "AVX2 required"),
        HostEvidence("apple_platform", apple, "Apple required"),
        HostEvidence("known_vm_absent", not vm, "VM absent required"),
    )
    reasons = tuple(item.detail for item in evidence if not item.passed)
    return HostReport(not reasons, "Linux", "x86_64", None,
                      "GenuineIntel" if intel else None, evidence, reasons)


class BuildProfileTests(unittest.TestCase):
    def test_missing_generated_marker_defaults_to_release(self):
        error = ModuleNotFoundError("missing", name="venfire._build_profile")
        with patch.object(policy.importlib, "import_module", side_effect=error):
            self.assertEqual(policy.load_build_profile(), "release")

    def test_literal_profiles_are_the_only_valid_profiles(self):
        for value in ("release", "developer-nonredistributable"):
            with self.subTest(value=value), \
                    patch.object(policy.importlib, "import_module", return_value=SimpleNamespace(BUILD_PROFILE=value)):
                self.assertEqual(policy.load_build_profile(), value)
        for value in (True, "developer", "", None):
            with self.subTest(value=value), \
                    patch.object(policy.importlib, "import_module", return_value=SimpleNamespace(BUILD_PROFILE=value)):
                with self.assertRaises(policy.BuildPolicyError):
                    policy.load_build_profile()

    def test_broken_marker_dependency_is_not_treated_as_release(self):
        error = ModuleNotFoundError("missing dependency", name="unrelated_dependency")
        with patch.object(policy.importlib, "import_module", side_effect=error):
            with self.assertRaises(policy.BuildPolicyError):
                policy.load_build_profile()

    def test_release_gate_rejects_developer_build(self):
        with patch.object(policy, "load_build_profile", return_value=policy.DEVELOPER_PROFILE):
            with self.assertRaisesRegex(policy.BuildPolicyError, "release packaging rejects"):
                policy.require_release_build()
        with patch.object(policy, "load_build_profile", return_value=policy.RELEASE_PROFILE):
            self.assertEqual(policy.require_release_build(), "release")


class HostPolicyTests(unittest.TestCase):
    def setUp(self):
        self.marker = patch.object(policy, "load_build_profile", return_value=policy.DEVELOPER_PROFILE)
        self.marker_mock = self.marker.start()
        self.addCleanup(self.marker.stop)
        self.detector = patch.object(policy, "detect_host", return_value=host_report())
        self.detector_mock = self.detector.start()
        self.addCleanup(self.detector.stop)

    def test_release_rejects_explicit_flag_before_host_inspection(self):
        self.marker_mock.return_value = policy.RELEASE_PROFILE
        with self.assertRaisesRegex(policy.BuildPolicyError, "NONREDISTRIBUTABLE"):
            policy.authorize_host(developer_host_bypass=True)
        self.detector_mock.assert_not_called()

    def test_developer_profile_requires_explicit_flag_on_pc(self):
        with self.assertRaises(HostEligibilityError):
            policy.authorize_host()
        authorization = policy.authorize_host(developer_host_bypass=True)
        self.assertTrue(authorization.developer_bypass_applied)
        self.assertFalse(authorization.report.eligible)
        self.assertTrue(authorization.report.cpu_eligible)
        self.assertEqual(authorization.distribution_status, policy.DEVELOPER_DISTRIBUTION_STATUS)
        rendered = authorization.to_dict()
        self.assertFalse(rendered["cpu_requirements_waived"])
        self.assertFalse(rendered["artifact_or_guest_trust_waived"])
        self.assertIn("NONREDISTRIBUTABLE", json.dumps(rendered))

    def test_lab_vm_allowed_only_by_explicit_developer_flag(self):
        self.detector_mock.return_value = host_report(vm=True)
        with self.assertRaises(HostEligibilityError):
            policy.authorize_host()
        self.assertTrue(policy.authorize_host(developer_host_bypass=True).developer_bypass_applied)

    def test_intel_avx2_and_64_bit_stay_mandatory_in_developer_build(self):
        for failure in (dict(intel=False), dict(avx2=False), dict(x86_64=False)):
            with self.subTest(failure=failure):
                self.detector_mock.return_value = host_report(**failure)
                with self.assertRaises(HostEligibilityError):
                    policy.authorize_host(developer_host_bypass=True)

    def test_missing_cpu_evidence_cannot_be_waived(self):
        self.detector_mock.return_value = HostReport(False, "unknown", "unknown", None, None, (), ("unknown",))
        with self.assertRaises(HostEligibilityError):
            policy.authorize_host(developer_host_bypass=True)

    def test_environment_cannot_enable_developer_profile_or_flag(self):
        self.marker_mock.return_value = policy.RELEASE_PROFILE
        with patch.dict(os.environ, {"VENFIRE_BUILD_PROFILE": policy.DEVELOPER_PROFILE,
                                     "VENFIRE_DEVELOPER_HOST_BYPASS": "1"}):
            with self.assertRaises(HostEligibilityError):
                policy.authorize_host()
            with self.assertRaises(policy.BuildPolicyError):
                policy.authorize_host(developer_host_bypass=True)

    def test_developer_on_apple_without_flag_stays_marked_nonredistributable(self):
        self.detector_mock.return_value = host_report(apple=True)
        result = policy.authorize_host()
        self.assertFalse(result.developer_bypass_applied)
        self.assertEqual(result.distribution_status, policy.DEVELOPER_DISTRIBUTION_STATUS)

    def test_normal_release_accepts_valid_linux_apple_evidence(self):
        self.marker_mock.return_value = policy.RELEASE_PROFILE
        self.detector_mock.return_value = host_report(apple=True)
        result = policy.authorize_host()
        self.assertEqual(result.profile, "release")
        self.assertFalse(result.developer_bypass_applied)

    def test_truthy_nonboolean_flag_is_rejected(self):
        with self.assertRaises(policy.BuildPolicyError):
            policy.authorize_host(developer_host_bypass="false")


if __name__ == "__main__":
    unittest.main()
