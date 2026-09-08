# NextCore

<div align="center">
  <img src="resources/branding/nextcore-logo-256.png" alt="NextCore" width="144" />
  <h3>macOS compatibility on x86 EFI</h3>
  <p>UEFI boot, HAL translation, and Metal acceleration development for macOS 26 Tahoe and macOS 27 Golden Gate.</p>
  <p>
    <a href="https://github.com/26x86/26x86/actions">Actions</a> ·
    <a href="https://26x86.github.io/26x86/">Documentation</a> ·
    <a href="docs/MELLOW_INTEGRATION.md">Mellow</a> ·
    <a href="SECURITY.md">Security</a>
  </p>
</div>

> **Experimental alpha.** Work from a full backup on a test machine. A passed
> static check, emulator probe, or firmware transfer is never presented as a
> physical-Mac or macOS boot result.

## Start here

| I want to… | Go to |
| --- | --- |
| Browse the documentation site | [NextCore docs](https://26x86.github.io/26x86/) |
| Understand the public architecture | [Documentation hub](docs/wiki/README.md) |
| Boot macOS on Intel hardware | [Setup and compatibility guide](docs/wiki/Home.md) |
| Develop ARM64e macOS on an x86 computer | [Module and EFI JIT guide](docs/wiki/Nextcore-Modules.md) |
| Run the guided tool | `26x86.command` or `python3 -m x86 wizard` |
| Build on Windows | [Windows EXE workflow](#windows-exe) |
| Inspect supported operating modes | [Mellow integration](docs/MELLOW_INTEGRATION.md) |
| Follow the boot-engineering work | [NextCore validation](nextcore/VALIDATION.md) |
| Review boundaries and notices | [Disclaimer](DISCLAIMER.md) · [Security](SECURITY.md) · [Source policy](SOURCE.md) |

## The platform

NextCore is an experimental macOS bootloader and compatibility layer for x86
computers. macOS 27 uses the ARM64e operating-system build, with an M1 baseline,
translated by a macOS-focused ARM64e-to-x86_64 JIT and hardware adaptation layer
running directly in x86 EFI. WSL2 is the development environment; QEMU/OVMF is a
firmware test fixture. Neither is required by the target EFI runtime.

The integration repository owns the guided tools, build orchestration and evidence.
Seven independently versioned repositories are checked out as real Git submodules
under `nextcore/crates/`. The ISE module owns the freestanding C/Rust JIT runtime;
the EFI module links it through a pinned build dependency. See the
[module guide](docs/wiki/Nextcore-Modules.md) for recursive clone and build commands.

Changes to `main` arrive **only through pull requests**. `main` is protected:
required reviews, required status checks (`docs-build`, `isolated-asset-guard`,
`workspace-tests`), and the documentation site deploys from `main` after a PR
merge. See the [branching and release policy](docs/wiki/Branching-and-Release.md).

| Area | Repository | What it owns |
| --- | --- | --- |
| **Patcher** | [26x86](https://github.com/26x86/26x86) | Guided workflow, OpenCore integration, EFI and root-patch preparation |
| **Boot core** | [Nextcore-Core](https://github.com/26x86/Nextcore-Core) | Configuration, public format codecs, and handoff contracts |
| **UEFI** | [Nextcore-EFI](https://github.com/26x86/Nextcore-EFI) | EFI application and controlled handoff probes |
| **Runtime** | [Nextcore-APLS](https://github.com/26x86/Nextcore-APLS) · [Nextcore-GPU](https://github.com/26x86/Nextcore-GPU) | Recovery diagnostics and GPU command execution |
| **Hardware translation** | [Nextcore-HAL](https://github.com/26x86/Nextcore-HAL) · [Nextcore-ISE](https://github.com/26x86/Nextcore-ISE) | Platform-table translation and the freestanding ARM64e JIT runtime |
| **CLI** | [Nextcore-Tool](https://github.com/26x86/Nextcore-Tool) | Reproducible command-line orchestration |
| **Compatibility packages** | [OpenCorePkg](https://github.com/26x86/OpenCorePkg) · [MetallibSupportPkg](https://github.com/26x86/MetallibSupportPkg) · [PatcherSupportPkg](https://github.com/26x86/PatcherSupportPkg) | Upstream integration and patcher support |

Each NextCore module has its own Git history, pinned integration commit,
file-hash inventory, and CI gate. The module boundary does not widen any
boot claim: it makes each layer easier to inspect and test.

## Evidence status

| Layer | Current evidence | Status |
| --- | --- | --- |
| EFI picker | Actual OVMF GOP selection, matching child execution, Esc cancellation, automatic boot and text fallback | Verified at the firmware UI layer |
| Tahoe native EFI | NextCore ConsoleControl → original booter → original XNU and launchd, correlated with a unique CPU memory sample | Early userspace reached; full HAL and OS acceptance unfinished |
| Tahoe external reference | Signed recovery reaches WindowServer and the recovery GUI after a standard virtual SMC is supplied | Recovery GUI verified; installed OS and Metal unfinished |
| ARM64e JIT in x86 EFI | Native translated blocks, software PAC/AUT, 16 GOP pixels read back, and 9 positive/negative firmware cases | Authored fixtures verified; macOS boot unfinished |
| Golden Gate ARM recovery | DFU, iBEC endpoint, Stage2 prompt, five restore roles and `bootx` acknowledgement | A same-event unmapped MMIO read stops firmware before XNU |
| Metal | Real Intel host GPU compute/readback; x86_64 and ARM64 guest Metal probes built | Guest Metal execution remains mandatory and unverified |

Read the complete acceptance boundary in [NextCore validation](nextcore/VALIDATION.md)
and the [session evidence report](nextcore/artifacts/NEXTCORE_SESSION_REPORT_20260907.md).

## Firmware picker

![NextCore picker running in OVMF](resources/branding/nextcore-picker.png)

This is an actual OVMF screenshot with authored test entries. Set
`Misc.Boot.ShowPicker=true` to select enabled `Misc.Entries` using the arrow keys
or Tab, Enter to boot, and Esc to cancel. The current loader selects configured
EFI applications on its own volume. Missing/false `ShowPicker` retains the
existing single-entry automatic boot behavior. Unsupported graphics modes use
the firmware text menu. This screen is separate from a macOS GUI or Metal result.

## Working modes

**x86 Mac mode** prepares the EFI and root-patch path for native hardware.
**Apple Silicon Sandbox mode** is a contained diagnostic and research path; it
does not load host kexts or apply root patches. The Tauri GUI is the default
desktop surface (WKWebView/WebView2); Cocoa pywebview remains a fallback.

Surface Pro 6 i5-8250U / Tahoe preparation is documented separately in the
[Surface Pro 6 guide](docs/SURFACE_PRO6.md). It uses the same evidence gate:
file checks are useful, but boot, display acceleration, audio, sleep, touch,
and recovery each need runtime acceptance.

<details>
<summary><strong>Windows EXE</strong></summary>

The [Build Windows EXE](https://github.com/26x86/26x86/actions/workflows/windows-exe.yml)
workflow builds `dist/26x86/26x86.exe` from
`scripts/build-windows-exe.ps1 -Clean`. Download the `26x86-windows-exe`
artifact from the corresponding Actions run. If the app has a blank window,
install Microsoft Edge WebView2 Runtime before diagnosing the bundle.

</details>

<details>
<summary><strong>Sandbox and recovery boundary</strong></summary>

The sandbox accepts caller-supplied original inputs, uses copy-on-write
overlays, and leaves IPSW, installer files, ESP, and source components
unchanged. It records the recovery chain but does not force a boot transition.
The current trace reached the iBEC prompt, the five restore roles, and `bootx`;
the subsequent firmware panic means XNU, graphics, and installer UI remain
unverified. See [Apple Silicon Sandbox](docs/APPLE_SILICON_SANDBOX.md),
[VSK](docs/VSK.md), and [Golden Gate GUI validation](docs/QEMU_GOLDEN_GATE_GUI.md).

</details>

## Project rules

- Public repositories contain clean-room source and public specifications only.
- `_isolated/` research material is excluded by Git and pre-commit guards.
- An observation advances only the layer it measures; it cannot stand in for a
  later firmware, kernel, userspace, graphics, or physical-hardware result.

Read [CONTRIBUTING guidance](docs/wiki/Developer.md), [NOTICE.md](NOTICE.md),
[CREDITS.md](CREDITS.md), and the [upstream inventory](docs/wiki/Upstream-Repositories.md)
before integrating changes.
