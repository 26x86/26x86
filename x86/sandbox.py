"""EFI-native Sandbox control plane. No Linux or QEMU guest launcher here."""
from __future__ import annotations

import hashlib
import json
import plistlib
import shutil
import struct
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
TARGETS = (26, 27)
SUPPORT_POLICY = "VSK 제품 정책은 AppleIntelOnly입니다. 승인된 Intel Mac만 허용하며 일반 PC·상위 VM 허용 설정은 제공하지 않습니다. 현재 EFI 자체 시험은 제품 부팅 인증이 아닙니다."
GAPS = [
    "VSK의 서명된 번들·실측 플랫폼 승인·VMX/EPT·VT-d/인터럽트 리매핑 실행 기판이 아직 구현되지 않았습니다.",
    "전체 AArch64 특권 ISA·MMU·예외·PAC 실행 경로가 완성되지 않았습니다.",
    "AIC 기반 Apple SoC 장치 모델과 원본 macOS 26/27 iBoot 체인의 EFI 실행 검증이 남아 있습니다.",
    "GPU/Metal 및 macOS 사용자 공간 진입은 검증되지 않았습니다.",
]


def _target(value: Any) -> int:
    if isinstance(value, bool) or str(value) not in {str(v) for v in TARGETS}:
        raise ValueError("Sandbox target must be macOS 26 or 27")
    return int(value)


def _artifact(root: Path) -> tuple[Path, dict]:
    binary = root / "sandbox/efi/build/BOOTX64.EFI"
    report_path = binary.parent / "build-report.json"
    if report_path.stat().st_size > 1024 * 1024 or binary.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Sandbox artifact exceeds size limit")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("Sandbox build report must be an object")
    raw = binary.read_bytes()
    if len(raw) < 64 or raw[:2] != b"MZ":
        raise ValueError("Sandbox artifact is not a PE executable")
    pe = struct.unpack_from("<I", raw, 60)[0]
    if pe + 94 > len(raw) or raw[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Invalid EFI PE header")
    if struct.unpack_from("<H", raw, pe + 4)[0] != 0x8664:
        raise ValueError("Sandbox EFI must be x86_64")
    if struct.unpack_from("<H", raw, pe + 24)[0] != 0x20B or struct.unpack_from("<H", raw, pe + 92)[0] != 10:
        raise ValueError("Sandbox artifact must be a PE32+ EFI application")
    count = struct.unpack_from("<H", raw, pe + 6)[0]
    optional_size = struct.unpack_from("<H", raw, pe + 20)[0]
    sections = pe + 24 + optional_size
    if not 1 <= count <= 96 or optional_size < 112 or sections + count * 40 > len(raw):
        raise ValueError("Invalid EFI section table or optional header")
    entry = struct.unpack_from("<I", raw, pe + 40)[0]
    image_size = struct.unpack_from("<I", raw, pe + 80)[0]
    header_size = struct.unpack_from("<I", raw, pe + 84)[0]
    if not sections + count * 40 <= header_size <= len(raw) or not 0 < entry < image_size:
        raise ValueError("Invalid EFI image/header size or entrypoint")
    executable_entry = False
    for index in range(count):
        at = sections + index * 40
        virtual_size, address, size, offset = struct.unpack_from("<IIII", raw, at + 8)
        flags = struct.unpack_from("<I", raw, at + 36)[0]
        if (size and (offset < header_size or offset + size > len(raw))) or address + max(size, virtual_size) > image_size:
            raise ValueError("EFI section exceeds file or virtual image bounds")
        if flags & 0x20000000 and address <= entry < address + min(size, virtual_size):
            executable_entry = True
    if not executable_entry:
        raise ValueError("EFI entrypoint must reside in backed executable code")
    digest = hashlib.sha256(raw).hexdigest()
    if report.get("sha256") != digest:
        raise ValueError("EFI artifact hash does not match its build report")
    return binary, report


def status(mode: str = "native", *, root: Path = REPO) -> dict[str, Any]:
    error = None
    try:
        binary, report = _artifact(root)
        available = True
    except (OSError, ValueError, KeyError, struct.error) as exc:
        binary, report, available, error = None, {}, False, str(exc)
    return {
        "ok": True, "execution_mode": mode, "efi_native": True,
        "minimum_cpu": "SSE4.1 + SSE4.2", "minimum_model": "MacPro4,1 (2009)",
        "avx_required": False, "boot_verified": False, "macos_boot_ready": False,
        "product_platform_policy": "AppleIntelOnly", "product_boot_authorized": False,
        "vsk_spec": "VF-SPEC-001/0.1", "vsk_isolation_implemented": False,
        "interrupt_controller": "AIC", "boot_protocol": "iBoot", "configuration": "config.plist",
        "aic_v1_model_max_cpus": 32,
        "supported_targets": list(TARGETS), "artifact_available": available,
        "stageable": available, "artifact_kind": "efi-jit-self-test",
        "artifact_path": str(binary) if binary else None,
        "artifact_sha256": report.get("sha256"), "artifact_error": error,
        "blockers": list(GAPS), "support_policy": SUPPORT_POLICY,
        "host_check": "Diagnostic EFI checks CPUID only. VSK product admission requires measured Apple platform, VMX/EPT, VT-d and interrupt remapping.",
    }


def plan(target_major: int, *, root: Path = REPO) -> dict[str, Any]:
    major = _target(target_major)
    result = status("sandbox", root=root)
    result.update(target_major=major, target_name="Tahoe" if major == 26 else "Golden Gate",
                  components=["OpenCore UEFI x86_64 loader", "AArch64 to x86_64 JIT EFI engine",
                              "AIC Apple SoC devices (incomplete)", "Original iBoot (not bundled)",
                              "config.plist: SandboxSMBIOS / Hardware / DeviceProperties"])
    return result


def prepare(target_major: int, output_path: str, *, root: Path = REPO) -> dict[str, Any]:
    """Stage a verified EFI self-test into a new folder, never an existing ESP."""
    major = _target(target_major)
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("Choose a new output folder")
    destination = Path(output_path).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Output must be a new folder; existing EFI files will not be overwritten")
    binary, report = _artifact(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".26x86-sandbox-", dir=destination.parent))
    try:
        boot = staging / "EFI/BOOT/BOOTX64.EFI"
        boot.parent.mkdir(parents=True)
        shutil.copyfile(binary, boot)
        if hashlib.sha256(boot.read_bytes()).hexdigest() != report["sha256"]:
            raise ValueError("Staged EFI verification failed")
        payload = {"schema": 1, "product": "26x86", "feature": "Apple Silicon Sandbox",
                   "artifact_kind": "efi-jit-self-test", "target_major": major,
                   "minimum_cpu": "SSE4.1 + SSE4.2", "boot_verified": False,
                   "macos_boot_ready": False, "sha256": report["sha256"],
                   "support_policy": SUPPORT_POLICY, "blockers": list(GAPS)}
        (staging / "26x86-sandbox.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        from x86.sandbox_config import default_config
        # A disabled merge fragment, never overwrite the user's OpenCore config.
        (staging / "Sandbox-config.fragment.plist").write_bytes(plistlib.dumps(default_config(major)))
        (staging / "README.txt").write_text(
            "26x86 Apple Silicon Sandbox — EFI JIT self-test\n"
            "This image executes a synthetic AArch64 guest. It does not boot macOS yet.\n"
            "macOS target selection records the intended target; it is not a compatibility claim.\n"
            + SUPPORT_POLICY + "\n", encoding="utf-8")
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"ok": True, "output_path": str(destination), **payload}
