"""Execution selection and native-action rejection at real GUI boundaries."""
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from x86.execution import HostFacts
from x86.gui import bootstrap
from x86.gui.bridge import WizardBridge
from x86.settings import SettingsStore


ROOT = Path(__file__).resolve().parents[2]


class MellowGuiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.store = SettingsStore(self.directory / "settings.json")
        self.store.save({"execution_mode": "x86", "mellow_deployment": "disabled"})
        self.environment = patch.dict(os.environ, {k: v for k, v in os.environ.items() if not k.startswith("X86_")}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.host = patch("x86.execution.detect_host", return_value=HostFacts("Windows", "AMD64"))
        self.host.start()
        self.addCleanup(self.host.stop)
        with patch("x86.gui.bridge.SettingsStore", return_value=self.store):
            self.bridge = WizardBridge()
        bootstrap.reset_constants()
        self.addCleanup(bootstrap.reset_constants)
        efi = self.directory / "EFI"
        (efi / "OC/Kexts/Lilu.kext/Contents/MacOS").mkdir(parents=True)
        for relative in ("Info.plist", "MacOS/Lilu"):
            shutil.copyfile(ROOT / "vendor/mellow/Lilu.kext/Contents" / relative,
                            efi / "OC/Kexts/Lilu.kext/Contents" / relative)
        (efi / "OC/config.plist").write_bytes(plistlib.dumps({
            "Kernel": {"Add": [{"BundlePath": "Lilu.kext", "PlistPath": "Contents/Info.plist",
                                "ExecutablePath": "Contents/MacOS/Lilu", "Enabled": True}]},
            "NVRAM": {"Add": {"7C436110-AB2A-4BBB-A880-FE41995C9F82": {"boot-args": "-v"}}}}))
        self.efi = efi

    def native_choice(self, deployment="efi"):
        return {"execution_mode": "x86", "mellow_deployment": deployment,
                "mellow_payload": str(ROOT / "payloads/Mellow"), "mellow_efi": str(self.efi)}

    def test_sandbox_save_and_status(self):
        result = self.bridge.save_settings({"execution_mode": "apple-silicon-sandbox", "mellow_deployment": "disabled"})
        self.assertTrue(result["ok"], result)
        self.assertTrue(self.bridge.get_app_info()["execution"]["is_sandbox"])
        with patch("x86.gui.bridge._patch_status_payload", side_effect=AssertionError("native detector")):
            self.assertFalse(self.bridge.get_patch_status()["patch"]["can_patch"])
        self.assertFalse(self.bridge.host_can_build()["can_build"])

    def test_sandbox_native_conflict_leaves_settings_bytes_unchanged(self):
        before = self.store.config_path.read_bytes()
        result = self.bridge.save_settings({**self.native_choice(), "execution_mode": "apple-silicon-sandbox"})
        self.assertFalse(result["ok"])
        self.assertEqual(before, self.store.config_path.read_bytes())

    def test_invalid_payload_does_not_save(self):
        before = self.store.config_path.read_bytes()
        result = self.bridge.save_settings({**self.native_choice(), "mellow_payload": str(self.directory / "missing")})
        self.assertFalse(result["ok"])
        self.assertEqual(before, self.store.config_path.read_bytes())

    def test_valid_efi_preparation_and_source_unchanged(self):
        result = self.bridge.save_settings(self.native_choice())
        self.assertTrue(result["ok"], result)
        before = (self.efi / "OC/config.plist").read_bytes()
        report = self.bridge.prepare_mellow_efi(str(self.directory / "PreparedEFI"))
        self.assertTrue(report["ok"], report)
        self.assertFalse(report["native_metal_verified"])
        self.assertEqual(before, (self.efi / "OC/config.plist").read_bytes())
        self.assertTrue((self.directory / "PreparedEFI/OC/Kexts/Mellow.kext/Contents/MacOS/Mellow").is_file())

    def test_root_efi_preparation_then_settings_save(self):
        before = (self.efi / "OC/config.plist").read_bytes()
        target = self.directory / "RootEFI"
        report = self.bridge.prepare_mellow_root_efi(str(self.efi), str(target), self.native_choice()["mellow_payload"])
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["lilu_route"], "disk-only")
        config = plistlib.loads((target / "OC/config.plist").read_bytes())
        self.assertFalse(config["Kernel"]["Add"][0]["Enabled"])
        self.assertFalse((target / "OC/Kexts/Mellow.kext").exists())
        self.assertIn("-mellowdiag", config["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"].split())
        self.assertEqual(before, (self.efi / "OC/config.plist").read_bytes())
        result = self.bridge.save_settings({**self.native_choice("root-patch"), "mellow_efi": str(target)})
        self.assertTrue(result["ok"], result)

    def test_all_native_actions_denied_in_sandbox_no_spawn(self):
        self.store.save({"execution_mode": "apple-silicon-sandbox", "mellow_deployment": "disabled"})
        with patch("x86.gui.bridge.subprocess.Popen") as spawn, patch("x86.gui.bridge.is_macos", return_value=True):
            for action in ("build", "install", "patch", "unpatch", "advanced", "model_change"):
                self.assertFalse(self.bridge.launch_wx_action(action)["ok"], action)
            spawn.assert_not_called()
        self.assertFalse(self.bridge.prepare_mellow_efi(str(self.directory / "Forbidden"))["ok"])
        self.assertFalse(self.bridge.prepare_mellow_root_efi(str(self.efi), str(self.directory / "Forbidden"),
                         self.native_choice()["mellow_payload"])["ok"])
        self.assertFalse((self.directory / "Forbidden").exists())

    def test_atomic_replace_failure_preserves_settings(self):
        before = self.store.config_path.read_bytes()
        with patch("x86.gui.execution_settings.os.replace", side_effect=OSError("injected replace failure")):
            self.assertFalse(self.bridge.save_settings({"verbose_logging": True})["ok"])
        self.assertEqual(before, self.store.config_path.read_bytes())
        self.assertEqual(list(self.directory.glob(".26x86-settings-*")), [])

    def test_environment_lock_conflict(self):
        with patch.dict(os.environ, {"X86_EXECUTION_MODE": "apple-silicon-sandbox"}):
            self.assertFalse(self.bridge.save_settings({"execution_mode": "x86"})["ok"])

    def test_apple_silicon_stale_native_settings_can_be_repaired(self):
        self.store.save(self.native_choice("root-patch"))
        facts = HostFacts("Darwin", "arm64", True, False)
        with patch("x86.execution.detect_host", return_value=facts), patch("x86.gui.bridge.is_macos", return_value=True), \
                patch("x86.gui.bootstrap.is_macos", return_value=True):
            info = self.bridge.get_app_info()
            self.assertIn("execution_error", info)
            self.assertFalse(info["execution"]["can_native_apply"])
            self.assertEqual(self.bridge.get_settings()["settings"]["execution_mode"], "apple-silicon-sandbox")
            self.assertTrue(self.bridge.get_status()["ok"])
            self.assertTrue(self.bridge.detect()["ok"])
            self.assertFalse(self.bridge.launch_wx_action("patch")["ok"])
            result = self.bridge.save_settings({"execution_mode": "apple-silicon-sandbox", "mellow_deployment": "disabled"})
            self.assertTrue(result["ok"], result)
            self.assertNotIn("execution_error", self.bridge.get_app_info())

    def test_conflicting_environment_still_blocks_repair_not_native_gate(self):
        facts = HostFacts("Darwin", "arm64", True, False)
        with patch("x86.execution.detect_host", return_value=facts), patch.dict(os.environ, {"X86_EXECUTION_MODE": "x86"}):
            self.assertIn("execution_error", self.bridge.get_app_info())
            self.assertFalse(self.bridge.save_settings({"execution_mode": "apple-silicon-sandbox"})["ok"])
            self.assertFalse(self.bridge.launch_wx_action("patch")["ok"])

    def test_bootstrap_sandbox_on_darwin_skips_native_imports(self):
        with patch("x86.gui.bootstrap.is_macos", return_value=True):
            c = bootstrap.get_constants(settings={"execution_mode": "apple-silicon-sandbox", "mellow_deployment": "disabled"})
        self.assertEqual(c.execution_mode, "apple-silicon-sandbox")
        self.assertEqual(c.computer.real_model, "Apple Silicon Sandbox")
        self.assertIsNone(getattr(c, "unpack_thread", None))

    def test_native_child_environment(self):
        self.store.save(self.native_choice("root-patch"))
        facts = HostFacts("Darwin", "x86_64", False, False)
        with patch("x86.execution.detect_host", return_value=facts), patch("x86.gui.bridge.is_macos", return_value=True), \
                patch("x86.gui.bridge.os.geteuid", return_value=0, create=True), patch("x86.gui.bridge.subprocess.Popen") as spawn:
            report = self.bridge.launch_wx_action("patch")
        self.assertTrue(report["ok"], report)
        environment = spawn.call_args.kwargs["env"]
        self.assertEqual(environment["X86_EXECUTION_MODE"], "x86")
        self.assertEqual(environment["X86_MELLOW_DEPLOYMENT"], "root-patch")
        self.assertEqual(environment["X86_MELLOW_EFI"], str(self.efi))
        self.assertTrue(environment["X86_MELLOW_PAYLOAD"].endswith("payloads\\Mellow") or environment["X86_MELLOW_PAYLOAD"].endswith("payloads/Mellow"))

    def test_native_nonroot_mellow_reports_correct_apply_and_unpatch(self):
        self.store.save(self.native_choice("root-patch"))
        facts = HostFacts("Darwin", "x86_64", False, False)
        with patch("x86.execution.detect_host", return_value=facts), patch("x86.gui.bridge.is_macos", return_value=True), \
                patch("x86.gui.bridge.os.geteuid", return_value=501, create=True), patch("x86.gui.bridge.subprocess.Popen") as spawn:
            for action, flag in (("patch", "--apply"), ("unpatch", "--unpatch")):
                report = self.bridge.launch_wx_action(action)
                self.assertTrue(report["needs_root"])
                self.assertIn(flag, report["command"])
            spawn.assert_not_called()

    def test_frozen_nonroot_command_uses_cli_reentry(self):
        self.store.save(self.native_choice("root-patch"))
        facts = HostFacts("Darwin", "x86_64", False, False)
        with patch("x86.execution.detect_host", return_value=facts), patch("x86.gui.bridge.is_macos", return_value=True), \
                patch("x86.gui.bridge.os.geteuid", return_value=501, create=True), \
                patch("x86.gui.bridge.sys.frozen", True, create=True):
            result = self.bridge.launch_wx_action("patch")
        self.assertEqual(result["command"][:4], ["sudo", sys.executable, "--x86-cli", "patch"])
        self.assertNotIn("-m", result["command"])

    def test_both_packaged_entries_dispatch_cli_before_native_imports(self):
        guard = """
import importlib.abc,runpy,sys
class DenyNative(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in ('wx','Security','webview') or fullname.startswith('opencore_legacy_patcher.detections.'):
   raise RuntimeError('native import forbidden: '+fullname)
sys.meta_path.insert(0,DenyNative())
entry=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(entry,run_name='__main__')
"""
        for entry in (ROOT / "x86/gui/entry.py", ROOT / "26x86-GUI.command"):
            result = subprocess.run([sys.executable, "-c", guard, str(entry), "--x86-cli",
                "mellow", "plan", "--mode", "apple-silicon-sandbox", "--efi", str(self.efi)],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=20)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)["ok"])
            self.assertNotIn("native import forbidden", result.stderr)
            help_result = subprocess.run([sys.executable, "-c", guard, str(entry), "--x86-cli",
                "mellow", "--help"], cwd=ROOT, capture_output=True, text=True, timeout=20)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("prepare-root-efi", help_result.stdout)

    def test_runner_rejects_before_wx_import(self):
        environment = dict(os.environ, X86_EXECUTION_MODE="apple-silicon-sandbox", X86_MELLOW_DEPLOYMENT="disabled")
        result = subprocess.run([sys.executable, "-m", "x86.gui.wx_runner", "patch"],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires verified native x86 macOS", result.stderr)
        self.assertNotIn("No module named", result.stderr)

    def test_http_settings_real_roundtrip_and_webview_facade(self):
        from x86.gui.http_bridge import start_bridge_http_server, wizard_base_url, API_METHODS
        from x86.gui.webview_app import WebviewApi
        self.assertIn("prepare_mellow_efi", API_METHODS)
        self.assertNotIn("inspect_vmapple_storage", API_METHODS)
        api = WebviewApi(self.bridge)
        self.assertFalse(api.prepare_mellow_efi(str(self.directory / "unused"))["ok"])
        self.assertFalse(hasattr(api, "inspect_vmapple_storage"))
        server, _ = start_bridge_http_server(self.bridge.web_root(), bridge=self.bridge)
        try:
            payload = {"method": "save_settings", "args": [{"execution_mode": "apple-silicon-sandbox", "mellow_deployment": "disabled"}]}
            req = Request(wizard_base_url(server) + "/api/invoke", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=10) as response:
                data = json.load(response)
            self.assertTrue(data["result"]["ok"], data)
            self.assertEqual(self.store.read("execution_mode"), "apple-silicon-sandbox")
            storage_payload = {"method": "inspect_vmapple_storage", "args": [{}]}
            storage_req = Request(
                wizard_base_url(server) + "/api/invoke",
                data=json.dumps(storage_payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(HTTPError) as caught:
                urlopen(storage_req, timeout=10)
            self.assertEqual(caught.exception.code, 404)
            self.assertFalse(json.load(caught.exception)["ok"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
