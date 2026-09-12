# Active memory runner validation

## Current Status

The 2026-09-12 parent CI run 34685416515 rejected the invalid pair writeback and
three unsupported scalar encodings because historical readers required ESR=0.
ISE's committed unknown-exception correction produces exact A64 EC0/IL1/ISS0,
or `0x02000000`. All other retirement, register, PC, and memory checks passed
in those failed cases. This is an expectation-version mismatch, not evidence
that the historical execution or its captured manifests should be rewritten.

The maintained `verify_arm_scalar_ovmf.py` and `verify_arm_pair_ovmf.py` retain
the original authored assembly inputs and all other exact checks. They require
the corrected full syndrome; they do not mask ESR or accept both old and new
values. The integrated memory runner now invokes these maintained readers.
Historical artifact folders remain unchanged.

## Validation

The replay used an immutable archive of EFI `0d4303e`, whose manifest pins ISE
`792abc11c6a8a4b242f99e91dc9c18e9caadc474`. Provider, direct, and bounded-tier
variants were separately built in WSL and executed in disposable x86 OVMF.

| Run | Result | Local receipt |
| --- | --- | --- |
| Integrated provider, exact observations, edge cases, bypass rejection, bounded tiers | PASS; 26 actual EFI cases, 6 CLI rejections | `/tmp/nextcore-ci-memory-792abc1/report.json` |
| Direct pair | 6/6 PASS | `/tmp/nextcore-ci-direct-pair-792abc1/report.json` |
| Direct scalar | 11/11 PASS | `/tmp/nextcore-ci-direct-scalar-792abc1/report.json` |
| Deliberately wrong signed-byte load | Expected exit 1; only `x1_value` failed | `/tmp/nextcore-ci-scalar-negative-792abc1/report.json` |

The integrated provider run required its real observation markers and rejected
the direct bypass control for the specific missing-provider checks. It did not
treat any arbitrary nonzero process result as successful negative coverage.

## Target State

Parent CI executes these maintained runners on the selected current EFI and
ISE revisions. A fresh CI result is required for later revisions; the results
above apply to the stated immutable inputs. OVMF execution does not establish
physical-host boot, macOS userspace, SPTM availability, or graphics acceleration.
