# 26x86 Development Environment Setup Guide

This guide describes how to configure, build, and test **26x86**, the clean-room boot engineering and compatibility project for macOS 26 Tahoe and x86 Macintosh hardware.

## Directory Structure

```
~/Desktop/26x86/
├── 26x86/                      # Main patcher and NextCore CLI/GUI
├── 26x86-MetallibSupportPkg/   # Metal library patching utilities
├── 26x86-PatcherSupportPkg/    # Universal binaries and patch DMGs
├── 26x86-OpenCorePkg/          # OpenCore bootloader integration fork
├── .venv/                      # Python 3.13 virtual environment
├── scripts/                    # Setup and build automation scripts
├── docs/                       # Project documentation
└── vm/                         # UTM / QEMU virtual machine templates
```

## Quick Start (One-Click)

```bash
cd ~/Desktop/26x86
bash scripts/setup-dev.sh
source .venv/bin/activate
cd 26x86
python3 26x86.command
```

## Manual Installation

### 1. Prerequisites

| Component | Version / Notes |
|-----------|-----------------|
| macOS | macOS 15.x (Sequoia) or newer recommended |
| Python | **3.13+** (python.org or `uv python install 3.13`) |
| Xcode CLT | `xcode-select --install` |
| Git | `git --version` |
| GitHub CLI | GitHub authentication (`gh auth status`, optional) |

> For development environment considerations (Python 3.9 deprecation, VM host limitations, etc.): see [wiki/Installation-Notes.md](./wiki/Installation-Notes.md) and [wiki/Warnings.md](./wiki/Warnings.md).

### 2. Clone Repositories

```bash
mkdir -p ~/Desktop/26x86 && cd ~/Desktop/26x86

git clone https://github.com/26x86/26x86.git
git clone https://github.com/26x86/MetallibSupportPkg.git
git clone https://github.com/26x86/PatcherSupportPkg.git
git clone https://github.com/26x86/OpenCorePkg.git
```

### 3. Python Virtual Environment

```bash
# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.13
~/.local/bin/python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies (including PyInstaller bootloader rebuild)
PYINSTALLER_COMPILE_BOOTLOADER=1 pip install --no-binary pyinstaller -r 26x86/requirements.txt
```

### 4. Verification & Running

```bash
cd 26x86
python3 26x86.command --help     # CLI help
python3 26x86.command            # GUI (Wizard mode)
python3 26x86.command --detect   # Hardware model detection
python3 26x86.command --build --model iMac11,2 --verbose
```

## Running on Windows / Linux (Source)

Full system modifications (**EFI partition deployment, live root patching, LaunchAgent persistence**) are **macOS-only**. On Windows and Linux, the CLI and HTML wizard GUI can be used for configuration inspection, platform detection, validation probes, and offline bundle assembly.

### Cross-Platform Prerequisites

| Item | Windows | Linux |
|------|---------|-------|
| Python | **3.13+** | **3.13+** |
| Virtual Env | `python -m venv .venv` | `python3 -m venv .venv` |
| Dependencies | `pip install -r 26x86/requirements.txt` | Same |
| GUI (Recommended) | **Tauri** (WebView2) + Python HTTP bridge | **Tauri** (WebKitGTK) or pywebview |
| GUI Fallback | pywebview + Edge WebView2 Runtime | pywebview + GTK (`python3-gi`) |
| GUI (Non-recommended) | `X86_GUI_BACKEND=qt` (Qt WebEngine/Chromium) | Same |

> macOS-specific packages (`pyobjc`, `py_sip_xnu`, etc.) are excluded automatically via platform environment markers in `requirements.txt`.

### Windows

```cmd
cd 26x86
python -m venv ..\.venv
..\.venv\Scriptsctivate
pip install -r requirements.txt

python -m x86 --help
python -m x86 wizard
python -m x86 detect --json
python -m x86 status

REM Or use the batch wrapper:
26x86.bat
26x86.bat detect --json
```

Configuration and logs: `%APPDATA%x86\` (`config.json`, `logs\`).

### Linux

```bash
cd 26x86
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt

# WebKitGTK bindings (Debian/Ubuntu example)
sudo apt install python3-gi gir1.2-webkit2-4.1

python3 -m x86 --help
python3 -m x86 wizard
python3 -m x86 detect --json

