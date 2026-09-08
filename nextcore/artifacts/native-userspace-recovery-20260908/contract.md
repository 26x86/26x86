# Native recovery early userspace — read-only diagnostic contract

Current: the production NextCore ConsoleControl path and unchanged original
Tahoe EFI booter reach XNU and launchd, then the recovery data-volume task fails.
Desired: identify and correct the smallest host execution condition responsible
for that failure, preserving original media and helpers.

The preserved isolated trace reports a temporary filesystem memory request larger
than the native VM's configured 2 GiB RAM immediately before mount failure. The
separate external reference that reaches Recovery GUI uses 8 GiB. DECIDED first
experiment: increase only native guest RAM from 2 to 8 GiB, with fresh firmware
variables, copied ESP and recovery COW. CPU, NextCore/original booter, Shell/HFS
helpers and NVRAM parameters remain identical. No SMC, USB, external OpenCore or
Reims GPU is added. Standard VGA and a private QMP/serial path avoid the shared
Reims diagnostic sink.

Support requires the data-volume boot task to finish and later launchd jobs to
run. A repeated matching mount failure refutes this single-variable explanation.
Screenshots and bounded execution/cleanup accompany serial evidence; actual GUI
or Metal is separately assessed. Original helper/media pre/post hashes and raw
guest output remain isolated. Production changes require a public interface
contract and explicit source ownership from the Build Plan owner first.

This is a measured host RAM configuration experiment, not an Apple-code-derived
public implementation or a general minimum-memory recommendation for macOS.

Result: the 8 GiB-only experiment completed both temporary filesystem mounts,
passed the formerly failing task, initialized launchd logging and started
WindowServer. The original sources/media hashes were unchanged; the bounded
observation was stopped and reaped. The final captured display remained black.

DECIDED next controlled observation: add only the existing public QEMU
`isa-applesmc` device to that native 8 GiB profile. The independent external
reference reports the same black-display stage progressing after this device
addition. Keep the native EFI chain, CPU, storage and lack of USB unchanged.
This tests an emulated device condition, not a new independent SMC implementation.
Device arguments and guest output remain isolated; public code is unchanged.

The SMC-only follow-up reached the language chooser and installer-progress
processes and produced a non-black WindowServer display with a pointer and UI
controls. Text/layout in the 45-second frame was not yet readable, so a complete
Recovery GUI is **not** approved. No guest Metal execution is observed.

Final evidence: `result.json` records the public aggregates; its hash points to
the full isolated comparison. Both runtime comparisons verify the exact native
guest command after normalizing fresh output paths: RAM is the sole initial
guest-variable change, and the second adds only SMC. All ten original guest input
hashes match the control, all copied ESP application/helper/config files read back
identically, and both VM groups and supervisor children were fully reaped.
The observations lasted 68.0624 and 68.0311 seconds before the intended deadline
stop. The fixed NextCore binary is the original BP20-J feature binary for strict
comparison; this is not represented as a BP21 picker-binary run.

One preliminary attempt failed before QEMU because the supervisor's 32 MiB file
limit rejected a 128 MiB fresh ESP. Its source and error are retained; the next
fresh attempt separated the 512 MiB preparation cap from the 16 MiB guest-output
cap. A late screenshot request after VM cleanup found no QMP socket; it contributes
no image evidence. The original preserved helper was never edited.

The next unresolved layer is readable guest GUI rendering/input. It does not
invalidate the measured recovery-task fix. Host memory configuration uses QEMU's
public [`-m` option](https://www.qemu.org/docs/master/system/invocation.html).

## Readable GUI and input continuation

Current uncertainty: the native UI frame was captured at 45 seconds, while the
external reference's readable Recovery GUI was confirmed around 195 seconds.
DECIDED next observation: retain exactly the native 8 GiB + SMC guest profile and
extend the bound to 300 seconds, collecting late frames. Do not attribute an early
transitional frame to a pixel-layout defect without this time comparison.

Acceptance is a readable language picker followed by actual selection and normal
Recovery menu/Terminal access. If a readable display still fails, compare actual
GOP/boot-video geometry and media/platform differences before a single-variable
experiment. The already verified external XHCI keyboard/tablet profile may be
added separately to supply real input devices; this is distinct from full OS
installation and guest Metal work owned by the other x86 agent. Original inputs,
fresh COW, bounded cleanup and existing NextCore branding remain invariant.

During the longer observation, the preserved native language-chooser state
explicitly reports no unambiguous keyboard or mouse and waits for a pointing
device. The external reference reports both devices present. This is stronger
evidence for an input-pairing screen than for a framebuffer-layout defect.
DECIDED follow-up: after the unchanged late frame, add the reference's public
QEMU XHCI controller plus USB keyboard/tablet to a new native fresh-COW run.
Use observed screen coordinates and ordinary keys for language selection and
Recovery Utilities/Terminal; keep all media, platform and display settings fixed.

The unchanged longer run preserved all inputs and completed cleanup after
298.0323 seconds. Its 210-second frame still shows the input-pairing illustration,
with readable setup-support text. The early frame is therefore not accepted as
evidence of broken font or framebuffer geometry. The diagnostic screenshot
worker's file stream stayed open between samples; the new USB observation closes
that stream after every sample so ordinary external QMP input can connect.
The original worker source is retained unchanged.

The USB-only run displayed a fully readable language chooser, accepted keyboard
selection changes and a pointer click, and reached the normal Recovery menu.
Its observation deadline expired before Terminal interaction. DECIDED: repeat
the exact native USB guest profile with fresh COW solely to finish Terminal
input acceptance; no additional guest variable or production code changes.

Final GUI result: the unchanged USB profile reached a readable 1280×800 language
chooser and Recovery menu. Ordinary pointer input opened Utilities → Terminal;
typed `uname -a` and `sw_vers` returned x86_64 Darwin 25.6.0 and macOS 26.6.2
(25G83). The first USB run also demonstrated the selected language changing with
Down/Up keys. Screenshots and exact input/reply receipts remain isolated.

The earlier panel is resolved as the input-device pairing flow: the no-USB log
reports zero unambiguous keyboard/mouse devices, while both USB runs report one
of each. The unchanged 210-second frame still displayed pairing. No framebuffer,
GOP geometry, Apple media, SMBIOS or production-code change was needed to pass
this native Recovery GUI/input acceptance.

The final VM was explicitly ended through QMP after the visible command results.
`result.json` links the aggregate and complete private comparison, including
pre/post source hashes, copied ESP readback, bounded execution and process cleanup.
The experiment still uses the pinned BP20-J EFI image; the later BP21 picker
binary is not represented as tested by these Recovery runs. Full installation,
NextCore-owned native HAL, physical-device execution and guest Metal remain
separate unverified layers for this result. Product branding was not altered.
