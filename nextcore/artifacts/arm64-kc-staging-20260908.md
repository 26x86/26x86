# ARM64 kernel collection staging — BP22-D

Current state: the Intel inspector and staging API were already implemented. The
new explicit ARM profile is now implemented and checked. Desired state: original
ARM64 collections can reach a separately validated physical handoff without
mistaking host-memory preparation for kernel execution.

DECIDED: `inspect_arm64_kernel_collection` and `KcStagingPlan::new_arm64` are
separate APIs. Default Intel inspection, audit, rebasing and EFI staging retain
their CPU gate. Each header retains its raw CPU type/subtype. Named public ARM64E
metadata values are accepted without stripping capabilities; unknown values and
mixed-member subtypes are rejected. See the independent [public contract review](arm64-kc-metadata-review-20260908.md).

The supported thread-command subset is one 288-byte ARM flavor-6/count-68 state.
Only the outer PC receives the boot-entry range check: four-byte alignment and
four complete file-backed executable bytes. Member entries remain descriptive
metadata. The host arena span rounds to 16 KiB; this does not align the `Vec`
backing as guest pages. Unaligned member views are valid when fully contained
and mapped consistently. The 128-MiB source and arena limits remain independent.

Outer mappings own copy/zero-fill; all holes and member views are read back.
Chained format 8 remains unsupported/unapplied for preparation, with its first
opaque word now required to have eight backed bytes. No chain walk, PAC change,
header slide, executable allocation or guest entry occurs.

Validation on 2026-09-08:

- Core all-targets passed 179 tests before the final additional member-alignment
  regression. All 12 ARM KC tests then passed; no production source changed
  between these two test runs. This yields 180 covered core tests.
- Core `--no-default-features --target x86_64-unknown-uefi` passed.
- The original Golden Gate input was supplied at runtime, never built into the
  crate. Actual staging/readback passed for 81,002,496 bytes, seven outer
  segments, 216 member headers and 1,096 segment views. Overlapping member
  comparisons total 3,463,261,621 bytes, not that many unique source bytes.
- The bounded child exited 0 in 6.594 seconds. Source SHA256 before/after:
  `0f8eb7a4ea2fe2393313075eb74c2260b5ca801dcade396f7a87f32c0e5f657f`.
  Tool hash before/after also matched. Private addresses and full metadata stay
  in `_isolated/nextcore/arm64-kc-staging-20260908/`.

Reproduce with `cargo run -p nextcore-core --example stage_kc -- --arm64 <input>`.
Its JSON contains addresses, so original-image output must be directed to an
isolated observation directory. Omitting `--arm64` preserves the Intel profile.

`physical_placement_verified`, `preparation_ready`, `firmware_executed`,
`xnu_executed`, `native_hal_verified`, `macos_boot_verified` and `metal_verified`
remain false. The next implementation must connect owned physical backing,
boot arguments and public bootstrap mapping constraints before attempting entry.
