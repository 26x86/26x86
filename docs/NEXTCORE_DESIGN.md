# NextCore Architectural Design (Design Specification)

## Responsibility

This specification defines the *what* and *why* of NextCore. Implementation details (*how*) reside in the Build Plan specification.

## Current Status

As of the 2026-09-12 documentation review, the x86 EFI product executes authored
A64 fixtures and bounded original-input prefixes. Normal ARM64e entry remains
`NOT_READY`; explicit incomplete-prefix diagnostics remain `ABORTED`. Passing
native/provider/UEFI tests does not establish physical macOS boot.

Seven independent module repositories supply the implementation. Native integer
execution, checked memory providers, immutable stage-1 and one-way dynamic MMU
fixtures are implemented within their documented bounds. Target-specific platform
services, persistent storage and guest display/input remain incomplete.

The active physical target is Samsung 750XHD. Its acceptance is external-media
installation, reboot and an interactive macOS 27 desktop; acceleration follows.
Hardware coverage is documented in [compatibility](compatibility.md), while
[current progress](progress.md) owns moving execution and publication receipts.
The 2026-09-08 picker result is Q35/TCG OVMF evidence, not physical acceptance.

## Target State

- Concise definition of what NextCore is and why it exists.
- Exhaustive stage-by-stage definition of the macOS EFI boot sequence.
- Comparative analysis illustrating how NextCore fulfills iBoot functions through clean-room methods.
- Clear articulation of OpenCore concepts inherited versus proprietary/hack layers discarded.
- Independent verification gates for EFI entry, child loader invocation, XNU kernel execution, userspace launch, and live Metal acceleration.

---

## Codified Decisions

### D1. NextCore Identity

> *Basis: AGENTS.md §0 Core Principles — (a) macOS boots in an EFI environment, (b) functional parity with iBoot without copying code, (c) inheritance of OpenCore concepts with zero source dependency.*

NextCore is an open, clean-room bootloader designed to initialize and boot macOS within standard UEFI firmware environments:

1. **Targets the functional role of early boot using clean-room methods:** NextCore develops external interfaces required by macOS post-firmware (DeviceTree representations, physical memory maps, boot arguments, kext catalogs, and handoff structures) without utilizing Apple proprietary binaries, decryption keys, signature blobs, or internal symbols. *Functional equivalence through independent implementation.*
2. **Inherits architectural principles from OpenCore:** Employs a declarative, `config.plist`-driven configuration model, directory layout compatibility with `EFI/OC/`, and interface compatibility across ACPI, DeviceProperties, boot-args, and kext registries. Source code dependency remains strictly zero.

**Execution Scope:** The bootloader core runs under UEFI firmware. Sustained execution post-`ExitBootServices()` relies on companion HAL, JIT, and driver virtualization layers (D9–D11). An individual EFI binary does not presume indefinite ownership of all hardware interrupts without these supporting subsystems.

Implemented in Rust with an independently authored native C JIT/runtime, NextCore delegates cryptographic trust decisions (e.g. Bootability Manifest, secure boot signatures) to platform policy. It is not an exploit payload or signature bypass utility.

Non-Goals:
- Reproduction or decompilation of proprietary Apple binaries (AGENTS.md §0).
- Bundling extracted IPSW components, private certificates, or cryptographic keys in the public tree.
- Incorporating fragile firmware hacks or runtime memory patchers (see D4).

Target Audience: Operators seeking an open, maintainable, clean-room EFI boot pathway for macOS on modern and legacy x86 hardware.

### D2. macOS Boot Flow (EFI Environment)

> *Basis: AGENTS.md §0 + UEFI 2.10A Specification + macOS Boot Architecture.*

The target execution path comprises five distinct verification tiers:

1. **EFI Entry & System Table Discovery:**
   - *Input:* NextCore EFI binary loaded by UEFI firmware; pointer to `EFI_SYSTEM_TABLE`.
   - *Output:* Initialized Boot Services handles (memory map, console protocols, file system volume handles).
   - *Boundary:* Operates strictly via standardized protocol discovery.
