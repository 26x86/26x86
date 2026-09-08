# Owned guest memory and authored DeviceTree EFI connection

Core f77c98f0 adds exclusive owned or borrowed backing, bounded purpose reservations and owner/generation-bound DeviceTree commit. The host proofs cover stale tokens, whole-capacity overlap, a separate byte-occupancy model, lifetime rejection and UEFI code generation. Arbitrary callback errors do not promise RAM rollback, and the ledger does not authenticate provider semantics.

The authored NXDT firmware allocates real RAM/table/JIT backing and derives placements from ledger records. It serializes an explicit observed-aperture property and consumes the bytes through generated x86 ARM loads/stores with nonidentity 4K/16K mappings. Four positive cases retire16 instructions and complete13 data operations; four invalid-leaf cases fault at the first DT load without retiring it. Every case rejects stale preparation before JIT entry and checks complete RAM plus immutable tables.

`historical-dt` retains the original outside-tree-patched build and actual8-case capture, a separate compiled wrong-mapping failure, assembler proof and original reader bytes. Its initial reader later proved too permissive about the report envelope and host integer bounds. That defect and the corrected reader validation are recorded separately under `review`; historical files are never rewritten or relabeled. Canonical module/parent builds have separate commit and binary identities in the integration evidence.

These are synthetic firmware fixtures, with no original OS inputs or target boot ABI. SPTM handoff, normal macOS27 startup, EFI GPU acceleration and guest Metal remain incomplete. The production sources live in the Core/EFI submodules; this directory contains validation evidence only.
