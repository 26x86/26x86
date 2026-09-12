# Application

**Current Status:** Preparation and diagnostic workflows do not establish guest OS boot.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

The NextCore application provides a guided workflow around EFI preparation,
diagnostics, and evidence collection.

## Modes

- **x86 Mac mode** prepares EFI and root-patch inputs for native hardware.
- **Apple Silicon Sandbox mode** is a contained diagnostic and research path;
  it does not imply host-kext or root-patch support.

## Safe operating pattern

Use the application with a backup, keep the target hardware identified, and
review the proposed file changes before transferring an EFI. For failures,
capture the log and identify the first failing layer before changing settings.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
