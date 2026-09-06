"""
cli.py: argparse subcommands — detect, build, patch, status, wizard
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from . import __version__
from .logging import setup_logging
from .manifest import APP_NAME
from .platform import (
    MACOS_ONLY_MESSAGE,
    is_macos,
    non_mac_detect_payload,
    platform_label,
)
from .settings import SettingsStore


def _ensure_repo_on_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    return repo_root


def _sw_vers(key: str) -> Optional[str]:
    if not is_macos():
        return None
    flag = key if key.startswith("-") else f"-{key}"
    try:
        result = subprocess.run(
            ["/usr/bin/sw_vers", flag],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _emit_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _serialize_detect_payload(computer: Any, model_override: Optional[str] = None) -> dict[str, Any]:
    from opencore_legacy_patcher.datasets import smbios_data
    from x86.pre_avx.detect import build_detect_fields, serialize_detect_fields
    from x86.settings import SettingsStore, read_auto_pre_avx_patch

    if not is_macos():
        payload = non_mac_detect_payload()
        model = model_override or payload.get("model") or "unknown"
        payload["model"] = model
        payload["real_model"] = model
        payload["build_model"] = model
        auto_pre_avx_patch = read_auto_pre_avx_patch(SettingsStore().load())
        fields = build_detect_fields(model, auto_pre_avx_patch=auto_pre_avx_patch, xnu_major=25)
        payload.update(serialize_detect_fields(fields))
        return payload

    model = computer.real_model
    marketing = smbios_data.smbios_dictionary.get(model, {}).get("Marketing Name", model)
    cpu_name = getattr(computer.cpu, "name", None) if computer.cpu else None

    gpus = []
    for gpu in computer.gpus or []:
        gpus.append(
            {
                "name": getattr(gpu, "name", "Unknown"),
                "vendor": hex(getattr(gpu, "vendor_id", 0)),
                "device": hex(getattr(gpu, "device_id", 0)),
            }
        )

    xnu_major = None
    try:
        from opencore_legacy_patcher.detections import os_probe

        xnu_major = os_probe.OSProbe().detect_kernel_major()
    except Exception:
        pass

    auto_pre_avx_patch = read_auto_pre_avx_patch(SettingsStore().load())
    cpu_features = None
    cpu_leaf7_features = None
    if getattr(computer, "cpu", None) is not None:
        cpu_features = getattr(computer.cpu, "flags", None)
        cpu_leaf7_features = getattr(computer.cpu, "leafs", None)

    fields = build_detect_fields(
        model,
        gpus=getattr(computer, "gpus", None),
        cpu_features=cpu_features,
        cpu_leaf7_features=cpu_leaf7_features,
        auto_pre_avx_patch=auto_pre_avx_patch,
        xnu_major=xnu_major,
    )

    payload = {
        "platform": "macOS",
        "host_is_mac": True,
        "model": model,
        "marketing_name": marketing,
        "build_model": computer.build_model,
        "real_model": computer.real_model,
        "cpu": cpu_name,
        "gpus": gpus,
        "os_version": _sw_vers("productVersion"),
        "os_build": _sw_vers("buildVersion"),
        "host_is_hackintosh": getattr(computer, "firmware_vendor", None) not in (None, "Apple"),
    }
    payload.update(serialize_detect_fields(fields))
    return payload


def cmd_detect(args: argparse.Namespace) -> int:
    _ensure_repo_on_path()

    if is_macos():
        from opencore_legacy_patcher.detections.device_probe import Computer

        computer = Computer.probe()
        payload = _serialize_detect_payload(computer)
    else:
        payload = _serialize_detect_payload(None, model_override=args.model)

    store = SettingsStore()
    detect_extra = {
        key: payload[key]
        for key in (
            "pre_avx_mac_pro",
            "recommended_metal_patch",
            "recommended_tahoe_graphics_policy",
            "avx_available",
            "avx2_available",
            "has_avx2",
            "tahoe_blocked_patches",
            "safari_pre_avx_fix_recommended",
            "auto_pre_avx_patch",
        )
        if key in payload
    }
    store.record_detect(str(payload["model"]), extra=detect_extra)

    if args.json:
        _emit_json(payload)
    else:
        if is_macos():
            logging.info("Mac 모델 감지 결과:")
            logging.info("  모델: %s", payload["model"])
            logging.info("  제품명: %s", payload["marketing_name"])
            logging.info("  CPU: %s", payload["cpu"] or "N/A")
            if payload.get("pre_avx_mac_pro"):
                logging.info("  Pre-AVX Mac Pro: 예 (Metal 힌트: %s)", payload.get("recommended_metal_patch"))
                logging.info("  AVX 사용 가능: %s", "예" if payload.get("avx_available") else "아니오")
                logging.info("  AVX2 사용 가능: %s", "예" if payload.get("avx2_available") else "아니오")
                if payload.get("recommended_tahoe_graphics_policy"):
                    logging.info("  Tahoe 그래픽 정책: %s", payload["recommended_tahoe_graphics_policy"])
                blocked = payload.get("tahoe_blocked_patches") or []
                if blocked:
                    logging.info("  Tahoe 차단 패치: %s", ", ".join(blocked[:4]) + ("…" if len(blocked) > 4 else ""))
        else:
            logging.info("%s 호스트 정보:", platform_label())
            logging.info("  플랫폼: %s", payload.get("platform"))
            logging.info("  Mac 하드웨어 감지: 불가")
            logging.info("  CPU: %s", payload.get("cpu") or "N/A")
            logging.info("  안내: %s", MACOS_ONLY_MESSAGE)
            safari = payload.get("safari26_preavx") or {}
            if safari.get("eligible_model"):
                logging.info(
                    "  Safari 26 Pre-AVX Fix: 이 호스트에서는 적용하지 않습니다. "
                    "MacPro5,1에서 EFI 빌드 시 자동 적용됩니다."
                )
        safari = payload.get("safari26_preavx") or {}
        if safari:
            logging.info(
                "  Safari 26 Pre-AVX Fix: %s (%s)",
                "적용 예정" if safari.get("should_apply") else "건너뜀",
                safari.get("reason"),
            )
        logging.info(
            "  OS: %s (%s)",
            payload["os_version"] or "N/A",
            payload["os_build"] or "N/A",
        )
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    from x86.execution import resolve_execution
    try:
        resolve_execution(getattr(args, "mode", None), settings=SettingsStore().load()).require_native_apply("Native EFI build")
    except ValueError as exc:
        _emit_json({"ok": False, "status": "native_build_blocked", "error": str(exc)})
        return 2
    if not is_macos():
        message = MACOS_ONLY_MESSAGE
        if args.json:
            _emit_json({"status": "unsupported_platform", "message": message, "platform": platform_label()})
        else:
            logging.error(message)
        return 2

    model = args.model or "(auto-detect)"
    message = (
        f"{APP_NAME} build is not yet implemented in the x86 CLI. "
        f"Requested model: {model}. "
        "Use `python -m x86 wizard` for the guided EFI build flow."
    )
    if args.json:
        _emit_json({"status": "not_implemented", "message": message, "model": model})
    else:
        logging.warning(message)
    return 2


def cmd_patch(args: argparse.Namespace) -> int:
    from x86.patch.root import apply, preflight, unpatch
    operation = unpatch if args.unpatch else apply if args.apply else preflight
    result = operation(
        args.profile,
        args.payload_dir,
        mode=args.mode,
        deployment=args.mellow,
        mellow_payload=args.mellow_payload,
        efi=args.efi,
        abstraction_manifest=args.abstraction_manifest,
    )
    _emit_json(result)
    return 0 if result.get("ok") else 2


def cmd_mellow(args: argparse.Namespace) -> int:
    from x86.mellow.integration import plan, prepare_efi
    try:
        options = {"mode": args.mode, "payload_dir": args.payload, "efi": args.efi}
        if args.operation in ("prepare-efi", "prepare-root-efi"):
            result = prepare_efi(output=args.output, deployment="root-patch" if args.operation == "prepare-root-efi" else "efi", **options)
        else:
            result = plan(deployment=args.deployment, **options)
    except (ValueError, OSError, KeyError) as exc:
        result = {"ok": False, "status": "mellow_rejected", "error": str(exc)}

    _emit_json(result)
    return 0 if result.get("ok") else 2


def cmd_surface(args: argparse.Namespace) -> int:
    from x86.surface import profile_info, validate_efi
    result = validate_efi(args.efi) if args.efi else {"ok": True, "profile": profile_info()}
    _emit_json(result)
    return 0 if result.get("ok") else 2


def _patch_status_payload() -> dict[str, Any]:
    if not is_macos():
        return {
            "platform": platform_label(),
            "host_is_mac": False,
            "error": MACOS_ONLY_MESSAGE,
            "can_patch": False,
            "can_unpatch": False,
            "patches_available": [],
        }

    from opencore_legacy_patcher import constants as constants_module
    from opencore_legacy_patcher.detections import device_probe, os_probe
    from opencore_legacy_patcher.sys_patch.patchsets import (
        HardwarePatchsetDetection,
        HardwarePatchsetValidation,
    )
    from x86.pre_avx.detect import build_detect_fields, serialize_detect_fields
    from x86.settings import SettingsStore

    global_constants = constants_module.Constants()
    os_data = os_probe.OSProbe()
    global_constants.detected_os = os_data.detect_kernel_major()
    global_constants.detected_os_build = os_data.detect_os_build()
    global_constants.detected_os_version = os_data.detect_os_version()
    global_constants.computer = device_probe.Computer.probe()

    patchset = HardwarePatchsetDetection(
        constants=global_constants,
        validation=True,
    )
    patches = patchset.device_properties

    active = [
        patch_name.split(": ", 1)[1]
        for patch_name in patches
        if patches[patch_name] is True
        and not patch_name.startswith("Validation")
        and not patch_name.startswith("Settings")
        and not patch_name.startswith("Graphics Policy")
    ]
    validations = {
        key.split("Validation: ", 1)[1]: value
        for key, value in patches.items()
        if key.startswith("Validation:")
    }

    model = global_constants.custom_model or global_constants.computer.real_model
    auto_pre_avx_patch = SettingsStore().read("auto_pre_avx_patch", True)
    cpu_features = None
    cpu_leaf7_features = None
    if getattr(global_constants.computer, "cpu", None) is not None:
        cpu_features = getattr(global_constants.computer.cpu, "flags", None)
        cpu_leaf7_features = getattr(global_constants.computer.cpu, "leafs", None)

    detect_fields = serialize_detect_fields(
        build_detect_fields(
            model,
            gpus=getattr(global_constants.computer, "gpus", None),
            cpu_features=cpu_features,
            cpu_leaf7_features=cpu_leaf7_features,
            auto_pre_avx_patch=bool(auto_pre_avx_patch),
            xnu_major=global_constants.detected_os,
        )
    )

    return {
        "model": model,
        "os_version": global_constants.detected_os_version,
        "os_build": global_constants.detected_os_build,
        "last_patched_version": global_constants.computer.oclp_sys_version,
        "last_patched_date": global_constants.computer.oclp_sys_date,
        "patches_available": active,
        "can_patch": not patches.get(HardwarePatchsetValidation.PATCHING_NOT_POSSIBLE, False),
        "can_unpatch": not patches.get(HardwarePatchsetValidation.UNPATCHING_NOT_POSSIBLE, False),
        "validations": validations,
        "graphics_policy_warnings": patchset.graphics_policy_warnings,
        **detect_fields,
    }


def cmd_status(args: argparse.Namespace) -> int:
    store = SettingsStore()
    settings = store.load()
    payload: dict[str, Any] = {
        "platform": platform_label(),
        "host_is_mac": is_macos(),
        "settings": settings,
        "config_path": str(store.config_path),
    }

    try:
        payload["patch"] = _patch_status_payload()
    except Exception as error:
        logging.debug("Patch status unavailable: %s", error)
        payload["patch"] = {"error": str(error)}

    if args.json:
        _emit_json(payload)
    else:
        logging.info("26x86 상태 요약")
        logging.info("  플랫폼: %s", platform_label())
        logging.info("  설정 파일: %s", store.config_path)
        last_detect = settings.get("last_detect")
        if last_detect:
            logging.info("  마지막 감지: %s", last_detect)
        patch = payload.get("patch") or {}
        if patch.get("model"):
            logging.info("  모델: %s", patch["model"])
            logging.info(
                "  macOS: %s (%s)",
                patch.get("os_version") or "N/A",
                patch.get("os_build") or "N/A",
            )
            if patch.get("last_patched_version"):
                logging.info(
                    "  마지막 패치: %s (%s)",
                    patch["last_patched_version"],
                    patch.get("last_patched_date") or "N/A",
                )
            if "can_patch" in patch:
                logging.info("  패치 가능: %s", "예" if patch.get("can_patch") else "아니오")
        elif not is_macos():
            logging.info("  패치 상태: macOS 전용 (현재 호스트에서는 사용 불가)")
    return 0


def cmd_wizard(args: argparse.Namespace) -> int:
    _ensure_repo_on_path()
    if args.mode:
        from x86.execution import resolve_execution
        os.environ["X86_EXECUTION_MODE"] = resolve_execution(args.mode).mode.value
    if args.profile:
        os.environ["X86_TARGET_PROFILE"] = args.profile
    if args.efi:
        os.environ["X86_SURFACE_EFI"] = args.efi

    try:
        from x86.gui.launch import launch_wizard
    except ImportError:
        launch_wizard = None

    if launch_wizard is not None:
        launch_wizard(advanced=args.advanced)
        return 0

    if not is_macos():
        logging.error(
            "GUI를 시작할 수 없습니다. Tauri 셸을 빌드하거나 "
            "`pip install pywebview wxpython` (폴백) / `X86_GUI_BACKEND=qt`용 PySide6를 확인하세요. "
            "Tauri: cd gui-tauri && cargo tauri build"
        )
        return 1

    from opencore_legacy_patcher.application_entry import main as oclp_main

    argv = [sys.argv[0]]
    if args.advanced or os.environ.get("X86_ADVANCED") == "1":
        argv.append("--advanced_gui")
    sys.argv = argv
    oclp_main()
    return 0


def cmd_assets(args: argparse.Namespace) -> int:
    # Keep the proven internal namespace while exposing the 26x86 command.
    from research.venfire.venfire.artifacts import create_manifest, write_manifest, load_manifest, verify_manifest
    from research.venfire.venfire.media import inspect_restore
    try:
        if args.asset_action == "inspect-restore":
            result = inspect_restore(args.path, hash_archive=args.sha256)
        elif args.asset_action == "manifest":
            manifest = create_manifest(args.files)
            write_manifest(manifest, args.output)
            result = manifest.to_dict()
        else:
            result = verify_manifest(load_manifest(args.path)).to_dict()
        _emit_json(result)
        return 0 if result.get("valid", True) else 2
    except (ValueError, OSError) as exc:
        _emit_json({"ok": False, "error": str(exc)})
        return 2


def cmd_vsk(args: argparse.Namespace) -> int:
    from x86.vsk_config import load_config
    # ASCII JSON is valid UTF-8 on Windows pipes regardless of the console code
    # page; JSON decoding restores Unicode config strings without data loss.
    def emit(result):
        print(json.dumps(result, ensure_ascii=True, indent=2))
    try:
        result = load_config(args.config)
        emit({"ok": True, **result})
        return 0
    except (ValueError, OSError) as exc:
        emit({"ok": False, "error": str(exc), "boot_authorized": False,
              "validation_level": "UNIT"})
        return 2


def cmd_sandbox(args: argparse.Namespace) -> int:
    from x86.sandbox import plan, prepare, prepare_vsk
    try:
        if args.config:
            from x86.sandbox_config import read
            result = read(args.config)
        elif args.vsk_bundle or args.trusted_public_key or args.vsk_efi:
            if not args.output or not args.vsk_bundle or not args.trusted_public_key:
                raise ValueError("VSK staging requires --output, --vsk-bundle and --trusted-public-key")
            result = prepare_vsk(args.target, args.output, args.vsk_bundle,
                                 args.trusted_public_key, efi_path=args.vsk_efi)
        else:
            result = prepare(args.target, args.output) if args.output else plan(args.target)
    except (ValueError, OSError) as exc:
        _emit_json({"ok": False, "error": str(exc)})
        return 1
    _emit_json(result)
    return 0 if result.get("ok") else 2


def cmd_vmapple(args: argparse.Namespace) -> int:
    from x86.vmapple import (
        VMappleConfig,
        apple_silicon_profile,
        configured_from_environment,
        inspect_macosvm_storage,
        inspect_storage,
        provision_macosvm,
        run,
    )

    if args.vmapple_action == "status":
        _emit_json(configured_from_environment())
        return 0
    if args.vmapple_action == "capabilities":
        _emit_json(apple_silicon_profile())
        return 0
    if args.vmapple_action == "provision":
        try:
            result = provision_macosvm(
                macosvm=args.macosvm,
                ipsw=args.ipsw,
                output=args.output,
                disk_size=args.disk_size,
                timeout=args.timeout,
            )
        except (ValueError, OSError, TimeoutError, RuntimeError) as exc:
            _emit_json({
                "ok": False,
                "error": str(exc),
                "provisioning_completed": False,
            })
            return 2
        _emit_json({"ok": True, **result})
        return 0
    if args.vmapple_action == "inspect-storage":
        try:
            if args.vm_json:
                result = inspect_macosvm_storage(args.vm_json)
            else:
                result = inspect_storage(
                    aux=args.aux,
                    root=args.root,
                    aux_offset=args.aux_offset,
                )
        except (ValueError, OSError) as exc:
            _emit_json({"ok": False, "error": str(exc), "installer_ui_verified": False})
            return 2
        _emit_json(result)
        # A definite zero fixture is a known blocker.  A non-zero image still
        # needs a hardware-model provisioning receipt, so it is reported as
        # unverified rather than being advertised as bootable.
        return 2 if result.get("provisioned") is False else 0

    config = VMappleConfig(
        target_major=args.target,
        qemu=args.qemu,
        firmware=args.firmware,
        ibss=args.ibss,
        ibec=args.ibec,
        aux=args.aux,
        root=args.root,
        output=args.output,
        vm_json=args.vm_json,
        qemu_img=args.qemu_img,
        display=args.display,
        uuid=args.uuid,
        aux_offset=args.aux_offset,
        memory_mib=args.memory_mib,
        smp=args.smp,
        transition_timeout=args.transition_timeout,
        duration=args.duration,
        research_only=args.research_only,
        build_manifest=args.build_manifest,
        tss_helper=args.tss_helper,
        original_ibss=args.original_ibss,
        original_ibec=args.original_ibec,
        live_personalize=args.live_personalize,
        optional_rpc_unavailable=args.optional_rpc_unavailable,
        restore_chain=args.restore_chain,
        restore_role_dir=args.restore_role_dir,
        restore_timeout=args.restore_timeout,
        machine_type=args.machine_type,
        guest_os=args.guest_os,
        recovery_protocol=args.recovery_protocol,
        recovery_image_name=args.recovery_image_name,
        boot_picker_enabled=args.boot_picker_enabled,
        boot_delay_seconds=args.boot_delay,
        boot_selection=args.boot_selection,
        boot_picker_trigger=args.boot_picker_trigger,
    )
    try:
        result = run(config)
    except (ValueError, OSError, TimeoutError, RuntimeError) as exc:
        if args.json:
            payload: dict[str, Any] = {"ok": False, "error": str(exc), "macos_boot_verified": False}
            policy = getattr(exc, "to_dict", None)
            if callable(policy):
                payload["policy_error"] = policy()
            _emit_json(payload)
        else:
            logging.error("VMApple launch failed: %s", exc)
        return 2
    _emit_json(result)
    return 0 if result.get("error") is None else 2


def cmd_personality(args: argparse.Namespace) -> int:
    """Validate the iBoot guest/recovery scope without touching any inputs."""
    from x86.iboot_personality import IbootScopeError, policy_matrix, validate_iboot_scope

    try:
        report = validate_iboot_scope(
            args.machine_type,
            args.guest_os,
            recovery_protocol=args.recovery_protocol,
            recovery_image_name=args.recovery_image_name,
            recovery_enabled=args.recovery_enabled,
            target_major=args.target,
        )
    except IbootScopeError as exc:
        _emit_json({"ok": False, "error": str(exc), "policy_error": exc.to_dict(),
                    "policy_matrix": policy_matrix()})
        return 2
    _emit_json({"ok": True, **report, "policy_matrix": policy_matrix()})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="x86",
        description=f"{APP_NAME} — x86 Mac OpenCore EFI build and root patch tooling",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    vsk = subparsers.add_parser("vsk", help="Validate VSK configuration offline; never authorize boot")
    vsk.add_argument("--config", required=True, help="Strict UTF-8 XML VSK config.plist")
    vsk.set_defaults(handler=cmd_vsk)

    assets = subparsers.add_parser("assets", help="Read-only original guest asset inspection and integrity")
    asset_commands = assets.add_subparsers(dest="asset_action", required=True)
    inspect = asset_commands.add_parser("inspect-restore", help="Inspect original IPSW BuildManifest in place")
    inspect.add_argument("path")
    inspect.add_argument("--sha256", action="store_true")
    inspect.set_defaults(handler=cmd_assets)
    manifest = asset_commands.add_parser("manifest", help="Record immutable input hashes")
    manifest.add_argument("--output", required=True)
    manifest.add_argument("files", nargs="+")
    manifest.set_defaults(handler=cmd_assets)
    verify = asset_commands.add_parser("verify", help="Verify recorded inputs")
    verify.add_argument("path")
    verify.set_defaults(handler=cmd_assets)

    sandbox = subparsers.add_parser("sandbox", help="Apple Silicon Sandbox EFI status and self-test staging")
    sandbox.add_argument("--target", type=int, choices=[26, 27], default=26)
    sandbox_mode = sandbox.add_mutually_exclusive_group()
    sandbox_mode.add_argument("--output", help="Stage EFI self-test or authenticated VSK inputs into a new folder")
    sandbox_mode.add_argument("--config", help="Validate OpenCore Sandbox config.plist without writes")
    sandbox.add_argument("--vsk-bundle", help="Signed VSK bundle directory for authenticated staging")
    sandbox.add_argument("--trusted-public-key", help="External raw32 VSK Ed25519 public key")
    sandbox.add_argument("--vsk-efi", help="Production VSKBOOT.EFI path (defaults to the local build receipt)")
    sandbox.add_argument("--json", action="store_true")
    sandbox.set_defaults(handler=cmd_sandbox)

    vmapple = subparsers.add_parser(
        "vmapple",
        help="Run the caller-supplied VMApple research VM with a visible GTK/SDL window",
    )
    vmapple_actions = vmapple.add_subparsers(dest="vmapple_action", required=True)
    vmapple_status = vmapple_actions.add_parser(
        "status", help="Show configured VMApple paths without launching a guest"
    )
    vmapple_status.set_defaults(handler=cmd_vmapple)
    vmapple_capabilities = vmapple_actions.add_parser(
        "capabilities",
        help="Show the qemu-t8030-derived Apple Silicon device profile without launching a guest",
    )
    vmapple_capabilities.set_defaults(handler=cmd_vmapple)
    vmapple_provision = vmapple_actions.add_parser(
        "provision",
        help="Provision a new Virtualization.framework macOS VM bundle on Apple Silicon macOS",
    )
    vmapple_ipsw = os.environ.get("X86_VMAPLE_IPSW")
    vmapple_provision.add_argument(
        "--macosvm", default=os.environ.get("X86_MACOSVM"),
        help="macosvm executable (or X86_MACOSVM)",
    )
    vmapple_provision.add_argument(
        "--ipsw", default=vmapple_ipsw, required=not bool(vmapple_ipsw),
        help="caller-supplied macOS IPSW; never downloaded or modified by 26x86",
    )
    vmapple_provision.add_argument(
        "--output", default=os.environ.get("X86_VMAPLE_PROVISION_OUTPUT"),
        help="new output directory; existing directories are rejected",
    )
    vmapple_provision.add_argument(
        "--disk-size", default="32g",
        help="macosvm sparse disk size, for example 32g (maximum 4t)",
    )
    vmapple_provision.add_argument(
        "--timeout", type=float, default=86400.0,
        help="provisioning timeout in seconds (maximum 172800)",
    )
    vmapple_provision.add_argument("--json", action="store_true")
    vmapple_provision.set_defaults(handler=cmd_vmapple)
    vmapple_inspect_storage = vmapple_actions.add_parser(
        "inspect-storage",
        help="Read-only AUX/root readiness inspection; never starts QEMU or writes inputs",
    )
    vmapple_inspect_storage.add_argument(
        "--aux", default=os.environ.get("X86_VMAPLE_AUX", ""), required=False,
        help="AUX raw image (or use --vm-json)",
    )
    vmapple_inspect_storage.add_argument(
        "--root", default=os.environ.get("X86_VMAPLE_ROOT", ""), required=False,
        help="root raw image",
    )
    vmapple_inspect_storage.add_argument(
        "--aux-offset", type=lambda value: int(value, 0), default=0,
        help="AUX metadata offset in bytes (512-byte aligned)",
    )
    vmapple_inspect_storage.add_argument(
        "--vm-json", default=os.environ.get("X86_VMAPLE_JSON", ""),
        help="macosvm.json; applies the documented 0x4000-byte AUX metadata trim",
    )
    vmapple_inspect_storage.add_argument("--json", action="store_true")
    vmapple_inspect_storage.set_defaults(handler=cmd_vmapple)
    vmapple_run = vmapple_actions.add_parser(
        "run", help="Launch VMApple direct macOS or Recovery mode and record observed boot boundaries"
    )
    vmapple_run.add_argument("--target", type=int, choices=[26, 27], default=27)
    vmapple_run.add_argument("--qemu", default=os.environ.get("X86_VMAPLE_QEMU"))
    vmapple_run.add_argument("--qemu-img", default=os.environ.get("X86_VMAPLE_QEMU_IMG"))
    vmapple_run.add_argument("--firmware", default=os.environ.get("X86_VMAPLE_AVPBOOTER", ""))
    vmapple_run.add_argument(
        "--vm-json", default=os.environ.get("X86_VMAPLE_JSON", ""),
        help="macosvm.json; atomically supplies ECID, hardwareModel, AUX, and root paths",
    )
    vmapple_run.add_argument("--ibss", default=os.environ.get("X86_VMAPLE_IBSS", ""))
    vmapple_run.add_argument("--ibec", default=os.environ.get("X86_VMAPLE_IBEC"))
    vmapple_run.add_argument("--aux", default=os.environ.get("X86_VMAPLE_AUX", ""))
    vmapple_run.add_argument("--root", default=os.environ.get("X86_VMAPLE_ROOT", ""))
    vmapple_run.add_argument("--output", default=os.environ.get("X86_VMAPLE_OUTPUT"))
    vmapple_run.add_argument(
        "--display", choices=["auto", "gtk", "sdl", "cocoa", "none", "dbus"], default="auto",
        help="Display backend; auto selects Cocoa on native Apple Silicon and headless on research hosts",
    )
    vmapple_run.add_argument("--uuid", type=lambda value: int(value, 0), default=0)
    vmapple_run.add_argument("--aux-offset", type=lambda value: int(value, 0), default=0)
    vmapple_run.add_argument("--memory-mib", type=int, default=4096)
    vmapple_run.add_argument("--smp", type=int, default=2)
    vmapple_run.add_argument("--transition-timeout", type=float, default=300.0)
    vmapple_run.add_argument("--duration", type=float)
    vmapple_run.add_argument(
        "--build-manifest", default=os.environ.get("X86_VMAPLE_BUILD_MANIFEST"),
        help="Official BuildManifest.plist; required for --live-personalize",
    )
    vmapple_run.add_argument(
        "--tss-helper", default=os.environ.get("X86_VMAPLE_TSS_HELPER"),
        help="Local libtatsu-compatible TSS request encoder",
    )
    vmapple_run.add_argument(
        "--original-ibss", default=os.environ.get("X86_VMAPLE_ORIGINAL_IBSS"),
        help="Unchanged Apple iBSS IM4P; never modified by the runner",
    )
    vmapple_run.add_argument(
        "--original-ibec", default=os.environ.get("X86_VMAPLE_ORIGINAL_IBEC"),
        help="Unchanged Apple iBEC IM4P; never modified by the runner",
    )
    vmapple_run.add_argument(
        "--live-personalize", action="store_true",
        help="Request fresh Apple TSS tickets for the live USB nonce",
    )
    vmapple_run.add_argument(
        "--optional-rpc-unavailable", action="store_true",
        help="Opt into the negative optional-RPC experiment (normally omitted)",
    )
    vmapple_run.add_argument(
        "--restore-chain", action="store_true",
        help="After a real Stage2 prompt, send the official restore-role sequence",
    )
    vmapple_run.add_argument(
        "--restore-role-dir", default=os.environ.get("X86_VMAPLE_RESTORE_ROLE_DIR"),
        help="Directory containing unchanged Restore*.im4p role inputs",
    )
    vmapple_run.add_argument(
        "--restore-timeout", type=float, default=900.0,
        help="Bounded timeout for the Stage2 restore-role sequence",
    )
    vmapple_run.add_argument("--machine-type", default="iBoot(AArch64)")
    vmapple_run.add_argument("--guest-os", default="macOS",
                             help="iBoot guest scope; only macOS is accepted")
    vmapple_run.add_argument("--recovery-protocol", default="DFU/IPSW",
                             help="iBoot recovery scope: Auto, DFU, IPSW or DFU/IPSW")
    vmapple_run.add_argument("--recovery-image-name", default="_default.ipsw",
                             help="macOS Local Recovery image name")
    vmapple_run.add_argument(
        "--boot-selection", choices=["macos", "recovery"], default="recovery",
        help="BootPicker entry after the two-second gate (macos uses provisioned AUX/root; recovery uploads iBSS)",
    )
    vmapple_run.add_argument(
        "--boot-delay", type=float, default=2.0,
        help="Fixed BootPicker delay; only 2 seconds is accepted",
    )
    vmapple_run.add_argument(
        "--boot-picker-trigger", default="cli",
        help="Audited selection source, for example alt-enter or runner-default-recovery",
    )
    vmapple_run.add_argument(
        "--no-boot-picker", dest="boot_picker_enabled", action="store_false",
        help="Disable the two-second gate for a control-plane experiment",
    )
    vmapple_run.set_defaults(boot_picker_enabled=True)
    vmapple_run.add_argument(
        "--research-only", action="store_true", required=True,
        help="Required acknowledgement that this is a non-redistributable research run",
    )
    vmapple_run.add_argument("--json", action="store_true")
    vmapple_run.set_defaults(handler=cmd_vmapple)

    personality = subparsers.add_parser(
        "personality", help="Validate the iBoot(AArch64) macOS-only guest policy"
    )
    personality_action = personality.add_subparsers(dest="personality_action", required=True)
    personality_validate = personality_action.add_parser(
        "validate", help="Check guest and DFU/IPSW recovery scope without I/O"
    )
    personality_validate.add_argument("--machine-type", default="iBoot(AArch64)")
    personality_validate.add_argument("--guest-os", default="macOS")
    personality_validate.add_argument("--recovery-protocol", default="Auto")
    personality_validate.add_argument("--recovery-image-name", default="_default.ipsw")
    personality_validate.add_argument("--target", type=int, choices=[26, 27], default=27)
    personality_validate.add_argument("--recovery-enabled", action="store_true")
    personality_validate.set_defaults(handler=cmd_personality)

    detect = subparsers.add_parser("detect", help="Mac 모델 및 하드웨어 정보 확인")
    detect.add_argument("--json", action="store_true", help="JSON 형식으로 결과 출력")
    detect.add_argument("--model", help="(비-macOS) 대상 Mac 모델을 수동 지정 (예: iMac18,3)")
    detect.set_defaults(handler=cmd_detect)

    build = subparsers.add_parser("build", help="OpenCore EFI 빌드 (macOS 전용)")
    build.add_argument("--mode", choices=["x86", "apple-silicon-sandbox"])
    build.add_argument("--model", help="대상 Mac 모델 (예: iMac18,3)")
    build.add_argument("--json", action="store_true", help="JSON 형식으로 결과 출력")
    build.set_defaults(handler=cmd_build)

    patch = subparsers.add_parser("patch", help="루트 볼륨 패치 적용 (macOS 전용)")
    patch.add_argument("--auto", action="store_true", help="호환 옵션; --apply 없이는 사전 검사만 실행")
    mode = patch.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="설치된 macOS의 루트 패치 실행 (sudo 필요)")
    mode.add_argument("--preflight", action="store_true", help="읽기 전용 사전 검사 (기본)")
    mode.add_argument("--unpatch", action="store_true", help="APFS 패치 및 Mellow Data 파일 복원 (sudo 필요)")
    patch.add_argument("--profile", choices=["surface-pro6-i5-tahoe"])
    patch.add_argument("--payload-dir", help="Universal-Binaries.dmg를 포함한 payloads 디렉터리")
    patch.add_argument("--mode", choices=["x86", "apple-silicon-sandbox"])
    patch.add_argument("--mellow", choices=["disabled", "efi", "root-patch"])
    patch.add_argument("--mellow-payload", help="검증된 Mellow manifest 디렉터리")
    patch.add_argument("--efi", help="실제 대상 OpenCore EFI 경로 (중복 주입 검사)")
    patch.add_argument("--abstraction-manifest", help="Exact OS build / architecture abstraction-binary manifest")
    patch.add_argument("--json", action="store_true", help="JSON 형식으로 결과 출력")
    patch.set_defaults(handler=cmd_patch)

    mellow = subparsers.add_parser("mellow", help="Mellow driver/root-patch 준비 및 검증")
    mellow_ops = mellow.add_subparsers(dest="operation", required=True)
    for operation in ("plan", "prepare-efi", "prepare-root-efi"):
        command = mellow_ops.add_parser(operation)
        command.add_argument("--mode", choices=["x86", "apple-silicon-sandbox"])
        command.add_argument("--payload", help="Mellow manifest 디렉터리")
        command.add_argument("--efi", required=True, help="OpenCore EFI 입력 경로")
        if operation in ("prepare-efi", "prepare-root-efi"):
            command.add_argument("--output", required=True, help="새 EFI 출력 디렉터리")
        else:
            command.add_argument("--deployment", choices=["efi", "root-patch"], default="root-patch")
        command.set_defaults(handler=cmd_mellow)

    surface = subparsers.add_parser("surface", help="Surface Pro 6 Tahoe EFI 읽기 전용 검사 (모든 OS)")
    surface.add_argument("--efi", help="EFI 디렉터리 또는 이를 포함한 폴더")
    surface.add_argument("--json", action="store_true")
    surface.set_defaults(handler=cmd_surface)

    status = subparsers.add_parser("status", help="설정·패치·EFI 상태 요약")
    status.add_argument("--json", action="store_true", help="JSON 형식으로 결과 출력")
    status.set_defaults(handler=cmd_status)

    wizard = subparsers.add_parser("wizard", help="기본 GUI 마법사 실행")
    wizard.add_argument("--mode", choices=["x86", "apple-silicon-sandbox"])
    wizard.add_argument("--profile", choices=["surface-pro6-i5-tahoe"])
    wizard.add_argument("--efi", help="Surface EFI 검사 경로 미리 입력 (자동 기록 없음)")
    wizard.add_argument(
        "--advanced",
        action="store_true",
        help="고급 GUI (X86_ADVANCED=1 과 동일, macOS 전용)",
    )
    wizard.set_defaults(handler=cmd_wizard)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()

    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    setup_logging(verbose=os.environ.get("X86_VERBOSE") == "1")
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
