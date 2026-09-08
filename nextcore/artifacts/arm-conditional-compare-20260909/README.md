# BP31 conditional comparison: reproducible evidence

This bundle records a standard A64 CCMP/CCMN extension in the native x86 EFI
compatibility JIT. It includes reproducible authored tests and reviewable source
patches. The selected receipts omit original-image coordinates and private
paths. They do not assert successful macOS boot or guest Metal support.

The native matrix passes34,264 cases; the complete reference suite passes93
tests. The independent Arm oracle passes3,668 cases. Actual x86 OVMF EFI
passes13 authored cases, covering both arithmetic operations, operand forms,
widths, fallback flags, NV, zero registers and flags consumed by B.cond. A
separate EFI binary with an intentionally wrong NV predicate fails only the
expected PSTATE assertion. Original-image diagnostics reached all three
approved budgets; the public progress audit explains the limited conclusion.

## Prepare canonical source checkouts

Read `source-provenance.json`. Prepare ISE at its listed base revision and
apply `ise-source.patch`. Prepare Core at its listed revision. Prepare EFI at
its listed base revision and apply `efi-tiered-source.patch`. Each patch is
applied to its own repository using `git apply --check` before `git apply`.
The build tool validates the resulting source hashes. The integrator may
replace these base-plus-patch instructions with equivalent published commits;
the expected source hashes remain authoritative for this historical receipt.

Requirements: Linux x86_64, Python3.10+, Rust with `x86_64-unknown-uefi`,
Clang/LLVM tools, `qemu-system-x86_64`, `qemu-system-aarch64`, and OVMF4M.
The recorded build used Rust1.98.1 and Clang18.1.3. QEMU is the authored test
computer/independent CPU oracle; the product executes its own JIT inside EFI.

```sh
python3 build_efi.py --core /path/to/core --efi /path/to/efi --ise /path/to/ise --output /path/to/build
python3 verify_efi.py --ise /path/to/ise --efi /path/to/build/target-positive/x86_64-unknown-uefi/release/NXARMJIT.efi --output /path/to/positive
python3 verify_efi.py --ise /path/to/ise --efi /path/to/build/target-nv-never/x86_64-unknown-uefi/release/NXARMJIT.efi --output /path/to/negative --negative-control
```

The positive command exits0. The last command must exit1 with source
preservation true and only the NV test's PSTATE check false. It is an expected
negative control. Never use that negative binary with an original OS image.
The build writes only its output directory and uses symlinks for canonical
source ownership. Exact EFI binary hashes can vary with absolute build paths;
the proof identity includes source hashes, compiler versions and behavior.

```sh
python3 probe_conditional_compare.py --work-dir /path/to/arm-oracle --output /path/to/arm-oracle.json
python3 /path/to/ise/tools/probe_efi_native_pauth.py --output /path/to/native.json
python3 /path/to/ise/tools/probe_efi_memory_provider.py --work-dir /path/to/provider --output /path/to/provider.json
```

The Arm oracle includes NV-never and wrong-NZCV expectation controls and rejects
SP/out-of-range assembly. The native and provider tools execute real generated
x86 and canonical C/Rust callbacks. The provider tool also detects a deliberate
memory-dispatch bypass. No original-image runner invocation or private asset
is included in this bundle; `original-aggregate.json` records aggregate
observations only.

`files.json` lists the selected files and SHA256 hashes. Production implementation
ownership remains in the ISE repository, Core configuration ownership in Core,
and EFI caller ownership in EFI. The patches here are provenance for replay,
not a replacement source tree.
