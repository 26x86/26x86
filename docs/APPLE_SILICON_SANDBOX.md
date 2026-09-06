# Apple Silicon Sandbox

26x86 has two execution paths: native OpenCore/root patching and an experimental
Apple Silicon Sandbox. User-facing platform research branding is 26x86; the
internal `venfire` namespace remains available under `research/venfire`.

## Architecture contract

The adopted VF-SPEC-001 v0.1 now defines the [VSK implementation](VSK.md):
a VMX-root kernel with isolated Execution, Block, GPU and Shader cells. The
direct EFI JIT described below is an existing diagnostic implementation, not
the final VSK isolation boundary. New product admission is `AppleIntelOnly`
with mandatory VMX/EPT, VT-d and interrupt remapping.

The Sandbox is an x86_64 UEFI engine launched by 26x86-OpenCorePkg. It translates
AArch64 guest code into x86_64 machine code. A Linux installation and a QEMU
process are not runtime dependencies. QEMU/TCG research remains a reference and
comparison harness; it is not substituted for this EFI implementation.

The virtual Apple SoC uses **AIC**, not GIC. Guest startup is an **iBoot** path.
Windows on ARM is outside the target platform. `config.plist` is the source for
Sandbox enablement, target macOS, engine paths, original guest boot assets,
`SandboxSMBIOS`, virtual hardware and device properties. Host SMBIOS is distinct
from virtual guest identity; selecting an identity does not create Apple trust
material or establish an accepted boot chain.

The minimum CPU is x86_64 with **SSE4.1 and SSE4.2**, corresponding to the requested
Mac Pro 2009 baseline. AVX and AVX2 are not required by the native engine.
Diagnostic EFI CPUID checks the actual boot CPU. VSK additionally requires
measured platform admission and all isolation features; it has no general-PC
or outer-VM product bypass setting. This policy does not change the source license.

## Evidence and current execution

macOS 26 Tahoe and macOS 27 Golden Gate are development targets. Selecting one
does not certify its bootability. The native EFI engine currently tests authored
AArch64 instruction programs. Full privileged execution, Apple hardware and
the original macOS iBoot-to-userspace path are not yet verified.

`python -m x86 sandbox --target 26 --json` reports the current capabilities.
After an EFI build, `python -m x86 sandbox --target 26 --output <new-folder>`
stages the verified EFI self-test and its SHA-256 receipt. It refuses an existing
folder. The receipt and GUI explicitly distinguish this from macOS boot media.
For the VSK path, pass a production `VSKBOOT.EFI` receipt, a signed bundle and
the external raw32 public key to the same command (`--vsk-bundle` and
`--trusted-public-key`; use `--vsk-efi` for a non-default EFI path). The stager
binds the key hash to the EFI trust anchor, re-verifies the copied bundle, and
places the inputs under `EFI/26x86/VSK`. It still stops before EBS/VMX and makes
no claim about macOS or physical-Mac boot.

The OVMF input harness can also run the valid case in a visible QEMU window:

```sh
python3 sandbox/vsk/tools/verify_efi_inputs.py \
  --bundle /path/to/signed-bundle \
  --output /tmp/26x86-vsk-gui-run \
  --gui
```

`--gui` selects QEMU's GTK display backend and intentionally runs one case so
that validation does not open three windows. This is an EFI/VSK input diagnostic
only: it does not load `iBoot`, start a macOS guest, or turn a target-27 label
into Golden Gate boot evidence. Headless `--display none` remains the default
for repeatable CI checks; `--display gtk|sdl` is available for an explicit
single-case run. On WSL or a non-default QEMU installation, pass `--qemu`,
`--ovmf-code` and `--ovmf-vars` explicitly (or set `QEMU_SYSTEM_X86_64`,
`OVMF_CODE` and `OVMF_VARS`). The resulting report records the resolved QEMU
version and SHA-256 hashes of both OVMF inputs so a visible run can be compared
with a headless run without treating the window itself as boot evidence.

An external lab run also exercised the Apple VMApple recovery path with a GTK
build of QEMU 11.1.50. It used the unchanged macOS 27.0 (26A5425a) personalized
`iBSS` input, a COW overlay over empty AUX/root fixtures, and the developer-only
host bypass. The GTK window was created and the real firmware completed 172 DFU
data blocks, reached `WAIT_RESET`, and acknowledged the USB reset. The saved
report recorded `input_integrity: true`, `signature_acceptance_verified: false`,
and `macos_boot_verified: false`. The host was Linux/x86_64 under WSL rather
than a physical Apple Intel Mac, so this is recovery-protocol evidence only; it
does not establish iBoot-to-XNU or Golden Gate user-space execution. A follow-up
developer-only probe kept the device at the iBSS DFU identity (`05ac:1227`)
after the reset, so no iBEC bulk endpoint was advertised and no iBEC/XNU claim
was recorded. The harness intentionally stops there instead of fabricating
signature acceptance or adding a release bypass.
The sanitized result is retained in
[`integration/vmapple-gui-recovery-report.json`](../integration/vmapple-gui-recovery-report.json).

The prior Linux research directory includes useful original-image hashing,
normal personalization and device experiments. It retains its historical CPU
and release restrictions; neither those experiments nor a synthetic UEFI test
constitute successful macOS 26/27 boot on a physical Mac.

## Licensing and scope

The project follows the existing OCLP-derived `LICENSE.txt`, including its four
numbered conditions. Third-party source and binary copyrights remain intact.
The legacy private host-bypass artifact policy is retained for those artifacts;
it is not applied as an additional restriction on upstream licensed source.
The Sandbox does not modify guest signatures, fabricate personalization tickets,
or silently apply native root patches to its guest.

Native root patching is a separately selected path, explicitly authorized for
this project. Abstraction binaries must bind to an exact guest architecture,
OS build, ABI and payload digest; an x86_64 kext is not an ARM64 driver merely
because it is wrapped in an abstraction manifest.
