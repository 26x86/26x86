# 26x86 Wiki

<div align="center">
<img src="../../resources/branding/26x86-logo-256.png" alt="26x86 Logo" width="128" />
</div>

**26x86** — NextCore EFI boot engineering and compatibility tooling for macOS 26 (Tahoe) on x86-based Macintosh systems.

> **Documentation Standard:** All official documentation is maintained strictly in English.

---

## Quick Start

| Method | Command |
|--------|---------|
| **Recommended** | Double-click `26x86.command` |
| Wizard | `python3 -m x86 wizard` |
| CLI | `python3 -m x86 --help` |

```bash
python3 -m x86 detect [--json]
python3 -m x86 build [--model ...]
python3 -m x86 patch [--auto]
python3 -m x86 status
```

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [Warnings.md](./Warnings.md) | Consolidated warnings and hardware risks |
| [Known-Issues.md](./Known-Issues.md) | Known issues and current mitigation status |
| [Disclaimer.md](./Disclaimer.md) | Legal and warranty disclaimer summary |
| [GPU-Limitations.md](./GPU-Limitations.md) | GPU compatibility tiers and graphics acceleration status |
| [Pre-AVX-Mac-Pro.md](./Pre-AVX-Mac-Pro.md) | Pre-AVX Mac Pro (5,1 / 6,1) detection and mitigation |
| [Safari-PreAVX-Fix.md](./Safari-PreAVX-Fix.md) | Safari 26 Pre-AVX instruction bypass |
| [Mac-Pro-Tahoe-Yellow-Screen.md](./Mac-Pro-Tahoe-Yellow-Screen.md) | WindowServer and compositor tint troubleshooting |
| [T2-Mac-Notes.md](./T2-Mac-Notes.md) | Apple T2 security chip considerations |
| [Installation-Notes.md](./Installation-Notes.md) | Clean installation and upgrade procedures |
| [Configuration.md](./Configuration.md) | Configuration paths and environment settings |
| [Migration.md](./Migration.md) | Migration from earlier patchers to 26x86 |
| [Upstream-Repositories.md](./Upstream-Repositories.md) | Upstream projects and integration map |
| [Developer.md](./Developer.md) | Contributor guidelines and English-only documentation standard |
| [Orphan-Files-Archive.md](./Orphan-Files-Archive.md) | Deprecated and cleaned asset archive |

---

## Legal & Licensing

[DISCLAIMER.md](../../DISCLAIMER.md) · [LICENSE.txt](../../LICENSE.txt) · [NOTICE.md](../../NOTICE.md) · [CREDITS.md](../../CREDITS.md) · [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md)

## External Links

- [Releases](https://github.com/26x86/26x86/releases)
- [Security Policy](https://github.com/26x86/26x86/security/policy)
