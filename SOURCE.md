# Building and Running from Source

26x86 is a Python-based GUI/CLI application and clean-room boot engineering tool.

Verified releases: [Releases](https://github.com/26x86/26x86/releases)

> Operational considerations: see [docs/wiki/Warnings.md](docs/wiki/Warnings.md).

## Getting Started

**Python 3.13+** is required. Use official distributions from [python.org](https://www.python.org/downloads/macos/) or `uv`.
System Python installations bundled with macOS or Xcode Command Line Tools are **not supported**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

```bash
python3 26x86.command              # Wizard GUI (Tauri preferred)
python3 -m x86 wizard              # Equivalent invocation
python3 -m x86 --help              # Command-line interface help
python3 -m x86 detect --json       # Hardware detection
```

The default graphical frontend uses **Tauri** (macOS: WKWebView, Windows: WebView2) connected via a local HTTP bridge. If Tauri binaries are not present, the app falls back to pywebview (Cocoa). For building the shell, see [gui-tauri/README.md](gui-tauri/README.md).

## Building Application Bundles

```bash
python3 Build-Project.command
```

For complete development environment setup: see [docs/SETUP.md](docs/SETUP.md).
