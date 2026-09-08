# ARM recovery CPU execution and provisioning — 2026-09-08

## Current state

The inherited VMApple CPU probe only executes `mov x0, #42`; it does not exercise the pointer authentication or privileged timer access required by the recovery CPU profile. The fresh WSL environment has no patched VMApple emulator. The known original firmware failure remains an unmapped four-byte MMIO transaction after bootx. No public source presently establishes that device's register semantics.

## Agreed implementation

The Build Plan root delegated this subtask. Provision the pinned QEMU commit and existing reviewed patch series in a fresh WSL output directory. Fetch the exact commit with shallow history rather than every QEMU revision, retaining source and patch hashes. Compile a separate authored AArch64 test and execute it on the exact recovery CPU options (`max,pauth=on,pauth-qarma5=on,cntfrq=24000000`) and Stage2 EL1 reset path. Verify architectural CurrentEL, timer frequency and progressing counter, 16 KiB translation-granule advertisement, APIA key access and readback, active signing, matching authentication and authenticated control flow. A no-PAuth negative run must fail the readiness gate.

Only authored guest instructions change CPU state in the probe's disposable VM. QMP observes state and terminates its owned process. Report individual results, commands, firmware and emulator hashes and cleanup. A capability result is neither ARM64e ABI conformance, XNU entry, nor macOS boot. Unknown device MMIO receives no invented response.

## Public basis

- [Pinned QEMU VMApple machine](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/vmapple.c): reset, RAM and firmware placement; existing patch series defines the explicit research reset contract.
- [Pinned QEMU PAuth implementation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/tcg/pauth_helper.c): architected PAC instruction behavior, SCTLR enable and EL2 trap gates. No implementation code is copied.
- [Arm A-profile architecture](https://developer.arm.com/documentation/ddi0487/latest): CurrentEL, architectural timer, ID_AA64ISAR1_EL1, ID_AA64MMFR0_EL1, APIAKey, TCR and SCTLR contracts.

## Verification gate

The exact built VMApple executable must finish the authored program under its EL1 reset contract, and the negative PAuth-disabled case must remain false. Public results contain authored inputs and runtime observations only. Original recovery will run separately once caller inputs are available; the previous MMIO failure remains open until measured otherwise.
