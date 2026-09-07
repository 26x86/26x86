# APLS host runner integration (Build Plan BP8)

## Current and desired state

The existing `guest` module describes plans and probes a framework. Its
`AbiPending` result is not an executable VM. The existing public Python
`x86.vmapple` and `x86.vmapple_tcg` workers already execute caller-selected
native or TCG processes, preserve base inputs using ephemeral/COW storage,
terminate them, and produce UART evidence in `launch.json`.

The new `runner` module implements an explicit Rust host adapter to those workers. This is
the **host user-space process orchestration layer**, not EFI, a kernel driver,
a VSK execution cell, an Objective-C ABI implementation, or Metal support.

## Adopted execution contract

- `runner::RunnerRequest` selects `RunnerHost::Local` or `RunnerHost::Wsl`
  and `RunnerBackend::Native` or `RunnerBackend::Tcg` explicitly. No platform
  fallback or policy relaxation is inferred. Native launch remains gated to
  local Apple-Silicon macOS; the worker also validates the macOS version.
- Repository, Python executable, VM JSON, firmware, QEMU, guest-output path,
  target 26/27, duration and research acknowledgement are explicit arguments.
  Paths passed to WSL belong to WSL; the adapter receipt directory belongs to
  the calling host. Arguments are passed without a command shell.
- The VM JSON is an atomic bundle. No fabricated identity, storage rewrite,
  direct disk override or VSK `boot_authorized` mutation is introduced.
- The adapter starts the existing worker and waits for its bounded VM run and
  cleanup. It saves command/PID, stdout JSON, stderr and an adapter receipt
  in a new host directory even when the worker rejects input. Worker-owned
  `launch.json`, UART and COW images stay in its separate new output folder.
- A completed worker process is a stopped host process, not a running VM.
  Guest execution, target match, original-input integrity, complete guest
  termination and XNU/userspace markers are evaluated separately. A zero
  exit code or a lone caller-supplied `macos_boot_verified` boolean is
  insufficient. No installation, physical-Mac or Metal verdict is inferred.
- Synthetic fixtures only test orchestration and evidence rejection; their
  results are not hardware/macOS verification. Real execution needs the
  user's existing original input bundle and actual selected backend.

## Evidence and references

- `docs/NEXTCORE_BUILD_PLAN.md` BP8 delegates this crate; AGENTS.md and the
  Design/Sandbox documents were read before implementation.
- Existing `x86/cli.py` `run-native`/`run-tcg` return JSON and exit 0 only on
  their boot-evidence gate; preflight rejection is exit 2.
- Existing `x86/vmapple.py::run_macosvm_native` uses `macosvm --ephemeral`;
  `x86/vmapple_tcg.py::run_tcg_macosvm` creates COW storage. Both keep process
  termination and input hash verification in their execution lifecycle.
- [macosvm upstream](https://github.com/s-u/macosvm) documents native Apple
  Silicon execution, the host/guest version constraint and ephemeral storage.
- [QEMU VMApple guide](https://www.qemu.org/docs/master/system/arm/vmapple.html)
  documents its native VMApple prerequisites and macOS 12.x guest limitation.
  The repository's explicitly selected patched TCG engine is a separate
  research path, not newly verified upstream modern-macOS support.
- [Rust child-process contract](https://doc.rust-lang.org/std/process/struct.Child.html)
  requires explicitly waiting for owned children; the adapter performs that
  wait before publishing its completed outcome.
- [Windows process flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
  defines `CREATE_NO_WINDOW`, used only to keep console helpers hidden.

## Verification performed on 2026-09-07

- `cargo test -p nextcore-apls`: 38 tests passed on Windows, including explicit
  WSL command construction, research acknowledgement, process-only success
  rejection, target mismatch, input mutation, marker order, backend-specific
  runtime flags and failure receipt interpretation.
- Executed the Rust `run_host` example and then the integrated
  `nextcore-tool apls run --backend tcg --host wsl` against the caller's existing
  raw Stage2 firmware and restore bundle, using new output folders and COW.
- Final host receipt: `nextcore/artifacts/apls-cli-run-20260907-1929/adapter.json`.
  Worker output: `/tmp/nextcore-apls-cli-resume-20260907-1929/launch.json` in
  `Ubuntu-24.04`. The report records the exact paths, commands, PID and hashes.
- Actual QEMU starts and exits with code 0. UART contains 417 bytes including
  the Stage2 startup banner and firmware panic before XNU. The worker and CLI
  return 2, and XNU/userspace/macOS/graphics verification remain false.
  The dedicated `qemu.debug.log` is empty, but inspection found 12,943 TCG
  `Trace` lines in the preserved `arm_psci_call.trace`, including firmware
  entry at `0x00100000`. The inherited worker read the wrong log for execution
  evidence. The root agent separately delegated that shared-log correction;
  this crate does not turn the inherited false trace field into a boot claim.
- Independently re-hashed VM JSON, AUX, root and firmware after the final run:
  all four match the run's prelaunch hashes. No QEMU process with this run's
  output path remains. These checks and copied text logs are in `readback.json`,
  `serial.log` and `qemu.stderr.log` beside the host receipt.
- A deliberately nonexistent QEMU path was sent through the real WSL worker:
  worker exit 2, guest runtime false, boot false, error JSON preserved in
  `nextcore/artifacts/apls-preflight-20260907-192309/adapter.json`.
- Native Apple-Silicon Virtualization.framework execution was not available
  on this Windows/WSL host and is not marked verified. This adapter does not
  change the existing VSK admission policy or the direct Objective-C ABI stub.

## OPEN_QUESTION

- `OPEN_QUESTION: Build Plan: Direct EFI/VSK execution-cell integration remains
  a separate implementation; a working host runner must not be labelled that
  integration.`
