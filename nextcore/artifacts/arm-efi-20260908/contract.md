# ARM EFI entry and physical handoff contract (2026-09-08)

Initial state: ARM64/ARM64E KC metadata and immutable 16 KiB staging are host
codecs. The executable EFI entry and architecture transition exist for x86 only.
Desired state (user correction): an x86 EFI compatibility runtime prepares an
ARM kernel and executes translated x86 code inside EFI. M1 is the macOS guest
baseline. WSL is the development environment, not the product runtime. An
AArch64 firmware binary remains a separate, secondary ABI diagnostic.

This Build Plan subtask is explicitly delegated by root. Owned scope is the EFI
Cargo entry, new ARM EFI/transition modules, authored fixture, QEMU harness and
this evidence directory. Root owns shared core placement/config and Build Plan.

Root subsequently delegated shared ARM placement/config, EFI JIT build/caller and
preOS boot wiring here. CPU agent owns `arch.rs`, `jit.c`, `boot_jit.c` and PAC;
GPU agent owns GOP presentation/readback. Root owns relocation to ISE's module.

Revised x86 EFI execution decisions (primary product path):

- `NXARMJIT` is an x86_64-unknown-uefi PE application. ARM guest PAs are checked
  offsets within an owned host RAM allocation, never direct host pointers or
  branch targets. Core `Arm64HandoffPlan` prepares the source-bound image,
  boot_args, DT and stack with distinct linked VA, guest PA and host address.
- The C JIT initializes guest EL1, DAIF and x0/PC from the prepared layout,
  translates real ARM instructions and calls generated x86 code. Runtime output
  includes actually executed native block count; a reference interpreter alone
  cannot satisfy the JIT proof. Unsupported instructions preserve fault state.
- Host Boot Services stay active for host memory protection and GOP. The host
  does not perform a native ARM transition or exit firmware on a guest request.
- Fix the preexisting RX predicate: RO must be set and XP must be clear. Every
  generated-code transition preserves W^X and reads actual host page permission
  state. Failure is not downgraded to a warning or an RWX fallback.
- The `x86-efi-arm64-jit-probe` profile and `arm-jit-probe` feature together
  select an independently authored input. Its ARM instructions read boot_args,
  store readback values and write sixteen pixels to guest RAM. Only actual
  native execution, expected register/data results, and GOP RGB readback count.
- Production ARM64E inputs may be staged with subtype preserved, but exact
  macOS 27/M1 providers and authentication remain unresolved. Probe outcomes
  never set `xnu_executed`, `macos_boot_verified` or `metal_verified` to true.
- After the nine EFI cases passed, root delegated a bounded original-input
  trace. Feature `arm-jit-trace` and profile `x86-efi-arm64-trace` require a
  `Nextcore.Kernel.Trace` dictionary with PhysicalBase, VirtualBase, MemorySize,
  ActualMemorySize, KernelPhysical, InstructionBudget integer fields and a
  DeviceTreePath string. `HandoffAbi=unprovisioned-sptm-prefix` is mandatory.
  RAM is 16 MiB..1 GiB, 16 KiB aligned; budget is 1..8. The public SPTM cold
  entry uses x0=0, x1=boot_args, x2=SPTM args. This diagnostic explicitly supplies
  x0=0, x1=the staged boot_args PA, x2=0, x3=0, with no SPTM argument or service
  provider. It reports this incomplete ABI before execution. The supplied DT
  has diagnostic status only; an authored DRAM-only tree can isolate the entry
  prefix without asserting a complete M1 runtime DT. Source and supplied DT
  are copied without patching; boot_args and
  range/profile validity are checked before native execution. Trace reports
  actual retirement/fault/PC/block counts and returns ABORTED even on guest halt.
  It is an explicit diagnostic; it does not claim authenticated OS boot.
  Original instruction words, execution addresses and detailed serial receipts
  stay under `_isolated`; only independently authored fixtures are published.

Secondary AArch64 firmware diagnostic decisions (build validated, not executed):

- Add BOOTAA64 as an explicit AArch64 EFI target. Default execution stages and
  validates the selected input, then reports provider requirements. Only the
  `arm-kernel-probe` feature may transfer to an authored test payload.
- Preserve source, KC chained fixups, CPU subtype and PAC instructions. A marker
  identifies the authored fixture only; it supplies no authentication claim.
- The test platform is QEMU virt, one CPU, 512 MiB RAM at 0x40000000, with the
  staging allocation fixed at 0x42000000 and a 16 KiB-aligned arena. LoaderCode
  pages and range checks provide executable firmware mappings before EBS.
  It runs under TCG on the user's x86_64 WSL2 host. M1 is the desired guest
  hardware baseline, not a requirement for an ARM host computer.
- Readback the entire staged arena. Bound file input, DT, page spans and memory
  map. Keep all page owners alive across EBS; do no allocation, drop, firmware
  call or Rust return after EBS. All error paths before EBS release ownership.
- Transition only from EL1 identity mappings. Validate address translation for
  code, allocation and stack before EBS. Mask DAIF, clean staged bytes to PoC,
  invalidate instruction cache, disable EL1 MMU/cache and branch with x0 holding
  the physical boot_args address. Unsupported ELs fail before EBS.
- The payload checks CurrentEL, SCTLR, DAIF, x0, boot_args layout/DT translation,
  copied initialized data and zero-fill independently. QEMU semihosting provides
  observable guest output and an independently required natural exit status.
- Positive and negative firmware cases distinguish default provider gate,
  malformed KC, absent marker, subtype mismatch and payload data corruption.
  No outcome here proves XNU/macOS 27, M1 devices, authentication or guest Metal.

Public sources:

- UEFI 2.10 A, AArch64 binding and memory services:
  https://uefi.org/specs/UEFI/2.10_A/02_Overview.html
  and https://uefi.org/specs/UEFI/2.10_A/07_Services_Boot_Services.html
- Apple public XNU pinned ARM entry and boot ABI:
  https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/start.s
  https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h
- Public XNU SPTM entry (cold x0, iBoot args x1, SPTM args x2):
  https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sptm/start_sptm.s
- ARM semihosting standard (SYS_WRITE0/SYS_EXIT_EXTENDED):
  https://github.com/ARM-software/abi-aa/blob/main/semihosting/semihosting.rst

OPEN_QUESTION: Actual macOS 27 ARM64E/M1 boot requires exact target ABI, real
platform device model, trust providers and PAC CPU execution evidence; this
firmware transition proof cannot discharge these requirements.
