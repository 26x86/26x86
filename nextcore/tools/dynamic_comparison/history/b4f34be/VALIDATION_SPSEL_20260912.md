# Immutable stack-selection revision replay

The active source is an immutable `git archive` of ISE
`b4f34be46cc5f61a531c084595a747a2f4a13ad4`. Its 90-file freeze SHA-256 is
`d0af1c6dd5d238bf3036a2be96b7e4ed9b8d52ff6eeae8fe9fd2b5ab207c773a`.
Every archive file was independently compared against the SHA-256 of its exact
Git blob before replay. The comparator verifies that identity and all runtime
file hashes before compilation and after execution.

The runtime delta from `f102f0769fcae98597478f6738ee1a69247e5207` contains three
files: `memory_stage1.inc`, `test_mapped_provider.rs`, and
`test_mapped_snapshot.c`. Their exact old/new hashes are retained in
`evidence-spsel-20260912/preservation.json`. The implementation accepts only two
SPSel immediate encodings at EL1 in the immutable v2 path. It saves the active
stack bank, changes PSTATE.SP, loads the selected bank and retires once. M0,
dynamic execution, immutable controls and other system boundaries are unchanged.

Fresh generated-x86 execution reproduced all six unchanged captured-Arm cases.
All fourteen comparator regressions passed. Three negative controls were
rejected: changed captured ESR, the old freeze identity, and an appended comment
in a separate runtime copy. The latter two fail before compilation. The only
`compare.py` change is the admitted freeze identity. No captured input or
acceptance predicate was changed.

`evidence-spsel-20260912` contains `receipt.json`, `actual.tsv`, the three
negative-control receipts, `comparator-regressions.json`, and `preservation.json`.
All 82 pre-existing history/evidence files remain byte-identical. Eight selected
files from the preceding package are retained in `history/f102f07`; history and
evidence were not recursively duplicated. Original captured inputs retain their
manifest-pinned bytes.

This checks dynamic profile 2 against captured Arm observations; it does not
exercise the newly supported immutable-v2 SPSel path. Separate independent
native and authored EFI tests own that behavior. The unchanged HVC boundary
remains unsupported and nonretired with ESR `0x02000000`. These results do not
establish an original entry ABI, physical boot, completed macOS initialization,
or a desktop.
