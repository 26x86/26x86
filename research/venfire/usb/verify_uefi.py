#!/usr/bin/env python3
"""Boot an image as read-only USB under OVMF and verify actual input and output."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import time


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(image: Path, output: Path, *, timeout=240, qemu="qemu-system-x86_64", expect_data=False, expect_large_cow=False,
           expect_cow_reopen=False, expect_network=False, expect_restore_helper=False, interactive_network=False):
    if not 0 < timeout <= 600:
        raise ValueError("timeout must be between 0 and 600 seconds")
    if not stat.S_ISREG(image.lstat().st_mode):
        raise ValueError("UEFI verification accepts a regular image file only, never a host block device or symlink")
    if (expect_large_cow or expect_cow_reopen) and not expect_data:
        raise ValueError("COW verification requires explicit data-image writes")
    if interactive_network and not expect_network:
        raise ValueError("Interactive network verification requires an explicitly attached network")
    output.mkdir(parents=True, exist_ok=False)
    image = image.resolve()
    image_hash_before = file_hash(image)
    vars_path = output / "OVMF_VARS.fd"
    shutil.copy2("/usr/share/OVMF/OVMF_VARS_4M.fd", vars_path)
    serial_path, stderr_path = output / "serial.log", output / "stderr.log"
    socket_path = output / "qmp.sock"
    command = [qemu, "-machine", "q35,i8042=off", "-accel", "tcg", "-cpu", "max,vendor=GenuineIntel",
               "-m", "2048M", "-smp", "2", "-display", "none", "-vga", "std",
               "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
               "-drive", f"if=pflash,format=raw,file={str(vars_path).replace(',', ',,')}",
               "-device", "qemu-xhci,id=xhci", "-drive", f"if=none,id=stick,format=raw,readonly={'off' if expect_data else 'on'},file={str(image).replace(',', ',,')}",
               "-device", "usb-storage,bus=xhci.0,drive=stick,bootindex=1",
               "-device", "usb-kbd,bus=xhci.0", "-serial", "file:" + str(serial_path),
               "-qmp", "unix:" + str(socket_path) + ",server=on,wait=off", "-no-reboot"]
    command += (["-netdev", "user,id=net0", "-device", "virtio-net-pci,netdev=net0"]
                if expect_network else ["-net", "none"])
    started = time.monotonic()
    client = None
    stream = None
    serial = ""
    input_sent = False
    network_stage = 0
    returned_menu_count = 0
    initial_menu_captured = False
    screenshot = output / "framebuffer.ppm"
    with stderr_path.open("w") as stderr:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stderr)
        try:
            while time.monotonic() - started < timeout and process.poll() is None:
                if client is None and socket_path.exists():
                    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    client.settimeout(5)
                    client.connect(str(socket_path))
                    stream = client.makefile("rwb", buffering=0)
                    json.loads(stream.readline())

                    def qmp(name, arguments=None):
                        request = {"execute": name}
                        if arguments is not None:
                            request["arguments"] = arguments
                        stream.write(json.dumps(request).encode() + b"\n")
                        while True:
                            reply = json.loads(stream.readline())
                            if "event" not in reply:
                                if "error" in reply:
                                    raise RuntimeError(reply["error"])
                                return reply.get("return")
                    qmp("qmp_capabilities")
                serial = serial_path.read_text(errors="replace") if serial_path.exists() else ""
                if "VENFIRE_USB|MENU_READY|keyboard" in serial and not input_sent and client:
                    def press(key):
                        qmp("human-monitor-command", {"command-line": "sendkey " + key})
                        time.sleep(0.25)
                    if not initial_menu_captured:
                        time.sleep(0.75)  # Allow deferred framebuffer updates to finish.
                        qmp("screendump", {"filename": str(output / "menu-before-input.ppm")})
                        (output / "usb-devices.txt").write_text(qmp("human-monitor-command", {"command-line": "info usb"}))
                        initial_menu_captured = True
                    # q35 i8042=off makes USB HID the sole keyboard path.
                    if interactive_network and network_stage == 0:
                        press("6")
                        press("ret")
                        network_stage = 1
                    if network_stage == 1 and "VENFIRE_USB|NETWORK_MENU|SELECT" in serial:
                        press("1")
                        press("ret")
                        network_stage = 2
                    if network_stage in (1, 2) and "VENFIRE_USB|NETWORK_MENU|DONE" in serial:
                        press("ret")
                        returned_menu_count = serial.count("VENFIRE_USB|MENU_READY|keyboard")
                        network_stage = 3
                    if network_stage == 3 and serial.count("VENFIRE_USB|MENU_READY|keyboard") > returned_menu_count:
                        time.sleep(0.75)
                        qmp("screendump", {"filename": str(output / "menu-after-network.ppm")})
                        network_stage = 4
                    if not interactive_network or network_stage == 4:
                        press("1")
                        press("ret")
                        input_sent = True
                if "VENFIRE_USB|KEYBOARD|ACCEPTED" in serial and client:
                    time.sleep(0.5)
                    qmp("screendump", {"filename": str(screenshot)})
                    qmp("quit")
                    break
                time.sleep(0.25)
        finally:
            if client and process.poll() is None and not screenshot.exists():
                try:
                    qmp("screendump", {"filename": str(output / "last-frame.ppm")})
                except (OSError, ValueError, RuntimeError):
                    pass
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if stream:
                stream.close()
            if client:
                client.close()
    serial = serial_path.read_text(errors="replace") if serial_path.exists() else ""
    expected = ["VENFIRE_USB|FIRMWARE|UEFI", "VENFIRE_USB|USERSPACE|READY",
                "VENFIRE_USB|HOST_POLICY|PASS", "VENFIRE_USB|CONFORMANCE|PASS",
                "VENFIRE_USB|MENU_READY|keyboard", "VENFIRE_USB|KEYBOARD|ACCEPTED"]
    if expect_data:
        expected.append("VENFIRE_USB|DATA|MATCHED_USB_PARTUUID")
    if expect_large_cow:
        expected.append("VENFIRE_USB|LARGE_COW|PASS")
    if expect_cow_reopen:
        expected.append("VENFIRE_USB|COW_REOPEN|PASS")
    if expect_network:
        expected.extend(["VENFIRE_USB|DHCP|PASS", "VENFIRE_USB|TSS_HTTPS|PASS"])
    if expect_restore_helper:
        expected.append("VENFIRE_USB|RESTORE_HELPER|READY")
    if interactive_network:
        expected.extend(["VENFIRE_USB|NETWORK_MENU|SELECT", "VENFIRE_USB|NETWORK_MENU|DONE"])
    found = {marker: marker in serial for marker in expected}
    image_hash_after = file_hash(image)
    report = {"schema": 1, "passed": all(found.values()) and screenshot.is_file() and (expect_data or image_hash_before == image_hash_after),
              "layer": "OVMF UEFI -> USB xHCI mass storage -> x86_64 Linux -> nested AArch64 TCG",
              "physical_usb_verified": False, "macos_boot_verified": False,
              "read_only_image": not expect_data, "self_authored_data_writes_enabled": expect_data,
              "ps2_controller_enabled": False,
              "explicit_user_network_attached": expect_network,
              "network_configured_through_usb_keyboard_menu": interactive_network and network_stage == 4,
              "image_sha256_before": image_hash_before, "image_sha256_after": image_hash_after,
              "command": command, "markers": found, "elapsed_seconds": round(time.monotonic() - started, 3),
              "serial_log": str(serial_path), "framebuffer": str(screenshot), "qemu_returncode": process.returncode}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new directory; use a short Unix socket path")
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--expect-data", action="store_true", help="enable writes to this self-authored test disk image for explicit USB data verification")
    parser.add_argument("--expect-large-cow", action="store_true")
    parser.add_argument("--expect-cow-reopen", action="store_true", help="require persisted COW data to be read before this boot writes")
    parser.add_argument("--expect-network", action="store_true", help="attach a QEMU user-mode NIC and require actual DHCP/TSS HTTPS success")
    parser.add_argument("--expect-restore-helper", action="store_true")
    parser.add_argument("--interactive-network", action="store_true", help="select menu 6 and its wired interface through USB HID, without a startup DHCP flag")
    args = parser.parse_args()
    if (args.expect_large_cow or args.expect_cow_reopen) and not args.expect_data:
        parser.error("COW checks require --expect-data")
    report = verify(args.image, args.output, timeout=args.timeout, expect_data=args.expect_data,
                    expect_large_cow=args.expect_large_cow, expect_cow_reopen=args.expect_cow_reopen,
                    expect_network=args.expect_network, expect_restore_helper=args.expect_restore_helper,
                    interactive_network=args.interactive_network)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
