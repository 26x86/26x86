# BP28 integration evidence

ARM64e integer pair operations now execute in the x86 EFI JIT with bounded
RAM access, precise alignment faults and success-only writeback. GPU UUID
selection and eligible noncoherent memory flow through the separately owned
GPU/APLS/Tool modules. Five module PRs passed CI and merged into main; their
completed branches were deleted after source reachability was proven.

A fresh recursive clone of implementation commit `41aa5d95` passed 472
workspace tests, 77 reference runtime tests, native generated execution and
C/Rust ABI checks, 28 authored x86 EFI cases, 18 independent MMU cases,
the pair oracle, 119 Vulkan tests, grant/C-policy differential checks, compiled
EFI packaging and host/EFI Clippy. Python discovery ran130 tests with one skip;
the explicit GUI boundary suites ran25 with one skip. Required opt-in C-policy
and compiled-EFI checks were run separately. Raw commands/results identify
this exact implementation base; final receipt-only publication has its own CI
and canonical network clone check.

Independent review caught MMU-off Device alignment missing when SCTLR.A=0.
The corrected ISE source and failing restored-bug control are in the companion
`arm-pair-memory-20260909` evidence. QEMU omits that Device rule and SP alignment;
these are specification-based native/reference and EFI checks, not claimed
QEMU confirmations. EFI observes ESR/registers/SP/retirement, while host probes
also inspect FAR and unchanged RAM.

The unchanged original diagnostic reaches47 instructions in10 native blocks
and remains explicitly incomplete. Native MMU, normal boot providers, stable
macOS use and guest Metal remain open. RX6800XT hardware evidence stays in the
GPU submodule; NVIDIA/Intel and physical noncoherent allocations remain unverified.
