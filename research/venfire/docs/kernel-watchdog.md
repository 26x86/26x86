# Original XNU watchdog: a virtual timer mismatch

The confirmed fault crosses the **virtual ARM timer → XNU clock conversion →
IOKit power-management watchdog** layers. In recovery experiment 021, both
QEMU CPU objects reported a 1,000,000,000 Hz counter, while the original running
XNU used 24,000,000 Hz and a Mach timebase of 125/3 nanoseconds per tick. Guest
time therefore advanced 41.6667 times faster than QEMU virtual time. This is a
concrete hardware contract mismatch, independent of whether graphics or a
secondary CPU is also incomplete. It does not establish that correcting the
timer alone completes boot.

The machine-readable evidence is [kernel-watchdog.json](../evidence/kernel-watchdog.json).
The guest is `xnu-8020.240.7~1/RELEASE_ARM64_VMAPPLE`, from the original Monterey
12.6.1 restore assets. Original firmware, DeviceTree and kernel files were read
only. This investigation used QMP memory reads and original Mach-O comparison;
it wrote no guest memory, changed no instructions, and left the watchdog enabled.

## Frequency provenance and original instructions

The original `DeviceTree.vma2macosap.im4p` matches the official BuildManifest's
**DeviceTree** SHA-384. Its compressed payload expands to a 58,476-byte Apple
DeviceTree, SHA-256
`01c07ac12b45086e351fa1933ec554c3d5ca961e0ef5bfc3b452f4709acdac5e`.
All 32 CPU template nodes contain `timebase-frequency = 24000000`. That template
node count is not the configured or online CPU count of experiment 021.

In Apple's related public XNU source, `PE_init_platform` receives `boot_args`,
initializes the supplied DeviceTree, and calls `pe_identify_machine`. The latter
reads `timebase-frequency` from the running CPU node into the platform clock
description. The standard restore command line used here has no frequency
override. The live `boot_args.deviceTreeP` was not captured, so the evidence
does not claim byte-for-byte identity between the template and iBoot's final
DeviceTree. The observed runtime frequency agrees with the original template.
[Apple platform initialization](https://github.com/apple-oss-distributions/xnu/blob/27b03b360a988dfd3dfdf34262bb0042026747cc/pexpert/arm/pe_init.c),
[Apple DeviceTree clock discovery](https://github.com/apple-oss-distributions/xnu/blob/27b03b360a988dfd3dfdf34262bb0042026747cc/pexpert/arm/pe_identify_machine.c).

The original exported `absolutetime_to_nanoseconds` implementation loads the
frequency global at runtime address `0xfffffe0024b30000`; the captured value is
24 MHz. `clock_timebase_info` returns the adjacent 125/3 fields. In the watchdog
callback at `0xfffffe0022ab583c`, the original instructions read `CNTVCT_EL0`,
add the per-CPU offset, and compare against the stored deadline without a
frequency correction. All 248 captured callback bytes exactly match the
original kernel Mach-O. QOM independently reported `cntfrq = 1000000000` for
both `max-arm-cpu` instances.

## What the panic actually identifies

The saved callback owner is an `IOPMrootDomain`: its vtable matches the original
exported symbol. The saved counter `0x21e80cfff99` exceeds its deadline
`0x21e7cf116f1`, so the observed callback followed an expired-deadline branch.
Its blocked-service array has zero members. The power-management workloop's
preserved stack includes an ARM exception/AST scheduling path and a saved PC
at the original exported `IOService::requestPowerDomainState + 0x180`; the
interrupted instruction is ordinary power-domain code, not an identified
device-acknowledgement wait.

The related public PM layout describes the current request as
`RegisterPowerDriver` and machine state as `kIOPM_Finished`. Those two field
interpretations use related source, not exact-build debug types. The owner,
deadline and empty-array offsets are independently checked against original
instructions. Apple's available source tag is **8020.140.41**, rather than
the exact guest **8020.240.7**. In that public file the panic is near line
12569; the guest's original panic metadata reports `IOPMrootDomain.cpp:12600`.
[Apple PM watchdog](https://github.com/apple-oss-distributions/xnu/blob/27b03b360a988dfd3dfdf34262bb0042026747cc/iokit/Kernel/IOServicePM.cpp#L5740),
[Apple panic callback](https://github.com/apple-oss-distributions/xnu/blob/27b03b360a988dfd3dfdf34262bb0042026747cc/iokit/Kernel/IOPMrootDomain.cpp#L12563).

CPU1 remains at its reset PC in the captured state, the fixture lacks an Apple
PV graphics implementation, and the console contains two early IOResources
registration errors. These are separate observations, not demonstrated causes
of this panic. The platform pointer is nonzero at the panic, and the registration
message itself does not identify a GPU failure. This old fixture also lacks
the later runtime virtio root/AUX devices. The timer must be corrected before
attributing its accelerated watchdog expiry to one of these other gaps.

## Smallest meaningful follow-up

Use `-cpu max,pauth-qarma5=on,cntfrq=24000000`, keep the original guest payloads
and trust checks, and capture the QOM frequency, XNU timebase, PM request progress
and console again. Compare actual counter progression with QEMU virtual time;
a changed printed frequency by itself is insufficient. Then isolate secondary
CPU startup, runtime storage and graphics as separate experiments.

There is a smaller remaining timer precision issue in the pinned QEMU:
`gt_cntfrq_period_ns` computes an integer `1000000000 / frequency` period.
At 24 MHz this becomes 41 ns, or about 24.390244 MHz, a 1.626016% rate error.
The runtime flag removes the large mismatch but does not implement exact
rational tick conversion. A future timer implementation must keep counter
reads and deadline scheduling consistent. No such core timer patch is included
in this report.
[Pinned QEMU timer period](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/cpu.c#L1430),
[Pinned QEMU counter implementation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/helper.c#L1402).
