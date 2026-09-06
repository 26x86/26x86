"""Host evidence fixtures are test-only; none is a runtime override."""

import json
import os
import plistlib
import subprocess
import unittest
from unittest.mock import patch

from venfire import host


class HostTests(unittest.TestCase):
    def setUp(self):
        self.sysctls = {
            "hw.model": b"MacBookPro11,3\n",
            "machdep.cpu.vendor": b"GenuineIntel\n",
            "kern.hv_vmm_present": b"0\n",
            "machdep.cpu.features": b"FPU SSE SSE2 AVX1.0\n",
            "machdep.cpu.leaf7_features": b"RDWRFSGS AVX2 SMEP ERMS\n",
        }
        self.platform_nodes = [{
            "manufacturer": b"Apple Inc.\x00",
            "model": b"MacBookPro11,3\x00",
            "board-id": b"Mac-2BD1B31983FE1663\x00",
            "IOPlatformSerialNumber": "DO-NOT-RETAIN-THIS-SERIAL",
            "IOPlatformUUID": "DO-NOT-RETAIN-THIS-UUID",
        }]
        self.smc_nodes = [{"IOObjectClass": "AppleSMC"}]
        self.commands = []
        self.patches = [
            patch.object(host.platform, "system", return_value="Darwin"),
            patch.object(host.platform, "machine", return_value="x86_64"),
            patch.object(host, "_probe", side_effect=self.probe),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def probe(self, arguments):
        self.commands.append(arguments)
        if arguments[0] == "/usr/sbin/sysctl":
            value = self.sysctls.get(arguments[-1])
            return host._Probe(value, "ok" if value is not None else "probe unavailable")
        nodes = self.platform_nodes if arguments[-1] == "IOPlatformExpertDevice" else self.smc_nodes
        return host._Probe(plistlib.dumps(nodes), "ok")

    def test_eligible_intel_mac_with_avx2_and_independent_evidence(self):
        report = host.require_apple_intel()
        self.assertTrue(report.eligible)
        self.assertEqual(report.hardware_model, "MacBookPro11,3")
        self.assertTrue(all(item.passed for item in report.evidence))
        self.assertEqual(len(self.commands), 7)
        self.assertTrue(all(command[0].startswith("/") for command in self.commands))

    def test_diagnostics_are_serial_free(self):
        rendered = json.dumps(host.detect_host().to_dict())
        self.assertNotIn("DO-NOT-RETAIN", rendered)
        self.assertNotIn("Mac-2BD1B31983FE1663", rendered)
        self.assertIn("not cryptographic attestation", rendered)

    def test_windows_is_diagnostic_only_and_runs_no_apple_probes(self):
        with patch.object(host.platform, "system", return_value="Windows"), \
                patch.object(host, "_windows_cpu", return_value=("GenuineIntel", True, "ok")):
            report = host.detect_host()
        self.assertFalse(report.eligible)
        self.assertTrue(report.cpu_eligible)
        self.assertEqual(self.commands, [])

    def test_arm_mac_denied_without_probes(self):
        with patch.object(host.platform, "machine", return_value="arm64"):
            self.assertFalse(host.detect_host().eligible)
        self.assertEqual(self.commands, [])

    def test_mac_pro_2009_without_avx2_is_denied(self):
        self.sysctls["hw.model"] = b"MacPro4,1\n"
        self.platform_nodes[0]["model"] = b"MacPro4,1\x00"
        self.sysctls["machdep.cpu.leaf7_features"] = b"SMEP ERMS\n"
        report = host.detect_host()
        self.assertFalse(report.eligible)
        self.assertIn("AVX2 CPU support required", report.reasons)

    def test_feature_token_must_be_exact(self):
        self.sysctls["machdep.cpu.leaf7_features"] = b"FAKEAVX2 AVX2_FAKE\n"
        self.assertFalse(host.detect_host().eligible)

    def test_any_missing_required_probe_denies(self):
        for key in list(self.sysctls):
            with self.subTest(key=key):
                value = self.sysctls.pop(key)
                self.assertFalse(host.detect_host().eligible)
                self.sysctls[key] = value

    def test_vm_flag_and_vm_identifiers_deny_even_apple_shaped_platform(self):
        self.sysctls["kern.hv_vmm_present"] = b"1\n"
        self.assertFalse(host.detect_host().eligible)
        self.sysctls["kern.hv_vmm_present"] = b"0\n"
        self.sysctls["machdep.cpu.features"] += b" VMM"
        self.assertFalse(host.detect_host().eligible)
        self.sysctls["machdep.cpu.features"] = b"FPU AVX1.0\n"
        self.platform_nodes[0]["compatible"] = b"VMware Virtual Machine\x00"
        self.assertFalse(host.detect_host().eligible)

    def test_mismatching_registry_model_or_manufacturer_denies(self):
        self.platform_nodes[0]["model"] = b"MacPro6,1\x00"
        self.assertFalse(host.detect_host().eligible)
        self.platform_nodes[0]["model"] = b"MacBookPro11,3\x00"
        self.platform_nodes[0]["manufacturer"] = b"Unknown\x00"
        self.assertFalse(host.detect_host().eligible)

    def test_missing_smc_or_invalid_board_id_denies(self):
        self.smc_nodes = []
        self.assertFalse(host.detect_host().eligible)
        self.smc_nodes = [{"IOClass": "AppleSMC"}]
        self.platform_nodes[0]["board-id"] = b"not-an-apple-board\x00"
        self.assertFalse(host.detect_host().eligible)

    def test_separate_nodes_cannot_combine_into_positive_identity(self):
        self.platform_nodes = [{"manufacturer": b"Apple Inc.\0"}, {"model": b"MacBookPro11,3\0", "board-id": b"Mac-2BD1B31983FE1663\0"}]
        self.assertFalse(host.detect_host().eligible)

    def test_invalid_xml_denies_and_has_no_raw_output_in_report(self):
        original = self.probe

        def invalid_registry(arguments):
            if arguments[0] == "/usr/sbin/ioreg":
                return host._Probe(b"<?xml version='1.0'?><plist><SERIAL-IN-BAD-XML", "ok")
            return original(arguments)

        with patch.object(host, "_probe", side_effect=invalid_registry):
            report = host.detect_host()
        self.assertFalse(report.eligible)
        self.assertNotIn("SERIAL-IN-BAD-XML", json.dumps(report.to_dict()))

    def test_no_environment_override_and_error_carries_report(self):
        self.sysctls["kern.hv_vmm_present"] = b"1\n"
        with patch.dict(os.environ, {"VENFIRE_ALLOW_NON_APPLE": "1", "VENFIRE_SKIP_HOST_CHECK": "1"}):
            with self.assertRaises(host.HostEligibilityError) as captured:
                host.require_apple_intel()
        self.assertFalse(captured.exception.report.eligible)


class ProbeTests(unittest.TestCase):
    def test_probe_timeout_is_fail_closed(self):
        with patch.object(host.subprocess, "run", side_effect=subprocess.TimeoutExpired("sysctl", 4)):
            result = host._probe(("/usr/sbin/sysctl", "-n", "hw.model"))
        self.assertIsNone(result.data)
        self.assertEqual(result.status, "probe timed out")

    def test_probe_uses_read_only_absolute_tool_and_never_shell(self):
        completed = subprocess.CompletedProcess([], 0, stdout=b"0\n")
        with patch.object(host.subprocess, "run", return_value=completed) as run:
            host._probe(("/usr/sbin/sysctl", "-n", "kern.hv_vmm_present"))
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertGreater(run.call_args.kwargs["timeout"], 0)
        self.assertLessEqual(run.call_args.kwargs["timeout"], 5)


class LinuxHostTests(unittest.TestCase):
    def setUp(self):
        self.cpu0 = "processor : 0\nvendor_id : GenuineIntel\nflags : fpu lm xsave avx avx2 sse2"
        self.cpu1 = "processor : 1\nvendor_id : GenuineIntel\nflags : fpu lm xsave avx avx2 sse2"
        self.metadata = {
            "/proc/cpuinfo": self.cpu0 + "\n\n" + self.cpu1,
            "/sys/class/dmi/id/sys_vendor": "Apple Inc.",
            "/sys/class/dmi/id/product_name": "MacBookPro11,3",
            "/sys/class/dmi/id/board_vendor": "Apple Inc.",
            "/sys/class/dmi/id/board_name": "Mac-2BD1B31983FE1663",
        }
        self.read_paths = []
        for item in (
            patch.object(host.platform, "system", return_value="Linux"),
            patch.object(host.platform, "machine", return_value="x86_64"),
            patch.object(host, "_linux_read", side_effect=self.read),
            patch.object(host, "_linux_smc_bound", return_value=True),
        ):
            item.start()
            self.addCleanup(item.stop)

    def read(self, path, limit=8192):
        self.read_paths.append(path)
        value = self.metadata.get(path)
        return value, "missing" if value is None else "ok"

    def test_linux_live_on_apple_can_pass_normal_policy(self):
        report = host.require_apple_intel()
        self.assertTrue(report.eligible)
        self.assertTrue(report.cpu_eligible)
        self.assertEqual(report.system, "Linux")
        self.assertFalse(any("serial" in path or "uuid" in path for path in self.read_paths))

    def test_pc_cpu_is_eligible_but_normal_platform_is_not(self):
        self.metadata["/sys/class/dmi/id/sys_vendor"] = "SAMSUNG ELECTRONICS CO., LTD."
        self.metadata["/sys/class/dmi/id/product_name"] = "Lab PC"
        report = host.detect_host()
        self.assertTrue(report.cpu_eligible)
        self.assertFalse(report.eligible)

    def test_each_cpu_must_have_intel_and_avx2(self):
        for bad in (
            self.cpu1.replace("GenuineIntel", "AuthenticAMD"),
            self.cpu1.replace("avx2", "avx2not"),
            "processor : 1\nvendor_id : GenuineIntel",
        ):
            with self.subTest(cpu=bad):
                self.metadata["/proc/cpuinfo"] = self.cpu0 + "\n\n" + bad
                report = host.detect_host()
                self.assertFalse(report.cpu_eligible)
                self.assertFalse(report.eligible)

    def test_cpu_records_cannot_be_missing_or_ambiguous(self):
        for value in (None, "", "flags : avx2\nvendor_id : GenuineIntel",
                      self.cpu0 + "\nflags : avx2"):
            with self.subTest(value=value):
                self.metadata["/proc/cpuinfo"] = value
                self.assertFalse(host.detect_host().cpu_eligible)

    def test_missing_smc_or_dmi_denies_release_but_keeps_cpu_evidence(self):
        with patch.object(host, "_linux_smc_bound", return_value=False):
            report = host.detect_host()
        self.assertFalse(report.eligible)
        self.assertTrue(report.cpu_eligible)
        self.metadata.pop("/sys/class/dmi/id/board_vendor")
        self.assertFalse(host.detect_host().eligible)

    def test_vm_flags_or_metadata_deny_normal_release(self):
        self.metadata["/proc/cpuinfo"] += " hypervisor"
        report = host.detect_host()
        self.assertFalse(report.eligible)
        self.assertTrue(report.cpu_eligible)
        self.metadata["/proc/cpuinfo"] = self.cpu0
        self.metadata["/sys/hypervisor/type"] = "xen"
        self.assertFalse(host.detect_host().eligible)
        self.metadata.pop("/sys/hypervisor/type")
        self.metadata["/sys/class/dmi/id/product_name"] = "QEMU Standard PC"
        self.assertFalse(host.detect_host().eligible)

    def test_unreadable_hypervisor_file_is_not_absence(self):
        original = self.read

        def unreadable(path, limit=8192):
            return (None, "unavailable") if path == "/sys/hypervisor/type" else original(path, limit)

        with patch.object(host, "_linux_read", side_effect=unreadable):
            self.assertFalse(host.detect_host().eligible)


class WindowsHostTests(unittest.TestCase):
    def report(self, vendor="GenuineIntel", avx2=True, architecture="AMD64"):
        with patch.object(host.platform, "system", return_value="Windows"), \
                patch.object(host.platform, "machine", return_value=architecture), \
                patch.object(host, "_windows_cpu", return_value=(vendor, avx2, "fixture")):
            return host.detect_host()

    def test_windows_collects_only_lab_cpu_evidence(self):
        report = self.report()
        self.assertTrue(report.cpu_eligible)
        self.assertFalse(report.eligible)
        self.assertEqual(report.architecture, "x86_64")

    def test_windows_never_infers_missing_avx2_or_vendor(self):
        for vendor, avx2, architecture in (
            (None, True, "AMD64"), ("AuthenticAMD", True, "AMD64"),
            ("GenuineIntel", None, "AMD64"), ("GenuineIntel", False, "AMD64"),
            ("GenuineIntel", True, "ARM64"),
        ):
            with self.subTest(vendor=vendor, avx2=avx2, architecture=architecture):
                self.assertFalse(self.report(vendor, avx2, architecture).cpu_eligible)

    def test_32_bit_process_never_meets_cpu_requirement(self):
        with patch.object(host.sys, "maxsize", 2**31 - 1):
            self.assertFalse(self.report().cpu_eligible)


if __name__ == "__main__":
    unittest.main()
