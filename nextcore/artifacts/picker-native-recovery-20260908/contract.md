# BP21 picker to original Tahoe Recovery integration

Current: the final BP21 EFI picker has actual authored-child OVMF evidence;
native original Tahoe Recovery and Terminal have separate evidence using the
earlier BP20-J EFI binary. Desired: verify the final archived BP21 image through
the complete visible picker → original booter → Recovery/Terminal path.

DECIDED, explicitly delegated by the Build Plan owner: use the existing
`8d29af2199999967145cd23145401c342294288366d17b6fcebc6bf02df00e96`
BOOTX64 archive without rebuilding. Relative to the successful native Terminal
control, change only the NextCore image and its explicit menu configuration:
`Misc.Boot.ShowPicker=true`, one enabled entry named
`Tahoe Recovery via EFI Shell`, targeting the same unchanged UEFI Shell helper.
The existing startup script loads the same HFS provider and original booter.
This is a configured chain entry, not automatic volume discovery.

Keep the original media, helpers, firmware code/template, CPU, 8 GiB RAM, SMC,
XHCI keyboard/tablet, standard VGA, original NVRAM values and boot arguments fixed.
Use new ESP, firmware variables and recovery COW paths. Never open or modify the
separately active installer target or its variables. No production source changes.

Acceptance requires an inspected actual NextCore GOP picker frame, an ordinary
keyboard Enter action, ordered picker/child-start markers, readable language
selection and Recovery Utilities/Terminal, followed by typed read-only commands.
Retain screenshots, input commands/replies, exact command and pre/post hashes in
isolation. Independently read back copied ESP files. Original guest assets stay
unchanged. Report explicit QMP quit/natural status and process cleanup; a crash,
timeout, missing GUI acceptance or changed original input cannot pass.

The whole supervisor is bounded to 600 seconds including cleanup; QEMU receives
a 540-second bound. Preparation has a 512 MiB per-file limit and QEMU retains the
existing 16 MiB output limit. The new run directory is checked against a 768 MiB
disk budget. Use separate QMP/serial paths and no shared Reims device/sink.
Any failed observation is retained. Native HAL, independent KC entry, installed
full OS, physical hardware and guest Metal remain separately unverified here.

Result: **PASS**. The archived BP21 image displayed the actual NextCore GOP
picker at 1280×800. Enter selected its configured entry; ordered picker, image
load, ConsoleControl and image-start output preceded the original guest boot.
The readable language chooser led through Recovery Utilities to Terminal.
Ordinary USB keyboard input produced `uname -a` and `sw_vers` output identifying
x86_64 Darwin 25.6.0 and macOS 26.6.2 (25G83).

QEMU exited naturally with code zero after explicit QMP quit at 329.1601 seconds;
the supervisor completed at 344.0045 seconds with no remaining process group or
adopted children. Nine original guest input hashes equal the BP20-J control, and
all new-run input pre/post/final hashes match. Copied ESP readback differs from
the control only in BOOTX64 and config.plist. NVRAM preparation JSON, decoded
initial variables and the startup script are byte-identical to the control.
The run uses 316,218,876 logical disk bytes within its 805,306,368-byte budget.

`result.json` binds these aggregates to the isolated complete receipt. `picker.png`
is the inspected authored NextCore screen; original guest screens, media, raw
logs and runtime samples remain isolated. No production code was changed or
rebuilt, and the earlier BP20-J receipt remains distinct.

The first offline finalization retained a failure receipt because a Windows
relative path in the plan was interpreted with backslashes on Linux. Normalizing
that metadata separator allowed the original-helper hash check and all remaining
checks to complete against the same already-preserved runtime; no VM was rerun.
