# Build and development

**Current Status:** Source-bound validation workflow; CI is not OS-boot evidence.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Use the [module guide](Nextcore-Modules.md) for a recursive clone and actual
firmware commands; use [Setup](../SETUP.md) for application dependencies.
The [library](../library.md) indexes public contracts and dated verification.

## Development loop

1. Read `AGENTS.md` and obtain ownership of the relevant specification/module.
2. Establish the public contract before changing implementation.
3. Use independently authored fixtures for instruction, ABI or device behavior.
4. Run the closest meaningful test, then actual native/firmware consumers when
   the change crosses those boundaries. A check-only build cannot prove execution.
5. Keep source identities immutable through a receipt; normalize text before
   recording proof hashes. Integrate modules serially after their own tests.
6. Record missing runtime requirements explicitly and link [progress](../progress.md).

For A64 execution, generated x86, the Rust reference, actual C/Rust providers and
UEFI consumption are distinct proof surfaces. Negative controls must reject a
specific incorrect implementation or malformed capture. Original-input replay
uses local caller-owned inputs and cannot replace independent public fixtures.

## Publication and evidence

Module CI and the parent integration checks establish reproducibility for the
named source. They do not certify all hardware or a macOS boot. Preserve dated
receipts and label superseded instruction boundaries as history; do not rewrite
old captures to match new code. Check [compatibility](../compatibility.md) before
promoting any per-machine result.

Public documentation and code remain English. Keep original assets and raw
private traces outside the public tree. Follow [the boundary](../PUBLIC_VS_PRIVATE_BOUNDARY.md)
and [release policy](Branching-and-Release.md).
