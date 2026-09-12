# Mellow in 26x86

**Current Status:** Diagnostic artifact and deployment checks; working guest Metal remains unavailable.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

**Mellow — Metal Emulation Layer Logic for OpenGL/OpenCL Workloads** is integrated
as a driver/runtime project, not solely an OpenCore kext switch. This change
connects the available native diagnostic artifact to 26x86 deployment policy and
the existing APFS root-patch engine. It does not introduce a working Tahoe Metal
driver, WindowServer acceleration, or an Apple Silicon VM backend.

## Source and artifact identity

`vendor/mellow` is the complete Git-tracked source snapshot of
`NiSeullent/Mellow@72f3df08ff05c20bdbbada7723009b88f6ccd25e`. The source archive
receipt is `vendor/mellow-source.json`. Original license files and per-file
notices remain authoritative; this snapshot is not relicensed under 26x86's
license. The vendored source does not run during patch installation.

`payloads/Mellow` includes the actual cross-built Mellow 0.4.3 x86_64 diagnostic
kext, its build report, licensing, and an exact manifest. Executable SHA256:
`6932453a484ac62fb46f19b78f4a6424cef8ba907a3abe655b051bf03daed3c7`.
The loader also pins the executable and Info.plist independently of the manifest.
Updating an artifact therefore requires a reviewed source/build/policy update;
rewriting manifest hashes alone cannot approve a different driver.

The component model separates:

- `kext`: `/Library/Extensions/Mellow.kext`, kernel/IOKit layer.
- `user_driver`: `/Library/Application Support/Mellow/Drivers/MellowDriver.bundle`,
  a reserved userspace driver destination.
- `runtime`: `/Library/Frameworks/Mellow.framework`, a reserved userspace runtime destination.

Only the diagnostic kext is currently available and accepted. Driver/runtime
categories without a validated Darwin artifact are rejected rather than filled
with empty bundles. The source tree contains compiler and userspace work, but
that is not evidence of a system Metal provider.

## Two execution modes

`x86` permits native EFI preparation on Windows/Linux and application on an
installed, verified x86 macOS host. `apple-silicon-sandbox` forbids native EFI
preparation, Mellow.kext loading and host root patching. Its backend belongs to a
virtualized userspace boundary; selecting the mode does not create or start a VM.

Policy is checked in settings, CLI/GUI, child workers, payload validation and the
native root engine. Apple Silicon is detected using architecture and live sysctl
facts, including Rosetta. An x86 process running under Rosetta cannot opt into
native x86 patching. Probe errors fail closed. The child environment mode cannot
be overridden by a conflicting command-line mode.

