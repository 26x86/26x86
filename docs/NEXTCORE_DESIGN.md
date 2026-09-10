# NextCore Architectural Design (Design Specification)

## Responsibility

This specification defines the *what* and *why* of NextCore. Implementation details (*how*) reside in the Build Plan specification.

## Current Status

- **Host Architecture Policy (2026-09-08):** The physical execution target is always x86. macOS 27 ARM64e builds execute on top of a macOS-dedicated JIT/HAL compatibility layer hosted within the x86 EFI environment. WSL2 serves as an offline development environment; host-OS QEMU and ARM Macs are not runtime execution prerequisites. Ownership of physical memory, exceptions, and hardware devices following EFI transition must be maintained by this compatibility layer.
- **Product Identity:** The official brand is **NextCore**. Support for macOS 27 GoldenGate, AMD64↔Apple Silicon HAL translation, and accelerated Metal graphics remain foundational milestones. External OpenCore origins, file compatibility layouts, and legacy test identifiers retain their original technical names.
- **D1 (Identity):** Codified — Clean-room definition, non-goals, and architectural rationale established.
- **D2/D3/D4:** Codified — 5-stage boot flow, iBoot role replacement matrix, and OpenCore idea inheritance boundaries defined.
- **D5–D8:** Codified — Internal handoff abstractions, public XNU ABI adapters, dynamic version discovery, and clean-room knowledge transfer rules defined.
- **D9–D12:** Objectives agreed — Instruction Set Emulation (ISE), GPU Virtualization & Abstraction Layer, Hardware Abstraction Layer (HAL), and Apple Silicon Sandbox (APLS) integration.
- **D13/D14 (Picker & Visual Identity):** Codified — Unified NextCore branding and standalone UEFI Boot Services graphical boot picker implemented and validated in Q35/TCG OVMF.

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

1. **Fulfills the functional role of iBoot using clean-room methods:** NextCore provides external interfaces required by macOS post-firmware (DeviceTree representations, physical memory maps, boot arguments, kext catalogs, and handoff structures) without utilizing Apple proprietary binaries, decryption keys, signature blobs, or internal symbols. *Functional equivalence through independent implementation.*
2. **Inherits architectural principles from OpenCore:** Employs a declarative, `config.plist`-driven configuration model, directory layout compatibility with `EFI/OC/`, and interface compatibility across ACPI, DeviceProperties, boot-args, and kext registries. Source code dependency remains strictly zero.

**Execution Scope:** The bootloader core runs under UEFI firmware. Sustained execution post-`ExitBootServices()` relies on companion HAL, JIT, and driver virtualization layers (D9–D11). An individual EFI binary does not presume indefinite ownership of all hardware interrupts without these supporting subsystems.

Written in Rust, NextCore delegates cryptographic trust decisions (e.g. Bootability Manifest, secure boot signatures) to platform policy. It is not an exploit payload or signature bypass utility.

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
- C codebase dependencies (implemented 100% in clean-room Rust).
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

#### D5-B. Abstract Representation & Wire Encoders
NextCore maintains an internal strongly-typed representation of physical memory maps, kernel positioning, video descriptors, and DeviceTree nodes, translating these to external wire formats via dedicated adapters prior to kernel invocation. Host pointers and data structures are never cast directly into guest memory.

### D6. Version Discovery Policy

NextCore dynamically detects available macOS installations from storage media rather than hardcoding static OS version lists. The configuration wizard reflects verified media identifiers detected at runtime.

### D7. DeviceTree Generation Boundaries

The internal DeviceTree model represents a platform-agnostic key-value hierarchy based on IEEE 1275, devicetree.org specifications, and ACPI/SMBIOS inputs. Serialized flattened trees provided to XNU are generated by clean-room encoders conforming to open ABI requirements without copying proprietary internal structures.

### D8. Clean-Room Knowledge Transfer Rules

Knowledge derived from isolated analysis is restricted to single-sentence natural-language functional requirements (e.g. "The kernel requires contiguous physical page tables below 4GB"). Code snippets, struct layouts, offsets, and magic numbers must never cross into public design documentation or code.

### D9. Instruction Set Emulation (ISE)

- **Objective:** Enable execution of missing CPU instruction sets (AVX, AVX2, FMA, SSE4.1/4.2, XSAVE, POPCNT) on older x86 processors (such as MacPro1,1 and MacPro5,1).
- **Execution Architecture:** Sustained emulation following boot handoff requires dedicated hypervisor or kernel exception trapping. Traps must distinguish `#UD` (invalid opcode) from `#GP` (general protection faults), decoding instruction lengths and register contexts cleanly.
- **Implementation Status:** `nextcore-ise` provides pure-function instruction decoders and register models. Full bare-metal IDT/exception routing requires companion hypervisor layers.

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
