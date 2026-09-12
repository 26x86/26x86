# Developer & Contributor Guide

**Current Status:** Contributor instructions; use current manifests and workflow receipts.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Contributor guidelines, codebase layout, and universal documentation standards for 26x86.

---

## ⚠️ Mandatory Documentation Policy: FORCE English Only

> [!IMPORTANT]
> **Universal English-Only Rule:**
> All documentation, architectural specifications, code comments, commit messages, CLI user messages, and PR descriptions across all 26x86 and NextCore repositories MUST be written strictly in **English**.
> - No bilingual documents, Korean-only documents, or foreign language drafts are permitted in the repository or doc builds.
> - Public documentation is checked by the documentation CI policy; source review must also enforce the English-only rule. Do not assume a documentation test audits every source comment.

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

The application's live root-patching and macOS service workflows require their supported Darwin host. Windows/Linux support inspection and developer builds within their own contracts; compiling EFI is separate from deploying or physically booting it. Use [Setup](../SETUP.md) and [Module repositories](Nextcore-Modules.md) for current commands.

## Configuration Defaults

- **macOS:** `~/Library/Application Support/26x86/config.json`
- **Windows:** `%APPDATA%\26x86\config.json`
- **Linux:** `~/.config/26x86/config.json`

## Licensing & Attribution

All contributions must adhere to clean-room development practices. See [PUBLIC_VS_PRIVATE_BOUNDARY.md](../PUBLIC_VS_PRIVATE_BOUNDARY.md), [CREDITS.md](https://github.com/26x86/26x86/blob/main/CREDITS.md), and [NOTICE.md](https://github.com/26x86/26x86/blob/main/NOTICE.md).

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
