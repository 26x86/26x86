# APFS Jumpstart extraction contract — 2026-09-08

Status: implemented and source-frozen; core validation passed on 2026-09-08. Root owns EFI integration, independent runtime validation and commits.
Layer: platform-independent, read-only APFS container metadata and opaque EFI file extraction.
The current EFI path cannot discover an installed APFS filesystem by itself. This step supplies bounded driver bytes to a later, separately validated EFI adapter. It does not mount APFS, validate a PE image/signature, call LoadImage/StartImage, or establish installed macOS/Metal success.

## Public sources and boundary

- [Apple File System Reference](https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf), revision 2020-06-22, SHA-256 `74c3db584971aea2b11549ca25799ead824e1bd8994e94cd3f8665ce5aea79cc`: physical ranges pp. 8–9; object header/types/flags pp. 10–21; Jumpstart pp. 22–25; container declaration pp. 27–28; Fusion/version/block-size definitions pp. 33, 37–39. This is the normative format source, including the block-zero discovery path rather than checkpoint traversal.
- [Public checksum description by the apfs.ksy author](https://github.com/cugu/apfs.ksy/blob/84b566c373c9baaf0c486866b7e455e338ee894e/docs/checksum.md), commit `84b566c373c9baaf0c486866b7e455e338ee894e`: supplemental mathematical check-word convention. Apple names Fletcher64 but does not give the check-word formula in its reference. This supplemental source is not an Apple implementation or an independent Apple compatibility result. No source code is copied or linked as a dependency.

All input fixtures and C/Rust implementations in this task are independently authored. No live installer disk, Apple driver, private input bytes, reverse-engineered implementation, or EFI protocol hook is part of this public change.

## API and accepted subset

`ReadAt::read_exact_at(offset: u64, out: &mut [u8]) -> Result<(), Error>` uses partition-relative byte offsets. The caller supplies `partition_len` and a stable, read-only partition view. The adapter must return an error on short read, media replacement, or device failure; the core preserves the error as `JumpstartError::Io`. It cannot detect a reader that falsely reports complete reads or a concurrently changing medium that happens to have consistent checksums.

`extract_jumpstart(&mut reader, partition_len, JumpstartLimits)` returns `JumpstartDriver` with exact file bytes and source geometry/extents. `max_driver_bytes` defaults to 16 MiB and `max_extents` to 1024; these are caller-selected resource policies, not APFS constants. Every individual read is at most one container block. Successful extraction provides no PE, machine-type, authentication, or execution verdict.

The parser reads a 40-byte prefix solely to choose a bounded block-zero read. It permits power-of-two blocks from 4096 through 65536 bytes. This power-of-two restriction is the implemented subset; the published numerical bounds alone are not a proof that every in-range size is supported. It verifies the complete NXSB block checksum and unchanged prefix before using container geometry. The advertised container must fit the supplied partition, with at least the published 1 MiB minimum and checked byte arithmetic.

Version-2 incompatible-feature value `2` is supported. Other incompatible features are rejected, including version 1. Fusion is rejected when indicated by its incompatible bit, low-capacity feature, or nonzero Fusion UUID/metadata references. Unknown optional and read-only-compatible feature bits do not enable filesystem operations and are ignored for this read-only extraction.

NXSB/JSDR object types and subtype zero are checked; encrypted, headerless, nonpersistent, invalid storage-type combinations and unknown object flags are rejected. NXSB is a copied superblock, so its object identifier is not equated to block zero. JSDR is physical and its object identifier must match the referenced block. Transaction identifiers must be nonzero. Reserved JSDR bytes are not required to be zero because the reference requires preservation when reading existing instances.

The JSDR must have magic/version 1, nonzero bounded file length and extent count. Its entire extent table must fit within the checksummed block. Signed physical addresses must be nonnegative, and Jumpstart address zero means no driver. Each nonempty extent must fit the advertised container and supplied partition without overflow. The complete table is checked before any driver data read, including extents after the file-length boundary. Checked aggregate capacity must cover the declared file length. Only the required prefix of the concatenated extents is read; allocation padding and surplus capacity are excluded from output. Driver bytes have no APFS metadata checksum in this contract.

All buffer allocations use fallible reservation. A failed read or validation returns no partial driver. No public mutable plan can redirect already-validated reads. No filesystem write API is exposed.

## Layout and checksum cross-check

`layout_fixture.c` restates public field declarations for `sizeof`/`offsetof` only; Rust uses explicit little-endian byte reads rather than casting disk bytes to native structs. Expected sizes: object header 32 bytes, physical range 16 bytes, published NXSB prefix 1408 bytes, JSDR prefix 176 bytes. The C output is the independent offset receipt used before implementation.

Fletcher64 consumes 32-bit little-endian words after the first eight checksum bytes. With modulus `M = 2^32 - 1`, running sums are `s1 = sum(words) mod M`, `s2 = sum(prefix sums) mod M`. Stored low/high check words are `M - ((s1+s2) mod M)` and `M - ((s1+low) mod M)`. The zero residue after appending both check words is checked independently. The C fixture computes the second sum by positional weights rather than the Rust recurrence. All-zero and carry-heavy cases, 4 KiB and 64 KiB blocks, plus checksum-field exclusion are checked.

## Acceptance

Focused self-authored tests cover ordered multi-extent extraction, partial final block, checksums, geometry and signed-address errors, table truncation, limits, overflow, insufficient capacity, malformed trailing extents, Fusion and unsupported versions/flags, I/O failure and no out-of-range callback. Independent C layout/checksum output, no_std build and relevant host checks must pass. EFI execution and real APFS input validation remain separate root-owned follow-up work.

## Completed evidence

- `layout-receipt.json`: GCC 13.3.0 C11 with `-Wall -Wextra -Werror`, all four structure sizes, 24 offsets and four checksum vectors/zero residues passed. In particular `nx_flags=1264`, `nx_efi_jumpstart=1272` (`0x4f8`), and `nej_rec_extents=176` (`0xb0`). An initial conversational offset estimate confused the first two fields; no production code used that estimate.
- `validation-receipt.json` and `check-1.log` through `check-4.log`: rustfmt check; 23 authored tests against the actual core with default features disabled; core no_std check for `x86_64-unknown-uefi`; exact owned source/test copies in a dependency-free no_std crate under strict Clippy `-D warnings`, all passed. Hashes before/after and of the lint copies match.
- Unscoped core Clippy initially reported 19 pre-existing arithmetic style diagnostics in other modules. The receipt records this separately; those files were not modified. A retry excluding those two lint categories also passed, but the exception-free owned-module gate is the scoped strict-lint evidence.

Reproduce C evidence on Linux with `python3 verify_layout.py --work-dir /tmp/nextcore-apfs-jumpstart-check`; reproduce Rust checks with `python validate.py` from a host with the UEFI target installed. These helpers preserve logs and use a temporary build directory for independent lint. They do not read any actual APFS image. The core crate gains no dependency.

Frozen source ownership: `crates/nextcore-core/src/apfs_jumpstart.rs`, `crates/nextcore-core/tests/apfs_jumpstart.rs`, and the one-line `lib.rs` export. The opaque output remains separate from driver validation, secure loading, controller connection, filesystem discovery and OS boot evidence.
