# Unsupported optional TCR controls: authored acceptance evidence

This bundle records rejection of TCR_EL1.HA, HD, HPD0 and HPD1 (bits 39 through 42) by the bounded software model. It contains authored receipts and text logs only. No original Apple input, executable binary, downloaded manual, or physical boot claim is included.

## Results and counting

- Current C register API: 160 assertions, zero failures; all 15 nonempty optional-bit combinations in both MMU states are exercised.
- Rust register-bank harness: 102 tests passed.
- Direct MMU harness: 102 tests passed. These two harnesses include overlapping baseline tests; they are not 204 unique new tests or hardware cases.
- Canonical service acceptance: all 15 combinations rejected in profiles 1 and 3 and the dynamic service, both granules. “Zero accepted” in the receipt means the all-zero optional-bit combination is admitted; it does not mean that the positive baseline is rejected.
- Nearest full service regression: 44 tests passed. Nearest pre-OS regression: 115 tests passed. These suites also overlap harness coverage and must not be summed into a unique-case total.
- The UEFI-target check completed compilation successfully. This is a real target build/check, **not EFI execution**, an OVMF run, physical boot, or macOS startup evidence.

## Historical controls

`old-control/receipt.json` reports success of a negative-control experiment, not success of the old implementation: the same rejection expectations detect 60 C assertion failures and failures in both Rust optional-control fixtures on old source. Its service guard already rejects the optional modes. Nonzero test exit codes are intentional and retained.

`independent-old-api/receipt.json` separately captures the older direct API acceptance/readback bug on immutable baseline 778473fd9c43d7ba3a4721852f838be996fed45d. This is an authored API observation, not native instruction execution or proof of hardware AF/dirty updates or hierarchy-disable behavior.

## Provenance and limits

The current and old receipts are copied byte-for-byte and preserve their source/test SHA-256 maps, commands, process exit/reaping fields, and scope declarations. Text logs are unchanged, including warnings and expected failures. Scratch absolute command paths describe acquisition and are not prerequisites for interpreting results. Use the committed module's `runtime/tests/verify_optional_tcr.py` with its documented arguments to reproduce the scoped fixtures; the receipt command arrays preserve the exact observed compilation and execution invocations.

`manifest.json` lists byte counts and SHA-256 for every payload file, including this README. `manifest.sha256` binds the manifest itself. Packaging verifies every copied byte against its source and then rechecks the full payload inventory. The standalone regression logs show test/compiler completion but do not independently contain the richer process lifecycle fields of the native runner receipts.

This patch does not implement MMFR1 reads, hardware AF/dirty management, hierarchical-permission disable, or SCTLR CMOW/TIDCP/SPAN/EPAN semantics. Normal installed-macOS startup and physical-machine display remain unverified.
