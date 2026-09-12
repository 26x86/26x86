# Authored mapped Normal-NC profile evidence

## Current Status

The latest EFI evidence is **r5**, using the final pinned EFI build. The earlier r4 EFI evidence remains unchanged in `efi-r4/`; native evidence is r4. All 10 aggregate EFI checks pass. Each of the cached, uncached and unobserved mapped runs retires 65,536 instructions and completes 26,207 data operations. Status 5 is diagnostic budget exhaustion, not successful operating-system startup.

The authored program checks a physical boot-argument read, high virtual addresses, unaligned Normal-NC loads/stores, XPACI and disabled PACDA. Cached and uncached execution and the last 64 ordered memory observations agree; removing observation preserves execution. Actual protection transitions are 28 writable/27 executable for cached and unobserved builds, versus 65,537/65,536 for uncached. The final writable restoration accounts for the difference of one.

Native r4 compares nine authored cases in cached, uncached and small-slot modes, including CPU state, result, RAM and ordered service requests/replies. It also passes 20 M0 regression tests and 125 pointer-authentication assertions. The independent QEMU oracle exposes APA5, while this runtime profile uses APA1/software QARMA5. Sixteen enabled sign/auth vectors and 24 XPAC/disabled vectors are compared; **eight upper-address enabled sign/auth vectors remain unverified**. This oracle mismatch must not be presented as full enabled PAC coverage.

The old EFI negative control lacks the required mapped acknowledgements and is rejected by the host acceptance gate. It actually executes an M0 trace; this is not evidence of an EFI configuration parser rejection.

`efi/receipt.json` and `native/receipt.json` preserve the complete aggregate receipts. Per-mode reports, commands and serial logs preserve authored OVMF evidence, including original line endings. Receipts retain local provenance paths and source/binary hashes. Native source verification compares receipt hashes with working files and committed Git blobs. Native executable hashes are recorded separately; executable payloads are not included. The inventory in `summary.json` hashes every other file in this directory.

No proprietary kernel, original-image bytes or original execution capture is included. **Physical boot, macOS startup, original-entry ABI, persistent platform services and the actual computer display remain unverified.** These authored checks do not establish forward progress of the original kernel or general firmware compatibility.

## Target State

Validate the original entry contract and remaining PAC coverage before extending original-image execution. Keep authored checks, original-image metadata and physical boot evidence distinct. A normal startup claim requires separate evidence on the intended hardware, including persistent storage, input and display.
