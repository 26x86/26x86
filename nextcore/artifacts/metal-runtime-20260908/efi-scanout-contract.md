# x86 EFI guest framebuffer scanout contract

Current: NXARMJIT can execute ARM instructions on an x86 EFI host. Its forthcoming
independently authored guest fixture writes a 4x4 XRGB framebuffer using guest STR
instructions, at an offset selected by the caller. No C helper currently submits
that framebuffer to GOP. Desired: copy those exact guest-generated pixels to the
firmware display through the public synchronous GOP Blt operation.

The GPU agent owns sandbox/efi/gop_scanout.h, gop_scanout.c and native protocol tests.
The ARM EFI agent owns NXARMJIT linking, calling and OVMF guest execution. A separate
preOS Rust module is deferred to avoid duplicate C/Rust address validation and the
ongoing ISE relocation. This C implementation is freestanding and allocation-free.

API: vf_gop_present(bs, guest_ram, ram_bytes, offset, width, height, stride,
                    destination_x, destination_y) returns an EFI_STATUS.
The caller owns readable guest memory and serializes guest execution with copying.
The helper validates nonzero width/height, four-byte-aligned offset/stride/base,
width <= 8192, height <= 8192, stride >= width * 4, and checked last-row bounds.
No pointer offset occurs before validating integer ranges and pointer overflow.
The accessible source span is (height - 1) * stride + width * 4; last-row padding
is not read by the GOP buffer contract. The input is little-endian XRGB8888, whose
B,G,R,reserved byte layout equals EFI_GRAPHICS_OUTPUT_BLT_PIXEL.

LocateProtocol selects the firmware default GOP. No mode change, arbitrary PCI
register access, DMA or native GPU command submission occurs. Mode metadata must
exist and have the public minimum structure size; dimensions and pixel format are
validated before the destination rectangle. PixelBltOnly is supported because the
Blt API provides the transfer. Blt receives sourceX/Y=0, caller-selected destination,
width, height and the actual source byte stride as Delta. Its exact nonzero status
is propagated; only EFI_SUCCESS is scanout completion. No guest IRQ/fence or Metal
capability is synthesized. Boot Services must remain active for this call.

Tests: a mock GOP implements the standard Blt byte copy into a guarded framebuffer
and records all inputs, enabling independent colored pixel, padding and destination
checks. Invalid ranges/metadata must avoid the Blt callback; firmware locate/blit
errors and warnings are preserved. Compile under Clang ASan/UBSan and separately as
x86_64 COFF freestanding code. Actual OVMF output is a separate integration result.

Public ABI source (UEFI spec fetch returned HTTP 403):
https://raw.githubusercontent.com/tianocore/edk2/edk2-stable202408/MdePkg/Include/Protocol/GraphicsOutput.h
The public UEFI 2.11 console protocol chapter is:
https://uefi.org/specs/UEFI/2.11/12_Protocols_Console_Support.html

The matching vf_gop_readback entry point uses the same checked buffer contract and
EfiBltVideoToBltBuffer. It provides actual firmware readback for independent pixel
checks. Both functions explicitly use the x86 EFI/MS ABI. Source/destination stride
span is additionally bounded to 256 MiB for one transfer.


Runtime relocation: root moved the freestanding EFI/JIT sources, including
gop_scanout.c, gop_scanout.h and test_gop_scanout.c, into
nextcore/crates/nextcore-ise/runtime/. Prior sandbox/efi paths above record the
implementation location before that move. Source hashes were rechecked unchanged.
