"""
Local HTTP server for the HTML wizard: static assets + JSON bridge API.

Used by Tauri (WKWebView / WebView2) and as a fallback transport when
pywebview ``js_api`` is unavailable. API contract mirrors ``WizardBridge``.
"""

from __future__ import annotations

import json
import logging
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import urlparse

from x86.gui.bridge import WizardBridge


API_METHODS = frozenset(
    {
        "get_app_info",
        "get_sandbox_status",
        "set_execution_mode",
        "get_sandbox_plan",
        "prepare_sandbox",
        "get_vmapple_status",
        "inspect_vmapple_storage",
        "get_boot_picker_status",
        "start_boot_picker",
        "tick_boot_picker",
        "boot_picker_key",
        "select_boot_entry",
        "launch_vmapple",
        "set_hardware_profile",
        "validate_surface_efi",
        "get_steps",
        "detect",
        "get_macos_choices",
        "set_target_os",
        "get_patch_status",
        "get_silicon_sandbox_demo",
        "get_status",
        "get_settings",
        "save_settings",
        "prepare_mellow_efi",
        "prepare_mellow_root_efi",
        "host_can_build",
        "launch_wx_action",
        "reveal_log",
        "open_guide",
        "mark_build_completed",
    }
)


class _WizardHTTPHandler(SimpleHTTPRequestHandler):
    bridge: WizardBridge

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logging.debug("wizard http: " + format, *args)

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(403, {"ok": False, "error": "Cross-origin bridge requests are disabled"})

    def _local_request(self) -> bool:
        host = self.headers.get("Host", "")
        port = self.server.server_address[1]
        if host not in (f"127.0.0.1:{port}", f"localhost:{port}"):
            self._send_json(403, {"ok": False, "error": "Invalid bridge host"})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            self._send_json(403, {"ok": False, "error": "Cross-origin bridge requests are disabled"})
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802
        if not self._local_request():
            return
        parsed = urlparse(self.path)
        if parsed.path in ("/api/health", "/api/ping"):
            self._send_json(200, {"ok": True, "transport": "http"})
            return
        if parsed.path.startswith("/api/"):
            method = parsed.path[len("/api/") :].strip("/")
            if method in API_METHODS and method.startswith("get_"):
                self._invoke(method, [])
                return
            self._send_json(404, {"ok": False, "error": f"Unknown API: {method}"})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if not self._local_request():
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"ok": False, "error": "JSON requests required"})
            return
        try:
            size = int(self.headers.get("Content-Length") or 0)
            if size < 0 or size > 1048576:
                raise ValueError()
        except ValueError:
            self._send_json(413, {"ok": False, "error": "Invalid request length"})
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/invoke":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._send_json(400, {"ok": False, "error": "Invalid JSON"})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "Request must be an object"})
                return
            method = str(payload.get("method") or "")
            args = payload.get("args") or []
            if not isinstance(args, list):
                self._send_json(400, {"ok": False, "error": "args must be a list"})
                return
            self._invoke(method, args)
            return

        if parsed.path.startswith("/api/"):
            method = parsed.path[len("/api/") :].strip("/")
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            args: list[Any] = []
            if raw:
                try:
                    body = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    self._send_json(400, {"ok": False, "error": "Invalid JSON"})
                    return
                if isinstance(body, list):
                    args = body
                elif isinstance(body, dict):
                    if "args" in body and isinstance(body["args"], list):
                        args = body["args"]
                    else:
                        args = [body]
            self._invoke(method, args)
            return

        self._send_json(404, {"ok": False, "error": "Not found"})

    def _invoke(self, method: str, args: list[Any]) -> None:
        if method not in API_METHODS:
            self._send_json(404, {"ok": False, "error": f"Unknown method: {method}"})
            return
        fn = getattr(self.bridge, method, None)
        if not callable(fn):
            self._send_json(500, {"ok": False, "error": f"Method missing: {method}"})
            return
        try:
            result = fn(*args)
            self._send_json(200, {"ok": True, "result": result})
        except TypeError as exc:
            logging.exception("API %s bad args", method)
            self._send_json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            logging.exception("API %s failed", method)
            self._send_json(500, {"ok": False, "error": str(exc)})


def start_bridge_http_server(
    directory,
    *,
    bridge: Optional[WizardBridge] = None,
    host: str = "127.0.0.1",
    port: int = 0,
) -> tuple[ThreadingHTTPServer, WizardBridge]:
    """Serve wizard static files and ``/api/*`` on a local port (daemon thread)."""
    wiz = bridge or WizardBridge()
    web_root = str(directory)

    class BoundHandler(_WizardHTTPHandler):
        bridge = wiz

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=web_root, **kwargs)

    httpd = ThreadingHTTPServer((host, port), BoundHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True, name="26x86-wizard-http")
    thread.start()
    return httpd, wiz


def wizard_base_url(httpd: ThreadingHTTPServer) -> str:
    host, port = httpd.server_address[:2]
    return f"http://{host}:{port}"
