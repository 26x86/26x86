#!/usr/bin/env python3
"""Build a UEFI USB image without mounting or opening a host disk.

Requires Linux, an installed generic kernel, GNU GRUB EFI tools, mtools, kmod,
BusyBox and Python. Input executables must come from the trusted local build.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import sysconfig
import uuid
import zlib

SECTOR = 512
MIB = 1024 * 1024
ESP_GUID = uuid.UUID("c12a7328-f81f-11d2-ba4b-00a0c93ec93b")
LINUX_GUID = uuid.UUID("0fc63daf-8483-4772-8e79-3d69d8477de4")
SOURCE = Path(__file__).resolve().parent.parent
MODULES = ("xhci_pci", "ehci_pci", "ohci_pci", "uhci_hcd", "usbhid", "hid_generic",
           "hid_apple", "applesmc", "usb_storage", "uas", "nvme", "ahci", "virtio_pci", "virtio_blk",
           "bochs", "efifb", "simpledrm", "ext4", "virtio_net", "e1000", "e1000e", "tg3", "igb",
           "r8169", "r8152", "ax88179_178a", "usbnet", "cdc_ether", "cdc_ncm")


def run(command: list[str], **kwargs):
    return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(MIB), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_restore_profile(profile_path, destination, *, available_bytes):
    """Copy explicitly selected regular assets into the new USB data image.

    Original bytes are verified before/after and copied files have their own
    hashes. This bundles source inputs, not tickets or a claimed boot result.
    """
    if str(SOURCE) not in sys.path:
        sys.path.insert(0, str(SOURCE))
    from venfire.artifacts import create_manifest, read_regular, require_intact
    from venfire.restore_chain import load_profile
    profile = load_profile(profile_path)
    named = {name: profile[name] for name in ("firmware", "aux", "disk", "build_manifest", "ibss", "ibec")}
    named.update(profile["components"])
    sources = create_manifest(list(dict.fromkeys([str(profile_path), *named.values()])))
    entries = {entry.path: entry for entry in sources.artifacts}
    required = sum(entries[str(Path(path).absolute())].size_bytes for path in named.values())
    if required + 512 * MIB > available_bytes:
        raise ValueError("USB data partition needs asset bytes plus at least 512 MiB working space")
    destination.mkdir(parents=True, exist_ok=False)
    asset_root = destination / "restore-assets"
    asset_root.mkdir()
    receipt = {"schema": 1, "assets": {}, "originals_preserved": False,
               "macos_boot_verified": False, "tickets_included": False}
    rewritten = dict(profile)
    rewritten["components"] = {}
    try:
        require_intact(sources)
        for name, source in named.items():
            relative = "restore-assets/" + name + ".bin"
            target = destination / relative
            copied_hash = hashlib.sha256()
            count = 0
            with read_regular(source) as stream, target.open("xb") as output:
                for block in iter(lambda: stream.read(MIB), b""):
                    copied_hash.update(block)
                    count += len(block)
                    if block.strip(b"\0"):
                        output.write(block)
                    else:
                        output.seek(len(block), 1)
                output.truncate(count)
            expected = entries[str(Path(source).absolute())]
            if count != expected.size_bytes or copied_hash.hexdigest() != expected.sha256 or file_hash(target) != expected.sha256:
                raise ValueError("Restore asset changed while bundling: " + name)
            target.chmod(0o444)
            receipt["assets"][name] = {"path": relative, "size_bytes": count, "sha256": expected.sha256}
            if name in profile["components"]:
                rewritten["components"][name] = relative
            else:
                rewritten[name] = relative
        (destination / "restore-profile.json").write_text(json.dumps(rewritten, indent=2) + "\n")
    finally:
        require_intact(sources)
    receipt["originals_preserved"] = True
    return receipt


def read_profile(project: Path) -> str:
    parsed = ast.parse((project / "venfire/_build_profile.py").read_text())
    nodes = parsed.body
    if nodes and isinstance(nodes[0], ast.Expr) and isinstance(nodes[0].value, ast.Constant) and isinstance(nodes[0].value.value, str):
        nodes = nodes[1:]
    if (len(nodes) != 1 or not isinstance(nodes[0], ast.Assign) or len(nodes[0].targets) != 1 or
            not isinstance(nodes[0].targets[0], ast.Name) or nodes[0].targets[0].id != "BUILD_PROFILE" or
            not isinstance(nodes[0].value, ast.Constant)):
        raise ValueError("Build profile must contain exactly one literal BUILD_PROFILE assignment")
    value = nodes[0].value.value
    if value not in ("release", "developer-nonredistributable"):
        raise ValueError("Explicit release or developer-nonredistributable build profile required")
    marker_path = project / "DEVELOPMENT_ONLY.json"
    if value == "release" and marker_path.exists():
        raise ValueError("Release profile cannot carry a developer artifact marker")
    if value == "developer-nonredistributable":
        marker = json.loads(marker_path.read_text())
        if (marker.get("schema") != 1 or marker.get("build_profile") != value or
                marker.get("redistribution_permitted") is not False or
                marker.get("intel_avx2_required") is not True or
                marker.get("guest_trust_bypassed") is not False):
            raise ValueError("Developer marker contradicts required build policy")
        if not (project / "DEVELOPMENT_POLICY.md").is_file():
            raise ValueError("Developer policy document is required")
    return value


def copy_file(source: Path, root: Path, destination: str | None = None) -> Path:
    destination_path = root / (destination or str(source)).lstrip("/")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source.resolve(strict=True), destination_path)
    return destination_path


def copy_libraries(binary: Path, root: Path) -> list[dict]:
    result = subprocess.run(["ldd", str(binary)], text=True, capture_output=True, check=False)
    if "not found" in result.stdout:
        raise RuntimeError(f"Missing runtime dependency of {binary}: {result.stdout}")
    if result.returncode != 0 and "not a dynamic executable" not in result.stderr and "statically linked" not in result.stdout:
        raise RuntimeError(f"Cannot inspect executable {binary}: {result.stderr}")
    inventory = []
    for path in re.findall(r"(?:=>\s+|^\s*)(/[^\s]+)", result.stdout, re.MULTILINE):
        copied = copy_file(Path(path), root)
        inventory.append({"path": path, "sha256": file_hash(copied)})
    return inventory


def newc_entry(stream, name: str, data: bytes, mode: int, inode: int, *, rdevmajor=0, rdevminor=0):
    encoded = name.encode() + b"\0"
    fields = (inode, mode, 0, 0, 1, 0, len(data), 0, 0, rdevmajor, rdevminor, len(encoded), 0)
    header = b"070701" + b"".join(f"{value:08x}".encode() for value in fields)
    stream.write(header + encoded)
    stream.write(bytes((-len(header) - len(encoded)) % 4))
    stream.write(data)
    stream.write(bytes(-len(data) % 4))


def write_initramfs(root: Path, destination: Path):
    with destination.open("xb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=6) as stream:
        for inode, path in enumerate([root, *sorted(root.rglob("*"))], start=1):
            name = "." if path == root else str(path.relative_to(root))
            info = path.lstat()
            if path.is_symlink():
                data = str(path.readlink()).encode()
            elif path.is_file():
                data = path.read_bytes()
            else:
                data = b""
            newc_entry(stream, name, data, info.st_mode, inode)
        newc_entry(stream, "dev/console", b"", stat.S_IFCHR | 0o600, inode + 1, rdevmajor=5, rdevminor=1)
        newc_entry(stream, "dev/null", b"", stat.S_IFCHR | 0o666, inode + 2, rdevmajor=1, rdevminor=3)
        newc_entry(stream, "TRAILER!!!", b"", 0, inode + 3)


def gpt_header(current: int, backup: int, sectors: int, table_lba: int, disk_guid: uuid.UUID, table_crc: int) -> bytes:
    header = bytearray(struct.pack("<8sIIIIQQQQ16sQIII", b"EFI PART", 0x10000, 92, 0, 0,
                                  current, backup, 34, sectors - 34, disk_guid.bytes_le,
                                  table_lba, 128, 128, table_crc))
    struct.pack_into("<I", header, 16, zlib.crc32(header))
    return bytes(header).ljust(SECTOR, b"\0")


def sparse_copy(source: Path, stream, destination_offset: int):
    """Copy sparse extents where supported; never read a host block device."""
    with source.open("rb") as input_stream:
        end = source.stat().st_size
        position = 0
        while position < end:
            try:
                start = os.lseek(input_stream.fileno(), position, os.SEEK_DATA)
                stop = os.lseek(input_stream.fileno(), start, os.SEEK_HOLE)
            except OSError as exc:
                import errno
                if exc.errno == errno.ENXIO:
                    break
                start, stop = position, end
            except AttributeError:
                start, stop = position, end
            input_stream.seek(start)
            stream.seek(destination_offset + start)
            remaining = min(stop, end) - start
            while remaining:
                data = input_stream.read(min(MIB, remaining))
                if not data:
                    raise IOError("Sparse source truncated while copying")
                stream.write(data)
                remaining -= len(data)
            position = stop


def write_disk(esp: Path, output: Path, data_partition: Path | None = None,
               data_guid: uuid.UUID | None = None) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError("Refusing to overwrite an existing path or device")
    if esp.stat().st_size % SECTOR:
        raise ValueError("ESP size must be sector aligned")
    sectors = esp.stat().st_size // SECTOR + 4096
    start, end = 2048, 2048 + esp.stat().st_size // SECTOR - 1
    disk_guid, partition_guid = uuid.uuid4(), uuid.uuid4()
    entry = struct.pack("<16s16sQQQ72s", ESP_GUID.bytes_le, partition_guid.bytes_le, start, end,
                        0, "VENFIRE".encode("utf-16le").ljust(72, b"\0"))
    data_layout = None
    if data_partition:
        if data_partition.stat().st_size % MIB:
            raise ValueError("Data partition size must be MiB aligned")
        data_guid = data_guid or uuid.uuid4()
        data_start = end + 1
        data_end = data_start + data_partition.stat().st_size // SECTOR - 1
        sectors = data_end + 2049
        entry += struct.pack("<16s16sQQQ72s", LINUX_GUID.bytes_le, data_guid.bytes_le,
                             data_start, data_end, 0, "VENFIRE_DATA".encode("utf-16le").ljust(72, b"\0"))
        data_layout = {"partuuid": str(data_guid), "start_lba": data_start,
                       "end_lba": data_end, "size_bytes": data_partition.stat().st_size, "filesystem": "ext4"}
    table = entry + bytes(128 * 128 - len(entry))
    crc = zlib.crc32(table)
    mbr = bytearray(SECTOR)
    mbr[446:462] = struct.pack("<B3sB3sII", 0, b"\0\x02\0", 0xee, b"\xff\xff\xff", 1, min(sectors - 1, 0xffffffff))
    mbr[510:512] = b"\x55\xaa"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.truncate(sectors * SECTOR)
        stream.write(mbr)
        stream.write(gpt_header(1, sectors - 1, sectors, 2, disk_guid, crc))
        stream.write(table)
        stream.seek(start * SECTOR)
        with esp.open("rb") as source:
            shutil.copyfileobj(source, stream, MIB)
        if data_partition:
            sparse_copy(data_partition, stream, data_layout["start_lba"] * SECTOR)
        stream.seek((sectors - 33) * SECTOR)
        stream.write(table)
        stream.write(gpt_header(sectors - 1, 1, sectors, sectors - 33, disk_guid, crc))
    return {"disk_guid": str(disk_guid), "esp_guid": str(partition_guid), "esp_start_lba": start,
            "esp_end_lba": end, "sector_size": SECTOR, "size_bytes": sectors * SECTOR,
            "data_partition": data_layout}


def grub_config(profile: str, *, autotest=False, data_partuuid=None, data_fixture=False, network_autotest=False) -> str:
    developer = profile == "developer-nonredistributable"
    label = "DEVELOPER - NOT FOR REDISTRIBUTION" if developer else "APPLE INTEL RELEASE POLICY"
    flags = "venfire.developer=1" if developer else ""
    if data_partuuid:
        flags += " venfire.data_partuuid=" + str(uuid.UUID(str(data_partuuid)))
    if data_fixture:
        flags += " venfire.data_fixture=1"
    if network_autotest:
        flags += " venfire.network_test=1"
    return f'''set timeout=5
set default={1 if autotest else 0}
serial --unit=0 --speed=115200
terminal_input console serial
terminal_output console serial
search --no-floppy --file --set=root /VENFIRE_BUILD.json
menuentry "Start 26x86 live host / {label}" {{
    linux /boot/vmlinuz rdinit=/init console=tty0 console=ttyS0,115200 loglevel=4 panic=0 {flags}
    initrd /boot/initramfs.gz
}}
menuentry "USB startup self-test / synthetic guest only" {{
    linux /boot/vmlinuz rdinit=/init console=tty0 console=ttyS0,115200 loglevel=4 panic=0 {flags} venfire.autotest=1
    initrd /boot/initramfs.gz
}}
'''


def build(args) -> dict:
    if sys.platform != "linux":
        raise RuntimeError("Build inside Linux/WSL; no host ESP or disk access is needed")
    project, qemu, kernel = args.project.resolve(), args.qemu.resolve(), args.kernel.resolve()
    profile = read_profile(project)
    restore_profile = getattr(args, "restore_profile", None)
    if restore_profile:
        if not args.restore_helper or args.data_size_mib <= 0:
            raise ValueError("Bundled restore assets require --restore-helper and an explicit data partition")
        for module in ("restore_chain.py", "boot.py", "cli.py", "personalization.py", "backend.py"):
            supplied = project / "venfire" / module
            if not supplied.is_file() or file_hash(supplied) != file_hash(SOURCE / "venfire" / module):
                raise ValueError("Restore USB requires a current source snapshot; refresh the private developer tree")
    if args.data_size_mib < 0 or args.data_size_mib > 1024 * 1024:
        raise ValueError("Data partition size must be 0..1048576 MiB")
    if args.data_fixture and args.data_size_mib < 6144:
        raise ValueError("The self-authored >4GiB fixture requires at least 6144 MiB data partition")
    data_guid = uuid.uuid4() if args.data_size_mib else None
    if not qemu.is_file() or not kernel.is_file():
        raise ValueError("A regular QEMU binary and Linux kernel are required")
    for command in ("grub-mkstandalone", "mformat", "mmd", "mcopy", "modprobe", "depmod", "strip"):
        if shutil.which(command) is None:
            raise RuntimeError(f"Missing build dependency: {command}")
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    root = work / "rootfs"
    root.mkdir()
    restore_bundle = None
    if restore_profile:
        available = args.data_size_mib * MIB - (6 * 1024**3 if args.data_fixture else 0)
        restore_bundle = bundle_restore_profile(restore_profile, work / "data-root", available_bytes=available)
    for name in ("dev", "proc", "sys", "run", "tmp", "bin", "sbin", "usr/bin", "etc", "opt/venfire"):
        (root / name).mkdir(parents=True, exist_ok=True)
    busybox = Path(shutil.which("busybox"))
    copy_file(busybox, root, "/bin/busybox")
    for name in ("sh", "mount", "mkdir", "cat", "echo", "sleep", "poweroff", "setsid"):
        (root / "bin" / name).symlink_to("busybox")
    python = Path(sys.executable)
    copy_file(python, root, "/usr/bin/python3")
    copy_libraries(python, root)
    stdlib = Path(sysconfig.get_path("stdlib"))
    shutil.copytree(stdlib, root / str(stdlib).lstrip("/"),
                    ignore=shutil.ignore_patterns("__pycache__", "test", "tests", "site-packages", "dist-packages"))
    for extension in (stdlib / "lib-dynload").glob("*.so"):
        copy_libraries(extension, root)
    copied_qemu = copy_file(qemu, root, "/usr/bin/qemu-system-aarch64")
    run(["strip", "--strip-debug", str(copied_qemu)])
    copy_libraries(qemu, root)
    qemu_img = args.qemu_img.resolve(strict=True)
    copied_qemu_img = copy_file(qemu_img, root, "/usr/bin/qemu-img")
    run(["strip", "--strip-debug", str(copied_qemu_img)])
    copy_libraries(qemu_img, root)
    for executable, destination in ((Path(shutil.which("qemu-io") or "/usr/bin/qemu-io"), "/usr/bin/qemu-io"),
                                    (Path(shutil.which("blkid") or "/usr/sbin/blkid"), "/sbin/blkid")):
        copy_file(executable, root, destination)
        copy_libraries(executable, root)
    restore_metadata = None
    if args.restore_helper:
        helper = args.restore_helper.resolve(strict=True)
        if not helper.is_file():
            raise ValueError("Restore helper must be a trusted regular executable")
        copied_helper = copy_file(helper, root, "/usr/bin/venfire-tss-request")
        restore_metadata = {"input_sha256": file_hash(helper), "embedded_sha256": file_hash(copied_helper),
                            "libraries": copy_libraries(helper, root)}
    ca_bundle = Path("/etc/ssl/certs/ca-certificates.crt")
    copy_file(ca_bundle, root)
    for directory in ("venfire", "guests"):
        shutil.copytree(project / directory, root / "opt/venfire" / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "verification-*"))
    if profile == "developer-nonredistributable":
        for filename in ("DEVELOPMENT_ONLY.json", "DEVELOPMENT_POLICY.md"):
            shutil.copy2(project / filename, root / "opt/venfire" / filename)
    shutil.copytree(SOURCE / "usb", root / "opt/venfire/usb", ignore=shutil.ignore_patterns("__pycache__"))
    (root / "opt/venfire/usb/dhcp_hook.py").chmod(0o755)
    copy_file(SOURCE / "usb/init", root, "/init").chmod(0o755)
    release = args.kernel.name.removeprefix("vmlinuz-")
    if release == args.kernel.name:
        raise ValueError("Kernel input must have its installed vmlinuz-<release> filename")
    module_root = Path("/lib/modules") / release
    module_inventory, unsupported = [], []
    firmware_inventory, missing_firmware = {}, set()
    for module in MODULES:
        result = subprocess.run(["modprobe", "--show-depends", "--set-version", release, module],
                                text=True, capture_output=True, check=False)
        if result.returncode:
            unsupported.append(module)
            continue
        for line in result.stdout.splitlines():
            if line.startswith("insmod "):
                filename = Path(line.split()[1])
                copy_file(filename, root)
                module_inventory.append(str(filename))
                listed = subprocess.run(["modinfo", "-F", "firmware", str(filename)], text=True, capture_output=True, check=False)
                for firmware in listed.stdout.splitlines():
                    matches = []
                    for suffix in ("", ".zst", ".xz"):
                        matches.extend(Path("/lib/firmware").glob(firmware + suffix))
                    if not matches:
                        missing_firmware.add(firmware)
                    for source_firmware in matches:
                        if source_firmware.is_file():
                            copied = copy_file(source_firmware, root)
                            firmware_inventory[str(source_firmware)] = file_hash(copied)
    for filename in ("modules.builtin", "modules.builtin.modinfo", "modules.order"):
        if (module_root / filename).is_file():
            copy_file(module_root / filename, root)
    run(["depmod", "-b", str(root), release])
    modprobe = Path(shutil.which("modprobe"))
    copy_file(modprobe, root, "/sbin/modprobe")
    copy_libraries(modprobe, root)
    (root / "etc/passwd").write_text("root:x:0:0:26x86 RAM console:/run:/bin/sh\n")
    (root / "etc/group").write_text("root:x:0:\n")
    (root / "etc/hostname").write_text("venfire-live\n")
    (root / "etc/hosts").write_text("127.0.0.1 localhost venfire-live\n::1 localhost\n")
    (root / "etc/nsswitch.conf").write_text("hosts: files dns\n")
    notice = ("DEVELOPER ARTIFACT" if profile == "developer-nonredistributable" else "RELEASE-POLICY RESEARCH ARTIFACT")
    metadata = {"schema": 1, "profile": profile, "redistributable": False,
                "notice": notice + " / NOT FOR REDISTRIBUTION; source/license release review incomplete",
                "macos_boot_verified": False, "internal_disks_automounted": False,
                "usb_data": {"enabled": bool(data_guid), "partuuid": str(data_guid) if data_guid else None,
                             "self_authored_fixture": args.data_fixture},
                "network": {"configured_by_default": args.network_autotest,
                            "explicit_autotest_optin": args.network_autotest, "ca_bundle_sha256": file_hash(ca_bundle)},
                "restore_helper": restore_metadata,
                "restore_assets": restore_bundle,
                "kernel": {"release": release, "sha256": file_hash(kernel)},
                "qemu": {"input_sha256": file_hash(qemu), "embedded_sha256": file_hash(copied_qemu),
                         "version": run([str(qemu), "--version"]).stdout.splitlines()[0]},
                "qemu_img": {"input_sha256": file_hash(qemu_img), "embedded_sha256": file_hash(copied_qemu_img),
                             "version": run([str(qemu_img), "--version"]).stdout.splitlines()[0]},
                "python": sys.version, "modules": sorted(set(module_inventory)), "unavailable_modules": unsupported,
                "module_firmware": firmware_inventory, "unavailable_firmware": sorted(missing_firmware)}
    apple_root = root / "opt/venfire/venfire/certs/AppleIncRootCertificate.cer"
    if apple_root.is_file():
        metadata["network"]["scoped_apple_root_sha256"] = file_hash(apple_root)
    (root / "opt/venfire/USB_BUILD.json").write_text(json.dumps(metadata, indent=2) + "\n")
    inventory = run(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"]).stdout
    (root / "opt/venfire/HOST_PACKAGE_INVENTORY.txt").write_text(inventory)
    license_root = root / "opt/venfire/licenses"
    license_root.mkdir()
    for name in ("busybox-static", "python3.12", "grub-efi-amd64-bin", "linux-image-" + release):
        copyright_path = Path("/usr/share/doc") / name / "copyright"
        if copyright_path.is_file():
            shutil.copy2(copyright_path.resolve(), license_root / (name + ".copyright"))
    if args.restore_helper:
        for name in ("libtatsu", "libplist"):
            license_file = args.restore_helper.resolve().parents[2] / name / "COPYING"
            if license_file.is_file():
                shutil.copy2(license_file, license_root / (name + ".COPYING"))
    for name in ("COPYING", "COPYING.LIB"):
        for source_name in ("qemu-source", "qemu", "qemu-src"):
            candidate = qemu.parent.parent / source_name / name
            if candidate.is_file():
                shutil.copy2(candidate, license_root / ("qemu-" + name))
                break
    if (project / "LICENSE").is_file():
        shutil.copy2(project / "LICENSE", license_root / "venfire-LICENSE")
    initramfs = work / "initramfs.gz"
    write_initramfs(root, initramfs)
    cfg = work / "grub.cfg"
    cfg.write_text(grub_config(profile, autotest=args.autotest, data_partuuid=data_guid,
                              data_fixture=args.data_fixture, network_autotest=args.network_autotest))
    efi = work / "BOOTX64.EFI"
    run(["grub-mkstandalone", "-O", "x86_64-efi", "--modules=part_gpt fat normal linux search search_fs_file serial terminal efi_gop efi_uga", "--locales=", "--fonts=", "-o", str(efi), "boot/grub/grub.cfg=" + str(cfg)])
    payload_bytes = kernel.stat().st_size + initramfs.stat().st_size + efi.stat().st_size
    esp_bytes = max(256 * MIB, math.ceil((payload_bytes + 96 * MIB) / (32 * MIB)) * 32 * MIB)
    esp = work / "esp.fat"
    with esp.open("xb") as stream:
        stream.truncate(esp_bytes)
    run(["mformat", "-i", str(esp), "-F", "-v", "VENFIRE", "::"])
    run(["mmd", "-i", str(esp), "::/EFI", "::/EFI/BOOT", "::/boot"])
    marker = work / "VENFIRE_BUILD.json"
    marker.write_text(json.dumps(metadata, indent=2) + "\n")
    for source, target in ((efi, "::/EFI/BOOT/BOOTX64.EFI"), (kernel, "::/boot/vmlinuz"),
                           (initramfs, "::/boot/initramfs.gz"), (marker, "::/VENFIRE_BUILD.json")):
        run(["mcopy", "-i", str(esp), str(source), target])
    output = args.output.absolute()
    data_image = None
    if args.data_size_mib:
        data_root = work / "data-root"
        if not restore_bundle:
            data_root.mkdir()
        data_marker = {"schema": 1, "partuuid": str(data_guid), "profile": profile,
                       "purpose": "Explicit 26x86 USB data and COW storage", "self_authored_fixture": args.data_fixture}
        if args.data_fixture:
            # Sparse, self-authored data; the tail is beyond both 4GiB and 5GiB.
            fixture = data_root / "large-base.fixture"
            with fixture.open("xb") as stream:
                stream.truncate(5 * 1024**3 + 8192)
                stream.seek(5 * 1024**3 + 4096)
                stream.write(b"VENFIRE_SELF_AUTHORED_LARGE_FILE")
            fixture.chmod(0o444)
            data_marker["fixture_size_bytes"] = fixture.stat().st_size
        (data_root / "VENFIRE_DATA.json").write_text(json.dumps(data_marker, indent=2) + "\n")
        data_image = work / "data.ext4"
        with data_image.open("xb") as stream:
            stream.truncate(args.data_size_mib * MIB)
        run(["mkfs.ext4", "-F", "-q", "-L", "VENFIRE_DATA", "-E", "lazy_itable_init=0,lazy_journal_init=0",
             "-d", str(data_root), str(data_image)])
    metadata["disk"] = write_disk(esp, output, data_image, data_guid)
    metadata["image"] = {"path": str(output), "sha256": file_hash(output)}
    metadata["initramfs"] = {"size_bytes": initramfs.stat().st_size, "sha256": file_hash(initramfs)}
    manifest_path = output.with_suffix(output.suffix + ".json")
    with manifest_path.open("x") as stream:
        json.dump(metadata, stream, indent=2)
        stream.write("\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--qemu", type=Path, required=True)
    parser.add_argument("--qemu-img", type=Path, default=Path(shutil.which("qemu-img") or "/usr/bin/qemu-img"))
    parser.add_argument("--restore-helper", type=Path, help="optional trusted native venfire-tss-request encoder and its exact runtime libraries")
    parser.add_argument("--restore-profile", type=Path,
        help="explicit restore-chain profile: bundle its named immutable assets on the USB data partition, without tickets")
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True, help="new private work directory")
    parser.add_argument("--output", type=Path, required=True, help="new regular .img file, never a block device")
    parser.add_argument("--autotest", action="store_true", help="default to bounded startup self-test and poweroff")
    parser.add_argument("--data-size-mib", type=int, default=0, help="optional explicit USB ext4 data partition; 0 keeps RAM-only mode")
    parser.add_argument("--data-fixture", action="store_true", help="include a self-authored >5GiB sparse base for USB COW verification")
    parser.add_argument("--network-autotest", action="store_true", help="explicit opt-in: configure one wired interface by DHCP and test TSS HTTPS on startup")
    args = parser.parse_args()
    if args.output.suffix != ".img":
        parser.error("output must be a new .img file")
    print(json.dumps(build(args), indent=2))


if __name__ == "__main__":
    main()
