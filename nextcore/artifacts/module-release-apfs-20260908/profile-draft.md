<div align="center">
  <a href="https://github.com/26x86/26x86"><img src="https://raw.githubusercontent.com/26x86/26x86/main/resources/branding/nextcore-logo-256.png" alt="NextCore" width="120" /></a>
  <h1>NextCore · 26x86</h1>
  <p><strong>Public EFI boot engineering, from firmware to graphics.</strong></p>
  <p>macOS 26 Tahoe native HAL · macOS 27 Golden Gate AMD64 ↔ Apple Silicon HAL · Metal</p>
  <p><a href="https://github.com/26x86/26x86">Project</a> · <a href="https://github.com/26x86/26x86/blob/main/docs/NEXTCORE_CURRENT_CONTEXT.md">Current progress</a> · <a href="https://github.com/orgs/26x86/repositories">Repositories</a> · <a href="https://github.com/26x86/26x86/actions">CI</a></p>
</div>

NextCore is a clean-room EFI boot stack developed within 26x86. We are building
native platform support for Tahoe and the AMD64 ↔ Apple Silicon path for Golden
Gate, including guest Metal. These are active engineering goals; the complete
platform and graphics stack is not yet verified.

## What runs today

The [2026-09-08 source snapshot](https://github.com/26x86/26x86/tree/65d1e85db2dfcd4e1c07656bb0bfc315d36fac83)
records each result at the layer actually exercised.

| Layer | Observed result | Remaining work |
| --- | --- | --- |
| NextCore EFI | GOP/text picker, keyboard selection and child launch in OVMF | Automatic OS volume discovery |
| Tahoe recovery | NextCore → original booter → XNU and userspace; readable, interactive Recovery menus in local QEMU/KVM | Independent KC-loader entry and complete native HAL |
| APFS EFI driver | [Original driver extraction, StartImage and controller connection succeeded](https://github.com/26x86/26x86/blob/65d1e85db2dfcd4e1c07656bb0bfc315d36fac83/nextcore/artifacts/apfs-firmware-20260908/original-apfs-result.json) | Filesystem opening and installed-OS boot verification |
| Golden Gate ARM64E | Public boot-argument codec and immutable KC host staging with full view readback | Physical placement, CPU/PAC/DT integration and original XNU entry |
| Graphics | Intel host Vulkan submission/readback; guest Metal probes built and a Tahoe Recovery probe executed | Guest probe reported no Metal device; **metal_verified=false** |

Host tests and emulator results do not establish physical-Mac support. Full
installation, the complete Golden Gate boot path and guest Metal remain open.
See the pinned [context](https://github.com/26x86/26x86/blob/65d1e85db2dfcd4e1c07656bb0bfc315d36fac83/docs/NEXTCORE_CURRENT_CONTEXT.md)
and [validation record](https://github.com/26x86/26x86/blob/65d1e85db2dfcd4e1c07656bb0bfc315d36fac83/nextcore/VALIDATION.md)
for the exact execution conditions and boundaries.
The [current development record](https://github.com/26x86/26x86/blob/main/docs/NEXTCORE_CURRENT_CONTEXT.md)
tracks later work; each released module retains its own immutable source-commit reference.

## Seven independently versioned modules

Core/EFI `v0.1.2` and Tool `v0.1.3` use the source commit above. GPU, HAL,
ISE and APLS retain their [original `v0.1.1` source](https://github.com/26x86/26x86/tree/dcc90013109eac694ccbf997b1e44a7018480f78).
Tool retains its [crate-local test-fixture correction](https://github.com/26x86/26x86/commit/045065700cbd037eaaa974faf957ba15cb628370).
The three updated modules passed independent Linux clone gates before and after
publishing; EFI additionally linked the NXAPFS application. Exact release-head CI
also passed. The linked module build is not itself an execution test.
Cross-module dependencies use fixed tags; inventories record the exported public
files. Package versions remain those of each source snapshot.

| Module | Responsibility | Fixed snapshot |
| --- | --- | --- |
| [Core](https://github.com/26x86/Nextcore-Core) | Configuration, public image/DT formats and architecture-specific preparation | [v0.1.2](https://github.com/26x86/Nextcore-Core/tree/26x86-Nextcore-Core-v0.1.2) · [6547be4](https://github.com/26x86/Nextcore-Core/commit/6547be4bbf6b75cf706b89ade4d4a60d5441d223) |
| [EFI](https://github.com/26x86/Nextcore-EFI) | Firmware picker, platform services and bounded handoff | [v0.1.2](https://github.com/26x86/Nextcore-EFI/tree/26x86-Nextcore-EFI-v0.1.2) · [64a2d4c](https://github.com/26x86/Nextcore-EFI/commit/64a2d4ce432c2f5ccd300728309556c898317436) |
| [Tool](https://github.com/26x86/Nextcore-Tool) | CLI preparation and orchestration | [v0.1.3](https://github.com/26x86/Nextcore-Tool/tree/26x86-Nextcore-Tool-v0.1.3) · [36e0fd5](https://github.com/26x86/Nextcore-Tool/commit/36e0fd50047182ee6b2abdca87249d8c1a084e73) |
| [HAL](https://github.com/26x86/Nextcore-HAL) | Public platform-table metadata | [v0.1.1](https://github.com/26x86/Nextcore-HAL/tree/26x86-Nextcore-HAL-v0.1.1) |
| [ISE](https://github.com/26x86/Nextcore-ISE) | Instruction and CPU feature policy | [v0.1.1](https://github.com/26x86/Nextcore-ISE/tree/26x86-Nextcore-ISE-v0.1.1) |
| [GPU](https://github.com/26x86/Nextcore-GPU) | Graphics contracts and optional host Vulkan backend | [v0.1.1](https://github.com/26x86/Nextcore-GPU/tree/26x86-Nextcore-GPU-v0.1.1) |
| [APLS](https://github.com/26x86/Nextcore-APLS) | ARM recovery orchestration and public guest interfaces | [v0.1.1](https://github.com/26x86/Nextcore-APLS/tree/26x86-Nextcore-APLS-v0.1.1) |

## Related projects and upstream integration

[26x86](https://github.com/26x86/26x86) also provides guided setup, OpenCore
integration, EFI preparation and diagnostics. [VenFire](https://github.com/26x86/VenFire)
and [VenFire-QEMU](https://github.com/26x86/VenFire-QEMU) hold the separate
emulation research track. Upstream integration and support packages remain in
[OpenCorePkg](https://github.com/26x86/OpenCorePkg),
[MetallibSupportPkg](https://github.com/26x86/MetallibSupportPkg) and
[PatcherSupportPkg](https://github.com/26x86/PatcherSupportPkg).

Public repositories contain independently authored source and public interfaces,
not Apple firmware, guest disks, extracted blobs or private research material.
