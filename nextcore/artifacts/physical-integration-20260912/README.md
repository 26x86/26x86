# Physical-target boot continuation: execution checkpoints

Target: Samsung 750XHD, Intel Core Ultra 7 255U, Intel Graphics 8086:7D41,
32 GiB RAM. Completion requires external-media installation and an interactive
macOS 27 desktop after physical reboot. Graphics acceleration is deferred.
No physical OS boot is established by this checkpoint.

## Changes

- Integrate the existing PR #17 deep diagnostic work without discarding the newer
  English documentation policy; preserve historical BP35 receipts unchanged.
- Connect published UBFM and new complete extended-register ADD/SUB arithmetic.
  Add complete CSEL/CSINC/CSINV/CSNEG conditional selection and integer scalar
  register-offset memory operations.
  Core bab7ac4, Tool 8ea73c8, ISE 08156f4 and EFI c1bdb42 identify the latest checkpoint.
- Continue text output when optional color/clear fails, preserve an accepted
  choice when confirmation redraw fails, and make diagnostic stdout best effort.
- In explicit picker mode, acknowledge returned target failures before reopening
  selection. Direct noninteractive boot retains its original error return.
- Add production-picker recovery and actual arithmetic-consumer CI gates.

## Fresh evidence

- `ubfm-native.json`: generated-x86 and canonical Rust/provider verification,
  with compiled arithmetic mutation rejection. This is host execution evidence.
- `extended-native.json`: 96,000 generated-x86 cases (1,249,154 assertions),
  432,000 independent reference cases, 101 preOS tests, 14/12/13 actual memory
  provider tests, compiled sign/carry negatives and freestanding UEFI compilation.
- `extended-before`: the new authored EFI arithmetic test rejects the previous
  binary. `extended-consumer` passes actual native-x86 EFI execution with exact
  arithmetic results, branch effects, PC, retirement and x1 preservation.
- `ubfm-consumer`: UBFM aliases execute through the actual existing EFI consumer.
- `select-native.json`: 131,072 generated-x86 cases and 1,728,514 assertions,
  131,072 independent reference cases, 102 preOS tests, 15/13/14 provider tests,
  three compiled semantic mutants rejected and freestanding UEFI compilation.
- `select-consumer`: all four operations execute through the actual EFI consumer;
  exact arithmetic results, PC, retirement, x1 and source preservation pass.
- `published-clone.json`: a new recursive network checkout of parent 4572ad70
  passes clean module inventories and host/UEFI local Cargo resolution. This is
  source publication verification; runtime evidence is recorded separately.
- `cold-published-consumer`: the same fresh public checkout also builds and
  executes the extended-arithmetic EFI fixture successfully.
- `register-memory-native.json`: 13,312 native family cases, 106,496 existing
  immediate-memory regression cases, 13,312 reference family cases, 104 preOS
  tests, 16/14/15 provider tests and four rejected compiled semantic mutants.
- `register-memory-consumer`: actual EFI scaled loads, negative signed index,
  signed result, store/readback, exact four data operations and 64 retired
  instructions pass. The previous binary stops at the first tested load.
- Active scalar/pair and dynamic readers are under `nextcore/tools`; historical
  readers and source freezes remain unchanged. Current dynamic replay binds
  exact ISE 08156f4 and passes six independent Arm/native comparisons plus
  fourteen comparator regressions. See their versioned validation documents.
- `picker-fallback`: four OVMF protocol-failure cases invoke production picker
  source; three execute the authored child and initial output failure executes none.
- `picker-recovery`: production BOOTX64 recovers both missing-image and returned
  child errors, then boots the selected working child. Noninteractive error status
  is preserved. This does not cover errors after ExitBootServices.
- `deep-control`: actual 16,384-instruction authored diagnostic, CLI rejections and
  x1 mutation control. It does not exercise independent clamp/default binaries.
- `stage1`: 108 actual EFI memory-translation cases. `dynamic`: six cases,
  58 data events, 40 control events and 30 captured-reader negative controls.
- `workspace-tests.log`: 505 passed, zero failed, two ignored across host and
  doctest results at the UBFM integration checkpoint; not a physical boot test.

## Original-input boundary

The existing local 27.0 / 26A5425a j274 boot-ready kernel is 121,864,192 bytes;
its input hash is recorded in the summaries and remains unchanged. It is an
independent local input/profile, not assumed equivalent to the historical run.

The first attempt was rejected before execution by BootstrapCorrespondence.
The corrected software-defined placement follows Core's existing 32-MiB
correspondence rule; no guard was removed. With UBFM, the trace retires 5,312
instructions and stops at CMP extended-register. With extended arithmetic it
retires 5,316 and stops at CSEL. Both runs report 783 completed data operations.
With conditional selection it retires 5,350 and stops at an integer scalar
register-offset load, with 787 completed data operations. With register-offset
memory support it retires 5,353 and stops at TBNZ, with 788 data operations.
All report provider
status zero. Raw original coordinates, instructions, logs and copies
remain only under ignored `_isolated/`; public summaries contain no such bytes.

This is an incomplete startup-prefix diagnostic: normal SPTM arguments/services,
complete platform DeviceTree, sustained kernel initialization, userspace,
installation, desktop, post-boot display and physical boot are not verified.
The next execution work is standard TBZ/TBNZ test-bit branch support,
followed by a new authored EFI gate and same-input original replay.

## Reproduction and provenance

Use Rust/Cargo 1.97.1, Clang/LLVM 18 and OVMF. On this WSL host `llvm-ar` and
`llvm-objcopy` require `/usr/lib/llvm-18/bin` in PATH; the initial build-tool
lookup failure is retained. Do not interpret that failure as a guest failure.
Public module working text was restored to canonical LF before file inventory
publication. Historical source-byte hashes still describe their captured runs;
Git content identities are retained. A fresh recursive checkout is the final
published-source validation, separate from these historical local observations.
