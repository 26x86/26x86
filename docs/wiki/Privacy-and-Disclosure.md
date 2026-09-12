# Privacy and disclosure boundary

**Current Status:** Public/private disclosure rules; private inputs remain outside public artifacts.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

The public repository contains OpenCore integration, clean-room Nextcore
contracts, public specifications, and reproducible user-facing tooling.

Private research is not part of the public documentation index. In particular,
do not expose internal project names, private backend implementation details,
Apple-extracted blobs, certificates, firmware images, or reverse-engineering
transcripts in public docs or links.

The `_isolated/` directory is reference-only and remains excluded from staged
public work. When a public document needs a decision from another ownership
slot, record an `OPEN_QUESTION` in the owning document rather than copying
private material into the public tree.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
