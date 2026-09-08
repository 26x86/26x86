# BP27 explicit platform profile results — 2026-09-08

Core configuration and the EFI trace caller now expose the optional
`nextcore-irq-compat-v1` software profile through the CPU-owned version2 bridge.
Its complete initial software value is reported separately from hardware reset
claims. An absent profile retains the earlier absent-provider diagnostic.

Five new configuration tests and twenty-five existing ARM placement, DeviceTree
and boot-selection tests pass.
The checks cover unknown profile/option names, unsupported control bits and
field values, PSTATE modes, vector-span bounds, level inputs, duplicate/type
errors and the separate eight/64 instruction limits. Core passes a no-default-
features check. EFI uses the shared `platform.rs` ABI definitions rather than
an independently copied options/result layout.

The incomplete SPTM cold convention remains explicit: x0=0, x1 points to the
staged boot arguments, x2=x3=0. No SPTM argument or service provider, resolved
M1 runtime DT, or original-hardware reset observation is implied by selection.
The firmware DT template gate remains active before guest entry.

Reproduction (after building NXARMJIT with `arm-jit-probe,arm-jit-trace`):

```sh
python3 nextcore/tools/verify_arm_platform_irq_ovmf.py \
  --efi /path/to/NXARMJIT.efi --output /tmp/bp27-platform-cases
```

The authored fixture checks saved exception/vector state and pending levels.
Asynchronous returns do not execute a guest handler; receipts say
`handler_executed=false`. These diagnostics do not establish macOS boot or
Metal acceleration.

The persistent host logs are `/home/sharh/work/bp27-efi/core-tests.log`,
`core-no-std.log` and `efi-default-check.log` in the same directory. The last
check builds the existing x86 EFI default entry without ARM diagnostic features.

The final diagnostic EFI SHA-256 is
`db4bea3aa7ac868b2d75c72f29dcbe390b1939e094e8ce12555ef9ab40c6e0b4`.
It was freshly linked after the CPU provider, logical-immediate and shifted
arithmetic implementations passed their independent runtime tests. The binary
is retained at `/home/sharh/work/bp27-efi/final-target/x86_64-unknown-uefi/release/NXARMJIT.efi`.

`platform-ovmf/report.json` records eight passing actual x86 OVMF cases:
provider read/write, absent provider, rejected unsupported fields, masked pending
levels, override release into EL1t IRQ and EL1h FIQ, and individual PSTATE IRQ/FIQ
unmasking. The tests check saved PC and PSTATE, exact vector selection, preserved
pending levels, unchanged asynchronous ESR, and native-block execution. The EFI
image, fixture sources and harness hashes remained unchanged during the suite.

With the explicit profile and budget64, the unchanged original kernel retired
**26 instructions in ten native x86 blocks**, compared with seven instructions
in BP26. The diagnostic returned status8 after 26.2 seconds. Independent mapping
against the unchanged input identified the next boundary as a standard 64-bit
paired store instruction; this boundary was not skipped or replaced. Original
input, ESP-copy and public source-file hashes all remained unchanged.

Detailed words and execution coordinates remain private in
`_isolated/macos27-j274/efi-original-prefix-r3/report.json`. The exact bounded
argument array is `trace-command-r3.private.json` in that isolated input
directory; `source-inputs.json` beside the report records source hashes before
and after execution. These receipts use the incomplete cold SPTM convention,
an authored diagnostic DRAM tree and a software-defined interrupt profile.

The next ISA work must implement paired memory access with real guest bounds,
addressing/writeback rules and fault behavior before another original run.
Beyond that instruction boundary, native MMU-backed instruction/data accesses,
SPTM arguments and services, resolved runtime platform data, authenticated boot,
device operation and persistent execution state still require their own working
contracts and end-to-end validation. This diagnostic supplies none of those
missing providers and is not an OS boot or stability result.

The same final EFI passed the authored ARM64 and ARM64e/PAC regressions in
`jit-pac-ovmf/report.json`: 25 and45 retired instructions respectively, with
sixteen actual GOP pixels read back per case. A separate selected-profile run
with the original firmware DT again rejected all48 unresolved templates before
TRACE_ENTER. Its private receipt is
`_isolated/macos27-j274/efi-original-template-rejected-r3/report.json`; input and
ESP-copy hashes remained unchanged. No template flag or expression was changed.

After these receipts, review added `platform_abi.h` to the EFI build script's
incremental rebuild dependencies. The recursive local-header audit in
`host-checks/header-dependencies.json` confirms all five transitive headers are
tracked. This build-trigger correction does not rewrite the historical binary
or its source snapshot; the parent integration rebuild validates the final pins.
