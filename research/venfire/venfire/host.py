"""Read-only, fail-closed eligibility checks for the 26x86 runtime.

These checks are best-effort local evidence, not cryptographic attestation. A
privileged host can fabricate all of it. This module always reports normal
release eligibility: AVX2-capable Intel Macs on Darwin or Linux. The separate
build-profile policy controls the explicit development-only platform exception.
It never relaxes CPU requirements. No guest is loaded or firmware changed.
"""

from __future__ import annotations

import platform
import plistlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.parsers.expat import ExpatError


_SYSCTL = "/usr/sbin/sysctl"
_IOREG = "/usr/sbin/ioreg"
_PROBE_TIMEOUT_SECONDS = 4
_MAX_PROBE_BYTES = 1024 * 1024
_MODEL = re.compile(r"(?:MacPro|Macmini|MacBookPro|MacBookAir|MacBook|iMacPro|iMac|Xserve)\d+,\d+\Z")
_BOARD = re.compile(r"Mac-[0-9A-Fa-f]{8,32}\Z")
_VM = re.compile(r"vmware|virtualbox|vbox|qemu|\bkvm\b|parallels|\bxen\b|bhyve|virtio|virtualmac|virtual machine", re.I)
_APPLE_VENDORS = {"Apple Inc.", "Apple Computer, Inc."}
_CPU_CHECKS = frozenset({"x86_64", "intel_cpu", "avx2"})


@dataclass(frozen=True)
class HostEvidence:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class HostReport:
    eligible: bool
    system: str
    architecture: str
    hardware_model: str | None
    cpu_vendor: str | None
    evidence: tuple[HostEvidence, ...]
    reasons: tuple[str, ...]

    @property
    def cpu_eligible(self) -> bool:
        """Mandatory requirements that even developer policy cannot waive."""
        checks = [entry for entry in self.evidence if entry.name in _CPU_CHECKS]
        return (len(checks) == len(_CPU_CHECKS)
                and {entry.name for entry in checks} == _CPU_CHECKS
                and all(entry.passed for entry in checks))

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "cpu_eligible": self.cpu_eligible,
            "system": self.system,
            "architecture": self.architecture,
            "hardware_model": self.hardware_model,
            "cpu_vendor": self.cpu_vendor,
            "evidence": [item.to_dict() for item in self.evidence],
            "reasons": list(self.reasons),
            "assurance": "Best-effort local hardware evidence; not cryptographic attestation.",
        }


class HostEligibilityError(RuntimeError):
    def __init__(self, report: HostReport):
        self.report = report
        super().__init__("26x86 runtime denied: " + "; ".join(report.reasons))


@dataclass(frozen=True)
class _Probe:
    data: bytes | None
    status: str


