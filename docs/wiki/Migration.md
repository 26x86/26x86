# Migrating an existing configuration

**Current Status:** Reversible preparation guidance; existing tool/system state must be identified.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

NextCore's experimental clean-room EFI runtime and the external OpenCore/patcher
workflow have different execution contracts. Moving configuration directories
does not turn one into the other or establish macOS compatibility.

1. Identify the currently installed tool, version, EFI volume and root-patch state.
2. Save its complete configuration, referenced files and recovery procedure.
3. Review the prior tool's supported uninstall/reversal workflow before removing
   services or changing the system volume. Do not delete LaunchAgent wildcards.
4. Prepare a separate candidate bundle and compare its proposed file changes.
5. Validate and test external media before replacing a working internal EFI.

A model identifier, boot argument or profile name is not proof of an active
WebKit instruction translator or an accepted macOS handoff. See
[configuration](Configuration.md), [installation boundaries](Installation-Notes.md)
and [current progress](../progress.md).

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
