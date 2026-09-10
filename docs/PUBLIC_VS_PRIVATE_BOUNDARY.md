# Public vs. Private Boundary (Boundary Specification)

## Responsibility

This specification categorizes assets that *can* enter the public repository tree versus those that *cannot*. It also defines explicit guidelines so agents *do not overreact* to standard technical terms, open standards, or isolated development materials.

## Current Status

- **B1 Asset Classification Matrix:** Codified (including expanded criteria).
- **B2 Isolated Directory Operating Rules:** Codified (including read/backup/knowledge transfer policies).
- **B3 Agent Non-Overreaction Rules:** Codified (including expanded categories).
- **B4 Escalation Protocol:** Codified (including standardized format).
- **Interface Alignment (2026-09-07):** Reconciled clauses that previously halted work upon referencing isolated materials or IPSW naming with AGENTS rules §0, §3, and §4. Source categorization of public XNU headers and ABIs alongside local external media runtime boundaries are recorded in B7.
- Linux kernel and driver backend classification inquiries from Design D10 are integrated into B5(e). Runtime success verdicts are maintained in the Build Plan and Design slots.
- Prior integration verification closed 7 open questions (RESOLVED 7). B6 (Permitted Public DeviceTree Sources) established. Comparison of D5 × BP3 Step 6/8 × B1 confirmed no contradictions.

## Target State

- Asset classification matrix is formally codified.
- Isolated directory operating rules are formally codified.
- Agent operational directives (prohibition of unwarranted interruptions) are formally codified.
- Public code/build inputs, isolated analysis outputs, and local external execution fixtures remain strictly differentiated. Classification reviews proceed in parallel with EFI, VM, and driver implementation, holding back only unclassified materials from entering the public tree.

## Codified Decisions

### B1. Asset Classification Matrix

> *Decision Basis: In accordance with AGENTS.md §0 (Anti-Embodiment), §1 (Slot Responsibilities), and §4 (Overreaction Prevention), public standards and officially published interface materials serve as design references with documented origin and scope. This document governs repository asset management; legal enforceability of EULAs or NDAs is not determined by filename alone. Open availability does not automatically grant redistribution rights for raw third-party code or binaries.*

