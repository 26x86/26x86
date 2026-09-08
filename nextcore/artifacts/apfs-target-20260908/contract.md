# BP24-C explicit APFS boot target

Current: the actual original APFS driver publishes four scoped SFS volumes and
BP24-B opens, reads and closes their roots successfully. The production picker
currently loads configured EFI paths only on its own filesystem. Desired: let
a configured picker entry select one APFS volume and load its exact EFI file
through the same firmware application lifecycle.

Decision: add optional string `Misc.Entries[].ApfsVolume`, mapped to
`BootTarget.apfs_volume: Option<String>`. Absence preserves the existing own-volume
path. Presence is an exact, case-sensitive Unicode label with no normalization,
1..255 UTF-16 code units, no control characters or path separators, and no
leading/trailing whitespace. This is an explicit label selector, not a trusted
identity or a path. Bad types/values are rejected even in disabled entries, as
with existing known fields. The EFI capability is opt-in at build time through
`apfs-jumpstart`; selecting an APFS entry in a build without it fails UNSUPPORTED.

Only the selected entry triggers extraction, repeat readback, validated EFI
driver loading/start and connection. Scope remains exactly one APFS GPT logical
partition. Enumerate at most 256 SFS handles, accepting only bounded strict
device-path descendants; inspect at most 32 qualifying volumes. Read bounded
FileSystemInfo from each open root, compare its validated original UTF-16 label
exactly, close every root/protocol before image loading, and require exactly one
match. Zero matches returns NOT_FOUND and multiple matches NO_MAPPING. Do not
pick the first ambiguous label, silently fall back to another volume, or infer
bootability from directory contents.

Append the already validated absolute configured Path as a public MEDIA_FILEPATH
node to an owned bounded device path. Preserve all existing application-type,
load-options ownership, ConsoleControl, ExitData, return and cleanup behavior.
Handle firmware LoadImage error handles without losing them; preserve the actual
authentication/error status. Release all protocol borrows before LoadImage or
StartImage and keep owned path storage alive for the LoadImage call. No driver
or booter bytes are included in the public source tree.

Root owns the Core configuration parser and its tests plus Build Plan/validation
integration. The x86 firmware agent owns the EFI adapter and actual authored
firmware regression. Root owns positive original-disk execution using a new COW
only after the installer owner identifies an immutable completed snapshot.
Original labels/paths may be supplied in isolated runtime configuration; public
code does not hard-code or infer vendor boot paths. No source disk or security
policy changes are part of this step.

Acceptance: parser compatibility/boundary tests; strict UEFI link build; authored
firmware selection, failure and lifetime checks; exact original configured path
load/start observation with hashes and cleanup. Booter entry, target XNU,
installed userspace and guest Metal remain separately adjudicated observations.
