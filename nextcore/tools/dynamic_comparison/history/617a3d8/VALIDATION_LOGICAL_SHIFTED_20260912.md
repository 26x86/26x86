# Logical shifted-register revision replay

## Current Status

The active runtime is a `git archive` of ISE
`617a3d8355bde87da695bd92e11539dfaef2923a`. All 98 runtime files match their
exact Git blob hashes. The source-freeze SHA-256 is
`f9ad771f3b851ea340d41496bc28ec682122a5ec40e8b964c4e7a6a5489206a3`.

The six changed runtime files contain the native/reference logical
shifted-register implementation and four independently authored verification
files. Eight operations support both widths, all four shifts, ZR, precise flags
and reserved W-shift rejection. Independent native, actual Arm, reference and
canonical-provider tests establish the new instruction semantics separately.

The unchanged captured-input comparison passes all six cases. Fourteen existing
comparator regressions and three negative controls pass: changed captured ESR,
the preceding freeze identity, and an appended comment in a separate runtime
archive copy. The latter two reject the input before compilation. No captured
input, expected retirement, terminal instruction or acceptance predicate changed.

All 112 pre-existing history/evidence files remain byte-identical. Eight selected
files from the preceding comparison are retained in `history/ea0a892`; previous
history and evidence were not recursively duplicated. The only comparator code
change admits the new source-freeze hash. `evidence-logical-shifted-20260912`
contains the receipt, actual results, negative controls, regression logs and
preservation hashes.

## Target State

Retain exact source and captured-input identity across subsequent implementation
changes. This replay continues to stop at unsupported, nonretired HVC with ESR
`0x02000000`. It does not establish the original entry ABI, completed kernel
initialization, physical macOS boot or a desktop.
