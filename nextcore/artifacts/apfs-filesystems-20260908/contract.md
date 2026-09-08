# BP24-B: bounded filesystem observation

Current: archived NXAPFS r3 extracts the original container's 745,080-byte
Jumpstart driver twice, starts it and receives ConnectController SUCCESS in
root's isolated COW experiment. That is not yet proof of OpenVolume or directory
reads. Desired: observe those standard UEFI filesystem operations on handles
whose device paths are strict descendants of the selected APFS partition.

Decision: preserve absent options and `--start-driver` behavior. The new exact
UTF-16 option `--inspect-filesystems` first performs the existing driver start
and connection sequence, then enumerates SimpleFileSystem handles. A path must
be a single-instance sequence of complete device-path nodes, ending in the
canonical four-byte EndEntire node. The selected partition's complete non-end
node sequence must be an exact prefix, with at least one additional child node.
The ESP, siblings, unrelated disks and equal parent path do not qualify. No
global filesystem count is interpreted as an APFS volume count.

Limits: at most 256 SFS handles examined, 32 matching volumes, 2,048 bytes and
64 nodes per device path; root only (one directory level, no recursion or child
file open); 128 records per volume and 512 records globally; 4,096 bytes per
Read/GetInfo response and 1 MiB of metadata responses globally. The loop reserves
one additional Read to prove EOF at the exact entry cap; a nonempty extra
record fails the limit. Reported UTF-16 names/labels are bounded to 255 code
units and escaped to printable ASCII. File names must be a single nonempty
component, without separators, ASCII C0/DEL control characters, malformed surrogate pairs,
or dot/dot-dot traversal tokens. Dot records are counted but not emitted as
paths. Canonical reported paths are root plus one validated name; labels are
data, never paths. C1 characters are permitted only as escaped data (for example
`\u0085`); the logger never emits them as control characters. Duplicate canonical
entry names and device paths fail.

Use the standard SimpleFileSystem.OpenVolume and FileProtocolV1.GetInfo/Read/
Close ABI from uefi-raw 0.16.0. Fixed aligned response buffers are validated by
returned count, declared size and bounded NUL before any string conversion.
No unbounded flexible-array conversion is used. Null protocol/root interfaces
fail. Every root is explicitly closed, with RAII cleanup on early return; Close
failure is preserved. All protocol guards and roots are released before calling
the logging callback. Logs retain completed observations and explicit failures;
partial results do not become overall success. No Write, SetInfo, Delete,
SetPosition, child Open or boot entry call exists in this mode.

Public contracts: [UEFI media access protocols, chapter 13](https://uefi.org/specs/UEFI/2.11/13_Protocols_Media_Access.html)
and [device-path protocol, chapter 10](https://uefi.org/specs/UEFI/2.11/10_Protocols_Device_Path_Protocol.html),
cross-checked against the locally pinned uefi 0.40.0/uefi-raw 0.16.0 declarations.
The web renderer returned HTTP 403 for these pages; local binding source remains
available for exact ABI and layout verification. A separately authored C layout
probe and Rust offset assertions verify variable-string field offsets.

The 2 KiB/64-node bound applies to the new filesystem classification phase.
It uses raw OpenProtocol rather than the binding's unbounded DevicePath DST-size
walk. The pre-existing driver LoadImage path still uses its established trusted
firmware DevicePath contract and is unchanged by this step.

Acceptance: authored path/record/limit negative tests, strict UEFI build and
no-dependency lint, unchanged six prior OVMF outcomes plus the new mode's honest
NOT_FOUND for a fixture without DriverBinding. Actual positive OpenVolume and
root reads belong to root's separately controlled original-disk COW experiment.
Neither authored tests nor original directory observations prove bootability,
installed OS launch, native HAL or Metal. Original filenames and raw actual
volume logs remain isolated; public evidence contains only authored data and
aggregate outcomes. No active installer input is used by this subtask.

Final validation: 7 authored Rust parser tests, 9 Python evidence tests, the
independent C layout probe, release UEFI link and no-dependency clippy with
warnings denied passed. The archived r1 passed all seven authored OVMF cases,
including the six prior outcomes. `result.json` records source hashes, commands,
complete cleanup, immutable inputs and guest-disk/ESP readback; `ovmf/` retains
the raw authored logs. The new mode's positive original-disk observation was
performed independently by root and is recorded in `original-result.json`:
four scoped volumes opened and verified, four records/eight Reads, all EOF and
Close results successful, with immutable-input hashes and normal QMP cleanup.

The tested archive remains SHA-256
`1e63c89b5426a2a9d589ee3ffcc93db4c0f8d79a8a1c828d01fea4e5ce5ec725`.
The final C1 regression only adds test code excluded from the EFI application.
Relinking changed PE/debug timestamps and the CodeView GUID; an initial strict
whole-file comparison failed and is preserved in `rebuild-metadata-failure.json`.
`verify.py` parses those PE/debug locations and proves every other byte,
including the entire .text section, identical. It records both hashes without
modifying either binary. The actual-tested r1 image is preserved as the release
artifact; a later build hash is not substituted for its execution evidence.
