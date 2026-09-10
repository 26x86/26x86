# Third-Party Licenses

Overview of licenses governing third-party libraries and upstream software components utilized within 26x86. Full upstream copyright notices reside in `LICENSE.txt`, `NOTICE.md`, and [docs/wiki/Upstream-Repositories.md](./docs/wiki/Upstream-Repositories.md).

## 26x86 (This Repository)

- **License:** BSD 3-Clause (derived from OpenCore Legacy Patcher); see [LICENSE.txt](./LICENSE.txt).
- **Copyright:** Copyright (c) 2026 NiSeullent and 26x86 contributors.
- **Upstream Origin:** Derived from OpenCore Legacy Patcher and OpenCore Legacy Patcher T2.

## Upstream Project Lineage

- **OpenCore-Legacy-Patcher:** https://github.com/dortania/OpenCore-Legacy-Patcher (BSD 3-Clause)
- **OpenCore-Legacy-Patcher-T2:** https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2 (BSD 3-Clause)
- **26x86 Repository:** https://github.com/26x86/26x86 (BSD 3-Clause)

## Support Packages & Bootloaders

| Component | License | Repository |
|-----------|---------|------------|
| OpenCorePkg | BSD 3-Clause | https://github.com/acidanthera/OpenCorePkg |
| 26x86-OpenCorePkg | BSD 3-Clause | https://github.com/26x86/OpenCorePkg |
| PatcherSupportPkg | Repository Policy | https://github.com/26x86/PatcherSupportPkg |
| MetallibSupportPkg | Repository Policy | https://github.com/26x86/MetallibSupportPkg |

## Acidanthera Kexts

| Kext | License | Role |
|------|---------|------|
| Lilu | BSD 3-Clause | Kernel and userland patching engine |
| WhateverGreen | BSD 3-Clause | Graphics drivers and framebuffer management |
| AppleALC | BSD 3-Clause | Audio driver enablement |
| RestrictEvents | BSD 3-Clause | CPU feature masking and instruction bridge |
| NVMeFix | GPL v2.0 | Power management for non-Apple NVMe drives |

## Trademark Disclaimer

- **macOS**, **Apple**, and associated marks are trademarks of Apple Inc.
- **OpenCore** is a trademark of Acidanthera.
- **26x86** is an independent community project with no corporate affiliation.
