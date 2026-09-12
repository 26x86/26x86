# Dynamic comparison source update validation

## Current Status

The active freeze is built from `git archive` of published ISE
`08156f4ba54a1bb4882beae30ea0e43b8614485a`, including the register-offset
implementation and final source inventory/comment commit. It contains 76 exact
runtime file hashes. Freeze SHA-256 is
`7a715e611a667a02baea2008881f94cb3973f86af3d6cd679b859cade6b82876`.
The working tree was not used to generate this freeze.

Compared with the preserved September 9 freeze, the changed production sources
are `arch.c`, `jit.c`, `memory_stage1.inc`, `preos/src/arch.rs`, and the documented
test-output comment in `preos/src/lib.rs`. These correspond to the committed A64
unknown-exception correction, UBFM, extended arithmetic, conditional selection,
and register-offset memory implementation. Associated test files changed, seven
runtime files were added (six test sources plus the preos Cargo lock), and no
previously frozen file was removed.

## Validation

The new native replay compiled the archived C JIT and canonical Rust memory
service and executed all six original captured cases. All six passed, with the
mutated captured ESR expectation rejected. The 14 comparator regression tests
passed, including a new rejection for clearing the unknown exception's IL bit.
The exact old freeze was also supplied as a negative input and rejected at the
freeze identity gate before runtime compilation.

The final full local replay is `/tmp/nextcore-ci-dynamic-08156f4`. Its receipt,
native output rows, and negative control are copied without alteration under
`evidence-20260912`. The receipt records before/after hashes for every runtime
file, all compared input files, comparator sources, native executable, and
captured Arm ELF. All original public oracle bytes remained unchanged.

## Target State

CI must replay this exact current freeze and run the comparator tests against
that fresh output. A future runtime source change must receive an explicit
reviewed freeze and replay; these results do not authorize accepting arbitrary
new hashes. Reproduce using the commands in `README.md` with a new output path.
The copied receipt is evidence of this specific native run, not a substitute
for a new execution after code changes or a physical macOS boot claim.
