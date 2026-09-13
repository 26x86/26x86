# Scalar unscaled revision replay

The active source is an immutable `git archive` of ISE
`ea0a892c4d55c0c09df35c576931c5a6f65c1426`. Its 94-file freeze SHA-256 is
`d95ea24671cd64c340ce5e4662ea4cf02f96fefd91328c431ac63b23819807f0`.
Every archive file was independently matched to its exact Git blob before replay.
The comparator checks the admitted freeze identity and all runtime hashes before
compilation and after execution.

The runtime delta from `b4f34be46cc5f61a531c084595a747a2f4a13ad4` contains seven
files: `arch.c`, `jit.c`, `preos/src/arch.rs`, three unscaled test files and their
runner. Exact old/new hashes appear in `evidence-unscaled-20260912/preservation.json`.
The change admits thirteen integer scalar unscaled forms with signed nine-bit
byte displacement and no writeback, and classifies their precise store-fault
syndromes consistently. Existing alignment and memory-provider contracts remain
unchanged. This replay uses the existing dynamic profile-2 captured inputs;
independent native/reference/EFI tests own the new instruction-family proof.

Fresh generated-x86 execution reproduced all six unchanged captured-Arm cases.
All fourteen comparator regressions passed. Three negative controls were rejected:
changed captured ESR, the preceding freeze identity, and an appended comment in
a separate archived runtime copy. The latter two fail before compilation. The
only `compare.py` change is its admitted freeze hash. No capture, expected
retirement, terminal instruction or acceptance predicate was changed.

`evidence-unscaled-20260912` contains the execution receipt, `actual.tsv`, three
negative-control receipts, comparator regressions and preservation hashes.
All 97 pre-existing history/evidence files remain byte-identical. Eight selected
files from the preceding package are retained in `history/b4f34be`; history and
evidence were not recursively duplicated. Original captured oracle inputs retain
their manifest-pinned bytes.

The HVC boundary remains unsupported and nonretired with ESR `0x02000000`.
These results do not establish an original entry ABI, completed initialization,
physical macOS boot or a desktop.