chmod +x 26x86.sh
./26x86.sh
```

Configuration and logs: `~/.config/26x86/config.json`, `~/.local/state/26x86/logs/`.

### Platform Feature Matrix

| Feature | macOS | Windows / Linux |
|---------|-------|-----------------|
| `wizard` (HTML GUI) | ✅ Tauri / pywebview | ✅ Tauri (WebView2/WebKitGTK) or pywebview |
| `detect --json` | ✅ Mac hardware probe | ✅ Host OS and platform environment info |
| `status` | ✅ | ✅ Configuration JSON inspection |
| `build` / `patch` | ✅ | ❌ Offline configuration only (guided notices) |
| OpenCore EFI build | ✅ | ❌ |
| LaunchAgent (`com.26x86.*`) | ✅ | ❌ |

## Build Environment

### OpenCorePkg Build

```bash
bash scripts/build-opencore.sh
```

**Method A — Native (Xcode CLT required):**
```bash
cd 26x86-OpenCorePkg
./build_oc.tool
```

**Method B — Docker:**
```bash
brew install --cask docker   # Install Docker Desktop
cd 26x86-OpenCorePkg
docker compose up --build
```

Place build artifacts (`OpenCore-RELEASE.zip`, `OpenCore-DEBUG.zip`) into `26x86/payloads/OpenCore/` or run:

```bash
cd 26x86/payloads/OpenCore
python3 Update-OpenCore.command
```

### PatcherSupportPkg DMG Creation

```bash
cd 26x86-PatcherSupportPkg
python3 ci.py
# Or run Generate-DMG.command
```

### MetallibSupportPkg

```bash
cd 26x86-MetallibSupportPkg
pip install -r requirements.txt
python3 metallib.py --help
```

### App Bundle Build (PyInstaller)

```bash
source .venv/bin/activate
cd 26x86
python3 Build-Project.command
open ./dist/
```

## UTM Virtual Machine (Testing)

UTM or QEMU can be used to validate EFI boot configuration without modifying physical Mac hardware.

### UTM Installation

```bash
brew install --cask utm
# Or download directly from https://mac.getutm.app
```

### VM Template Setup

1. Launch UTM → **File → Import**
2. Select `vm/26x86-test.utm`
3. Mount the macOS Recovery image or installation ISO
4. Copy the generated OpenCore EFI layout to the virtual disk's EFI partition

See [wiki/Installation-Notes.md](./wiki/Installation-Notes.md) for virtualization host boundary details.

## Environment Variables

Copy `.env.example` to `.env` to configure localized asset paths:

```bash
cp .env.example .env
```

## Repository Relationships

| Repository | Upstream Origin |
|------------|-----------------|
| [26x86/26x86](https://github.com/26x86/26x86) | albert-mueller/OpenCore-Legacy-Patcher-T2 |
| [26x86/OpenCorePkg](https://github.com/26x86/OpenCorePkg) | albert-mueller/OpenCorePkg-add-T2-support |
| [26x86/PatcherSupportPkg](https://github.com/26x86/PatcherSupportPkg) | hackdoc/PatcherSupportPkg |
| [26x86/MetallibSupportPkg](https://github.com/26x86/MetallibSupportPkg) | dortania/MetallibSupportPkg |

Acidanthera kexts (Lilu, WhateverGreen, etc.) are fetched from upstream releases via `payloads/Kexts/Update-Kexts.command`.

## Troubleshooting

| Symptom | Resolution |
|---------|------------|
| `Python 3.9` error | Recreate `.venv` and verify Python 3.13+ is active |
| PyInstaller codesign failure | Reinstall with `PYINSTALLER_COMPILE_BOOTLOADER=1` |
| wxPython import failure | Run `pip install 'wxpython<4.2.5'` |
| Homebrew permissions issue | Run `sudo chown -R $(whoami) /usr/local/share/man/man8` or use MacPorts |
| OpenCore build error | Verify Xcode CLT is installed, then check `./build_oc.tool --help` |

## Related Documentation

- [wiki/README.md](./wiki/README.md) — Documentation index and architectural overview
- [SOURCE.md](../SOURCE.md) — Running from source
- [DISCLAIMER.md](../DISCLAIMER.md) — Legal and liability disclaimer
- [wiki/Developer.md](./wiki/Developer.md) — Contributor guide and English-only documentation standard
