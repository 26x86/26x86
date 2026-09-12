# Upstream Repositories

**Current Status:** Attribution index; a reference does not establish current package use or compatibility.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

**26x86** — Clean-room boot engineering and compatibility tooling for macOS 26 Tahoe on x86-based Mac hardware.

## Overview

26x86 builds upon the collective foundations of the open-source bootloader and macOS compatibility communities, while establishing clean-room contracts for the next generation of operating systems.

This document lists all upstream projects and repositories referenced, utilized, or forked. Copyright and attribution remain with their respective authors.

## Core Boot & Patcher Repositories

| Project | Organization / Repository | Focus |
|---------|---------------------------|-------|
| OpenCorePkg | [acidanthera/OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) | Foundational UEFI bootloader |
| OpenCore-Legacy-Patcher | [dortania/OpenCore-Legacy-Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) | Community legacy hardware patcher |
| OCLP T2 Fork | [albert-mueller/OpenCore-Legacy-Patcher-T2](https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2) | Initial T2 hardware enablement experiments |
| PatcherSupportPkg | [dortania/PatcherSupportPkg](https://github.com/dortania/PatcherSupportPkg) | Pre-built binaries, payload kexts, and helper tools |
| MetallibSupportPkg | [dortania/MetallibSupportPkg](https://github.com/dortania/MetallibSupportPkg) | Metal shading language bytecode utilities |

## Kernel Extensions (Kexts)

| Kext | Maintainer | Role |
|------|------------|------|
| Lilu | Acidanthera | Arbitrary kernel and userland patching engine |
| WhateverGreen | Acidanthera | Graphics subsystem patches and framebuffer management |
| AppleALC | Acidanthera | High-definition audio driver patches |
| RestrictEvents | Acidanthera | CPU and hardware capability policy control |

## Clean-Room Standards

All original components developed under the 26x86 organization (including the NextCore boot stack: `Nextcore-Core`, `Nextcore-EFI`, `Nextcore-Tool`, `Nextcore-APLS`, `Nextcore-GPU`, `Nextcore-HAL`, and `Nextcore-ISE`) are developed under clean-room procedures without inclusion of proprietary Apple binaries or internal trade secrets.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
