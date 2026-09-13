# Authored EFI Entry Provenance Validation

## Current Status

The fileset staging contract selects the outer `LC_UNIXTHREAD` program counter. Member thread metadata and the minimum mapped image address are separate values. This validation owns only an independently authored fixture runner and this evidence record; it changes no production parser, firmware, instruction budget or readiness gate.

## Target State

The existing `NXARMJIT.efi` diagnostic must execute the outer entry canary through the real OVMF path. Changing only the outer PC must change the observed canary. Changing only the member PC must leave execution at the outer canary. A third executable canary at the minimum mapped image address makes accidental image-base selection observable.

## Fixture and Acceptance Contract

The fixture extends the existing public `build_arm64_handoff_probe.image` layout. Its fileset member is named `fixture.kernel`; all code and metadata are authored locally. ARM64 instructions are assembled with LLVM rather than hand-encoded. The member receives its own ARM thread command. An additional executable outer segment below the header holds the image-base canary; the original header and member remain mapped at their original virtual addresses.

Four independent runs use the same EFI binary, code bytes, placement and exact 64-instruction budget:

| Case | Only changed field | Expected result |
| --- | --- | --- |
| Outer entry | None | Outer canary and its exact loop PC |
| Outer selects member | Outer thread PC | Member canary and its exact loop PC |
| Member metadata changes | Member thread PC | Unchanged outer canary and loop PC |
| Outer selects image base | Outer thread PC | Image-base canary and its exact loop PC |

Each case requires an ordered diagnostic receipt, exact entry marker, status 5 with 64 retired instructions, expected registers, 64 fetches, zero data operations and provider status zero. Source and EFI hashes must remain unchanged, and the existing trace runner must confirm its source inputs and ESP copies remain intact. Pairwise fixture byte differences must be confined to the selected eight-byte PC field. Successful budget return is only an authored diagnostic result.

## Reproduction

Run `python3 nextcore/tools/verify_entry_provenance_ovmf.py --efi /path/to/NXARMJIT.efi --output /fresh/output/path` in the existing Linux LLVM/QEMU/OVMF environment. Output includes assembly, fixtures, per-case trace reports and serial evidence, all invocation arguments and an aggregate receipt. The runner preserves failures and returns nonzero if any acceptance check fails.

## Evidence Boundary

No original Apple image is an input. This checks entry provenance through a firmware diagnostic, not XNU, normal startup, userspace, physical display or macOS boot. It does not authenticate an image, implement platform services, or validate every possible fileset layout.

## Observed Result — 2026-09-12

All four final OVMF cases passed with the unchanged BFM diagnostic EFI. Each retired exactly 64 instructions, preserved the boot argument register, completed zero data operations and reported provider status zero. All entry, final PC, canary and integrity checks passed.

| Case | Observed entry PA | Final loop PA | X0 / X2 / X3 |
| --- | --- | --- | --- |
| Outer entry | `0x42004400` | `0x4200440c` | `0x1111 / 0xaaaa / 0x111` |
| Outer selects member | `0x42004440` | `0x4200444c` | `0x2222 / 0xbbbb / 0x222` |
| Member metadata changes | `0x42004400` | `0x4200440c` | `0x1111 / 0xaaaa / 0x111` |
| Outer selects image base | `0x41ffc000` | `0x41ffc00c` | `0x3333 / 0xcccc / 0x333` |

Evidence is retained in the local run directory `/tmp/nextcore-entry-provenance-20260912-r3`, including its aggregate `receipt.json` and the four firmware reports and serial logs. Reproduction requires an equivalent diagnostic EFI build; this document does not embed an EFI binary.

- EFI SHA-256: `dc413ead68408ad6fa017e06062349771568ab84061dbede4fda45261563a376`
- Runner SHA-256: `dd1a2b9621a41cd43578fb2abca9a457561219b1ca979f0f7c971f34460183d2`
- Aggregate receipt SHA-256: `d8405dd1a222f58ae60254efe8e97ab3d1adf3059a32959572905e252fb14ae8`

Two earlier attempts remain in adjacent local run directories. The first was correctly rejected by the unchanged bootstrap correspondence gate because the added lower segment required matching physical placement. The second executed all canaries correctly but the new runner searched for `pc=` instead of the existing `TRACE_ENTER entry=` field. The final run corrects only authored placement and receipt parsing, and also explicitly checks the trace runner's tool-source integrity field. Earlier failing runner versions and their receipts remain preserved.
