# Explicit software platform profile and EFI diagnostics — BP27

Current: the original ARM64e startup prefix retires seven instructions through
the x86 EFI JIT and stops on an absent platform interrupt-control provider.
Firmware DT templates, SPTM arguments/services and complete M1 runtime data are
unprovided. BP27 explicitly delegates optional Core/EFI profile selection and
firmware tests here; CPU agent owns every native/reference runtime and bridge.

Wanted: select an explicitly named software compatibility profile with defined
interrupt-control behavior, validate its real pending/mask/vector effects through
authored EFI payloads, then observe the next bounded original startup boundary.

Decisions:

- Selection is optional and explicit inside the existing `Trace` configuration.
  Missing selection keeps the provider absent and the existing eight-instruction
  prefix bound. Unknown names are errors; no input image automatically selects a
  profile. The `arm-jit-trace` build feature remains required.
- The agreed name is `Trace.PlatformProfile=nextcore-irq-compat-v1` (runtime
  id1). An optional `Trace.Platform` dictionary has InitialOverride,
  InitialPstate, VectorBase, IrqLevel and FiqLevel integer fields. Its defaults
  are 0, 0x3c5, 0, 0, 0 respectively. This dictionary requires explicit selection.
  Override bits are limited to 0x00f00000 with each two-bit field 00 or10;
  PSTATE is EL1t/EL1h plus DAIF/NZCV only, levels are0/1, and nonzero VBAR must
  cover an aligned2KiB guest RAM span. Unknown option keys are rejected.
- The selected profile defines its own software initial state. Diagnostics must
  state that it is not a measured Apple reset state. Unsupported register fields
  and access modes remain runtime errors, not silently stored or ignored values.
- An explicit selected-profile diagnostic may use a budget of 1..64 instructions
  to cover register read/modify/write and committed interrupt vector entry.
  Initial x0..x3 retain the stated incomplete SPTM cold-entry convention.
  No SPTM argument object or service provider is invented by this extension.
- Pending interrupt inputs, if exposed for authored diagnostics, require explicit
  bounded configuration. Native and reference behavior must preserve pending
  levels while masks block delivery, select the correct vector and save real
  guest exception state. The EFI caller reports returned state through the
  CPU-owned versioned bridge; it does not implement a separate interrupt model.
- Original inputs are executed only after the provider passes independent native
  and EFI tests. Their words, coordinates and detailed receipts stay `_isolated`.
  Unresolved firmware DT templates still stop before TRACE_ENTER. A validated
  authored diagnostic DT is never labeled a complete M1 platform tree.
- Tests distinguish absent selection, invalid selection, configuration bounds,
  supported mask effects, preserved pending levels, committed vector state,
  and explicit rejection of unsupported fields. Prior authored PAC/GOP and
  standard-register results remain separate from macOS boot and Metal outcomes.

The CPU-owned `vf_boot_run_v2` bridge has options64bytes and result128bytes;
abi_version=2, size fields and reserved fields are checked. Asynchronous IRQ/FIQ
returns commit the exception vector and saved state but do not execute a guest
handler. Receipts explicitly retain handler_executed=false for these returns.

OPEN_QUESTION: SPTM services and a resolved platform DT remain absent; interrupt
entry into a defined software profile does not establish original hardware state.
