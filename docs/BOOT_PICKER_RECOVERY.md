# 26x86 Boot Picker and macOS Recovery

**Current Status:** Reference picker policy and historical VMApple recovery observations.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

This specification defines the `Alt/Option` key handling pathway used to trigger macOS Recovery. This applies specifically to `iBoot(AArch64)` macOS guests; iOS, iPadOS, and other mobile Apple platforms are out of scope.

## EFI / OpenCore Layer — Physical Intel Mac

The reference configuration is [`integration/opencore/Sample.plist`](https://github.com/26x86/26x86/blob/main/integration/opencore/Sample.plist). The following policy is enforced under `Misc -> Boot`:

```text
PollAppleHotKeys = true
ShowPicker       = false
Timeout          = 2
PickerMode       = Builtin
```

This reference configuration intends Option/Alt to select OpenCore's built-in picker during startup; the firmware/key timing must be verified on the actual machine. The `macOS Recovery` entry is populated dynamically only when a valid Recovery environment is detected on the corresponding APFS volume container. If `ScanPolicy`, APFS drivers, or volume states do not align, omitting the recovery entry is expected behavior. This reference plist is never written automatically to the active ESP without explicit operator command.

Evidence required on physical Intel Mac systems includes:

1. OpenCore debug log verifying Option key detection within 2 seconds of power-on;
2. Built-in picker screen displaying both production macOS and `macOS Recovery` entries;
3. Loader logs confirming successful transfer to `boot.efi` on the target APFS Recovery volume;
4. Display of the macOS Recovery utilities and disk selection interface.

If screen captures or log files are unavailable, the state is recorded strictly as static plist verification.

## VMApple GUI Layer — Input State Machine & Recovery Transport

The `Apple Silicon Sandbox` step within the Windows and macOS GUI employs the identical 2-second timeout policy via `x86/boot_picker.py`:

1. Clicking `Start 2-Second Boot Picker` sets the state machine to `armed`.
2. Receiving an authentic `Alt` or `Option` `keydown` event from the browser or WebView shifts the state to `picker`.
3. Selecting `macOS Recovery · _default.ipsw` or navigating via Down Arrow followed by Enter transitions the state to `selected`, persisting selection and timestamp data to the IPC bridge.
4. Clicking `Open Recovery VM Window` passes `--boot-selection recovery` and `--boot-picker-trigger alt-enter` to the VMApple worker. Standard boots pass `--boot-selection macos` directly.
5. The Recovery worker initiates iBSS DFU payload transfer only after QEMU opens the recovery socket and fulfills the 2-second timing gate. Direct macOS workers skip DFU transfer and monitor AVPBooter AUX/root boot sequence. If bulk OUT endpoint 4 fails to enumerate following recovery reset, execution halts at `transition-blocked`.

State machine transitions are verifiable via the bridge API endpoints (`get_boot_picker_status`, `start_boot_picker`, `tick_boot_picker`, `boot_picker_key`, `select_boot_entry`). These APIs perform read-only state changes without altering EFI or guest disk contents.

## Historical VMApple recovery observations and installation gates

In the recorded research setup, caller-owned Golden Gate inputs comprise authentic AVPBooter/iBSS binaries and read-only AUX/root disks. Output directories contain only COW overlays and `launch.json`. Consequently, reaching the installer UI requires fulfilling all four verification criteria:

```text
signature_acceptance_verified = true
ibec_executed                 = true
xnu_executed                  = true
macos_boot_verified           = true
```

In live TSS test runs, following iBSS DFU reset, the virtual device re-enumerated as `05ac:1281` advertising bulk OUT endpoint 4. Personalized IMG4 payloads for LocalPolicy and authentic iBEC were transmitted, followed by receipt of `go` acknowledgments. Following Stage2 prompt observation in selective RPC experiments, all five official restore roles were transmitted, pre-boot notification `0200` STALL was logged, and `bootx` acknowledgments were received. Subsequent iBoot kernel panics mean that signature acceptance, XNU handoff, and Recovery UI presentation cannot be presumed. In reports, `macos_boot_verified` and `forced_transition` remain `false`. Without Apple PV graphics virtualization on Linux QEMU, visual UI cannot be verified. Full data is archived in [`integration/vmapple-gui-bootpicker-report.json`](https://github.com/26x86/26x86/blob/main/integration/vmapple-gui-bootpicker-report.json).

In direct boot paths, this recovery table is not reused. The runner records `Darwin Kernel Version` as XNU execution evidence and `launchd`/`loginwindow`/`WindowServer` as userspace evidence, asserting `macos_boot_verified=true` only when both tiers are present. Missing evidence triggers `direct-boot-evidence-timeout`, and `installation_verified` remains `false`.

## Configuration Schema

The 26x86 fragment in `config.plist` utilizes the following schema:

```xml
<key>Venfire</key>
<dict>
  <key>MachineType</key><string>iBoot(AArch64)</string>
  <key>GuestOS</key><string>macOS</string>
  <key>Recovery</key>
  <dict>
    <key>Enabled</key><true/>
    <key>Protocol</key><string>DFU/IPSW</string>
    <key>LocalRecovery</key><dict><key>ImageName</key><string>_default.ipsw</string></dict>
  </dict>
  <key>BootPicker</key>
  <dict>
    <key>Enabled</key><true/>
    <key>DelaySeconds</key><integer>2</integer>
    <key>AltKey</key><string>Alt</string>
    <key>ShowPickerOnAlt</key><true/>
    <key>RecoveryEntry</key><dict><key>Enabled</key><true/></dict>
  </dict>
</dict>
```

`x86.sandbox_config.validate()` enforces this specification before evaluating EFI or SMBIOS parameters, rejecting configurations where delay is not 2 seconds, key is not Alt/Option, or recovery image is not `_default.ipsw`.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](index.md), [progress](progress.md),
[compatibility catalog](compatibility.md) and
[library](library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
