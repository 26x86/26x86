"""Mount only a kernel-command-line PARTUUID on a verified USB descendant.

No internal block device is probed. Discovery starts only at the USB bus.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import uuid


def requested_uuid(cmdline: str) -> str | None:
    values = [word.split("=", 1)[1] for word in cmdline.split() if word.startswith("venfire.data_partuuid=")]
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("Duplicate data partition selection is forbidden")
    normalized = str(uuid.UUID(values[0]))
    if values[0].lower() != normalized:
        raise ValueError("Data PARTUUID must use canonical UUID notation")
    return normalized


def usb_partition_paths(sys_root=Path("/sys")) -> list[Path]:
    usb_bus = (sys_root / "bus/usb").resolve()
    devices = sys_root / "bus/usb/devices"
    found = set()
    if not devices.is_dir():
        return []
    for usb_device in devices.iterdir():
        device_root = usb_device.resolve()
        if not device_root.is_relative_to((sys_root / "devices").resolve()):
            continue
        for attribute in device_root.rglob("partition"):
            partition = attribute.parent.resolve()
            if not re.fullmatch(r"[A-Za-z0-9._!-]+", partition.name):
                continue
            if any((ancestor / "subsystem").is_symlink() and
                   (ancestor / "subsystem").resolve() == usb_bus for ancestor in [partition, *partition.parents]):
                found.add(partition)
    return sorted(found)


def select_partition(expected: str, *, sys_root=Path("/sys"), dev_root=Path("/dev"), probe=None) -> Path:
    matches = []
    for sys_path in usb_partition_paths(sys_root):
        device = dev_root / sys_path.name
        if probe is None:
            try:
                info = device.lstat()
            except FileNotFoundError:
                continue  # devtmpfs can lag the USB sysfs entry during discovery.
            if not stat.S_ISBLK(info.st_mode):
                continue
            identity = (sys_path / "dev").read_text().strip()
            if not re.fullmatch(r"[0-9]+:[0-9]+", identity):
                continue
            if identity != f"{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}":
                continue  # Bind the USB sysfs evidence to this devtmpfs node.
            result = subprocess.run(["/sbin/blkid", "-c", "/dev/null", "-p", "-s", "PART_ENTRY_UUID", "-o", "value", str(device)],
                                    text=True, capture_output=True, timeout=5, check=False)
            actual = result.stdout.strip().lower() if result.returncode == 0 else ""
        else:
            actual = probe(device)
        if actual == expected:
            matches.append(device)
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one USB partition with configured PARTUUID; found {len(matches)}")
    return matches[0]


def mount_selected(cmdline: str, profile: str, emit=print, *, target=Path("/data")) -> Path | None:
    expected = requested_uuid(cmdline)
    if expected is None:
        return None
    deadline = time.monotonic() + 10
    while True:
        try:
            device = select_partition(expected)
            break
        except ValueError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.5)
    target.mkdir(exist_ok=False)
    before = device.stat().st_rdev
    def mount(options):
        subprocess.run(["/bin/busybox", "mount", "-t", "ext4", "-o", options, str(device), str(target)],
                       check=True, capture_output=True, text=True, timeout=15)
    mount("ro,noload,nodev,nosuid")
    try:
        marker_path = target / "VENFIRE_DATA.json"
        marker_info = marker_path.lstat()
        if not stat.S_ISREG(marker_info.st_mode) or marker_info.st_size > 65536:
            raise ValueError("Invalid USB data marker")
        marker = json.loads(marker_path.read_text())
        if (not isinstance(marker, dict) or type(marker.get("schema")) is not int or
                marker.get("schema") != 1 or marker.get("partuuid") != expected or marker.get("profile") != profile):
            raise ValueError("USB data marker does not match the explicit image profile/PARTUUID")
    finally:
        subprocess.run(["/bin/busybox", "umount", str(target)], check=True, timeout=10)
    if select_partition(expected) != device or device.stat().st_rdev != before:
        raise ValueError("USB partition changed before writable mount")
    mount("rw,nodev,nosuid")
    emit("VENFIRE_USB|DATA|MATCHED_USB_PARTUUID")
    emit("Mounted only explicitly selected USB data partition: " + str(device))
    if "venfire.data_fixture=1" in cmdline.split():
        try:
            if marker.get("self_authored_fixture") is not True:
                raise ValueError("Fixture mode requires a self-authored fixture marker")
            check_large_fixture(target, emit)
        except Exception:
            subprocess.run(["/bin/busybox", "umount", str(target)], check=True, timeout=10)
            raise
    return target


def check_large_fixture(target: Path, emit=print):
    base, overlay = target / "large-base.fixture", target / "usb-fixture-overlay.qcow2"
    offset = 5 * 1024**3
    expected_tail = b"VENFIRE_SELF_AUTHORED_LARGE_FILE"
    base_info = base.lstat()
    if not stat.S_ISREG(base_info.st_mode) or base_info.st_size != offset + 8192:
        raise ValueError("Large fixture must be the exact self-authored sparse regular file")
    def check_base():
        with base.open("rb") as stream:
            stream.seek(offset)
            if stream.read(4096) != bytes(4096) or stream.read(len(expected_tail)) != expected_tail:
                raise ValueError("Large base fixture samples changed")
    check_base()
    if overlay.exists() or overlay.is_symlink():
        if overlay.is_symlink() or not overlay.is_file():
            raise ValueError("Invalid existing fixture overlay")
        info = subprocess.run(["/usr/bin/qemu-img", "info", "--output=json", str(overlay)],
                              check=True, capture_output=True, text=True, timeout=20)
        parsed = json.loads(info.stdout)
        if parsed.get("format") != "qcow2" or parsed.get("full-backing-filename") != str(base):
            raise ValueError("Fixture overlay backing does not match")
        # Read persisted content before any new write can mask lost data.
        subprocess.run(["/usr/bin/qemu-io", "-f", "qcow2", "-c", f"read -P 0x5a {offset} 4096", str(overlay)],
                       check=True, capture_output=True, text=True, timeout=30)
        emit("VENFIRE_USB|COW_REOPEN|PASS")
    else:
        subprocess.run(["/usr/bin/qemu-img", "create", "-f", "qcow2", "-F", "raw", "-b", str(base), str(overlay)],
                       check=True, capture_output=True, text=True, timeout=20)
    for action in ("write", "read"):
        subprocess.run(["/usr/bin/qemu-io", "-f", "qcow2", "-c", f"{action} -P 0x5a {offset} 4096", str(overlay)],
                       check=True, capture_output=True, text=True, timeout=30)
    check_base()
    descriptor = os.open(target / "usb-fixture.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError("Fixture evidence destination is not a regular file")
    with os.fdopen(descriptor, "a") as stream:
        stream.write("PASS: >5GiB sparse base, COW write/read, base samples preserved\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.sync()
    emit("VENFIRE_USB|LARGE_COW|PASS")
