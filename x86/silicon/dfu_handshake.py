"""
dfu_handshake.py: pure state machine modeling a DFU-like recovery USB handshake — SIMULATED.

The 05ac:1227-style vendor:product identifier is cited only for label realism in the
simulated trace (it is the publicly known shape of Apple recovery-mode USB devices).
This module never opens a real USB device, never imports ``usb``/``libusb``/``pyusb``,
and never spawns a subprocess — every transition below is computed in memory.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Optional


class DfuState(str, enum.Enum):
    DETACHED = "detached"
    IBSS_ENUMERATED = "ibss_enumerated"
    RESET_PENDING = "reset_pending"
    IBSS_REENUMERATED = "ibss_reenumerated"
    BULK_OUT_READY = "bulk_out_ready"
    IBEC_HANDOFF_GATE = "ibec_handoff_gate"
    COMPLETE = "complete"
    FAILED = "failed"


_ORDER: tuple[DfuState, ...] = (
    DfuState.DETACHED,
    DfuState.IBSS_ENUMERATED,
    DfuState.RESET_PENDING,
    DfuState.IBSS_REENUMERATED,
    DfuState.BULK_OUT_READY,
    DfuState.IBEC_HANDOFF_GATE,
    DfuState.COMPLETE,
)

_EVENT_LABELS: dict[DfuState, str] = {
    DfuState.IBSS_ENUMERATED: "USB re-enumerates as a 05ac:1227-style iBSS DFU device (simulated identifier, no real USB I/O)",
    DfuState.RESET_PENDING: "Host issues a USB reset to hand off from iBSS to iBEC",
    DfuState.IBSS_REENUMERATED: "Device re-enumerates as 05ac:1227 after reset",
    DfuState.BULK_OUT_READY: "Bulk-OUT endpoint 4 is advertised and ready for the iBEC image",
    DfuState.IBEC_HANDOFF_GATE: "iBSS -> iBEC handoff gate reached",
    DfuState.COMPLETE: "Simulated DFU handshake reaches its terminal, pre-kernel state",
}


@dataclass(frozen=True)
class DfuTransition:
    event: str
    from_state: DfuState
    to_state: DfuState
    detail: str = ""


@dataclass(frozen=True)
class DfuTrace:
    transitions: tuple[DfuTransition, ...]
    final_state: DfuState
    ok: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "final_state": self.final_state.value,
            "ok": self.ok,
            "transitions": [
                {
                    "event": transition.event,
                    "from": transition.from_state.value,
                    "to": transition.to_state.value,
                    "detail": transition.detail,
                }
                for transition in self.transitions
            ],
        }


def run_dfu_handshake(*, inject_failure_at: Optional[DfuState] = None) -> DfuTrace:
    """Walk the simulated DFU state machine. If ``inject_failure_at`` matches the
    current state before a transition, the trace ends in ``FAILED`` instead —
    this is how the mock fixtures prove the model represents failure, not only
    the happy path."""
    transitions: list[DfuTransition] = []
    current = DfuState.DETACHED
    for next_state in _ORDER[1:]:
        if inject_failure_at is not None and current == inject_failure_at:
            transitions.append(
                DfuTransition(
                    event=f"fault-injected failure before reaching {next_state.value}",
                    from_state=current,
                    to_state=DfuState.FAILED,
                    detail="Simulated fixture requested a failure at this stage.",
                )
            )
            return DfuTrace(transitions=tuple(transitions), final_state=DfuState.FAILED, ok=False)
        transitions.append(
            DfuTransition(event=_EVENT_LABELS.get(next_state, next_state.value), from_state=current, to_state=next_state)
        )
        current = next_state
    return DfuTrace(transitions=tuple(transitions), final_state=current, ok=current == DfuState.COMPLETE)
