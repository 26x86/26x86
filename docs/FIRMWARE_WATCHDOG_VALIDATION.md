# Firmware watchdog ownership validation

## Current Status

An authored OVMF probe demonstrates that the shared firmware watchdog-disable
helper permits execution beyond an armed two-second timeout. The armed control
exits before its delayed completion marker. All 15 host checks pass. This does
not establish that watchdog expiry caused the original r21 termination, and it
does not establish normal macOS startup or a physical desktop.

## Target State

The baseline firmware application and NXARMJIT explicitly request watchdog
disable after service initialization, report the actual result and preserve
otherwise usable firmware behavior when disable is unsupported or fails.
Host execution deadlines and guest instruction budgets remain unchanged.

## Actual EFI experiment

Both probe variants call the same injected failure boundary first. It verifies
exactly one call with timeout zero and watchdog code 0x10000, and confirms that
DEVICE_ERROR propagates unchanged. The failure marker is emitted only after
these checks. This is an injected service failure, not an actual firmware service
failure. The probe then arms the real firmware watchdog for two seconds.

| Variant | Subsequent operation | Observed result |
| --- | --- | --- |
| Disabled | Call the shared production disable helper, then stall for three seconds | SURVIVED marker; host terminates and reaps QEMU after the complete row |
| Armed control | Keep the timer armed, then stall for three seconds | Natural QEMU exit 0 under `-no-reboot`; no SURVIVED marker and no host termination |

Total observed times, including firmware startup, were 12.062 seconds disabled
and 10.541 seconds armed. Serial receive timestamps are not guest timer
measurements. Both runs reached each required marker exactly once in order,
remained inside the host deadline, preserved source/firmware/binary hashes and
preserved the executable copied onto the authored ESP. The verifier uses a new
process group, reserves cleanup time, and terminates/kills and reaps a process
when needed. It accepts only LF-complete serial rows; four independent fragment
checks covered absent, CR-only, LF and CRLF suffixes.

## Reproduction

Use an isolated Linux scratch directory and a fixed published Nextcore-EFI
checkout containing `watchdog-probe`. Build the same NXWATCHDOG binary twice with
separate target directories: first with `watchdog-probe`, then with
`watchdog-probe-armed`. Both builds use release `x86_64-unknown-uefi`. The additional
armed feature includes the probe and retains the real timer. Neither probe is a
normal BOOTX64 or NXARMJIT release entry.

```sh
cargo build --locked --release --target x86_64-unknown-uefi   -p nextcore-efi --bin NXWATCHDOG --features watchdog-probe   --target-dir /tmp/watchdog-disabled
cargo build --locked --release --target x86_64-unknown-uefi   -p nextcore-efi --bin NXWATCHDOG --features watchdog-probe-armed   --target-dir /tmp/watchdog-armed
python3 nextcore/tools/verify_watchdog_ovmf.py   --disabled-efi /tmp/watchdog-disabled/x86_64-unknown-uefi/release/NXWATCHDOG.efi   --armed-efi /tmp/watchdog-armed/x86_64-unknown-uefi/release/NXWATCHDOG.efi   --output /tmp/watchdog-proof --timeout 60
```

Run the Cargo commands from the pinned runtime workspace and the Python command
from the parent repository. The output directory must not exist. Defaults select
QEMU x86_64 TCG and the installed OVMF 4M code/variable templates; explicit path
options are available. No kernel, Apple payload, disk image or private input is
required. The helper creates only an authored FAT-backed ESP and a private copy
of the OVMF variables template in its output directory.

[Integrity summary](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/firmware-watchdog/summary.json)
and its listed reports/logs preserve the actual experiment. Logs and receipt
bytes are copied unchanged; hashes in the summary cover all nine evidence files.
EFI binaries, generated ESPs and variable images are excluded from this evidence
bundle. The receipt records the binary and source hashes instead.

## Evidence limits

The control establishes watchdog behavior in this OVMF environment and verifies
the shared helper's successful disable path. The failure-path check verifies
argument forwarding and error preservation through an injected callback. It
cannot certify arbitrary physical firmware implementations. Original r21 has no
terminal execution record or retired count, so its watchdog-cause field remains
false. A separate original replay must establish whether the fix changes that
outcome. No original instruction words or addresses are published here.
