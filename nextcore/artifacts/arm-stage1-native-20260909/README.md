# Native stage-1 checkpoint (BP32)

These are authored execution and review receipts, with their original source and
binary hashes preserved. They precede canonical module/root integration and do
not claim normal macOS startup or guest Metal. Reproduce current code using
ISE docs/NATIVE_MMU_PROVIDER_V2.md and EFI docs/ARM_STAGE1_EFI_PROBE.md.

ISE records10 native C/Rust tests,39 service/shared tests,98 reference tests and
158 older captured Arm comparisons, plus semantic negative controls and legacy
regressions. Root moved the updated comparison adapter to
compare_current_walker.py and restored the historical helper bytes; the source
preparation receipt records that relocation. The60 runtime files did not change.

EFI historical binary589d48ea passes108 actual x86 OVMF cases. r1 retained the
original reader; r2 uses strict independent numeric/key validation, role-keyed
input hashes and the final reader. The separate compiled VA-as-PA mutation
is rejected at first fetch (provider unavailable, zero retirements/blocks and
no fabricated ESR/FAR). Build commands used explicit outside-tree source patches;
they are not canonical Git dependency proof. That proof belongs to the later
integration bundle with its own commits and binaries.

Independent review preserves original failures and correction retests. The
trusted callback boundary test deliberately corrupts an acknowledgement after
a store: C rejects the reply without retirement, but cannot undo callback RAM
side effects. completed_data_operations counts validated acknowledgements.
Those host-error runs are not precise resumable guest state.

The separately indexed arm-stage1-oracle and arm-stage1-service-comparison
bundles preserve actual Arm captures, known12 QEMU PC-priority deviations,
354 recorded-value comparisons (322 data plus32 completion-state fetch cases),
74 BTYPE rejections, and a separate78-case actual ERET fetch proof. Read the
capture provenance overlay: completion snapshots are not target-fetch captures,
and HCR/SCR/ABI profile adaptation is explicit. No original OS input was used.
