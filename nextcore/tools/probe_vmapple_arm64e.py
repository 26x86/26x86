#!/usr/bin/env python3
"""Execute authored EL1/PAuth checks on the exact VMApple recovery CPU profile.

This verifies architectural CPU operations, not Apple ARM64e ABI or macOS boot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time


RECOVERY_CPU = "max,pauth=on,pauth-qarma5=on,cntfrq=24000000"
NO_PAUTH_CPU = "max,pauth=off,cntfrq=24000000"
CHECKS = (
    "el1_entry", "qarma5_advertised", "granule_16k_advertised",
    "counter_24mhz_progressing", "apia_key_readback", "pacia_autia_roundtrip",
    "authenticated_branch",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for data in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def registers(text: str) -> dict[int, int]:
    values: dict[int, int] = {}
    for match in re.finditer(r"\bX(\d{1,2})=([0-9a-fA-F]{1,16})(?=\s|$)", text):
        number = int(match.group(1))
        if number > 30 or number in values:
            raise ValueError("invalid or duplicate QMP register")
        values[number] = int(match.group(2), 16)
    return values


def evaluate(before: str, after: str, exit_code: int | None) -> dict[str, object]:
    initial, final = registers(before), registers(after)
    bitmap = final.get(20, 0)
    checks = {name: bool(bitmap & (1 << index)) for index, name in enumerate(CHECKS)}
    fresh = initial.get(0) == 0 and initial.get(20) == 0
    completed = final.get(0) == 0x64E and final.get(19) == 0 and bitmap == 0x7F
    # Inspect the underlying architectural observations as well as the guest's
    # bitmap so a truncated or inconsistent monitor response cannot pass.
    observations_match = (
        {4, 10, 11, 12, 13, 21, 22, 23, 24, 25, 26, 27, 28}.issubset(final)
        and final.get(21) == 4
        and ((final.get(22, 0) >> 4) & 15) != 0
        and ((final.get(23, 0) >> 20) & 15) in (1, 2)
        and final.get(24) == 24_000_000
        and final.get(26, 0) > final.get(25, 0)
        and final.get(12) == final.get(10)
        and final.get(13) == final.get(11)
        and 27 in final and not final[27] & 1
        and final.get(28) != final.get(4)
    )
    passed = fresh and completed and observations_match and all(checks.values()) and exit_code == 0
    return {
        "checks": checks,
        "initial_registers_zero": fresh,
        "guest_completed": completed,
        "architectural_observations_match": observations_match,
        "failed_check": final.get(19),
        "final_marker": final.get(0),
        "qemu_exit_code": exit_code,
        "passed": passed,
    }


def execute(qemu: Path, firmware: Path, output: Path, *, cpu: str) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    for name in ("aux.raw", "root.raw"):
        with (output / name).open("xb") as disk:
            disk.truncate(8 * 1024 * 1024)
    transcript: list[object] = []
    before = after = ""
    error = None
    process = None
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="nextcore-pauth-") as temporary:
        address = str(Path(temporary) / "qmp.sock")
        command = [
            str(qemu), "-M", "vmapple,research-headless=on,research-stage2=on",
            "-accel", "tcg,thread=single", "-cpu", cpu,
            "-m", "256", "-smp", "1", "-bios", str(firmware),
            "-drive", f"if=pflash,index=0,format=raw,readonly=on,file={output / 'aux.raw'}",
            "-drive", f"if=pflash,index=1,format=raw,readonly=on,file={output / 'root.raw'}",
            "-display", "none", "-serial", "none", "-nic", "none", "-no-reboot",
            "-d", "guest_errors,unimp", "-D", str(output / "qemu.log"),
            "-qmp", f"unix:{address},server=on,wait=off", "-S",
        ]
        (output / "command.json").write_text(json.dumps(command, indent=2) + "\n")
        with (output / "stderr.log").open("wb") as stderr:
            try:
                process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stderr)
                deadline = time.monotonic() + 10
                while not Path(address).exists():
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("QMP socket did not become ready")
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                    connection.settimeout(2)
                    connection.connect(address)
                    with connection.makefile("rwb", buffering=0) as channel:
                        def receive():
                            data = channel.readline(1024 * 1024 + 1)
                            if not data.endswith(b"\n") or len(data) > 1024 * 1024:
                                raise RuntimeError("missing or oversized QMP response")
                            response = json.loads(data)
                            transcript.append(response)
                            return response

                        receive()

                        def request(name, arguments=None):
                            ident = len(transcript)
                            data = {"execute": name, "id": ident}
                            if arguments is not None:
                                data["arguments"] = arguments
                            transcript.append(data)
                            channel.write(json.dumps(data).encode() + b"\n")
                            while time.monotonic() < deadline:
                                response = receive()
                                if response.get("id") == ident:
                                    if "error" in response:
                                        raise RuntimeError(str(response["error"]))
                                    return response["return"]
                            raise TimeoutError("QMP request deadline")

                        def snapshot():
                            return request("human-monitor-command", {"command-line": "info registers"})

                        request("qmp_capabilities")
                        before = snapshot()
                        while time.monotonic() < deadline - 1:
                            request("cont")
                            time.sleep(0.1)
                            request("stop")
                            after = snapshot()
                            if registers(after).get(0) in (0x64E, 0xBAD):
                                break
                        request("quit")
                        process.wait(timeout=2)
            except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=2)
                (output / "qmp.json").write_text(json.dumps(transcript, indent=2) + "\n")
    report = evaluate(before, after, process.returncode if process is not None else None)
    report.update({
        "schema": "nextcore.vmapple-arm64e-cpu-probe/1",
        "cpu": cpu,
        "registers_before": before, "registers_after": after,
        "qemu_sha256": sha256(qemu), "firmware_sha256": sha256(firmware),
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "process_terminated": process is not None and process.poll() is not None,
        "error": error,
        "arm64e_abi_verified": False, "macos_boot_verified": False,
    })
    report["passed"] = report["passed"] and error is None and report["process_terminated"]
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args(argv)
    qemu = args.qemu.resolve(strict=True)
    output = args.output.resolve()
    if "," in str(output):
        parser.error("output cannot contain commas")
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name("aarch64_pauth_probe.S")
    clang = shutil.which(args.clang)
    objcopy = shutil.which("llvm-objcopy")
    if clang is None or objcopy is None:
        parser.error("clang and llvm-objcopy are required")
    commands = [
        [clang, "--target=aarch64-none-elf", "-c", str(source), "-o", str(output / "probe.o")],
        [objcopy, "-O", "binary", str(output / "probe.o"), str(output / "probe.bin")],
    ]
    (output / "build-commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    for command in commands:
        subprocess.run(command, check=True, timeout=30)
    positive = execute(qemu, output / "probe.bin", output / "positive", cpu=RECOVERY_CPU)
    summary = {"positive": positive, "passed": positive["passed"]}
    if args.negative_control:
        negative = execute(qemu, output / "probe.bin", output / "negative", cpu=NO_PAUTH_CPU)
        negative_rejected = (
            not negative["passed"] and negative["failed_check"] == 2
            and negative["final_marker"] == 0xBAD
            and negative["checks"]["el1_entry"]
            and not negative["checks"]["qarma5_advertised"]
            and negative["process_terminated"] and negative["error"] is None
            and negative["qemu_exit_code"] == 0
        )
        summary.update({"negative": negative, "negative_rejected": negative_rejected})
        summary["passed"] = summary["passed"] and negative_rejected
    (output / "report.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
