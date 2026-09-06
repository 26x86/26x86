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


def _vsk_artifact(root: Path, efi_path: str | Path | None = None) -> tuple[Path, dict]:
    """Validate a production VSK EFI and its build receipt.

    The production image is deliberately separate from the legacy synthetic
    JIT self-test.  A report marked as test instrumentation can never be used
    for VSK bundle staging, even when its PE hash is valid.
    """
    binary = (Path(efi_path).expanduser() if efi_path else
              root / "sandbox/vsk/build/efi/production/VSKBOOT.EFI").absolute()
    report_path = binary.parent / "report.json"
    if report_path.stat().st_size > 1024 * 1024:
        raise ValueError("VSK EFI build report exceeds size limit")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("schema") != "26x86.vsk-efi-input/1":
        raise ValueError("Invalid VSK EFI build report")
    if report.get("test_instrumentation") is not False:
        raise ValueError("Test-instrumented VSK EFI cannot be staged as production")
    if report.get("trust_anchor_provisioned") is not True:
        raise ValueError("VSK EFI has no provisioned external trust anchor")
    if report.get("boot_authorized") is not False or report.get("macos_boot_verified") is not False:
        raise ValueError("VSK EFI receipt contains an invalid boot claim")
    if report.get("exit_boot_services_implemented") is not False or report.get("exit_boot_services_adapter_implemented") is not True:
        raise ValueError("VSK EFI EBS boundary is not fail-closed")
    if report.get("artifact") != binary.name:
        raise ValueError("VSK EFI artifact name does not match its report")
    raw = binary.read_bytes()
    if len(raw) < 64 or raw[:2] != b"MZ":
        raise ValueError("VSK EFI artifact is not a PE executable")
    pe = struct.unpack_from("<I", raw, 60)[0]
    if pe + 94 > len(raw) or raw[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Invalid VSK EFI PE header")
    if struct.unpack_from("<H", raw, pe + 4)[0] != 0x8664:
        raise ValueError("VSK EFI must be x86_64")
    if struct.unpack_from("<H", raw, pe + 24)[0] != 0x20B or struct.unpack_from("<H", raw, pe + 92)[0] != 10:
        raise ValueError("VSK EFI must be a PE32+ EFI application")
    count = struct.unpack_from("<H", raw, pe + 6)[0]
    optional_size = struct.unpack_from("<H", raw, pe + 20)[0]
    sections = pe + 24 + optional_size
    if not 1 <= count <= 96 or optional_size < 112 or sections + count * 40 > len(raw):
        raise ValueError("Invalid VSK EFI section table or optional header")
    entry = struct.unpack_from("<I", raw, pe + 40)[0]
    image_size = struct.unpack_from("<I", raw, pe + 80)[0]
    header_size = struct.unpack_from("<I", raw, pe + 84)[0]
    if not sections + count * 40 <= header_size <= len(raw) or not 0 < entry < image_size:
        raise ValueError("Invalid VSK EFI image/header size or entrypoint")
    executable_entry = False
    for index in range(count):
        at = sections + index * 40
        virtual_size, address, size, offset = struct.unpack_from("<IIII", raw, at + 8)
        flags = struct.unpack_from("<I", raw, at + 36)[0]
        if (size and (offset < header_size or offset + size > len(raw))) or address + max(size, virtual_size) > image_size:
            raise ValueError("VSK EFI section exceeds file or virtual image bounds")
        if flags & 0x20000000 and address <= entry < address + min(size, virtual_size):
            executable_entry = True
    if not executable_entry:
        raise ValueError("VSK EFI entrypoint must reside in backed executable code")
    if report.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("VSK EFI artifact hash does not match its build report")
    key_hash = report.get("public_key_sha256")
    if not isinstance(key_hash, str) or len(key_hash) != 64:
        raise ValueError("VSK EFI report has no usable trust-anchor hash")
    try:
        int(key_hash, 16)
    except ValueError:
        raise ValueError("VSK EFI trust-anchor hash is not hexadecimal") from None
    target = report.get("target_major")
    epoch = report.get("minimum_release_epoch")
    if type(target) is not int or target not in TARGETS or type(epoch) is not int or not 1 <= epoch < 2**64:
        raise ValueError("VSK EFI report has invalid target or rollback floor")
    return binary, report


def _vsk_public_key(path: str | Path) -> bytes:
    """Read a raw32 public key with the bundle module's anti-TOCTOU checks."""
    from x86.vsk_bundle import _read
    _, raw, _ = _read(Path(path).expanduser(), 32)
    if len(raw) != 32:
        raise ValueError("VSK trusted public key must be exactly 32 raw bytes")
    return raw


def prepare_vsk(target_major: int, output_path: str, bundle_path: str,
                trusted_public_key: str, *, efi_path: str | Path | None = None,
                root: Path = REPO) -> dict[str, Any]:
    """Stage a signed VSK bundle and production EFI into a new directory.

    This creates boot media input only. It does not write an ESP, call EBS,
    execute a guest, or claim physical Mac/macOS success. The caller supplies
    the public trust key; a private signing key is never accepted here.
    """
    major = _target(target_major)
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("Choose a new output folder")
    if not isinstance(bundle_path, str) or not bundle_path.strip():
        raise ValueError("A signed VSK bundle directory is required")
    if not isinstance(trusted_public_key, str) or not trusted_public_key.strip():
        raise ValueError("An external VSK trusted public key is required")
    destination = Path(output_path).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Output must be a new folder; existing EFI files will not be overwritten")
    binary, efi_report = _vsk_artifact(root, efi_path)
    if efi_report["target_major"] != major:
        raise ValueError("VSK EFI target does not match the requested macOS target")
    public_key = _vsk_public_key(trusted_public_key)
    public_hash = hashlib.sha256(public_key).hexdigest()
    if public_hash != efi_report["public_key_sha256"]:
        raise ValueError("Bundle trust key does not match the EFI trust anchor")
    from x86.vsk_bundle import verify_bundle
    bundle = Path(bundle_path).expanduser().absolute()
    bundle_report = verify_bundle(bundle, trusted_public_key=public_key,
                                  expected_target=major,
                                  minimum_release_epoch=efi_report["minimum_release_epoch"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".26x86-vsk-", dir=destination.parent))
    try:
        boot = staging / "EFI/BOOT/BOOTX64.EFI"
        boot.parent.mkdir(parents=True)
        shutil.copyfile(binary, boot)
        if hashlib.sha256(boot.read_bytes()).hexdigest() != efi_report["sha256"]:
            raise ValueError("Staged VSK EFI verification failed")
        vsk_dir = staging / "EFI/26x86/VSK"
        vsk_dir.mkdir(parents=True)
        names = ["manifest.vfb", "manifest.sig", "bundle-report.json"]
        names.extend(entry["name"] for entry in bundle_report["entries"])
        from x86.vsk_bundle import _read
        for name in names:
            source = bundle / name
            limit = 64 if name == "manifest.sig" else 64 * 1024 * 1024
            _, raw, _ = _read(source, limit)
            target = vsk_dir / name
            with target.open("xb") as stream:
                stream.write(raw)
                stream.flush()
        # Revalidate the copied bundle, catching a source mutation between the
        # first verification and the byte copy.
        copied = verify_bundle(vsk_dir, trusted_public_key=public_key,
                               expected_target=major,
                               minimum_release_epoch=efi_report["minimum_release_epoch"])
        if copied["manifest_sha256"] != bundle_report["manifest_sha256"]:
            raise ValueError("Copied VSK bundle manifest changed during staging")
        payload = {
            "schema": 1, "product": "26x86", "feature": "Apple Silicon Sandbox",
            "artifact_kind": "vsk-authenticated-bootstrap", "target_major": major,
            "efi_sha256": efi_report["sha256"],
            "trusted_public_key_sha256": public_hash,
            "release_epoch_floor": efi_report["minimum_release_epoch"],
            "bundle_manifest_sha256": copied["manifest_sha256"],
            "boot_verified": False, "macos_boot_ready": False,
            "physical_mac_verified": False, "exit_boot_services_called": False,
            "boot_authorized": False, "support_policy": SUPPORT_POLICY,
            "blockers": list(GAPS),
        }
        (staging / "26x86-sandbox.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (staging / "README.txt").write_text(
            "26x86 Apple Silicon Sandbox — authenticated VSK bootstrap\n"
            "This media contains a signed VSK input bundle and a production EFI bootstrap.\n"
            "It does not execute ExitBootServices, start VMX, or boot macOS yet.\n"
            "The original guest image is not modified and existing ESP contents are untouched.\n"
            + SUPPORT_POLICY + "\n", encoding="utf-8")
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"ok": True, "output_path": str(destination), **payload}


def status(mode: str = "native", *, root: Path = REPO) -> dict[str, Any]:
    error = None
    try:
        binary, report = _artifact(root)
        available = True
    except (OSError, ValueError, KeyError, struct.error) as exc:
        binary, report, available, error = None, {}, False, str(exc)
    vsk_error = None
    try:
        vsk_binary, vsk_report = _vsk_artifact(root)
        vsk_available = True
    except (OSError, ValueError, KeyError, struct.error) as exc:
        vsk_binary, vsk_report, vsk_available, vsk_error = None, {}, False, str(exc)
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
        "vsk_artifact_available": vsk_available,
        "vsk_artifact_path": str(vsk_binary) if vsk_binary else None,
        "vsk_artifact_sha256": vsk_report.get("sha256"),
        "vsk_trust_anchor_sha256": vsk_report.get("public_key_sha256"),
        "vsk_artifact_error": vsk_error,
        "vsk_efi_scope": vsk_report.get("scope"),
        "vsk_exit_boot_services_adapter": vsk_report.get("exit_boot_services_adapter_implemented") is True,
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
