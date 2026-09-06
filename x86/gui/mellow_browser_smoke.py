"""Optional real-browser GUI test: requires installed Playwright + Chromium.

Runs a private localhost bridge with temporary settings and EFI, never the
user's saved settings/USB. Screenshots and report default to build/gui-mellow-smoke.
"""
import argparse
import json
from pathlib import Path
from unittest.mock import patch


def run(output: Path):
    from playwright.sync_api import sync_playwright
    from x86.gui.test_mellow_gui import MellowGuiTests
    from x86.gui.http_bridge import start_bridge_http_server, wizard_base_url
    fixture = MellowGuiTests("test_valid_efi_preparation_and_source_unchanged")
    fixture.setUp()
    server = None
    output.mkdir(parents=True, exist_ok=True)
    try:
        server, _ = start_bridge_http_server(fixture.bridge.web_root(), bridge=fixture.bridge)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 960, "height": 720})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(wizard_base_url(server))
            page.wait_for_selector("#boot-banner", state="detached")
            page.click("#btn-settings")
            page.select_option("#setting-mode", "apple-silicon-sandbox")
            assert page.locator("#setting-mellow").is_disabled()
            assert page.locator("#setting-mellow").input_value() == "disabled"
            page.screenshot(path=str(output / "sandbox-settings.png"))
            page.click("#settings-save")
            page.wait_for_selector("#settings-dialog", state="hidden")
            page.wait_for_function("document.querySelector('#step-content').textContent.includes('Apple Silicon Sandbox Mode')")
            for _ in range(3):
                page.click("#btn-next")
            page.wait_for_function("document.querySelector('#step-content').textContent.includes('Mellow.kext')")
            assert page.locator("#action-patch").count() == 0
            page.screenshot(path=str(output / "sandbox-native-blocked.png"))
            page.click("#btn-settings")
            page.select_option("#setting-mode", "x86")
            page.select_option("#setting-mellow", "efi")
            page.fill("#setting-mellow-payload", fixture.native_choice()["mellow_payload"])
            page.fill("#setting-mellow-efi", str(fixture.efi))
            page.click("#settings-save")
            page.wait_for_selector("#settings-dialog", state="hidden")
            page.wait_for_selector("#action-mellow-efi")
            target = fixture.directory / "BrowserPreparedEFI"
            page.fill("#mellow-output", str(target))
            page.click("#action-mellow-efi")
            page.wait_for_function("document.querySelector('#mellow-result').textContent.includes('준비됨:')")
            assert (target / "OC/Kexts/Mellow.kext/Contents/MacOS/Mellow").is_file()
            page.screenshot(path=str(output / "efi-prepared.png"))
            page.click("#btn-settings")
            page.select_option("#setting-mellow", "root-patch")
            root_target = fixture.directory / "BrowserRootEFI"
            page.fill("#setting-root-output", str(root_target))
            page.click("#setting-root-prepare")
            page.wait_for_function("document.querySelector('#setting-root-result').textContent.includes('새 EFI를 준비했습니다')")
            assert page.locator("#setting-mellow-efi").input_value() == str(root_target)
            import plistlib
            config = plistlib.loads((root_target / "OC/config.plist").read_bytes())
            assert not config["Kernel"]["Add"][0]["Enabled"]
            assert not (root_target / "OC/Kexts/Mellow.kext").exists()
            page.screenshot(path=str(output / "root-efi-prepared.png"))
            page.click("#settings-save")
            page.wait_for_selector("#settings-dialog", state="hidden")
            assert fixture.store.read("mellow_deployment") == "root-patch"
            from x86.execution import HostFacts
            fixture.store.save(fixture.native_choice("root-patch"))
            with patch("x86.execution.detect_host", return_value=HostFacts("Darwin", "arm64", True, False)), \
                    patch("x86.gui.bridge.is_macos", return_value=True), patch("x86.gui.bootstrap.is_macos", return_value=True):
                page.reload()
                page.wait_for_selector("#boot-banner", state="detached")
                page.wait_for_function("document.querySelector('#step-content').textContent.includes('설정에서 실행 모드')")
                page.click("#btn-settings")
                page.wait_for_selector("#settings-dialog", state="visible")
                assert page.locator("#setting-mode").input_value() == "apple-silicon-sandbox"
                assert page.locator("#setting-mellow").is_disabled()
                page.click("#settings-save")
                page.wait_for_selector("#settings-dialog", state="hidden")
                page.wait_for_function("!document.querySelector('#step-content').textContent.includes('설정에서 실행 모드')")
                assert fixture.store.read("execution_mode") == "apple-silicon-sandbox"
                page.screenshot(path=str(output / "stale-native-settings-repaired.png"))
            assert not errors, errors
            report = {"ok": True, "browser": browser.version, "backend": "real local HTTP bridge",
                "viewport": [960, 720], "sandbox_settings_disabled": True,
                "sandbox_native_controls_absent": True, "x86_efi_prepared_and_file_readback": True,
                "root_efi_prepared_lilu_disabled_no_mellow_injection": True,
                "simulated_apple_silicon_stale_native_settings_repaired": True,
                "page_errors": errors, "native_tahoe_tested": False, "native_metal_verified": False}
            (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            browser.close()
            return report
    finally:
        if server:
            server.shutdown()
            server.server_close()
        fixture.doCleanups()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/gui-mellow-smoke"))
    print(json.dumps(run(parser.parse_args().output), indent=2))
