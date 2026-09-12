# Independent Arm page-hierarchy oracle

Current Status: authored guest source and bounded host runner. A successful
receipt proves only the recorded QEMU Arm execution cases.

Target State: independently discriminate baseline hierarchy permissions before
using these observations to qualify the NextCore native and reference walkers.

## Primary contract

The owning repository Build Plan records the baseline table-permission contract.
The independently inspected Arm-authored DDI0596 ID121321 (2021-12) algorithms
are `S1ApplyTablePerms` (PDF3071), `S1HasPermissionsFault` (PDF3051), `S1Walk`
(PDF3076-3077) and `S1Translate` (PDF3064-3065). Local PDF SHA256 is
`756449b122fa43ff55d81be5e889451bc8c7ba8576ad4a877b91c77b8675e349`.
The [official landing](https://developer.arm.com/documentation/ddi0596/2021-12)
was opened but did not provide extractable text; the local PDF's original
download URL is not established. No copyrighted PDF or pseudocode is packaged.

The [official QEMU virt documentation](https://www.qemu.org/docs/master/system/arm/virt.html)
defines `virtualization=off` and `secure=off` as disabling the corresponding
CPU extensions. The runner also requires actual CurrentEL and PFR0 readbacks.
Its exact installed QEMU version and binary hash are recorded, rather than
treating the current documentation as proof of an installed binary's behavior.

## Controls and comparison boundary

| Item | Actual authored Arm setting | Comparison scope |
|---|---|---|
| CPU | TCG `max`, version/hash and MMFR0/MMFR1/PFR0 recorded | Feature ID values are not asserted equal to the NextCore model |
| Entry | CurrentEL=1; no EL transition in the startup path | EL0 accesses use ERET, then SVC or abort returns to an explicit EL1 label |
| EL2/HCR | Virtualization disabled; PFR0 EL2 field must show absent | HCR is not read, and absence is not a zero-readback claim; no HCR.RW adaptation |
| EL3/SCR | Security extensions disabled; PFR0 EL3 field must show absent | SCR is not read, and absence is not a zero-readback claim |
| 4K | T0SZ=T1SZ=16, TG0=0/TG1=2, EPD1=1, L0 root | Admitted 48-bit VA profile controls; only TTBR0 addresses execute |
| 16K | T0SZ=T1SZ=17, TG0=2/TG1=1, EPD1=1, L1 root | Admitted 47-bit VA profile controls; no fabricated 16K L0 coverage |
| PA | IPS=5 (48 bits), except kind8 IPS=2 (40 bits) | Both IPS values are admitted; kind8 explicitly tests descriptor OA bit44 beyond configured 40 bits |
| Memory | MAIR=0x44, SCTLR=0x30d00801, descriptor SH=00 | Normal-NC, profile3 alignment setting; no HA/HD/HPD/WXN/PAN enabling |
| TTBR | Actual aligned TTBR0 readback, TTBR1 explicitly zero | No ASID, upper-half or stage-2 claim |
| Updates | Break target root entry, DSB/TLBI/DSB/ISB, rebuild, make and repeat barriers | Fresh per-case context; no unsafe live table mutation or software-cache proof |

Every row records the actual TCR/SCTLR/TTBR0/MAIR, leaf and all existing table
descriptors before and after access, ESR/FAR/ELR, memory result and authored
continuation PC. Faults must match EC/FSC, WnR, target VA and instruction PC;
failed stores cannot change the data word or return instruction. Exact row
identity/order prevents missing or duplicate cases from satisfying the count.

## Cases

The full 16 leaf-AP/parent-AP combinations execute EL0/EL1 read, write and fetch.
Additional rows discriminate leaf/table PXN and UXN, restrictions split across
ancestors, identical restrictions moved to each admitted ancestor, and deeper
invalid-descriptor, AF=0 and out-of-range-output faults despite a restrictive
ancestor. This gives 156 4K and 150 16K cases, 306 total. The return instruction
is independently assembled from `ret`; no private binaries are used.

The host's small independent expectation matrix is checked against actual
guest execution results. NextCore code is neither linked into the guest nor
used to generate its observed answers. Reusers should compare the raw captured
outcome fields, not merely copy the host expectation function.

This oracle covers final level3 pages and cold contexts. Supported block leaves,
upper TTBR1 addresses, warmed software caches, profile1 alignment and transactional
cross-page stores remain separate native/reference/EFI tests. It does not prove
physical hardware boot, XNU startup, userspace or a persistent display.

Run on a Linux host with LLVM and QEMU installed:

```sh
python3 runtime/tests/hierarchy_oracle/run.py --output /tmp/hierarchy-arm-new
```

Each run requires a new output directory and copies its exact source inputs.
The QEMU group is terminated and reaped within a bounded deadline. Raw RAM,
registers and process receipts remain available when a completed expectation
fails. Earlier development captures are not silently replaced by a final run.
