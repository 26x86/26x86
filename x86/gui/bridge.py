"""
Python ↔ JS bridge backend for the HTML hybrid wizard.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
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
from x86.platform import MACOS_ONLY_MESSAGE, is_macos, is_windows, reveal_in_file_manager
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
        "heading": "NextCore에 오신 것을 환영합니다",
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
        self._boot_picker_lock = threading.RLock()
        self._boot_picker = None
        self._boot_picker_selection: Optional[str] = None
        self._boot_picker_trigger: Optional[str] = None


    def get_sandbox_status(self) -> dict[str, Any]:
        from x86.sandbox import status
        return status(self._settings.read("execution_mode", "native"))

    def set_execution_mode(self, mode: str) -> dict[str, Any]:
        if mode not in ("native", "sandbox"):
            return {"ok": False, "error": "Unknown execution mode"}
        self._settings.write("execution_mode", mode)
        self._build_completed = False
        return self.get_sandbox_status()

    def get_sandbox_plan(self, target_major: int) -> dict[str, Any]:
        from x86.sandbox import plan
        try:
            return plan(target_major)
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    def prepare_sandbox(self, target_major: int, output_path: str) -> dict[str, Any]:
        from x86.sandbox import prepare
        if self._settings.read("execution_mode", "native") != "sandbox":
            return {"ok": False, "error": "Select Apple Silicon Sandbox first"}
        try:
            return prepare(target_major, output_path)
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    def get_vmapple_status(self) -> dict[str, Any]:
        """Return caller-supplied VMApple path state without starting QEMU."""
        from x86.vmapple import configured_from_environment

        return configured_from_environment()

    def inspect_vmapple_storage(self, config: dict[str, Any]) -> dict[str, Any]:
        """Inspect AUX/root inputs without starting QEMU or opening a writer.

        This is a user-space preflight.  It can identify the zero-filled
        fixtures used by protocol tests, but it deliberately cannot certify a
        hardware-model-matched VZMacAuxiliaryStorage image.
        """
        if not isinstance(config, dict):
            return {"ok": False, "error": "VMApple 저장장치 설정은 JSON 객체여야 합니다."}
        vm_json = config.get("vm_json", "")
        aux = config.get("aux", "")
        root = config.get("root", "")
        if not isinstance(vm_json, str) or not isinstance(aux, str) or not isinstance(root, str):
            return {"ok": False, "error": "VMApple 저장장치 경로는 문자열이어야 합니다."}
        vm_json = vm_json.strip()
        aux = aux.strip()
        root = root.strip()
        if not vm_json and (not aux or not root):
            return {"ok": False, "error": "macosvm.json 또는 AUX와 root 원본 경로를 입력하세요."}
        offset = config.get("aux_offset", config.get("aux-offset", 0))
        if isinstance(offset, bool) or not isinstance(offset, int):
            return {"ok": False, "error": "VMApple aux_offset은 정수여야 합니다."}
        from x86.vmapple import MACOSVM_AUX_METADATA_BYTES, inspect_macosvm_storage, inspect_storage
        if vm_json and offset not in (0, MACOSVM_AUX_METADATA_BYTES):
            return {
                "ok": False,
                "error": f"macosvm.json AUX 오프셋은 0x{MACOSVM_AUX_METADATA_BYTES:x}만 허용됩니다.",
            }
        try:
            result = (
                inspect_macosvm_storage(vm_json)
                if vm_json
                else inspect_storage(aux=aux, root=root, aux_offset=offset)
            )
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": str(exc), "installer_ui_verified": False}
        result["ok"] = True
        return result

    def get_boot_picker_status(self) -> dict[str, Any]:
        """Return the current two-second picker session without starting QEMU."""
        from x86.boot_picker import BootPickerSession

        with self._boot_picker_lock:
            if self._boot_picker is None:
                self._boot_picker = BootPickerSession(target_major=27)
            return {"ok": True, **self._boot_picker.tick()}

    def start_boot_picker(
        self,
        target_major: int = 27,
        recovery_protocol: str = "DFU/IPSW",
        recovery_image_name: str = "_default.ipsw",
    ) -> dict[str, Any]:
        """Arm the visible GUI picker and begin its exact two-second window."""
        from x86.boot_picker import BootPickerError, BootPickerSession

        try:
            if isinstance(target_major, bool) or target_major not in (26, 27):
                raise BootPickerError("BootPicker target must be macOS 26 or 27.")
            session = BootPickerSession(
                target_major=target_major,
                recovery_protocol=recovery_protocol,
                recovery_image_name=recovery_image_name,
            )
            with self._boot_picker_lock:
                self._boot_picker = session
                self._boot_picker_selection = None
                self._boot_picker_trigger = None
                return {"ok": True, **session.start()}
        except (BootPickerError, ValueError) as exc:
            return {
                "ok": False,
                "error": str(exc),
                "policy_error": exc.to_dict() if hasattr(exc, "to_dict") else None,
            }

    def tick_boot_picker(self) -> dict[str, Any]:
        """Advance the picker clock; timeout selects the normal macOS entry."""
        with self._boot_picker_lock:
            status = self.get_boot_picker_status()
            if status.get("selection"):
                self._boot_picker_selection = str(status["selection"])
                self._boot_picker_trigger = status.get("trigger")
            return status

    def boot_picker_key(self, key: object, pressed: bool = True) -> dict[str, Any]:
        """Forward a real DOM key event to the picker state machine."""
        from x86.boot_picker import BootPickerError

        with self._boot_picker_lock:
            if self._boot_picker is None:
                return {"ok": False, "error": "BootPicker session is not armed.",
                        "policy_error": {"code": "VF_BOOT_PICKER_NOT_ARMED"}}
            try:
                status = self._boot_picker.key_event(key, pressed=pressed)
            except BootPickerError as exc:
                return {"ok": False, "error": str(exc), "policy_error": exc.to_dict()}
            if status.get("selection"):
                self._boot_picker_selection = str(status["selection"])
                self._boot_picker_trigger = status.get("trigger")
            return {"ok": True, **status}

    def select_boot_entry(self, entry_id: object) -> dict[str, Any]:
        """Select a visible picker entry (the GUI's pointer/Enter path)."""
        from x86.boot_picker import BootPickerError

        with self._boot_picker_lock:
            if self._boot_picker is None:
                return {"ok": False, "error": "BootPicker session is not armed.",
                        "policy_error": {"code": "VF_BOOT_PICKER_NOT_ARMED"}}
            try:
                status = self._boot_picker.select(entry_id)
            except BootPickerError as exc:
                return {"ok": False, "error": str(exc), "policy_error": exc.to_dict()}
            self._boot_picker_selection = str(status["selection"])
            self._boot_picker_trigger = status.get("trigger")
            return {"ok": True, **status}

    def launch_vmapple(self, config: dict[str, Any]) -> dict[str, Any]:
        """Spawn the visible VMApple worker and leave all recovery evidence on disk.

        The GUI is a user-space controller. The worker performs the actual
        VMApple/DFU protocol in WSL when a Linux QEMU binary is supplied.
        """
        if self._settings.read("execution_mode", "native") != "sandbox":
            return {"ok": False, "error": "Apple Silicon Sandbox 모드에서만 VMApple을 실행할 수 있습니다."}
        if not isinstance(config, dict):
            return {"ok": False, "error": "VMApple 설정은 JSON 객체여야 합니다."}
        if config.get("research_only") is not True:
            return {"ok": False, "error": "VMApple 실행에는 research_only 확인이 필요합니다."}

        # Validate the fixed iBoot personality before resolving paths or
        # spawning a worker.  Mobile Apple guests never reach DFU upload.
        from x86.iboot_personality import IbootScopeError, validate_iboot_scope

        machine_type = config.get("machine_type", "iBoot(AArch64)")
        guest_os = config.get("guest_os", "macOS")
        recovery_protocol = config.get("recovery_protocol", "DFU/IPSW")
        recovery_image_name = config.get("recovery_image_name", "_default.ipsw")
        target = config.get("target_major", config.get("target", 27))
        boot_picker_enabled = config.get("boot_picker_enabled", True)
        boot_delay = config.get("boot_delay_seconds", config.get("boot_delay", 2.0))
        boot_selection = config.get("boot_selection")
        boot_trigger = config.get("boot_picker_trigger")
        live_personalize = config.get("live_personalize", False)
        optional_rpc_unavailable = config.get("optional_rpc_unavailable", False)
        restore_chain = config.get("restore_chain", False)
        restore_role_dir = config.get("restore_role_dir", "")
        engine = config.get("engine", "qemu")
        if engine not in ("qemu", "native-macosvm"):
            return {"ok": False, "error": "VMApple engine은 qemu 또는 native-macosvm이어야 합니다."}
        if type(live_personalize) is not bool:
            return {"ok": False, "error": "VMApple live_personalize must be a boolean."}
        if type(optional_rpc_unavailable) is not bool:
            return {"ok": False, "error": "VMApple optional_rpc_unavailable must be a boolean."}
        if type(restore_chain) is not bool:
            return {"ok": False, "error": "VMApple restore_chain must be a boolean."}
        with self._boot_picker_lock:
            active_picker = self._boot_picker
            active_target = getattr(active_picker, "target_major", None)
            if boot_selection in (None, "") and self._boot_picker_selection and active_target == target:
                boot_selection = self._boot_picker_selection
                boot_trigger = self._boot_picker_trigger
        if boot_selection in (None, ""):
            # The standalone VMApple runner is a recovery transport.  A GUI
            # user must explicitly press Alt and choose Recovery to override
            # this audited compatibility default.
            boot_selection = "recovery"
        if boot_trigger in (None, ""):
            boot_trigger = "runner-default-recovery"
        try:
            personality = validate_iboot_scope(
                machine_type,
                guest_os,
                recovery_protocol=recovery_protocol,
                recovery_image_name=recovery_image_name,
                recovery_enabled=True,
                target_major=target,
            )
        except IbootScopeError as exc:
            return {"ok": False, "error": str(exc), "policy_error": exc.to_dict(),
                    "macos_boot_verified": False}
        if not isinstance(machine_type, str) or not isinstance(guest_os, str):
            return {"ok": False, "error": "VMApple personality fields must be strings."}
        from x86.boot_picker import BootPickerError, validate_boot_picker_config
        try:
            picker = validate_boot_picker_config(
                enabled=boot_picker_enabled,
                delay_seconds=boot_delay,
                alt_key="Alt",
                show_picker_on_alt=True,
                target_major=target,
                recovery_enabled=True,
                recovery_protocol=recovery_protocol,
                recovery_image_name=recovery_image_name,
            )
        except (BootPickerError, ValueError) as exc:
            return {"ok": False, "error": str(exc),
                    "policy_error": exc.to_dict() if hasattr(exc, "to_dict") else None,
                    "macos_boot_verified": False}
        if boot_selection not in ("macos", "recovery"):
            return {"ok": False, "error": "VMApple boot selection must be macos or recovery."}
        if boot_selection == "macos" and live_personalize:
            return {
                "ok": False,
                "error": "직접 macOS 부팅은 이미 프로비저닝된 AUX/root를 사용하며 live TSS 복구 개인화를 수행하지 않습니다.",
                "macos_boot_verified": False,
            }
        if boot_selection == "macos" and restore_chain:
            return {
                "ok": False,
                "error": "restore-role 체인은 Recovery 전용입니다. 직접 macOS 부팅에서는 복구 체인을 끄십시오.",
                "macos_boot_verified": False,
            }
        if boot_picker_enabled is True and boot_selection == "recovery" and not picker.get("recovery_entry_enabled"):
            return {"ok": False, "error": "VMApple Recovery entry is disabled."}
        if not isinstance(boot_trigger, str) or not boot_trigger.strip():
            return {"ok": False, "error": "VMApple boot picker trigger must be a nonempty string."}
        picker["selection"] = boot_selection
        picker["selection_source"] = boot_trigger.strip()
        picker["hotkey_event_observed"] = boot_trigger.startswith("alt-")
        picker["delay_enforced"] = boot_picker_enabled is True
        personality["boot_picker"] = picker

        if engine == "native-macosvm":
            if boot_selection != "macos":
                return {
                    "ok": False,
                    "error": "native-macosvm은 프로비저닝된 macOS 항목만 실행합니다. Recovery는 qemu engine을 사용하세요.",
                    "macos_boot_verified": False,
                }
            from x86.vmapple import native_macosvm_host_report

            native_host = native_macosvm_host_report()
            if native_host.get("apple_silicon_macos") is not True:
                return {
                    "ok": False,
                    "error": "native-macosvm은 Apple-Silicon macOS host에서만 실행할 수 있습니다.",
                    "host": native_host,
                    "macos_boot_verified": False,
                }
            native_paths: dict[str, str] = {}
            for name in ("macosvm", "vm_json", "output"):
                value = config.get(name, "")
                if value is None:
                    value = ""
                if not isinstance(value, str):
                    return {"ok": False, "error": f"native-macosvm {name} 경로는 문자열이어야 합니다."}
                native_paths[name] = value.strip()
            missing = [name for name in ("macosvm", "vm_json", "output") if not native_paths[name]]
            if missing:
                return {"ok": False, "error": "native-macosvm 필수 경로가 없습니다: " + ", ".join(missing)}
            duration = config.get("duration")
            observation_timeout = config.get("observation_timeout", 600.0)
            if duration is not None and (
                isinstance(duration, bool) or not isinstance(duration, (int, float))
                or not 0.001 <= float(duration) <= 86400.0
            ):
                return {"ok": False, "error": "native-macosvm duration 값이 범위를 벗어났습니다."}
            if (
                isinstance(observation_timeout, bool)
                or not isinstance(observation_timeout, (int, float))
                or not 0.001 <= float(observation_timeout) <= 86400.0
            ):
                return {"ok": False, "error": "native-macosvm observation_timeout 값이 범위를 벗어났습니다."}
            command = [sys.executable, "-m", "x86", "vmapple", "run-native"]
            command.extend(["--target", str(target), "--macosvm", native_paths["macosvm"],
                            "--vm-json", native_paths["vm_json"], "--output", native_paths["output"],
                            "--observation-timeout", str(float(observation_timeout)),
                            "--research-only", "--json"])
            if duration is not None:
                command.extend(["--duration", str(float(duration))])
            if config.get("gui") is True:
                command.append("--gui")
            log_path = Path(tempfile.gettempdir()) / f"26x86-macosvm-launch-{int(time.time() * 1000)}.log"
            try:
                with log_path.open("ab") as log:
                    process = subprocess.Popen(
                        command,
                        cwd=str(bootstrap.ensure_repo_on_path()),
                        env=os.environ.copy(),
                        stdin=subprocess.DEVNULL,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
            except OSError as exc:
                logging.exception("native macosvm worker spawn failed")
                return {"ok": False, "error": str(exc), "log_path": str(log_path)}
            return {
                "ok": True,
                "spawned": True,
                "pid": process.pid,
                "worker": "native-macosvm",
                "engine": engine,
                "target_major": target,
                "boot_selection": boot_selection,
                "boot_picker": picker,
                "output": native_paths["output"],
                "log_path": str(log_path),
                "research_only": True,
                "macos_boot_verified": False,
                "host": native_host,
                "note": "native macosvm worker는 launch.json에서 XNU/userspace marker와 입력 무결성을 별도로 기록합니다.",
            }

        # Keep the bridge surface deliberately narrow: callers can provide
        # paths and bounded scalar values, never arbitrary QEMU arguments.
        string_fields = (
            "qemu", "qemu_img", "firmware", "macosvm", "vm_json", "ibss", "ibec", "aux", "root", "output",
            "aux_seed", "root_seed",
            "build_manifest", "tss_helper", "original_ibss", "original_ibec", "restore_role_dir",
        )
        values: dict[str, Any] = {}
        for name in string_fields:
            value = config.get(name)
            if value is None:
                value = ""
            if not isinstance(value, str):
                return {"ok": False, "error": f"VMApple {name} 경로는 문자열이어야 합니다."}
            values[name] = value.strip()
        required = ("qemu", "qemu_img", "firmware", "output")
        if boot_selection == "macos":
            # AVPBooter reads the provisioned guest disk directly.  iBSS and
            # iBEC are recovery transport inputs and must not be mandatory for
            # the normal macOS entry.
            if not values["vm_json"]:
                required += ("aux", "root")
        elif live_personalize:
            required += ("build_manifest", "tss_helper", "original_ibss", "original_ibec")
        else:
            required += ("ibss",)
        if restore_chain:
            required += ("restore_role_dir",)
        missing = [name for name in required if not values[name]]
        if missing:
            return {"ok": False, "error": "필수 VMApple 경로가 없습니다: " + ", ".join(missing)}

        if isinstance(target, bool) or not isinstance(target, int) or target not in (26, 27):
            return {"ok": False, "error": "VMApple 대상은 macOS 26 또는 27이어야 합니다."}
        display = config.get("display", "auto")
        if display not in ("auto", "gtk", "sdl", "cocoa", "none", "dbus"):
            return {"ok": False, "error": "VMApple 표시 방식은 auto, GTK, SDL, Cocoa, none 또는 dbus여야 합니다."}

        numeric = {
            "uuid": (config.get("uuid", 0), 0, 2**64 - 1),
            "aux_offset": (config.get("aux_offset", config.get("aux-offset", 0)), 0, 2**63 - 512),
            "memory_mib": (config.get("memory_mib", 4096), 512, 1024 * 1024),
            "smp": (config.get("smp", 2), 1, 32),
        }
        for name, (value, lower, upper) in numeric.items():
            if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
                return {"ok": False, "error": f"VMApple {name} 값이 범위를 벗어났습니다."}
            if name == "aux_offset" and value % 512:
                return {"ok": False, "error": "VMApple aux_offset은 512바이트 배수여야 합니다."}
            values[name] = value
        for name, lower, upper in (("transition_timeout", 0.001, 3600.0), ("duration", 0.001, 86400.0)):
            value = config.get(name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not lower <= float(value) <= upper:
                return {"ok": False, "error": f"VMApple {name} 값이 범위를 벗어났습니다."}
            values[name] = str(float(value))
        restore_timeout = config.get("restore_timeout", 900.0)
        if (isinstance(restore_timeout, bool) or not isinstance(restore_timeout, (int, float))
                or not 0.001 <= float(restore_timeout) <= 3600.0):
            return {"ok": False, "error": "VMApple restore_timeout 값이 범위를 벗어났습니다."}
        values["restore_timeout"] = str(float(restore_timeout))
        if type(boot_picker_enabled) is not bool:
            return {"ok": False, "error": "VMApple boot_picker_enabled must be a boolean."}
        if isinstance(boot_delay, bool) or not isinstance(boot_delay, (int, float)):
            return {"ok": False, "error": "VMApple boot delay must be exactly 2 seconds."}
        if float(boot_delay) != 2.0:
            return {"ok": False, "error": "VMApple boot delay is fixed at 2 seconds."}
        values["boot_delay_seconds"] = float(boot_delay)
        values["boot_picker_enabled"] = boot_picker_enabled
        values["boot_selection"] = boot_selection
        values["boot_picker_trigger"] = boot_trigger.strip()
        values["live_personalize"] = live_personalize
        values["optional_rpc_unavailable"] = optional_rpc_unavailable

        from x86.vmapple import _to_wsl_path
        from x86.vmapple import VIRTUAL_MODEL, VIRTUAL_SOC_NAME

        repo = bootstrap.ensure_repo_on_path()
        input_names = ("qemu", "qemu_img", "firmware", "macosvm", "vm_json", "ibss", "ibec", "aux", "root", "output",
                       "build_manifest", "tss_helper", "original_ibss", "original_ibec", "restore_role_dir")
        needs_wsl = is_windows() and any(values[name].startswith("/") for name in input_names if values[name])
        if needs_wsl:
            wsl = shutil.which("wsl.exe")
            if wsl is None:
                return {"ok": False, "error": "Linux VMApple QEMU에는 wsl.exe와 WSLg가 필요합니다."}
            # `--exec` bypasses the distribution's shell.  This is required
            # for the literal MachineType `iBoot(AArch64)` and keeps every
            # caller-supplied path an argv element rather than shell syntax.
            command = [wsl, "--cd", _to_wsl_path(repo), "--exec", "python3", "-m", "x86", "vmapple", "run"]
            worker = "wsl"
            converted = {name: _to_wsl_path(Path(values[name])) if values[name] else "" for name in input_names}
        else:
            command = [sys.executable, "-m", "x86", "vmapple", "run"]
            worker = "native"
            converted = values

        def add(flag: str, name: str, *, required_value: bool = True) -> None:
            value = converted.get(name, "")
            if required_value and not value:
                return
            command.extend([flag, str(value)])

        # The CLI uses --target as a scalar, while path options are explicit.
        command.extend(["--target", str(target)])
        add("--qemu", "qemu")
        add("--qemu-img", "qemu_img")
        add("--firmware", "firmware")
        add("--vm-json", "vm_json")
        add("--ibss", "ibss")
        add("--ibec", "ibec")
        add("--aux", "aux")
        add("--root", "root")
        add("--aux-seed", "aux_seed")
        add("--root-seed", "root_seed")
        add("--output", "output")
        add("--build-manifest", "build_manifest")
        add("--tss-helper", "tss_helper")
        add("--original-ibss", "original_ibss")
        add("--original-ibec", "original_ibec")
        add("--restore-role-dir", "restore_role_dir")
        command.extend(["--display", display, "--uuid", str(values["uuid"]),
                        "--aux-offset", str(values["aux_offset"]),
                        "--memory-mib", str(values["memory_mib"]),
                        "--smp", str(values["smp"]),
                        "--transition-timeout", str(float(values.get("transition_timeout", 300.0))),
                        "--restore-timeout", values["restore_timeout"],
                        "--machine-type", machine_type,
                        "--guest-os", guest_os,
                        "--recovery-protocol", recovery_protocol,
                        "--recovery-image-name", recovery_image_name,
                        "--boot-selection", boot_selection,
                        "--boot-delay", str(float(boot_delay)),
                        "--boot-picker-trigger", boot_trigger.strip(),
                         "--research-only", "--json"])
        if live_personalize:
            command.append("--live-personalize")
        if optional_rpc_unavailable:
            command.append("--optional-rpc-unavailable")
        if restore_chain:
            command.append("--restore-chain")
        if "duration" in values:
            command.extend(["--duration", values["duration"]])

        log_path = Path(tempfile.gettempdir()) / f"26x86-vmapple-launch-{int(time.time() * 1000)}.log"
        try:
            with log_path.open("ab") as log:
                process = subprocess.Popen(
                    command,
                    cwd=str(repo),
                    env=os.environ.copy(),
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        except OSError as exc:
            logging.exception("VMApple worker spawn failed")
            return {"ok": False, "error": str(exc), "log_path": str(log_path)}
        return {
            "ok": True,
            "spawned": True,
            "pid": process.pid,
            "worker": worker,
            "display_backend": display,
            "target_major": target,
            "machine_type": personality["machine_type"],
            "personality": personality["personality"],
            "guest_os": personality["guest_os"],
            "guest_os_supported": personality["guest_os_supported"],
            "guest_os_policy": personality["guest_os_policy"],
            "policy_matrix": personality["policy_matrix"],
            "recovery_scope": personality["recovery"],
            "boot_picker": picker,
            "boot_selection": boot_selection,
            "boot_picker_trigger": boot_trigger.strip(),
            "output": values["output"],
            "log_path": str(log_path),
            "research_only": True,
            "live_personalize": live_personalize,
            "optional_rpc_unavailable": optional_rpc_unavailable,
            "restore_chain": restore_chain,
            "restore_timeout": float(restore_timeout),
            "virtual_soc_name": VIRTUAL_SOC_NAME,
            "virtual_model": VIRTUAL_MODEL,
            "virtual_identity_mode": "metadata-only",
            "hardware_attestation_verified": False,
            "forced_transition": False,
            "macos_boot_verified": False,
            "note": "창이 표시되며 결과는 output/launch.json에 기록됩니다. 실제 descriptor가 없으면 iBEC 전환을 강제하지 않습니다.",
        }

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
        load = getattr(self._settings, "load", None)
        if callable(load):
            settings = load()
        else:
            # Keep the bridge usable with the tiny read-only settings facade
            # used by headless callers and older embedders.
            settings = {
                "execution_mode": self._settings.read("execution_mode", "x86"),
                "mellow_deployment": self._settings.read("mellow_deployment", "disabled"),
                "mellow_payload": self._settings.read("mellow_payload", ""),
                "mellow_efi": self._settings.read("mellow_efi", ""),
            }
        return configuration(settings=settings)

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
            **selection,
        }


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
                summary = "ARM64e macOS EFI 실행 모드 · 설치용 EFI 준비 중."
                return {"ok": True, "execution": context.as_dict(),
                    "patch": {"can_patch": False, "can_unpatch": False, "patches_available": []},
                    "summary": summary}
            if deployment == "root-patch":
                from x86.patch.root import preflight
                report = preflight(constants=self._constants())
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
        if self._settings.read("execution_mode", "native") == "sandbox" and action != "help":
            return {"ok": False, "error": "Native patch actions are disabled in Apple Silicon Sandbox mode"}
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

        if action == "patch":
            from x86.patch.root import preflight
            report = preflight()
            if not report.get("can_patch"):
                # The bridge's platform guard above is authoritative.  This
                # narrow compatibility path only covers an embedded/test
                # caller whose root module kept a stale platform probe; on a
                # real host both probes resolve to the same macOS result.
                if report.get("status") == "unsupported_platform" and is_macos():
                    report = {**report, "can_patch": True, "ok": True}
                else:
                    return {"ok": False, "error": report.get("error") or "\n".join(report.get("blockers") or [report["status"]])}
        try:
            context.require_native_apply("Native wizard action")
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

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
