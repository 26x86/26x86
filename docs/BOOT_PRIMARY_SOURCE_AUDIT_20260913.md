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


## Optional translation controls and generic MMFR1 evidence

The official [Cortex-A55 TRM](https://documentation-service.arm.com/static/5e7e1405b471823cb9de57ae), `100442_0100_00_en`, B2.90 Figure B2-78, PDF page 412, confirms TCR_EL1 HA[39], HD[40], HPD0[41] and HPD1[42]. The same page defines the hardware Access Flag and dirty-update controls. Its SHA-256 is `b48da6cc513e4d22ab67dcbb062097364099c46fe2b4e208dbe1ecf637e73a53`. These positions bind the narrow control audit; the A55's own feature values are not software-profile values.

An isolated archive of ISE `778473fd9c43d7ba3a4721852f838be996fed45d` reproduced successful write and unchanged readback of each of those four set bits with translation disabled and enabled: eight C public API cases and eight Rust register-bank cases. This is evidence that the old generic paths stored and reported unsupported optional state, rather than ignoring the writes as zero. It is a direct API experiment, not a translated-instruction or memory-effect test. ISE 3a0ed3dd39f78fc3c55415f898d7faa8f34699c2 now rejects all fifteen nonzero combinations before mutation. Final independent old/current runs use identical test sources: 160 C assertions pass for the corrected runtime, and the Rust register-bank and direct-MMU suites each pass 102 tests (overlapping suites, not 204 unique tests). Rejection preserves CPU/register observations, translation configuration and warm caches. Separate service/reference suites pass 44/115 tests. The UEFI target compiles; no new EFI execution is claimed by that check. It is a bounded unsupported-input policy, not a claim to emulate architectural RES0 write-ignore behavior. Immutable and dynamic profile admission already rejected these bits. No final MMFR1 word or bootstrap progress is established by this correction.

Two additional official acquisitions narrow the remaining feature-policy questions:

- The [2025-09 BSD machine-readable register distribution](https://developer.arm.com/-/cdn-downloads/permalink/Exploration-Tools-OS-Machine-Readable-Data/AARCHMRS_BSD/AARCHMRS_OPENSOURCE_A_profile_FAT-2025-09_ASL0.tar.gz), `2025-09_rel`, build 415, schema 2.7.1, identifies AFP at [47:44], nTLBPA at [51:48] and ECBHB at [63:60]. Each enumerates 0000 and 0001, but its meaning and description values are null. This verifies field positions and listed encodings; it does not supply normative prose or all feature dependencies.
- The [A-profile known-issues supplement L.b Issue 02](https://documentation-service.arm.com/static/6894bc07e7f7ce6150e88fca), `102105_L.b_02_en`, dated 4 August 2025, page 82, corrects the generic ECBHB table in D24.2.83. Zero leaves restrictions on branch-history speculation around exceptions undisclosed; one reports that restrictions are imposed. Zero therefore does not assert that restrictions are absent and does not advertise a mitigation. This is a generic correction, not the complete system-register manual.

The JSON index records exact archive/PDF hashes and acquisition scope. Neither the downloaded bodies nor extracted register records are redistributed here. Generic AFP zero-value prose and the current DDI0601 MMFR1 table remain unacquired. The follow-up below independently binds nTLBPA zero to an official generic erratum. The newer machine-readable metadata does not upgrade the older hierarchy pseudocode's edition.

OPEN_QUESTION: Build Plan: With the four-bit rejection tests complete, audit remaining generic SCTLR optional controls and bind every proposed MMFR1 field to its actual behavior and admitted control state. EL1 with inactive HCR/SCR alone does not validate directly injected CPU state. Do not infer a complete Arm revision or a final all-zero feature policy from access success, enum availability, or the next diagnostic boundary.


The official [H.a known-issues supplement Issue 06](https://documentation-service.arm.com/static/62f4d062e95b0a633aff7ad7), `102105_H.a_06_en`, section 2.59 C18798, PDF pages 48–49, clarifies the generic nTLBPA table. Zero allows the possibility of noncoherent physical translation caches; it does not require such a cache. One excludes that cache class. The definition concerns previously valid translation entries and the relevant completed invalidation boundary. This is an acquired H.a correction, not a claim that the current complete register manual was obtained. PDF SHA-256: `66bebb12577684ff0b2a6eefe6d5b296d470a95d0afcd42993dfc86d3aa22cca`.

The already acquired official 2025-09 register schema also provides conditional field rules even where prose is omitted. In SCTLR_EL1, TIDCP[63], EPAN[57] and CMOW[32] are conditional on FEAT_TIDCP1, FEAT_PAN3 and FEAT_CMOW respectively, with RES0 otherwise. **SPAN[23] differs:** it is conditional on FEAT_PAN and otherwise RES1. FPCR NEP[2], AH[1] and FIZ[0] are conditional on FEAT_AFP and otherwise RES0. Consequently, a future no-PAN policy must not blindly treat every named optional bit as required zero. These are source constraints for the next admission audit, not an implementation or a final feature word. The completed four-bit TCR results above are unchanged.


OPEN_QUESTION: Build Plan: Consider binding a future exact MMFR1 read to a validated immutable control tuple, checked live on every generated-code execution including cache hits. This is a bounded alternative to changing unrelated generic reset/write behavior. The ordinary CPU-state validity check and EL1/HCR/SCR gate alone do not establish that tuple; its precise admission and negative tests require a separate contract.
