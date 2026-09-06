"""
HTML hybrid 26x86 wizard shell.

Default: Tauri (WKWebView on macOS / WebView2 on Windows) + local HTTP bridge.
Fallbacks: pywebview Cocoa (WebKit). Qt WebEngine is opt-in via
``X86_GUI_BACKEND=qt`` — Chromium/Metal aborts on flashed Mac Pro + Vega.

Always serve the wizard over local HTTP (never file://) so WKWebView can
load CSS/JS and the shell paints before the Python bridge is ready.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from x86.gui import bootstrap
from x86.gui.bridge import WizardBridge
from x86.gui.http_bridge import start_bridge_http_server
from x86.platform import is_macos, resolve_pywebview_gui, qt_webengine_available


class WebviewApi:
    """JS-callable API surface (pywebview js_api / Qt QWebChannel)."""

    def __init__(self, bridge: Optional[WizardBridge] = None) -> None:
        self._bridge = bridge or WizardBridge()

    def get_app_info(self) -> dict[str, Any]:
        return self._bridge.get_app_info()

    def get_sandbox_status(self):
        return self._bridge.get_sandbox_status()

    def set_execution_mode(self, mode: str):
        return self._bridge.set_execution_mode(mode)

    def get_sandbox_plan(self, target_major: int):
        return self._bridge.get_sandbox_plan(target_major)

    def prepare_sandbox(self, target_major: int, output_path: str):
        return self._bridge.prepare_sandbox(target_major, output_path)

    def get_vmapple_status(self):
        return self._bridge.get_vmapple_status()

    def get_boot_picker_status(self):
        return self._bridge.get_boot_picker_status()

    def start_boot_picker(self, target_major: int = 27, recovery_protocol: str = "DFU/IPSW",
                          recovery_image_name: str = "_default.ipsw"):
        return self._bridge.start_boot_picker(target_major, recovery_protocol, recovery_image_name)

    def tick_boot_picker(self):
        return self._bridge.tick_boot_picker()

    def boot_picker_key(self, key: object, pressed: bool = True):
        return self._bridge.boot_picker_key(key, pressed)

    def select_boot_entry(self, entry_id: object):
        return self._bridge.select_boot_entry(entry_id)

    def launch_vmapple(self, config: dict[str, Any]):
        return self._bridge.launch_vmapple(config)

    def set_hardware_profile(self, profile=None) -> dict[str, Any]:
        return self._bridge.set_hardware_profile(profile)

    def validate_surface_efi(self, path: str) -> dict[str, Any]:
        return self._bridge.validate_surface_efi(path)

    def get_steps(self) -> list[dict[str, str]]:
        return self._bridge.get_steps()

    def detect(self, refresh: bool = False) -> dict[str, Any]:
        return self._bridge.detect(refresh=refresh)

    def get_macos_choices(self) -> dict[str, Any]:
        return self._bridge.get_macos_choices()

    def set_target_os(self, kernel: int) -> dict[str, Any]:
        return self._bridge.set_target_os(kernel)

    def get_patch_status(self) -> dict[str, Any]:
        return self._bridge.get_patch_status()

    def get_silicon_sandbox_demo(self) -> dict[str, Any]:
        return self._bridge.get_silicon_sandbox_demo()

    def get_status(self) -> dict[str, Any]:
        return self._bridge.get_status()

    def get_settings(self) -> dict[str, Any]:
        return self._bridge.get_settings()

    def save_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._bridge.save_settings(data)

    def prepare_mellow_efi(self, output: str) -> dict[str, Any]:
        return self._bridge.prepare_mellow_efi(output)

    def prepare_mellow_root_efi(self, source: str, output: str, payload: str) -> dict[str, Any]:
        return self._bridge.prepare_mellow_root_efi(source, output, payload)

    def host_can_build(self) -> dict[str, Any]:
        return self._bridge.host_can_build()

    def launch_wx_action(self, action: str) -> dict[str, Any]:
        return self._bridge.launch_wx_action(action)

    def reveal_log(self) -> dict[str, Any]:
        return self._bridge.reveal_log()

    def open_guide(self) -> dict[str, Any]:
        return self._bridge.open_guide()


def start_wizard_http_server(directory):
    """Serve wizard static files + JSON API on 127.0.0.1 (daemon thread)."""
    httpd, _bridge = start_bridge_http_server(directory)
    return httpd


def _ensure_stdio_for_frozen_gui() -> None:
    if not getattr(sys, "frozen", False):
        return
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


def _requested_backend() -> str:
    return (os.environ.get("X86_GUI_BACKEND") or "auto").strip().lower()


def _should_try_tauri(requested: str) -> bool:
    """Tauri is the default native shell (not Chromium)."""
    if requested in (
        "cocoa",
        "pywebview",
        "webview",
        "qt",
        "chromium",
        "webengine",
        "edge",
        "edgechromium",
    ):
        return False
    return requested in ("auto", "tauri", "webkit", "")


def _should_try_qt_chromium(requested: str) -> bool:
    """Chromium is never the default; Vega/Metal hosts abort in QWebEnginePage."""
    return requested in ("chromium", "qt", "webengine")


def _qt_chromium_available() -> bool:
    """Safe wrapper — find_spec can raise when PySide6 is absent (py3.9)."""
    try:
        return bool(qt_webengine_available())
    except Exception:
        return False


def launch_webview_wizard(*, advanced: bool = False) -> None:
    """Open the HTML hybrid wizard. Default shell is Tauri (WKWebView)."""
    _ensure_stdio_for_frozen_gui()
    bootstrap.ensure_repo_on_path()
    requested = _requested_backend()

    if _should_try_qt_chromium(requested) and _qt_chromium_available():
        try:
            from x86.gui.qt_chromium import launch_qt_chromium_wizard

            logging.info("Launching HTML wizard with Qt WebEngine (Chromium, opt-in)")
            launch_qt_chromium_wizard(advanced=advanced)
            return
        except Exception:
            logging.exception("Qt WebEngine (Chromium) failed; trying Tauri / pywebview")

    if _should_try_tauri(requested):
        try:
            from x86.gui.tauri_app import launch_tauri_wizard, tauri_available

            if tauri_available():
                logging.info("Launching HTML wizard with Tauri (WKWebView / WebView2)")
                launch_tauri_wizard(advanced=advanced)
                return
            logging.info("Tauri binary not found; falling back to pywebview")
        except FileNotFoundError:
            logging.info("Tauri binary missing; falling back to pywebview")
        except Exception:
            logging.exception("Tauri wizard failed; falling back to pywebview")

    if requested in ("tauri", "webkit"):
        logging.warning(
            "X86_GUI_BACKEND=%s requested but Tauri unavailable; using pywebview",
            requested,
        )

    _launch_pywebview_wizard(advanced=advanced, requested=requested)


def _launch_pywebview_wizard(*, advanced: bool, requested: str, smoke_report=None) -> None:
    import webview

    bridge = WizardBridge()
    api = WebviewApi(bridge)

    if advanced:
        result = bridge.launch_wx_action("advanced")
        if result.get("ok"):
            logging.info("Advanced GUI requested; spawned wx runner.")
            return
        logging.warning("Advanced GUI unavailable: %s", result.get("error"))

    web_root = bridge.web_root()
    index_path = bridge.index_path()
    if not index_path.exists():
        raise FileNotFoundError(f"Wizard HTML missing: {index_path}")

    httpd, _ = start_bridge_http_server(web_root, bridge=bridge)
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/index.html"
    logging.info("pywebview wizard url=%s root=%s exists=%s", url, web_root, index_path.exists())

    gui = resolve_pywebview_gui()
    if is_macos():
        gui = "cocoa"
    elif requested in ("edge", "edgechromium"):
        gui = "edgechromium"

    backends = ["cocoa"] if is_macos() else [gui or "gtk"]
    title = bridge.get_app_info()["title"]

    last_error = None
    for index, backend in enumerate(backends):
        try:
            logging.info("Starting pywebview with gui=%s url=%s", backend, url)
            window = webview.create_window(
                title,
                url=url,
                js_api=api,
                width=1180,
                height=820,
                min_size=(760, 560),
                resizable=True,
                text_select=True,
                background_color="#e8edf3",
            )

            def _shutdown_http() -> None:
                try:
                    httpd.shutdown()
                except Exception:
                    logging.debug("wizard http shutdown failed", exc_info=True)

            try:
                window.events.closed += _shutdown_http
            except Exception:
                pass

            def _verify_window():
                import json
                import time
                report = {"ok": False, "backend": backend}
                try:
                    for _ in range(100):
                        status = window.evaluate_js("document.getElementById('status-text')?.textContent")
                        report["status"] = status
                        if status and ("준비" in status or "Ready" in status):
                            report["ok"] = True
                            report["title"] = window.evaluate_js("document.title")
                            break
                        time.sleep(0.2)
                except Exception as exc:
                    report["error"] = str(exc)
                finally:
                    try:
                        report["url"] = window.evaluate_js("location.href")
                        if not report["ok"]:
                            report["body"] = window.evaluate_js("document.body?.innerText?.slice(0, 2000)")
                    except Exception:
                        pass
                    smoke_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                    window.destroy()

            webview.start(_verify_window if smoke_report else None, debug=False, gui=backend, http_server=False)
            return
        except Exception as exc:
            last_error = exc
            logging.warning("pywebview gui=%s failed: %s", backend, exc)
            if index == len(backends) - 1:
                try:
                    httpd.shutdown()
                except Exception:
                    pass
                raise
            continue

    try:
        httpd.shutdown()
    except Exception:
        pass
    if last_error:
        raise last_error


def smoke_test_bridge() -> dict[str, Any]:
    bootstrap.ensure_repo_on_path()
    bridge = WizardBridge()
    results: dict[str, Any] = {"ok": True, "checks": {}}
    for name, fn in (
        ("app_info", bridge.get_app_info),
        ("steps", bridge.get_steps),
        ("detect", lambda: bridge.detect(refresh=False)),
        ("macos", bridge.get_macos_choices),
        ("status", bridge.get_status),
        ("host_can_build", bridge.host_can_build),
    ):
        try:
            payload = fn()
            results["checks"][name] = {
                "ok": True,
                "keys": list(payload.keys()) if isinstance(payload, dict) else len(payload),
            }
        except Exception as exc:
            results["ok"] = False
            results["checks"][name] = {"ok": False, "error": str(exc)}
    results["web_index"] = str(bridge.index_path())
    results["index_is_file_uri"] = False
    results["qt_chromium_available"] = _qt_chromium_available()
    results["pywebview_gui"] = resolve_pywebview_gui()
    results["gui_backend_env"] = _requested_backend()
    results["macos_default_cocoa"] = is_macos() and resolve_pywebview_gui() == "cocoa"
    results["qt_opt_in_only"] = not _should_try_qt_chromium(_requested_backend())
    results["tauri_preferred"] = _should_try_tauri(_requested_backend())
    try:
        from x86.gui.tauri_app import smoke_tauri_paths

        results["tauri"] = smoke_tauri_paths()
    except Exception as exc:
        results["tauri"] = {"ok": False, "error": str(exc)}
    return results


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv and argv[0] == "--smoke":
        import json

        payload = smoke_test_bridge()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 1
    launch_webview_wizard(advanced="--advanced" in argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
