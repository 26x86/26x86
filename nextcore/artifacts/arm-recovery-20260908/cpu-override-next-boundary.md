# CPU override boundary after the standard thread-register prefix

The BP26 x86 EFI run retires seven original instructions in three generated
native blocks, then stops on an implementation-defined system-register read.
An independent private check matched the saved fault instruction to the
unchanged input. Exact original addresses and bytes remain in `_isolated`.
This is a bounded instruction diagnostic; it supplies neither SPTM arguments
nor SPTM services and does not demonstrate macOS boot.

## Public evidence

The register is named `CPU_OVRD` in Apple's public startup source and
`CYC_OVRD` in Asahi m1n1. Asahi publishes its encoding as
`S3_5_C15_C5_0`. Apple explicitly clears the external interrupt override
fields during SPTM startup after non-retention WFI.
[Apple startup](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sptm/start_sptm.s),
[Asahi register definitions](https://github.com/AsahiLinux/m1n1/blob/main/src/cpu_regs.h).

Apple identifies IRQ override at bits 23:22 and FIQ override at bits 21:20;
field value 2 disables each input. Its startup clear establishes that value
0 removes this override. The same register controls power-down behavior and
WFI retention. These are functional controls, not an arbitrary scratch bank.
[Apple field definitions](https://github.com/apple-oss-distributions/xnu/blob/main/pexpert/pexpert/arm64/apple_arm64_regs.h),
[Apple sleep code](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/machine_routines_asm.s).

Asahi independently uses the two disable values before sleep, preserves the
previous register around deep WFI, and calls WFI mode 0 the default. Its
initialization changes only the WFI field while preserving other bits.
That is evidence for a field default; it is **not evidence that the complete
64-bit register resets to zero**.
[Asahi sleep implementation](https://github.com/AsahiLinux/m1n1/blob/main/src/utils.c),
[Asahi guest initialization](https://github.com/AsahiLinux/m1n1/blob/main/src/hv.c).

No source reviewed here specifies the complete reset value or the meaning of
all fields. The register remains unsupported in BP26. Returning zero for
every MRS or accepting every MSR would invent state that the evidence does
not establish.

## Proposed next implementation contract

The first implementation should be a provisioned platform register provider,
distinct from the generic AArch64 bank. The default provider is absent.
A documented software platform profile or a validated initial-state receipt
must supply a complete known value before an MRS can succeed. A partial
known-bit mask is insufficient for an architectural full-register read.
An authored test profile may choose a known initial value, but that receipt
must not be presented as measured Apple reset state.

For an IRQ/FIQ-only provider, the writable bit mask is `0x00f00000`.
Each two-bit field accepts only 0 (no override) or 2 (disabled), based on
the cited sources. MRS returns the provisioned value including preserved
nonwritable bits. MSR rejects changes outside the mask, field values 1/3,
and unprovisioned state before committing anything. Unchanged power/WFI
fields must already have a defined provider interpretation; preserving
arbitrary unknown bits is not a substitute for modeling their behavior.
Guest EL0 and unsupported platform/security modes remain fault boundaries
until their access behavior has a documented contract.

Masking must affect the corresponding guest IRQ/FIQ input before PSTATE
masking and exception delivery. It must not discard a level-pending event.
Clearing the override makes that event eligible at the next instruction
boundary, subject to the architectural masks and routing. It must never
change host interrupt masks.

## Existing integration gaps and file ownership

| File under `nextcore-ise/runtime` | Required work |
| --- | --- |
| `jit.h`, `arch.c` | Separate provisioned platform state; explicit access errors; distinct IRQ/FIQ pending inputs and masks. Keep exported bridge layouts versioned. |
| `jit.c` | Provider dispatch at a precise guest instruction boundary; commit only after validation. Native `vf_run` currently has no asynchronous IRQ/FIQ polling path. |
| `preos/src/arch.rs` | Matching provider contract and input routing. `poll_interrupt` currently combines timers and external events behind PSTATE.I; it does not implement a distinct FIQ path. |
| `preos/src/m1.rs`, `machine.rs` | Connect actual platform interrupt sources and preserve pending levels while masked. Establish timer-to-IRQ/FIQ routing instead of inferring it from an event name. |
| `boot_jit.h`, `boot_jit.c` | Optional versioned platform-provider configuration. Legacy callers must retain absent-provider behavior. |

The asynchronous vector calculation also needs an EL1t versus EL1h test:
the current Rust timer/external case uses the EL1h IRQ region even when
the saved SP selector is zero. Fix that with the interrupt integration,
not by hiding it in a register implementation.

## Verification plan

1. Use independently authored MRS/MSR inputs to test provider absence,
   complete-state requirements, value preservation, unsupported writes,
   faulting PC, zero retirement on failure, and per-CPU isolation.
2. For every supported IRQ/FIQ override combination, test pending input
   before masking, while masked, and after unmasking. Check PSTATE.I and
   PSTATE.F independently and verify the exception vector/ELR/SPSR for
   EL0, EL1t, and EL1h.
3. Run the same cases through the actual generated x86 path and Rust
   reference core. Compare stable ABI receipts and source hashes.
4. Repeat an authored x86 EFI test with a named, explicit platform profile.
   Keep the original diagnostic on the absent provider until its input
   contract is established; the initial state must be shown in its receipt.
5. Continue the original bounded run only after that contract is supplied.
   Generic instruction work likely includes logical immediates, comparison
   with shifted-register operands, and SPSel/SP banking before the image
   fixup routines. SPTM dispatch and boot argument providers remain separate
   requirements and must not be synthesized from a successful prefix.

No CPU override model or original-kernel bypass was added with this research.
