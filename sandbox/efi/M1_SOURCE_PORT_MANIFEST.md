# Venfire M1 source-port manifest

## Status

**Status: future-only registry; no completed M1 source port is recorded here.**

This file is the required technical provenance and behaviour ledger for a
future M1-only Venfire machine graph. It is not evidence that the current
x86-64 EFI/OVMF host, the `VF_MACHINE_PROFILE_M1_DIAGNOSTIC` (`M1_DIAGNOSTIC`)
Phase-1 policy seed, the AArch64
diagnostic guest, or any existing diagnostic device model is a physical M1,
an Apple virtual-Mac machine, or an iBoot/XNU/macOS-capable platform.

Until an entry has an exact source revision, a bounded guest-visible contract,
and test evidence, its state is `planned`, `in-progress`, or `blocked` — never
implicitly implemented. No entry may use generic QEMU `virt`, qemu-t8030, an
iPhone device tree, a GIC model, or a virtual `soc_name` as an M1 fallback.

## Machine contract rule

The eventual target is **M1-only**. It is one inseparable guest-visible
contract, not a selector string:

```text
M1 machine profile
  |- CPU topology
  |- memory map and RAM ownership
  |- interrupt topology
  |- timer / event contract
  |- MMIO and bus topology
  |- storage and recovery transport
  |- DMA / IOMMU policy
  |- serial and display paths
  |- firmware-visible identity
  |- device-tree / firmware handoff
  `- target-specific boot contract
```

The manifest must classify physical Apple M1/t8103 assumptions, Apple
virtual-Mac guest-ABI assumptions, confirmed source behaviour, inferred
behaviour, and unavailable behaviour separately. A profile mismatch fails
closed; it must not fall back to another Apple SoC, iOS/t8030, generic ARM
`virt`, Windows ARM, or U-Boot target.

## Required component-entry schema

Create one entry for every guest-visible machine or device component before
implementation work starts. Do not replace an unknown value with a plausible
one: use `unavailable`, `not recorded`, or `blocked` and add the experiment or
source needed to resolve it.

```yaml
schema_version: 1
component:
  name: "<unique component name>"
  target_machine_profile: "M1-only"
  guest_visible_purpose: "<what a guest observes or depends on>"

  source:
    project: "<project name or public specification>"
    upstream_repository: "<canonical repository URL or specification URL>"
    upstream_commit: "<immutable exact commit; not recorded until pinned>"
    upstream_file_path: "<path(s), tag, or specification section>"
    source_license: "<SPDX identifier or explicit license statement>"
    provenance_status: "confirmed | inferred | reference-only | unavailable"

  port:
    mode: "direct-port | adapted-port | clean-room-reimplementation | behavior-reference-only"
    venfire_destination: "<repository path(s), or not started>"
    rationale: "<why this mode and dependency boundary are appropriate>"

  guest_contract:
    reset_behavior: "<reset state/order or unavailable>"
    mmio_pio_map: "<base, length, address space, or none>"
    register_layout: "<registers, widths, alignment, reset values>"
    read_behavior: "<read results and error behaviour>"
    write_side_effects: "<state transition and error behaviour>"
    irq_behavior: "<assert/deassert/routing/masking or none>"
    dma_behavior: "<addressing, isolation, failure, or none>"
    timer_behavior: "<clock, events, reset, or none>"
    firmware_visible_identity: "<DT/firmware identity or none>"
    device_tree_acpi_exposure: "<exact exposure, or none>"
    boot_time_dependency: "<ordering/dependency or none>"

  evidence:
    references:
      - "<at least two independent, applicable references when implementation begins>"
    source_trace: "<path/hash/log, or not collected>"
    guest_driver_trace: "<path/hash/log, or not collected>"
    register_differential_test: "<path/hash/log, or not written>"
    venfire_test_evidence: "<test path + immutable result/hash, or not run>"
    evidence_status: "confirmed | inferred | reference-only | unavailable"

  state: "planned | in-progress | runtime-tested | blocked"
  known_gaps: "<explicit omissions; never leave this implicit>"
```

### Port-mode meaning

| Mode | Meaning | Required provenance treatment |
| --- | --- | --- |
| `direct-port` | Upstream source text or structure is materially carried into Venfire. | Pin every upstream file/revision and preserve applicable notices/license obligations. |
| `adapted-port` | An upstream algorithm or state machine is changed for Venfire's static HAL. | Pin the source behaviour and explain every material adaptation. |
| `clean-room-reimplementation` | Venfire is independently implemented from public behaviour/specifications. | Do not copy source; record the behavioural references and differential/architecture tests. |
| `behavior-reference-only` | A source is an oracle/research aid only. | Do not describe it as shipped or ported code. |

## Investigation and evidence rules

For every register-bearing device, record guest-visible address ranges, reset
values, allowed access widths and alignments, reads, write side effects, state
transitions, IRQ conditions, DMA source/destination and failure modes, timeout
behaviour, firmware identity, and boot-time ordering. If a behaviour is
unknown, choose one of the following rather than a success stub:

- obtain a source trace;
- obtain a guest-driver trace;
- add a register-level differential test; or
- return an explicit unsupported failure.

Use at least two applicable reference perspectives before calling a behaviour
confirmed: an architecture/firmware specification, target-specific emulator or
device source, boot-path source, Linux driver/Device Tree binding, TF-A/m1n1 or
public Apple boot evidence, or an actual trace/register capture. Each entry
must identify which evidence is confirmed, inferred, reference-only, or
unavailable.

## QEMU reference boundary

QEMU source can describe specific machine/device behaviour, but Venfire does
not run QEMU as its deployed EFI runtime. A future native machine is expected
to reduce its concepts into static Venfire-owned components, for example:

```text
QEMU MachineState                   -> VfMachine
QEMU AddressSpace / MemoryRegion    -> VfGuestPhysicalAddressSpace / VfRegion / VfMmioRegion
QEMU DeviceState                    -> VfDevice
QEMU IRQ                            -> VfIrqLine / VfInterruptRouter
QEMUTimer                           -> VfTimerEvent
QEMU DMA helper                     -> VfDmaAccess / VfIommuPolicy
QEMU BlockBackend                   -> VfStorageBackend
QEMU reset / realize lifecycle      -> VfMachineBuild / VfMachineReset / VfDeviceStart
```

Do not import or recreate QOM, GLib, QEMU's main loop, coroutines, monitor,
CLI/QMP, generic migration, POSIX host abstraction, generic block layer,
plugin framework, GUI frontend, or QEMU process lifecycle merely to imitate
the upstream API. Capture only the selected guest-visible behaviour and its
tests.

qemu-t8030 is an iPhone 11/t8030/iOS-oriented reference. It can help inspect
individual AIC, ANS/NVMe, DART/SART, UART, NVRAM, USB, framebuffer, reset, DMA,
or recovery-transport semantics after an exact revision is pinned. It is not
an M1 firmware source, M1 device tree, macOS recovery/restore contract, or an
M1 virtual machine implementation. Likewise, generic QEMU `virt` is only a
generic ARM-platform reference; it cannot fill an M1-only manifest entry.

## Phase-1 relation

Phase 1 records no native-M1 acceptance. Its only machine-facing work is a
bounded, fail-closed `VF_MACHINE_PROFILE_M1_DIAGNOSTIC` policy seed and a
diagnostic AArch64 guest executed from the x86-64 EFI application. The M1 machine/device graph becomes
eligible for `in-progress` entries only after the Phase-1 EFI/Rust/JIT path has
its own runtime evidence; iBoot, XNU, and macOS remain separate later gates.
