# BP29 scalar memory execution in x86 EFI

Current: scalar runtime commit8b09f8764f13838baf71c1676575cb829bcd7902 has native
and reference tests, but this contract independently runs it inside x86 OVMF
using the existing root NXARMJIT trace binary. Desired: reproducible authored
width/sign, Device alignment, SP alignment, and unsupported-encoding results
observed through the EFI C JIT, with exact immutable source hashes.

Root explicitly delegates this bounded build and verification. All authored
sources, build outputs, ESPs and receipts remain under this external directory.
No root/module source, dependency pins, metadata, Git index or original Apple
asset is changed/read. Build uses NEXTCORE_PREOS_RUNTIME pointing at the frozen
scalar worktree and a new persistent CARGO_TARGET_DIR, with existing root EFI.

Use existing trace_arm_jit_ovmf and independently authored short Mach-O fixtures
within its64-instruction bound. Cover all13 valid integer size/opc forms,
32-bit destination clearing, signed values and SP/ZR/overlap where practical.
Add explicit Device A=0 read/write alignment, SP alignment, and SIMD/reserved
rejection. Expected register values and retirement boundaries are supplied
independently by the verifier, not derived from runtime status assertions.

Assert only actual EFI-exposed status, ESR, X0-X3, SP, PC, retired instructions
and native compiled blocks. EFI does not expose FAR or post-fault RAM here;
those belong to separate host proofs and are not claimed. Positive readback can
show successful memory effects through guest loads. QEMU emulates an x86
computer; ARM instructions execute through NXARMJIT's native x86 generator.
This is not physical hardware EFI, macOS boot, SPTM services or guest Metal.

Deliver reusable public assembly/Python sources, explicit build/run commands,
source/output hashes and actual serial/results with a failing negative control.
Public bundle excludes generated ESP/firmware images and source assets from
other projects; their observed hashes remain in provenance. Root owns integration
and publication after the complete authored result is reviewable.
