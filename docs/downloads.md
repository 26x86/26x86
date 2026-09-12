# Download the prebuilt EFI package

**Current Status:** Development binaries. Normal macOS startup is **NOT_READY**;
physical desktop boot is **unverified**.

**Target State:** Every website deployment includes a verified EFI archive built
from the exact public source pin, with separate baseline and diagnostic binaries.

[Download prebuiltefi.zip](https://26x86.github.io/26x86/prebuiltefi.zip){ .md-button .md-button--primary }
[Archive SHA-256 and source revision](https://26x86.github.io/26x86/prebuiltefi.json){ .md-button }

The ZIP is generated during this website deployment. Deployment fails if its
release binaries or inventory cannot be verified. The download is a development
package; it is not a working macOS installer or a hardware compatibility promise.

| Archive path | Purpose |
| --- | --- |
| `EFI/BOOT/BOOTX64.EFI` | Baseline x86_64 UEFI application, without selected diagnostic features |
| `EFI/OC/config.plist` | Public empty configuration; no automatic guest selection |
| `diagnostics/NXARMJIT.efi` | Explicit mapped ARM diagnostic, separate from the normal boot entry |
| `manifest.json` | Exact source, submodule revisions, build commands and per-file hashes |
| `README.txt` | Layout, configuration and evidence limits |

Use a separate FAT-formatted removable test volume with the `EFI` directory at
its root. Preserve the existing system EFI and recovery path. The package makes
no disk or NVRAM changes automatically. With its empty configuration, the baseline
shows the configuration recovery screen: Enter retries the same file and Esc
returns to firmware with NOT_FOUND. Required display or input failures retain
their actual error. It does not select or boot a guest: hardware-specific
configuration and Apple payloads are not included.

Do not rename `NXARMJIT.efi` to `BOOTX64.EFI`. The diagnostic requires separately
supplied inputs and an explicitly accepted configuration. It does not prove that
the original kernel's entry requirements are satisfied. Read the included README
and the [current execution evidence](PREFIX_PROGRESS_VALIDATION.md).

The reviewed build selection is recorded in [the source manifest](data/prebuilt.json).
The downloadable archive sidecar records the hash of this deployment's ZIP;
verify it before using the files. A source-pin update changes this manifest
explicitly and rebuilds both binaries.
