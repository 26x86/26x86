"""
x86.silicon — Apple Silicon boot-chain simulation plus an explicit VMApple direct
macOS adapter.

The default ``session``/``hosts`` commands remain deterministic simulations and
never claim a real boot.  The separate ``direct`` command delegates to the real
VMApple runner when the caller supplies an Apple Silicon/macOS HVF environment and
unchanged AVPBooter/AUX/root inputs, or selects the native ``macosvm``/
Virtualization.framework engine with an immutable ``macosvm.json`` bundle.

Two facts constrain everything in this package:

1. There is no publicly known way to boot real macOS to completion outside genuine
   Apple Silicon Mac hardware plus Apple's own Virtualization.framework. qemu-t8030
   (cited as an architectural reference) emulates the T8030/A12 SoC used in
   iPhones/iPads for iOS — macOS has never run on that silicon. QEMU's real
   ``vmapple`` machine type emulates the ABI Apple's Virtualization.framework exposes
   to a *Linux* guest, not a way to boot macOS as a QEMU guest.
2. ``x86.execution``'s ``apple-silicon-sandbox`` mode retains its strict, tested
   simulation contract.  The explicit ``x86.silicon direct`` command is not wired
   into that default mode; it is a separately audited user-space VMApple entry.

Given both constraints, the default simulation modules are pure Python,
deterministic, and zero-I/O: data models of the Apple Silicon boot chain
(``boot_chain``) and a DFU-like recovery handshake (``dfu_handshake``), composed
by ``session.run_install_session()`` into a stage-by-stage trace that is
structurally prevented from claiming a real boot
(``InstallSessionResult.simulated`` is always ``True``; ``real_boot_verified`` and
``xnu_executed`` are always ``False`` — computed properties, not settable fields).

qemu-t8030's publicly documented architecture (SecureROM/LLB/iBoot stage concepts,
DFU USB handshake shape) informs the *naming and shape* of the simulated stages in
``boot_chain.py`` and ``dfu_handshake.py``; no code from that project is used here.

Entry points:
    python -m x86.silicon session [--host ID] [--json]
    python -m x86.silicon hosts [--json]
    python -m x86.silicon direct --firmware ... --aux ... --root ... --research-only
    python -m x86.silicon direct --engine native-macosvm --macosvm ... --vm-json ... --research-only
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
