"""
Shared constants bootstrap for HTML wizard bridge and wx subprocess runner.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional

from opencore_legacy_patcher import constants
from x86.platform import is_linux, is_macos, is_windows


_constants: Optional[constants.Constants] = None
_init_lock = threading.Lock()


def ensure_repo_on_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def get_constants(*, start_unpack: bool = True, settings=None) -> constants.Constants:
    """Return a process-wide Constants instance (lazy, thread-safe)."""
    global _constants
    from x86.mellow.integration import configuration, configure_constants
    context, deployment, payload, efi = configuration(settings=settings)
    key = (context.mode.value, deployment, str(payload), str(efi or ""))
    if _constants is not None and getattr(_constants, "_gui_execution_key", None) == key:
        return _constants

    with _init_lock:
        if _constants is not None and getattr(_constants, "_gui_execution_key", None) == key:
            return _constants

        ensure_repo_on_path()
        c = constants.Constants()
        c.wxpython_variant = True
        c.gui_mode = True
        c.cli_mode = False
        configure_constants(c, settings=settings)
        c._gui_execution_key = key

        if not is_macos() or not context.can_native_apply:
            # Preparation hosts must never import Security/IOKit or run macOS
            # probes and payload mounts just to render the wizard.
            from types import SimpleNamespace
            from x86.platform import non_mac_detect_payload

            host = non_mac_detect_payload() if not is_macos() else {"model": (
                "Apple Silicon Sandbox" if context.is_sandbox else "Native host verification unavailable")}
            c.computer = SimpleNamespace(real_model=host["model"], build_model=host["model"])
            c.detected_os = 25  # target Darwin; not a claim about the host OS
            c.detected_os_minor = 0
            c.detected_os_build = ""
            c.detected_os_version = ""
            c.host_is_hackintosh = True
            c.launcher_binary = sys.executable
            c.launcher_script = str(ensure_repo_on_path() / ("26x86.bat" if is_windows() else "26x86.sh"))
            _constants = c
            return c

        from opencore_legacy_patcher.detections import device_probe, os_probe
        from opencore_legacy_patcher.support import defaults, reroute_payloads, utilities

        os_data = os_probe.OSProbe()
        c.detected_os = os_data.detect_kernel_major()
        c.detected_os_minor = os_data.detect_kernel_minor()
        c.detected_os_build = os_data.detect_os_build()
        c.detected_os_version = os_data.detect_os_version()

        c.computer = device_probe.Computer.probe()
        if not is_macos():
            c.host_is_hackintosh = True
        elif c.computer.firmware_vendor != "Apple":
            c.host_is_hackintosh = True
        if c.computer.real_model and c.computer.real_model.startswith("VMware"):
            c.host_is_hackintosh = True
            c.host_is_vmware_vm = True

        if c.computer.build_model is None:
            c.computer.build_model = c.computer.real_model

        defaults.GenerateDefaults(c.computer.real_model, True, c)

        if start_unpack and is_macos():
            c.unpack_thread = threading.Thread(
                target=reroute_payloads.RoutePayloadDiskImage,
                args=(c,),
                daemon=True,
            )
            c.unpack_thread.start()

        launcher_binary = sys.executable
        repo = ensure_repo_on_path()
        if is_macos() and "python" in launcher_binary.lower():
            c.launcher_script = str(repo / "26x86-GUI.command")
        elif is_windows():
            c.launcher_script = str(repo / "26x86.bat")
        elif is_linux():
            c.launcher_script = str(repo / "26x86.sh")
        c.launcher_binary = launcher_binary

        if is_macos():
            try:
                c.booted_oc_disk = utilities.find_disk_off_uuid(
                    utilities.clean_device_path(c.computer.opencore_path)
                )
            except Exception as exc:
                logging.debug("booted_oc_disk unavailable: %s", exc)

        _constants = c
        return c


def reset_constants() -> None:
    """Clear cached constants (tests)."""
    global _constants
    with _init_lock:
        _constants = None