2. **Configuration Parsing:**
   - *Input:* Declarative `config.plist` read from the boot volume (`EFI/OC/config.plist`).
   - *Output:* Strongly-typed configuration structures (SMBIOS metadata, ACPI tables, kext catalogs, DeviceProperties, boot-args).
   - *Boundary:* Parsing and schema validation only; hardware validation occurs in later stages.
3. **Hardware & Subsystem Preparation:**
   - *Input:* Parsed configuration structures and firmware ACPI tables.
   - *Output:* Resolved ACPI override sets, DeviceProperties dictionaries, and ordered kext catalogs.
   - *Boundary:* Distinguishes host configuration storage from table publishing in EFI.
4. **Boot Chain Handoff:**
   - *Input:* Prepared boot environment and designated OS EFI loader or Mach-O kernelcache.
   - *Output:* Standard EFI child invocation (D2-A) or direct kernel entry complying with target ABI specifications (D5).
   - *Boundary:* Internal roundtrip tests do not prove boot execution; memory lifetimes, entry state transitions, and exception vectors must be verified on bare metal or hardware emulators.
5. **XNU Execution & Userspace Initialization:**
   - *Input:* Physical memory, descriptor tables, and handoff pointers initialized in Step 4.
   - *Output:* Kernel initialization messages (`Darwin Kernel Version`) followed by `launchd`, `loginwindow`, and `WindowServer`.
   - *Boundary:* Full transition to XNU and companion runtime subsystems. Failures during handoff must be attributed to the faulty boot tier rather than assumed to be kernel issues.

#### D2-A. Intermediate Integration Pathway via Explicit OS EFI Loader

- Allows invoking secondary 64-bit EFI applications via standard `LoadImage()` and `StartImage()` protocol interfaces.
- The target is selected via explicit file path on the same volume; recursive execution of NextCore is prevented.
- `LoadOptions` buffers are populated only when explicit invocation contracts are established; arbitrary internal plists or raw argument strings are not forced onto unknown loaders.
- NextCore does not call `ExitBootServices()` prior to launching child EFI applications; subsequent memory allocation and kernel entry are managed by the child.

### D3. iBoot Role Replacement Matrix

| Functional Domain | NextCore Approach | Architectural Rationale |
|-------------------|-------------------|-------------------------|
| Trust Cache / Manifest Validation | Delegates trust verification to caller / platform policy | Cryptographic trust policy belongs outside the bootloader core |
| Hardware Description Tree | Decouples internal device model from external XNU wire ABI (D7) | Translates open standards (ACPI/SMBIOS) into expected formats without proprietary code |
| RAM Disk Allocation | Utilizes standard UEFI ramdisk protocols | Vendor-proprietary ramdisk parsers cannot be maintained in clean-room code |
| Kernelcache Ingestion | Resolves inputs via UEFI file services; validates targets via D5 | Separates Mach-O header parsing from kernel placement and execution |
| Kext Registration | Employs declarative configuration-driven kext catalogs | Open list specifications provide full compatibility without proprietary kext injection hacks |
| Firmware / Kernel Signatures | Defers to firmware and platform Secure Boot infrastructure | Cryptographic key management is outside public repository boundaries |
| Memory Map Construction | Preserves firmware descriptor attributes; converts descriptors to target ABI via D5 | Avoids fragile memory map patching; honors underlying firmware allocation |
| Console & Framebuffer | GOP / ConOut during EFI; calibrated linear framebuffers during handoff | Terminal protocol calls cease post-Boot Services; framebuffer handoff is decoupled from Metal acceleration |
| Boot Arguments | Formats argument strings according to target ABI (D5) or child contracts (D2-A) | Writing EFI NVRAM variables does not prove kernel ingestion; requires direct handoff validation |
| SMBIOS Exposure | Exposes firmware tables by default; applies profile transforms via HAL (D11) | Distinguishes table collection from runtime synthesis |

### D4. OpenCore Concept Inheritance