def _probe(arguments: tuple[str, ...]) -> _Probe:
    """Run only fixed absolute, read-only host tools without invoking a shell."""
    try:
        result = subprocess.run(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=_PROBE_TIMEOUT_SECONDS,
            check=False,
            shell=False,
            env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired:
        return _Probe(None, "probe timed out")
    except OSError:
        return _Probe(None, "probe unavailable")
    if result.returncode != 0:
        return _Probe(None, "probe failed")
    if len(result.stdout) > _MAX_PROBE_BYTES:
        return _Probe(None, "probe output exceeds limit")
    return _Probe(result.stdout, "ok")


def _sysctl(key: str) -> tuple[str | None, str]:
    result = _probe((_SYSCTL, "-n", key))
    if result.data is None:
        return None, result.status
    try:
        value = result.data.decode("ascii").strip()
    except UnicodeDecodeError:
        return None, "invalid sysctl output"
    if not value or len(value) > 8192 or "\n" in value or "\r" in value or "\x00" in value:
        return None, "invalid sysctl output"
    return value, "ok"


def _registry(class_name: str) -> tuple[list[dict[str, Any]] | None, str]:
    result = _probe((_IOREG, "-a", "-r", "-d", "1", "-c", class_name))
    if result.data is None:
        return None, result.status
    try:
        parsed = plistlib.loads(result.data)
    except (ValueError, TypeError, OverflowError, ExpatError, plistlib.InvalidFileException):
        return None, "invalid IORegistry plist"
    if not isinstance(parsed, list) or not all(isinstance(node, dict) for node in parsed):
        return None, "invalid IORegistry structure"
    return parsed, "ok"


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    return value if isinstance(value, str) else ""


def _contains_vm(value: Any) -> bool:
    """Inspect identifiers locally, returning a boolean without logging data."""
    if isinstance(value, dict):
        # Serial/UUID values are intentionally never inspected or retained.
        return any(
            _contains_vm(item)
            for key, item in value.items()
            if not any(token in str(key).lower() for token in ("serial", "uuid"))
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_vm(item) for item in value)
    return bool(_VM.search(_text(value)))


def _detect_darwin(system: str, architecture: str) -> HostReport:
    evidence: list[HostEvidence] = []

    def check(name: str, passed: bool, detail: str) -> None:
        evidence.append(HostEvidence(name, passed, detail))

    check("host_os", True, "Darwin or Linux release host required")
    check("x86_64", architecture == "x86_64" and sys.maxsize > 2**32, "x86_64 host process required")
    if architecture != "x86_64" or sys.maxsize <= 2**32:
        return HostReport(False, system, architecture, None, None, tuple(evidence), tuple(e.detail for e in evidence if not e.passed))

    model, model_status = _sysctl("hw.model")
    vendor, vendor_status = _sysctl("machdep.cpu.vendor")
    hypervisor, hv_status = _sysctl("kern.hv_vmm_present")
    features, features_status = _sysctl("machdep.cpu.features")
    leaf7, leaf7_status = _sysctl("machdep.cpu.leaf7_features")
    registry, registry_status = _registry("IOPlatformExpertDevice")
    smc, smc_status = _registry("AppleSMC")

    valid_model = model is not None and _MODEL.fullmatch(model) is not None
    check("apple_model", valid_model, "Apple Intel model identifier required" + (f" ({model_status})" if model is None else ""))
    check("intel_cpu", vendor == "GenuineIntel", "GenuineIntel CPU required" + (f" ({vendor_status})" if vendor is None else ""))
    check("avx2", leaf7 is not None and "AVX2" in leaf7.upper().split(), "AVX2 CPU support required" + (f" ({leaf7_status})" if leaf7 is None else ""))
    check("hypervisor_absent", hypervisor == "0", "kern.hv_vmm_present must explicitly report 0" + (f" ({hv_status})" if hypervisor is None else ""))
    feature_tokens = set(features.upper().split()) if features is not None else set()
    check("cpu_vm_flag_absent", features is not None and not {"VMM", "HYPERVISOR"}.intersection(feature_tokens), "CPU feature evidence must be available and contain no VMM/HYPERVISOR flag" + (f" ({features_status})" if features is None else ""))
    known_vm = _contains_vm([model, vendor, registry, smc])
    check("known_vm_absent", not known_vm, "Known virtual-machine identifiers must be absent")

    # A single root must carry a consistent set of Apple properties. Combining
    # fields from unrelated registry nodes is not accepted as positive evidence.
    consistent_platform = any(
        _text(node.get("manufacturer")) in _APPLE_VENDORS
        and _text(node.get("model")) == model
        and valid_model
        and _BOARD.fullmatch(_text(node.get("board-id"))) is not None
        for node in registry or []
    )
    check("apple_platform_registry", consistent_platform, "Matching Apple manufacturer, model, and board-id required in IOPlatformExpertDevice" + (f" ({registry_status})" if registry is None else ""))
    present_smc = any(
        node.get("IOObjectClass") == "AppleSMC" or node.get("IOClass") == "AppleSMC"
        for node in smc or []
    )
    check("apple_smc", present_smc, "AppleSMC service evidence required" + (f" ({smc_status})" if smc is None else ""))
    reasons = tuple(item.detail for item in evidence if not item.passed)
    return HostReport(
        eligible=not reasons,
        system=system,
        architecture=architecture,
        hardware_model=model if valid_model else None,
        cpu_vendor="GenuineIntel" if vendor == "GenuineIntel" else None,
        evidence=tuple(evidence),
        reasons=reasons,
    )


def _linux_read(path: str, limit: int = 8192) -> tuple[str | None, str]:
    """Bounded reads of fixed kernel-owned procfs/sysfs metadata, never serials.

    Sysfs class/device symlinks are kernel API structure, unlike guest inputs.
    These reads intentionally follow them. No user-selected path is accepted by
    the public host detector and no sysfs write or driver load is performed.
    """
    try:
        with open(path, "rb") as stream:
            data = stream.read(limit + 1)
    except FileNotFoundError:
        return None, "missing"
    except OSError:
        return None, "unavailable"
    if len(data) > limit:
        return None, "metadata exceeds limit"
    try:
        return data.decode("ascii").strip(), "ok"
    except UnicodeDecodeError:
        return None, "invalid metadata encoding"


def _linux_smc_bound() -> bool:
    try:
        driver = Path("/sys/bus/platform/drivers/applesmc")
        for child in driver.iterdir():
            if child.name.startswith("applesmc") and child.is_symlink():
                device = child.resolve(strict=True)
                if str(device).startswith("/sys/devices/") and device.is_dir():
                    return True
    except OSError:
        pass
    return False


def _linux_cpu_records(text: str | None) -> list[dict[str, str]]:
    if text is None:
        return []
    records = []
    for block in re.split(r"\n\s*\n", text):
        fields = {}
        for line in block.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                if key in {"processor", "vendor_id", "flags"}:
                    if key in fields:
                        return []
                    fields[key] = value.strip()
        if fields:
            if "processor" not in fields:
                return []
            records.append(fields)
    return records


def _report(system: str, architecture: str, model: str | None, vendor: str | None,
            evidence: list[HostEvidence]) -> HostReport:
    reasons = tuple(item.detail for item in evidence if not item.passed)
    valid_model = isinstance(model, str) and _MODEL.fullmatch(model) is not None
    return HostReport(not reasons, system, architecture, model if valid_model else None,
                      "GenuineIntel" if vendor == "GenuineIntel" else None,
                      tuple(evidence), reasons)


def _detect_linux(system: str, architecture: str) -> HostReport:
    cpuinfo, cpu_status = _linux_read("/proc/cpuinfo", 4 * 1024 * 1024)
    cpus = _linux_cpu_records(cpuinfo)
    vendors = [cpu.get("vendor_id") for cpu in cpus]
    flags = [set(cpu.get("flags", "").lower().split()) for cpu in cpus]
    intel = bool(vendors) and all(vendor == "GenuineIntel" for vendor in vendors)
    avx2 = bool(flags) and all("avx2" in features for features in flags)
    cpu_vm_clear = bool(flags) and all(features and not {"hypervisor", "vmm"}.intersection(features) for features in flags)
    dmi = {}
    for key in ("sys_vendor", "product_name", "board_vendor", "board_name"):
        value, _ = _linux_read("/sys/class/dmi/id/" + key)
        dmi[key] = value
    model = dmi["product_name"]
    valid_model = isinstance(model, str) and _MODEL.fullmatch(model) is not None
    hypervisor, hypervisor_status = _linux_read("/sys/hypervisor/type")
    hypervisor_clear = hypervisor_status == "missing" or (hypervisor_status == "ok" and not hypervisor)
    cpu_detail = "" if cpus else f" ({cpu_status}; no complete CPU records)"
    evidence = [
        HostEvidence("host_os", True, "Darwin or Linux release host required"),
        HostEvidence("x86_64", architecture == "x86_64" and sys.maxsize > 2**32, "x86_64 host process required"),
        HostEvidence("intel_cpu", intel, "Every observed CPU must report GenuineIntel" + cpu_detail),
        HostEvidence("avx2", avx2, "Every observed CPU must expose AVX2 to the Linux kernel" + cpu_detail),
        HostEvidence("cpu_vm_flag_absent", cpu_vm_clear, "Linux CPU flags must be available and contain no hypervisor/VMM flag"),
        HostEvidence("hypervisor_absent", hypervisor_clear, "Linux hypervisor metadata must be absent or explicitly empty"),
        HostEvidence("known_vm_absent", not _contains_vm([dmi, hypervisor]), "Known virtual-machine identifiers must be absent"),
        HostEvidence("apple_model", valid_model, "Apple Intel DMI product_name required"),
        HostEvidence("apple_platform_dmi", dmi["sys_vendor"] in _APPLE_VENDORS
                     and dmi["board_vendor"] in _APPLE_VENDORS
                     and isinstance(dmi["board_name"], str)
                     and _BOARD.fullmatch(dmi["board_name"]) is not None,
                     "Apple DMI system vendor, board vendor, and board identifier required"),
        HostEvidence("apple_smc", _linux_smc_bound(), "A bound Linux applesmc platform device is required; an unavailable driver is not positive evidence"),
    ]
    return _report(system, architecture, model, "GenuineIntel" if intel else None, evidence)


def _windows_cpu() -> tuple[str | None, bool | None, str]:
    """Read-only Windows CPU evidence; Windows never passes release policy."""
    try:
        import ctypes
        from ctypes import wintypes
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                            0, winreg.KEY_READ) as key:
            vendor, _ = winreg.QueryValueEx(key, "VendorIdentifier")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        feature = kernel32.IsProcessorFeaturePresent
        feature.argtypes = [wintypes.DWORD]
        feature.restype = wintypes.BOOL
        # Documented PF_AVX2_INSTRUCTIONS_AVAILABLE, not a guessed CPUID bit.
        avx2 = bool(feature(40))
        return vendor if isinstance(vendor, str) else None, avx2, "ok"
    except (ImportError, AttributeError, OSError, ValueError):
        return None, None, "Windows CPU evidence unavailable"


