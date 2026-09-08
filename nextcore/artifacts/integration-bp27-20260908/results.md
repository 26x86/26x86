# BP27 integration evidence

The x86 EFI compatibility runtime, independently owned modules and Windows
application cleanup are integrated. Six module PRs passed CI and merged into
main. Their completed task branches were removed only after reachability from
main was verified. The parent PR is checked separately before its merge.

A clean recursive clone of implementation commit `369f1bf4` passed 472 workspace
tests, 73 reference runtime tests, native generated execution and ABI checks,
22 authored x86 EFI cases, 18 independent MMU cases, grant/C-policy comparison,
compiled-EFI packaging and host/EFI Clippy. Python discovery ran 130 tests with
one platform skip. Two previously unrun GUI suites required test-only updates
for deliberately removed endpoints; their 32 tests then passed with one skip.
The earlier full clone remains an exact historical source receipt, not a claim
that its obsolete endpoint assertions passed.

The actual Windows application EXE and Chrome UI have separate cleanup evidence
in `docs/validation/windows-app-cleanup-20260908`. The retained binary, source
snapshot and original/publication hashes identify what was verified.

Original macOS 27 diagnostic execution reached 26 instructions in 10 native blocks.
It still uses an explicitly incomplete startup contract. Native MMU, normal boot
providers, guest handler continuation, stable macOS usage and guest Metal remain
open. AMD host Vulkan evidence does not establish NVIDIA/Intel hardware support.

See `validation.json`, `fresh-integration.json`, module receipts and logs for
commands, scopes and exact hashes. Original firmware bytes are not published.
