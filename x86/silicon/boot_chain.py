"""
boot_chain.py: data-only model of the Apple Silicon boot chain — SIMULATED.

Stage naming/shape is informed by qemu-t8030's publicly documented Apple Silicon
boot-chain architecture (SecureROM -> LLB -> iBoot stages -> kernel handoff); no code
from that project is used here, and T8030/A12 (iPhone/iPad silicon) has never run
macOS regardless. This module never touches USB, serial, a subprocess, or a real
bootloader — ``BOOT_CHAIN`` is a static tuple, and ``simulate_boot_chain()`` only
ever returns it.

The last two stages are structurally forbidden from ever reporting ``PASS``:
``macos_guest_abi_boundary`` (the real, currently-unsolved point where a genuine
macOS-as-QEMU-guest handoff would need to exist) is always ``BLOCKED``, and
``xnu_boot`` (actual kernel execution) is always ``SKIPPED``. ``assert_never_claims_real_boot``
enforces this as code, not just as a docstring promise.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Optional


class StageStatus(str, enum.Enum):
    PASS = "pass"        # simulated pass of a well-documented, pre-kernel boot-chain concept
    BLOCKED = "blocked"  # simulated hard stop — no publicly known way past this point
    SKIPPED = "skipped"  # never attempted, by design


@dataclass(frozen=True)
class BootStage:
    id: str
    title: str
    purpose: str
    status: StageStatus
    detail: str = ""


BOOT_CHAIN: tuple[BootStage, ...] = (
    BootStage(
        id="secure_rom",
        title="SecureROM",
        purpose="Boot ROM root of trust; first code to execute after power-on.",
        status=StageStatus.PASS,
    ),
    BootStage(
        id="llb",
        title="LLB (Low-Level Bootloader)",
        purpose="Loads and verifies the next-stage iBoot image.",
        status=StageStatus.PASS,
    ),
    BootStage(
        id="iboot_stage1",
        title="iBoot stage 1 (iBSS-equivalent)",
        purpose="Minimal recovery-mode bootloader used during DFU/recovery restore.",
        status=StageStatus.PASS,
    ),
    BootStage(
        id="iboot_stage2",
        title="iBoot stage 2 (iBEC-equivalent)",
        purpose="Full bootloader stage; prepares the device tree and hands off to the kernel loader.",
        status=StageStatus.PASS,
    ),
    BootStage(
        id="device_tree_handoff",
        title="Device tree / boot-args handoff",
        purpose="Publishes the device tree and boot-args the kernel would read at startup.",
        status=StageStatus.PASS,
    ),
    BootStage(
        id="macos_guest_abi_boundary",
        title="macOS guest / Virtualization.framework ABI handoff",
        purpose=(
            "The boundary where a real macOS guest would hand off into Apple's own "
            "Virtualization.framework-provided guest ABI."
        ),
        status=StageStatus.BLOCKED,
        detail=(
            "No publicly available tooling implements this boundary outside genuine "
            "Apple Silicon Mac hardware running Apple's own hypervisor. This simulation "
            "stops here rather than inventing a fake success."
        ),
    ),
    BootStage(
        id="xnu_boot",
        title="XNU kernel execution",
        purpose="Kernel startup and user-space handoff (login window, etc.).",
        status=StageStatus.SKIPPED,
        detail="Never attempted by this simulation.",
    ),
)

_REAL_BOOT_STAGE_IDS = frozenset({"macos_guest_abi_boundary", "xnu_boot"})


@dataclass(frozen=True)
class BootChainResult:
    stages: tuple[BootStage, ...]
    blocked_at: Optional[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "blocked_at": self.blocked_at,
            "stages": [
                {
                    "id": stage.id,
                    "title": stage.title,
                    "purpose": stage.purpose,
                    "status": stage.status.value,
                    "detail": stage.detail,
                }
                for stage in self.stages
            ],
        }


def simulate_boot_chain(*, target_os: int) -> BootChainResult:
    """Return the static, simulated boot-chain trace. ``target_os`` is currently
    only carried through for labeling by callers — the stage list and stopping
    point do not vary by target OS, since the blocking boundary is a tooling/
    hardware limit, not an OS-version limit."""
    del target_os
    blocked_at = next((stage.id for stage in BOOT_CHAIN if stage.status is StageStatus.BLOCKED), None)
    return BootChainResult(stages=BOOT_CHAIN, blocked_at=blocked_at)


def assert_never_claims_real_boot(result: BootChainResult) -> None:
    """Structural guard: raise if any real-boot-labeled stage is ever reported PASS."""
    for stage in result.stages:
        if stage.id in _REAL_BOOT_STAGE_IDS and stage.status is StageStatus.PASS:
            raise RuntimeError(
                f"Refusing to report {stage.id!r} as PASS — no simulation in this "
                "package may claim a real macOS boot or a real Virtualization.framework handoff."
            )
