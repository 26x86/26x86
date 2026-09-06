"""Build-profile policy for explicit, nonredistributable lab host exceptions.

This is project release policy, not an upstream license amendment or a claim
that source modifications/forks can be prevented. No environment switch turns
a normal release into a developer build.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from .host import HostEligibilityError, HostReport, detect_host


RELEASE_PROFILE = "release"
DEVELOPER_PROFILE = "developer-nonredistributable"
DEVELOPER_DISTRIBUTION_STATUS = "NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT"


class BuildPolicyError(RuntimeError):
    """Build metadata or requested release action violates project policy."""


@dataclass(frozen=True)
class HostAuthorization:
    report: HostReport
    profile: str
    developer_bypass_applied: bool
    distribution_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized": True,
            "host": self.report.to_dict(),
            "build_profile": self.profile,
            "developer_host_bypass": self.developer_bypass_applied,
            "distribution_status": self.distribution_status,
            "cpu_requirements_waived": False,
            "artifact_or_guest_trust_waived": False,
        }


def load_build_profile() -> str:
    """Read generated package-local BUILD_PROFILE; missing marker means release.

    Only a missing marker is defaulted. Malformed metadata or errors while
    loading an existing marker fail closed. Packaging must generate the marker
    in an isolated build tree, not modify a running release installation.
    """
    name = __package__ + "._build_profile"
    try:
        marker = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            return RELEASE_PROFILE
        raise BuildPolicyError("Build profile has an unavailable dependency") from exc
    except (ImportError, SyntaxError, OSError, RuntimeError) as exc:
        raise BuildPolicyError("Build profile cannot be loaded") from exc
    profile = getattr(marker, "BUILD_PROFILE", None)
    if type(profile) is not str or profile not in {RELEASE_PROFILE, DEVELOPER_PROFILE}:
        raise BuildPolicyError("Invalid generated BUILD_PROFILE")
    return profile


def require_release_build() -> str:
    """Release packaging entry points must call this before producing outputs."""
    profile = load_build_profile()
    if profile != RELEASE_PROFILE:
        raise BuildPolicyError("Normal release packaging rejects NONREDISTRIBUTABLE developer builds")
    return profile


def authorize_host(*, developer_host_bypass: bool = False) -> HostAuthorization:
    """Authorize current host under the generated build profile.

    The flag only waives Apple/OS/model/SMC/VM platform requirements. A known VM
    may be used in an explicitly marked lab build. Intel, x86_64 and AVX2 stay
    mandatory, as do every caller's input-integrity and guest-trust checks.
    """
    if type(developer_host_bypass) is not bool:
        raise BuildPolicyError("developer_host_bypass must be an explicit boolean")
    profile = load_build_profile()
    if developer_host_bypass and profile != DEVELOPER_PROFILE:
        raise BuildPolicyError("--developer-host-bypass requires a generated NONREDISTRIBUTABLE developer build")
    report = detect_host()
    if not report.cpu_eligible:
        raise HostEligibilityError(report)
    if not developer_host_bypass and not report.eligible:
        raise HostEligibilityError(report)
    return HostAuthorization(
        report=report,
        profile=profile,
        developer_bypass_applied=developer_host_bypass,
        distribution_status=DEVELOPER_DISTRIBUTION_STATUS if profile == DEVELOPER_PROFILE else "NORMAL RELEASE PROFILE",
    )
