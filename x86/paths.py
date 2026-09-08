"""
paths.py: Filesystem paths for 26x86 (bundle ID com.niseullent.26x86).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BUNDLE_ID: str = "com.niseullent.26x86"
APP_NAME: str = "NextCore"
APP_BUNDLE_NAME: str = "26x86.app"

BUNDLE_ID_PRIVILEGED_HELPER: str = f"{BUNDLE_ID}.privileged-helper"
BUNDLE_ID_UNINSTALLER: str = f"{BUNDLE_ID}-uninstaller"
BUNDLE_ID_INSTALLER: str = BUNDLE_ID
BUNDLE_ID_AUTOPKG: str = f"{BUNDLE_ID}.pkg.AutoPkg-Assets"

LAUNCH_AGENT_SUFFIXES: tuple[str, ...] = (
    "auto-patch",
    "macos-update",
    "rsr-monitor",
    "os-caching",
)


def _windows_appdata() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata)
    return Path.home() / "AppData" / "Roaming"


def _linux_config_home() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def _linux_state_home() -> Path:
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".local" / "state"


def _linux_cache_home() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".cache"


class Paths:
    """Canonical filesystem locations for 26x86."""

    @staticmethod
    def repo_root() -> Path:
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                return Path(meipass)
        return Path(__file__).resolve().parent.parent

    @staticmethod
    def user_config_dir() -> Path:
        if sys.platform == "darwin":
            return Path.home() / "Library/Application Support/26x86"
        if sys.platform == "win32":
            return _windows_appdata() / "26x86"
        return _linux_config_home() / "26x86"

    @staticmethod
    def user_config() -> Path:
        return Paths.user_config_dir() / "config.json"

    @staticmethod
    def user_preferences_plist() -> Path:
        if sys.platform == "darwin":
            return Path.home() / "Library/Preferences/com.niseullent.26x86.plist"
        if sys.platform == "win32":
            return Paths.user_config_dir() / "com.niseullent.26x86.plist"
        return Paths.user_config_dir() / "com.niseullent.26x86.plist"

    @staticmethod
    def user_cache_dir() -> Path:
        if sys.platform == "darwin":
            return Paths.user_config_dir() / "cache"
        if sys.platform == "win32":
            return Paths.user_config_dir() / "cache"
        return _linux_cache_home() / "26x86"

    @staticmethod
    def user_logs_dir() -> Path:
        if sys.platform == "darwin":
            return Path.home() / "Library/Logs/26x86"
        if sys.platform == "win32":
            return Paths.user_config_dir() / "logs"
        return _linux_state_home() / "26x86" / "logs"

    @staticmethod
    def user_launch_agents_dir() -> Path:
        if sys.platform == "darwin":
            return Path.home() / "Library/LaunchAgents"
        return Paths.user_config_dir() / "launchagents"

    @staticmethod
    def system_app_support() -> Path:
        if sys.platform == "darwin":
            return Path("/Library/Application Support/26x86")
        if sys.platform == "win32":
            program_data = os.environ.get("ProgramData", "C:\\ProgramData")
            return Path(program_data) / "26x86"
        return Path("/usr/local/share/26x86")

    @staticmethod
    def developer_mode_marker() -> Path:
        return Path.home() / ".26x86_developer"

    @staticmethod
    def payloads_dir() -> Path:
        return Paths.repo_root() / "payloads"

    @staticmethod
    def resources_dir() -> Path:
        return Paths.repo_root() / "resources"

    @staticmethod
    def launch_agents_templates_dir() -> Path:
        return Paths.resources_dir() / "launchagents"

    @staticmethod
    def launch_agent_label(suffix: str) -> str:
        return f"{BUNDLE_ID}.{suffix}"

    @staticmethod
    def launch_agent_plist_name(suffix: str) -> str:
        return f"{Paths.launch_agent_label(suffix)}.plist"

    @staticmethod
    def launch_agent_user_path(suffix: str) -> Path:
        return Paths.user_launch_agents_dir() / Paths.launch_agent_plist_name(suffix)

    # PatcherSupportPkg DMG paths (see x86.patch.PayloadManager)
    @staticmethod
    def universal_binaries_dmg() -> Path:
        return Paths.repo_root() / "Universal-Binaries.dmg"

    @staticmethod
    def internal_resources_dmg() -> Path:
        return Paths.repo_root() / "DortaniaInternalResources.dmg"

    @staticmethod
    def universal_binaries_mount() -> Path:
        return Paths.payloads_dir() / "Universal-Binaries"

    @staticmethod
    def universal_binaries_overlay() -> Path:
        return Paths.payloads_dir() / "Universal-Binaries_overlay"

    @staticmethod
    def internal_resources_mount() -> Path:
        return Paths.payloads_dir() / "DortaniaInternal"

    @staticmethod
    def cached_universal_binaries_dmg(version: str) -> Path:
        return Paths.user_cache_dir() / f"Universal-Binaries-{version}.dmg"
