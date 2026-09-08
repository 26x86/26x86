"""Host isolation, EFI integrity and root patch failure boundary tests."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class GuiPlatformTests(unittest.TestCase):
    def test_retired_profile_is_rejected_before_any_native_probe(self):
        from x86.patch import root
        with self.assertRaisesRegex(ValueError, "Unknown root patch profile"):
            root._context("retired-device")

    def test_missing_optional_qt_parents_are_not_startup_errors(self):
        from x86.platform import qt_webengine_available
        with patch("importlib.util.find_spec", side_effect=ModuleNotFoundError("optional Qt")):
            self.assertFalse(qt_webengine_available())


    def test_non_mac_root_patch_never_loads_engine(self):
        from x86.patch import root
        with patch.object(root, "is_macos", return_value=False), patch.object(root, "_context", side_effect=AssertionError("must not probe")):
            result = root.apply()
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "unsupported_platform")

    def test_rollback_success_cannot_be_reported_as_patch_success(self):
        from x86.patch import root
        constants = SimpleNamespace(computer=SimpleNamespace(real_model="MacBookPro15,2"), root_patcher_succeeded=True)
        engine = SimpleNamespace(start_patch=lambda **kwargs: False)
        module = SimpleNamespace(PatchSysVolume=lambda *args: engine)
        with patch.object(root, "is_macos", return_value=True), patch.object(root, "_context", return_value=constants), \
             patch.object(root, "preflight", return_value={"ok": True, "can_patch": True}), \
             patch.object(root.os, "geteuid", return_value=0, create=True), \
             patch.dict(sys.modules, {"opencore_legacy_patcher.sys_patch.sys_patch": module}):
            result = root.apply()
        self.assertEqual(result["status"], "patch_failed")
        self.assertFalse(result["ok"])


    @unittest.skipIf(sys.platform == "darwin", "Native macOS probing has platform dependencies")
    def test_preparation_does_not_import_mac_frameworks_or_wx(self):
        code = "from x86.gui.webview_app import smoke_test_bridge; import sys; assert smoke_test_bridge()['ok']; assert not {'Security', 'wx', 'applescript'} & set(sys.modules)"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class BridgeBoundaryTests(unittest.TestCase):
    def test_desktop_transports_omit_research_launchers(self):
        from x86.gui.http_bridge import API_METHODS
        from x86.gui.webview_app import WebviewApi
        from x86.gui.bridge import WizardBridge
        for method in ("prepare_sandbox", "launch_vmapple", "start_boot_picker",
                       "get_vmapple_status", "get_silicon_sandbox_demo"):
            self.assertNotIn(method, API_METHODS)
            self.assertFalse(hasattr(WebviewApi, method))
        # Existing runtime/CLI regression callers retain the actual controller.
        self.assertTrue(callable(WizardBridge.launch_vmapple))

    def test_websites_cannot_launch_local_patch_or_read_efi(self):
        from x86.gui.http_bridge import start_bridge_http_server, wizard_base_url
        bridge = SimpleNamespace(get_app_info=lambda: {"ok": True})
        with tempfile.TemporaryDirectory() as tmp:
            server, _ = start_bridge_http_server(tmp, bridge=bridge)
            try:
                base = wizard_base_url(server)
                data = json.dumps({"method": "launch_wx_action", "args": ["patch"]}).encode()
                request = Request(base + "/api/invoke", data=data, headers={"Content-Type": "application/json", "Origin": "https://example.com"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request, timeout=5)
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/launch_wx_action", timeout=5)
                self.assertEqual(error.exception.code, 404)
                request = Request(base + "/api/invoke", data=b"{}", headers={"Content-Type": "text/plain"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request, timeout=5)
                self.assertEqual(error.exception.code, 415)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
