# APFS EFI adapter independent review — 2026-09-08

Layer: UEFI protocol access, image loading and driver lifetime. Read-only review; the core extraction implementation and its receipt remain frozen. Initial adapter SHA-256: `152f1318ae616d27fba328b4d9ac034e50ca0565d35c88f5d2bf1ddd21724b74`.

Two bounded corrections were sent to the owner before final integration:

1. `inspect` invokes its report callback while GET_PROTOCOL guards and shared firmware references remain live on extraction error and success. A safe function pointer can perform registry-changing calls; the current callback also opens Serial exclusively. Move diagnostic text/result construction out of those borrowed scopes before invoking the callback, so the stated no-removal/reconnection lifetime condition does not depend on the callback's implementation. This is a source-contract issue, not an observed OVMF use-after-free.
2. `ScopedProtocol<DevicePath>` can have a null interface. Implicit dereferencing for `to_boxed()` panics instead of returning a firmware error. Use `get().ok_or(Status::UNSUPPORTED)?` before making the owned copy. The installed APFS partition's ordinary device path is expected to be non-null, but the public API explicitly permits this failure case.

The local pinned uefi 0.40.0 `src/boot.rs` (protocol access safety, `ScopedProtocol` optional interface and `Deref`/`Drop`) provides the first-party crate contract. Its [published protocol-access documentation](https://docs.rs/uefi/latest/uefi/boot/index.html) states the distinction between exclusive access and unsafe protocol access. No crate source was copied into NextCore.

The [official EDK2 image services implementation](https://github.com/tianocore/edk2/blob/a4610f9cfef179f2013156da9768039f52519f04/MdeModulePkg/Core/Dxe/Image/Image.c), pin `a4610f9cfef179f2013156da9768039f52519f04`, confirms these relevant behaviors:

- `CoreLoadImageCommon` copies both file-path representations; a caller-owned path need not remain borrowed across driver execution. It also documents that SECURITY_VIOLATION can return a valid loaded-image handle. Preserving and attempting to unload that handle is appropriate; a cleanup failure is reported rather than treated as successful reclamation.
- `CoreStartImage` unloads a driver returning an EFI error. The adapter's later UnloadImage can therefore see an already-invalid handle; this outcome is diagnostic cleanup, not successful driver start. The accepted BOOT_SERVICES_CODE/DATA pair excludes applications and runtime drivers from this explicit subset. Successful driver residency is intentional.
- The EFI 1.10 compatibility path automatically connects newly created or changed handles before driver StartImage returns. The adapter's explicit final ConnectController is restricted to its selected partition and loaded driver handle, but that does not restrict the complete effects of StartImage or of the external driver to one controller. Do not claim a global single-controller isolation property.

No additional confirmed blocker was found in partition-relative range/MediaId forwarding, fallible parser output handling, owned DevicePath copying, LoadImage status preservation, image memory-type gating, or deliberate success residency. This review does not prove firmware authentication policy enforcement in a particular OVMF build, APFS driver behavior, filesystem discovery or installed macOS/Metal boot. Runtime reports remain separate.

## Owner correction recheck

Re-read adapter SHA-256 `d9a270d8345e12bf3703fe9c03d1a7aeebc7b9c47c0c050fbfd46fbcd88fe894` after the owner corrections. Both findings above are resolved: the new `read_driver` helper returns only after all protocol guards are dropped, and `inspect` then reports; `read_protocol` now rejects a missing interface through `get().is_none()` before returning any guard, covering the nullable DevicePath case. No additional confirmed source blocker was found. This is a source/lifetime recheck, not a substituted runtime test. Root and the firmware harness owner retain integration and runtime-test ownership.
