"""Auditable, macOS-only entry to the existing APFS root patch engine."""

from __future__ import annotations

import os
from pathlib import Path
from x86.platform import is_macos, MACOS_ONLY_MESSAGE
from x86.surface import PROFILE_ID, configure_surface_constants


def _context(profile=None, payload_dir=None):
    from opencore_legacy_patcher.constants import Constants
    from opencore_legacy_patcher.detections import device_probe, os_probe

    c = Constants()
    from x86.paths import Paths
    c.payload_path = Paths.repo_root() / "payloads"
    probe = os_probe.OSProbe()
    c.detected_os = probe.detect_kernel_major()
    c.detected_os_minor = probe.detect_kernel_minor()
    c.detected_os_build = probe.detect_os_build()
    c.detected_os_version = probe.detect_os_version()
    c.computer = device_probe.Computer.probe()
    c.cli_mode = True
    c.gui_mode = False
    if payload_dir:
        c.payload_path = Path(payload_dir).expanduser().resolve()
    if profile == PROFILE_ID:
        configure_surface_constants(c)
    return c


def preflight(profile=None, payload_dir=None, *, constants=None, abstraction_manifest=None):
    """No root writes, payload mounts, or privileges requested by this entry."""
    if not is_macos():
        return {"ok": False, "status": "unsupported_platform", "can_patch": False, "error": MACOS_ONLY_MESSAGE}
    if profile not in (None, PROFILE_ID):
        return {"ok": False, "status": "invalid_profile", "can_patch": False, "error": "Unknown root patch profile"}
    try:
        c = constants or _context(profile, payload_dir)
        abstraction = None
        if c.detected_os >= 26 or abstraction_manifest is not None:
            from x86.patch.abstraction import deployment_gate
            abstraction = deployment_gate(c, abstraction_manifest)
            if not abstraction["ok"]:
                return {"ok": False, "status": "abstraction_blocked", "can_patch": False,
                        "blockers": abstraction["errors"], "abstraction": abstraction,
                        "os_build": c.detected_os_build, "hardware_verified": False}
        if profile == PROFILE_ID:
            configure_surface_constants(c)
            if c.detected_os != 25:
                raise ValueError("The Surface Tahoe root profile requires installed Darwin 25 / macOS 26.")
        from opencore_legacy_patcher.sys_patch.patchsets import HardwarePatchsetDetection

        detected = HardwarePatchsetDetection(c)
        patches = list(detected.patches)
        blockers = []
        if profile == PROFILE_ID and any(name != "Modern Audio" for name in patches):
            blockers.append("Unexpected patch set for UHD 620. This profile permits only Modern Audio: " + ", ".join(patches))
        if not detected.can_patch:
            blockers.append("Live SIP / AMFI / FileVault / update / security validation rejected patching.")
        kdk_report = None
        warnings = []
        if detected.device_properties.get("Settings: Kernel Debug Kit required"):
            from opencore_legacy_patcher.support.kdk_handler import KernelDebugKitObject
            kdk = KernelDebugKitObject(c, c.detected_os_build, c.detected_os_version, passive=True)
            selected_build = kdk.kdk_url_build
            if not selected_build and kdk.kdk_installed_path:
                selected_build = Path(kdk.kdk_installed_path).stem.rsplit("_", 1)[-1]
            kdk_report = {"available": bool(kdk.success), "host_build": c.detected_os_build,
                          "selected_build": selected_build or None,
                          "exact_build_match": bool(selected_build) and selected_build == c.detected_os_build,
                          "installed": bool(kdk.kdk_already_installed), "url": kdk.kdk_url or None,
                          "error": kdk.error_msg or None}
            if not kdk.success:
                blockers.append("No usable KDK selected: " + kdk.error_msg)
            elif not kdk_report["exact_build_match"]:
                warnings.append("The existing engine selected a nearby KDK build, not an exact match. Review the KDK report before applying.")
        payload = Path(c.payload_local_binaries_root_path_dmg)
        if patches and not payload.is_file():
            blockers.append(f"Missing published support payload: {payload}. See docs/SURFACE_PRO6.md.")
        return {"ok": not blockers, "status": "blocked" if blockers else ("ready" if patches else "not_required"),
                "can_patch": not blockers and bool(patches), "patches": patches, "blockers": blockers,
                "validations": dict(detected.device_properties), "os_build": c.detected_os_build,
                "payload": str(payload), "profile": profile, "hardware_verified": False,
                "kdk": kdk_report, "warnings": warnings}
    except Exception as exc:
        return {"ok": False, "status": "preflight_failed", "can_patch": False, "error": str(exc)}


def apply(profile=None, payload_dir=None, *, abstraction_manifest=None):
    if not is_macos():
        return preflight(profile, payload_dir, abstraction_manifest=abstraction_manifest)
    try:
        c = _context(profile, payload_dir)
        report = preflight(profile, payload_dir, constants=c, abstraction_manifest=abstraction_manifest)
        if not report.get("can_patch"):
            return report
        if os.geteuid() != 0:
            return {**report, "ok": False, "status": "needs_root", "error": "Run this explicit --apply command through sudo on the installed macOS."}
        from opencore_legacy_patcher.sys_patch.sys_patch import PatchSysVolume

        engine = PatchSysVolume(c.computer.real_model, c)
        # No interactive Software Update prompt in automated CLI calls. A pending
        # update still stops the existing engine before root file writes.
        completed = engine.start_patch(interactive=False)
        succeeded = completed is True and bool(c.root_patcher_succeeded)
        return {**report, "ok": succeeded, "status": "patched_reboot_required" if succeeded else "patch_failed",
                "reboot_required": succeeded, "hardware_verified": False}
    except Exception as exc:
        return {"ok": False, "status": "patch_failed", "error": str(exc)}
