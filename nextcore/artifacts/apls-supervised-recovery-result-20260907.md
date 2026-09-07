# BP15 supervised normal-recovery result

Layer: Windows Nextcore host adapter -> Linux recovery supervisor -> QEMU
VMApple firmware observation.

The first actual `tcg-recovery` adapter run completed in 48.365 seconds and
returned Nextcore exit code 2 (completed but boot unverified). The supervisor
reported no deadline or cancellation, correlated the raw QEMU PID with one
observed process in the worker's Linux session, reaped the leader and all
observed descendants, and left no recorded PID behind.

Observed recovery progress:

- DFU upload completed.
- The iBEC endpoint, Stage2 banner, and Stage2 prompt were observed.
- Five distinct restore roles completed transfer.
- The restore sequence was sent and `bootx` was acknowledged.
- Firmware panic was observed after `bootx`.

All 15 declared inputs, including the AUX and root paths resolved from the VM
JSON, had complete matching pre/post fingerprints. The supervisor worker exited
0, but no XNU execution, target kernel major, or macOS userspace evidence was
observed. `macos_boot_verified` is therefore false.

The full bounded host receipt is in
`apls-supervised-recovery-host-20260907/adapter.json`. Exact invocation paths are
kept in that local receipt. This result does not establish macOS boot.

An independent post-run summary and the host receipt hashes are in
`apls-supervised-recovery-independent-check-20260907.json`.