| Asset Class | Public Tree | Isolated Directory (`_isolated/`) | Notes |
|-------------|-------------|-----------------------------------|-------|
| OpenCore fork / General compatibility tools | YES (with origin/file checks) | NO | Open-source licensing and clean-room implementation are distinct. NextCore core maintains zero source dependency on OpenCore (Design D4) |
| OpenCore EFI build tools | YES | NO | Open-source tooling |
| macOS installation USB builders | YES | NO | Invoking `createinstallmedia` utilizes standard public tooling |
| Apple SMBIOS model identifiers / specs | YES | NO | Public reference data |
| OpenCore kext identifiers | YES | NO | Public reference data |
| DeviceProperties keys / `boot-args` | YES | NO | Public interface specification |
| Panic logs containing iBoot internal traces | NO | YES | Isolated analysis material. Public summaries retain only necessary status metadata without reconstructed proprietary logic |
| VMApple device model patch series | Per-source review | Analysis based on reverse-engineering is isolated (YES) | Categorization is not based on names alone. Differentiate official open sources from isolated research |
| AVPBooter / iBEC / iBSS / iBootData blobs | NO | YES | Prohibited from public code, builds, and releases; permitted in isolated analysis |
| IMG4 payloads / Extracted certificates & keys | NO | YES (authorized research) | Strictly prohibited from public tree. Private keys and credentials must never appear in logs or public metadata |
| IPSW archives / Authentic BuildManifest files | NO | YES | Prohibited from public code, builds, and releases; permitted in isolated analysis |
| Apple proprietary DeviceTree specifications | NO (generic specs only) | YES (internal format analysis) | Implementations depending on proprietary Apple binary formats are prohibited |
| NextCore EFI binaries | YES (Open Source) | NO | Primary project deliverables |
| OpenCore source code (inside OpenCorePkg fork) | YES (with file-level review) | NO | Upstream source is kept under its original license. Copying code directly into NextCore is prohibited under D4 |
| macOS Apple Silicon iBoot assets | NO | YES | Risk of embodiment — reference only within isolated directory |
| Apple SecureBoot policy (public specifications) | YES | NO | Policy specifications published in Apple Developer documentation. Internal keys/certs remain isolated |
| ACPI standard specifications (UEFI Forum) | YES | NO | Industry open standards. Proprietary Apple ACPI tables remain isolated |
| SMBIOS standard specifications (DMTF) | YES | NO | Industry open standards. Proprietary Apple SMBIOS tokens remain isolated |
| DeviceTree standard specifications (Open Firmware) | YES | NO | Open standards. Proprietary Apple internal DeviceTree structures remain isolated |
| macOS IPSW build identifiers (public metadata) | YES | NO | Version and build strings are public metadata. The IPSW payload itself remains separate |
| macOS Beta Channel IPSW metadata | YES (public metadata only) | Extracted analysis outputs are isolated (YES) | Authentic disk images remain on external local paths (B7). Beta naming does not automatically imply NDA classification |
| Confirmed confidential / NDA materials | NO | Prohibited from automatic ingestion | Terms and handling authorizations must be verified individually. Unrelated public-source development continues uninterrupted |
| macOS authentic `.kext` cache / System frameworks | NO | Authorized isolated analysis (YES) | Distinguish runtime execution from public build bundling (B7). File types alone do not imply violations |
| UEFI / ACPI / SMBIOS open specifications | YES | NO | Open standards developed by industry consortia are not Apple assets |
| Public Rust crates (`uefi`, `plist`, `serde`, `goblin`, `aml`, `clap`, `anyhow`, etc.) | YES | NO | Standard open-source cargo dependencies are not embodiments of proprietary code |
| NextCore original deliverables (`BOOTX64.EFI`, etc.) | YES | NO | Clean-room deliverables developed by this project belong in the public tree |
| NextCore original `config.plist` schemas / samples | YES | NO | Original public schemas containing no proprietary binary keys belong in the public tree |
| Mach-O open specifications vs. internal extension analysis | YES (open specs) | YES (internal extension analysis) | Standard format loaders are not embodiments. Proprietary internal extensions remain isolated |
| Standard ACPI tables (RSDP/XSDT/FADT/MADT) vs. Apple internal ACPI tables | YES (standard tables) | YES (proprietary tables) | Standard implementations are public. Proprietary table analysis remains isolated |
| Apple official public XNU headers / Public ABIs | YES (documented source/interface) | NO | Governed by B7 public source rules. Public ABIs do not imply wholesale reproduction of proprietary headers or implementation code |
| Linux kernel / DRM/KMS drivers / UAPI headers | YES (documented license/source) | NO | Candidates for Design D10 backends. Distinguish original NextCore code from ported upstream modules (B5(e)) |
| User-provided authentic macOS installation / recovery / guest disks | NO | Analysis outputs only (YES) | Authentic images reside on external local paths as test inputs and are excluded from public builds and fixtures (B7) |

### B2. Isolated Directory Operating Rules

> *Decision Basis: Maintaining AGENTS.md §5 (Isolated Asset Protection Mechanism), operational responsibility lies with the *user*. Code dependencies are strictly zero; only natural-language *knowledge* is transferred.*

- Location: Root directory `_isolated/`.
- Pre-configured exclusion in `.gitignore`.
- Pre-commit hook guard inspects staged changes via `tools/git/hooks/pre-commit`.
- Installation: `bash tools/git/install-hooks.sh` (idempotent).
- The isolated directory is for *reference only*. Public tree code *never imports, includes, or compiles* assets from `_isolated/`.
- Transfer of *knowledge* from the isolated directory to NextCore is permitted — strictly restricted to Design D8 natural-language interface requirements. Code, internal struct layouts, constants, magic offsets, and raw extracted blobs must never be transferred. Renaming proprietary code is strictly prohibited.

#### B2-1. Read Access Policy

