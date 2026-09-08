# NextCore module integration review — 2026-09-08

Read-only review requested after runtime relocation. Findings sent to integration owner; module publication was still in progress at review time.

## Actionable findings

1. `Tools/verify_nextcore_submodules.py` uses line-delimited, default Git-quoted output for private-path detection. A filename with a non-ASCII component under `_isolated/` is quoted by Git; `Path(quoted_name).parts` therefore begins with a quote and misses the exact `_isolated` component. Use `git ls-files -z` and split on NUL without stripping filename bytes. Pure string fixtures demonstrate the parser error; no private paths or assets were staged or added.
2. EFI still has sibling path dependencies on Core and ISE. Publish those module revisions and replace the EFI dependencies with revision-pinned Git dependencies before validating a standalone EFI clone. The integration workspace patches correctly keep its seven crates local.
3. EFI CI checks all features but links only NXAPFS. Add an NXARMJIT link build with the `arm-jit` feature, because `cargo check` does not establish that the native JIT/GOP archive links. Ensure clang and llvm-ar are present in CI.

## Confirmed relocation properties

- Every C source linked by EFI/build.rs and its quoted headers exists under ISE/runtime.
- The generated PAC module uses the ISE-owned runtime/preos/src/pauth.rs file.
- ISE exports its runtime source directory through EFI_RUNTIME_DIR; no monorepo path is needed by the new EFI build script.
- Legacy runtime/main.c reaches ISE/devices/aic_v1.h through its existing relative include; the device directory was relocated with the runtime.
- runtime/preos has a standalone Cargo workspace declaration.
- The seven integration patches and verifier's package-source/manifest/workspace checks prevent silently resolving a second remote NextCore package.
- GOP implementation source hashes match the pre-relocation validated files. Artifact source paths were updated to nextcore/crates/nextcore-ise/runtime.

This review does not verify remote commit availability. The integration owner's fresh recursive clone and standalone builds establish publication completeness after the final commits.
