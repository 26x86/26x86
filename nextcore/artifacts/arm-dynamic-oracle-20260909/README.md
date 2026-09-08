# One-way MMU enable: independent actual Arm oracle

The strict run passes six authored cases on QEMU 8.2.2's AArch64 max CPU: successful enable, absent next code page, and absent data page, each with 4 KiB and 16 KiB granules. Eight host-reader regression tests pass. Two separately compiled semantic negative controls are detected; each intentionally breaks its two success cases while retaining the four fault cases.

The controller enters EL1h by actual ERET with SCTLR.M=0/A=1/C=I=0, MAIR0x44, HCR.RW-only, stage2 disabled and DAIF masked. The 4 KiB regime uses T0SZ=T1SZ16 and an L0 root. The 16 KiB regime uses T0SZ=T1SZ17 and an L1 root. All used table pages are explicitly zeroed first; each page base and every nonzero descriptor are captured. The EL2 controller resets controls between independent cases; this is not a claim that the one-way guest profile supports clearing M.

The final eight bytes of an identity-mapped granule contain MSR SCTLR_EL1, X0 then exact ISB SY. Immediately after ISB, sequential fetch crosses the page boundary to a different physical page. Its first instruction reads SCTLR, its second records the actual virtual PC, and subsequent scalar operations load and store through data VA0x60000000 mapped to a different physical address. A nonzero seed, a different store operand, a preexisting canary and actual physical readback distinguish translated execution from direct physical access.

The successful path also executes DSB SY, local TLBI VMALLE1, DSB SY, ISB, and a second data read. Because the mappings are immutable, that result does **not** observe hardware TLB eviction or refill. Native canonical-service table-reader counters are a separate form of evidence.

For a missing immediate post-ISB code page, actual EL1 instruction abort reports ESR0x86000007 and FAR/ELR at that next VA. For a missing data page, actual LDR reports ESR0x96000007, FAR0x60000000 and ELR at the translated code VA+8. No data write occurs before either failure. Normal and exception paths return to the EL2 controller through HVC; ESR/FAR/ELR/SPSR and final controls are read from architectural registers.

The first negative binary replaces the actual enable MSR with NOP only in the success cases. The MMU stays off and the physical next page executes a distinct terminating decoy, with marker0xbad and unchanged data. The second negative omits the actual next-page descriptor and takes the precise instruction translation abort. The ordinary positive comparator rejects these results. The negative verifier requires each exact intended observation and exact failed-check set, preserving the other four cases; missing output, a crash, a wrong control or an unrelated failure cannot count as detection.

## Reproduce

Python3, Clang, LLD, LLVM objdump and qemu-system-aarch64 are required. Keep the seven source/contract/reader files together and choose a new output directory:

    python3 /path/to/bundle/probe_enable.py --output /path/to/fresh-enable-oracle
    python3 /path/to/bundle/test_reader.py --oracle-run /path/to/fresh-enable-oracle

The captured directory contains the strict execution report, three actual authored ELFs and logs, command records and payload disassembly. The reader tests can also be run directly against captured. The report preserves all source hashes before/after, ELF hashes, captured sparse tables/controls, exact observations and expected values. No production implementation is imported or used to calculate expectations.

The initial local fixture used the wrong 16 KiB root width (T0SZ16 with an L1 table); the 16 KiB vector fetch timed out. Its source/debug output remains separately preserved outside this public bundle. The corrected fixture explicitly selects the intended 47-bit/L1 regime before these passing executions. This was a test-harness configuration error, not a Nextcore runtime finding.

## Scope and architectural basis

[Arm's Address Translation guide, sections3.4 and4.2](https://documentation-service.arm.com/static/5efa1d23dbdee951c1ccdec5) explains the common mapping needed for the next instruction and the post-ISB guarantee; its granule diagrams distinguish the 16 KiB root width. [Arm's barrier explanation](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/memory-access-ordering-part-3---memory-access-ordering-in-the-arm-architecture) explains the separate synchronization operations.

The checks begin after the first ISB. They do not assert when the implementation applies the MSR before that barrier. Actual hardware may make the new mapping effective early; the shared physical mapping keeps the transition safe either way. This proof covers one independent software Arm CPU model. It does not execute physical Arm hardware, the generated x86 JIT, EFI, dynamic service callbacks, an original OS image, or guest Metal. No Apple asset or original trace is used.
