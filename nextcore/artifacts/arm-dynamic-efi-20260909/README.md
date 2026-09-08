# Actual one-way MMU activation on x86 EFI

Six authored NXDYN cases execute generated x86 code with the canonical dynamic
C/Rust service: 4K/16K roundtrips, missing immediate post-ISB fetch, and missing
data page. The success cases retire15 instructions, fetch15, and complete5 data
operations; revision2/epoch2 and one invalidation are observed. Faults retire3
and preserve the precise ESR/FAR/ELR/SPSR boundary. Separate owned RAM, table and
JIT allocations, entire expected RAM, immutable tables, control events and final
acknowledged service state are checked. The six cases record58 fetch/data and40
control events. Thirty malformed capture controls reject.

The separately compiled omission actually leaves M=0 and reaches the original
unsupported HVC decoy: status8, retired3, blocks/fetch4, data0, control2 and
unchanged RAM. A crash or unrelated failure is not accepted as this negative.

Historical release proof uses Coref77 and an outside-tree workspace patch,
ISE0d722886 and consumer SHA f3a18707e53f0b112dfc195327a6b0ef8bf0ae51408679e40799b0c1c6bb2394.
Its source/binary/runner hashes and original receipts remain unchanged. The
canonical integrated EFIed9 uses Core147's UEFI software hash backend; its fresh
build/execution evidence is published separately in the integration bundle.
Historical expanded command paths describe that run; use current module tools
with a newly built binary to reproduce firmware execution.

The report reader binds the raw serial digest and ordered six-case envelope,
recomputes every expected field and rejects malformed or forged success. Replay:

    python3 check_dynamic_capture.py --report historical/ovmf-serial-bound/report.json --output /path/to/new-reader.json
    python3 check_dynamic_omission.py --report historical/ovmf-negative-serial-bound/report.json --output /path/to/new-omission.json

The independent Arm oracle and captured native comparison are separate bundles.
Only one-way M0-to-M1, fixed controls, immutable tables and one CPU are covered.
No hardware TLB refill, exception-handler execution, normal macOS boot or guest
Metal is established by these authored results. No original Apple input is used.
