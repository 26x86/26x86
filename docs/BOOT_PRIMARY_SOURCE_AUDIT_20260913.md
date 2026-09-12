# Public boot-source audit — 2026-09-13

## Current Status

This audit publishes source metadata and paraphrases only. No downloaded source bodies, PDFs, private images, or original execution coordinates are included. The [source index](evidence/boot-primary-sources-20260913.json) records acquisition status, immutable revisions and hashes. It supplements the accepted Build Plan; it does not revise its contracts.

The hierarchy increment has independent qualification of 34 provider tests in each of three modes, 104 reference tests, 306 Arm TCG observations with 258 direct comparison joins, and 961 authored EFI cases. These are separate coverage dimensions, not an additive boot score. They do not establish physical hardware or macOS desktop operation.

## Target State

Every externally visible boot claim should identify an exact public contract, the implementation that consumes it, and the observed target result. Missing documents, unspecified target ABI details and untested physical transitions remain explicit. The practical target is guest-owned screen output sustained through platform initialization and firmware transition, followed by verified storage and userspace startup.

## Source identity and acquisition

Apple sources below are pinned to `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`, release `xnu-12377.121.6`, dated 2026-06-17. This public release is **not identified as the target private build**. Dates and release identity do not establish ABI equivalence.

TianoCore `edk2-stable202502` resolves to `fbe0805b2091393406952e84724188f8c1941837`, dated 2025-02-21. Both relevant headers were fetched again by full commit and matched the previously downloaded tag bytes exactly. The JSON records their SHA-256 values.

The [UEFI Forum version index](https://uefi.org/specifications) was successfully opened and identifies UEFI 2.11 as released in December 2024. Attempts to read chapters 4, 7, 12 and the PDF did not yield the normative bodies; the relevant requests returned access errors. TianoCore headers below are upstream implementation contracts, not a substitute claim that those specification chapters were read.

Arm's 2026.06 MMFR1 description was opened on an [Arm-authored community mirror](https://arm.jonpalmisc.com/latest_sysreg/AArch64-id_aa64mmfr1_el1). It is not an official-host acquisition. The latest official DDI0601 endpoint did not yield its body. Verified hierarchy pseudocode remains **DDI0596 ID121321, December 2021**, local PDF SHA-256 `756449b122fa43ff55d81be5e889451bc8c7ba8576ad4a877b91c77b8675e349`; its original download URL is unknown. Physical pages 3051, 3071 and 3076–3077 contain S1HasPermissionsFault, S1ApplyTablePerms and S1Walk. Modern-edition equivalence remains unverified. A separately cached file named arm-ddi0487.pdf was identified as the I.a known-issues supplement, not the architecture manual, and is not used as a substitute.

## Source-to-implementation gap table

| Verified public contract | Current implementation/evidence | Missing acceptance boundary |
|---|---|---|
| [Boot_Video and boot_args](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h#L24-L64) define LP64 video and memory inputs. | Core owns a checked framebuffer reservation and encodes dimensions, stride and base. | Prove the target consumes that layout and its own writes reach the intended screen. Serialization alone is insufficient. |
| [Non-SPTM cold entry](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/start.s#L461-L490) uses x0 as boot arguments. [SPTM entry](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/sptm/start_sptm.s#L34-L68) uses a reason value and separate argument pointers. | Entry provenance and diagnostic profiles are explicit. | Bind the exact target entry to its register contract. Neither a copied load address nor missing SPTM manifest roles proves the ABI. |
| [SPTM cold path](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/sptm/start_sptm.s#L136-L174) has a fixup-completion transaction before arm_init. | Software instruction and PAC tests cover bounded operations. | If applicable to the target, implement the actual service transaction and its state changes. Do not invent unavailable external argument structures. |
| [arm_init](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm/arm_init.c#L572) invokes arm_vm_init, later platform initialization and [machine_startup](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm/arm_init.c#L690). | Immutable diagnostics validate a fixed translation context. Hierarchy now has independent qualification. | Guest-owned mapping changes and required invalidation must be implemented under a separate transaction contract. Static-table success is not that transition. |
| [PE_init_platform](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/arm/pe_init.c#L435-L472) consumes video/DT and initializes platform state. | Boot arguments and selected diagnostic platform services exist; normal startup retains NOT_READY. | Verify target DT, interrupts and platform callbacks, then root storage and IOKit startup. |
| [initialize_screen](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/console/video_console.c#L2797-L2881) establishes the kernel framebuffer mapping. | EFI presents owned guest pixels after bounded execution and can read them back. | Demonstrate XNU's own virtual mapping and first pixel writes, plus sustained display. A post-run host blit is not evidence that this kernel path ran. |
| [GOP mode contract](https://github.com/tianocore/edk2/blob/fbe0805b2091393406952e84724188f8c1941837/MdePkg/Include/Protocol/GraphicsOutput.h#L26-L86) distinguishes pixel formats, stride and PixelBltOnly; [mode state](https://github.com/tianocore/edk2/blob/fbe0805b2091393406952e84724188f8c1941837/MdePkg/Include/Protocol/GraphicsOutput.h#L239-L251) describes framebuffer extent. | Diagnostic GOP conversion/readback is exercised on OVMF. | Verify the real computer's mode, physical aperture, memory attributes and persistent access. PixelBltOnly cannot be treated as a linear framebuffer. |
| [ExitBootServices declaration](https://github.com/tianocore/edk2/blob/fbe0805b2091393406952e84724188f8c1941837/MdePkg/Include/Uefi/UefiSpec.h#L1023-L1040) terminates boot services using the current map key. | Current diagnostic presentation retains firmware services. | Define final memory ownership and post-transition display/I/O services. Test stale-map-key failure and physical transition without continuing to rely on firmware GOP calls. |

Anchors above use the actual downloaded file line numbers. No binary offsets were inferred from source lines.

## Prioritized open questions

OPEN_QUESTION: Build Plan: Bind the target entry and selected public ABI using metadata and a private-only comparison before changing initial registers. Public source alternatives alone do not resolve it.

OPEN_QUESTION: Build Plan: Acquire and compare the modern Arm hierarchy definition against the explicitly identified 2021 contract; do not silently relabel editions or use a known-issues PDF as the manual.

OPEN_QUESTION: Build Plan: Design and verify mutable guest translation controls, table writes and TLBI ordering after the fixed-context hierarchy gate. This audit does not authorize broader control admission.

OPEN_QUESTION: Build Plan: Prove the causal chain from target kernel framebuffer mapping to guest pixel writes, presentation and persistence across firmware transition. OVMF and actual Arm TCG remain distinct from physical-host evidence.

OPEN_QUESTION: Design: Obtain the UEFI 2.11 normative lifecycle/GOP chapter bodies and validate the exact post-ExitBootServices ownership plan against them. Successful version-index retrieval is not normative-body verification.

OPEN_QUESTION: Build Plan: Establish ordered target storage, root mount, launchd, WindowServer and input evidence before any desktop claim. Conditional SPTM support is required only once target applicability is established.

## Classification

**Confirmed:** the pinned public interfaces, downloaded source hashes, documented acquisition failures, bounded hierarchy qualification and present diagnostic display behavior. **Inferred:** the priority of future gates from those dependencies; this is not a prediction of the next original instruction. **Unknown:** exact target ABI equivalence, modern hierarchy equivalence, physical post-firmware display behavior and macOS userspace completion. Normal readiness is unchanged.
