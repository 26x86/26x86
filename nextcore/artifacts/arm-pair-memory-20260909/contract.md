# BP28 public EFI pair-memory evidence contract

Current state: the frozen ISE runtime at
`07cd3e19f397556fa6d233c562fb245bfe528363` passed sixteen authored x86 EFI cases
and an explicitly incomplete, bounded original-kernel diagnostic. This bundle
packages that evidence without changing module or parent sources.

Wanted: reproducible authored verification after integration under
`nextcore/artifacts/arm-pair-memory-20260909`. The runner locates the repository,
uses its ISE runtime through the existing build override, verifies the immutable
runtime identity and source hashes, and creates a fresh caller-selected output
directory. It never downloads or executes an original OS image.

The public fixture covers integer paired load/store widths and addressing
modes, value and stack restoration, precise original-SP alignment faults, and
the implementation's permitted UNDEFINED choice for writeback/source overlap.
The existing provider/vector and ARM/PAC/GOP harnesses supply ten regressions.

Review correction: the MMU-off regime uses Device memory, so unaligned pair
elements fault even when SCTLR.A is clear. Add a general-base 64-bit store and
32-bit load with A=0, checking exact ESR, saved destinations/base, SP and
retirement in actual EFI. Keep v2 ABI unchanged: FAR and unchanged RAM are
verified by the separate host native/reference tests, not observed by this
EFI caller. The corrected final runtime identity replaces the superseded one.

Publish only authored checks, reproducible source identities and aggregate
original retirement/block counts plus a generic next instruction family. Do
not include original words, addresses, blobs, private report locations, full
original traces or local host paths. Keep SPTM, runtime-DT, native MMU, OS boot
and Metal limitations explicit. Root retains integration and publication.