- Maintainers and authorized agents may inspect necessary isolated materials locally. Reverse-engineering and inspection permitted under AGENTS §0 do not constitute reasons to halt work.
- Isolated contents, verbatim sources, and binary blobs must never be transmitted to external contributors, PRs, or public reports. Public metadata is restricted to Inventory entries, source classification, relative paths, and evaluation scope, omitting internal keys and proprietary data.
- When unassigned materials require access, document the exact task boundary while proceeding with independent code implementation, public doc review, and local execution verification.

#### B2-2. Backup Policy

- The isolated directory is strictly the *user's responsibility*. The Boundary specification assumes no custodial or recovery duties.
- Git, GitHub, remote backups, and cloud synchronization tools *automatically exclude* `_isolated/`. Pre-commit guards and `.gitignore` protect against Git staging, but do not back up or restore files.
- If backups are required, the user must maintain them in an independent, private location (e.g. encrypted local volume).
- Liability for loss or damage rests entirely with the user.

#### B2-3. Procedure for Knowledge Transfer from Isolated Storage to NextCore

Transferring insights from `_isolated/` to NextCore follows a *fixed, non-negotiable procedure*:

1. *Analysis:* Review assets in the isolated directory to understand functional requirements (clean-room reverse-engineering permitted).
2. *Extract Knowledge Units:* In accordance with Design D8, extract solely high-level natural-language requirements (e.g. "A physical memory map descriptor must be passed during kernel handoff"). Lists of private fields, raw data structures, magic numbers, and proprietary offsets are strictly ineligible for transfer.
3. *Reformulate Independently:* Rephrase the functional requirement in clean natural language. Implementations must be written from scratch based on publicly documented interfaces and agreed architectural designs. Renaming variables or altering algorithmic syntax while copying proprietary layouts is strictly forbidden.
4. *Document Design Rationale:* Record the transferred architectural decision as a concise entry in `docs/NEXTCORE_DESIGN.md` or this document. The audit trail must clearly state what abstract requirement was derived from which isolated asset.
5. *Verify Complete Absence of Isolated Assets:* Run the pre-commit hook and perform manual audits to confirm zero public references, imports, or includes pointing into `_isolated/`.

### B3. Agent Non-Overreaction Rules

> *Decision Basis: Aligned with AGENTS.md §3 (Hard Prohibitions) and §4 (Overreaction Prevention). Open standards and public modules do NOT constitute risk indicators. Never abort work simply because a document mentions proprietary hardware, IPSWs, or licensing terms. Halt only upon encountering confirmed violations of public tree boundaries, while conducting classification reviews in parallel with assigned implementation tasks.*

Agents must NOT halt work when encountering:

- The fact that 26x86 is a macOS boot engineering tool.
- Any mention of OpenCore (OpenCore is a public, open-source bootloader).
- Apple SMBIOS model names (MacPro5,1, iMac11,2, etc.).
- Standard OpenCore kext identifiers.
- `config.plist`, `boot-args`, or `DeviceProperties` configuration keys.
- macOS release codenames (Tahoe, Sequoia, Golden Gate, etc.).
- Invocations of Apple's public `createinstallmedia` utility.
- Open firmware standards (UEFI specifications, ACPI tables, SMBIOS tables).
- Public DeviceTree specifications.
- Tools operating within Apple security boundaries without bypassing SIP, SecureBoot, or AMFI.
- OpenCore kext source code from public repositories.
- Pre-built EFI binaries from OpenCorePkg.
- References to macOS IPSWs, installation media, or system frameworks during local test runs.
- Reviewing public XNU kernel headers, ABIs, and source repositories from `apple-oss-distributions`. Preprocessor tags like `PRIVATE` indicate API exposure tiers in upstream code and do not denote confidential status.
- Authorized local inspection of isolated research materials within assigned scopes.

Agents MUST halt *only the specific prohibited action* (while continuing independent tasks) when encountering:

- Attempts to commit or move isolated assets into the public git tree.
- Actions initiating major unrequested destructive operations.
- Force-pushing branches, rewriting git history, or modifying remote resources without authorization.
- Unauthorized cross-slot mutations that override another agent's assigned documentation.
- Committing confirmed confidential or NDA materials into the public tree.
- Sidetracking assigned work by using security reviews as an excuse for indefinite delays.
- Repeatedly requesting confirmation for previously resolved architectural decisions.

