# BP26 startup continuation results — 2026-09-08

## Firmware device tree

Core now exposes a borrowed `firmware_dt::FirmwareDeviceTree` structural view.
It preserves the original 32-bit length, payload, property name and alignment
bytes. Bit31 identifies a template; template text can be viewed as an ASCII
C-string but is never evaluated. Any template prevents runtime validation.
Unflagged input still passes through the unchanged strict `flat_dt` validator.

Seven independent tests pass, including every truncated prefix, malformed
length/count/name inputs, depth limits, exact and exceeded aggregate budgets,
opaque template values and preservation of nonzero padding. Combined with the
existing ARM placement/profile checks, fifteen targeted Core tests pass. Core
also passes a no-default-features check.

The unchanged original firmware DT was inspected completely: 299,188 bytes,
338 nodes, 4,289 properties, depth five and 48 unresolved templates. The
runtime bridge reports `UnresolvedTemplates { count: 48 }`. Original input
hashes and count-only inspection receipts are under `_isolated/macos27-j274`.
No template text or original DT payload is included in this public artifact.

The EFI trace caller now reports unresolved template count and returns
UNSUPPORTED before TRACE_ENTER. A supplied unflagged diagnostic DT still has
`platform_complete=false`; no M1 platform values or SPTM services are supplied.

Host reproduction from the repository root:

```sh
cargo test --manifest-path nextcore/Cargo.toml -p nextcore-core \
  --test firmware_dt --test arm64_handoff --test arm64_boot_config --test kernel_target
cargo check --manifest-path nextcore/Cargo.toml -p nextcore-core --no-default-features
cargo run --manifest-path nextcore/Cargo.toml -p nextcore-core \
  --example inspect_firmware_dt -- /path/to/firmware-device-tree
```

The inspection example emits counts and error categories only. Its successful
structural parse does not mean templates are resolved or the platform is complete.

## x86 EFI execution

`prefix-ovmf/report.json` records five passing firmware cases: explicit cold
register handoff, exact one-instruction budget, disabled trace feature, unresolved
template rejection, and a seven-instruction native thread-register payload.
The latter writes and reads TPIDR_EL0, TPIDRRO_EL0 and TPIDR_EL1 at guest EL1
using a nonzero staged argument address, then verifies x0=x1=x2=x3 after HALT.
`jit-pac-ovmf/report.json` records passing ARM64 and ARM64e/PAC regression cases,
including 25/45 retired instructions and sixteen GOP pixels read back per case.

The original kernel was rerun with the unchanged explicit diagnostic convention
and budget eight. It retired **seven instructions in three native blocks**,
passing the former standard TPIDR write boundary and stopping on the next
implementation-defined platform system-register access. The trace completed in
31.923 seconds. Original input and ESP-copy SHA-256 values remained unchanged.
Detailed execution coordinates and instructions remain private in
`_isolated/macos27-j274/efi-original-prefix-r2/report.json`; the exact argument
array is `trace-command-r2.private.json` in the same isolated input directory.

A separate actual EFI run supplied the original firmware DT. It reported all
48 unresolved templates and returned UNSUPPORTED before TRACE_ENTER. Its private
receipt is `efi-original-template-rejected-r2/report.json`. No flag or template
value was cleared or replaced to obtain this result.

The native EFI build uses `arm-jit-probe,arm-jit-trace`. Reproduce the five
authored cases with the same script as BP25 (it now includes the new cases):

```sh
python3 nextcore/tools/verify_arm_sptm_prefix_ovmf.py \
  --efi-trace /path/to/diagnostic/NXARMJIT.efi \
  --efi-default /path/to/default/NXARMJIT.efi --output /tmp/bp26-prefix-cases
```

SPTM arguments/services, resolved M1 platform data, actual XNU boot and Metal
acceleration remain unimplemented. Advancing an executable prefix and transport
tests does not change those outcome fields.
