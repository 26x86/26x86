# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

try:
    SPEC_DIR = Path(SPECPATH).resolve()
except NameError:
    SPEC_DIR = Path(os.getcwd()).resolve()

ENTRY = SPEC_DIR / "x86" / "gui" / "entry.py"
WEB_DIR = SPEC_DIR / "x86" / "gui" / "web"
BRANDING_DIR = SPEC_DIR / "resources" / "branding"
ICON_ICO = SPEC_DIR / "payloads" / "Resources" / "AppIcons" / "26x86.ico"

datas = [
    (str(WEB_DIR), "x86/gui/web"),
    (str(BRANDING_DIR), "resources/branding"),
    (str(SPEC_DIR / "payloads/Mellow"), "payloads/Mellow"),
]

sys.path.insert(0, str(SPEC_DIR))

a = Analysis(
    [str(ENTRY)],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "webview",
        "webview.platforms",
        "webview.platforms.edgechromium",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="26x86",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ICON_ICO) if ICON_ICO.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="26x86",
)
