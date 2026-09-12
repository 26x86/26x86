# AGENTS.md — NextCore Collaboration and Operational Principles

This document is the normative specification that all AI and human agents must read prior to beginning work in this repository. It defines decision boundaries, architectural slots, and hard prohibitions to ensure clean coordination across multiple contributors.

## 0. Foundational Principles (Non-Negotiable)

- **Mandatory Documentation Policy: FORCE English Only.**
  All documentation, technical design specifications, architectural records, code comments, commit messages, CLI user-facing messages, and pull request descriptions must be written strictly in **English**. No bilingual, Korean-only, or non-English documentation is permitted anywhere in the repository.
- **No Embodiment of Apple Proprietary Assets in the Public Tree.**
  Embodiment refers to decompiling or reverse-engineering Apple internal code and porting it into this repository, storing raw blobs, certificates, or images extracted from IPSWs, or duplicating Apple internal structures to mimic behavior.
- **Clean-Room Engineering and Isolated Analysis.**
  Reverse-engineering for interoperability is permitted strictly within the root `_isolated/` directory. Files in `_isolated/` must never be staged or committed to Git. The isolated directory is for reference only; public code must never import, include, or link against it.
- **Functional Equivalence Without Code Duplication.**
  NextCore performs functions equivalent to iBoot, but through completely clean-room, independently authored implementations. It shares no code dependencies and uses no Apple internal naming. While it inherits the architectural concept of OpenCore (declarative plist-driven configuration, filesystem placement conventions), it maintains zero source code dependency on OpenCore.
- **EFI Boot Architecture.**
  macOS must boot within standard UEFI environments. NextCore replaces early pre-boot functions with an open, clean-room implementation.

## 1. Decision Boundaries (Slots)

To prevent uncoordinated cross-cutting modifications, work is divided into explicit slots. Each slot owns a designated starting specification; other slots may inspect but not directly mutate specifications outside their domain without explicit delegation:

| Slot | Canonical Specification | Primary Responsibility |
|------|-------------------------|------------------------|
| **Design** | `docs/NEXTCORE_DESIGN.md` | *What* and *Why* — Objectives, EFI boot flow, iBoot role replacement, OpenCore inheritance boundaries |
| **Build Plan** | `docs/NEXTCORE_BUILD_PLAN.md` | *How* — Rust workspace layout, phased implementation roadmap, validation gates, dependency matrices |
| **User Flow (Prompts)** | `docs/NEXTCORE_PROMPTS.md` | Wizard UX flow, user choices, diagnostics, English-only copy |
| **Boundary** | `docs/PUBLIC_VS_PRIVATE_BOUNDARY.md` | Public vs. private asset categorization, isolated folder rules, safe-harbor standards |
| **Inventory** | `docs/ISOLATED_INVENTORY.md` | Audit metadata of materials in `_isolated/` (metadata only; no proprietary content) |
| **Operations** | `AGENTS.md` (this file) | Agent coordination, slot protocols, prohibitions, workflow rules |

## 2. Multi-Agent Collaboration Workflow

- Multiple agents may operate concurrently within a session.
- Each agent must work by extending their assigned slot specification. Do not undertake tasks lacking a defined canonical document.
- Specifications must remain self-contained. Do not leave ambiguous placeholders such as "TBD". Unresolved architectural questions must be recorded as single-line entries in an `OPEN_QUESTION` section.
- If an agent determines that an adjustment is required in another slot, they must not modify the foreign specification directly; instead, record an entry formatted as:
  `OPEN_QUESTION: <slot>:<summary>`
- Code follows documentation: code is authored only after underlying specifications are agreed upon and recorded in files.

## 3. Hard Prohibitions

The following actions are strictly prohibited under all circumstances:

- Staging or committing any file from the `_isolated/` directory into Git. Pre-commit hooks and `.gitignore` enforce this boundary; any attempt to circumvent them must be halted immediately.
- Force-pushing to the public repository or rewriting Git history.
- Initiating unauthorized destructive tasks under the guise of security reviews. Security audits proceed in *parallel* with assigned engineering tasks and must never be used as an excuse to indefinitely sidetrack delivery.
- Directly editing specifications owned by other slots without formal delegation. Escalate via `OPEN_QUESTION`.
- Introducing non-English text into documentation, source comments, or user-facing messages.

## 4. Overreaction Prevention (Do Not Halt on Open Standards)

The following items are standard engineering concepts and do NOT constitute security risks. Agents must not halt work when encountering:

- The fact that 26x86 / NextCore is a macOS boot tool.
- Mentions of OpenCore (OpenCore is an open-source, public bootloader).
- Apple SMBIOS model names (MacPro5,1, MacBookPro11,1, iMac11,2, etc.).
- OpenCore kext identifiers (Lilu, WhateverGreen, VirtualSMC, RestrictEvents, etc.).
- `config.plist`, `boot-args`, or `DeviceProperties` configuration keys.
- Invocation of Apple's public `createinstallmedia` utility.
- Open standards (UEFI, ACPI, SMBIOS, IEEE 1275 DeviceTree).
- Public XNU kernel headers and ABIs from `apple-oss-distributions`.

## 5. Isolated Asset Protection

- The isolated directory resides at repository root: `_isolated/`.
- Pre-configured exclusion exists in `.gitignore` (`/_isolated/`).
- The pre-commit hook (`tools/git/hooks/pre-commit`) scans the Git staging index and rejects commits containing `_isolated/` paths.
- Installation: `bash tools/git/install-hooks.sh` (idempotent).

## 6. Documentation Standards

- All documents must declare *Current Status* and *Target State*.
- Every decision item must clearly distinguish codified decisions from open questions.
- Unresolved items are logged strictly as single-line `OPEN_QUESTION` entries.
- All documentation is maintained in **English only**.
- Every website deployment must publish `prebuiltefi.zip` with the site. Build it
  from an explicit immutable public source revision and verify the archive,
  executable types, file hashes and source provenance before deployment. Missing
  or invalid archives must block deployment. Keep normal firmware and diagnostic
  binaries clearly identified, and state the actual boot-validation boundary.

## 7. Git Commit Disciplines

- Changes belonging to a specific slot should be committed in focused, atomic commits.
- Commit messages must concisely state *what* changed and *why* in English.
- Remote push operations require explicit operator authorization or automated CI pipeline triggers.
