#!/usr/bin/env python3
"""
PyInstaller Entry Point - Hardened with Full Extraction Fix
"""
import sys
import logging
import os
import zipfile
import shutil
import subprocess
from pathlib import Path

# Packaged GUI executable CLI re-entry must precede legacy help/GUI imports.
if sys.argv[1:2] == ["--x86-cli"]:
    from x86.gui.entry import dispatch_cli
    raise SystemExit(dispatch_cli(sys.argv[2:]))

# Fast path: show CLI help without loading the full GUI stack
if "--help" in sys.argv or "-h" in sys.argv:
    _lang = "en"
    for i, arg in enumerate(sys.argv):
        if arg == "--lang" and i + 1 < len(sys.argv):
            _lang = sys.argv[i + 1]
            break
        if arg.startswith("--lang="):
            _lang = arg.split("=", 1)[1]
            break
    if _lang not in ("ko", "en"):
        _lang = "en"
    from opencore_legacy_patcher.support.cli import build_parser
    build_parser(_lang).print_help()
    sys.exit(0)

# SECURITY FIX: Remove the current directory from the search path.
if "" in sys.path:
    sys.path.remove("")

# We configure logging to write to sys.stdout (the Terminal window)
logging.basicConfig(
    level=logging.ERROR,
    format='%(message)s', # Keep it clean for the Terminal
    stream=sys.stdout
)

from opencore_legacy_patcher import main

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("\n" + "="*60)
        logging.error("Whoops, the app crashed because of the following error:")
        print(f"Direct Error: {e}")
        print("-" * 60)
        logging.exception("Stack Trace:")
        print("="*60)
        input("\nPress ENTER to close this window...")
        sys.exit(3)
