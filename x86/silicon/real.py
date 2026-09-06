"""Explicit real VMApple direct-boot adapter for the Apple Silicon layer.

The existing :mod:`x86.silicon.session` module is intentionally a deterministic
simulation.  This module is the opposite boundary: it is imported only by the
explicit ``python -m x86.silicon direct`` command and delegates to the real
VMApple runner.  It never edits the AVPBooter, AUX, or root inputs; the runner
creates copy-on-write overlays and records UART evidence.
"""

from __future__ import annotations

from typing import Any


def run_direct_macos(
    *,
    target_os: int,
    qemu: str | None,
    qemu_img: str | None,
    firmware: str,
    aux: str,
    root: str,
    output: str | None,
    vm_json: str | None = None,
    display: str = "auto",
    uuid: int = 0,
    aux_offset: int = 0,
    memory_mib: int = 4096,
    smp: int = 2,
    timeout: float = 300.0,
    duration: float | None = None,
    research_only: bool = False,
) -> dict[str, Any]:
    """Run the normal macOS entry with no DFU/personalization stage.

    This function is deliberately small so the ownership boundary stays clear:
    VMApple owns process/storage orchestration, while this adapter only selects
    the ARM-only direct boot contract.
    """
    from x86.vmapple import VMappleConfig, run

    report = run(
        VMappleConfig(
            target_major=target_os,
            qemu=qemu,
            qemu_img=qemu_img,
            firmware=firmware,
            ibss="",
            aux=aux,
            root=root,
            output=output,
            vm_json=vm_json,
            display=display,
            uuid=uuid,
            aux_offset=aux_offset,
            memory_mib=memory_mib,
            smp=smp,
            transition_timeout=timeout,
            duration=duration,
            research_only=research_only,
            live_personalize=False,
            restore_chain=False,
            boot_selection="macos",
            boot_picker_trigger="direct-command",
        )
    )
    report.setdefault("layer", "Apple Silicon user-space VMApple runner -> AVPBooter -> XNU/userspace UART")
    return report
