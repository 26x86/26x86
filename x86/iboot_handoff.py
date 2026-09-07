"""Evidence-gated iBoot -> XNU handoff contract.

This module is deliberately below the GUI and above the transport details: it
consumes a completed VMApple report and checks whether the report contains a
causal boot-chain trace.  It does not execute iBoot, verify IMG4 signatures, or
turn a transport acknowledgement into a macOS boot claim.

The distinction matters for the Apple boot-chain layer.  A real recovery run
can reach an iBSS endpoint, upload iBEC, enter Stage2, send restore roles, and
receive a ``bootx`` acknowledgement while iBoot still panics before XNU.  Each
of those is useful evidence, but none is interchangeable with the next stage.
The verifier therefore derives the stage result from observed evidence and
rejects contradictory positive claims in caller-supplied reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


SCHEMA = "26x86.iboot-xnu-handoff/1"
IBOOT_MACHINE_TYPE = "iBoot(AArch64)"
SUPPORTED_TARGET_MAJORS = frozenset({26, 27})


class HandoffContractError(ValueError):
    """The supplied report is malformed or makes an impossible claim."""


class StageStatus(str, Enum):
    VERIFIED = "verified"
    BLOCKED = "blocked"
    NOT_OBSERVED = "not-observed"


@dataclass(frozen=True)
class HandoffStage:
    """One causally ordered boot-chain stage and its supporting observation."""

    stage_id: str
    status: StageStatus
    evidence: tuple[str, ...] = ()
    blocker: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.stage_id,
            "status": self.status.value,
            "evidence": list(self.evidence),
        }
        if self.blocker is not None:
            payload["blocker"] = self.blocker
        return payload


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _bool(value: object) -> bool:
    # bool(1) is intentionally not accepted.  Reports are JSON contracts and
    # a numeric value must not silently become security/boot evidence.
    return value is True


def _path(root: Mapping[str, Any], *names: str) -> object:
    value: object = root
    for name in names:
        if not isinstance(value, Mapping):
            return None
        value = value.get(name)
    return value


def _marker_present(observation: Mapping[str, Any], category: str, names: tuple[str, ...]) -> bool:
    markers = observation.get("observed_markers")
    if not isinstance(markers, Mapping):
        return False
    entries = markers.get(category)
    if not isinstance(entries, list):
        return False
    accepted = set(names)
    for entry in entries:
        if isinstance(entry, Mapping) and isinstance(entry.get("marker"), str):
            if (
                entry["marker"] in accepted
                and isinstance(entry.get("byte_offset"), int)
                and not isinstance(entry.get("byte_offset"), bool)
                and entry["byte_offset"] >= 0
            ):
                return True
    return False


def _first_marker_offset(observation: Mapping[str, Any], category: str, names: tuple[str, ...]) -> int | None:
    """Return the first absolute offset for a marker category, if present."""
    markers = observation.get("observed_markers")
    if not isinstance(markers, Mapping):
        return None
    entries = markers.get(category)
    if not isinstance(entries, list):
        return None
    accepted = set(names)
    offsets = [
        entry.get("byte_offset")
        for entry in entries
        if isinstance(entry, Mapping)
        and entry.get("marker") in accepted
        and isinstance(entry.get("byte_offset"), int)
        and not isinstance(entry.get("byte_offset"), bool)
        and entry["byte_offset"] >= 0
    ]
    return min(offsets) if offsets else None


def _observation(report: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = _mapping(report.get("direct_boot"))
    observation = _mapping(direct.get("observation"))
    # Recovery reports can expose a future direct observation at the top level;
    # accepting this alias keeps the contract forward-compatible but never
    # accepts a bare boolean without marker evidence below.
    if not observation:
        observation = _mapping(report.get("observation"))
    if not observation and isinstance(report.get("observed_markers"), Mapping):
        # The live USB/Stage2 runner stores its UART observation at the report
        # root.  Reuse that durable shape without manufacturing any missing
        # marker or execution field.
        observation = report
    return observation


def _input_integrity(report: Mapping[str, Any]) -> bool:
    value = report.get("input_integrity")
    if _bool(value):
        return True
    if isinstance(value, Mapping):
        return _bool(value.get("valid"))
    return False


def _target_major(report: Mapping[str, Any]) -> int | None:
    value = report.get("target_major")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _stage(
    stage_id: str,
    passed: bool,
    *,
    evidence: tuple[str, ...] = (),
    blocker: str,
) -> HandoffStage:
    return HandoffStage(
        stage_id=stage_id,
        status=StageStatus.VERIFIED if passed else StageStatus.BLOCKED,
        evidence=evidence if passed else (),
        blocker=None if passed else blocker,
    )


def _not_observed(stage_id: str, *, evidence: tuple[str, ...] = ()) -> HandoffStage:
    """Represent an optional path that was not selected, not a successful stage."""
    return HandoffStage(stage_id=stage_id, status=StageStatus.NOT_OBSERVED, evidence=evidence)


def verify_handoff_report(
    report: Mapping[str, Any],
    *,
    expected_target_major: int | None = None,
    require_recovery_chain: bool = False,
) -> dict[str, Any]:
    """Verify a VMApple/iBoot report without starting a process or opening files.

    The result is ``valid=True`` when the report is internally consistent.  It
    is still perfectly valid for a report to be blocked before XNU; in that
    case ``macos_boot_verified`` is false and ``blockers`` explains the first
    missing causal stage.  ``HandoffContractError`` is reserved for malformed
    scope or an explicit impossible positive claim.
    """

    if not isinstance(report, Mapping):
        raise HandoffContractError("iBoot handoff report must be a JSON object")

    machine_type = report.get("machine_type")
    guest_os = report.get("guest_os")
    if machine_type not in (None, IBOOT_MACHINE_TYPE):
        raise HandoffContractError(f"unsupported machine_type for iBoot handoff: {machine_type!r}")
    if guest_os not in (None, "macOS"):
        raise HandoffContractError(f"unsupported guest_os for iBoot handoff: {guest_os!r}")

    target_major = _target_major(report)
    if expected_target_major is not None:
        if expected_target_major not in SUPPORTED_TARGET_MAJORS:
            raise HandoffContractError("expected target major must be macOS 26 or 27")
        if target_major is not None and target_major != expected_target_major:
            raise HandoffContractError(
                f"report target major {target_major} does not match expected {expected_target_major}"
            )
        target_major = expected_target_major
    if target_major is not None and target_major not in SUPPORTED_TARGET_MAJORS:
        raise HandoffContractError("iBoot handoff target must be macOS 26 or 27")

    observation = _observation(report)
    xnu_marker = _marker_present(observation, "xnu", ("Darwin Kernel Version", "Darwin Kernel"))
    userspace_marker = _marker_present(
        observation, "userspace", ("launchd:", "launchd ", "loginwindow", "WindowServer")
    )
    xnu_offset = _first_marker_offset(
        observation, "xnu", ("Darwin Kernel Version", "Darwin Kernel")
    )
    userspace_offset = _first_marker_offset(
        observation, "userspace", ("launchd:", "launchd ", "loginwindow", "WindowServer")
    )
    xnu_to_userspace = (
        xnu_offset is not None
        and userspace_offset is not None
        and xnu_offset <= userspace_offset
    )

    # Direct mode is intentionally distinct from DFU recovery.  A direct
    # AVPBooter launch can be a real attempt at the normal macOS entry without
    # passing through the user-space DFU uploader in this process.
    direct = _mapping(report.get("direct_boot"))
    direct_mode = direct.get("requested") is True and direct.get("selection") == "macos"
    recovery = not direct_mode
    transition = _mapping(report.get("transition"))
    dfu = _mapping(report.get("dfu_upload"))
    # Recovery reports from the live GUI/USB runner keep the protocol
    # observations under ``recovery``.  Accept that durable shape as an
    # alias, but never fill in an absent observation from a claim alone.
    recovery_report = _mapping(report.get("recovery"))
    stage2 = _mapping(report.get("stage2"))
    restore = _mapping(report.get("restore_chain"))

    stages: list[HandoffStage] = []
    if direct_mode:
        stages.append(_stage(
            "avpbooter-direct-entry",
            _bool(direct.get("requested")) and direct.get("dfu_entered") is False,
            evidence=("direct_boot.requested", "direct_boot.dfu_entered=false"),
            blocker="direct macOS entry was not explicitly selected without DFU",
        ))
    else:
        recovery_inputs_required = (
            _bool(report.get("recovery_inputs_required"))
            or _bool(recovery_report.get("recovery_inputs_required"))
            or _bool(recovery_report.get("dfu_transfer_complete"))
        )
        dfu_complete = (
            _bool(dfu.get("transfer_complete"))
            or _bool(recovery_report.get("dfu_transfer_complete"))
        )
        transition_state = transition.get("state")
        if not isinstance(transition_state, str):
            transition_state = recovery_report.get("transition_state")
        ibec_ready = transition_state == "ibec-ready"
        stages.append(_stage(
            "ibss-dfu",
            recovery_inputs_required and (ibec_ready or dfu_complete),
            evidence=("dfu_upload.transfer_complete", "transition.state=ibec-ready"),
            blocker="iBSS DFU completion and an iBEC-ready transition were not both observed",
        ))
        ibec_executed = _bool(report.get("ibec_executed")) or _bool(stage2.get("ibec_executed"))
        stage2_observed = (
            _bool(report.get("stage2_execution_observed"))
            or _bool(stage2.get("observed"))
            or _bool(stage2.get("execution_observed"))
        )
        stages.append(_stage(
            "ibec-stage2",
            ibec_executed and stage2_observed,
            evidence=("ibec_executed", "stage2_execution_observed", "stage2.observed"),
            blocker="iBEC execution and the Stage2 UART marker were not both observed",
        ))
        restore_complete = _bool(report.get("restore_chain_completed")) or (
            _bool(restore.get("sequence_sent"))
            and _bool(restore.get("bootx_acknowledged"))
            and _bool(restore.get("input_integrity"))
        )
        if not restore and not require_recovery_chain:
            stages.append(_not_observed("restore-roles-bootx"))
        else:
            stages.append(_stage(
                "restore-roles-bootx",
                restore_complete,
                evidence=("restore_chain.sequence_sent", "restore_chain.bootx_acknowledged", "restore_chain.input_integrity"),
                blocker="official restore-role sequence did not reach an integrity-checked bootx acknowledgement",
            ))

    # Marker evidence is mandatory even if a caller tries to set xnu_executed
    # or macos_boot_verified directly.  This is the key anti-claim boundary.
    xnu_claim = _bool(report.get("xnu_executed")) or _bool(observation.get("xnu_executed"))
    userspace_claim = _bool(observation.get("macos_userspace_reached"))
    xnu_ok = xnu_claim and xnu_marker
    userspace_ok = userspace_claim and userspace_marker and xnu_to_userspace
    kernel_major = observation.get("guest_kernel_major")
    target_match = observation.get("guest_target_match")
    if target_major is not None:
        target_match_ok = target_match is True and kernel_major == target_major
    else:
        target_match_ok = target_match is True

    stages.append(_stage(
        "xnu-entry",
        xnu_ok and target_match_ok,
        evidence=("xnu_executed", "observed_markers.xnu", "guest_target_match"),
        blocker="Darwin/XNU marker, target-major match, and xnu_executed evidence are required",
    ))
    stages.append(_stage(
        "macos-userspace",
        xnu_ok and userspace_ok and target_match_ok,
        evidence=("observed_markers.userspace", "macos_userspace_reached", "marker_offsets_ordered"),
        blocker="XNU must be evidenced before a launchd/loginwindow/WindowServer marker can count",
    ))

    signature_claim = _bool(report.get("signature_acceptance_verified"))
    personalization = _mapping(report.get("personalization"))
    signature_evidence = _mapping(report.get("signature_acceptance_evidence"))
    # Ticket issuance and payload preservation are preparation evidence, not
    # guest acceptance.  A positive signature claim needs an explicit guest
    # acknowledgement with a method and source in the report.
    signature_ok = signature_claim and _bool(signature_evidence.get("accepted_by_guest")) \
        and isinstance(signature_evidence.get("method"), str) \
        and isinstance(signature_evidence.get("source"), str)
    if signature_claim and not signature_ok:
        raise HandoffContractError(
            "signature_acceptance_verified=true requires guest acceptance evidence; "
            "TSS ticket/payload fields alone are insufficient"
        )

    input_ok = _input_integrity(report)
    boot_claim = _bool(report.get("macos_boot_verified"))
    runtime_started = any(
        _bool(report.get(key))
        for key in ("runtime_started", "native_runtime_started", "tcg_runtime_started")
    )
    boot_verified = (
        xnu_ok and userspace_ok and target_match_ok and input_ok and runtime_started
        and all(stage.status is StageStatus.VERIFIED for stage in stages)
    )
    if boot_claim and not boot_verified:
        raise HandoffContractError(
            "macos_boot_verified=true is inconsistent with the causal iBoot/XNU evidence chain"
        )

    blockers = [stage.blocker for stage in stages if stage.blocker]
    if not input_ok:
        blockers.append("input_integrity=true is required for a boot claim")
    if not runtime_started:
        blockers.append("a started native/TCG guest runtime is required for a boot claim")
    if not signature_ok:
        blockers.append("Apple signature acceptance remains unverified; transport/TSS evidence is not guest acceptance")
    return {
        "schema": SCHEMA,
        "valid": True,
        "machine_type": machine_type or IBOOT_MACHINE_TYPE,
        "guest_os": guest_os or "macOS",
        "target_major": target_major,
        "mode": "direct-macos" if direct_mode else "recovery",
        "stages": [stage.as_dict() for stage in stages],
        "claims": {
            "signature_acceptance_verified": signature_ok,
            "xnu_executed": xnu_ok and target_match_ok,
            "macos_userspace_reached": xnu_ok and userspace_ok and target_match_ok,
            "macos_boot_verified": boot_verified,
        },
        "input_integrity": input_ok,
        "blockers": blockers,
    }


__all__ = [
    "HandoffContractError",
    "HandoffStage",
    "IBOOT_MACHINE_TYPE",
    "SCHEMA",
    "SUPPORTED_TARGET_MAJORS",
    "StageStatus",
    "verify_handoff_report",
]
