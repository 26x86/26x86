# Getting started

26x86 prepares an OpenCore-based EFI workflow for Intel Macs and related
experimental targets. Begin with a complete backup and identify the exact Mac
model, GPU, storage layout, firmware mode, and target macOS release.

## Recommended path

1. Read [Supported models](Supported-Models.md).
2. Read the matching [macOS support](macOS-Support.md) notes.
3. Prepare an installer and recovery path.
4. Generate and inspect the OpenCore configuration.
5. Install to a known ESP only after the static checks are clean.
6. Record physical boot and device results separately from file validation.

Do not treat a generated EFI, emulator result, or validation tool output as
proof of a physical Mac boot.
