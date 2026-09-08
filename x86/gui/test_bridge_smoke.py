"""Headless smoke tests for the HTML wizard Python bridge."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class BridgeSmokeTest(unittest.TestCase):
    def test_bridge_roundtrip(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        info = bridge.get_app_info()
        self.assertEqual(info["bundle_id"], "com.niseullent.26x86")
        self.assertTrue(bridge.index_path().exists())
        self.assertFalse(bridge.index_uri().startswith("file://"))
        self.assertTrue((bridge.web_root() / "app.js").exists())
        self.assertTrue((bridge.web_root() / "index.html").exists())
        if info.get("logo_url"):
            self.assertTrue(
                info["logo_url"].startswith("data:image/"),
                "logo should be embedded for HTTP-served wizard UI",
            )

        steps = bridge.get_steps()
        self.assertEqual(len(steps), 5)

        detect = bridge.detect(refresh=False)
        self.assertTrue(detect["ok"])
        self.assertIn("model", detect["detect"])

        macos = bridge.get_macos_choices()
        self.assertIn("choices", macos)
        self.assertGreaterEqual(len(macos["choices"]), 1)

        status = bridge.get_status()
        self.assertTrue(status["ok"])

        vmapple = bridge.get_vmapple_status()
        self.assertTrue(vmapple["ok"])
        self.assertIn("configured", vmapple)
        self.assertEqual(vmapple["machine_type"], "iBoot(AArch64)")
        self.assertEqual(vmapple["guest_os_policy"], "macOS-only")
        self.assertEqual(vmapple["recovery_scope"]["default_image_name"], "_default.ipsw")

    def test_boot_picker_alt_recovery_roundtrip(self) -> None:
        from x86.gui.bridge import WizardBridge

        bridge = WizardBridge()
        armed = bridge.start_boot_picker(
            target_major=27,
            recovery_protocol="DFU/IPSW",
            recovery_image_name="_default.ipsw",
        )
        self.assertTrue(armed["ok"])
        self.assertEqual(armed["state"], "armed")
        shown = bridge.boot_picker_key("Alt")
        self.assertTrue(shown["ok"])
        self.assertEqual(shown["state"], "picker")
        moved = bridge.boot_picker_key("ArrowDown")
        self.assertEqual(moved["selected_entry"], "recovery")
        selected = bridge.boot_picker_key("Enter")
        self.assertEqual(selected["selection"], "recovery")
        self.assertEqual(selected["trigger"], "alt-enter")
        status = bridge.get_boot_picker_status()
        self.assertEqual(status["selection"], "recovery")
        self.assertTrue(status["picker_visible"] is False)

    def test_webview_smoke_helper(self) -> None:
        from x86.gui.webview_app import smoke_test_bridge
        from x86.platform import is_macos

        payload = smoke_test_bridge()
        self.assertTrue(payload["ok"], json.dumps(payload, ensure_ascii=False))
        self.assertIn("qt_chromium_available", payload)
        self.assertIn("pywebview_gui", payload)
        self.assertTrue(payload["qt_opt_in_only"])
        self.assertTrue(payload["tauri_preferred"])
        if is_macos():
            self.assertEqual(payload["pywebview_gui"], "cocoa")
            self.assertTrue(payload["macos_default_cocoa"])

    def test_macos_gui_prefers_tauri_not_chromium(self) -> None:
        from x86.gui.webview_app import (
            _requested_backend,
            _should_try_qt_chromium,
            _should_try_tauri,
            launch_webview_wizard,
        )
        from x86.platform import is_macos, resolve_pywebview_gui

        if not is_macos():
            self.skipTest("macOS-only backend preference")
        self.assertEqual(resolve_pywebview_gui(), "cocoa")
        self.assertEqual(_requested_backend(), "auto")
        self.assertTrue(_should_try_tauri("auto"))
        self.assertFalse(_should_try_qt_chromium("auto"))
        self.assertTrue(_should_try_qt_chromium("qt"))
        self.assertFalse(_should_try_tauri("cocoa"))
        self.assertFalse(_should_try_tauri("qt"))
        self.assertIn("tauri", (launch_webview_wizard.__doc__ or "").lower())

    def test_http_bridge_api(self) -> None:
        from x86.gui.bridge import WizardBridge
        from x86.gui.http_bridge import start_bridge_http_server, wizard_base_url

        bridge = WizardBridge()
        httpd, _ = start_bridge_http_server(bridge.web_root(), bridge=bridge)
        try:
            base = wizard_base_url(httpd)
            with urlopen(f"{base}/api/health", timeout=5) as resp:
                health = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(health["ok"])
            with urlopen(f"{base}/api/get_app_info", timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["result"]["bundle_id"], "com.niseullent.26x86")
            # Retired application test endpoints are absent on the real bridge.
            with self.assertRaises(HTTPError) as caught:
                urlopen(f"{base}/api/get_vmapple_status", timeout=5)
            self.assertEqual(caught.exception.code, 404)
            self.assertFalse(json.load(caught.exception)["ok"])
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_html_bootstraps_http_and_legacy_bridges(self) -> None:
        from x86.gui.bridge import WizardBridge

        index = WizardBridge().index_path().read_text(encoding="utf-8")
        js = (WizardBridge().web_root() / "app.js").read_text(encoding="utf-8")
        self.assertIn("qrc:", index)
        self.assertIn("connectQtWebChannel", js)
        self.assertIn("promisifyQtBridge", js)
        self.assertIn("probeHttpBridge", js)
        self.assertIn("/api/invoke", js)
        self.assertIn("/api/health", js)

    def test_tauri_project_scaffolded(self) -> None:
        tauri_dir = REPO / "gui-tauri"
        self.assertTrue((tauri_dir / "Cargo.toml").is_file())
        self.assertTrue((tauri_dir / "tauri.conf.json").is_file())
        self.assertTrue((tauri_dir / "src" / "main.rs").is_file())
        conf = (tauri_dir / "tauri.conf.json").read_text(encoding="utf-8")
        self.assertIn("com.niseullent.26x86", conf)
        self.assertIn("../x86/gui/web", conf)

    def test_frozen_webengine_lookup_is_safe(self) -> None:
        from x86.gui.qt_chromium import _frozen_webengine_process

        self.assertIsNone(_frozen_webengine_process())


if __name__ == "__main__":
    unittest.main()
