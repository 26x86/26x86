# BP32 captured Arm operations versus canonical memory service

The comparison retains the frozen original428 observations. Of them,354 fit the service profile and compare architectural result, fault kind/level, FSC, ESR and FAR. The other74 carry saved BTYPE0x800 after an actual BLR; their exact PSTATE is preserved and the current service rejects them as INVALID_REQUEST. They are not counted as architectural matches. The original12 QEMU PC-priority contradictions and A0 negative control remain separate and excluded.

A new78-case authored ERET-entry oracle covers those74 fault cases plus4 valid RET controls. Actual EL2->EL1 or EL1->EL0 ERET restores SPSR with BTYPE0; no captured state is masked. Every saved SPSR is checked. Its normal/negative executions have new ELFs, table addresses, source hashes and receipts. The real negative binary aligns the first normally misaligned target, removing its PC alignment exception. The service comparator also changes exactly one expected observed ESR bit and requires comparison failure while keeping the actual execution unchanged.

## Exact inputs and documented adaptation

TTBR0/1, TCR, MAIR, SCTLR, upper table addresses/first entries, second-page entry, target VA, access and origin SPSR come from actual logs. Data-operation PC comes from the log's printed instruction-label address and is checked against the captured ELF symbol and original instruction word. Fetch PC is the target VA. Scalar and pair widths/counts use the exact authored selected A64 instructions.

Controls80 is an adapted service record, not a byte-exact original hardware snapshot. ABI version2/size80/profile1/epoch1 are adapter metadata. Captured HCR must equal RW-only0x80000000: VM, TGE and all other bits must be zero. Only then is it represented as inactive HCR0 because this service models EL0/EL1 without EL2. SCR0 is also an inactive profile field; the EL2 harness did not capture SCR_EL3, and no equality is asserted. PSTATE is never masked.

ELF symbols identify original tables/code/data arrays, each64KiB. The original authored C explicitly clears every array each case. Captured upper descriptors are restored without modifying their values. Uncaptured lower code-table entries are separately reconstructed from the original authored assignments and ELF symbol addresses. The full tables+code arrays form immutable128KiB table backing; writable RAM is exactly the original64KiB data array. The authored RET is placed at data+0x230 only for fetch cases, exactly as the fixture does. Stores use XZR/WZR; successful load data is zero. Faulting block cases fail before ordinary backing is consulted; no extra backing or replacement mapping is invented.

The comparison's RAM-unchanged check uses those exact zero/store-zero fixture bytes. It is not a sensitive partial-store corruption test; the independent native provider suite uses nonzero canaries for that guarantee. Native x86 JIT execution, Win64 EFI ABI, physical Arm hardware and original macOS boot are not exercised by this service-only replay.

## Replay

Use Python3, Rust1.98.1 (or a separately recorded supported compiler), canonical ISE runtime source including sibling preos files, and the saved authored oracle inputs/ELFs. Choose a fresh output directory. Example:

```sh
python3 replay.py --oracle-kind original428 --oracle-run /path/to/oracle-original --oracle-elf /path/to/oracle-original/normal.elf --runtime /path/to/ISE/runtime --output /path/to/fresh-original
python3 replay.py --oracle-kind eret78 --oracle-run /path/to/oracle-eret --oracle-elf /path/to/oracle-eret/normal.elf --runtime /path/to/ISE/runtime --output /path/to/fresh-eret
```

To rerun the new actual Arm oracle itself, `python3 oracle-eret/probe_operations.py --output /path/to/fresh-oracle` requires clang, ld.lld and qemu-system-aarch64. The captured replay pins the recorded inputs/ELF by SHA256; a new compiler-built oracle may have different addresses and hashes, and must not silently replace the frozen capture.

## Capture phase qualification

Of the354 original-record comparisons,322 are data operations and32 are successful target fetches. Those32 save SPSR at the later authored SVC after RET; their recorded BTYPE0 is a completion snapshot, not a direct capture at BLR target entry. Replaying the recorded request values compares translation/result behavior but does not prove that the original at-target BTYPE state fit the service profile. The74 faulting target fetches save the actual fault-site BTYPE0x800 and remain exact INVALID_REQUEST rejections. No captured PSTATE was masked or rewritten.

The separate new ERET78 proof establishes BTYPE0 at target entry by actual SPSR/ERET setup and checks its subsequent saved state. Existing execution receipts and frozen oracle bytes are unchanged. See `capture-provenance-overlay.json` for the32 affected names and receipt hashes.
