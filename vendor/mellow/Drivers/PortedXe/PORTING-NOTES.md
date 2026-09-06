# Ported Xe page-table subsystem

This directory contains executable source-derived driver algorithms from Linux
`0d9ff90a5422cc7509258aaaba1e7481df4d332a`, not a whole GPU driver.
`provenance.json` records original source URLs, whole-file SHA256, and six exact
function fragments compiled from `XePteAlgorithms.inc`. Original source and MIT
notices remain under `upstream`; the permission text is in `LICENSE.MIT`.

The six functions preserve their upstream bodies. `XePageTable.cpp` supplies
freestanding integer types, three BO-property predicates, and invariant traps.
The public wrappers reject misalignment, excess DMA width, invalid page-table
levels and Xe-LPG PAT indices before entering upstream code. PAT values are
indices only: this code neither picks a cache policy nor programs PAT registers.
The read-only wrapper follows `xelp_pte_encode_vma`'s separate RW-bit policy.

`GgttMapping` ports the system-memory scatter/gather page loop and zero-clear
loop into explicit DMA ownership and PTE-write callbacks. Mapping becomes
`Bound` only after the adapter completes write posting and GT invalidation.
Partial writes or failed invalidation leave `Faulted` and retain DMA pins;
successful clear plus invalidation is required before releasing them. Callers
must reserve a nonoverlapping GGTT range below 4 GiB and serialize access.

The provided tests simulate the MMIO aperture, TLB visibility and DMA leases.
They exercise real production algorithms and failure paths, with independent
fixed and table-driven PTE vectors. The simulator does not execute Xe commands,
firmware, GuC or shaders. A QEMU CPU guest can execute this same test binary but
does not become a 7D41 GPU model.

Hardware use still requires actual pinned IOMemoryDescriptor/IODMACommand
ownership, validated DMA address width, GGTT reservation, real GSM MMIO mapping,
platform-specific write workarounds, completed TLB invalidation, PAT setup,
reset-safe lifetime and integration into a loaded XNU driver. None are silently
implemented as successful callbacks. The default subsystem supplies no hardware
adapter, and no GPU support/Metal claim follows from its host test result.

Build and verify source integrity with:

```text
python Tools/run-ported-xe-tests.py --out /path/outside/repository/new-scratch
```
