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
