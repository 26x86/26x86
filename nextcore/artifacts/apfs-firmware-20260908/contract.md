# APFS Jumpstart EFI adapter — BP24

Current: the final NextCore picker can enter original Tahoe Recovery through
unchanged Shell/HFS helpers. It cannot yet supply an installed APFS filesystem
provider. Desired: read the disk's opaque Jumpstart driver through standard EFI
protocols and explicitly start it under firmware image policy.

The owning Build Plan recorded BP24 before implementation. `NXAPFS` is an
opt-in application (`apfs-jumpstart` feature), leaving BOOTX64 behavior unchanged.
It selects exactly one GPT APFS partition (type
`7c3457ef-0000-11aa-aa11-00306543ecac`), verifies partition/media geometry and reads
with DiskIo. The core parser validates complete metadata and bounds every read.
Every driver byte and returned metadata field is read and compared a second time,
and media geometry/ID must remain unchanged. This is consistency, not signature
authentication. Original images remain immutable behind fresh COWs.

No-options mode inspects only. The exact UTF-16 load option `--start-driver`
permits LoadImage, boot-services driver type validation and StartImage. Other
options fail. This is a diagnostic API, not EFI Shell command-line parsing.
All disk protocol guards are released and the source device path copied before
LoadImage/StartImage. No parent-owned load-option pointer is passed to the driver.
The firmware copies the source image. A successfully started driver stays resident
and receives an explicit ConnectController call for its selected partition only; a connection
failure remains failure and is not called an APFS mount.

Firmware StartImage can additionally connect newly created/modified handles under
the EFI 1.10 compatibility rule. The whole execution is not confined to the final
explicit controller call. This is confirmed in public EDK2 `Image.c` at commit
`a4610f9cfef179f2013156da9768039f52519f04`, lines 1744–1752; the source also confirms
copied device paths, failed-load handles and driver-error automatic unloading.

Peer review found that diagnostic callbacks ran while disk protocol guards were
alive and that a nullable protocol interface could panic during dereference.
The final adapter reports only after the read helper releases every guard, and
rejects a null protocol interface before use. These are contract/error-path fixes;
neither was an observed original-driver crash.

Sources: [UEFI 2.10 image/driver services](https://uefi.org/specs/UEFI/2.10/07_Services_Boot_Services.html)
sections 7.3–7.4 and the pinned local `uefi` 0.40.0/`uefi-raw` 0.16 protocol
declarations. APFS source/layout/math provenance belongs to the
[core extraction contract](../apfs-jumpstart-20260908/contract.md).
The first UEFI compile rejected a borrowed field of the packed GPT entry;
copying the public GUID value to an aligned local fixed the compile error.
No raw packed reference or protocol-layout cast was introduced.

UEFI LoadImage may return SECURITY_VIOLATION together with a loaded handle. The
adapter keeps and unloads that handle; non-success statuses are not promoted.
Wrong application/runtime-driver types are unloaded before entry. Start failures
retain diagnostics and attempt cleanup; a resident successful driver is preserved
even when controller connection fails. No security variable, image bytes, image
type or callback is altered for original drivers.

Acceptance: independent authored GPT/APFS fixtures in OVMF, exact archive hashes,
configured NextCore-to-NXAPFS dispatch, full extraction/readback, explicit driver
entry/residency, rejection of application/invalid checksum/ambiguous partition,
QMP natural exit and complete cleanup. The authored fixture driver is a copy of
NXTEST with only its own PE subsystem changed to boot driver; it has no APFS
filesystem implementation or DriverBinding, so connection failure is expected.
Original APFS driver execution and filesystem publication require a separate
isolated snapshot run. Neither authored success nor driver entry proves installed
macOS, native HAL or guest Metal.

## Completed original APFS execution

After all six authored OVMF cases passed, the installer owner delegated read-only
use of its completed first-stage snapshot. Two separate fresh COWs retained the
39 GB immutable base and all running installer disks/variables. OVMF first visited
the original disk (empty boot ESP), then fell back to the generated NextCore ESP;
this exposed its APFS PartitionInfo without a global reconnect operation.

Both runs extracted 745,080 bytes from one 4 KiB-block extent and compared every
byte again. Inspection completed in 64.2548 seconds including full input hashing.
The subsequent explicit start returned SUCCESS from the original driver's entry
and ConnectController, then returned through the NextCore parent with its console
lease released. `original-apfs-result.json` records exact durations, archive/source
hashes and complete isolated receipt hashes. Both QEMU and supervisors exited
naturally with zero status, complete process cleanup and unchanged original inputs
and ESP files. Only the completed snapshot was used; the active installer target
and variables were never opened.

The inspection-only run stopped after NXAPFS's result marker; the stronger start
run waited for the parent's image-return marker as well. Both used the same final
r3 EFI archive. No driver bytes were exported to the public tree. Driver entry and
successful controller connection are established; filesystem root access and
installed OS boot still require a subsequent experiment.
