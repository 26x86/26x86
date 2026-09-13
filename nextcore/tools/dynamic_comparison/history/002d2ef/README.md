# Active captured-Arm dynamic comparison

## Current Status

The active exact runtime is ISE `002d2eff8b262e728224b9b039b9ffe168ed4586`,
including BFM and prior multiply/reference branch corrections. Its fresh
six-case replay and 14 comparator tests passed; see
`VALIDATION_BFM_20260912.md` and `evidence-bfm-20260912`.
The preceding `7cd9ac0` selected source package is preserved byte-for-byte
under `history/7cd9ac0`; existing `evidence-madd-20260912` remains in place.

The preceding `a8a06da` source package is preserved byte-for-byte under
`history/a8a06da`, with its existing `evidence-tbz-20260912` left in place.
Only selected sources, the exact freeze and documentation are copied; histories
and evidence are never recursively duplicated.

The preceding `08156f4` comparator sources, freeze, and documentation are
preserved byte-for-byte under `history/08156f4`. Their original
`evidence-20260912` remains in place and is not recursively copied into history.
Use that history's `compare.py` with archived ISE `08156f4` to reproduce it;
the active comparator accepts only the new freeze identity.

This is the maintained comparator for the immutable six-case oracle in
`nextcore/artifacts/arm-dynamic-oracle-20260909`. The original comparator,
source freeze, manifests, and evidence under
`nextcore/artifacts/arm-dynamic-comparison-20260909` remain unchanged and describe
their original runtime revision.

The active runtime includes the A64 unknown-exception correction: EC=0, IL=1,
ISS=0, so the full ESR is exactly `0x02000000`. The comparison still requires
the unchanged terminal HVC opcode, no HVC retirement, the exact exception PC
and saved state, and the original captured memory and control effects. It does
not reinterpret the original Arm HVC-to-EL2 completion as native support.

## Target State

Each new runtime revision must reproduce all six captures and pass the negative
controls against a reviewed exact source freeze. `compare.py` verifies the
freeze file's own hardcoded SHA-256, then verifies every listed runtime file
before compilation and after execution. Do not generate a freeze from the
working tree as part of a test or relax the identity comparison to pass CI.

When the runtime intentionally changes, archive the exact committed ISE revision
to a new scratch directory, review the source delta, create the new freeze from
those archive bytes, update its admitted identity, and rerun the native replay
and comparator regressions. Preserve old captured inputs and historical proofs.

```sh
python3 -B nextcore/tools/dynamic_comparison/compare.py --oracle nextcore/artifacts/arm-dynamic-oracle-20260909 --runtime nextcore/crates/nextcore-ise/runtime --output /tmp/dynamic-new-run
python3 -B nextcore/tools/dynamic_comparison/test_compare.py --oracle nextcore/artifacts/arm-dynamic-oracle-20260909 --evidence /tmp/dynamic-new-run
```

The active scalar and pair runners in `nextcore/tools` likewise consume the
original authored `.S` fixtures, while requiring the corrected exact syndrome.
The memory-provider aggregate uses those active runners. Historical runners and
their manifest-pinned bytes are retained without reinterpretation.

This is captured Arm versus native generated-x86 comparison and separate OVMF
validation. It does not establish physical hardware or macOS boot.
