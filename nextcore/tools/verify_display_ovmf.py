#!/usr/bin/env python3
"""Capture an actual OVMF/Nextcore VGA surface; never assert OS or GPU-driver boot."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import plistlib
import re
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import zlib


def save_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_info(path: Path) -> dict:
    """Validate chunk boundaries/CRCs and dimensions, without inferring content."""
    if not 0 < path.stat().st_size <= 32 * 1024 * 1024:
        raise ValueError("capture size outside 1..32 MiB")
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("capture is not PNG")
    offset, dimensions, image_data = 8, None, False
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:end - 4]
        if zlib.crc32(kind + payload) != struct.unpack_from(">I", data, end - 4)[0]:
            raise ValueError("PNG CRC mismatch")
        if offset == 8:
            if kind != b"IHDR" or length != 13:
                raise ValueError("missing PNG header")
            dimensions = struct.unpack_from(">II", payload)
            if not all(0 < size <= 16384 for size in dimensions):
                raise ValueError("PNG dimensions out of bounds")
        image_data |= kind == b"IDAT" and length > 0
        if kind == b"IEND":
            if length or end != len(data) or not image_data or dimensions is None:
                raise ValueError("invalid PNG end")
            return {"path": str(path), "width": dimensions[0], "height": dimensions[1],
                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        offset = end
    raise ValueError("missing PNG end")


class Qmp:
    def __init__(self, path: Path, deadline: float, transcript: list):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.buffer = b""
        self.deadline = deadline
        self.transcript = transcript
        self.sequence = 0
        try:
            while True:
                try:
                    self.sock.connect(str(path))
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("QMP endpoint did not become ready")
                    time.sleep(0.05)
            if "QMP" not in self.receive():
                raise ValueError("missing QMP greeting")
            self.command("qmp_capabilities")
        except BaseException:
            self.sock.close()
            raise

    def receive(self) -> dict:
        while b"\n" not in self.buffer:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("QMP capture deadline exceeded")
            self.sock.settimeout(min(remaining, 5))
            part = self.sock.recv(65536)
            if not part:
                raise ConnectionError("QMP closed before response")
            self.buffer += part
            if len(self.buffer) > 1024 * 1024:
                raise ValueError("QMP response exceeds bound")
        line, self.buffer = self.buffer.split(b"\n", 1)
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("QMP response is not an object")
        self.transcript.append({"received": value})
        return value

    def command(self, name: str, arguments: dict | None = None):
        self.sequence += 1
        request = {"execute": name, "id": self.sequence}
        if arguments is not None:
            request["arguments"] = arguments
        self.transcript.append({"sent": request})
        self.sock.sendall(json.dumps(request).encode() + b"\n")
        while True:
            response = self.receive()
            if response.get("id") != self.sequence:
                continue
            if "error" in response:
                raise RuntimeError(f"QMP {name}: {response['error']}")
            if "return" not in response:
                raise ValueError("QMP reply lacks return value")
            return response["return"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True, help="compiled Nextcore BOOTX64.efi")
    parser.add_argument("--output", type=Path, required=True, help="fresh receipt directory; Linux /tmp recommended")
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--display", choices=("none", "gtk", "sdl"), default="none")
    parser.add_argument("--vnc-display", type=int, help="optional IPv4 loopback VNC display 0..99 (port 5900+n)")
    parser.add_argument("--timeout", type=float, default=30, help="guest/QMP capture deadline, 1..60 seconds")
    parser.add_argument("--hold-seconds", type=float, default=0, help="retain paused screen for viewing, 0..60 seconds")
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        if any(ch in str(output) for ch in (",", "\n", "\r", "\0")):
            raise ValueError("output path contains QEMU option delimiters/control characters")
        output.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        parser.error(f"cannot create a fresh receipt directory: {error}")
    report = {"schema": "nextcore.ovmf-display/1", "passed": False,
              "layer": "x86 UEFI console / QEMU standard VGA / host framebuffer capture",
              "efi_entry_observed": False, "no_target_observed": False,
              "host_framebuffer_captured": False, "gop_protocol_directly_verified": False,
              "nextcore_screen_text_visually_verified": False,
              "physical_display_verified": False, "metal_verified": False,
              "xnu_executed": False, "macos_userspace_reached": False, "macos_boot_verified": False,
              "process_started": False, "process_reaped": False,
              "original_inputs_preserved": None, "display_requested": args.display,
              "vnc_requested": args.vnc_display, "error": None}
    inputs, before, transcript = {}, {}, []
    process, qmp = None, None
    started = time.monotonic()
    try:
        if os.name != "posix":
            raise ValueError("run this harness inside Linux/WSL (QMP Unix socket required)")
        if not math.isfinite(args.timeout) or not 1 <= args.timeout <= 60:
            raise ValueError("timeout must be 1..60 seconds")
        if not math.isfinite(args.hold_seconds) or not 0 <= args.hold_seconds <= 60:
            raise ValueError("hold-seconds must be 0..60 seconds")
        if args.vnc_display is not None and not 0 <= args.vnc_display <= 99:
            raise ValueError("vnc-display must be 0..99")
        executable = shutil.which(args.qemu)
        if executable is None:
            raise FileNotFoundError(f"QEMU executable unavailable: {args.qemu}")
        for name in ("efi", "ovmf_code", "ovmf_vars"):
            path = getattr(args, name).resolve(strict=True)
            if (not path.is_file() or not 0 < path.stat().st_size <= 64 * 1024 * 1024
                    or any(ch in str(path) for ch in (",", "\n", "\r", "\0"))):
                raise ValueError(f"invalid {name} file/path")
            inputs[name] = path
        before = {name: digest(path) for name, path in inputs.items()}
        image = inputs["efi"].read_bytes()
        pe = struct.unpack_from("<I", image, 60)[0] if len(image) >= 64 else len(image)
        if (image[:2] != b"MZ" or pe + 94 > len(image) or image[pe:pe + 4] != b"PE\0\0"
                or struct.unpack_from("<H", image, pe + 4)[0] != 0x8664
                or struct.unpack_from("<H", image, pe + 24)[0] != 0x20b
                or struct.unpack_from("<H", image, pe + 92)[0] != 10):
            raise ValueError("EFI input is not an x86_64 PE32+ EFI application")
        report["qemu_version"] = subprocess.run([executable, "--version"], check=True,
            capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
        report["display_capabilities"] = subprocess.run([executable, "-display", "help"], check=True,
            capture_output=True, text=True, timeout=10).stdout.splitlines()
        if args.display not in [line.strip() for line in report["display_capabilities"]]:
            raise ValueError("requested display backend is unavailable")
        boot, config = output / "esp/EFI/BOOT", output / "esp/EFI/OC"
        boot.mkdir(parents=True)
        config.mkdir()
        shutil.copyfile(inputs["efi"], boot / "BOOTX64.EFI")
        (config / "config.plist").write_bytes(plistlib.dumps({"Misc": {"Entries": []}}))
        variables = output / "vars.fd"
        shutil.copyfile(inputs["ovmf_vars"], variables)
        serial = output / "serial.log"
        # A short private Unix path avoids AF_UNIX limits on long /mnt/c paths.
        with tempfile.TemporaryDirectory(prefix="nextcore-display-") as sockets:
            endpoint = Path(sockets) / "qmp.sock"
            command = [executable, "-no-user-config", "-machine", "q35,accel=tcg", "-cpu", "Nehalem",
                "-m", "256", "-smp", "1", "-vga", "std", "-display", args.display,
                "-monitor", "none", "-qmp", f"unix:{endpoint},server=on,wait=off",
                "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
                "-drive", f"if=pflash,format=raw,readonly=on,file={inputs['ovmf_code']}",
                "-drive", f"if=pflash,format=raw,file={variables}",
                "-drive", f"format=raw,file=fat:rw:{output / 'esp'}"]
            if args.vnc_display is not None:
                command += ["-vnc", f"127.0.0.1:{args.vnc_display}"]
            save_json(output / "command.json", command)
            with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
                report.update(process_started=True, qemu_pid=process.pid)
                deadline = time.monotonic() + args.timeout
                qmp = Qmp(endpoint, deadline, transcript)
                while time.monotonic() < deadline and process.poll() is None:
                    log = serial.read_text(errors="replace") if serial.exists() else ""
                    lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log).splitlines()
                    report["efi_entry_observed"] = "NEXTCORE: EFI_ENTRY" in lines
                    report["no_target_observed"] = "NEXTCORE: NO_BOOT_TARGET" in lines
                    if report["efi_entry_observed"] and report["no_target_observed"]:
                        if lines.index("NEXTCORE: EFI_ENTRY") >= lines.index("NEXTCORE: NO_BOOT_TARGET"):
                            raise ValueError("EFI markers out of order")
                        break
                    time.sleep(0.02)
                if not (report["efi_entry_observed"] and report["no_target_observed"]):
                    raise TimeoutError("expected Nextcore markers absent before process exit/deadline")
                qmp.command("stop")
                screenshot = output / "screen.png"
                qmp.command("screendump", {"filename": str(screenshot), "format": "png"})
                report["screenshot"] = png_info(screenshot)
                report["host_framebuffer_captured"] = True
                if args.vnc_display is not None:
                    vnc = qmp.command("query-vnc")
                    report["vnc"] = vnc
                    if not vnc.get("enabled") or vnc.get("host") != "127.0.0.1":
                        raise ValueError("loopback VNC listener not confirmed")
                if args.hold_seconds:
                    process.wait(timeout=args.hold_seconds)
    except subprocess.TimeoutExpired:
        # The optional viewing hold expiring is intentional, unlike preflight timeouts.
        if not report["host_framebuffer_captured"]:
            report["error"] = "preflight subprocess timeout"
    except (Exception, KeyboardInterrupt) as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if qmp is not None:
            qmp.sock.close()
        if process is not None:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                report["process_reaped"] = process.poll() is not None
                report["qemu_exit_code"] = process.returncode
            except (OSError, subprocess.TimeoutExpired) as error:
                report["error"] = f"cleanup failed: {error}"
        try:
            after = {name: digest(path) for name, path in inputs.items()}
            report["input_sha256_before"] = before
            report["input_sha256_after"] = after
            report["original_inputs_preserved"] = bool(before) and before == after
        except OSError as error:
            report["error"] = f"input readback failed: {error}"
        report["input_paths"] = {name: str(path) for name, path in inputs.items()}
        report["passed"] = bool(not report["error"] and report["host_framebuffer_captured"]
            and report["efi_entry_observed"] and report["no_target_observed"]
            and report["process_reaped"] and report["original_inputs_preserved"])
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        save_json(output / "qmp.json", transcript)
        save_json(output / "report.json", report)
    print(json.dumps(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
