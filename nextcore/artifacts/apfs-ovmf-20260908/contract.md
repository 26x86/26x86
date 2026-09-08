# BP24 authored APFS Jumpstart firmware validation

Current: the core read-only extractor and opt-in NXAPFS adapter compile, but
neither has actual firmware execution evidence. Desired: validate the standard
GPT/PartitionInfo/DiskIo/image-service path through the archived BP21 NextCore
BOOTX64, using only independently authored metadata and an authored EFI child.

Decision: create a fresh FAT ESP, OVMF variable copy and synthetic GPT disk for
each case. ESP and APFS share one GPT disk so the boot disk's PartitionDxe
enumerates both children. A fresh qcow2 overlay protects that immutable base.
The APFS partition has 4 KiB blocks, a 1 MiB advertised container,
block-zero NXSB and block-one JSDR. Two non-contiguous extents carry the exact
child bytes, with nonzero padding excluded from the declared file length. This
is extraction metadata only; it is not a mountable APFS filesystem.

The fixture follows the [public APFS reference](https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf)
and the separately recorded independent C offsets in
`../apfs-jumpstart-20260908/contract.md`: NX Jumpstart field 1272, JSDR extents
176. GPT headers and entry arrays use their standard CRC32 checksums. The
authored NXTEST application is copied and only its PE subsystem is changed
from EFI application (10) to boot-services driver (11); its original hash and
the exact byte diff are recorded. No Apple image is modified or included.

Acceptance cases: default inspect succeeds without child entry; explicit start
enters NXTEST, returns SUCCESS and leaves a resident driver, then reports
ConnectController NOT_FOUND because the fixture supplies no DriverBinding;
an unmodified application is rejected before entry; independently corrupted
NXSB and JSDR checksums are rejected; two APFS partitions are rejected as
ambiguous. Exact ordered serial markers, repeated extraction equality, original
input and generated disk hashes, and ESP file readback are required. After QMP
quit the complete guest-visible COW disk is flattened and must exactly match
the generated base before the ESP files are independently read back with mtools.

Each Q35/TCG run has a 30-second budget including TERM/KILL/reap fallback.
After the final parent return marker the harness sends QMP quit and requires
natural exit zero, successful QMP acknowledgement and complete process cleanup.
Unexpected exit, timeout, absent or duplicated markers, and any post-hash read
failure are failures. A receipt is written atomically even after validation or
post-hash failure. QEMU serial output is limited to 2 MiB; child file writes are
bounded to 64 MiB, and each individual fresh image remains below 64 MiB.

Preserved setup findings: QEMU's IDE model rejects a read-only leaf block node;
the accepted run uses a writable fresh COW over the immutable generated base.
A separate non-boot SATA APFS disk was not connected by OVMF BDS before NXAPFS,
so it returned NOT_FOUND. That result is not attributed to a parser defect.
The same-disk fixture requires no production adapter or BOOTX64 change.

UEFI's StartImage may itself connect newly created or modified handles. Only
the adapter's explicit ConnectController request is restricted to the selected
partition; this does not constrain firmware's internal driver dispatch effects.

Scope: this tests EFI discovery, extraction and authored driver lifecycle. It
does not prove APFS mount, original driver execution, installed macOS, native
HAL or guest Metal. Active installer media and all original APFS disks remain
outside this harness. Production source changes belong to root and the core
parser owner; the harness owns only its Python code, tests and this evidence.

Final result: r3 passed all six actual Q35/TCG OVMF cases. QEMU execution took
2.42–2.87 seconds per case, and preparation/readback/hash verification completed
in 3.00–3.52 seconds per case. Nine authored host tests passed. `result.json`
records exact source/image hashes; `r3/` preserves commands, serial logs, configs
and complete per-case receipts. Full independently authored disk/COW images stay
in `/tmp/nextcore-apfs-ovmf-r3-20260908`; they contain no Apple payload. The
archive finalizer separately revalidated markers, process receipts, all stored
output hashes and full-disk equality without restarting any VM.
