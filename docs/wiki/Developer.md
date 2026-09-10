# Developer & Contributor Guide

Contributor guidelines, codebase layout, and universal documentation standards for 26x86.

---

## ⚠️ Mandatory Documentation Policy: FORCE English Only

> [!IMPORTANT]
> **Universal English-Only Rule:**
> All documentation, architectural specifications, code comments, commit messages, CLI user messages, and PR descriptions across all 26x86 and NextCore repositories MUST be written strictly in **English**.
> - No bilingual documents, Korean-only documents, or foreign language drafts are permitted in the repository or doc builds.
> - Pull requests containing non-English text in `docs/` or source comments will fail automated CI checks.

---

## Repository Structure

| Path | Responsibility |
|------|----------------|
| `x86/` | CLI, wizard GUI backends, platform detection, and configuration management |
| `opencore_legacy_patcher/` | Legacy patch and OpenCore payload building shims |
| `payloads/` | Upstream kext payloads, OpenCore binaries, and helper scripts |
| `ci_tooling/` | Packaging automation, CI builds, and validation tooling |
| `docs/` | Single source of truth for all public and architectural documentation |
| `nextcore/` | NextCore clean-room boot stack modules and tools |

## Running & Building

```bash
# macOS
python3 26x86.command
python3 -m x86 detect --json
python3 Build-Project.command

# Windows
python -m x86 wizard
26x86.bat

# Linux
python3 -m x86 wizard
./26x86.sh
```

## Cross-Platform Boundaries

Full EFI deployment, live system patching, and LaunchAgent daemon installation require macOS. Windows and Linux environments provide CLI configuration, offline bundle generation, hardware profile inspection, and the HTML wizard GUI.

## Configuration Defaults

- **macOS:** `~/Library/Application Support/26x86/config.json`
- **Windows:** `%APPDATA%\26x86\config.json`
- **Linux:** `~/.config/26x86/config.json`

## Licensing & Attribution

All contributions must adhere to clean-room development practices. See [PUBLIC_VS_PRIVATE_BOUNDARY.md](../PUBLIC_VS_PRIVATE_BOUNDARY.md), [CREDITS.md](../../CREDITS.md), and [NOTICE.md](../../NOTICE.md).
