# 26x86 Configuration

26x86 maintains an independent configuration schema, automated patch management, and application directory structure. It **does not share paths** with upstream OpenCore Legacy Patcher.

> For migration instructions: see [Migration.md](./Migration.md).

## Configuration Paths

| Operating System | Path |
|------------------|------|
| macOS | `~/Library/Application Support/26x86/config.json`<br>Legacy fallback: `~/Library/Preferences/com.26x86.plist` |
| Windows | `%APPDATA%\26x86\config.json` |
| Linux | `~/.config/26x86/config.json` |

## Key Configuration Fields

```json
{
  "General": {
    "AutoPreAVXPatch": true,
    "AutoUpdateEFI": false,
    "VerboseBoot": true
  },
  "Hardware": {
    "TargetModel": "MacPro5,1",
    "GPUClass": "AMD_GCN"
  },
  "Storage": {
    "TargetDisk": "/dev/disk0"
  }
}
```

## Environment Variables

- `X86_CONFIG_PATH`: Override default path to `config.json`.
- `X86_GUI_BACKEND`: Specify GUI backend (`tauri`, `pywebview`, or `qt`).
- `X86_LOG_LEVEL`: Set logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
