"""
Python ↔ JS bridge backend for the HTML hybrid wizard.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any, Optional

from opencore_legacy_patcher.datasets import smbios_data
from opencore_legacy_patcher.datasets.os_data import os_conversion
from opencore_legacy_patcher.datasets import os_data as os_data_module

from x86.cli import _patch_status_payload, _serialize_detect_payload, _sw_vers
from x86.gui import bootstrap
from x86.gui.branding import (
    is_advanced_gui_enabled,
    logo_png_path,
    logo_svg_path,
    resolve_gui_logo_path,
    window_title,
)
from x86.gui.wizard import errors, strings
from x86.manifest import APP_NAME, BUNDLE_ID, COPYRIGHT, PATCHER_VERSION, URL_GUIDE
from x86.platform import MACOS_ONLY_MESSAGE, is_macos, reveal_in_file_manager
from x86.settings import SettingsStore


MACOS_CHOICES: list[dict[str, Any]] = [
    {"label": "macOS Ventura (13)", "kernel": os_data_module.os_data.ventura},
    {"label": "macOS Sonoma (14)", "kernel": os_data_module.os_data.sonoma},
    {"label": "macOS Sequoia (15)", "kernel": os_data_module.os_data.sequoia},
    {"label": "macOS Tahoe (26)", "kernel": os_data_module.os_data.tahoe},
]

WEB_STEPS: list[dict[str, str]] = [
    {
        "id": "welcome",
        "title": "시작",
        "heading": "26x86에 오신 것을 환영합니다",
        "desc": "오래된 Mac에서 최신 macOS를 사용할 수 있도록 단계별로 안내합니다.",
    },
    {
        "id": "detect",
        "title": "1. 내 Mac 확인",
        "heading": strings.STEP_DETECT_HEADING,
        "desc": strings.STEP_DETECT_DESC,
    },
    {
        "id": "build",
        "title": "2. 패치 생성",
        "heading": strings.STEP_BUILD_HEADING,
        "desc": strings.STEP_BUILD_DESC,
    },
    {
        "id": "patch",
        "title": "3. 설치·패치",
        "heading": strings.STEP_ROOT_HEADING,
        "desc": f"{strings.STEP_INSTALL_DESC}\n{strings.STEP_ROOT_DESC}",
    },
    {
        "id": "done",
        "title": "4. 완료",
        "heading": "설정이 완료되었습니다",
        "desc": "EFI를 설치하고 macOS를 부팅한 뒤, 필요하면 루트 패치를 적용하세요.",
    },
]


class WizardBridge:
    """Backend API consumed by pywebview and headless smoke tests."""

    def __init__(self) -> None:
        self._settings = SettingsStore()
        self._selected_target_os: Optional[int] = None
        self._build_completed = False

    def _hardware_profile(self):
        return os.environ.get("X86_TARGET_PROFILE") or self._settings.read("hardware_profile")

    def _constants(self):
        from .execution_settings import effective
        selection = effective(self._settings.load())
        if selection.get("execution_error"):
            # An invalid saved native mode must not strand the mode selector.
            # This object is for labels only and never starts a native probe.
            from opencore_legacy_patcher.constants import Constants
            from types import SimpleNamespace
            c = Constants()
            c.computer = SimpleNamespace(real_model="Execution configuration needs correction",
                                         build_model="Execution configuration needs correction")
            c.detected_os, c.detected_os_minor = 25, 0
            c.detected_os_build = c.detected_os_version = ""
            c.execution_mode = selection["execution"]["mode"]
            c.gui_mode, c.cli_mode = True, False
            c.launcher_binary = sys.executable
            c.launcher_script = str(bootstrap.ensure_repo_on_path() / "26x86.py")
            return c
        # Viewing or changing modes must not race an old payload-mount thread.
        # Native action workers request unpacking only after their own guard.
        return bootstrap.get_constants(start_unpack=False, settings=self._settings.load())

    def _configuration(self):
        from x86.mellow.integration import configuration
        return configuration(settings=self._settings.load())

    def get_app_info(self) -> dict[str, Any]:
        from .execution_settings import effective
        selection = effective(self._settings.load())
        c = self._constants()
        logo = resolve_gui_logo_path(c.icns_resource_path)
        logo_url = self._logo_data_uri(logo)
        if logo_url is None and logo_svg_path().exists():
            logo_url = self._logo_data_uri(logo_svg_path())

        return {
            "app_name": APP_NAME,
            "bundle_id": BUNDLE_ID,
            "version": PATCHER_VERSION,
            "copyright": COPYRIGHT,
            "title": window_title(PATCHER_VERSION),
            "guide_link": URL_GUIDE,
            "logo_url": logo_url,
            "advanced_enabled": is_advanced_gui_enabled() and selection["execution"]["can_native_apply"],
            "host_is_mac": is_macos(),
            "macos_only_message": None if is_macos() else MACOS_ONLY_MESSAGE,
            "status_ready": strings.STATUS_READY,
            "hardware_profile": self._hardware_profile(),
            "profile_locked": bool(os.environ.get("X86_TARGET_PROFILE")),
            "surface_efi_path": os.environ.get("X86_SURFACE_EFI", ""),
            **selection,
        }

    def set_hardware_profile(self, profile: Optional[str] = None) -> dict[str, Any]:
        from x86.surface import PROFILE_ID, profile_info
        if profile not in (None, PROFILE_ID):
            return {"ok": False, "error": "Unknown hardware profile"}
        if os.environ.get("X86_TARGET_PROFILE") and profile != os.environ["X86_TARGET_PROFILE"]:
            return {"ok": False, "error": "이 실행 파일은 Surface 대상 모드로 시작되었습니다."}
        data = self._settings.load()
        data["hardware_profile"] = profile
        self._settings.save(data)
        return {"ok": True, "profile": profile_info() if profile else None}

    def validate_surface_efi(self, path: str) -> dict[str, Any]:
        from x86.surface import validate_efi
        return validate_efi(path)

    def get_steps(self) -> list[dict[str, str]]:
        return WEB_STEPS

    def get_macos_choices(self) -> list[dict[str, Any]]:
        c = self._constants()
        current_kernel = c.detected_os
        choices = []
        default_idx = 2
        for i, item in enumerate(MACOS_CHOICES):
            if item["kernel"] == current_kernel:
                default_idx = i
            choices.append(
                {
                    "label": item["label"],
                    "kernel": item["kernel"],
                    "marketing": os_conversion.convert_kernel_to_marketing_name(item["kernel"]),
                }
            )

        if self._selected_target_os is None:
            self._selected_target_os = MACOS_CHOICES[default_idx]["kernel"]

        model = c.custom_model or c.computer.real_model
        max_os = smbios_data.smbios_dictionary.get(model, {}).get("Max OS Supported")
        recommended = None
        if max_os is not None:
            recommended = os_conversion.convert_kernel_to_marketing_name(max_os)

        return {
            "choices": choices,
            "default_index": default_idx,
            "selected_kernel": self._selected_target_os,
            "current_marketing": os_conversion.convert_kernel_to_marketing_name(current_kernel),
            "recommended": recommended,
        }

    def set_target_os(self, kernel: int) -> dict[str, Any]:
        self._selected_target_os = int(kernel)
        label = next(
            (item["label"] for item in MACOS_CHOICES if item["kernel"] == kernel),
            str(kernel),
        )
        return {"ok": True, "selected_kernel": kernel, "label": label}

    def detect(self, refresh: bool = False) -> dict[str, Any]:
        try:
            context, _, _, _ = self._configuration()
        except ValueError as exc:
            return {"ok": True, "detect": {"model": "Execution configuration needs correction",
                "host_is_mac": is_macos(), "native_device_probe": False, "error": str(exc)}}
        if not context.can_native_apply and is_macos():
            label = "Apple Silicon Sandbox" if context.is_sandbox else "Native host verification unavailable"
            return {"ok": True, "detect": {"model": label, "host_is_mac": True,
                "execution": context.as_dict(), "native_device_probe": False,
                "marketing_name": label, "os_version": "", "os_build": ""}}
        c = self._constants()
        if refresh and is_macos():
            from opencore_legacy_patcher.detections import device_probe

            c.computer = device_probe.Computer.probe()
            if c.computer.build_model is None:
                c.computer.build_model = c.computer.real_model

        payload = _serialize_detect_payload(c.computer)
        payload["os_version"] = payload.get("os_version") or c.detected_os_version or _sw_vers("productVersion")
        payload["os_build"] = payload.get("os_build") or c.detected_os_build or _sw_vers("buildVersion")
        payload["marketing_name"] = smbios_data.smbios_dictionary.get(
            payload["model"], {}
        ).get("Marketing Name", payload["model"])

        payload["host_is_mac"] = is_macos()
        if not is_macos():
            payload["macos_only_note"] = MACOS_ONLY_MESSAGE

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
        self._settings.record_detect(payload["model"], extra=detect_extra)
        return {"ok": True, "detect": payload}

    def get_patch_status(self) -> dict[str, Any]:
        try:
            context, deployment, payload, efi = self._configuration()
            if context.is_sandbox:
                return {"ok": True, "execution": context.as_dict(),
                    "patch": {"can_patch": False, "can_unpatch": False, "patches_available": []},
                    "summary": "Apple Silicon Sandbox Mode · native kext 및 루트 패치 사용 불가. 가상 GPU 런타임은 아직 제공되지 않습니다."}
            if deployment == "root-patch":
                from x86.patch.root import preflight
                report = preflight(self._hardware_profile(), constants=self._constants())
                return {"ok": True, "execution": context.as_dict(), "patch": report,
                    "summary": "Mellow diagnostic root patch · GPU 가속 미검증\n" + "\n".join(
                        report.get("patches", []) + report.get("blockers", []) + [report.get("error") or ""])}
            if deployment == "efi":
                from x86.mellow.integration import plan
                report = plan(mode=context.mode.value, deployment=deployment, payload_dir=payload,
                              efi=efi, settings=self._settings.load())
                return {"ok": True, "execution": context.as_dict(), "patch": {"can_patch": False},
                    "summary": "Mellow EFI 준비 가능 · 새 출력 폴더에 생성합니다. 실제 부팅 및 Metal 가속은 미검증입니다."}
        except Exception as exc:
            return {"ok": False, "patch": {"can_patch": False}, "summary": str(exc), "error": str(exc)}
        from x86.surface import PROFILE_ID
        if self._hardware_profile() == PROFILE_ID:
            from x86.patch.root import preflight
            report = preflight(PROFILE_ID)
            summary = ["Surface Pro 6 · Tahoe · AppleHDA root patch"]
            summary.extend(report.get("patches", []))
            summary.extend(report.get("blockers", []))
            summary.extend(report.get("warnings", []))
            if report.get("kdk"):
                summary.append("KDK: " + str(report["kdk"].get("selected_build")) + " / macOS: " + str(report["kdk"].get("host_build")))
            if report.get("error"):
                summary.append(report["error"])
            summary.append("Surface EFI는 그대로 사용합니다. UHD 620에는 레거시 GPU 루트 패치를 적용하지 않습니다.")
            return {"ok": True, "patch": report, "summary": "\n".join(summary)}
        try:
            patch = _patch_status_payload()
            active = patch.get("patches_available") or []
            lines = []
            if patch.get("last_patched_version"):
                lines.append(f"{strings.STEP_ROOT_LAST}: {patch['last_patched_version']}")
            if active:
                lines.append("적용 가능한 패치:")
                lines.extend(f"• {name}" for name in active[:8])
                if len(active) > 8:
                    lines.append(f"… 외 {len(active) - 8}개")
            else:
                lines.append(strings.STEP_ROOT_NONE)

            if not patch.get("can_patch"):
                lines.append("현재 상태에서는 패치를 적용할 수 없습니다 (SIP 등 확인 필요).")

            for warning in patch.get("graphics_policy_warnings") or []:
                lines.append(f"⚠ {warning}")

            return {"ok": True, "patch": patch, "summary": "\n".join(lines)}
        except Exception as exc:
            logging.exception("patch status failed")
            return {"ok": False, "error": errors.user_message(exc), "summary": errors.user_message(exc)}

    def get_status(self) -> dict[str, Any]:
        from .execution_settings import effective
        settings = self._settings.load()
        patch_result = self.get_patch_status()
        return {
            "ok": True,
            "settings": settings,
            "config_path": str(self._settings.config_path),
            "patch": patch_result.get("patch"),
            "build_completed": self._build_completed,
            "execution": effective(settings)["execution"],
        }

    def get_settings(self) -> dict[str, Any]:
        from .execution_settings import effective
        data = self._settings.load()
        data.setdefault("analytics", True)
        selection = effective(data)
        if selection["execution"]["can_native_apply"]:
            from opencore_legacy_patcher.support import global_settings
            existing = global_settings.GlobalEnviromentSettings().read_property("EnableCrashAndAnalyticsReporting")
            if existing is not None:
                data["analytics"] = bool(existing)
        data.update(execution_mode=selection["execution"]["mode"],
            mellow_deployment=selection["mellow_deployment"], mellow_payload=selection["mellow_payload"],
            mellow_efi=selection["mellow_efi"])
        return {"ok": True, "settings": data, "config_path": str(self._settings.config_path)}

    def save_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            from .execution_settings import save_choice, effective
            saved = save_choice(self._settings, data)
            self._build_completed = False
            bootstrap.reset_constants()
            if "analytics" in data and self._configuration()[0].can_native_apply:
                from opencore_legacy_patcher.support import global_settings
                global_settings.GlobalEnviromentSettings().write_property("EnableCrashAndAnalyticsReporting", data["analytics"])
            return {"ok": True, "settings": saved, **effective(saved)}
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            logging.exception("save_settings failed")
            return {"ok": False, "error": errors.user_message(exc)}

    def prepare_mellow_efi(self, output: str) -> dict[str, Any]:
        try:
            context, deployment, payload, efi = self._configuration()
            context.require_native_plan("Mellow EFI preparation")
            if deployment != "efi":
                raise ValueError("Select Mellow EFI deployment in settings first")
            from x86.mellow.integration import prepare_efi
            return prepare_efi(efi, output, mode=context.mode.value, payload_dir=payload,
                               settings=self._settings.load())
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    def prepare_mellow_root_efi(self, source: str, output: str, payload: str) -> dict[str, Any]:
        """Prepare a separate disk-Lilu EFI before committing root-patch settings."""
        try:
            context, _, _, _ = self._configuration()
            context.require_native_plan("Mellow root-patch EFI preparation")
            from x86.mellow.integration import prepare_efi
            return prepare_efi(source, output, mode=context.mode.value, payload_dir=payload,
                               settings=self._settings.load(), deployment="root-patch")
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    def host_can_build(self) -> dict[str, Any]:
        try:
            context, _, _, _ = self._configuration()
            context.require_native_apply("Native EFI builder")
        except ValueError as exc:
            return {"ok": True, "can_build": False, "build_completed": False, "message": str(exc)}
        if not is_macos():
            return {
                "ok": True,
                "can_build": False,
                "build_completed": self._build_completed,
                "message": MACOS_ONLY_MESSAGE,
            }
        c = self._constants()
        from opencore_legacy_patcher.wx_gui import gui_support
        can_build = gui_support.CheckProperties(c).host_can_build()
        return {"ok": True, "can_build": bool(can_build), "build_completed": self._build_completed}

    def mark_build_completed(self) -> dict[str, Any]:
        self._build_completed = True
        return {"ok": True, "build_completed": True}

    def launch_wx_action(self, action: str) -> dict[str, Any]:
        """Spawn legacy wx UI for build/install/patch flows (separate process)."""
        allowed = {
            "build",
            "install",
            "patch",
            "unpatch",
            "model_change",
            "advanced",
            "help",
        }
        if action not in allowed:
            return {"ok": False, "error": f"Unknown action: {action}"}

        try:
            context, deployment, payload, efi = self._configuration()
            context.require_native_apply("Native wizard action")
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

        if not is_macos():
            return {"ok": False, "error": MACOS_ONLY_MESSAGE}

        if deployment == "root-patch" and action in ("patch", "unpatch") and (
                not hasattr(os, "geteuid") or os.geteuid() != 0):
            import shlex
            command = ["sudo", sys.executable] + (
                ["--x86-cli"] if getattr(sys, "frozen", False) else ["-m", "x86.cli"])
            command += ["patch",
                       "--apply" if action == "patch" else "--unpatch", "--mode", "x86",
                       "--mellow", "root-patch", "--mellow-payload", str(payload), "--efi", str(efi or "")]
            return {"ok": False, "needs_root": True, "command": command,
                "error": "Mellow 복원 저널은 관리자 권한의 전체 작업 프로세스가 필요합니다. "
                "저장한 설정으로 터미널에서 실행하세요: " + shlex.join(command)}

        from x86.surface import PROFILE_ID
        surface = self._hardware_profile() == PROFILE_ID
        if surface and action in ("build", "install", "model_change", "advanced"):
            return {"ok": False, "error": "Surface 전용 EFI를 사용하세요. Mac용 EFI 빌더로 덮어쓰지 않습니다."}
        if surface and action == "patch":
            from x86.patch.root import preflight
            report = preflight(PROFILE_ID)
            if not report.get("can_patch"):
                return {"ok": False, "error": report.get("error") or "\n".join(report.get("blockers") or [report["status"]])}

        if action == "advanced" and not is_advanced_gui_enabled():
            return {"ok": False, "error": strings.ERR_ADVANCED_DISABLED}

        if action == "build":
            check = self.host_can_build()
            if not check["can_build"]:
                return {
                    "ok": False,
                    "error": "이 Mac에서는 EFI를 만들 수 없습니다. 다른 지원 Mac에서 실행해 주세요.",
                }

        repo = bootstrap.ensure_repo_on_path()
        env = os.environ.copy()
        env.setdefault("X86_LEGACY_GUI", "1")
        env.update(X86_EXECUTION_MODE=context.mode.value, X86_MELLOW_DEPLOYMENT=deployment,
                   X86_MELLOW_PAYLOAD=str(payload), X86_MELLOW_EFI=str(efi or ""))
        if surface:
            env["X86_TARGET_PROFILE"] = PROFILE_ID
        if action == "advanced":
            env["X86_ADVANCED"] = "1"

        cmd = [sys.executable, "-m", "x86.gui.wx_runner", action]
        try:
            subprocess.Popen(
                cmd,
                cwd=str(repo),
                env=env,
                start_new_session=True,
            )
            return {"ok": True, "action": action, "spawned": True}
        except OSError as exc:
            logging.exception("wx_runner spawn failed")
            return {"ok": False, "error": errors.user_message(exc)}

    def reveal_log(self) -> dict[str, Any]:
        c = self._constants()
        log_path = getattr(c, "log_filepath", None) or str(c.app_support_path / "26x86.log")
        if reveal_in_file_manager(log_path):
            return {"ok": True, "path": log_path}
        return {"ok": False, "error": f"로그 파일을 열 수 없습니다: {log_path}"}

    def open_guide(self) -> dict[str, Any]:
        c = self._constants()
        webbrowser.open(c.guide_link)
        return {"ok": True, "url": c.guide_link}

    @staticmethod
    def _bundle_root() -> Optional[Path]:
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                return Path(meipass)
        return None

    @staticmethod
    def _logo_data_uri(path: Optional[Path]) -> Optional[str]:
        if path is None or not path.exists() or not path.is_file():
            return None
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            suffix = path.suffix.lower()
            mime = "image/svg+xml" if suffix == ".svg" else "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def web_root(self) -> Path:
        bundle_root = self._bundle_root()
        if bundle_root is not None:
            candidate = bundle_root / "x86" / "gui" / "web"
            if candidate.exists():
                return candidate
        return Path(__file__).resolve().parent / "web"

    def index_path(self) -> Path:
        index = self.web_root() / "index.html"
        if not index.exists():
            raise FileNotFoundError(f"Wizard HTML not found: {index}")
        return index.resolve()

    def index_uri(self) -> str:
        """Filesystem path for pywebview (not a file:// URI)."""
        return str(self.index_path())