This is a 26x86 product policy, not a claim that Apple Silicon universally cannot
use custom kernel extensions. Apple's separate requirements are described in
[Installing a custom kernel extension](https://developer.apple.com/documentation/apple-silicon/installing-a-custom-kernel-extension).

## EFI and root deployment

Choose one Mellow deployment route: `efi` or `root-patch`. `disabled` is the
default. An enabled Mellow bundle ID in the supplied EFI blocks a second route,
including renamed bundles. Lilu must be version 1.6.4 or newer, with an
entry covering x86_64/Darwin 25 and a present executable. EFI deployment requires
enabled Lilu; root-patch deployment requires its `Kernel/Add` entry disabled and
the dependency available on disk. Enabled Mellow/Lilu `Kernel/Force` or
`Kernel/Block` entries are rejected. A supplied EFI path is
not proof that it is the firmware's actual boot ESP; verify that association on
the test host before applying.

Cross-platform, read-only plan:

```sh
python3 -m x86.cli mellow plan --mode x86 --deployment root-patch --efi /path/to/EFI
```

Prepare a separate root-patch EFI configuration from an EFI with Lilu enabled:

```sh
python3 -m x86.cli mellow prepare-root-efi --mode x86 --efi /path/to/EFI --output /new/root-patch/EFI
```

This disables Lilu EFI injection, leaves Mellow uninjected and adds `-mellowdiag`.
It requires a working disk-loaded Lilu on the target before booting the prepared
configuration. The reference Lilu bundle stays in the EFI directory, disabled,
so native preflight can compare it to the installed dependency. Do not activate
this configuration on a target that only has EFI-loaded Lilu.

Prepare a new EFI copy with dependency ordering and `-mellowdiag`:

```sh
python3 -m x86.cli mellow prepare-efi --mode x86 --efi /path/to/EFI --output /new/path/EFI
```

This command refuses an existing output, copies the actual payload, reads back
its bytes, and preserves the source EFI. It does not mount an ESP, modify a USB,
boot an OS, or run `ocvalidate`. Validate the complete prepared EFI with the
matching OpenCore validator before using it. A root-patch plan does not inject
Mellow into EFI; ensure `-mellowdiag` is present in the actual running boot
arguments while retaining the required Lilu dependency.

EFI-loaded Lilu is not a link input to `kmutil`. Root preflight additionally
requires exactly one existing on-disk Lilu bundle in `/Library/Extensions`, with
bundle contents matching the supplied EFI's disabled reference dependency, plus an
available KDK matching the installed OS build exactly. A missing/mismatched
dependency blocks before root writes. This integration does not silently install
Lilu. OpenCore 1.0.7's `Kernel/Add` path does not supply the bundle identifier
used by its conditional existing-kext check, so matching bytes do not justify
dual injection. See the [caller](https://github.com/acidanthera/OpenCorePkg/blob/1.0.7/Library/OcMainLib/OpenCoreKernel.c#L643)
and [conditional check](https://github.com/acidanthera/OpenCorePkg/blob/1.0.7/Library/OcAppleKernelLib/PrelinkedContext.c#L999).
Native kernel collection and boot verification remain required on the target.

On installed Tahoe, read-only native preflight followed by explicit application:

```sh
python3 -m x86.cli patch --preflight --mode x86 --mellow root-patch --efi /Volumes/EFI/EFI
sudo python3 -m x86.cli patch --apply --mode x86 --mellow root-patch --efi /Volumes/EFI/EFI
sudo python3 -m x86.cli patch --unpatch --mode x86
```

An alternate Mellow manifest directory uses `--mellow-payload`; the existing
`--payload-dir` still refers to the Universal-Binaries support package. GUI
selection propagates the same configuration. Native Mellow mutation requires
the complete worker to run as root; an unprivileged GUI supplies the explicit
CLI command instead of attempting partial privileged copies.

## Root-patch transaction and cache boundary

The selected Mellow hardware patchset supplies `Overwrite Data Volume` entries
to the existing root engine. The bundled `OSBundleRequired=Safe Boot` metadata
is preserved, so it requests KDK and primary kernel collection handling instead
of pretending to be an AuxKC-only patch. Existing SIP, AMFI, FileVault, secure
boot, pending-update, KDK, kernel-cache and APFS checks remain in force.

Before root mounting, live preflight checks the x86 host, Darwin 25, physical
8086:7D41 device, Lilu loading, `-mellowdiag`, and absence of already-loaded Mellow.
The supplied EFI is checked for duplicate injection. A Mellow-only plan uses its
validated absolute source paths and does not require Universal-Binaries.dmg;
other selected patchsets still require their normal payloads.

Data-volume state is journaled under
`/Library/Application Support/26x86/Mellow/transaction`. Backup precedes generic
patch cleanup and file writes. Installed bytes must match the validated payload
before kernel-cache regeneration and snapshot creation. Generic AuxKC cleanup
does not delete or relocate Mellow; its own transaction controls those files.
APFS snapshot reversion alone does not undo `/Library` changes, so unpatch also
restores the Mellow Data files and rebuilds the kernel collection. Unknown file
changes or inconsistent journals stop restoration rather than overwrite them.

An installation receipt records verified files, not GPU execution. Copy, readback,
kernel-cache and snapshot failures propagate to rollback and cannot set a patch
success flag. Recovery of a pending transaction must preserve its backups until
restoration and the required cache work are confirmed.

Apple's [signed system volume description](https://support.apple.com/guide/security/signed-system-volume-security-secd698747c9/web)
explains the System-volume seal; the Data-file journal is a separate 26x86 layer.

## Validation boundary

Run the Python tests with `python3 -m unittest discover -s tests -v` and the GUI
mode tests with `python3 -m unittest x86.gui.test_mellow_gui -v`. Tests exercise
real manifest/Mach-O/hash checks, temporary EFI readback, filesystem transactions,
mode refusal and orchestrator failure propagation. Native APFS/kmutil services
are injected in orchestration tests; this is not a macOS emulator test.

Windows tests cannot establish Tahoe boot, KDK/kernel collection linking, kext
load order, root snapshot bootability, Metal compute/render, WindowServer or
sleep/wake. Acceptance on the target requires boot logs and kernel collection
inspection, then actual device-attributed GPU output/readback and sustained
submission tests. The bundled diagnostic payload reports native Metal, GPU
submission and WindowServer acceleration as unavailable.

The 2026-09-06 local checks are retained in the repository-only
[validation evidence](https://github.com/26x86/26x86/tree/main/docs/validation/mellow-20260906).
They are historical artifact/deployment checks, not current GPU acceptance.
The WSL root ownership test exercises actual UID/GID restoration on temporary
files. The two complete EFI configurations pass the matching OpenCore 1.0.7
validator; this remains a configuration check, not an OS boot result.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](index.md), [progress](progress.md),
[compatibility catalog](compatibility.md) and
[library](library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
