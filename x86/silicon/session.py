"""
session.py: orchestrates one simulated Apple Silicon install session — never a real one.

Combines ``boot_chain.simulate_boot_chain()`` and ``dfu_handshake.run_dfu_handshake()``
into a single narrative trace for a target OS (macOS 27 "Golden Gate" by default).
``InstallSessionResult.simulated``/``real_boot_verified``/``xnu_executed`` are computed
properties, not constructor fields, so no caller can build a result that claims a real
boot happened.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from opencore_legacy_patcher.datasets.os_data import os_conversion, os_data

from .boot_chain import BootChainResult, assert_never_claims_real_boot, simulate_boot_chain
from .dfu_handshake import DfuState, DfuTrace, run_dfu_handshake


@dataclass(frozen=True)
class InstallSessionResult:
    target_os: int
    target_os_name: str
    host_label: str
    dfu_trace: DfuTrace
    boot_chain: BootChainResult
    ok: bool
    notes: tuple[str, ...] = ()

    @property
    def simulated(self) -> bool:
        return True

    @property
    def real_boot_verified(self) -> bool:
        return False

    @property
    def xnu_executed(self) -> bool:
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_os": self.target_os,
            "target_os_name": self.target_os_name,
            "host_label": self.host_label,
            "ok": self.ok,
            "simulated": self.simulated,
            "real_boot_verified": self.real_boot_verified,
            "xnu_executed": self.xnu_executed,
            "dfu_trace": self.dfu_trace.as_dict(),
            "boot_chain": self.boot_chain.as_dict(),
            "notes": list(self.notes),
        }


def run_install_session(
    *,
    target_os: Optional[int] = None,
    inject_dfu_failure_at: Optional[DfuState] = None,
    host_label: str = "Apple Silicon sandbox (simulated)",
) -> InstallSessionResult:
    kernel = int(target_os) if target_os is not None else int(os_data.golden_gate)
    boot_chain_result = simulate_boot_chain(target_os=kernel)
    assert_never_claims_real_boot(boot_chain_result)
    dfu_trace = run_dfu_handshake(inject_failure_at=inject_dfu_failure_at)

    xnu_stage = next(stage for stage in boot_chain_result.stages if stage.id == "xnu_boot")
    ok = boot_chain_result.blocked_at == "macos_guest_abi_boundary" and xnu_stage.status.value == "skipped"

    return InstallSessionResult(
        target_os=kernel,
        target_os_name=os_conversion.convert_kernel_to_marketing_name(kernel),
        host_label=host_label,
        dfu_trace=dfu_trace,
        boot_chain=boot_chain_result,
        ok=ok,
        notes=(
            "This is a simulation of publicly documented boot-chain concepts, not a real boot.",
            "No QEMU, hypervisor, or USB/DFU hardware was touched to produce this trace.",
        ),
    )
