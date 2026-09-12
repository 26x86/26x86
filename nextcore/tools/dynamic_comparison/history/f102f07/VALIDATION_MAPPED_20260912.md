# Immutable mapped PAC revision replay

The active source is an immutable `git archive` of ISE
`f102f0769fcae98597478f6738ee1a69247e5207`. Its 90-file freeze SHA-256 is
`a844d285bd7d66863d86d096e4bd7799642579c58fb93424e3c8863a162040bc`.
Every archive file was independently compared against the SHA-256 of its exact
`git show <commit>:runtime/<path>` bytes before replay. The comparator verifies
that identity and all runtime file hashes before compilation and after execution.

The source delta from `bd3a8195385106ce9bdeb09160a3f1bfb447ea11` contains twelve
runtime implementation/test files, listed with old/new hashes in
`evidence-mapped-20260912/preservation.json`. The distinct PAC-capable v2 wrapper
preserves the original entry's gate and rejects immutable callback control
mutation before commitment. Run-local v2 native reuse retains fresh fetch and
control checks. Baseline QARMA5 supports 47/48-bit addresses and PACGA. Actual
QEMU APA=5 upper enabled signatures are explicitly outside the canonical APA=1
comparison; the module documentation and independent PAC receipt retain that
feature boundary. No dynamic profile-2 behavior is intentionally changed.

Fresh generated-x86 execution reproduced all six unchanged captured-Arm cases.
All fourteen comparator regressions passed. Three negative controls were
rejected: changed captured ESR, the old freeze identity, and an appended comment
in a separate runtime copy. The latter two fail before compilation. The only
`compare.py` change is the admitted freeze identity; no captured input or
acceptance predicate was changed.

`evidence-mapped-20260912` contains `receipt.json`, `actual.tsv`, the three
negative-control receipts, `comparator-regressions.json`, and `preservation.json`.
All 67 pre-existing history/evidence files remain byte-identical. Eight selected
files from the preceding package are retained in `history/bd3a819`; history and
evidence were not recursively duplicated. The original captured oracle inputs
retain their manifest-pinned bytes.

This checks dynamic profile 2 against captured Arm observations. Independent
native and authored EFI tests own the new mapped/PAC/cache behavior. The unchanged
HVC boundary remains unsupported and nonretired with ESR `0x02000000`.
These results do not establish a private original entry ABI, physical boot,
completed macOS initialization, or a desktop.
