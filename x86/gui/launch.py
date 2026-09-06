"""
Bootstrap and launch the default 26x86 wizard GUI.
"""

import os
import sys
from pathlib import Path


def _ensure_repo_root() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _strip_x86_subcommand() -> None:
    """Remove ``python -m x86 <subcommand>`` tokens so legacy CLI parsing succeeds."""
    filtered: list[str] = []
    skip_next = False
    for i, arg in enumerate(sys.argv):
        if skip_next:
            skip_next = False
            continue
        if i == 0:
            filtered.append(arg)
            continue
        if arg in ("-m", "x86"):
            continue
        if arg in ("wizard", "detect", "build", "patch", "status"):
            continue
        if arg == "--json":
            continue
        if arg.startswith("--model="):
            continue
        if arg == "--model":
            skip_next = True
            continue
        filtered.append(arg)
    sys.argv = filtered


def _launch_legacy_wx(advanced: bool = False) -> None:
    from x86.mellow.integration import configuration
    configuration()[0].require_native_apply("Legacy native GUI")
    _ensure_repo_root()
    _strip_x86_subcommand()
    if advanced:
        if os.environ.get("X86_ADVANCED") != "1":
            os.environ["X86_ADVANCED"] = "1"
        if "--advanced_gui" not in sys.argv:
            sys.argv.append("--advanced_gui")
    from opencore_legacy_patcher.application_entry import main

    main()


def launch_wizard(advanced: bool = False) -> None:
    """
    Start the default end-user wizard.

    Default: Tauri shell (WKWebView / WebView2) over local HTTP bridge.
    Fallbacks: pywebview Cocoa (macOS), then legacy wx when ``X86_LEGACY_GUI=1``
    or HTML shells cannot start. Qt WebEngine (Chromium) is opt-in via
    ``X86_GUI_BACKEND=qt``.
    """
    _ensure_repo_root()

    if os.environ.get("X86_LEGACY_GUI") == "1":
        _launch_legacy_wx(advanced=advanced)
        return

    try:
        from x86.gui.webview_app import launch_webview_wizard

        launch_webview_wizard(advanced=advanced)
    except ImportError as exc:
        import logging

        logging.warning("HTML wizard unavailable (%s); falling back to legacy wx wizard.", exc)
        _launch_legacy_wx(advanced=advanced)


def launch_advanced_gui() -> None:
    """Start the legacy wx MainFrame (requires ``X86_ADVANCED=1``)."""
    from x86.gui.branding import is_advanced_gui_enabled

    if not is_advanced_gui_enabled():
        raise RuntimeError(
            "Advanced GUI requires X86_ADVANCED=1. "
            "Normal users should use: python -m x86 wizard"
        )
    _launch_legacy_wx(advanced=True)
