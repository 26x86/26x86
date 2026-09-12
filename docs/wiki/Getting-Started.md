# Getting started

**Current Status:** Read-only setup and preparation guide for experimental workflows.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Choose a workflow from the [documentation portal](../index.md), then check the
[compatibility catalog](../compatibility.md) before preparing media. NextCore's
macOS 27 ARM64e-on-x86 path is experimental and does not yet provide a usable
physical macOS desktop. External OpenCore preparation is a separate workflow.

## Read-only first steps

1. Identify the real model, CPU features, firmware architecture, GPU, storage
   controller and target macOS build. An SMBIOS override is not the real model.
2. Read [current progress](../progress.md) and the relevant hardware entry.
3. For application inspection, follow [Setup](../SETUP.md) and run
   `python -m x86 detect --json`; detection does not certify support.
4. For firmware development, use the recursive clone and pinned-module build
   instructions in [Module repositories](Nextcore-Modules.md).
5. Prepare backups and a separately bootable recovery path before a deployment.
6. Validate a complete candidate EFI on external media, then record physical
   firmware, guest boot, display and input observations separately.

`NOT_READY` from normal ARM64e entry means required providers are missing.
`ABORTED` from an explicitly bounded trace is its diagnostic result, not an
installation failure to bypass. See [Troubleshooting](Troubleshooting.md).
