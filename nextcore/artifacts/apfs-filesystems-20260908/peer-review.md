# BP24-B root review

Reviewed the raw protocol adapter, pure byte parser, option transition and
authored OVMF harness separately from their implementer. The new mode preserves
the prior extract/start path and does not continue after failed connection.

- DevicePath uses a raw GUID lease, fixed four-byte node headers and a bounded
  owned copy. No uefi DevicePath DST conversion occurs before bounds validation.
  Pointer readability remains the live firmware ABI trust boundary.
- SFS handles qualify only by exact complete parent-node prefix and at least one
  additional node. Equal paths and siblings are excluded; duplicate qualifying
  paths fail. Protocol and root leases end before the reporting callback.
- FileInfo and FileSystemInfo use aligned fixed buffers and returned-size checks
  before declared-size/NUL/UTF-16 conversion. No child Open or filesystem write
  is used. Every observed root has explicit Close and protocol Close outcomes.
- The per-volume/global entry caps allow a further Read only to prove EOF;
  nonempty data at the cap fails. The authored tests cover Budget boundaries,
  while the original runtime independently demonstrates ordinary EOF handling.
- Clarified the name contract: C0 and DEL are rejected; C1 is printable escaped
  data. This was a documentation precision issue, not a change to firmware code.

The original-disk COW run of archived r1 independently confirmed four scoped
volumes, root metadata, four records, eight directory Read calls, all EOF and
all Close statuses. Parent console cleanup, return, natural QMP exit and nine
input hash comparisons passed. See original-result.json; raw paths and logs are
isolated. No installed OS, native HAL or Metal result is inferred.
