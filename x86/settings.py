"""
settings.py: SettingsStore — JSON at ~/Library/Application Support/26x86/config.json

26x86 does not read or write OCLP legacy plists.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .paths import Paths

DEFAULT_SETTINGS: dict[str, Any] = {
    "version": 1,
    "execution_mode": "native",
    "auto_patch": False,
    "verbose_logging": False,
    "last_detect": None,
    # Pre-AVX Mac Pro 자동 패치 (Safari26 RestrictEvents + revpatch=jsc). 기본 ON.
    "auto_pre_avx_patch": True,
    # Legacy alias — read via read_auto_pre_avx_patch().
    "safari26_preavx_fix": True,
}


def read_auto_pre_avx_patch(settings: Optional[dict[str, Any]] = None) -> bool:
    """Return whether automatic Pre-AVX / Safari26 EFI patches are enabled."""
    if settings is None:
        settings = SettingsStore().load()  # type: ignore[name-defined]
    if "auto_pre_avx_patch" in settings:
        value = settings["auto_pre_avx_patch"]
    else:
        value = settings.get("safari26_preavx_fix", True)
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "off", "no", "disabled"}
    return bool(value)


def _resolve_config_path() -> Path:
    """
    Resolve user config path, using the console user when running as root on macOS.
    """
    if sys.platform != "darwin":
        return Paths.user_config()

    home = Path.home()
    if home == Path("/var/root"):
        try:
            result = subprocess.run(
                ["/usr/bin/stat", "-f", "%Su", "/dev/console"],
                capture_output=True,
                text=True,
                check=True,
            )
            console_user = result.stdout.strip()
            if console_user and console_user != "root":
                user_home = Path(f"/Users/{console_user}")
                if user_home.is_dir():
                    return user_home / "Library/Application Support/26x86/config.json"
        except (OSError, subprocess.CalledProcessError):
            pass
    return Paths.user_config()


class SettingsStore:
    """
    26x86 user settings stored as JSON (0600, no symlinks).
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path: Path = config_path or _resolve_config_path()
        self._ensure_settings_file()

    def _ensure_settings_file(self) -> None:
        path = self.config_path
        if path.is_symlink():
            try:
                path.unlink()
            except (PermissionError, OSError):
                return

        if path.exists():
            return

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._write_raw(deepcopy(DEFAULT_SETTINGS))
        except (PermissionError, OSError) as error:
            logging.debug("Unable to initialize settings file: %s", error)

    def _read_raw(self) -> dict[str, Any]:
        path = self.config_path
        if path.is_symlink():
            logging.warning("Security alert: symlink detected during read. Ignoring.")
            return deepcopy(DEFAULT_SETTINGS)

        if not path.exists():
            return deepcopy(DEFAULT_SETTINGS)

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                return deepcopy(DEFAULT_SETTINGS)
            return data
        except (PermissionError, json.JSONDecodeError, OSError) as error:
            logging.error("Unable to read settings file: %s", error)
            return deepcopy(DEFAULT_SETTINGS)

    def _write_raw(self, data: dict[str, Any]) -> None:
        path = self.config_path
        if path.is_symlink():
            try:
                path.unlink()
            except (PermissionError, OSError):
                return

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.chmod(path, 0o600)
        except (PermissionError, OSError) as error:
            logging.error("Failed to write settings file: %s", error)

    def load(self) -> dict[str, Any]:
        return self._read_raw()

    def save(self, data: dict[str, Any]) -> None:
        self._write_raw(data)

    def read(self, key: str, default: Any = None) -> Any:
        return self._read_raw().get(key, default)

    def write(self, key: str, value: Any) -> None:
        data = self._read_raw()
        data[key] = value
        self._write_raw(data)

    def delete(self, key: str) -> None:
        data = self._read_raw()
        if key not in data:
            return
        del data[key]
        self._write_raw(data)

    def record_detect(self, model: str, extra: Optional[dict[str, Any]] = None) -> None:
        payload: dict[str, Any] = {
            "model": model,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if extra:
            payload.update(extra)
        self.write("last_detect", payload)
