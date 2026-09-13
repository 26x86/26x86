# Immutable unaligned profile revision replay

## Current Status

The active source is an immutable `git archive` of ISE
`bd3a8195385106ce9bdeb09160a3f1bfb447ea11`. The 84-file freeze SHA-256 is
`283ce5878bdf12bb270e10e846332c043a23aed6f47e0a08091eab8cec3269fa`.
Every archived runtime file was independently SHA-256 matched to the bytes from
`git show bd3a8195385106ce9bdeb09160a3f1bfb447ea11:runtime/<path>` before replay.
`source-freeze.json` contains those exact Git-blob source hashes. The comparator
checks them before compilation and after execution, and admits the freeze only
through its exact hardcoded identity.

Review against `f387224baf43fc309436d2f27a5ca4677c8b2008` found seven changed
runtime files: the C/Rust ABI constants, `memory_boot_v2.h`, `memory_stage1.inc`,
`memory-service/src/stage1.rs`, the existing stage-1 test, and the new independent
unaligned-profile test. Profile 3 fixes SCTLR.A=0 while retaining immutable
Normal-NC controls. The shared reply validator permits byte-granular in-span
faults for its ordinary unaligned transfers and rejects fabricated alignment
faults. The Rust service preflights every byte before stores. Dynamic profile 2
still maps controls to strict profile 1 with SCTLR.A=1, including its M=0 state.
No captured input, acceptance predicate, retirement boundary or syndrome changed.

Fresh native replay passes all six unchanged captured-Arm cases. All 14 existing
comparator regression tests pass. The captured ESR-bit mutation is detected.
An old freeze identity and a comment appended to a separate archived runtime
copy are both rejected before any compilation starts. The only `compare.py`
change is the admitted freeze hash.

The `evidence-unaligned-20260912` directory contains:

- `receipt.json` and `actual.tsv`: actual native execution and exact checks.
- `negative-control.json`: captured ESR expectation mutation rejection.
- `old-freeze-negative.json`: preceding identity rejected before compilation.
- `runtime-mismatch-negative.json`: changed runtime rejected before compilation.
- `comparator-regressions.json`: 14 tests with no errors or failures.
- `preservation.json`: exact source delta, Git-blob verification count, and hashes
  of 52 pre-existing history/evidence files and eight selected archived files.

The preceding selected package is preserved under `history/f387224b`. All 52
pre-existing history/evidence files retain their previous bytes. No evidence or
history was recursively duplicated. Original captured oracle inputs retain their
manifest-pinned bytes, as verified by the fresh replay receipt.

## Target State

Maintain this exact captured-Arm regression gate for the selected runtime. This
replay exercises dynamic profile 2, not profile 3. Separate native and authored
OVMF acceptance owns profile-3 behavior. Mapping construction, PAC support and
the original image's entry ABI remain separate contracts. The unchanged HVC
boundary remains unsupported and nonretired with exact ESR `0x02000000`.
These results do not establish physical startup or a macOS desktop.
