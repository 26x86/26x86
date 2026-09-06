"""Execution policy for native x86 preparation and Apple Silicon sandbox mode.

This module resolves policy and observes the host; it never loads a kext, patches
a volume, starts a VM, or reads settings from disk. ``facts`` injection is for
unit tests/internal callers only and must not be exposed as a CLI host override.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import os
import platform
import subprocess
from typing import Any, Optional


MODE_ENV = "X86_EXECUTION_MODE"
SYSCTL_TIMEOUT_SECONDS = 5


class ExecutionMode(str, Enum):
    X86 = "x86"
    APPLE_SILICON_SANDBOX = "apple-silicon-sandbox"


class ExecutionPolicyError(ValueError):
    """A mode selection or native operation violates the execution policy."""

    def __init__(self, message: str, *, code: str = "execution_policy_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class HostFacts:
    system: str
    machine: str
    hw_optional_arm64: Optional[bool] = None
    proc_translated: Optional[bool] = None
    probe_errors: tuple[str, ...] = ()
    probe_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.system, str) or not isinstance(self.machine, str):
            raise ExecutionPolicyError("Host system/machine must be strings", code="invalid_host_facts")
        known = {"darwin": "Darwin", "windows": "Windows", "linux": "Linux"}
        object.__setattr__(self, "system", known.get(self.system.lower(), self.system))
        for key in ("hw_optional_arm64", "proc_translated"):
            value = getattr(self, key)
            if value is not None and (type(value) not in (bool, int) or value not in (0, 1)):
                raise ExecutionPolicyError("Host sysctl facts must be 0, 1 or None", code="invalid_host_facts")
            if value is not None:
                object.__setattr__(self, key, bool(value))
        for key in ("probe_errors", "probe_notes"):
            values = getattr(self, key)
            if not isinstance(values, (tuple, list)) or any(not isinstance(v, str) for v in values):
                raise ExecutionPolicyError("Host probe details must be strings", code="invalid_host_facts")
            object.__setattr__(self, key, tuple(values))

    @property
    def is_apple_silicon(self) -> bool:
        return self.system == "Darwin" and (
            self.machine.lower() in {"arm64", "arm64e", "aarch64"}
            or self.hw_optional_arm64 is True
            or self.proc_translated is True
        )

    @property
    def is_verified_native_x86_macos(self) -> bool:
        return (
            self.system == "Darwin"
            and self.machine.lower() in {"x86_64", "amd64"}
            and self.hw_optional_arm64 is False
            and self.proc_translated is False
            and not self.probe_errors
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "machine": self.machine,
            "hw_optional_arm64": self.hw_optional_arm64,
            "proc_translated": self.proc_translated,
            "probe_errors": list(self.probe_errors),
            "probe_notes": list(self.probe_notes),
            "is_apple_silicon": self.is_apple_silicon,
            "is_verified_native_x86_macos": self.is_verified_native_x86_macos,
        }


def _sysctl_bool(name: str, *, permit_absent: bool = False) -> tuple[Optional[bool], Optional[str], Optional[str]]:
    environment = dict(os.environ)
    environment["LC_ALL"] = "C"
    try:
        result = subprocess.run(
            ["/usr/sbin/sysctl", "-n", name],
            capture_output=True,
            text=True,
            check=False,
            timeout=SYSCTL_TIMEOUT_SECONDS,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, f"{name}: {type(error).__name__}", None
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if result.returncode == 0 and stdout in {"0", "1"} and not stderr:
        return stdout == "1", None, None
    # The caller selects whether this particular absent OID is meaningful.
    # Match ONLY the exact C-locale ENOENT diagnostic from Apple's
    # sysctl utility. Other errors append errno text or emit different output.
    # Do not use sysctl -i: it suppresses other name2oid failures as well.
    # https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment
    # https://github.com/apple-oss-distributions/system_cmds/blob/main/sysctl/sysctl.c
    if (
        permit_absent
        and name in {"sysctl.proc_translated", "hw.optional.arm64"}
        and result.returncode == 1
        and not stdout
        and stderr == f"sysctl: unknown oid '{name}'"
    ):
        meaning = "not translated" if name == "sysctl.proc_translated" else "not ARM64 on verified nontranslated x86"
        return False, None, f"{name}: absent (ENOENT), treated as {meaning}"
    detail = stderr or ("unexpected output " + repr(stdout))
    return None, f"{name}: exit {result.returncode}: {detail[:240]}", None


def detect_host() -> HostFacts:
    """Read host architecture with bounded, read-only probes on Darwin only."""
    system = platform.system()
    machine = platform.machine()
    if system != "Darwin":
        return HostFacts(system=system, machine=machine)
    translated, translation_error, translation_note = _sysctl_bool(
        "sysctl.proc_translated", permit_absent=True
    )
    # XNU 12377.1.9 registers hw.optional.arm64 only under __arm64__.
    # Its optional-feature contract permits either no OID or 0 for absence.
    # Accept that absence only with independent x86/nontranslation evidence;
    # timeouts, access errors and ambiguous diagnostics still fail closed.
    # https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_mib.c#L1030-L1036
    # https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_mib.c#L1131-L1210
    arm64, arm_error, arm_note = _sysctl_bool(
        "hw.optional.arm64",
        permit_absent=(machine.lower() in {"x86_64", "amd64"}
                       and translated is False and translation_error is None),
    )
    return HostFacts(
        system=system,
        machine=machine,
        hw_optional_arm64=arm64,
        proc_translated=translated,
        probe_errors=tuple(e for e in (arm_error, translation_error) if e is not None),
        probe_notes=tuple(n for n in (arm_note, translation_note) if n is not None),
    )


@dataclass(frozen=True)
class ExecutionContext:
    mode: ExecutionMode
    source: str
    host: HostFacts
    environment_locked: bool = False

    @property
    def is_sandbox(self) -> bool:
        return self.mode is ExecutionMode.APPLE_SILICON_SANDBOX

    @property
    def can_native_plan(self) -> bool:
        return self.mode is ExecutionMode.X86 and (
            self.host.system in {"Windows", "Linux"}
            or self.host.is_verified_native_x86_macos
        )

    @property
    def can_native_apply(self) -> bool:
        return self.mode is ExecutionMode.X86 and self.host.is_verified_native_x86_macos

    def require_native_plan(self, feature: str = "Native driver preparation") -> ExecutionContext:
        if not self.can_native_plan:
            raise ExecutionPolicyError(
                f"{feature} requires x86 mode and a Windows/Linux preparation host or verified native x86 macOS; "
                f"selected {self.mode.value} on {self.host.system}/{self.host.machine}",
                code="native_plan_blocked",
            )
        return self

    def require_native_apply(self, feature: str = "Native driver/root patch application") -> ExecutionContext:
        if not self.can_native_apply:
            raise ExecutionPolicyError(
                f"{feature} requires verified native x86 macOS in x86 mode. "
                "Apple Silicon/Rosetta, sandbox mode and Windows/Linux cannot apply native x86 kexts or root patches.",
                code="native_apply_blocked",
            )
        return self

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "source": self.source,
            "environment_locked": self.environment_locked,
            "is_sandbox": self.is_sandbox,
            "can_native_plan": self.can_native_plan,
            "can_native_apply": self.can_native_apply,
            "host": self.host.as_dict(),
        }


def _mode(value: Any, source: str) -> ExecutionMode:
    if isinstance(value, ExecutionMode):
        return value
    if isinstance(value, str):
        try:
            return ExecutionMode(value)
        except ValueError:
            pass
    raise ExecutionPolicyError(
        f"Invalid execution mode from {source}; expected 'x86' or 'apple-silicon-sandbox'",
        code="invalid_execution_mode",
    )


def resolve_execution(
    requested: Optional[str | ExecutionMode] = None,
    settings: Optional[Mapping[str, Any]] = None,
    environ: Optional[Mapping[str, str]] = None,
    facts: Optional[HostFacts | Mapping[str, Any]] = None,
) -> ExecutionContext:
    """Resolve explicit > environment > supplied settings > host auto.

    An environment mode also locks child invocations: a conflicting explicit
    request raises instead of overriding it. There is no implicit settings I/O.
    Unknown Darwin architecture/probe failures never permit a native operation.
    """
    if settings is not None and not isinstance(settings, Mapping):
        raise ExecutionPolicyError("settings must be a mapping", code="invalid_execution_settings")
    environment = os.environ if environ is None else environ
    if not isinstance(environment, Mapping):
        raise ExecutionPolicyError("environ must be a mapping", code="invalid_execution_environment")
    explicit = None if requested is None else _mode(requested, "request")
    locked = MODE_ENV in environment
    inherited = _mode(environment[MODE_ENV], MODE_ENV) if locked else None
    if explicit is not None and inherited is not None and explicit is not inherited:
        raise ExecutionPolicyError(
            f"{MODE_ENV} locks this process to {inherited.value}; request {explicit.value} conflicts",
            code="execution_mode_locked",
        )
    selected = explicit or inherited
    source = "request" if explicit is not None else "environment"
    if selected is None:
        value = None if settings is None else settings.get("execution_mode")
        if value is not None:
            selected = _mode(value, "settings")
            source = "settings"
    if facts is None:
        host = detect_host()
    elif isinstance(facts, HostFacts):
        host = facts
    elif isinstance(facts, Mapping):
        try:
            host = HostFacts(**facts)
        except TypeError as error:
            raise ExecutionPolicyError("Invalid injected host facts", code="invalid_host_facts") from error
    else:
        raise ExecutionPolicyError("facts must be HostFacts or a mapping", code="invalid_host_facts")
    if selected is None:
        selected = ExecutionMode.APPLE_SILICON_SANDBOX if host.is_apple_silicon else ExecutionMode.X86
        source = "host"
    if host.is_apple_silicon and selected is ExecutionMode.X86:
        raise ExecutionPolicyError(
            "Apple Silicon/Rosetta requires apple-silicon-sandbox; selecting x86 cannot enable native x86 kext/root operations",
            code="apple_silicon_native_mode_blocked",
        )
    return ExecutionContext(mode=selected, source=source, host=host, environment_locked=locked)
