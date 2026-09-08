# ARM64 boot-argument codec contract — BP22-C

Current state: Intel boot arguments already have a separate codec. This change implements a public ARM64 byte-layout and range-validation layer. Desired state: NextCore can prepare independently described arguments for a future original-kernel handoff without treating encoding as execution.

DECIDED: implement a separate `xnu_arm64_boot_args` core module, independent fixtures and no_std validation. No EFI entry guard, Intel codec, CPU executor, kernel loading, or device implementation changes are part of this step. Successful encoding always reports `execution_ready=false`.

## Public source profile

The profile is **XNU xnu-12377.121.6**, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`. The public ARM64 [boot header](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h) declares the LP64 structure; this is distinct from both the ARM32 header and Intel's EFI boot arguments. Revision 2/version 2 is this codec's explicit selection. The public tag is not evidence that a later macOS 27 kernel accepts an identical complete handoff.

The wire occupies 1,152 bytes, little-endian, aligned to 8 bytes. An independent C layout fixture checks both host LP64 offsetof/sizeof output and Clang's actual Darwin ARM64 target compilation. The Rust encoder writes offsets explicitly and does not transmute a Rust struct.

| Wire field | Offset | Bytes |
| --- | ---: | ---: |
| Revision / Version | 0 / 2 | 2 / 2 |
| virtBase / physBase | 8 / 16 | 8 / 8 |
| memSize / topOfKernelData | 24 / 32 | 8 / 8 |
| Video's six LP64 words | 40 | 48 |
| machineType | 88 | 4 |
| deviceTreeP / deviceTreeLength | 96 / 104 | 8 / 4 |
| CommandLine | 108 | 1,024 |
| bootFlags / memSizeActual | 1,136 / 1,144 | 8 / 8 |

Padding and unused command-line bytes are zero. The command line is ASCII, has no embedded NUL and has at most 1,023 bytes. Video is explicit caller-supplied metadata; writing its six words proves neither a framebuffer nor display operation. Only the publicly declared dark-boot flag is accepted in this initial profile. The machine type remains caller-supplied.

## Address and device-tree contract

The caller supplies physical RAM, its initial kernel virtual window, the fully occupied kernel range, boot-argument storage and actual flattened DT bytes. No private kernel placement address is built into the codec. All interval additions and PA-to-KVA calculations are checked. The selected VMApple profile uses 16-KiB memory/placement alignment, 8-byte argument alignment and 4-byte DT alignment. The kernel, arguments and DT must not overlap; arguments and DT must follow the kernel's complete occupied range and end at or below `topOfKernelData`. The top leaves some RAM for subsequent allocations, but this check does not prove enough early-allocation headroom exists.

The DT uses the public XNU flattened tree format, not Linux FDT. Its structure is validated through the existing bounded `flat_dt` validator. The root's `chosen` child must supply exactly 8-byte little-endian `dram-base` and `dram-size` properties. They must describe non-overflowing, aligned actual DRAM containing the managed RAM window and match the explicitly supplied actual memory size. These are early public [arm_init consumers](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm/arm_init.c), not a complete enumeration of required platform properties. CPU topology, interrupts, entropy, storage, security and device semantics remain separate requirements.

`x0` at the cold entry is the **physical** boot-argument address. The encoded `deviceTreeP` is this codec's explicit initial **kernel virtual** pointer, calculated as `virtBase + (dt_phys - physBase)`. Public [start.s](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/start.s) performs this transformation on the argument pointer before calling C; [PE_init_platform](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/arm/pe_init.c) consumes the DT pointer directly, and [arm_vm_init](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/arm_vm_init.c) later moves the DT/ramdisk/argument region. Encoding does not allocate, copy, reserve or retain those physical objects; their owner must preserve all backing through handoff.

## Execution contract still outstanding

The public cold path uses EL1 registers and installs its own stacks, translation tables, exception vectors and control state. A future entry adapter must establish and measure AArch64 EL1 execution, masked exceptions, physical execution with MMU off, coherent loaded memory and the required cache/TLB transition. These are preparation obligations derived from the public entry sequence, not state established by a host-side codec. Platform-specific reset, monitor, PAC and integrity behavior must remain functional.

The public [VMAPPLE configuration](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/VMAPPLE.h) selects 16-KiB granules and paravirtualized PAC/CTRR plus CPU/device features. Its [register definitions](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/proc_reg.h) make the L2 bootstrap block 32 MiB. The actual assembly adjusts memory bases to the collection header, shifts the remaining size to obtain a whole-block count, and masks physical block descriptors. Consequently a placement checker must prove matching VA/PA within-block offsets, actual whole-block coverage of every early object and sufficient bootstrap table space. This codec does **not** impose an invented fixed kernel address, round reported memory upward or claim these mapping conditions were met.

For the public fileset path, XNU derives its slide from the kernel's first segment and the compiled kernel-link address, then rebases/signs chained pointers and adjusts Mach-O addresses itself. The loader must preserve this division of responsibility and must not pre-apply those same operations. See [arm_init](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm/arm_init.c) and [public kernel fixup consumer](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/mach/dyld_kernel_fixups.h). A kernel collection's entry metadata, full placement, authenticated fixup support and applicability to the selected build require their own inspection and execution evidence.

Actual Golden Gate kernel metadata stays isolated. It is ARM64E; ordinary ARM64 user-space probe compilation does not verify that kernel's authenticated-pointer execution. The newer input's ABI equivalence, original-kernel execution, guest device support, userspace and Metal remain unverified by BP22-C.

## Implemented and checked

The separate core codec and 15 authored tests are complete. Tests cover the wire layout and padding, PA/KVA roles, command-line termination, supported flags, non-wrapping RAM/kernel/argument/DT intervals, alignment, pairwise overlap, occupied-region boundaries, and the actual flattened DT's public DRAM properties. `cargo check -p nextcore-core --no-default-features` passed.

The independent C fixture passed both Darwin ARM64 target compilation and a native LP64 executable's actual `sizeof`, `_Alignof` and `offsetof` output. [The layout receipt](layout-r1/receipt.json) records all three commands and hashes. The executable is a host layout probe, not an ARM64 guest boot test; its generated binary need not be committed.

Focused Clippy passed with three named lint classes excluded. The initial stricter invocation failed on three existing ACPI `unnecessary_lazy_evaluations` diagnostics and one existing picker `implicit_saturating_sub` diagnostic. The existing `manual_is_multiple_of` exclusion was retained. No unrelated source was edited. [The validation receipt](validation-receipt.json) records the exact commands, results and hashes for the new sources.

The source is frozen for independent review. The next execution step must validate the actual collection placement and public bootstrap mapping requirements, retain the real memory/DT backing, and establish the required ARM64E CPU/platform state before any original-kernel entry is attempted.
