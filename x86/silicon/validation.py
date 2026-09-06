"""
Apple Silicon sandbox simulation gate/validation orchestration (mock-only).

Entry: ``python -m x86.silicon.validation`` or ``--gates-only``.
Never touches real hardware, USB, or a hypervisor — see x86/silicon/__init__.py.

This module defines its own ``StepResult`` — a distinct, unrelated class from
``x86.extreme.validation.StepResult`` (same shape, different track: this package is
Apple-Silicon-sandbox simulation, not the unrelated x86-hardware/Tahoe-Vega64 track).
"""

from __future__ import annotations

import json
import platform
import sys
import unittest
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

UNITTEST_MODULES: tuple[str, ...] = (
    "x86.silicon.test_boot_chain",
    "x86.silicon.test_dfu_handshake",
    "x86.silicon.test_mock_host",
    "x86.silicon.test_session",
)


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def _which(name: str) -> Optional[str]:
    from shutil import which

    return which(name)


def _host_snapshot() -> dict[str, Any]:
    return {
        "platform": sys.platform,
        "machine": platform.machine(),
        "has_qemu_t8030": bool(_which("qemu-t8030") or _which("qemu-system-aarch64")),
    }


def step_boot_chain_never_claims_real_boot() -> StepResult:
    from opencore_legacy_patcher.datasets.os_data import os_data

    from .boot_chain import assert_never_claims_real_boot, simulate_boot_chain

    result = simulate_boot_chain(target_os=int(os_data.golden_gate))
    try:
        assert_never_claims_real_boot(result)
        guard_ok = True
    except RuntimeError:
        guard_ok = False
    return StepResult(
        name="boot_chain_never_claims_real_boot",
        ok=guard_ok and result.blocked_at == "macos_guest_abi_boundary",
        detail=result.as_dict(),
    )


def step_dfu_handshake_default_trace() -> StepResult:
    from .dfu_handshake import run_dfu_handshake

    trace = run_dfu_handshake()
    return StepResult(name="dfu_handshake_default_trace", ok=trace.ok, detail=trace.as_dict())


def step_mock_host_matrix() -> StepResult:
    from .mock_host import run_mock_host_matrix

    payload = run_mock_host_matrix()
    return StepResult(
        name="mock_host_matrix",
        ok=bool(payload.get("ok")),
        detail={"hosts": payload.get("hosts"), "results": payload.get("results")},
    )


def step_install_session_labels() -> StepResult:
    from .session import run_install_session

    result = run_install_session()
    ok = result.simulated is True and result.real_boot_verified is False and result.xnu_executed is False
    return StepResult(name="install_session_labels", ok=ok, detail=result.as_dict())


def run_gates() -> list[StepResult]:
    steps = (
        step_boot_chain_never_claims_real_boot,
        step_dfu_handshake_default_trace,
        step_mock_host_matrix,
        step_install_session_labels,
    )
    results: list[StepResult] = []
    for fn in steps:
        try:
            results.append(fn())
        except Exception as exc:  # noqa: BLE001
            results.append(StepResult(name=fn.__name__, ok=False, error=str(exc)))
    return results


def run_unit_suite(verbosity: int = 1) -> unittest.TestResult:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod in UNITTEST_MODULES:
        try:
            suite.addTests(loader.loadTestsFromName(mod))
        except Exception as exc:  # noqa: BLE001
            print(f"SKIP load {mod}: {exc}", file=sys.stderr)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def run_all(*, run_unittests: bool = True, verbosity: int = 1) -> dict[str, Any]:
    host = _host_snapshot()
    gates = run_gates()
    unit: dict[str, Any] = {"skipped": True}
    if run_unittests:
        result = run_unit_suite(verbosity=verbosity)
        unit = {
            "skipped": False,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "ok": result.wasSuccessful(),
        }
    payload = {
        "host": host,
        "gates": [asdict(g) for g in gates],
        "gates_ok": all(g.ok for g in gates),
        "unit": unit,
        "note": (
            "Pure simulation. No QEMU/hypervisor is ever spawned by this package, "
            "regardless of what is installed on this host."
        ),
    }
    payload["ok"] = payload["gates_ok"] and (unit.get("ok", True) if not unit.get("skipped") else True)
    return payload


def main(argv: Optional[list[str]] = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    skip_unit = "--gates-only" in args
    quiet = "--quiet" in args
    payload = run_all(run_unittests=not skip_unit, verbosity=0 if quiet else 1)
    print(json.dumps(payload, indent=2, default=str))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