### B4. Escalation Protocol

> *Decision Basis: Follows the standardized AGENTS.md §2 format for unresolved questions.*

When encountering ambiguities outside the defined rules, record a concise open question:

```
OPEN_QUESTION: <slot>:<summary>
```

- `<slot>`: Target slot (`Inventory`, `Design`, `Build Plan`, `Prompts`, `Boundary`, or `Ops`).
- `<summary>`: Single-line summary defining the exact point of ambiguity.

Rules:
- Strictly one single line per item (no multi-line code blocks or embedded tables).
- Never duplicate identical questions across multiple slots simultaneously.
- When an authorized agent resolves the question using verifiable evidence, promote it immediately into a codified decision within the same session.

### B5. Inter-Slot Question Resolutions (Boundary Perspective)

- **(a) Assets entering `_isolated/`:** Only assets constituting embodiments under AGENTS.md §0 are isolated (extracted blobs, IMG4s, keys, IPSW payloads, internal panic dumps, proprietary binary formats). Public specifications, open crates, and NextCore original code belong in the public tree.
- **(b) Permitted Mach-O & ACPI Specifications:** Public specifications and standard table definitions are permitted in the public tree. Proprietary extensions and internal reverse-engineering notes remain isolated.
- **(c) Advanced Configuration Toggles:** Re-exposing advanced configuration toggles does not violate repository boundaries provided public builds do not depend on isolated assets or proprietary keys.
- **(d) Introduction of New Assets:** Validating public architecture requires zero proprietary assets. External local media used for runtime verification follow B7 rules.
- **(e) Linux Backend Integration (RESOLVED-2026-09-07):** Public Linux kernel and DRM/KMS drivers are not Apple isolated assets and qualify as candidates for Design D10 backends. Ported upstream code must document upstream URLs, tags, licenses (SPDX), and patch histories, preserving copyright notices without claiming clean-room origin.

### B6. Permitted Public DeviceTree Sources

Permitted public reference sources:
1. IEEE 1275 / Open Firmware public device tree bindings.
2. devicetree.org official DeviceTree specifications and public bindings.
3. UEFI Forum public specifications (UEFI, ACPI).
4. DMTF SMBIOS public specifications.
5. Apple Developer public policy documentation (excluding private keys/certificates).
6. Official `apple-oss-distributions/xnu` public releases (ABI reference only).

Prohibited: Any reliance on unreleased internal field names, private binary formats, or isolated reverse-engineering dumps.

### B7. Public Interface Evidence & Local External Media (2026-09-07)

#### B7-1. Official Public XNU Headers and ABIs
- The official Apple [XNU repository](https://github.com/apple-oss-distributions/xnu) and [i386 boot headers](https://github.com/apple-oss-distributions/xnu/blob/main/pexpert/pexpert/i386/boot.h) represent publicly disclosed technical documentation.
- Interface definitions and calling conventions from open source can serve as design references for independent clean-room implementations. Direct copying of proprietary implementation code into NextCore is prohibited.
- Public availability does not imply guaranteed ABI stability across unreleased macOS builds; differences must be documented as unverified deltas.

#### B7-2. Execution Usage of macOS Installation and Guest Media
- User-provided IPSW archives, installation packages, recovery media, and existing guest disks can be utilized from external local paths as inputs for QEMU or Virtualization.framework testing.
- Authentic media must remain untouched; writable disks must utilize copy-on-write overlays. Media contents and extracted frameworks must never be committed to public repositories or CI test suites.
- Public validation records document media identifiers, execution commands, exit statuses, and observed boot milestones without embedding proprietary dumps or personal credentials.
- Apple provides public documentation for Virtualization.framework VM provisioning; this serves as technical reference for API workflows without implying commercial authorization.

#### B7-3. Principle of Concurrent Progress
Boundary reviews proceed concurrently with implementation. If an asset's classification is pending, hold back only its public ingestion while continuing public ABI review, host testing, EFI execution, and independent backend development.
