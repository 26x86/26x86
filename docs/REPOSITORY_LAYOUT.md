# Repository layout and ownership

**Current Status:** Seven-module ownership and separate legacy research/export scope.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

The integration repository records exact commits for seven independent NextCore
module repositories. [Module repositories](wiki/Nextcore-Modules.md) is the
canonical clone/build/publication guide; the [documentation library](library.md)
indexes specifications and verification material.

| Location | Owns |
| --- | --- |
| `nextcore/crates/nextcore-core` | Formats, configuration, placement and owned staging |
| `nextcore/crates/nextcore-efi` | UEFI picker, handoff and firmware consumers |
| `nextcore/crates/nextcore-ise` | A64 generated-native execution, reference CPU and checked memory service |
| `nextcore/crates/nextcore-tool` | CLI orchestration |
| `nextcore/crates/nextcore-hal` | Platform descriptions and device contracts |
| `nextcore/crates/nextcore-gpu` | Graphics/backend experiments and evidence |
| `nextcore/crates/nextcore-apls` | Execution adapters and guest contracts |
| `x86/`, `Tools/`, `integration/` | Application, integration and validation tools |
| `docs/` | Public guides, specifications and dated evidence boundaries |
| `_isolated/` | Ignored local inputs and private runtime material; never published |

The allocation-free `nextcore-memory-service` package is owned inside ISE; it is
not an eighth Git submodule. Parent Cargo patches bind both ISE packages to the
same local checkout. Standalone dependencies use immutable remote revisions.

External OpenCore/support packages and separately maintained VMApple/QEMU
research remain attributed to their own source identities. They are not the
seven clean-room workspace modules and do not replace the physical x86 EFI
product runtime. See [Upstream repositories](wiki/Upstream-Repositories.md).

## Updating published modules

Commit and validate changes inside the owning module, publish its reviewed
source, then integrate the exact gitlink and dependency identities in the parent.
Verify fresh recursive resolution before publication. Do not use an exporter to
reinitialize existing module histories or recreate release tags. Never substitute
`git submodule update --remote` for an immutable integration checkout.

Legacy export/synchronization tools are historical migration utilities, not the
routine module release path. Review their side effects before use; documentation
refreshes do not authorize repository creation, release deletion or tag changes.

[Progress](progress.md) records release and execution evidence separately.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](index.md), [progress](progress.md),
[compatibility catalog](compatibility.md) and
[library](library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
