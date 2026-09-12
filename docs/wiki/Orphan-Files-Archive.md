# Orphan & Deprecated Files Archive

**Current Status:** Historical archive index; entries are not active deployment instructions.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Record of deprecated and archived assets removed from the active tree during code health cleanups.

## Archived Documentation

| Path | Reason for Removal / Successor |
|------|--------------------------------|
| `docs/ARCHITECTURE-26x86.md` | Consolidated into [Developer.md](./Developer.md) and [wiki/Architecture.md](./Architecture.md) |
| `docs/KOREAN_EDITION.md` | Removed under universal English-only documentation mandate |
| `docs/SETUP.en.md` | Unified directly into canonical [SETUP.md](../SETUP.md) |
| `docs/wiki/README.en.md` | Unified directly into canonical [wiki/README.md](./README.md) |

## Archived Scripts & Binaries

| Asset | Notes |
|-------|-------|
| Legacy shell wrappers | Replaced by unified `26x86.command`, `26x86.bat`, and `26x86.sh` |
| Obsolete test payloads | Replaced by automated Python test suites in `tests/` |

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
