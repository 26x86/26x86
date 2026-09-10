# BP31 — macOS 27 ARM64e Entry Contract Verification

Read-only audit: Repositories, modules, source images, and execution configurations were not altered. Re-analyzed preserved IPSW metadata, extracted structures, and public Apple/XNU documentation.

## Scope & Purpose

This contract defines the entry state expectations for early AArch64 kernel execution in macOS 27:
- Initial translation regimes and page table setup.
- Register state upon entry (`X0` pointing to boot argument structures).
- Exception level expectations (EL1 vs. EL2).
- Memory attributes and device tree positioning in physical RAM.

## Verification Boundaries

- Synthetic test fixtures written for `nextcore-ise` validate instruction decoding and memory access semantics.
- Hardware virtualization on Apple Silicon hosts uses Virtualization.framework directly, distinct from x86 translation harnesses.
