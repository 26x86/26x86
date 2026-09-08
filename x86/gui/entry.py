"""Portable GUI packaging entry; never starts the macOS legacy application on Windows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def dispatch_cli(argv):
    """Frozen GUI binaries expose CLI before any GUI/native imports or help."""
    # A windowed PyInstaller binary can start without standard streams. Match
    # the GUI's stdio fallback without importing its webview stack here.
    if getattr(sys, "frozen", False):
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")
    from x86.cli import main as cli_main
    return cli_main(argv)


def main():
    if sys.argv[1:2] == ["--x86-cli"]:
        return dispatch_cli(sys.argv[2:])
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-report", type=Path, help="Write a backend smoke report without opening a window")
    parser.add_argument("--gui-smoke-report", type=Path, help="Open the native window, verify its DOM and close it")
    args = parser.parse_args()
    from x86.gui.webview_app import _ensure_stdio_for_frozen_gui, smoke_test_bridge, launch_webview_wizard, _launch_pywebview_wizard
    _ensure_stdio_for_frozen_gui()
    if args.smoke_report:
        report = smoke_test_bridge()
        args.smoke_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if report["ok"] else 1
    if args.gui_smoke_report:
        _launch_pywebview_wizard(advanced=False, requested="auto", smoke_report=args.gui_smoke_report)
        if not args.gui_smoke_report.exists():
            return 1
        return 0 if json.loads(args.gui_smoke_report.read_text(encoding="utf-8")).get("ok") else 1
    launch_webview_wizard()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
