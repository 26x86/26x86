# Owned Boot Framebuffer Validation

## Current Status

The opt-in EFI trace path connects encoded ARM64 boot-video fields to owned guest RAM and the current GOP mode. An authored fixture passed nine checks at 1280 by 800 pixels: seven boot-argument loads, two pixel stores, 64 retired instructions, preserved x1, validated geometry and complete GOP RGB readback. The previous EFI without this connection fails the requested display checks. The unchanged headless bitfield-merge consumer still passes with the new EFI.

This is diagnostic firmware output. It is not a macOS desktop, persistent framebuffer service, physical PC result or graphics acceleration. Normal startup remains unavailable.

An actual OVMF run with the VGA device removed reports `TRACE_VIDEO_UNAVAILABLE error=NOT_FOUND` and still completes 64 instructions without a panic marker. The requested video checks fail with CLI exit 1 while CPU diagnostic completion remains true. The final EFI hash is `f6c3ccd08d113ba1325f212abed0f6bb8cb1aa9099b10ba715813fd32f3fa30a`. [Exact authored evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/boot-framebuffer/inventory.json) records the positive, old-EFI negative, headless arithmetic regression and no-GOP cases.

The same local macOS 27.0 / 26A5425a input was replayed with owned video enabled. It again reached 16,384 instructions and 2,763 completed data operations with no provider error. The GOP readback matched the guest buffer, whose RGB hash matched an all-zero frame. This supplies no evidence of kernel-generated visible output or additional boot progress. Only sanitized metadata is public; original traces remain isolated.

## Target State

Provide a non-accelerated display backed by guest-owned memory throughout actual kernel and userspace startup on physical hardware. Firmware-exit lifetime, persistent presentation and the operating system's platform/display contract remain separate acceptance gates.

## Contract and Reproduction

Core reserves page-rounded framebuffer storage after the stack and includes it in allocation bounds and `topOfKernelData`. The EFI adapter reads the current GOP resolution, uses a contiguous XRGB8888 guest buffer and converts through the firmware BLT interface. It does not assume hardware pixel layout or expose the physical GOP aperture to the guest.

The authored assembly reads boot-video address, stride, dimensions, depth, display code and allocation end through x1. It checks their relationships, writes red to the first pixel and blue to the last, and returns a success canary. The host independently computes the expected RGB hash of the entire otherwise-zero frame. Firmware also performs exact RGB byte comparison against GOP readback before writing diagnostic text.

Field provenance is the [pinned public ARM64 boot header](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h). This fixture validates that implemented codec and does not establish the original macOS 27 image's entry ABI.

Build `NXARMJIT` for `x86_64-unknown-uefi` with `arm-jit-deep-trace,arm-jit-video-readback`, then run:

```sh
python3 nextcore/tools/verify_boot_framebuffer_ovmf.py \
  --efi /absolute/path/NXARMJIT.efi --output /new/receipt/directory
```

The host requires Python 3.11 or newer, LLVM tools, QEMU and OVMF. Receipts preserve input and tool hashes, guest execution counters and the distinction between requested video checks and CPU diagnostic completion. A missing, invalid or unsuccessful presentation cannot pass the video request even if CPU execution completes. Source images and private analysis are not used by this fixture.

OPEN_QUESTION: Build Plan: Physical non-accelerated display must survive normal platform startup and the boot-services transition before this can be called a boot display implementation.
