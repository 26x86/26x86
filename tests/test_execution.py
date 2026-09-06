"""Execution policy and bounded host probes; injected facts never prove hardware success."""

import dataclasses
import json
import subprocess
import unittest
from unittest.mock import patch

from x86.execution import (
    MODE_ENV,
    ExecutionMode,
    ExecutionPolicyError,
    HostFacts,
    detect_host,
    resolve_execution,
)


INTEL = HostFacts("Darwin", "x86_64", False, False)
ARM = HostFacts("Darwin", "arm64", True, False)
ROSETTA = HostFacts("Darwin", "x86_64", True, True)
WINDOWS = HostFacts("Windows", "AMD64")
LINUX = HostFacts("Linux", "x86_64")


class ExecutionPolicyTests(unittest.TestCase):
    def resolve(self, **kwargs):
        kwargs.setdefault("environ", {})
        kwargs.setdefault("facts", INTEL)
        return resolve_execution(**kwargs)

    def test_auto_native_intel_and_preparation_hosts(self):
        for facts in (INTEL, WINDOWS, LINUX, HostFacts("Windows", "ARM64"), HostFacts("Linux", "aarch64")):
            with self.subTest(facts=facts):
                context = self.resolve(facts=facts)
                self.assertEqual(context.mode.value, "x86")
                self.assertEqual(context.source, "host")
                self.assertIs(context.require_native_plan(), context)
                self.assertEqual(context.can_native_apply, facts is INTEL)
                if facts is INTEL:
                    self.assertIs(context.require_native_apply(), context)
                else:
                    with self.assertRaises(ExecutionPolicyError):
                        context.require_native_apply()

    def test_arm_and_rosetta_default_to_sandbox_and_block_all_native_paths(self):
        # Any positive ARM evidence wins, even if other injected fields disagree.
        for facts in (ARM, ROSETTA, HostFacts("Darwin", "x86_64", False, True),
                      HostFacts("Darwin", "arm64", False, False), HostFacts("Darwin", "arm64e"),
                      HostFacts("Darwin", "aarch64"), HostFacts("Darwin", "x86_64", True, None)):
            with self.subTest(facts=facts):
                context = self.resolve(facts=facts)
                self.assertTrue(context.is_sandbox)
                self.assertFalse(context.can_native_plan)
                self.assertFalse(context.can_native_apply)
                with self.assertRaises(ExecutionPolicyError):
                    context.require_native_plan()
                with self.assertRaises(ExecutionPolicyError):
                    context.require_native_apply()
                with self.assertRaises(ExecutionPolicyError) as error:
                    self.resolve(requested="x86", facts=facts)
                self.assertEqual(error.exception.code, "apple_silicon_native_mode_blocked")

    def test_stored_and_environment_x86_do_not_bypass_arm_detection(self):
        for kwargs in ({"settings": {"execution_mode": "x86"}}, {"environ": {MODE_ENV: "x86"}}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ExecutionPolicyError):
                self.resolve(facts=ROSETTA, **kwargs)

    def test_explicit_sandbox_restricts_native_intel_too(self):
        context = self.resolve(requested="apple-silicon-sandbox")
        self.assertEqual(context.source, "request")
        self.assertFalse(context.can_native_apply)
        self.assertFalse(context.can_native_plan)
        self.assertTrue(context.host.is_verified_native_x86_macos)

    def test_precedence(self):
        context = self.resolve(requested="x86", settings={"execution_mode": "apple-silicon-sandbox"})
        self.assertEqual((context.mode, context.source), (ExecutionMode.X86, "request"))
        context = self.resolve(environ={MODE_ENV: "apple-silicon-sandbox"}, settings={"execution_mode": "x86"})
        self.assertEqual((context.mode.value, context.source), ("apple-silicon-sandbox", "environment"))
        self.assertTrue(context.environment_locked)
        context = self.resolve(settings={"execution_mode": "apple-silicon-sandbox"})
        self.assertEqual(context.source, "settings")
        self.assertTrue(context.is_sandbox)

    def test_matching_explicit_and_environment_mode_is_allowed_but_locked(self):
        context = self.resolve(requested="x86", environ={MODE_ENV: "x86"})
        self.assertEqual(context.source, "request")
        self.assertTrue(context.environment_locked)

    def test_environment_lock_rejects_both_conflicting_directions(self):
        for requested, inherited in (("x86", "apple-silicon-sandbox"), ("apple-silicon-sandbox", "x86")):
            with self.subTest(requested=requested), self.assertRaises(ExecutionPolicyError) as error:
                self.resolve(requested=requested, environ={MODE_ENV: inherited})
            self.assertEqual(error.exception.code, "execution_mode_locked")

    def test_invalid_selected_modes_fail_closed(self):
        for invalid in ("", "auto", "X86", "x86 ", "native", "sandbox", False, 0, [], {}):
            for field in ("request", "environment", "settings"):
                kwargs = {"request": {"requested": invalid}, "environment": {"environ": {MODE_ENV: invalid}},
                          "settings": {"settings": {"execution_mode": invalid}}}[field]
                with self.subTest(invalid=invalid, field=field), self.assertRaises(ExecutionPolicyError):
                    self.resolve(**kwargs)

    def test_invalid_environment_is_not_ignored_by_explicit_request(self):
        with self.assertRaises(ExecutionPolicyError):
            self.resolve(requested="x86", environ={MODE_ENV: "broken"})

    def test_explicit_request_does_not_read_unused_setting_value(self):
        context = self.resolve(requested="x86", settings={"execution_mode": "old-invalid-setting"})
        self.assertEqual(context.mode, ExecutionMode.X86)

    def test_enum_request_and_mapping_facts(self):
        context = self.resolve(requested=ExecutionMode.X86, facts=dataclasses.asdict(INTEL))
        self.assertTrue(context.can_native_apply)

    def test_unknown_darwin_facts_never_permit_native_operations(self):
        for facts in (HostFacts("Darwin", "x86_64"), HostFacts("Darwin", "x86_64", False, None),
                      HostFacts("Darwin", "x86_64", None, False), HostFacts("Darwin", "i386", False, False),
                      HostFacts("Darwin", "", False, False), HostFacts("FreeBSD", "amd64"),
                      HostFacts("Darwin", "x86_64", False, False, ("probe failed",))):
            with self.subTest(facts=facts):
                context = self.resolve(facts=facts)
                with self.assertRaises(ExecutionPolicyError):
                    context.require_native_plan()
                with self.assertRaises(ExecutionPolicyError):
                    context.require_native_apply()

    def test_invalid_fact_types_and_unknown_fact_keys_are_rejected(self):
        for facts in ({"system": "Darwin", "machine": "x86_64", "hw_optional_arm64": "0"},
                      {"system": "Darwin", "machine": "x86_64", "proc_translated": 2},
                      {"system": "Darwin", "machine": "x86_64", "probe_errors": "ignored"},
                      {"system": "Darwin", "machine": "x86_64", "allow_native": True},
                      {"system": False, "machine": "x86_64"}, [], "Darwin"):
            with self.subTest(facts=facts), self.assertRaises(ExecutionPolicyError):
                self.resolve(facts=facts)

    def test_context_is_immutable_and_json_does_not_expose_mutable_internal_errors(self):
        context = self.resolve(facts=HostFacts("Darwin", "x86_64", None, False, ("probe failed",)))
        payload = context.as_dict()
        json.dumps(payload)
        payload["host"]["probe_errors"].clear()
        self.assertEqual(context.host.probe_errors, ("probe failed",))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.mode = ExecutionMode.APPLE_SILICON_SANDBOX

    def test_no_implicit_settings_io_and_explicit_empty_environ_is_respected(self):
        with patch.dict("os.environ", {MODE_ENV: "apple-silicon-sandbox"}), \
             patch("x86.settings.SettingsStore", side_effect=AssertionError("no settings I/O")):
            self.assertEqual(self.resolve().mode, ExecutionMode.X86)
            inherited = resolve_execution(facts=INTEL)
            self.assertTrue(inherited.is_sandbox)

    def test_default_calls_real_host_detector_once(self):
        with patch("x86.execution.detect_host", return_value=WINDOWS) as detect:
            context = resolve_execution(environ={})
        detect.assert_called_once_with()
        self.assertTrue(context.can_native_plan)
        self.assertFalse(context.can_native_apply)


