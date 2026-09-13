# Exact ISAR0 revision replay

## Current Status

The active runtime is a Git archive of ISE
`29413d9ca770c2b6e9487f91838452c7987f3a4e`. All 114 runtime files match their
exact Git blobs. The source-freeze SHA-256 is
`557bf4cb1e531941b375f65e7b1aab1b19591e0faac099ce4fb058c8ca593ddc`.

Seven runtime files changed: native JIT, C register API, Rust reference and
four independent verification files. The exact read-only ISAR0 instruction
returns the field-derived absent-extension value only at EL1 with inactive
live HCR/SCR. Independent tests pass 928 native assertions, 35 reference tests,
32 canonical provider tests per cache mode, and rejection of 16 extensions.
The 32 Cortex-A72 destination observations validate encoding/access/XZR/NZCV;
their hardware feature value is deliberately distinct from the software policy.

All six unchanged captured inputs, fourteen comparator regressions and three
negative controls pass. The preceding freeze identity and altered runtime copy
are rejected before compilation. Captured inputs and expectations are unchanged.
All 172 earlier history/evidence files remain byte-identical. Eight selected
preceding files are preserved in `history/401619a`; new receipts are in
`evidence-isar0-20260913`.

## Target State

Preserve exact source identity and captured expectations in future revisions.
This replay still stops at unsupported, nonretired HVC with ESR `0x02000000`.
It does not establish original reset ABI, normal startup or a physical desktop.
