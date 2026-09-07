# 26x86

<div align="center">
  <img src="resources/branding/26x86-logo-256.png" alt="26x86" width="144" />
  <h3>macOS 26 on x86-based Macintosh hardware</h3>
  <p>OpenCore integration, clean-room boot research, and evidence-first compatibility tooling.</p>
  <p>
    <a href="https://github.com/26x86/26x86/actions">Actions</a> ·
    <a href="docs/wiki/Home.md">Docs</a> ·
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
| Prepare an Intel Mac for Tahoe | [Setup and compatibility guide](docs/wiki/Home.md) |
| Run the guided tool | `26x86.command` or `python3 -m x86 wizard` |
| Build on Windows | [Windows EXE workflow](#windows-exe) |
| Inspect supported operating modes | [Mellow integration](docs/MELLOW_INTEGRATION.md) |
| Follow the boot-engineering work | [Nextcore validation](nextcore/VALIDATION.md) |
| Review boundaries and notices | [Disclaimer](DISCLAIMER.md) · [Security](SECURITY.md) · [Source policy](SOURCE.md) |

## The platform

26x86 is organized as small, inspectable modules. The core repository carries
the user-facing patcher, OpenCore integration, EFI preparation, diagnostics,
and cross-layer contracts. The companion repositories isolate reusable boot
and runtime components so their evidence can be reviewed independently.

| Area | Repository | What it owns |
| --- | --- | --- |
| **Patcher** | [26x86](https://github.com/26x86/26x86) | Guided workflow, OpenCore integration, EFI and root-patch preparation |
| **Boot core** | [Nextcore-Core](https://github.com/26x86/Nextcore-Core) | Configuration, public format codecs, and handoff contracts |
| **UEFI** | [Nextcore-EFI](https://github.com/26x86/Nextcore-EFI) | EFI application and controlled handoff probes |
| **Runtime** | [Nextcore-APLS](https://github.com/26x86/Nextcore-APLS) · [Nextcore-GPU](https://github.com/26x86/Nextcore-GPU) | VMApple recovery orchestration and GPU policy |
| **Hardware translation** | [Nextcore-HAL](https://github.com/26x86/Nextcore-HAL) · [Nextcore-ISE](https://github.com/26x86/Nextcore-ISE) | Platform-table translation and instruction policy |
| **CLI** | [Nextcore-Tool](https://github.com/26x86/Nextcore-Tool) | Reproducible command-line orchestration |
| **TCG research** | [VenFire](https://github.com/26x86/VenFire) · [VenFire-QEMU](https://github.com/26x86/VenFire-QEMU) | Isolated VMApple/TCG conformance and backend contracts |
| **Compatibility packages** | [OpenCorePkg](https://github.com/26x86/OpenCorePkg) · [MetallibSupportPkg](https://github.com/26x86/MetallibSupportPkg) · [PatcherSupportPkg](https://github.com/26x86/PatcherSupportPkg) | Upstream integration and patcher support |

Every exported Nextcore module has an independent `main` branch, fixed initial
tag, file-hash inventory, and CI gate. The module boundary does not widen any
boot claim: it makes each layer easier to inspect and test.

## Evidence status

| Layer | Current evidence | Status |
| --- | --- | --- |
| x86 UEFI | Authored OVMF handoff probes validate allocation, memory-copy, flat DeviceTree, and 32-bit transition contracts | Contract verified; not XNU boot |
| ARM recovery | DFU, iBEC endpoint, Stage2 prompt, restore-role transfer, and `bootx` acknowledgement are recorded | Firmware panic after `bootx`; macOS not verified |
| Native Apple Silicon | The current Windows and registered remote hosts are x86_64 | A native macOS/Apple Silicon host is still required |
| Userspace and Metal | No target-matching XNU/userspace boot evidence yet | Not verified |

Read the complete acceptance boundary in [Nextcore validation](nextcore/VALIDATION.md)
and the [session evidence report](nextcore/artifacts/NEXTCORE_SESSION_REPORT_20260907.md).

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

Read [CONTRIBUTING guidance](docs/wiki/Home.md), [NOTICE.md](NOTICE.md),
[CREDITS.md](CREDITS.md), and the [upstream inventory](docs/wiki/Upstream-Repositories.md)
before integrating changes.
