#!/usr/bin/env python3
"""Boot a production self-test image as read-only USB storage under OVMF."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify(directory: Path) -> dict:
    directory = directory.resolve()
    media = json.loads((directory / "media-report.json").read_text())
    image = directory / "26x86-sandbox-selftest.img"
    before = digest(image)
    if before != media["image_sha256"]:
        raise ValueError("Image no longer matches media receipt")
    output = directory / "production-usb-boot"
    output.mkdir(exist_ok=False)
    serial = output / "serial.log"
    screenshot = output / "screen.ppm"
    console = ""
    qmp_results = []
    with tempfile.TemporaryDirectory(prefix="26x86-usb-ovmf-") as tmp:
        p = Path(tmp)
        shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", p / "vars.fd")
        command = ["qemu-system-x86_64", "-machine", "q35,accel=tcg", "-cpu", "Nehalem",
                   "-m", "512", "-smp", "1", "-display", "none", "-serial", f"file:{serial}",
                   "-monitor", "none", "-qmp", f"unix:{p / 'qmp.sock'},server=on,wait=off",
                   "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
                   "-drive", f"if=pflash,format=raw,file={p / 'vars.fd'}",
                   "-device", "qemu-xhci,id=xhci", "-drive", f"if=none,id=media,format=raw,readonly=on,file={image}",
                   "-device", "usb-storage,bus=xhci.0,drive=media,removable=on,bootindex=0",
                   "-net", "none", "-no-reboot"]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and process.poll() is None:
                console = serial.read_text(errors="replace") if serial.exists() else ""
                if "JIT SELFTEST PASS" in console and "macOS boot not implemented" in console:
                    break
                time.sleep(0.1)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect(str(p / "qmp.sock"))
                f = sock.makefile("rwb", buffering=0)
                qmp_results.append(json.loads(f.readline()))
                for request in [{"execute": "qmp_capabilities"},
                                {"execute": "screendump", "arguments": {"filename": str(screenshot)}},
                                {"execute": "quit"}]:
                    f.write(json.dumps(request).encode() + b"\n")
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        result = json.loads(line)
                        qmp_results.append(result)
                        if "return" in result or "error" in result:
                            break
            process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            stderr = process.stderr.read() if process.stderr else ""
    console = serial.read_text(errors="replace") if serial.exists() else ""
    after = digest(image)
    passed = before == after and all(s in console for s in ["26x86 Apple Silicon Sandbox", "AIC WIRED IRQ SELFTEST PASS",
                                                           "JIT SELFTEST PASS", "macOS boot not implemented"])
    screenshot_file = None
    if screenshot.exists():
        screenshot_file = screenshot.name
        try:
            from PIL import Image
            with Image.open(screenshot) as visual:
                visual.save(output / "screen.png")
            screenshot_file = "screen.png"
        except ImportError:
            pass
    report = {"schema": 1, "passed": passed, "production_efi": True,
              "efi_sha256": media["efi_sha256"], "image_sha256_before": before, "image_sha256_after": after,
              "image_unchanged": before == after, "qemu_drive_readonly": True,
              "boot_path": "OVMF -> USB mass storage -> GPT ESP -> FAT32 -> EFI/BOOT/BOOTX64.EFI",
              "cpu_model": "Nehalem", "avx_available": False, "guest_linux_used": False,
              "macos_boot_verified": False, "physical_usb_verified": False, "physical_mac_verified": False,
              "console_markers_verified": passed, "screenshot": screenshot_file,
              "qemu_exit_code": process.returncode, "stderr": stderr, "qmp": qmp_results}
    (output / "boot-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    report = verify(parser.parse_args().directory)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
