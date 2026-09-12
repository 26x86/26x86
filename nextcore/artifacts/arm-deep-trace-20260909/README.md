# Explicit deep ARM diagnostics on x86 EFI

Merged Corebab7/EFI03a/Tool8ea retain ISE0d and the existing parser/default limits.
The deep feature and exact deep-16384 selector opt into a longer diagnostic.
Parent tools trace_deep_arm_jit_ovmf.py, verify_deep_budget_ovmf.py and the authored
three-instruction assembly are promoted byte-for-byte from the corrected freeze.

Fresh recursive6bca2907 passes14 targeted commands: workspace505, Python149,
Core no-default235+3doctests, memory service44, package and Clippy checks, actual
debug NXAPFS, and the full deep-control gate. That gate executes four cases from
the new workspace binaries and one separately compiled canonical clamp binary:
16384/4096/64 counts, tiered-only configuration rejection before entry, and actual
clamped4096 semantics. Twenty-eight preflight rejections and a copied x1
corruption are separate host controls. This targeted suite follows BP34's full
53-command200-EFI suite; it does not relabel unchanged old executions as new.
The unchanged full CI jobs remain, with an additional actual deep1/CLI28/x1 job.

Canonical module receipts resolve published Git dependencies without workspace
patches. The first canonical control supplied a non-trace binary, which stopped
at PROVIDERS_PENDING/NOT_READY rather than the required TRACE_CONFIG_INVALID;
that strict control failed and its receipt is retained. The corrected tiered-only
input passed without changing code or predicates. The independently compiled
clamp changes only the two execution-call budgets; its configuration and build
markers stay deep16384. Actual counts/readback detect the reduced execution.
Historical outside-tree Core/EFI/ISE and binary identities remain separate from
current canonical and fresh integrated results. Initial reader findings and
corrected provenance/CLI/x1 checks are retained without rewriting old receipts.

The historical original diagnostic ran once using the earlier frozen binary.
It reached5311 retired instructions,5312 native fetches and783 completed data
operations, then stopped at an independently classified64-bit UBFM/LSL-immediate
unsupported boundary. Its aggregate contains no original coordinates or bytes.
Different prior runtime/dispatch versions prevent block-count path/performance
inferences. This does not supply normal SPTM arguments/services or a platform DT,
and does not establish normal macOS boot, a usable desktop or guest Metal.

Raw receipts, serials and authored input bytes are preserved. EFI binaries,
build caches and ESP/firmware disks are omitted, with their hashes retained.
Historical absolute paths are provenance. Reproduce current authored execution
with the parent tools and explicit --tools/--core-source/--efi-source paths. Full
five-case mode needs separate actual tiered-only and clamped binaries;
--recheck-provenance runs one actual deep case plus28 CLI and one x1 control only.
