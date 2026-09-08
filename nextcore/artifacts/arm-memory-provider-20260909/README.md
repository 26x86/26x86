# x86 EFI caller-owned memory provider proof

Actual x86 OVMF execution passes 23 authored provider cases (11 scalar, 6 pair, 6 range/PC boundaries), plus 1 separately built callback transport-failure case. The 17 scalar/pair cases also match exact fetch/data/completed counters and data-alignment FAR. The service callback and C caller execute under the firmware Win64 ABI.

A real direct-path EFI still computes the correct signed byte result but is rejected by the provider verifier (exit 1). A separate Rust callback variant returns -7 on data requests before any transfer; EFI reports provider_status=4, no fabricated ESR/FAR, and no completed/retired data operation. The production provider source is unchanged.

This is M=0, caller-owned RAM with Boot Services active. It does not establish M=1 translation, post-fault RAM observation, physical-machine execution, macOS boot, or guest Metal. SP-alignment FAR is captured but has no architectural-value assertion in these tests.

## Evidence

- `build-results.json`: fresh builds, 101 input source hashes before/after, binary hashes.
- `replay-results.json`: actual complete replay and expected bypass failure.
- `scalar-results.json`, `pair-results.json`, `provider-observations.json`: 17 cases with legacy architectural checks and additional provider counters/FAR.
- `edge-results.json`: missing scalar backing, missing second pair element with unchanged destinations/base, missing fetch, and exact PC-alignment ESR/FAR/ELR.
- `transport-results.json`, `transport-mutation.json`: actual callback transport failure and precise authored source mutation.
- `bypass-execution.json`, `bypass-negative.json`: successful direct execution and failed provider verification.
- `serial/`: 25 original authored execution logs.

The four scalar/pair fixture and verifier files are byte-for-byte copies of the earlier public proofs. New wrappers add provider checks; historical proof files were not edited. `provenance.json` distinguishes the early development binary from the fresh three-variant build used by the full replay. The later tiered-trace integration is a separate source/binary result.

## Reproduce

Use Linux x86_64/WSL2 with Rust 1.98.1 and its x86_64-unknown-uefi target, clang/LLVM tools, qemu-system-x86_64, OVMF and Python 3. The captured tool versions are in `provenance.json`; `build-Cargo.lock` pins registry dependencies.

For the exact historical source, use fresh Nextcore-EFI at 6feba80a9ceea22811b6bf08f98010501654375e, Nextcore-ISE at 41e8997c4b8d6f029ed3a3fbec0669374046ab6f, and Nextcore-Core at 6105cd7996ef2ea4db35d7d3a1e8822d0703aae9. Apply `efi-provider.patch` from inside the fresh EFI checkout. Its output was checked against all three frozen EFI source hashes. The final integrated module also contains this provider feature but is a distinct source identity.

```sh
python3 build_variants.py --efi-source /path/Nextcore-EFI --ise-source /path/Nextcore-ISE --core-source /path/Nextcore-Core --output /tmp/provider-build
python3 reproduce.py --provider-efi /tmp/provider-build/target-provider/x86_64-unknown-uefi/release/NXARMJIT.efi --direct-efi /tmp/provider-build/target-direct/x86_64-unknown-uefi/release/NXARMJIT.efi --transport-efi /tmp/provider-build/target-transport/x86_64-unknown-uefi/release/NXARMJIT.efi --tools /path/26x86/nextcore/tools --output /tmp/provider-replay
```

The output directories must be new. Build inputs are read-only; the scripts create isolated workspaces and the failure-injection copy beneath the output directory. Both public scripts were run successfully from fresh output directories. Build locations and toolchain/linker metadata can change binary hashes; each actual run records its own hashes. No generated EFI/firmware/ESP binary is included in this source-and-receipt bundle.