**Inherited:**
- Declarative `config.plist` configuration architecture.
- Filesystem layout convention (`EFI/OC/`).
- Property schemas for ACPI, DeviceProperties, and boot-args.
- Kext catalog declarations.

**Intentionally Discarded:**
- OpenCore source dependencies (the independent implementation includes Rust and native C).
- Build system sharing (uses native Cargo workspace).
- Trademarks and proprietary branding.
- Embedded private keys, certificates, and binary blobs.
- Complex firmware patching layers (`OpenRuntime`, `OpenCanopy`).
- Memory map patching (`AptioMemoryFix`). Firmware descriptors are respected directly.

### D5. Internal Handoff Abstraction & Public XNU Handoff ABI

#### D5-A. Public Sources & Reference Targets
Interface definitions are derived from Apple official public release **`xnu-12377.121.6`** (commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`).
The public header [pexpert/i386/boot.h](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/i386/boot.h) defines the external wire format for x86 handoff:

- **x86 Entry Protocol:** Early kernel entry on x86 expects 32-bit protected mode with paging disabled, flat memory addressing, and boot argument pointer in `EAX` ([osfmk/x86_64/start.s](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/x86_64/start.s)). Standard 64-bit EFI function calls cannot jump directly to this entry without an architectural mode transition.
- **Consumption Pipeline:** `vstart` consumes memory maps, kernelcache descriptors, and DeviceTree structures ([osfmk/i386/i386_init.c](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/i386/i386_init.c)).
- **ARM64 Isolation:** AArch64 handoff utilizes distinct physical memory layouts ([pexpert/arm64/boot.h](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h)) and must not be conflated with x86 structures.

The [ARM64e entry contract](NEXTCORE_ARM64E_ENTRY_CONTRACT.md) distinguishes legacy x0 boot arguments from SPTM cold-entry x1/x2 arguments. Target-specific provisioning and live services remain open.

#### D5-B. Abstract Representation & Wire Encoders
NextCore maintains an internal strongly-typed representation of physical memory maps, kernel positioning, video descriptors, and DeviceTree nodes, translating these to external wire formats via dedicated adapters prior to kernel invocation. Host pointers and data structures are never cast directly into guest memory.

### D6. Version Discovery Policy

NextCore dynamically detects available macOS installations from storage media rather than hardcoding static OS version lists. The configuration wizard reflects verified media identifiers detected at runtime.

### D7. DeviceTree Generation Boundaries

The internal DeviceTree model represents a platform-agnostic key-value hierarchy based on IEEE 1275, devicetree.org specifications, and ACPI/SMBIOS inputs. Serialized flattened trees provided to XNU are generated by clean-room encoders conforming to open ABI requirements without copying proprietary internal structures.

### D8. Clean-Room Knowledge Transfer Rules

Knowledge derived from isolated analysis is restricted to single-sentence natural-language functional requirements (e.g. "The kernel requires contiguous physical page tables below 4GB"). Code snippets, struct layouts, offsets, and magic numbers must never cross into public design documentation or code.

### D9. Instruction Set Emulation (ISE)

- **Current objective:** Translate the required ARM64e macOS instruction behavior into generated x86 code with a separate Rust reference and checked memory/provider contracts. Legacy x86 missing-instruction work is a distinct scope.
- **Execution Architecture:** Sustained emulation following boot handoff requires dedicated hypervisor or kernel exception trapping. Traps must distinguish `#UD` (invalid opcode) from `#GP` (general protection faults), decoding instruction lengths and register contexts cleanly.
- **Implementation Status:** `nextcore-ise` executes supported A64 integer families as generated x86 and verifies them against independent reference/provider fixtures. Unsupported operations remain gated; this is not a complete A64 CPU or physical platform.

### D10. GPU Abstraction & Graphics Acceleration

- **Objective:** Provide a uniform virtual device interface across AMD, NVIDIA, and Intel graphics hardware, routing compute and render commands to hardware backends or software rasterizers.
- **Metal Verification Standard:** True Metal acceleration requires successful device enumeration, resource creation, command queue execution, and fence synchronization in the guest. Framebuffer scanout alone does not constitute Metal acceleration.
- **Linux Driver Backends:** Porting open-source Linux DRM/KMS drivers into the abstraction layer is an approved design path.

### D11. Hardware Abstraction Layer (HAL)

- **Objective:** Synthesize SMBIOS tables, DeviceTree nodes, and ACPI tables matching target hardware profiles, isolating guest macOS from underlying motherboard quirks.
- **Clean-Room Standard:** HAL components utilize documented public specifications without incorporating proprietary firmware patchers.

### D12. Apple Silicon Sandbox (APLS)

- **Objective:** Orchestrate execution of Apple Silicon macOS guest workloads using Virtualization.framework on genuine Apple Silicon Macs, or using QEMU TCG emulators for research.
- **Separation of Tiers:** Hardware virtualization on native Apple Silicon hosts is strictly separated from x86 OVMF EFI execution. Emulation milestones (e.g. iBSS DFU resets) are tracked as protocol verification rather than finished boots.

### D13. NextCore Product Identity

- Public UI, EFI boot screens, and CLI tools consistently display the unified brand: **NextCore**.
- External attribution to OpenCore and upstream projects is preserved without misrepresenting external binaries as original NextCore implementations.
- macOS 27 GoldenGate compatibility and guest Metal acceleration remain foundational engineering milestones.

### D14. Standalone Graphical EFI Boot Picker

NextCore features a native graphical boot picker operating entirely within UEFI Boot Services:
- Dark theme featuring the NextCore wordmark, centered volume selection tiles, highlighted selection borders, and keyboard navigation (Left/Right/Tab to navigate, Enter to boot, Esc to cancel).
- Renders via standard UEFI GOP `Blt` interfaces with automatic fallback to Simple Text Output on headless or unsupported displays.
- Selecting an entry launches the designated EFI application via standard `LoadImage` and `StartImage` services without terminating Boot Services prematurely.
- Fully decoupled from proprietary visual bootloader assets.

OPEN_QUESTION: Design:Complete persistent guest display, storage and platform ownership after firmware transition before claiming physical macOS startup.

SPTM applicability to the selected j274 target is unverified. The diagnostic
profile name does not establish its normal startup ABI; see the
[entry contract](NEXTCORE_ARM64E_ENTRY_CONTRACT.md).

## Mandatory website EFI package

Current Status: Website deployment requires a verified `prebuiltefi.zip` built
from the immutable public source commit recorded in `docs/data/prebuilt.json`.
Normal macOS startup remains NOT_READY and physical desktop boot is unverified.

Target State: Every published website includes a downloadable, source-bound EFI
archive. The docs branch is not the runtime source: CI checks out the exact
manifest commit recursively into a separate directory and verifies its Git and
submodule identities before compiling release x86_64 UEFI binaries. The baseline
`EFI/BOOT/BOOTX64.EFI` uses the normal build with no diagnostic feature selection.
The mapped diagnostic remains `diagnostics/NXARMJIT.efi`; it must never replace
or impersonate the baseline boot entry. No Apple payload is included.

The archive contains an explicit, empty public configuration at
`EFI/OC/config.plist`, the firmware's existing configuration path. It selects no
external loader, displays "No enabled boot entries" and returns NOT_FOUND to
firmware. It does not guess a target computer's disk, kernel or settings.
README instructions explain isolated removable-media use and separate diagnostic
configuration. Source revision, submodule revisions, build commands, tool versions
and per-file SHA-256/size records are included in the archive manifest.

The packaging gate validates PE32+ AMD64 EFI application headers, nonempty mapped
sections and entry points, then reopens the ZIP and verifies its exact path set,
CRC, sizes and hashes. Missing binaries, changed source identity, extra entries,
invalid PE or digest mismatch fail the job before Pages artifact upload. A public
JSON sidecar contains the archive SHA-256. Source pin updates are explicit reviewed
manifest changes. Unit negative controls cover rejected binaries and altered ZIPs;
an actual build validates the positive boundary. This package proves distribution
integrity and compilation, not macOS installation or physical boot.
