"""Conservative UART evidence extraction for the Apple boot-chain boundary.

This module is deliberately a parser, not a boot-success generator.  It only
reports a stage when a byte marker is present in the caller-provided UART
transcript.  In particular, a QEMU process exit, an iBoot ACK, a firmware
version string, or a synthetic guest result cannot promote the XNU or macOS
stages.

The layer represented here is the guest-visible boot chain::

    original AVPBooter/iBoot -> XNU -> macOS userspace

It is independent of the EFI/preOS layer and of the QEMU machine-capability
probe.  Callers can use ``parse_uart_evidence`` for a completed log or
combine it with a bounded growing-file observer owned by the runtime runner.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


MAX_KERNEL_MAJOR = 99

# These are intentionally conservative.  A generic "iBoot" string is useful
# context but is not enough to distinguish a running stage, so the stage
# prompts/supervisor banners are preferred.  The markers are bytes because
# UART output is an untrusted binary stream and offsets must remain exact.
IBOOT_STAGE1_MARKERS = (
    b"Entering iBootStage1 recovery mode, starting command prompt",
    b"Supervisor iBootStage1",
)
IBOOT_STAGE2_MARKERS = (
    b"Entering iBootStage2 recovery mode, starting command prompt",
    b"Supervisor iBootStage2",
    # The raw iBootStage2 restore-ramdisk run emits this framing banner before
    # its panic.  It proves that the Stage2 image executed, but it must not be
    # treated as proof of an iBoot -> XNU handoff or a successful macOS boot.
    b"======== Start of iBootStage2 serial output. ========",
)
XNU_MARKERS = (b"Darwin Kernel Version", b"Darwin Kernel")
USERSPACE_MARKERS = (b"launchd:", b"launchd ", b"loginwindow", b"WindowServer")
INSTALLER_MARKERS = (b"macOS Utilities", b"Install macOS", b"RecoveryOS")
# These markers are intentionally independent of the boot-chain markers.  A
# WindowServer process can start with a software renderer, so its name alone
# is never promoted to accelerated graphics.  The provider/device markers
# are the small, portable subset emitted by macOS diagnostics and IORegistry.
GRAPHICS_WINDOWSERVER_MARKERS = (b"WindowServer",)
GRAPHICS_ACCELERATOR_MARKERS = (
    b"IOAccelerator",
    b"AppleGPUWrangler",
    b"AGXAccelerator",
    b"AGXMetal",
)
GRAPHICS_METAL_MARKERS = (
    b"Metal device",
    b"MTLDevice",
    b"MTLCreateSystemDefaultDevice",
    b"Metal GPU",
)
GRAPHICS_FRAMEBUFFER_MARKERS = (
    b"framebuffer presented",
    b"CAMetalLayer drawable",
    b"IOSurface accelerated",
    b"CoreAnimation compositor: GPU",
)
_KERNEL_VERSION_RE = re.compile(rb"Darwin Kernel Version\s+([0-9]+)(?:\.[0-9]+)*")


@dataclass(frozen=True)
class MarkerEvidence:
    """One marker occurrence in a UART transcript."""

    category: str
    marker: str
    byte_offset: int
    kernel_major: int | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "category": self.category,
            "marker": self.marker,
            "byte_offset": self.byte_offset,
        }
        if self.kernel_major is not None:
            result["kernel_major"] = self.kernel_major
        return result


def _occurrences(data: bytes, category: str, markers: Iterable[bytes], *, kernel: bool = False) -> list[MarkerEvidence]:
    """Return every distinct marker occurrence, retaining the absolute offset."""
    found: list[MarkerEvidence] = []
    seen: set[tuple[str, int]] = set()
    for marker in markers:
        start = 0
        while True:
            position = data.find(marker, start)
            if position < 0:
                break
            key = (category, position)
            if key not in seen:
                major: int | None = None
                if kernel:
                    version = _KERNEL_VERSION_RE.search(data[position:position + 256])
                    if version is not None:
                        value = int(version.group(1))
                        if 1 <= value <= MAX_KERNEL_MAJOR:
                            major = value
                found.append(MarkerEvidence(category, marker.decode("ascii", "replace"), position, major))
                seen.add(key)
            start = position + max(1, len(marker))
    found.sort(key=lambda item: (item.byte_offset, item.category, item.marker))
    return found


def parse_uart_evidence(data: bytes, *, expected_kernel_major: int | None = None) -> dict[str, object]:
    """Classify the observed boot stages without inferring missing stages.

    ``expected_kernel_major`` is a policy gate, not a way to supply a missing
    version.  When the Darwin banner omits a parseable version, target match is
    false for a requested target.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("UART evidence must be bytes-like")
    if expected_kernel_major is not None and (
        isinstance(expected_kernel_major, bool)
        or not isinstance(expected_kernel_major, int)
        or not 1 <= expected_kernel_major <= MAX_KERNEL_MAJOR
    ):
        raise ValueError("expected kernel major must be between 1 and 99")
    raw = bytes(data)
    evidence = {
        "iboot_stage1": _occurrences(raw, "iboot_stage1", IBOOT_STAGE1_MARKERS),
        "iboot_stage2": _occurrences(raw, "iboot_stage2", IBOOT_STAGE2_MARKERS),
        "xnu": _occurrences(raw, "xnu", XNU_MARKERS, kernel=True),
        "userspace": _occurrences(raw, "userspace", USERSPACE_MARKERS),
        "installer": _occurrences(raw, "installer", INSTALLER_MARKERS),
        "graphics_windowserver": _occurrences(raw, "graphics_windowserver", GRAPHICS_WINDOWSERVER_MARKERS),
        "graphics_accelerator": _occurrences(raw, "graphics_accelerator", GRAPHICS_ACCELERATOR_MARKERS),
        "graphics_metal": _occurrences(raw, "graphics_metal", GRAPHICS_METAL_MARKERS),
        "graphics_framebuffer": _occurrences(raw, "graphics_framebuffer", GRAPHICS_FRAMEBUFFER_MARKERS),
    }
    # The order check avoids treating unrelated log fragments as a handoff.
    stage2_offset = min((item.byte_offset for item in evidence["iboot_stage2"]), default=None)
    xnu_offset = min((item.byte_offset for item in evidence["xnu"]), default=None)
    userspace_offset = min((item.byte_offset for item in evidence["userspace"]), default=None)
    majors = sorted({
        item.kernel_major for item in evidence["xnu"]
        if item.kernel_major is not None
    })
    target_match = expected_kernel_major is None or expected_kernel_major in majors
    xnu_executed = bool(evidence["xnu"])
    userspace_reached = bool(evidence["userspace"])
    iboot_executed = bool(evidence["iboot_stage1"] or evidence["iboot_stage2"])
    stage2_to_xnu = (
        stage2_offset is not None and xnu_offset is not None and stage2_offset <= xnu_offset
    )
    xnu_to_userspace = (
        xnu_offset is not None and userspace_offset is not None and xnu_offset <= userspace_offset
    )
    macos_boot_verified = xnu_executed and userspace_reached and target_match and xnu_to_userspace
    graphics = parse_graphics_evidence(raw)
    if macos_boot_verified:
        blocker = None
    elif not iboot_executed:
        blocker = "No iBoot Stage1/Stage2 UART marker was observed"
    elif not xnu_executed:
        blocker = "iBoot evidence exists, but no Darwin/XNU UART marker was observed"
    elif not userspace_reached:
        blocker = "XNU UART evidence exists, but no macOS userspace marker was observed"
    elif not xnu_to_userspace:
        blocker = "macOS userspace marker preceded the Darwin/XNU marker"
    elif expected_kernel_major is not None and not majors:
        blocker = "Darwin/XNU marker has no parseable kernel major for target matching"
    elif expected_kernel_major is not None:
        blocker = f"Darwin/XNU kernel major mismatch (observed={majors}, expected={expected_kernel_major})"
    else:
        blocker = "Boot evidence is incomplete"
    return {
        "iboot_executed": iboot_executed,
        "iboot_stage1_verified": bool(evidence["iboot_stage1"]),
        "iboot_stage2_verified": bool(evidence["iboot_stage2"]),
        "iboot_to_xnu_handoff_verified": stage2_to_xnu,
        "xnu_to_userspace_handoff_verified": xnu_to_userspace,
        "xnu_executed": xnu_executed,
        "macos_userspace_reached": userspace_reached,
        "guest_kernel_majors": majors,
        "guest_target_match": target_match,
        "macos_boot_verified": macos_boot_verified,
        "installer_ui_visible": bool(evidence["installer"]),
        "installation_verified": False,
        "observed_markers": {
            category: [item.as_dict() for item in items]
            for category, items in evidence.items()
        },
        "direct_boot_blocker": blocker,
        "expected_kernel_major": expected_kernel_major,
        "byte_length": len(raw),
        "evidence_policy": "UART markers only; no ACK/process-exit/synthetic promotion",
        "graphics": graphics,
    }


