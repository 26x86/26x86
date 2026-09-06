> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# Experiment protocol

Experiments are small, falsifiable, and ordered by dependency. They never use a
successful boot or visible display as a proxy for acceleration. All hardware
results in this initial document are **UNVERIFIED**.

## Required record template

Copy this block for every run and commit the completed record separately from
the implementation change:

```text
Experiment ID:
Date/time and operator:
Current goal:
Target hardware (CPU, physical PCI ID/revision, firmware):
Software (macOS build, kernel, OpenCore, driver-bundle versions):
Mellow commit, artifact URL, and SHA-256:
EFI commit/hash and boot arguments:
Classification (diagnostic/workaround/feature-limited/prototype/etc.):

Hypothesis:
Basis:
Counter-evidence:
Validation method:
Expected result:
Pass boundary:
Fail boundary:
Abort/recovery boundary:

Change made:
Build result:
Execution result:
CPU fallback excluded by:
Raw evidence paths and hashes:
New problem found:
Actual result (PASS/FAIL/INCONCLUSIVE/NOT RUN):
Next action:
Regression risk:
Git change unit:
```

`INCONCLUSIVE` is the correct result when positive evidence is missing. The
absence of an error message is not a pass.

## Safety protocol

Before any Mellow-enabled boot:

1. Preserve a known-good EFI and verify an OpenCore entry that omits or disables
   Mellow. Keep physical access or a separately tested remote/serial path.
2. Record a Mellow-disabled baseline with `Tools/collect-mellow-logs.sh`.
3. Change only the kext/artifact and documented boot arguments. Do not combine
   WhateverGreen or unrelated graphics patches during isolation.
4. Do not enable `-mellow7d41timings`, `-mellowfullmtl`, forced completion, or
   other aggressive diagnostics unless the experiment explicitly tests one of
   them and has a rollback plan.
5. Never issue arbitrary MMIO writes or use `/dev/mem`. A read requires a cited,
   generation-appropriate register definition; a write additionally requires a
   reviewed rollback and timeout.
6. Abort on panic, GPU hang, visual corruption, repeated timeout, loss of input,
   or loss of the recovery channel. Reboot the known-good entry and collect logs
   before making another change.

Diagnostic output may contain serial numbers and private paths. The collector
uses restrictive permissions, but the operator must review/redact output before
sharing it.

## E0001 — physical PCI identity, BAR0 mapping, and driver-load boundary

**State:** `NOT RUN`; all expected target results are **UNVERIFIED**.

**Classification:** diagnostic bring-up. Passing E0001 does not demonstrate
GPU initialization, rendering, command submission, QE/CI, or Metal.

### Hypothesis

On the `8086:7D41` / family 6 model `0xB5` target, Mellow reads the physical PCI
identity before the OpenCore `9A49` spoof, admits the expected CPU/GPU pair,
loads only the requested Apple TGL framebuffer path, and obtains a valid BAR0
mapping without a panic or out-of-range access.

### Basis and counter-evidence

- Source review shows a physical PCI configuration read and a CPU/GPU allow-list
  in `MellowCore::processPatcher`.
- Source review shows BAR0 mapping through `mapDeviceMemoryWithRegister` and
  explicit failure logs.
- OpenCore properties can make IORegistry report the spoofed ID, so IORegistry
  alone cannot establish the physical ID.
- The source emits a dedicated, read-only `E0001 BAR0 mapped` marker containing
  the mapped length plus `PWR_WELL_CTL1` and `DC_STATE_EN`. This is source
  evidence only; until that exact marker is captured on the target, the MMIO
  subtest remains **UNVERIFIED**.

### Preconditions

- Known-good recovery boot has been tested immediately before this run.
- CI artifact and exact SHA-256 are retained; build provenance is known.
- OpenCore contains `device-id=499A0000` and
  `AAPL,ig-platform-id=0000499A` at `PciRoot(0x0)/Pci(0x2,0x0)`.
- Use only the minimal diagnostic arguments:

  ```text
  -MellowDebug -mellowtglfb mellow-dmc=skip
  ```

  `mellow-dmc=skip` bypasses Mellow's compatibility profile but passes through
  Apple's initializer; it does **not** promise that the driver performs no MMIO
  writes. Do not use the panel-timing or full-Metal arguments.

### Procedure

1. From the known-good Mellow-disabled boot, collect a baseline:

   ```sh
   sh Tools/collect-mellow-logs.sh mellow-e0001-baseline
   ```

2. Record the EFI hash, Mellow zip/kext hash, Apple TGL bundle versions, macOS
   build, and exact boot arguments in an experiment record.
3. Boot the isolated Mellow entry. Do not continue if the system panics, hangs,
   corrupts the display, or loses the recovery channel.
4. If the system remains responsive, collect the candidate data promptly:

   ```sh
   sh Tools/collect-mellow-logs.sh mellow-e0001-candidate
   ```

5. Compare the baseline and candidate `metadata.txt`, `ioreg-*.txt`,
   `kmutil-showloaded.txt`/`kextstat.txt`, `system-profiler-displays.txt`,
   `mellow-unified-log.txt`, and `key-lines.txt`. Retain the directories and
   their `SHA256SUMS`.
6. Reboot the known-good entry once more. A failure to return to it is an abort
   and recovery failure, regardless of earlier observations.

### Expected data

- A Mellow log reporting family `0x6`, model `0xb5`, physical vendor `8086`,
  physical device `7d41`, and an enabled `7D41` branding path.
- IORegistry data showing the IGPU at PCI `00:02.0`, along with the injected TGL
  properties. The physical-ID log and injected property must be recorded as
  distinct facts.
- `Mellow.kext` and the requested Apple TGL framebuffer visible in loaded-kext
  output or an equivalent authoritative load record.
- The exact `E0001 BAR0 mapped len=... PWR_WELL_CTL1=... DC_STATE_EN=...`
  marker with a non-zero length. Capture two boots and compare the bounded
  reads; do not improvise another register offset during the run.
- No panic, invalid CPU/GPU-pair log, BAR0-map failure, or out-of-range-access
  report.

### Pass/fail boundaries

E0001 has three independently reported subresults:

| Subtest | PASS | FAIL | INCONCLUSIVE |
| --- | --- | --- | --- |
| `E0001-P` physical identity | Mellow's pre-spoof PCI log is `8086:7D41` and CPU model is `0xB5`. | Gate reports another identity, rejects the pair, or matches only through injected data. | Required log is absent or truncated. |
| `E0001-D` driver load | The exact Mellow artifact and requested TGL framebuffer are authoritatively shown loaded, with expected init logs. | Wrong/duplicate graphics stack, load error, panic, or Mellow remains inactive. | Only IORegistry naming or a visible display is available. |
| `E0001-M` BAR0 mapping | The exact positive marker shows a non-zero BAR0 length and the two approved reads are captured on two boots without a fault. | Map failure, null virtual address, bounds failure, machine check, panic, hang, or non-repeatable invalid reads. | The exact positive marker is absent or truncated, even if no failure line appears. |

The overall result is `PASS` only if all three pass and the known-good recovery
boot still works. Any fail makes the overall result `FAIL`; otherwise it is
`INCONCLUSIVE`.

### Next minimum experiment

After E0001 passes, add one read-only, generation-cited GPU status/heartbeat
observation and prove it changes or remains stable as predicted. Do not proceed
directly to WindowServer or Metal patches. Command submission begins only after
reset, force-wake, and mapping evidence is reproducible.
