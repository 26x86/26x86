# Apple Silicon Sandbox

**Current Status:** Separate bounded Sandbox/VSK and VMApple research paths; original OS boot unverified.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

26x86 has two execution paths: native OpenCore/root patching and an experimental
Apple Silicon Sandbox. User-facing platform research branding is 26x86; the
internal `venfire` namespace remains available under `research/venfire`.

## Scope relative to the current product

This page preserves the separate Sandbox/VSK and VMApple research contracts.
The VSK `AppleIntelOnly` admission policy is specific to that design and does
not redefine the active NextCore physical x86 target. The product's live status,
startup gaps and physical acceptance are recorded in [progress](progress.md),
[compatibility](compatibility.md) and [Design](NEXTCORE_DESIGN.md).

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

The iBoot(AArch64) MachineType is a macOS guest personality only. Its guest-policy
matrix is fixed and enforced before firmware inputs are opened:

```text
iBoot(AArch64)
 ├─ macOS     → Allowed guest target; boot unverified
 ├─ iOS       → Unsupported
 └─ iPadOS    → Unsupported
```

Other mobile Apple operating systems are rejected by the same scope validator.
The personality targets interfaces needed by macOS boot and recovery; current
implementations are partial. DFU and Local IPSW Recovery are macOS recovery paths; the local image
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
[`integration/vmapple-gui-bootpicker-report.json`](https://github.com/26x86/26x86/blob/main/integration/vmapple-gui-bootpicker-report.json),
with the earlier iBSS-only report preserved separately at
[`integration/vmapple-gui-recovery-report.json`](https://github.com/26x86/26x86/blob/main/integration/vmapple-gui-recovery-report.json).

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

For a VM created by Virtualization.framework, pass its `macosvm.json` to the
native worker described below. The legacy QEMU direct command is intentionally
rejected for target 26/27 because QEMU's documented VMApple guest support does
not cover those modern macOS versions; QEMU remains available for the separate
recovery/protocol research path.

### Portable VMApple TCG path (non-Apple host)

The native worker above is not the only host execution layer. When the host is
Linux, Windows/WSL, or another non-Apple system, the repository now provides an
explicit software-emulation path. It builds a pinned QEMU source revision with
the reviewed `research/venfire/patches/series`; the series exposes an explicit
TCG/headless mode, barrier/recovery plumbing, a default-off BDIF write gate,
and the opt-in j274 Stage2 contract (EL2, observed implementation-defined
registers, and high-RAM relocation alias). It does not alter a guest image,
its signatures, or its VM bundle.

Build the exact binary in a new directory (the source checkout must be clean):

```sh
python3 Tools/build_vmapple_tcg.py \
  --output /tmp/26x86-vmapple-tcg \
  --source /path/to/qemu-at-ff1d2d19d7e2 \
  --jobs 4
```

The build receipt pins the QEMU commit, every patch digest, configure/build
commands, binary digest, `vmapple` machine, and `tcg` accelerator. A normal upstream
QEMU binary is not silently accepted: the runner probes this exact binary for
the VMApple machine, TCG, and BDIF storage device before opening the guest.

Run an unchanged Virtualization.framework bundle through headless TCG with an
explicit research acknowledgement:

```sh
python3 -m x86 vmapple run-tcg \
  --target 27 \
  --qemu /tmp/26x86-vmapple-tcg/qemu/build/qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /path/to/AVPBooter.vmapple2.bin \
  --vm-json /path/to/macosvm.json \
  --output /tmp/26x86-goldengate-tcg \
  --observation-timeout 900 \
  --research-only --json
```

This path uses qcow2 copy-on-write overlays for AUX/root and re-hashes the
original firmware, JSON, and storage files after the process exits.  It is
headless by design; `--display auto` resolves to `none`/`dbus` only when the
selected QEMU advertises that backend.  The fixed Rust VMApple graph and the
QEMU GICv3/BDIF graph are contracts for this TCG layer, not a claim that the
native Sandbox AIC, ANS, DART/SART, PV graphics, or Metal stack is emulated.

For the macOS 27 j274 IPSW, the decoded raw iBoot Stage2 can be selected
explicitly. This is a firmware-execution probe, not an AVPBooter replacement:
the runner enables a bounded QEMU `exec` trace and records Stage2 entry and the
observed high-RAM relocation separately from UART iBoot/XNU/userspace evidence.

```sh
python3 -m x86 vmapple run-tcg \
  --target 27 \
  --qemu /tmp/26x86-vmapple-tcg/qemu/build/qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /path/to/iboot-stage2-decoded.bin \
  --firmware-kind iboot-stage2 \
  --vm-json /path/to/macos27-j274-macosvm.json \
  --research-graphics --duration 60 --research-only --json
```

The report fields `firmware_execution_evidence.stage2_execution_observed` and
`high_ram_relocation_observed` mean that QEMU executed the supplied raw Stage2
input. `graphics_host_evidence.host_frame_presented` means only that the
optional Reims host swapchain presented a synthetic frame; it is not evidence
of WindowServer, AGX, Metal, or a guest framebuffer. `macos_boot_verified`
still requires target-matching Darwin/XNU and userspace UART markers.

The pinned QEMU map is explicit: firmware `0x00100000/0x00200000`, config
`0x00400000/0x00010000`, GIC distributor `0x10000000/0x00010000`, GIC
redistributors `0x10010000/0x00400000`, UART `0x20010000/0x00010000`, PL031
RTC `0x20050000/0x00001000`, PL061 GPIO `0x20060000/0x00001000`, pvpanic
`0x20070000/0x2`, BDIF `0x30000000/0x00200000`, APV graphics/IOSFC
`0x30200000/0x10000` and `0x30210000/0x10000`, AES windows
`0x30220000/0x4000` and `0x30230000/0x4000`, PCIe ECAM
`0x40000000/0x10000000`, PCIe MMIO `0x50000000/0x1fff0000`, and RAM from
`0x70000000`, with a research-only RAM alias at `0x1fc000000` for the j274
Stage2 relocation path. Its realized IRQ routes are UART 1, RTC 2, GPIO 5, IOSFC
`0x10`, graphics `0x11`, AES `0x12`, and PCIe `0x20`; the virtual timer is
PPI 27. The current Rust descriptor records only its bounded subset and the
same-call reset/validity gate; it does not silently claim the AES, PCIe, or PV
graphics windows are implemented. Unsupported firmware backing, AES DMA,
PCIe enumeration, and PV graphics accesses fail closed. The map is QEMU
VMApple behavior, not
evidence of the physical M1 AIC/DART or an iBoot-compatible native machine.

The command returns success only when the UART observer sees a target-matching
Darwin/XNU banner and a userspace marker.  A TCG process start, a machine help
line, an iBoot banner, or a recovery prompt is not `macos_boot_verified`.
Without caller-supplied original Golden Gate firmware and a provisioned bundle,
the evidence gate must remain false.  This preserves the distinction between
the portable TCG/emulation layer and the native Apple Virtualization.framework
layer below.

`macosvm.json` is treated as an atomic, read-only bundle: the ECID comes from
the binary-plist `machineId`, the hardware-model digest comes from
`hardwareModel`, and exactly one `aux` plus one `disk` storage entry is
required. The runner applies the official VMApple `0x4000` AUX metadata view
offset to the original `aux.img`, then creates only qcow2 copy-on-write
overlays. It refuses a manually supplied UUID, AUX, root, or offset that does
not match the bundle. This implements the trim documented by
[QEMU's VMApple guide](https://www.qemu.org/docs/master/system/arm/vmapple.html)
without modifying the source image. A read-only preflight is available with:

```sh
python3 -m x86 vmapple inspect-storage --vm-json /path/to/macosvm.json --json
```

### Native Apple-Silicon VM provisioning

The repository does not download, decrypt, patch, or overwrite an IPSW. On the
actual Apple-Silicon macOS host that owns the Virtualization.framework restore
workflow, a caller can create a new VM bundle with the locally installed
`macosvm` tool:

```sh
python3 -m x86 vmapple provision \
  --ipsw /path/to/UniversalMac_26...ipsw \
  --output /path/to/new-goldengate-vm \
  --disk-size 32g \
  --timeout 86400 \
  --json
```

`X86_MACOSVM` may name the `macosvm` executable and `X86_VMAPLE_IPSW` may
provide the IPSW path. The command is intentionally fail-closed unless the
host is Apple-Silicon macOS and the standard
`Virtualization.framework/Resources/AVPBooter.vmapple2.bin` is present. It
rejects WSL/Linux execution, invalid disk sizes (the bounded range is `1k` to
`4t`), a non-regular IPSW, and an existing output directory. The output is
created as a new directory, and contains the tool's `macosvm.json`, AUX/disk
images, stdout/stderr logs, and a `provision-report.json` receipt. The receipt
re-validates `machineId`, `hardwareModel`, and the exact AUX/root storage
entries through the same immutable loader used by direct boot.

Provisioning success is only a valid VM-input receipt. It is not XNU,
userspace, installer, display, or Golden Gate boot evidence. Run the direct
entry separately with `--vm-json` and require both Darwin/XNU and userspace
UART markers before treating `macos_boot_verified` as true.

### Native Golden Gate launch

For macOS 26/27, use the native Virtualization.framework runner after a
bundle has been provisioned on the Apple-Silicon host. The QEMU VMApple path
is retained as a research/compatibility harness; the upstream QEMU guide
currently documents guest support through macOS 12.x and says newer guest
versions are not supported by its guest-side implementation. Do not interpret
a QEMU process start or a Cocoa window as modern macOS boot evidence.

The native worker runs the caller's `macosvm.json` with `macosvm --ephemeral`,
so AUX/root are APFS-cloned for the session. It never rewrites the bundle,
uses the default serial channel (PTY mode is intentionally not enabled because
the tool requires an interactive newline for PTY attachment), and stores a
combined `macosvm.log` plus `launch.json` evidence receipt in a new output
directory:

```sh
python3 -m x86 vmapple run-native \
  --target 27 \
  --macosvm /usr/local/bin/macosvm \
  --vm-json /path/to/goldengate-vm/macosvm.json \
  --output /tmp/26x86-goldengate-native \
  --observation-timeout 900 \
  --duration 900 \
  --research-only --json
```

`run-native` is host-gated to Apple-Silicon macOS and requires the explicit
`--research-only` acknowledgement. The report distinguishes
`native_runtime_started`, `xnu_executed`, `macos_userspace_reached`,
`macos_boot_verified`, and `installation_verified`. Only the first two boot
layers are observable from serial evidence; the Darwin kernel major must also
match the requested target (26 or 27). The host macOS major must be at least
the guest major because Virtualization.framework does not run a newer guest on
an older host. A successful process exit,
Virtualization.framework configuration, or installer marker does not by itself
prove a completed Golden Gate installation. Use `native`, `native-run`, and
`run-native` as equivalent CLI spellings.

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
