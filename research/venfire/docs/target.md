# Target and intermediate boot evidence

The final user target is original ARM64 macOS 27 Golden Gate booting and
functioning from a 26x86 USB on the user's AVX2 Intel computer. The permitted
private developer host flag bypasses only the Apple platform check. Production
retains the genuine Intel Mac requirement. A synthetic guest, Linux USB host,
original iBSS prompt or older macOS guest cannot replace that final acceptance.

Apple's official release index, checked on 2026-09-06, lists macOS 27.0 beta 8
build `26A5425a`, released 2026-08-31:
https://developer.apple.com/news/releases/.
The current SDK/release notes are published at
https://developer.apple.com/documentation/macos-release-notes/macos-27-release-notes.
The attached design's beta 3 reference is an earlier snapshot, not a requirement
to accept an older or unverified build as the final result.

The current bring-up uses the user's original Monterey 12.6.1/21G217 firmware
because the pinned upstream QEMU VMApple device ABI explicitly targets 12.x.
This establishes original secure boot and device behavior before porting later
Virtual Mac ABIs. It does not reduce the requested target or prove that macOS
27 will accept this platform unchanged. Final target restore manifests, firmware,
kernel, virtual GPU protocol, install/update and hardware acceptance must each
be verified from actual inputs and execution.

Mac Pro 2009 is outside the required AVX2 floor. The current development host is
the user's Intel AVX2 Windows computer, with Linux/TCG in WSL for experiments.
No attached physical USB has been selected, written or booted. Current OVMF
USB tests prove the image's emulated UEFI/Linux path, not that hardware result.
