"""
Mock Apple Silicon host harness — SIMULATED, no real device or hypervisor required.

Mirrors x86.extreme.mock_guest's shape: a static fixture table plus an evaluator that
lazily imports the real (here: simulation) logic under test, so this module stays
import-cheap and decoupled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from opencore_legacy_patcher.datasets.os_data import os_data

from .dfu_handshake import DfuState


@dataclass(frozen=True)
class MockAppleSiliconHost:
    """One synthetic Apple Silicon sandbox host identity for the simulation gates."""

    host_id: str
    label: str
    target_os_kernel: int = int(os_data.golden_gate)
    inject_dfu_failure_at: Optional[DfuState] = None
    notes: tuple[str, ...] = ()


HOSTS: tuple[MockAppleSiliconHost, ...] = (
    MockAppleSiliconHost(
        host_id="golden-gate-nominal",
        label="Apple Silicon sandbox · macOS 27 Golden Gate · nominal trace",
        notes=("happy-path simulated trace; still never claims a real boot",),
    ),
    MockAppleSiliconHost(
        host_id="golden-gate-dfu-fault-injected",
        label="Apple Silicon sandbox · macOS 27 Golden Gate · DFU fault injected",
        inject_dfu_failure_at=DfuState.BULK_OUT_READY,
        notes=("proves the state machine represents failure, not only success",),
    ),
)


@dataclass
class HostEval:
    host_id: str
    ok: bool
    blocked_at: Optional[str]
    dfu_ok: bool
    detail: dict[str, Any]


def evaluate_host(host: MockAppleSiliconHost) -> HostEval:
    from .session import run_install_session

    result = run_install_session(
        target_os=host.target_os_kernel,
        inject_dfu_failure_at=host.inject_dfu_failure_at,
        host_label=host.label,
    )
    expect_dfu_ok = host.inject_dfu_failure_at is None
    ok = result.ok and result.dfu_trace.ok == expect_dfu_ok
    return HostEval(
        host_id=host.host_id,
        ok=ok,
        blocked_at=result.boot_chain.blocked_at,
        dfu_ok=result.dfu_trace.ok,
        detail=result.as_dict(),
    )


def run_mock_host_matrix() -> dict[str, Any]:
    results = [evaluate_host(host) for host in HOSTS]
    return {
        "hosts": len(results),
        "ok": all(result.ok for result in results),
        "results": [
            {
                "host_id": result.host_id,
                "ok": result.ok,
                "blocked_at": result.blocked_at,
                "dfu_ok": result.dfu_ok,
            }
            for result in results
        ],
    }


def main(argv: Optional[list[str]] = None) -> int:
    import json

    del argv
    payload = run_mock_host_matrix()
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
