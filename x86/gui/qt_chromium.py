"""
Chromium wizard shell via PySide6 Qt WebEngine.

Opt-in only (``X86_GUI_BACKEND=qt`` / ``chromium`` / ``webengine``).
Default GUI is Tauri (WKWebView / WebView2); Cocoa pywebview is the fallback.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

from x86.gui.bridge import WizardBridge
from x86.gui.webview_app import WebviewApi


def qt_chromium_available() -> bool:
    """True when PySide6 Qt WebEngine can be imported."""
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
        from PySide6.QtWebChannel import QWebChannel  # noqa: F401

        return True
    except Exception:
        return False


def _frozen_webengine_process() -> Optional[str]:
    """Locate QtWebEngineProcess inside a PyInstaller .app (symlink layout varies)."""
    if not getattr(sys, "frozen", False):
        return None
    roots: list[Path] = []
    exe = Path(sys.executable).resolve()
    if exe.parent.name == "MacOS":
        roots.append(exe.parent.parent)  # Contents
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
        roots.append(Path(meipass).parent)
    seen: set[Path] = set()
    for root in roots:
        if root in seen or not root.exists():
            continue
        seen.add(root)
        for relative in (
            "Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework/Versions/Resources/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess",
            "Resources/PySide6/Qt/lib/QtWebEngineCore.framework/Versions/Resources/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess",
            "MacOS/QtWebEngineProcess",
        ):
            candidate = root / relative
            if candidate.is_file():
                return str(candidate)
    return None


def _prepare_qt_environment() -> None:
    os.environ.setdefault("QT_API", "pyside6")
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    process = _frozen_webengine_process()
    if process:
        os.environ["QTWEBENGINEPROCESS_PATH"] = process
        logging.info("QtWebEngineProcess=%s", process)
    if getattr(sys, "frozen", False):
        os.environ.setdefault(
            "QTWEBENGINE_CHROMIUM_FLAGS",
            "--disable-in-process-stack-traces --disable-gpu-sandbox",
        )


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logging.debug("wizard http: " + format, *args)


def _start_http_server(directory) -> ThreadingHTTPServer:
    handler = partial(_QuietHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True, name="26x86-wizard-http")
    thread.start()
    return httpd


def launch_qt_chromium_wizard(*, advanced: bool = False) -> None:
    """Block until the Chromium wizard window is closed."""
    _prepare_qt_environment()

    from PySide6.QtCore import QObject, QUrl, Slot
    from PySide6.QtGui import QColor
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication, QMainWindow

    from x86.gui import bootstrap

    bootstrap.ensure_repo_on_path()
    bridge = WizardBridge()
    api = WebviewApi(bridge)

    if advanced:
        result = bridge.launch_wx_action("advanced")
        if result.get("ok"):
            logging.info("Advanced GUI requested; spawned wx runner.")
            return
        logging.warning("Advanced GUI unavailable: %s", result.get("error"))

    class QtWizardApi(QObject):
        """QWebChannel facade matching WebviewApi / window.pywebview.api."""

        def __init__(self) -> None:
            super().__init__()

        @Slot(result="QVariant")
        def get_app_info(self):
            return api.get_app_info()

        @Slot(result="QVariant")
        def get_sandbox_status(self):
            return api.get_sandbox_status()

        @Slot(str, result="QVariant")
        def set_execution_mode(self, mode):
            return api.set_execution_mode(mode)

        @Slot(int, result="QVariant")
        def get_sandbox_plan(self, target_major):
            return api.get_sandbox_plan(target_major)

        @Slot(int, str, result="QVariant")
        def prepare_sandbox(self, target_major, output_path):
            return api.prepare_sandbox(target_major, output_path)

        @Slot(result="QVariant")
        def get_steps(self):
            return api.get_steps()

        @Slot(bool, result="QVariant")
        def detect(self, refresh: bool = False):
            return api.detect(refresh)

        @Slot(result="QVariant")
        def get_macos_choices(self):
            return api.get_macos_choices()

        @Slot(int, result="QVariant")
        def set_target_os(self, kernel: int):
            return api.set_target_os(kernel)

        @Slot(result="QVariant")
        def get_patch_status(self):
            return api.get_patch_status()

        @Slot(result="QVariant")
        def get_status(self):
            return api.get_status()

        @Slot(result="QVariant")
        def get_settings(self):
            return api.get_settings()

        @Slot("QVariantMap", result="QVariant")
        def save_settings(self, data):
            return api.save_settings(dict(data) if data is not None else {})

        @Slot(result="QVariant")
        def host_can_build(self):
            return api.host_can_build()

        @Slot(str, result="QVariant")
        def launch_wx_action(self, action: str):
            return api.launch_wx_action(action)

        @Slot(result="QVariant")
        def reveal_log(self):
            return api.reveal_log()

        @Slot(result="QVariant")
        def open_guide(self):
            return api.open_guide()

    class LoggingPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):  # noqa: N802
            logging.warning(
                "wizard JS [%s] %s:%s %s",
                level,
                sourceID,
                lineNumber,
                message,
            )

    class WizardWindow(QMainWindow):
        def __init__(self, title: str, url: str, httpd: ThreadingHTTPServer) -> None:
            super().__init__()
            self._httpd = httpd
            self.setWindowTitle(title)
            self.resize(1180, 820)
            self.setMinimumSize(760, 560)

            view = QWebEngineView(self)
            page = LoggingPage(view)
            view.setPage(page)
            settings = view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
            view.setStyleSheet("background-color: #e8edf3;")

            channel = QWebChannel(page)
            self._qt_api = QtWizardApi()
            channel.registerObject("bridge", self._qt_api)
            page.setWebChannel(channel)

            page.loadFinished.connect(self._on_load_finished)
            view.load(QUrl(url))
            self.setCentralWidget(view)
            self._view = view
            self._url = url

        def _on_load_finished(self, ok: bool) -> None:
            logging.info("Chromium wizard loadFinished ok=%s url=%s", ok, self._url)
            if not ok:
                logging.error("Chromium failed to load %s", self._url)
            self._view.page().runJavaScript(_BRIDGE_INJECT_JS)

        def closeEvent(self, event) -> None:  # noqa: N802
            try:
                self._httpd.shutdown()
            except Exception:
                logging.debug("wizard http shutdown failed", exc_info=True)
            event.accept()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("26x86")
    app.setQuitOnLastWindowClosed(True)
    palette_bg = QColor("#e8edf3")
    app.setStyleSheet(f"QMainWindow {{ background-color: {palette_bg.name()}; }}")

    httpd = _start_http_server(bridge.web_root())
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/index.html"
    logging.info("Starting Chromium wizard at %s (root=%s)", url, bridge.web_root())

    window = WizardWindow(bridge.get_app_info()["title"], url, httpd)
    window.show()
    window.raise_()
    window.activateWindow()
    app.exec()


_BRIDGE_INJECT_JS = """
(function () {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.__qtWrapped) {
    return;
  }
  function promisifyBridge(bridge) {
    var names = [
      "get_app_info", "get_steps", "detect", "get_macos_choices", "set_target_os",
      "get_patch_status", "get_status", "get_settings", "save_settings",
      "host_can_build", "launch_wx_action", "reveal_log", "open_guide"
    ];
    var wrapped = { __qtWrapped: true };
    names.forEach(function (name) {
      wrapped[name] = function () {
        var args = Array.prototype.slice.call(arguments);
        return new Promise(function (resolve, reject) {
          try {
            var fn = bridge[name];
            if (typeof fn !== "function") {
              reject(new Error(name + " is not available"));
              return;
            }
            fn.apply(bridge, args.concat([function (ret) { resolve(ret); }]));
          } catch (err) {
            reject(err);
          }
        });
      };
    });
    return wrapped;
  }
  function attach(api) {
    if (!api) {
      return;
    }
    window.pywebview = { api: promisifyBridge(api) };
    window.dispatchEvent(new Event("pywebviewready"));
  }
  function connect() {
    if (typeof QWebChannel === "undefined" || typeof qt === "undefined" || !qt.webChannelTransport) {
      return false;
    }
    new QWebChannel(qt.webChannelTransport, function (channel) {
      attach(channel.objects.bridge);
    });
    return true;
  }
  if (connect()) {
    return;
  }
  var script = document.createElement("script");
  script.src = "qrc:///qtwebchannel/qwebchannel.js";
  script.onload = connect;
  script.onerror = function () {
    console.error("qwebchannel.js failed to load from qrc");
  };
  document.head.appendChild(script);
})();
"""