def detect_host() -> HostReport:
    """Collect normal eligibility and separate nonwaivable CPU evidence.

    No environment setting or fixture file changes these facts. Explicit lab
    authorization, when compiled into a developer profile, lives in policy.py.
    """
    system = platform.system()
    native_architecture = platform.machine()
    architecture = "x86_64" if native_architecture.lower() in {"amd64", "x86_64"} else native_architecture
    if system == "Darwin":
        return _detect_darwin(system, architecture)
    if system == "Linux":
        return _detect_linux(system, architecture)
    vendor, avx2, status = _windows_cpu() if system == "Windows" else (None, None, "unsupported host OS")
    evidence = [
        HostEvidence("host_os", False, "Darwin or Linux release host required"),
        HostEvidence("x86_64", architecture == "x86_64" and sys.maxsize > 2**32, "x86_64 host process required"),
        HostEvidence("intel_cpu", vendor == "GenuineIntel", "GenuineIntel CPU required" + (f" ({status})" if vendor is None else "")),
        HostEvidence("avx2", avx2 is True, "OS-available AVX2 required" + (f" ({status})" if avx2 is None else "")),
        HostEvidence("apple_platform", False, "Apple platform evidence is unavailable on this host OS"),
    ]
    return _report(system, architecture, None, vendor, evidence)


def require_apple_intel() -> HostReport:
    """Enforce fresh best-effort eligibility, including mandatory AVX2."""
    report = detect_host()
    if not report.eligible:
        raise HostEligibilityError(report)
    return report
