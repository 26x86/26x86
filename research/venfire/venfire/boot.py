"""Original-preserving VMApple bring-up: read-only probes or guest-written COW sessions."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import threading
import time

from .artifacts import create_manifest, require_intact, verify_manifest, write_manifest
from .backend import probe_backend
from .policy import authorize_host

MAX_LOG_BYTES = 16 * 1024 * 1024
# Original vma2 XNU timebase observed as 125/3 ns and 24,000,000 Hz.
# QEMU's historical integer-ns counter rounding is audited separately.
VMAPPLE_CPU = "max,pauth=on,pauth-qarma5=on,cntfrq=24000000"


def raw_drive(path: Path, index: int, offset: int = 0) -> str:
    """A read-only byte view; an offset never edits/trims the source image."""
    if index not in (0, 1) or offset < 0 or offset % 512:
        raise ValueError("Drive index must be 0/1 and offset a nonnegative multiple of 512")
    view = {"driver": "raw", "file": {"driver": "file", "filename": str(path)},
            "offset": offset, "read-only": True}
    # QemuOpts uses doubled commas to embed a literal comma in a value.
    filename = "json:" + json.dumps(view, separators=(",", ":"))
    return f"if=pflash,index={index},readonly=on,file={filename.replace(',', ',,')}"


def boot_probe(*, qemu: str, firmware: str, aux: str, disk: str,
               uuid: int, output: str, seconds: int = 20, aux_offset: int = 0,
               developer_host_bypass: bool = False, recovery_socket: str | None = None) -> dict:
    return _run_boot(qemu=qemu, firmware=firmware, aux=aux, disk=disk, uuid=uuid,
                     output=output, seconds=seconds, aux_offset=aux_offset,
                     developer_host_bypass=developer_host_bypass, recovery_socket=recovery_socket)


def boot_session(*, qemu: str, firmware: str, directory: str, uuid: int, output: str,
                 seconds: int | None = None, developer_host_bypass: bool = False,
                 recovery_socket: str | None = None, runtime_action=None, graphics="auto") -> dict:
    from .storage import load_storage
    authorize_host(developer_host_bypass=developer_host_bypass)
    storage = load_storage(directory)
    return _run_boot(qemu=qemu, firmware=firmware,
                     aux=storage.manifest.artifacts[0].path, disk=storage.manifest.artifacts[1].path,
                     uuid=uuid, output=output, seconds=seconds, aux_offset=storage.aux_offset,
                     developer_host_bypass=developer_host_bypass, storage=storage,
                     recovery_socket=recovery_socket, runtime_action=runtime_action, graphics=graphics)


def _run_boot(*, qemu, firmware, aux, disk, uuid, output, seconds, aux_offset,
              developer_host_bypass, storage=None, recovery_socket=None, runtime_action=None, graphics="off"):
    # CPU requirements and input checks remain mandatory in a private lab build.
    authorization = authorize_host(developer_host_bypass=developer_host_bypass)
    if graphics not in ("auto", "on", "off"):
        raise ValueError("Graphics selection must be auto, on or off")
    if runtime_action is not None and (storage is None or recovery_socket is None or not callable(runtime_action)):
        raise ValueError("A runtime action requires a COW session and exclusive recovery socket")
    host = authorization.report
    if storage is None and (type(seconds) is not int or not 1 <= seconds <= 300):
        raise ValueError("Probe duration must be between 1 and 300 seconds")
    if storage is not None and seconds is not None and (type(seconds) is not int or not 1 <= seconds <= 86400):
        raise ValueError("Session duration must be omitted or between 1 and 86400 seconds")
    if not 0 <= uuid <= (1 << 64) - 1:
        raise ValueError("VMApple ECID uuid must fit an unsigned 64-bit integer")
    if aux_offset < 0 or aux_offset % 512:
        raise ValueError("Aux offset must be a nonnegative multiple of 512")
    backend = probe_backend(qemu)
    if not (backend["tcg"] and backend["vmapple"] and backend["research_headless"]):
        raise ValueError("A VMApple TCG backend advertising research-headless is required")
    if storage is not None and not backend.get("bdif_block_writes"):
        raise ValueError("COW boot sessions require the BDIF block-write backend patch")
    if graphics == "on" and not backend.get("research_graphics"):
        raise ValueError("The explicitly requested GPU device is unavailable in this backend")
    graphics_enabled = graphics != "off" and bool(backend.get("research_graphics"))
    manifest = create_manifest([firmware, aux, disk, backend["executable"]])
    firmware_entry, aux_entry, disk_entry, _ = manifest.artifacts
    firmware_path, aux_path, disk_path = [Path(entry.path) for entry in (firmware_entry, aux_entry, disk_entry)]
    if not 0 < firmware_entry.size_bytes <= 1024 * 1024:
        raise ValueError("Firmware must fit the upstream VMApple 1 MiB ROM window")
    if aux_offset >= aux_entry.size_bytes:
        raise ValueError("Aux byte-view offset exceeds input size")
    folder = Path(output).absolute()
    folder.mkdir(parents=True, exist_ok=False)
    write_manifest(manifest, folder / "inputs.json")
    disks = (storage.arguments(allow_bdif_writes=True) if storage else
             ["-drive", raw_drive(aux_path, 0, aux_offset), "-drive", raw_drive(disk_path, 1)])
    recovery = []
    if recovery_socket is not None:
        from .artifacts import _absolute_path, _inspect_path
        endpoint = _absolute_path(recovery_socket)
        _inspect_path(endpoint, must_exist=False)
        if endpoint.exists() or len(str(endpoint).encode()) > 100:
            raise ValueError("Recovery socket needs a fresh local path of at most 100 bytes")
        recovery = ["-chardev", "socket,id=vusb,path=" + str(endpoint).replace(",", ",,") + ",server=on,wait=off",
                    "-global", "vmapple-bdif.usbdev=vusb"]
    machine = f"vmapple,research-headless=on,uuid={uuid}"
    if graphics_enabled:
        machine += ",research-graphics=on"
    command = [backend["executable"], "-M", machine,
               "-accel", "tcg,thread=single", "-cpu", VMAPPLE_CPU,
               "-m", "4G", "-smp", "2", "-bios", str(firmware_path),
               *disks, *recovery, "-display", "none", "-monitor", "none",
               "-serial", "stdio", "-nic", "none", "-no-reboot"]
    # Deliberately no -semihosting, host passthrough, network, or guest debug patch.
    started = time.monotonic()
    reason = "exited"
    process = None
    failure = None
    action_report = None
    watchdog = None
    stop_watchdog = threading.Event()
    watchdog_failure = []
    stop_lock = threading.Lock()

    def stop_process():
        with stop_lock:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    try:
        with (folder / "serial.log").open("xb") as serial, (folder / "backend.log").open("xb") as errors:
            # This is deliberately the last operation before launching the
            # backend: both guest inputs and executable must still match.
            require_intact(manifest)
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=serial, stderr=errors)
            execution_started = time.monotonic()
            try:
                if runtime_action is not None:
                    # The action alone consumes the USB socket. This watcher
                    # only bounds the backend process and its two log files.
                    def watch():
                        try:
                            while not stop_watchdog.wait(0.05):
                                if process.poll() is not None:
                                    return
                                if seconds is not None and time.monotonic() - execution_started >= seconds:
                                    watchdog_failure.append("time_budget")
                                    stop_process()
                                    return
                                if max(serial.tell(), errors.tell()) > MAX_LOG_BYTES:
                                    watchdog_failure.append("log_limit")
                                    stop_process()
                                    return
                        except BaseException as exc:
                            watchdog_failure.append("watchdog_error:" + type(exc).__name__)
                            stop_process()

                    def check_running():
                        if watchdog_failure:
                            raise RuntimeError("Backend observation stopped: " + watchdog_failure[0])
                        if seconds is not None and time.monotonic() - execution_started >= seconds:
                            raise TimeoutError("Backend session deadline expired")
                        if process.poll() is not None:
                            raise RuntimeError("Backend exited during recovery action")

                    watchdog = threading.Thread(target=watch, name="venfire-session-watchdog")
                    watchdog.start()
                    check_running()
                    action_report = runtime_action(serial_log=folder / "serial.log", check_running=check_running)
                    check_running()
                    reason = "action_complete"
                while runtime_action is None and process.poll() is None:
                    if seconds is not None and time.monotonic() - execution_started >= seconds:
                        reason = "time_budget"
                        break
                    if max(serial.tell(), errors.tell()) > MAX_LOG_BYTES:
                        reason = "log_limit"
                        break
                    time.sleep(0.05)
            finally:
                stop_watchdog.set()
                try:
                    stop_process()
                finally:
                    if watchdog is not None:
                        watchdog.join()
    except BaseException as exc:
        reason = "error"
        failure = exc
        action_report = getattr(exc, "chain_report", action_report)
    finally:
        # Persist post-use evidence even if spawn, polling, or cancellation
        # failed. An invalid integrity result can never mean completed safely.
        integrity = verify_manifest(manifest)
        # A requested observation deadline is normal; a crash or exhausted log
        # bound is not. Neither outcome establishes that the guest booted.
        backend_returncode = process.returncode if process is not None else None
        execution_completed = (failure is None and integrity.valid and
                               (reason in ("time_budget", "action_complete") or
                                (reason == "exited" and backend_returncode == 0)))
        report = {"schema": 1, "host": host.to_dict(), "backend": backend,
                  "host_authorization": authorization.to_dict(),
                  "command": command, "termination": reason,
                  "returncode": backend_returncode,
                  "duration_seconds": round(time.monotonic() - started, 3),
                  "input_integrity": integrity.to_dict(),
                  "mode": "cow-session" if storage else "read-only-probe",
                  "graphics_requested": graphics, "graphics_device_enabled": graphics_enabled,
                  "physical_display_verified": False,
                  "probe_completed": storage is None and execution_completed,
                  "session_completed": storage is not None and execution_completed,
                  "macos_boot_verified": False,
                  "limitation": "Guest process execution does not establish macOS boot/install/update support."}
        if storage:
            report["storage_session"] = str(storage.directory)
            report["guest_writes"] = "Persisted to separate AUX/root qcow2 overlays; originals remain read-only."
        if runtime_action is not None:
            report["runtime_action"] = action_report
            report["runtime_action_completed"] = reason == "action_complete" and execution_completed
            report["watchdog_stop"] = watchdog_failure[0] if watchdog_failure else None
        if failure is not None:
            report["error_type"] = type(failure).__name__
        with (folder / "result.json").open("x", encoding="utf-8") as destination:
            destination.write(json.dumps(report, indent=2) + "\n")
    if failure is not None:
        raise failure
    return report
