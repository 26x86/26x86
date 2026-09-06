"""
x86.silicon — Apple Silicon boot-chain / DFU handshake SIMULATION, never a real boot.

This package exists to answer one request honestly: "show a Golden Gate (macOS 27)
install progressing" from inside apple-silicon-sandbox mode, without pretending that
is achievable. It is not.

Two facts constrain everything in this package:

1. There is no publicly known way to boot real macOS to completion outside genuine
   Apple Silicon Mac hardware plus Apple's own Virtualization.framework. qemu-t8030
   (cited as an architectural reference) emulates the T8030/A12 SoC used in
   iPhones/iPads for iOS — macOS has never run on that silicon. QEMU's real
   ``vmapple`` machine type emulates the ABI Apple's Virtualization.framework exposes
   to a *Linux* guest, not a way to boot macOS as a QEMU guest.
2. ``x86.execution``'s ``apple-silicon-sandbox`` mode has a strict, tested contract:
   it never loads a kext, patches a volume, starts a VM, or reads settings from disk.
   This package must stay additive to that contract, never wired into
   ``resolve_execution()``, and must never spawn a real subprocess/hypervisor.

Given both constraints, every module here is pure Python, deterministic, and zero-I/O:
data models of the Apple Silicon boot chain (``boot_chain``) and a DFU-like recovery
handshake (``dfu_handshake``), composed by ``session.run_install_session()`` into a
stage-by-stage trace that is structurally prevented from claiming a real boot
(``InstallSessionResult.simulated`` is always ``True``; ``real_boot_verified`` and
``xnu_executed`` are always ``False`` — computed properties, not settable fields).

qemu-t8030's publicly documented architecture (SecureROM/LLB/iBoot stage concepts,
DFU USB handshake shape) informs the *naming and shape* of the simulated stages in
``boot_chain.py`` and ``dfu_handshake.py``; no code from that project is used here.

Entry points:
    python -m x86.silicon session [--host ID] [--json]
    python -m x86.silicon hosts [--json]
    python -m x86.silicon.validation [--gates-only] [--quiet]
"""

from __future__ import annotations

from .boot_chain import BOOT_CHAIN, BootChainResult, BootStage, StageStatus, simulate_boot_chain
from .dfu_handshake import DfuState, DfuTrace, DfuTransition, run_dfu_handshake
from .mock_host import HOSTS, MockAppleSiliconHost, run_mock_host_matrix
from .session import InstallSessionResult, run_install_session

__all__ = [
    "BOOT_CHAIN",
    "BootChainResult",
    "BootStage",
    "StageStatus",
    "simulate_boot_chain",
    "DfuState",
    "DfuTrace",
    "DfuTransition",
    "run_dfu_handshake",
    "HOSTS",
    "MockAppleSiliconHost",
    "run_mock_host_matrix",
    "InstallSessionResult",
    "run_install_session",
]
