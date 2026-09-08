# NXARMJIT integration review

Reviewed the ARM EFI caller, shared ARM handoff placement, firmware page owner,
C boot-JIT bridge, and GOP lifetime while the Rust compiler download proceeds.

- MemoryAttributeProtocol RX check: the previous shared helper incorrectly
  required RO clear. The EFI agent had already corrected it to require RO set and
  XP clear; the latest source was refreshed and confirmed. No duplicate edit.
- GOP readback backing storage: the caller used [u8;64], whose Rust type has
  alignment one. The GOP helper's pinned contract requires alignment four. The EFI
  owner added a repr(align(4)) wrapper; latest source confirmed the correction.
- Host Boot Services remain active across native JIT execution and GOP calls.
  There is no ARM guest ExitBootServices operation applied to the x86 host.
- Guest entry/boot-arguments/stack addresses are guest physical values separate
  from retained host allocations. The staging slice is bounded inside 64MiB RAM.
- Success requires actual returned registers, boot-argument RAM output, guest-written
  framebuffer bytes, GOP transfer success and pixel readback. No XNU/macOS/Metal
  completion is inferred from the independently authored guest fixture.
- Native code pages are returned to writable/NX before normal owner destruction.
  Both GOP entry points preserve all nonzero firmware statuses.

This is source review and native C validation, not a Rust build or OVMF result.
The EFI owner integrates and records execution evidence separately.


Runtime relocation: root moved the freestanding EFI/JIT sources, including
gop_scanout.c, gop_scanout.h and test_gop_scanout.c, into
nextcore/crates/nextcore-ise/runtime/. Prior sandbox/efi paths above record the
implementation location before that move. Source hashes were rechecked unchanged.
