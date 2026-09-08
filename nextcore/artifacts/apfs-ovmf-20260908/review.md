# Independent adapter read review and firmware evidence

Reviewed layer: UEFI PartitionInfo/BlockIO/DiskIo and LoadImage/StartImage/ConnectController.
The r3 source is recorded by SHA-256 in result.json. No production source was
changed by this reviewer. The review found no additional confirmed defect after
the root/peer fixes which release every shared protocol before reporting and
reject a null interface before dereference.

The adapter selects exactly one APFS GPT partition, compares the GPT and media
length, bounds every partition-relative read, repeats complete extraction and
compares all returned metadata and bytes. Its source device path is copied and
disk protocol guards are dropped before image services. Failure statuses stay
failures; loaded failure handles are offered to UnloadImage. The accepted image
must use boot-services code/data memory. A successful resident driver owns its
firmware-loaded image rather than borrowing the source Vec. Explicit connection
targets the selected partition; firmware StartImage can separately connect new
or changed handles, as documented in the root contract.

Final r3 NXAPFS SHA-256:
`234af48bdf5e2fee3cdf48b6a1bd0ea8e51ab557c1742f941f8796852388a0ac`.
Final BP21 BOOTX64 SHA-256:
`8d29af2199999967145cd23145401c342294288366d17b6fcebc6bf02df00e96`.

Six authored OVMF cases passed. Default mode extracted the 29,696-byte child
twice without entering it. Explicit start entered the copied boot driver,
returned SUCCESS and reported resident state, then preserved NOT_FOUND from
connection because the authored child has no DriverBinding. The unmodified
application was unloaded with SUCCESS before entry. Independent NXSB/JSDR
checksum corruption returned VOLUME_CORRUPTED, and duplicate APFS candidates
returned NO_MAPPING. Every case ended by acknowledged QMP quit with natural
zero status, no forced stop and complete process cleanup; original inputs and
the entire guest-visible disk remained unchanged. ESP file readback also matched.

These are actual UEFI outcomes for an authored fixture, not an APFS mount or
original filesystem-driver test. Security-policy rejection, driver error exit,
media replacement during extraction, and malformed firmware protocol pointers
were not injected into OVMF here. Host tests reject missing/duplicated/reordered
markers, wrong byte counts/readback flag, unexpected connection success,
unexpected child entry, crashes including SIGXFSZ, incomplete cleanup and late
hash failures; the failure receipt is still written atomically.
