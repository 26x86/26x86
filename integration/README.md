# Coordinated source integration

The main checkout is based on `d47409b992795ed2c1375a35d65980bdf7d791af`.
`sources.lock.json` records immutable source revisions and upstream license
blob identities for 26x86 and its three support repositories. Mellow is a
separate design reference with its own license; it is not relicensed here.

Changes for the support repositories are exported under `patches/` and bound
to hashes in `support-patch-report.json`. Reconstruct the coordinated source
trees using `python scripts/prepare-support-sources.py --output <new-folder>`.
This fetches source repositories and applies their reviewed patches; it does
not install anything on a boot disk or upload changes to GitHub.

The OpenCore source patch supplies the config parser and EFI handoff. Patcher
Support and Metallib Support add explicit artifact identity receipt modes.
These receipts describe exact OS/build/architecture/compiler identity; they
do not certify unimplemented macOS 27 adapters or Metal acceleration.

Native EFI engine sources live in `sandbox/efi`, the AIC device model in
`sandbox/devices`, and the imported internal platform research in
`research/venfire`. `python -m x86 assets` exposes the imported original-file
integrity and IPSW metadata inspection functions through the 26x86 interface.

The subsequently adopted VSK design is tracked by `vsk-spec.json` and
`docs/VSK.md`. Its M0 code and M1 input validators live in `sandbox/vsk`;
`python -m x86 vsk --config ...` is an offline configuration check. The older
OpenCore binaries and handoff receipt remain diagnostic evidence and do not
incorporate a VSK kernel or provide VMX/VT-d isolation. VSK unit receipts must
remain separate from the existing EFI and physical-Mac acceptance fields.

The visible EFI check is `sandbox/vsk/tools/verify_efi_inputs.py --gui`. It
executes the authored EFI under GTK OVMF and records QEMU/OVMF hashes in
`vsk-efi-gui-report.json`, while keeping `boot_authorized`,
`macos_boot_verified` and `physical_mac_verified` false. The GUI run is a
reproducibility check for the EFI input boundary, not a Golden Gate or
physical-Mac boot result.

The current live-TSS GTK VMApple observation is summarized in
`vmapple-gui-bootpicker-report.json`. It records the real two-second Alt→Recovery
selection, Apple TSS status `0` for iBSS/iBEC/LocalPolicy, 173 DFU blocks, reset,
re-enumeration as `05ac:1281` with bulk endpoint 4, LocalPolicy/iBEC uploads and
`go` acknowledgement. The original iBEC reaches its Stage2 UART prompt; the
restore chain then uploads all five official roles, records the expected pre-boot
notification STALL and receives a `bootx` acknowledgement. iBoot subsequently
panics before XNU, so XNU/macOS/installer success remains unverified. The older
iBSS-only transition report is retained in `vmapple-gui-recovery-report.json`.
