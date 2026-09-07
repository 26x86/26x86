#!/usr/bin/env python3
"""Calibrate VMApple TCG CPU execution with authored assembly and QMP."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    qemu = args.qemu.resolve(strict=True)
    out = args.output.resolve()
    if "," in str(out):
        parser.error("output path cannot contain commas")
    out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name("aarch64_execution_probe.S")
    subprocess.run(["aarch64-linux-gnu-as", "-o", str(out / "probe.o"), str(source)], check=True)
    subprocess.run(["aarch64-linux-gnu-objcopy", "-O", "binary", str(out / "probe.o"), str(out / "probe.bin")], check=True)
    for name in ("aux.raw", "root.raw"):
        with (out / name).open("xb") as file:
            file.truncate(8 * 1024 * 1024)
    transcript = []
    with tempfile.TemporaryDirectory(prefix="nextcore-qmp-") as temp:
        address = str(Path(temp) / "control.sock")
        command = [str(qemu), "-M", "vmapple,research-headless=on,research-stage2=on",
                   "-accel", "tcg,thread=single", "-cpu", "max", "-m", "256", "-smp", "1",
                   "-bios", str(out / "probe.bin"),
                   "-drive", f"if=pflash,index=0,format=raw,readonly=on,file={out / 'aux.raw'}",
                   "-drive", f"if=pflash,index=1,format=raw,readonly=on,file={out / 'root.raw'}",
                   "-display", "none", "-serial", "none", "-nic", "none", "-no-reboot",
                   "-d", "exec,cpu_reset", "-D", str(out / "exec.log"),
                   "-qmp", f"unix:{address},server=on,wait=off", "-S"]
        (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
        with (out / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stderr)
            try:
                deadline = time.monotonic() + 10
                while not Path(address).exists():
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError("QMP socket did not become ready")
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                    connection.settimeout(5)
                    connection.connect(address)
                    with connection.makefile("rwb", buffering=0) as channel:
                        transcript.append(json.loads(channel.readline()))

                        def request(name, arguments=None):
                            ident = len(transcript)
                            data = {"execute": name, "id": ident}
                            if arguments is not None:
                                data["arguments"] = arguments
                            transcript.append(data)
                            channel.write(json.dumps(data).encode() + b"\n")
                            while True:
                                response = json.loads(channel.readline())
                                transcript.append(response)
                                if response.get("id") == ident:
                                    if "error" in response:
                                        raise RuntimeError(response["error"])
                                    return response["return"]

                        request("qmp_capabilities")
                        before = request("human-monitor-command", {"command-line": "info registers"})
                        request("cont")
                        time.sleep(0.25)
                        state = request("query-status")
                        request("stop")
                        after = request("human-monitor-command", {"command-line": "info registers"})
                        request("quit")
                        process.wait(timeout=5)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                (out / "qmp.json").write_text(json.dumps(transcript, indent=2) + "\n")
    executed = bool(re.search(r"X0*0=0*2a(?:\s|$)", after, re.IGNORECASE))
    initial_zero = bool(re.search(r"X0*0=0+(?:\s|$)", before, re.IGNORECASE))
    trace = (out / "exec.log").read_text(errors="replace")
    report = {"schema": "nextcore.vmapple-cpu-probe.v1",
              "qemu_sha256": hashlib.sha256(qemu.read_bytes()).hexdigest(),
              "firmware_sha256": hashlib.sha256((out / "probe.bin").read_bytes()).hexdigest(),
              "registers_before": before, "registers_after": after,
              "run_state": state, "initial_x0_zero": initial_zero,
              "authored_instruction_executed": executed and initial_zero,
              "exec_trace_present": "Trace " in trace,
              "qemu_exit_code": process.returncode,
              "macos_boot_verified": False,
              "passed": executed and initial_zero and process.returncode == 0}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
