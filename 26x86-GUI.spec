# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import time
import subprocess
from pathlib import Path

try:
    SPEC_DIR = Path(SPECPATH).resolve()
except NameError:
    SPEC_DIR = Path(os.getcwd()).resolve()

sys.path.append(str(SPEC_DIR))

from opencore_legacy_patcher import constants

block_cipher = None

datas = [
   (str(SPEC_DIR / 'payloads.dmg'), '.'),
   (str(SPEC_DIR / 'Universal-Binaries.dmg'), '.'),
   (str(SPEC_DIR / 'x86/gui/web'), 'x86/gui/web'),
   (str(SPEC_DIR / 'resources/branding'), 'resources/branding'),
   (str(SPEC_DIR / 'payloads/Mellow'), 'payloads/Mellow'),
]

if (SPEC_DIR / "sandbox/efi/build/BOOTX64.EFI").exists():
   from x86.sandbox import _artifact
   engine, _ = _artifact(SPEC_DIR)
   datas.extend((str(file), "sandbox/efi/build") for file in (engine, engine.parent / "build-report.json"))

if (SPEC_DIR / "DortaniaInternalResources.dmg").exists():
   datas.append((str(SPEC_DIR / 'DortaniaInternalResources.dmg'), '.'))

a = Analysis([str(SPEC_DIR / '26x86-GUI.command')],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[
                 'webview',
                 'webview.platforms',
                 'webview.platforms.qt',
                 'webview.platforms.cocoa',
                 'x86.gui.qt_chromium',
                 'x86.gui.webview_app',
                 'x86.gui.bridge',
                 'PySide6',
                 'PySide6.QtCore',
                 'PySide6.QtGui',
                 'PySide6.QtWidgets',
                 'PySide6.QtNetwork',
                 'PySide6.QtWebEngineCore',
                 'PySide6.QtWebEngineWidgets',
                 'PySide6.QtWebChannel',
                 'shiboken6',
                 'objc',
                 'WebKit',
                 'Foundation',
                 'AppKit',
             ],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='26x86',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='26x86')

app = BUNDLE(coll,
             name='26x86.app',
             icon=str(SPEC_DIR / "payloads/Resources/AppIcons/26x86.icns"),
             bundle_identifier="com.niseullent.26x86",
             info_plist={
                "CFBundleName": "26x86",
                "CFBundleVersion": constants.Constants().patcher_version,
                "CFBundleShortVersionString": constants.Constants().patcher_version,
                "NSHumanReadableCopyright": constants.Constants().copyright_date,
                "LSMinimumSystemVersion": "10.13.6",
                "NSRequiresAquaSystemAppearance": False,
                "NSHighResolutionCapable": True,
                "Build Date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "BuildMachineOSBuild": subprocess.run(["/usr/bin/sw_vers", "-buildVersion"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip(),
                "NSPrincipalClass": "NSApplication",
                "NSAppTransportSecurity": {
                    "NSAllowsLocalNetworking": True,
                    "NSAllowsArbitraryLoads": False,
                },
             })

def _repair_qtwebengine_helpers(bundle: Path) -> None:
    """PyInstaller leaves Helpers at Versions/Resources; Qt looks in Versions/Current."""
    for rel in (
        "Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework",
        "Contents/Resources/PySide6/Qt/lib/QtWebEngineCore.framework",
    ):
        fw = bundle / rel
        src = fw / "Versions" / "Resources" / "Helpers"
        dst = fw / "Versions" / "A" / "Helpers"
        if src.exists() and not dst.exists():
            os.symlink("../Resources/Helpers", dst)

_repair_qtwebengine_helpers(SPEC_DIR / "dist" / "26x86.app")