def parse_graphics_evidence(data: bytes) -> dict[str, object]:
    """Evaluate WindowServer acceleration evidence from a guest transcript.

    This is deliberately a conjunctive gate: WindowServer + an accelerator
    provider + a Metal device are required.  A framebuffer/compositor marker
    is reported separately because serial logs often omit it; callers that
    need proof of an actually presented accelerated frame must require that
    field too.  No marker is treated as proof merely because QEMU exited.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("graphics evidence must be bytes-like")
    raw = bytes(data)
    groups = {
        "windowserver": _occurrences(raw, "graphics_windowserver", GRAPHICS_WINDOWSERVER_MARKERS),
        "accelerator": _occurrences(raw, "graphics_accelerator", GRAPHICS_ACCELERATOR_MARKERS),
        "metal": _occurrences(raw, "graphics_metal", GRAPHICS_METAL_MARKERS),
        "framebuffer": _occurrences(raw, "graphics_framebuffer", GRAPHICS_FRAMEBUFFER_MARKERS),
    }
    ws = bool(groups["windowserver"])
    accel = bool(groups["accelerator"])
    metal = bool(groups["metal"])
    framebuffer = bool(groups["framebuffer"])
    verified = ws and accel and metal
    if verified and framebuffer:
        blocker = None
    elif not ws:
        blocker = "No WindowServer marker was observed"
    elif not accel:
        blocker = "WindowServer observed, but no GPU accelerator provider marker"
    elif not metal:
        blocker = "GPU provider observed, but no Metal device marker"
    else:
        blocker = "Metal provider observed, but no presented accelerated framebuffer marker"
    return {
        "windowserver_reached": ws,
        "metal_accelerator_verified": verified,
        "metal_device_verified": metal,
        "framebuffer_presented": framebuffer,
        "graphics_acceleration_verified": verified,
        "rendered_frame_verified": verified and framebuffer,
        "observed_markers": {k: [item.as_dict() for item in v] for k, v in groups.items()},
        "blocker": blocker,
        "evidence_policy": "WindowServer + accelerator provider + Metal device; presented frame is separate",
    }


__all__ = [
    "IBOOT_STAGE1_MARKERS",
    "IBOOT_STAGE2_MARKERS",
    "INSTALLER_MARKERS",
    "USERSPACE_MARKERS",
    "XNU_MARKERS",
    "GRAPHICS_ACCELERATOR_MARKERS",
    "GRAPHICS_FRAMEBUFFER_MARKERS",
    "GRAPHICS_METAL_MARKERS",
    "GRAPHICS_WINDOWSERVER_MARKERS",
    "MarkerEvidence",
    "parse_graphics_evidence",
    "parse_uart_evidence",
]
