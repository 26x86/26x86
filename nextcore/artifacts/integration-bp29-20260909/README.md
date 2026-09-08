# BP29 recursive integration evidence

A fresh recursive checkout of `d45b107deb384278ee9efaaa471a66d1a6d3008b` passes the full
integration driver. The changed ISE and EFI PRs both passed their final CI jobs
and merged into their independent main branches. Completed module branches were
deleted only after ancestry checks. No other module source was copied into the
parent repository.

The suite passes 472 workspace tests, 91 architectural tests,
39 authored x86 EFI cases, 158 captured ARM fault comparisons, the existing
18 granule/physical-width oracle cases, native scalar/PAC/IRQ/pair/ABI checks,
Vulkan and Python/GUI boundaries, compiled firmware packaging and Clippy.
The scalar EFI test here uses the newly built integrated binary; its hash is in
validation.json. The earlier scalar bundle and original 64-instruction prefix
use their separately identified historical binary and are not relabeled.

report.json preserves every command, exit status and duration. Captured reports
retain their original paths as provenance. The comparison tool and standalone
oracle sources are in the pinned ISE module. firmware-scalar/report.json
preserves all actual register, syndrome and retirement assertions.

An initial remote Linux GUI job completed all GUI tests but failed artifact
finalization with an intermediary HTTP403. Its complete job and annotation
receipt is preserved; the failed job was rerun without source changes. Final
publication checks are assessed against the final PR head separately.

Native SCTLR.M, normal macOS startup, usable desktop and guest Metal remain
incomplete. The original prefix is a diagnostic with missing SPTM/platform
providers; reaching its configured budget does not identify a failing opcode.
