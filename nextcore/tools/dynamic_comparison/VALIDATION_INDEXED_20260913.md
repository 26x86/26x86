# Scalar immediate writeback revision replay

## Current Status

The active runtime is a Git archive of ISE
`fa5fe9e1b78cfce6b3bf0a0da82e68ece0704979`. All 102 runtime files match their
exact Git blobs. The source-freeze SHA-256 is
`d1b92f8bd96264ed3b372b09f77d5e02da038c770d6b32a58947a0f9305dc2d4`.

Eight runtime files changed: native and reference scalar writeback, matching
store-fault classification, four independent indexed verification files, and
the existing unscaled test's now-obsolete pre/post rejection assertions.
The thirteen scalar forms support pre/post indexing with successful-transaction
writeback. Independent Arm, native, reference, provider and EFI tests establish
these instruction semantics separately.

The six unchanged captured-input comparisons, fourteen comparator regressions
and three negative controls pass. The preceding freeze and altered runtime
copies are rejected before compilation. No captured input or expected result
changed. All 127 previous history/evidence files remain byte-identical; eight
selected preceding files are preserved in `history/617a3d8`. New receipts and
preservation hashes are in `evidence-indexed-20260913`.

## Target State

Keep exact source identity and unchanged captured expectations across subsequent
changes. This diagnostic still stops at unsupported, nonretired HVC with ESR
`0x02000000`. It does not establish original reset ABI, complete kernel
initialization, physical boot or a desktop.
