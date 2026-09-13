#!/usr/bin/env python3
"""Independent authored OVMF watchdog ownership proof; no guest kernel inputs."""
import argparse
import errno
import hashlib
import json
import os
import signal
from pathlib import Path
import re
import shutil
import subprocess
import time


PREFIX = "NXWATCHDOG: "
SURVIVED = PREFIX + "SURVIVED"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    if not path.exists():
        return []
    data = path.read_bytes().split(b"\n")[:-1]
    return [re.sub(rb"\x1b\[[0-?]*[ -/]*[@-~]", b"", row).rstrip(b"\r").decode("utf-8", "replace") for row in data]


def case(args, binary, mode, out):
    out.mkdir()
    boot = out / "esp/EFI/BOOT"
    boot.mkdir(parents=True)
    copied = boot / "BOOTX64.EFI"
    shutil.copyfile(binary, copied)
    variables = out / "vars.fd"
    shutil.copyfile(args.ovmf_vars, variables)
    serial = out / "serial.log"
    command = [args.qemu, "-machine", "q35,accel=tcg,smm=off", "-cpu", "Nehalem",
               "-m", "512", "-smp", "1", "-display", "none", "-vga", "std",
               "-monitor", "none", "-serial", "file:" + str(serial), "-net", "none", "-no-reboot",
               "-drive", "if=pflash,format=raw,readonly=on,file=" + str(args.ovmf_code),
               "-drive", "if=pflash,format=raw,file=" + str(variables),
               "-drive", "format=raw,file=fat:rw:" + str(out / "esp")]
    start = time.monotonic()
    observations = {}
    process = None
    stopped = False
    timed_out = False
    retries = 0
    failure = None
    actual = []
    try:
        with (out / "stdout.log").open("wb") as stdout, (out / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
            while process.poll() is None:
                elapsed = time.monotonic() - start
                if elapsed >= args.timeout - 5:
                    timed_out = True
                    break
                try:
                    actual = rows(serial)
                except OSError as error:
                    if error.errno not in {errno.EAGAIN, errno.EINTR, getattr(errno, "ENODATA", 61)}:
                        raise
                    retries += 1
                    time.sleep(0.02)
                    continue
                for row in actual:
                    if row.startswith(PREFIX):
                        observations.setdefault(row, elapsed)
                if mode == "disabled" and SURVIVED in actual:
                    break
                time.sleep(0.02)
    except Exception as error:
        failure = type(error).__name__ + ": " + str(error)
    finally:
        if process is not None:
            if process.poll() is None:
                stopped = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)
    try:
        actual = rows(serial)
    except OSError as error:
        failure = "final serial read: " + str(error)
    markers = [row for row in actual if row.startswith(PREFIX)]
    required = [PREFIX + "FAILURE_PRESERVED status=DEVICE_ERROR", PREFIX + "ARMED seconds=2",
                PREFIX + ("DISABLED" if mode == "disabled" else "CONTROL_ARMED"), PREFIX + "STALL seconds=3"]
    if mode == "disabled":
        required.append(SURVIVED)
    ordered = all(row in markers for row in required)
    if ordered:
        ordered = [markers.index(row) for row in required] == sorted(markers.index(row) for row in required)
    checks = dict(required_markers_once=all(markers.count(row) == 1 for row in required), ordered_markers=ordered,
                  no_failure=failure is None and not any("ERROR" in row and "FAILURE_PRESERVED" not in row for row in markers),
                  process_reaped=process is not None and process.returncode is not None, within_deadline=not timed_out,
                  binary_copy_preserved=sha(binary) == sha(copied))
    if mode == "disabled":
        checks["survived_real_delay"] = SURVIVED in markers
        # Host observation can first see multiple buffered rows together; do not
        # pretend serial receive timestamps are guest timer measurements.
    else:
        checks["natural_reset_exit"] = process is not None and process.returncode == 0 and not stopped
        checks["armed_did_not_survive"] = SURVIVED not in markers
    result = dict(mode=mode, passed=all(checks.values()), checks=checks, command=command,
                  markers=markers, marker_observed_seconds=observations,
                  elapsed_seconds=round(time.monotonic()-start, 3), failure=failure,
                  qemu_exit_code=process.returncode if process else None, stopped_by_harness=stopped,
                  timed_out=timed_out, transient_serial_retries=retries, efi_sha256=sha(binary))
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disabled-efi", type=Path, required=True)
    parser.add_argument("--armed-efi", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    if not 10 <= args.timeout <= 60:
        parser.error("timeout must be between 10 and 60 seconds (five seconds reserved for cleanup)")
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    args.qemu = shutil.which(args.qemu) or args.qemu
    for field in ["disabled_efi", "armed_efi", "ovmf_code", "ovmf_vars"]:
        setattr(args, field, getattr(args, field).resolve(strict=True))
    sources = [Path(__file__).resolve(), args.disabled_efi, args.armed_efi, args.ovmf_code, args.ovmf_vars, Path(args.qemu).resolve()]
    before = {str(path): sha(path) for path in sources}
    disabled = case(args, args.disabled_efi, "disabled", args.output / "disabled")
    armed = case(args, args.armed_efi, "armed", args.output / "armed")
    preserved = before == {str(path): sha(path) for path in sources}
    receipt = dict(schema="nextcore.watchdog-ovmf.v1", passed=disabled["passed"] and armed["passed"] and preserved,
                   disabled=disabled, armed=armed, sources_sha256=before, sources_preserved=preserved,
                   original_images_used=False, r21_watchdog_cause_verified=False,
                   physical_boot_verified=False, macos_boot_verified=False)
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed":receipt["passed"], "receipt":str(args.output / "receipt.json")}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