class HostDetectionTests(unittest.TestCase):
    def probe(self, machine, results):
        by_name = dict(zip(("hw.optional.arm64", "sysctl.proc_translated"), results))

        def respond(command, **kwargs):
            value = by_name[command[2]]
            if isinstance(value, BaseException):
                raise value
            return value

        with patch("x86.execution.platform.system", return_value="Darwin"), \
             patch("x86.execution.platform.machine", return_value=machine), \
             patch("x86.execution.subprocess.run", side_effect=respond) as run:
            facts = detect_host()
        self.assertEqual(run.call_count, 2)
        for invocation in run.call_args_list:
            self.assertEqual(invocation.kwargs["timeout"], 5)
            self.assertFalse(invocation.kwargs["check"])
            self.assertEqual(invocation.kwargs["env"]["LC_ALL"], "C")
            self.assertEqual(invocation.args[0][:2], ["/usr/sbin/sysctl", "-n"])
        return facts

    @staticmethod
    def result(stdout="0\n", stderr="", returncode=0):
        return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)

    def test_non_darwin_does_not_run_sysctl(self):
        for system, machine in (("Windows", "AMD64"), ("Linux", "aarch64")):
            with self.subTest(system=system), \
                 patch("x86.execution.platform.system", return_value=system), \
                 patch("x86.execution.platform.machine", return_value=machine), \
                 patch("x86.execution.subprocess.run", side_effect=AssertionError("not Darwin")):
                facts = detect_host()
            self.assertIsNone(facts.hw_optional_arm64)
            self.assertFalse(facts.is_verified_native_x86_macos)

    def test_native_intel_probes(self):
        facts = self.probe("x86_64", [self.result(), self.result()])
        self.assertTrue(facts.is_verified_native_x86_macos)
        self.assertFalse(facts.is_apple_silicon)

    def test_rosetta_is_detected_despite_x86_process_machine(self):
        facts = self.probe("x86_64", [self.result("1\n"), self.result("1\n")])
        self.assertTrue(facts.is_apple_silicon)
        self.assertFalse(facts.is_verified_native_x86_macos)

    def test_arm_process_never_becomes_native_after_probe_failures(self):
        facts = self.probe("arm64", [OSError("blocked"), subprocess.TimeoutExpired("sysctl", 5)])
        self.assertTrue(facts.is_apple_silicon)
        self.assertEqual(len(facts.probe_errors), 2)

    def test_exact_translation_enoent_is_nontranslated_with_note(self):
        missing = self.result("", "sysctl: unknown oid 'sysctl.proc_translated'\n", 1)
        facts = self.probe("x86_64", [self.result(), missing])
        self.assertTrue(facts.is_verified_native_x86_macos)
        self.assertEqual(len(facts.probe_notes), 1)
        self.assertFalse(facts.probe_errors)

    def test_other_sysctl_failures_never_become_native(self):
        failures = [OSError("missing binary"), subprocess.TimeoutExpired("sysctl", 5),
                    self.result("", "permission denied", 1),
                    self.result("", "sysctl: unknown oid 'sysctl.proc_translated': Operation not permitted", 1),
                    self.result("", "sysctl: unknown oid 'sysctl.proc_translated'", 2),
                    self.result("", "", 0), self.result("0\n1\n"), self.result("2\n"),
                    self.result("0\n", "warning", 0)]
        for failure in failures:
            with self.subTest(failure=failure):
                facts = self.probe("x86_64", [self.result(), failure])
                self.assertFalse(facts.is_verified_native_x86_macos)
                self.assertTrue(facts.probe_errors)

    def test_exact_arm64_oid_absence_accepts_verified_nontranslated_x86(self):
        missing = self.result("", "sysctl: unknown oid 'hw.optional.arm64'", 1)
        for machine in ("x86_64", "AMD64"):
            for translation in (self.result(), self.result("", "sysctl: unknown oid 'sysctl.proc_translated'", 1)):
                with self.subTest(machine=machine, translation=translation):
                    facts = self.probe(machine, [missing, translation])
                    self.assertIs(facts.hw_optional_arm64, False)
                    self.assertIs(facts.proc_translated, False)
                    self.assertFalse(facts.probe_errors)
                    self.assertIn("hw.optional.arm64: absent (ENOENT)", facts.probe_notes[0])
                    self.assertTrue(resolve_execution(environ={}, facts=facts).can_native_apply)

    def test_missing_arm64_oid_does_not_relax_machine_check(self):
        missing = self.result("", "sysctl: unknown oid 'hw.optional.arm64'", 1)
        for machine in ("arm64", "arm64e", "aarch64", "i386", "", "unknown"):
            with self.subTest(machine=machine):
                facts = self.probe(machine, [missing, self.result()])
                self.assertIsNone(facts.hw_optional_arm64)
                self.assertTrue(facts.probe_errors)
                self.assertFalse(resolve_execution(environ={}, facts=facts).can_native_apply)

    def test_missing_arm64_oid_cannot_hide_translated_process(self):
        missing = self.result("", "sysctl: unknown oid 'hw.optional.arm64'", 1)
        facts = self.probe("x86_64", [missing, self.result("1\n")])
        self.assertIsNone(facts.hw_optional_arm64)
        self.assertTrue(facts.is_apple_silicon)
        with self.assertRaises(ExecutionPolicyError):
            resolve_execution(requested="x86", environ={}, facts=facts)

    def test_missing_arm64_oid_requires_successful_translation_evidence(self):
        missing = self.result("", "sysctl: unknown oid 'hw.optional.arm64'", 1)
        failures = (OSError("denied"), subprocess.TimeoutExpired("sysctl", 5),
                    self.result("", "permission denied", 1), self.result("0\n", "warning", 0),
                    self.result("", "sysctl: unknown oid 'sysctl.proc_translated': Operation not permitted", 1))
        for failure in failures:
            with self.subTest(failure=failure):
                facts = self.probe("x86_64", [missing, failure])
                self.assertIsNone(facts.hw_optional_arm64)
                self.assertTrue(facts.probe_errors)
                self.assertFalse(resolve_execution(environ={}, facts=facts).can_native_apply)

    def test_generic_or_ambiguous_arm64_errors_remain_denied(self):
        diagnostic = "sysctl: unknown oid 'hw.optional.arm64'"
        failures = (OSError("missing binary"), subprocess.TimeoutExpired("sysctl", 5),
                    self.result("", "permission denied", 1),
                    self.result("", diagnostic + ": Operation not permitted", 1),
                    self.result("", diagnostic + "\nwarning", 1),
                    self.result("", "sysctl: unknown oid 'hw.optional.arm'", 1),
                    self.result("", diagnostic, 0), self.result("", diagnostic, 2),
                    self.result("0\n", diagnostic, 1), self.result("", "", 0),
                    self.result("0\n", "warning", 0), self.result("0\n1\n"), self.result("2\n"))
        for failure in failures:
            with self.subTest(failure=failure):
                facts = self.probe("x86_64", [failure, self.result()])
                self.assertIsNone(facts.hw_optional_arm64)
                self.assertTrue(facts.probe_errors)
                self.assertFalse(resolve_execution(environ={}, facts=facts).can_native_apply)

    def test_positive_arm64_evidence_wins_over_nontranslated_sysctl_helper(self):
        for translation in (self.result(), self.result("", "sysctl: unknown oid 'sysctl.proc_translated'", 1)):
            with self.subTest(translation=translation):
                facts = self.probe("x86_64", [self.result("1\n"), translation])
                self.assertTrue(facts.is_apple_silicon)
                self.assertFalse(facts.is_verified_native_x86_macos)
                with self.assertRaises(ExecutionPolicyError):
                    resolve_execution(requested="x86", environ={}, facts=facts)


if __name__ == "__main__":
    unittest.main()
