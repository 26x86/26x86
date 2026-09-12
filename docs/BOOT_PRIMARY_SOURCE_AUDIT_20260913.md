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


## Official Arm acquisition follow-up

After the first hierarchy publication, two additional official Arm documents
were downloaded, hashed and opened locally. The source index preserves their
exact identities; the PDFs remain outside the public repository.

- [Cortex-X925 r0p1 Technical Reference Manual](https://documentation-service.arm.com/static/665741bb876c8d213b78610b),
  document 102807_0001_05_en, Issue 05: A.5.15/Table A-313, PDF pages 419-421.
  This identifies the core's implemented MMFR1 values. It confirms that
  CMOW=0 and TIDCP1=0 omit their named controls; AFP=1 adds the corresponding
  FPCR controls; nTLBPA=1 excludes noncoherent physical intermediate walk
  caches. This edition describes ETS=1 as no enhanced translation
  synchronization. A numeric one must not be interpreted as feature support
  without its field definition. These are X925-specific values, not an
  authorized NextCore feature word or a complete generic value table.
- [Architecture Registers Release Note](https://documentation-service.arm.com/static/68da4ea586b96e39e38c215c?token=),
  document 111109_2025-09_01_en, Issue 01: the change list records revisions
  to CMOW and ECBHB descriptions. It establishes that wording changed, not
  the full replacement semantics. Its future-extension content has an
  explicit Alpha-quality qualification.

The current generic DDI0601 MMFR1 table remains unacquired. The official
2024 core manual does not become the 2026 register specification. The next
implementation contract must connect each chosen software feature value to
its actual optional-control acceptance or rejection. Positive synchronization
or branch-history guarantees require separate evidence. No MMFR1 instruction
support, original-input progress, or readiness change follows from acquisition.

## Target identity cross-check

A bounded read-only load-command audit identifies the target kernel member's
source version as `13432.1.9`. The pinned public Apple import identifies itself
as `xnu-12377.121.6`. These different version identities do not prove ABI
incompatibility, but they prevent treating that public source as a verified
target-source binding. The [sanitized identity receipt](evidence/target-entry-audit-20260913.json)
records input preservation and scope; UUID values and original coordinates
remain isolated.

Existing staging and r29 metadata agree on the outer LC_UNIXTHREAD entry;
the member entry differs. The selected entry is inside a file-backed executable
boot segment. These relations corroborate the current entry selection, not its
exact register or service contract. They supply no basis for replacing the
entry with an image base or a different member PC. Target SPTM applicability
remains unverified.

OPEN_QUESTION: Build Plan: Bind the exact selected entry to matching target symbols or a UUID-matched KDK/source identity before changing initial state; an approximate symbol or older public startup path is insufficient.

## Clean CI confirmation

The complete immutable source `3d3a434dfc9f84dcc1c34a2257f8cf7ceaafd99c`
passed all six workspace/EFI jobs in
[run 34713439375](https://github.com/26x86/26x86/actions/runs/34713439375)
and the separate EFI Sandbox. Its fresh hierarchy run passes 306 Arm TCG cases,
258 direct joins, 34 native tests in each mode, 104 reference tests, and 961 EFI
cases with source preservation. Five downloaded original CI receipts and their
hashes are retained under
`nextcore/artifacts/physical-integration-20260912/hierarchy-ci-20260913`.
This fresh successful run supplements the separately qualified local r6 evidence;
the original local preservation failure remains recorded. No physical or macOS
boot claim follows from the CI result.
