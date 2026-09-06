# VMApple TCG backend: source and limits

This work is at the **host emulator/device-model layer**. The patch changes
QEMU source only. It provides an explicit, headless TCG research entry point
on an x86 host. It does not establish that any version of macOS boots.

Upstream is pinned to QEMU commit
`ff1d2d19d7e24893e2012d879f8e73077e17b9bd`, observed from the official QEMU
GitHub mirror on 2026-09-06. The commit timestamp is 2026-09-04. Use this exact
commit when applying `patches/0001-vmapple-explicit-tcg-research.patch`.

## Verified source blockers

1. **Build selection:** the aarch64 default device configuration explicitly
   sets `CONFIG_VMAPPLE=n`. Separately, upstream `VMAPPLE` depends on `HVF`, so a TCG-only
   x86/Linux build excludes the machine. It also unconditionally selects
   `MAC_PVG_MMIO`.
   [Pinned default configuration](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/configs/devices/aarch64-softmmu/default.mak#L12),
   [pinned Kconfig](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/Kconfig#L18)
2. **Graphics:** machine initialization unconditionally creates
   `apple-gfx-mmio`; that device is built with the host
   ParavirtualizedGraphics.framework. A headless x86/Linux research build
   cannot provide this device merely by choosing `-display none`.
   [Machine creation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/vmapple.c#L501),
   [build dependency](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/display/meson.build#L66)
3. **CPU:** the default is `host`; cross-ISA TCG needs an explicit emulated
   CPU. The patch preserves that upstream default for existing users and
   requires the research command to name its CPU.
   [CPU default](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/vmapple.c#L586)
4. **Guest support:** pinned upstream documentation specifies an already
   installed macOS 12.x Virtualization.framework guest and an Apple Silicon
   macOS host with HVF. It does not claim newer macOS guest support or x86
   TCG compatibility.
   [Pinned prerequisites](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/docs/system/arm/vmapple.rst#L12)

## Minimal change

The four-file patch does the following:

- Removes the explicit default-device exclusion, restricts the machine to
  AARCH64 targets, makes VMApple selectable with `HVF || TCG`, and selects
  Apple PV graphics only when the host provides `MAC_PVG`.
- Adds `research-headless=on` as an explicit TCG opt-in. TCG without that
  opt-in fails. Selecting the research mode with a non-TCG accelerator fails.
  The property is registered on the machine class so `-machine vmapple,help`
  exposes it to the launcher's backend capability probe.
- Omits the unavailable PV graphics device in research mode. Its MMIO ranges
  are left unmapped; the patch does not install success-returning stubs or
  claim a working display/Metal implementation.
- Preserves the existing ARM CPU, MMU, exception, GICv3, PSCI, and PAC code.
- Preserves the upstream virtual NVRAM AES engine, including its documented
  virtual key slots.
- Makes the AES debug hexdump's `MAX_LEN` an enum constant. GCC correctly
  rejects the upstream initialized array when its bound is a block-scope
  `static const size_t`, which is not an integer constant expression in C.
  This one-line portability fix preserves the buffer size and AES behavior.

Upstream `aes.c` defines virtual key slots using fixed 32-byte values beginning
with `01`, `02`, and `03`. The original patch author explicitly documents
these as VMApple's own fixed keys for encrypting/decrypting virtual NVRAM.
Preserving that reverse-engineered virtual-device behavior is not a
signature bypass or transplantation of physical keys. They do **not**
represent a physical Mac's UID/GID keys or Secure Enclave behavior.
[Author's explanation in upstream review](https://lists.nongnu.org/archive/html/qemu-riscv/2024-11/msg00129.html),
[pinned key-slot implementation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/aes.c#L101)

No macOS executable, boot-policy file, signed image, PAC instruction, or trust
decision is rewritten by this patch. Synthetic test firmware is project-owned
code. The patch contains no Apple firmware or proprietary key material.

## Architectural facts used by the synthetic test

These addresses come from the pinned upstream machine, rather than inferred
Apple physical-SoC register semantics:

- Firmware aperture and reset entry: `0x00100000`, size `0x00100000`.
- RAM base: `0x70000000`.
- PL011 UART: `0x20010000`, interrupt 1 in the machine IRQ map.
- GICv3 distributor: `0x10000000`; redistributor: `0x10010000`.
- Configuration region: `0x00400000`.

[Pinned memory map](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/vmapple.c#L100)

At the **guest ISA layer**, QEMU's TCG already contains architectural PAC
implementation and authentication failure behavior. A test command should
explicitly use `-cpu max,pauth=on,pauth-qarma5=on` so the selected test algorithm
is recorded. This is a standard architectural test profile; it is not a
claim that Apple's implementation-defined algorithm, exception behavior, or
every arm64e ABI case is equivalent.
[PAC helper](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/tcg/pauth_helper.c#L227),
[PAC properties](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/cpu64.c)

The existing userspace GICv3 model is selected for TCG. EL2 and EL3 remain
disabled by the machine, and secondary CPUs use the upstream PSCI HVC path.
No extra physical Apple interrupt-controller semantics were invented.
[GIC selection](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/intc/arm_gicv3_common.c#L653)

The reset path was reviewed at the **emulated CPU and firmware-entry layer**:
after EL2/EL3 removal, the CPU resets into EL1h. `arm_load_kernel()` registers
the CPU reset handlers first; VMApple then registers its own reset callback
which sets the primary PC to the firmware base. In firmware-boot mode the
generic loader leaves `env->boot_info` unset and does not override that PC.
PSCI interception occurs before architectural HVC execution, so an EL2
implementation is not required for this existing emulated PSCI conduit.
These are source-level findings; CPU reset, interrupts, and SMP still require
runtime tests to establish their behavior in the built binary.
[CPU reset EL](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/cpu.c#L431),
[firmware reset setup](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/arm/boot.c#L1171),
[PSCI interception](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/tcg/psci.c#L30)

## Reproduce the source audit

Run from the 26x86 project root, supplying a QEMU checkout path:

```powershell
python tools/backend_audit.py --source PATH_TO_QEMU --require-patched --output evidence/backend-source-audit.json
```

The audit verifies the exact upstream commit; verifies forward/reverse patch
applicability; constructs an isolated temporary git index from the pinned
commit and applies the patch there; compares resulting source bytes with
the actual checkout; checks for extra tracked source changes; and records
upstream source hashes, patch hash, source URLs, and line evidence. It leaves
the real source tree and its index unchanged. Git may cache objects created
for the temporary index.

Validation completed for the delivered patch:

- `git diff --check`: passed.
- Clean-index patch application and byte comparison: passed.
- `backend_audit.py --require-patched`: passed.
- QEMU `scripts/checkpatch.pl --no-tree --no-signoff`: 0 errors, 0 warnings.

`--no-signoff` is used because this local artifact has not been submitted
upstream and no human Developer Certificate of Origin sign-off was invented.
Source-audit success is separate from the build and runtime evidence collected
by the project runner.

## Research invocation shape

Use only project-owned synthetic firmware and disposable fixture disks for
this smoke-test shape:

```text
qemu-system-aarch64
  -machine vmapple,research-headless=on
  -accel tcg
  -cpu max,pauth=on,pauth-qarma5=on
  -smp 1 -m 512M
  -bios OWN_SYNTHETIC_FIRMWARE.bin
  -drive file=DISPOSABLE_AUX.raw,if=pflash,format=raw
  -drive file=DISPOSABLE_ROOT.raw,if=pflash,format=raw
  -nodefaults -nic none -display none -serial stdio -monitor none
```

The line breaks above are explanatory; use the project runner for actual
subprocess invocation and bounded execution. VMApple's backdoor block device
requires both AUX and root backends even for a tiny synthetic ROM. Empty
fixture disks establish no Apple boot chain or installation validity.

## Remaining proof obligations

- A legally obtained, matching Apple VM boot environment has not been run.
  AVPBooter/AUX/root image compatibility and signed boot-chain behavior remain
  unverified. User-provided assets must not be modified to make tests pass.
- Apple implementation-defined system registers, proprietary instructions,
  arm64e/PAC corner cases, and page-size/exception assumptions require real
  traces and narrowly scoped experiments.
- The virtual NVRAM AES engine retains upstream behavior. Physical SEP
  behavior and hardware-backed identity are separate, unimplemented
  capabilities; no success stub is provided for them.
- PV graphics and Metal are absent in this research mode. CPU instruction
  execution says nothing about GPU acceleration.
- Upstream's documented macOS 12 limitation is still present. Removing the
  build gate does not solve later-OS boot failures.
- Genuine Intel-Mac host enforcement and the project's AVX2 minimum are
  launcher policy. The QEMU research patch itself does not attest Apple
  hardware. A development smoke test on another x86 host is synthetic proof
  only, not a production authorization or a real-Mac test.

An unsupported guest operation must yield an actionable failure trace before
any new implementation is added. Passing evidence is limited to the layer
actually exercised.
