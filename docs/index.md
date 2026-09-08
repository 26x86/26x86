---
hide:
  - navigation
---

# 26x86

<div class="hero">
  <h1>Modern Intel &amp; Apple Silicon macOS bootloader</h1>
  <p class="hero-sub">
    Clean-room EFI boot research, OpenCore integration, and evidence-first
    compatibility tooling for macOS Tahoe — documented the way the ecosystem
    actually builds it.
  </p>
  <div class="hero-actions">
    <a class="md-button md-button--primary" href="wiki/README.md">Start here</a>
    <a class="md-button" href="wiki/Getting-Started.md">Getting started</a>
    <a class="md-button" href="wiki/Supported-Models.md">Supported models</a>
  </div>
</div>

!!! danger "Experimental alpha"

    Work from a full backup on a test machine. A passed static check, emulator
    probe, or firmware transfer is **never** presented as a physical-Mac or
    macOS boot result. Every acceptance boundary is documented per layer in
    [Boot engineering](wiki/Architecture.md).

## What this documentation covers

| Section | What you will find |
| --- | --- |
| [Quick start](wiki/README.md) | Install, configure, and run the guided tool |
| [macOS compatibility](wiki/macOS-Support.md) | Supported machines, Tahoe notes, known limits |
| [OpenCore integration](wiki/OpenCore.md) | Bootloader wiring, EFI preparation, upstream packages |
| [Application](wiki/Application.md) | GUI, Mellow mode, sandbox and validation harnesses |
| [Troubleshooting](wiki/Troubleshooting.md) | Common failures, GPU limitations, warnings |
| [Boot engineering](wiki/Architecture.md) | Nextcore clean-room EFI/xnu handoff contracts and evidence |
| [Contribution](wiki/Developer.md) | PR workflow, branch and release policy, boundaries |

## Front page of the boot-engineering effort

```text
x86 UEFI handoff probes      → contract verified (not XNU boot)
ARM recovery (VMApple)       → bootx acknowledged, firmware panic after
Native Apple Silicon         → no registered native host yet
Userspace + Metal            → no target-matched XNU/userspace evidence yet
```

Detailed per-layer status lives in **Nextcore validation** (repository)
[`nextcore/VALIDATION.md`](https://github.com/26x86/26x86/blob/main/nextcore/VALIDATION.md)
and the [session evidence report][1]. The documentation site itself is built
from [`docs/`](https://github.com/26x86/26x86/tree/main/docs) with MkDocs
Material and deployed only from `main` through a pull request.

[1]: https://github.com/26x86/26x86/blob/main/nextcore/artifacts/NEXTCORE_SESSION_REPORT_20260907.md

## Working modes

- **x86 Mac mode** — prepares the EFI and root-patch path for native Intel Macs.
- **Apple Silicon Sandbox mode** — contained diagnostic and research path; never
  loads host kexts or applies root patches.
- **Surface Pro 6 / Tahoe orientation** — same evidence gate: *file checks are
  useful, but boot, display acceleration, audio, sleep, touch, and recovery each
  need runtime acceptance.*

See [Setup guides](SETUP.md) and [Supported hardware](wiki/Supported-Models.md).

## Project rules

- Public repositories contain clean-room source and public specifications only.
- `_isolated/` research material is excluded by Git and pre-commit guards and is
  never staged, committed, or pushed.
- An observation advances only the layer it measures; it cannot stand in for a
  later firmware, kernel, userspace, graphics, or physical-hardware result.