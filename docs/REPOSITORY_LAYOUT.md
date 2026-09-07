# 26x86 repository layout

The GitHub publication boundary is explicit at the repository/CI layer. All
modules live in the [`26x86`](https://github.com/26x86) organization and use
OpenCore-style naming: no organization prefix inside the organization (the
same convention as `acidanthera/OpenCorePkg`).

| Repository | Layer | Owns | Depends on |
| --- | --- | --- | --- |
| `26x86/26x86` | Core EFI/control plane | OpenCore, EFI, native host control and integration contracts | none |
| `26x86/VenFire` | User-space emulation/evidence | ARM64 synthetic guests, input integrity, storage/recovery policy, packaging and conformance | `26x86/VenFire-QEMU` |
| `26x86/VenFire-QEMU` | Emulator backend | Pinned QEMU commit, VMApple TCG/headless patch series, backend audit/build tools | upstream QEMU commit `ff1d2d19d7e24893e2012d879f8e73077e17b9bd` |
| `26x86/OpenCorePkg` | Bootloader fork | OpenCore bootloader with 26x86 integration | `acidanthera/OpenCorePkg` |
| `26x86/MetallibSupportPkg` | Support package | Metal library patching utilities | none |
| `26x86/PatcherSupportPkg` | Support package | Patcher support | none |
| `26x86/.github` | Organization profile | `profile/README.md` module-family overview | none |

`26x86/26x86` is the transferred continuation of the former `NiSeullent/26x86`
repository; GitHub redirects the old URL. The support packages were likewise
transferred from their `26x86-*` personal-repository names.

`26x86-VenFire` is not a release namespace inside the core repository. Its
release tags and assets belong to the standalone repository. The QEMU patch
series is likewise published under its own module repository so a backend
change cannot be mistaken for an EFI or macOS guest release.

The portable runtime boundary is:

```text
26x86 core contract -> VenFire control plane -> VenFire-QEMU backend
                              |
                       QEMU TCG -> AArch64 guest
```

The chain is software emulation on non-Apple hosts. It does not depend on
Virtualization.framework. A QEMU capability probe or synthetic guest PASS is
not a macOS boot result; the VenFire UART gate still requires target-matching
XNU and userspace evidence from caller-supplied signed Golden Gate inputs.

## Export and publication

From a clean working tree, generate fresh local trees:

```sh
python3 Tools/export_repositories.py --output /tmp/26x86-repositories
```

The exporter refuses to overwrite an existing output. Each tree is given its
own initial commit and module-specific tag. Publishing uses only the `ADGIT`
credential and never writes it into a Git remote URL or a file:

```sh
python3 Tools/sync_github_repositories.py \
  --exports /tmp/26x86-repositories --apply
```

The synchronization command creates missing organization repositories as
public, verifies the authenticated user is an active admin of the `26x86`
organization, pushes the module branch/tags, and removes only legacy core
releases whose tag starts with the exact known-wrong prefix
`26x86-VenFire-GoldenGate-v` (release and tag are cleaned together).
Deletion is opt-in via `--apply` and is reported per release.
