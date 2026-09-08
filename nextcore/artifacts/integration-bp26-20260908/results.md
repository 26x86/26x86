# BP26 final integration — 2026-09-08

The product target remains a macOS-focused ARM64e-to-x86_64 JIT compatibility
layer entered by x86 EFI. M1 is the guest platform baseline. WSL is the build
environment; QEMU/OVMF is used only as an automated firmware test fixture.

## Implemented and independently reviewed

- Native and reference TPIDR_EL0, TPIDRRO_EL0 and TPIDR_EL1 state, access faults,
  full-width reads/writes, per-CPU isolation and C/Rust bridge consistency.
- Correct distinct TG0/TG1 encodings for 4 KiB and 16 KiB, disabled-walk faults,
  failed configuration preservation and partial initial-table indexing. The
  partial-index test failed before the fix, then passed all 24 boundary cases.
  Four independent Arm CPU oracle cases pass; an incorrect PA control fails.
- A separate borrowed firmware DeviceTree parser preserves all length flags,
  values and padding. The original tree has 48 unresolved templates and is
  rejected before executable entry; the strict runtime parser is unchanged.
- SGPU codec ownership moved from APLS to GPU, preserving the existing command
  format and APLS re-exports. A bounded session maps opaque resources/kernels,
  preflights whole command lists and connects supported compute to the backend.
  APLS additionally validates exact inline frames, resource budgets and error
  conversion. Nine follow-up regressions cover independently reproduced bugs.
- All seven modules remain actual Git submodules. Manifests use canonical Git
  URLs and immutable revisions. A fresh-clone check caught an incidental Python
  cache in the source inventory; it was removed and ignored, then the clean
  recursive check and all final validation below were rerun successfully.

## Final source and tests

Tested integration commit: `e1f64b3f4a4aa9f0530c031f5d3a6173ff0765ba`.
The later documentation commit adds receipts only.

| Module | Integrated commit |
| --- | --- |
| Core | `757d8e668141ebc15a265f13383448bc609defb9` |
| EFI | `7a42084f92c7eadcd11ece0f2d06962c73450598` |
| Tool | `5804b6618a78371fcdde04f1481c6ae81d80d8ae` |
| ISE | `1d5ffb56799f70ce622e4813be66d0592cb5a292` |
| GPU | `34d617cca37d563d13ed0b0c966e2557921c6125` |
| HAL | `9c1cd8dfff33478e32668c5cd181dd094ec2881b` |
| APLS | `b885ab2f5dfe1d0c450bba148fa94b8a1e7e79c9` |

[validation.json](validation.json) and [fresh-integration.json](fresh-integration.json)
record the final source revisions, commands and timings. Fresh standalone module
receipts use local committed objects with temporary Git URL mappings, without
parent workspace patches. Remote publication is not asserted.

- Rust workspace: 461 passed, zero failed; its one opt-in compiled-EFI bundle
  test also passed separately against the newly built default binary.
- Reference runtime: 65 passed, including 13 MMU tests. Native C/Rust JIT and
  PAC/thread-state verification passed; see [native-pac.json](native-pac.json).
- Python: 132 run, 131 passed, one privileged ownership fixture skipped.
- x86 EFI: all nine standard fixture cases and five prefix cases passed.
- Legacy x86 EFI build and ABI audit passed. Required host and EFI Clippy
  commands passed, with non-fatal existing/style warnings preserved in logs.
- RX 6800 XT: eight physical host Vulkan dispatches in the GPU-module receipt.
  An independent calculation matched all 1,024 persisted output values.
  The new wire path accounts for one copy and two of those GPU dispatches.

The default EFI is 169,472 bytes; SHA-256
`f07953b4539504dc01131739020c05a0fabc6dee12f7d307032b1353026554fc`. The probe/trace EFI is
235,008 bytes; SHA-256
`643f341e56aedf519fff52b4e48e870459c2197d7c214447132f7dd595e4aa44`. These authored final-binary tests are
separate from the original-input diagnostic recorded below.

## Original input and remaining product work

The unchanged macOS 27 original prefix retired seven instructions in three
native blocks, compared with four before TPIDR support. Its exact diagnostic
binary hash, argument convention and limits are retained in
[the original-prefix results](../arm-startup-continuation-20260908/results.md).
This was an explicitly incomplete diagnostic with a budget of eight, not XNU
startup. It stops at an implementation-defined CPU override register. Public
sources support particular interrupt fields but do not establish the entire
initial register state. The [next provider contract](../arm-recovery-20260908/cpu-override-next-boundary.md)
documents the required state and interrupt semantics; no no-op provider was added.

Native JIT MMU enablement, provisioned CPU override/IRQ/FIQ behavior, SPTM
arguments/services and a resolved runtime device tree remain necessary for
actual macOS boot. Host Vulkan compute does not establish guest Metal or an
EFI GPU submission backend. APLS inline SGPU frames and VSK grant-backed
payloads are distinct transports and still require explicit integration.
The existing Intel/Darwin-25 Mellow path does not validate RX 6800 XT or macOS
27 graphics. Actual x86 macOS Metal was not verified either.

Apple assets and original execution coordinates remain in `_isolated/` and
are excluded from all commits. The entire 22,740,609,058-byte IPSW is downloaded and its expected SHA-256
verified. Selected ZIP members also match the previously tested inputs, with
CRC and SHA-256 checks. See [acquisition.json](acquisition.json).

All implementation changes are committed locally on `codex/arm64e-boot-metal`.
No remote push, PR publication, driver replacement or host EFI installation
was performed. Remote publication remains pending the previously requested
explicit push approval required by the repository's AGENTS.md section 7.
