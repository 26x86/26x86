"""Scope policy for the synthetic iBoot(AArch64) machine personality.

The personality is deliberately narrower than the generic Venfire machine
type catalogue.  It describes the guest interface that 26x86 is willing to
construct; it is not an Apple signature verifier and it never classifies a
firmware image by filename or by guessed bytes.
"""

from __future__ import annotations

from typing import Any


IBOOT_MACHINE_TYPE = "iBoot(AArch64)"
MACOS_GUEST_OS = "macOS"
DEFAULT_RECOVERY_IMAGE = "_default.ipsw"
SUPPORTED_GUEST_OSES = (MACOS_GUEST_OS,)
UNSUPPORTED_GUEST_OSES = ("iOS", "iPadOS", "tvOS", "watchOS", "visionOS")
SUPPORTED_RECOVERY_PROTOCOLS = ("DFU", "IPSW")
RECOVERY_PROTOCOLS = ("Auto", "DFU", "IPSW", "DFU/IPSW")


class IbootScopeError(ValueError):
    """A configuration requests an iBoot guest outside the macOS scope."""

    def __init__(self, message: str, *, code: str = "VF_GUEST_SCOPE_VIOLATION") -> None:
        self.code = code
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": str(self)}


def _token(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().casefold().replace("_", " ").replace("-", " ").split())


def normalize_guest_os(value: object) -> str:
    """Return a canonical guest name, rejecting unknown/mobile guests."""
    aliases = {
        "macos": MACOS_GUEST_OS,
        "mac os": MACOS_GUEST_OS,
        "ios": "iOS",
        "ipad os": "iPadOS",
        "ipados": "iPadOS",
        "tvos": "tvOS",
        "tv os": "tvOS",
        "watchos": "watchOS",
        "watch os": "watchOS",
        "visionos": "visionOS",
        "vision os": "visionOS",
    }
    canonical = aliases.get(_token(value))
    if canonical is None:
        raise IbootScopeError(
            "iBoot(AArch64)는 macOS 게스트만 지원합니다. "
            "지원 값은 macOS이며 iOS/iPadOS 및 기타 모바일 Apple OS는 사용할 수 없습니다."
        )
    if canonical != MACOS_GUEST_OS:
        raise IbootScopeError(
            f"iBoot(AArch64) guest OS '{canonical}' is unsupported; only macOS is supported."
        )
    return canonical


def normalize_recovery_protocol(value: object) -> str:
    """Normalize the iBoot recovery selector without accepting Fastboot."""
    if value is None:
        return "Auto"
    token = _token(value)
    aliases = {
        "auto": "Auto",
        "dfu": "DFU",
        "ipsw": "IPSW",
        "dfu/ipsw": "DFU/IPSW",
        "dfu + ipsw": "DFU/IPSW",
        "dfu and ipsw": "DFU/IPSW",
    }
    protocol = aliases.get(token)
    if protocol is None or protocol not in RECOVERY_PROTOCOLS:
        raise IbootScopeError(
            "iBoot(AArch64) recovery는 DFU/IPSW만 지원합니다. Fastboot 및 기타 프로토콜은 거부됩니다.",
            code="VF_RECOVERY_SCOPE_VIOLATION",
        )
    return protocol


def validate_iboot_scope(
    machine_type: object = IBOOT_MACHINE_TYPE,
    guest_os: object = MACOS_GUEST_OS,
    *,
    recovery_protocol: object = "Auto",
    recovery_image_name: object = DEFAULT_RECOVERY_IMAGE,
    recovery_enabled: object = True,
    target_major: object = None,
) -> dict[str, Any]:
    """Validate and describe the user-visible iBoot policy.

    The function is intentionally pure.  It performs no filesystem access,
    IPSW inspection, USB I/O, or signature decision.  Those later layers must
    consume this result only after the scope check succeeds.
    """
    if machine_type != IBOOT_MACHINE_TYPE:
        raise IbootScopeError(
            f"This policy applies only to {IBOOT_MACHINE_TYPE}; got {machine_type!r}.",
            code="VF_MACHINE_PERSONALITY_MISMATCH",
        )
    canonical_guest = normalize_guest_os(guest_os)
    protocol = normalize_recovery_protocol(recovery_protocol)
    if type(recovery_enabled) is not bool:
        raise IbootScopeError(
            "Venfire.Recovery.Enabled must be a boolean.", code="VF_RECOVERY_CONFIG_INVALID"
        )
    if target_major is not None and (
        type(target_major) is not int or target_major not in (26, 27)
    ):
        raise IbootScopeError(
            "iBoot(AArch64) target must be macOS 26 or 27.", code="VF_TARGET_SCOPE_VIOLATION"
        )
    if not isinstance(recovery_image_name, str) or not recovery_image_name.strip():
        raise IbootScopeError(
            "iBoot Local Recovery image name must be _default.ipsw.",
            code="VF_RECOVERY_IMAGE_SCOPE_VIOLATION",
        )
    image_name = recovery_image_name.strip()
    if image_name != DEFAULT_RECOVERY_IMAGE:
        raise IbootScopeError(
            f"iBoot Local Recovery accepts the macOS recovery image name {DEFAULT_RECOVERY_IMAGE!r}; "
            f"got {image_name!r}.",
            code="VF_RECOVERY_IMAGE_SCOPE_VIOLATION",
        )
    return {
        "machine_type": IBOOT_MACHINE_TYPE,
        "personality": "iBoot",
        "guest_os": canonical_guest,
        "guest_os_supported": True,
        "guest_os_policy": "macOS-only",
        "supported_guest_os": list(SUPPORTED_GUEST_OSES),
        "unsupported_guest_os": list(UNSUPPORTED_GUEST_OSES),
        "policy_matrix": policy_matrix(),
        "target_major": target_major,
        "recovery": {
            "enabled": recovery_enabled,
            "scope": "macOS-only",
            "protocol": protocol,
            "supported_protocols": list(SUPPORTED_RECOVERY_PROTOCOLS),
            "default_image_name": DEFAULT_RECOVERY_IMAGE,
            "image_name": image_name,
            "dfu_macos_recovery": True,
            "ipsw_macos_recovery": True,
        },
    }


def default_scope(*, target_major: int | None = None, recovery_enabled: bool = False) -> dict[str, Any]:
    """Return the fixed policy metadata used by status and GUI surfaces."""
    return validate_iboot_scope(
        target_major=target_major, recovery_enabled=recovery_enabled
    )


def policy_matrix() -> list[dict[str, str | bool]]:
    """Return the explicit machine/guest matrix for diagnostics and UI."""
    return [
        {"machine_type": IBOOT_MACHINE_TYPE, "guest_os": "macOS", "supported": True},
        {"machine_type": IBOOT_MACHINE_TYPE, "guest_os": "iOS", "supported": False},
        {"machine_type": IBOOT_MACHINE_TYPE, "guest_os": "iPadOS", "supported": False},
    ]


__all__ = [
    "DEFAULT_RECOVERY_IMAGE",
    "IBOOT_MACHINE_TYPE",
    "IbootScopeError",
    "MACOS_GUEST_OS",
    "RECOVERY_PROTOCOLS",
    "SUPPORTED_GUEST_OSES",
    "SUPPORTED_RECOVERY_PROTOCOLS",
    "UNSUPPORTED_GUEST_OSES",
    "default_scope",
    "normalize_guest_os",
    "normalize_recovery_protocol",
    "policy_matrix",
    "validate_iboot_scope",
]
