"""
Window titles and branding helpers for 26x86 GUI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from x86.manifest import APP_NAME, BUNDLE_ID
from x86.paths import Paths

LOGO_BASENAME = "nextcore-logo"
APP_ICON_BASENAME = "26x86"


def window_title(version: str = "") -> str:
    """Product title; the persistent bundle identifier remains unchanged."""
    base = APP_NAME
    if version:
        return f"{base} {version}"
    return base


def about_title() -> str:
    return f"{APP_NAME} 정보"


def about_description_lines() -> list[str]:
    return [
        "오래된 Mac에서 Apple이 공식 지원하지 않는",
        "최신 macOS를 사용할 수 있도록 돕는 도구입니다.",
        "외부 구성요소: OpenCore / OpenCore Legacy Patcher",
        "",
        BUNDLE_ID,
    ]


def is_advanced_gui_enabled() -> bool:
    """Legacy wx MainFrame is available only when ``X86_ADVANCED=1``."""
    return os.environ.get("X86_ADVANCED") == "1"


def branding_dir() -> Path:
    return Paths.resources_dir() / "branding"


def logo_svg_path() -> Path:
    return branding_dir() / f"{LOGO_BASENAME}.svg"


def logo_png_path(size: int = 256) -> Path:
    return branding_dir() / f"{LOGO_BASENAME}-{size}.png"


def app_icon_icns_path() -> Path:
    return Paths.payloads_dir() / "Resources" / "AppIcons" / f"{APP_ICON_BASENAME}.icns"


def resolve_gui_logo_path(icns_resource_path: Optional[Path] = None) -> Optional[Path]:
    """
    Best logo for wx StaticBitmap: bundled PNG, then bundled or app .icns.
    """
    png = logo_png_path(256)
    if png.exists():
        return png
    if icns_resource_path is not None:
        candidate = icns_resource_path / f"{APP_ICON_BASENAME}.icns"
        if candidate.exists():
            return candidate
    bundled_icns = app_icon_icns_path()
    if bundled_icns.exists():
        return bundled_icns
    return None
