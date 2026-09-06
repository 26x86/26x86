# Apple Silicon Sandbox

26x86 has two execution paths: native OpenCore/root patching and an experimental
Apple Silicon Sandbox. User-facing platform research branding is 26x86; the
internal `venfire` namespace remains available under `research/venfire`.

## Architecture contract

The adopted VF-SPEC-001 v0.1 now defines the [VSK implementation](VSK.md):
a VMX-root kernel with isolated Execution, Block, GPU and Shader cells. The
EFI-integrated Rust/JIT path described below is a bounded diagnostic
implementation, not the final VSK isolation boundary. New product admission is
`AppleIntelOnly` with mandatory VMX/EPT, VT-d and interrupt remapping.

The Sandbox is one x86_64 UEFI package launched by 26x86-OpenCorePkg. Its
existing C EFI entry owns protocols, page allocation, W^X and cleanup; a
statically linked Rust `no_std` micro-preOS validates the bounded context and
orchestrates the existing AArch64-to-x86_64 JIT through a C wrapper. There is no
second Rust EFI image, kernel, stage-2 loader, or host operating-system runtime.
A Linux installation and a QEMU process are not runtime dependencies.
QEMU/TCG research remains a reference and comparison harness; it is not
substituted for this EFI implementation.

The virtual Apple SoC uses **AIC**, not GIC. Guest startup is an **iBoot** path.
Windows on ARM is outside the target platform. `config.plist` is the source for
Sandbox enablement, target macOS, engine paths, original guest boot assets,
`SandboxSMBIOS`, virtual hardware and device properties. Host SMBIOS is distinct
from virtual guest identity; selecting an identity does not create Apple trust
material or establish an accepted boot chain.

The VMApple/QEMU comparison profile is derived from the archived
[qemu-t8030](https://github.com/TrungNguyen1909/qemu-t8030) device model. That
project targets an iPhone 11/T8030 iOS guest. 26x86 uses its public device
topology as a research reference (AIC, ANS/NVMe, DART/SART, Apple peripherals
and framebuffer helpers) and does not import its iOS firmware, device tree or
restore flow. The current TCG VMApple backend still exposes GICv3 and the
project's BDIF AUX/root path; this is recorded as a capability gap instead of
being relabelled as AIC/ANS support. Use `python3 -m x86 vmapple capabilities`
to inspect the pinned reference and the current implementation boundary.

The iBoot(AArch64) MachineType is a macOS guest personality only. Its supported
matrix is fixed and enforced before firmware inputs are opened:

```text
iBoot(AArch64)
 ├─ macOS     → Supported
 ├─ iOS       → Unsupported
 └─ iPadOS    → Unsupported
```

Other mobile Apple operating systems are rejected by the same scope validator.
The personality implements only the interfaces needed by macOS boot and
recovery. DFU and Local IPSW Recovery are macOS recovery paths; the local image
name is `_default.ipsw`. A request for iOS/iPadOS, Fastboot, or another recovery
image is stopped with a policy error before any DFU transfer. The broader
Venfire MachineType catalogue in the attached design remains a reference for
future personalities and does not expand this iBoot scope.

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
for repeatable CI checks; VMApple `auto` selects Cocoa on native Apple Silicon
and a QEMU-advertised headless backend (normally `none`) on Linux/WSL.
`--display gtk|sdl|cocoa|none` remains available for an explicit run. On WSL or
a non-default QEMU installation, pass `--qemu`,
`--ovmf-code` and `--ovmf-vars` explicitly (or set `QEMU_SYSTEM_X86_64`,
`OVMF_CODE` and `OVMF_VARS`). The resulting report records the resolved QEMU
version and SHA-256 hashes of both OVMF inputs so a visible run can be compared
with a headless run without treating the window itself as boot evidence.

A 26x86 GUI bridge run (Windows to WSLg) exercised the Apple VMApple recovery
path with a GTK build of QEMU 11.1.50. The live path supplied the unchanged
macOS 27.0 (26A5425a) BuildManifest, original iBSS/iBEC IM4P files and a local
TSS request helper. Apple returned status `0` for both component tickets and
the bound LocalPolicy; the original payload hashes were preserved and
`installer_modified` remained `false`. A COW overlay over empty AUX/root
fixtures received all guest writes.

The GUI and CLI now run a bounded, read-only storage preflight before the
visible recovery launch. A zero-filled AUX or root view is labelled
`unprovisioned-zero` (or `partially-unprovisioned`) and the GUI launch control
remains disabled. Non-zero data is still `unverified` until a supported Apple
Silicon host supplies a hardware-model-matched auxiliary-storage provisioning
receipt; byte markers do not establish an install target.

The GTK window was created and the real firmware completed 173 DFU data blocks
(including the DFU suffix), reached `WAIT_RESET`, and acknowledged the USB
reset. It then re-enumerated as Apple `05ac:1281`, advertised bulk OUT endpoint
4, accepted the LocalPolicy and iBEC transfers, and acknowledged `go`. With the
explicit optional-RPC experiment enabled, the original iBEC reached the Stage2
command prompt. The restore chain sent the five official restore roles, recorded
the expected pre-boot notification STALL, and received a `bootx` acknowledgement.
iBoot then emitted a panic before XNU, so `signature_acceptance_verified`,
`xnu_executed` and `macos_boot_verified` remain `false`; no Recovery or Golden
Gate installer UI was rendered. The Linux/x86_64 host is not a physical Apple
Intel Mac, and the Linux QEMU build has no Apple ParavirtualizedGraphics device,
so this remains recovery-protocol evidence. The runner records this failure
boundary and never forces a transition or modifies the installer.

The VMApple report records the explicit guest metadata `Apple M1 (Virtual)` /
`VM0001` as `virtual_identity_mode: metadata-only`; it does not claim Apple
hardware attestation. The sanitized result is retained in
[`integration/vmapple-gui-bootpicker-report.json`](../integration/vmapple-gui-bootpicker-report.json),
with the earlier iBSS-only report preserved separately at
[`integration/vmapple-gui-recovery-report.json`](../integration/vmapple-gui-recovery-report.json).

The prior Linux research directory includes useful original-image hashing,
normal personalization and device experiments. It retains its historical CPU
and release restrictions; neither those experiments nor a synthetic UEFI test
constitute successful macOS 26/27 boot on a physical Mac.

The normal macOS entry is now a separate runner path. Selecting
`--boot-selection macos` skips iBSS/iBEC personalization and DFU, starts the
provisioned AUX/root pair through AVPBooter, and records separate Darwin/XNU and
userspace UART markers. On an Apple-Silicon macOS host the runner selects QEMU
HVF and the normal VMApple graphics path; elsewhere it remains the explicit
TCG research-headless path. No marker is promoted to `macos_boot_verified` until
both XNU and userspace evidence are present, and a Golden Gate installation is
still a separate receipt/UI claim.

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
