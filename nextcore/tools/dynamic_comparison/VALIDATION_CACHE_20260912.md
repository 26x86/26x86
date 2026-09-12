# Provider cache revision replay

## Current Status

The active source is an immutable `git archive` of ISE
`f387224baf43fc309436d2f27a5ca4677c8b2008`. Its 83-file freeze SHA-256 is
`6de2b14b1a43a293954beb303edbf6048e81d691597d0ab5e203a9b61f374d75`.
The comparator admits this exact freeze through its hardcoded identity and
checks every listed runtime file before compilation and after execution.

Review against the previous `002d2eff8b262e728224b9b039b9ffe168ed4586`
freeze found three runtime file changes: `jit.c`, the new native cache
acceptance test, and its standalone test runner. The production change adds
bounded run-local native-entry reuse only to `vf_run_memory_provider` (v1).
Lookup follows a fresh validated fetch and keys on PC, instruction, and EL.
The default uses up to 64 slots of 1,024 bytes, preserves full-buffer fallback,
and publishes entries only after successful executable protection. The dynamic
provider and memory-service sources used by this comparator remain unchanged.
No new ISA semantics, entry registers, or comparison expectations were added.

All six unchanged captured-Arm cases and all 14 existing comparator regressions
pass. The captured ESR-bit mutation is detected. Two independent pre-compilation
negative controls reject the preceding freeze identity and a comment appended
to an isolated copy of the archived runtime. No acceptance predicate changed;
the comparator code delta is its admitted freeze hash only.

Sanitized authored receipts are in `evidence-cache-20260912`:

- `receipt.json` and `actual.tsv`: fresh native execution and captured-state checks.
- `negative-control.json`: mutated captured ESR expectation is rejected.
- `old-freeze-negative.json`: previous identity is rejected before compilation.
- `runtime-mismatch-negative.json`: modified runtime is rejected before compilation.
- `comparator-regressions.json`: 14 tests, no failures or errors.
- `preservation.json`: previous history/evidence hashes and selected source archive.

Eight selected active source, freeze, and documentation files are preserved
byte-for-byte under `history/002d2ef`. All 37 pre-existing files in historical
packages and evidence directories retain their original hashes. Captured oracle
inputs retain their manifest-pinned bytes. Prior evidence and histories were
not recursively copied, regenerated, or reinterpreted.

## Target State

Use this exact source freeze for the maintained captured-Arm regression gate.
This dynamic replay does not exercise the v1 cache or measure its performance;
the separately authored cache acceptance and EFI integration checks own those
claims. Native HVC remains unsupported and nonretired with the existing exact
diagnostic syndrome. Neither this replay nor the cache change establishes
physical hardware startup, SPTM provisioning, or a macOS desktop.
