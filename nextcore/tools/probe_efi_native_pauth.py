#!/usr/bin/env python3
"""Run the ISE-owned native ARM64e JIT proof from the integration workspace."""
from pathlib import Path
import runpy
if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] /
        "crates/nextcore-ise/tools/probe_efi_native_pauth.py"), run_name="__main__")
