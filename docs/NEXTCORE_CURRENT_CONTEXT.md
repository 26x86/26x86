# NextCore Current Context and Resumption Standards

Updated: 2026-09-09. The latest BP summaries take precedence over legacy historical logs. This document provides an objective baseline summary so future agents and contributors can resume development without overstating completion states. Detailed specifications reside in `docs/NEXTCORE_BUILD_PLAN.md`, and verification records are maintained in `nextcore/VALIDATION.md`.

## BP35 Integration and Physical Boot Work

PR #17 adds explicit deep diagnostics with Core bab7ac4, EFI 03a376d and Tool
8ea73c8. Historical authored firmware gates reached the selected 16384 budget;
the historical original-input diagnostic stopped after 5311 retired instructions
at UBFM. Those receipts do not establish normal startup or macOS boot.

The 2026-09-12 integration preserves those historical results and connects ISE
792abc1 (UBFM, undefined-syndrome correction, extended-register arithmetic and
conditional selection) with EFI 0d4303e. Authored native/EFI execution and production picker recovery
pass; receipts are in `nextcore/artifacts/physical-integration-20260912`.
The local original-prefix diagnostic retires 5350 instructions before a scalar register-offset load,
with normal startup prerequisites still incomplete. The physical target is Samsung 750XHD with Intel
Core Ultra 7 255U and Intel Graphics 8086:7D41. Acceptance requires external-media
installation and an interactive macOS 27 desktop after reboot. Optional firmware
presentation failures must degrade gracefully. Graphics acceleration is deferred.
SPTM services, complete platform providers and physical OS boot remain unverified.

## BP34 Development Status

BP33 was merged into upstream main (`9ef0e262`) via PR #15 following validation across 29 CI checks and clean recursive cloning audits. BP34 integrates merged ISE updates (`PR #7 / bcf1ca9`) and EFI updates (`PR #8 / cfc8af9`). The 7-submodule architecture (Core, EFI, Tool, ISE, GPU, HAL, APLS) is preserved.

ISE implements one-way MMU enablement, distinct architectural vs. effective machine states, and canonical TLBI invalidation. Authored test fixtures in `NXDYN` execute within x86 EFI, activating the MMU and performing instruction fetches, loads, and stores across remapped physical pages with strict fault verification. Verification covers 58 fetch/data and 40 control events across entire RAM spaces and immutable page tables, alongside 30 reader mutation rejection tests.
Comparison suites against independent Arm fixtures and native C/Rust reference models pass cleanly. HVC instructions in successful fixtures remain unmodified and are isolated at unsupported instruction boundaries. Hardware TLB refill and authentic HVC dispatch are not claimed.

Verification passes across workspace unit tests (502 tests), Python suites (149 tests), GUI tests (25 tests), reference suites (98 tests), memory services (44 tests), and 200 real EFI execution tests. Full session artifacts are preserved under `nextcore/artifacts/integration-bp34-20260909`.

An independent 16,384-budget execution run under BP35 reached instruction 5,311 at the UBFM/LSL boundary. Instruction coordinates remain private, and BP36 UBFM handling and Undefined ESR instruction length fixes are undergoing independent verification. Frozen BP34 sources remain untouched. macOS 27 handoff, live SPTM services, bare-metal EFI GPU drivers, and guest Metal acceleration remain active engineering milestones.

## BP33 Development Status

BP32 was merged via PR #14 (`1b86a2e`) with full CI qualification. BP33 final integration links Core (`147f4c4`), EFI (`7e7a08b`), and Tool (`4bb09da`). Stage-1 memory translation validates execution across isolated physical memory pages, consuming authored DeviceTree structures and passing handoff state tables.

## Development Resumption Guidelines

1. Physical target is bare-metal x86 EFI.
2. Maintain zero code dependency on proprietary binaries or reverse-engineered blobs.
3. Validate each execution milestone with standalone and integration test harnesses.
4. Keep all technical records, code comments, and commit messages strictly in **English**.
