import gzip
import json
import importlib.util
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid
import zlib


SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("venfire_build_usb", SOURCE / "tools/build_usb.py")
usb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usb)
menu_spec = importlib.util.spec_from_file_location("venfire_live_menu", SOURCE / "usb/live_menu.py")
menu = importlib.util.module_from_spec(menu_spec)
menu_spec.loader.exec_module(menu)
data_spec = importlib.util.spec_from_file_location("venfire_usb_data", SOURCE / "usb/data_partition.py")
usb_data = importlib.util.module_from_spec(data_spec)
data_spec.loader.exec_module(usb_data)
dhcp_spec = importlib.util.spec_from_file_location("venfire_dhcp_hook", SOURCE / "usb/dhcp_hook.py")
dhcp = importlib.util.module_from_spec(dhcp_spec)
dhcp_spec.loader.exec_module(dhcp)
network_spec = importlib.util.spec_from_file_location("venfire_usb_network", SOURCE / "usb/network.py")
network = importlib.util.module_from_spec(network_spec)
network_spec.loader.exec_module(network)


class USBImageTests(unittest.TestCase):
    def test_gpt_has_consistent_primary_backup_and_esp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            esp = root / "esp.fat"
            esp.write_bytes(b"self-authored partition fixture".ljust(1024 * 1024, b"\0"))
            image = root / "disk.img"
            result = usb.write_disk(esp, image)
            with image.open("rb") as stream:
                mbr = stream.read(512)
                self.assertEqual(mbr[510:], b"\x55\xaa")
                self.assertEqual(mbr[450], 0xee)
                primary = bytearray(stream.read(512))
                self.assertEqual(primary[:8], b"EFI PART")
                recorded = struct.unpack_from("<I", primary, 16)[0]
                struct.pack_into("<I", primary, 16, 0)
                self.assertEqual(recorded, zlib.crc32(primary[:92]))
                stream.seek(2 * 512)
                table = stream.read(16384)
                self.assertEqual(uuid.UUID(bytes_le=table[:16]), usb.ESP_GUID)
                self.assertEqual(zlib.crc32(table), struct.unpack_from("<I", primary, 88)[0])
                stream.seek(-512, 2)
                backup = bytearray(stream.read(512))
                self.assertEqual(backup[:8], b"EFI PART")
                recorded = struct.unpack_from("<I", backup, 16)[0]
                struct.pack_into("<I", backup, 16, 0)
                self.assertEqual(recorded, zlib.crc32(backup[:92]))
                self.assertEqual(struct.unpack_from("<Q", backup, 32)[0], 1)
                stream.seek(result["esp_start_lba"] * 512)
                self.assertEqual(stream.read(esp.stat().st_size), esp.read_bytes())

    def test_disk_builder_refuses_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "existing.img"
            image.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                usb.write_disk(Path(directory) / "not-read", image)
            self.assertEqual(image.read_bytes(), b"preserve")

    def test_developer_optin_never_leaks_into_release_config(self):
        release = usb.grub_config("release")
        developer = usb.grub_config("developer-nonredistributable")
        self.assertNotIn("venfire.developer=1", release)
        self.assertIn("venfire.developer=1", developer)
        self.assertIn("NOT FOR REDISTRIBUTION", developer)
        self.assertIn("synthetic guest only", release)

    def test_initramfs_contains_executable_init_and_console(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            (root / "dev").mkdir()
            (root / "init").write_bytes(b"#!/bin/sh\n")
            (root / "init").chmod(0o755)
            output = Path(directory) / "initramfs.gz"
            usb.write_initramfs(root, output)
            archive = gzip.decompress(output.read_bytes())
            self.assertTrue(archive.startswith(b"070701"))
            self.assertIn(b"dev/console\0", archive)
            self.assertIn(b"TRAILER!!!\0", archive)
            self.assertIn(b"#!/bin/sh\n", archive)

    def test_profile_rejects_code_duplicate_assignment_and_marker_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "venfire").mkdir()
            profile = root / "venfire/_build_profile.py"
            for content in ("BUILD_PROFILE = 'release'\nBUILD_PROFILE = 'developer-nonredistributable'\n",
                            "BUILD_PROFILE = 'release'\nimport os\n",
                            "BUILD_PROFILE = str('release')\n"):
                profile.write_text(content)
                with self.assertRaises(ValueError):
                    usb.read_profile(root)
            profile.write_text("BUILD_PROFILE = 'release'\n")
            self.assertEqual(usb.read_profile(root), "release")
            (root / "DEVELOPMENT_ONLY.json").write_text("{}")
            with self.assertRaises(ValueError):
                usb.read_profile(root)
            profile.write_text("BUILD_PROFILE = 'developer-nonredistributable'\n")
            with self.assertRaises(ValueError):
                usb.read_profile(root)

    def test_live_init_is_unix_shell_text(self):
        init = (SOURCE / "usb/init").read_bytes()
        self.assertTrue(init.startswith(b"#!/bin/busybox sh\n"))
        self.assertNotIn(b"\r\n", init)
        self.assertNotIn(b"mount /dev/", init)
        self.assertIn(b"applesmc", init)
        self.assertIn(b'/sbin/modprobe "$module"', init)

    def test_storage_session_selects_persistent_cli_without_raw_inputs(self):
        profile = {"schema": 1, "firmware": "/assets/fw", "uuid": 42,
                   "storage_session": "/data/session", "aux": "must-not-use", "disk": "must-not-use"}
        command = menu.boot_arguments(profile, "/run/evidence", True)
        self.assertIn("boot-session", command)
        self.assertIn("/data/session", command)
        self.assertNotIn("--disk", command)
        self.assertNotIn("--aux", command)
        self.assertIn("--developer-host-bypass", command)
        probe = menu.boot_arguments({"schema": 1, "firmware": "/assets/fw", "uuid": 42,
                                     "aux": "/assets/aux", "disk": "/assets/disk"}, "/run/evidence", False)
        self.assertIn("boot-probe", probe)
        self.assertNotIn("--developer-host-bypass", probe)

    def test_second_partition_uuid_and_data_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            esp, data, output = root / "esp", root / "data", root / "disk.img"
            esp.write_bytes(bytes(1024 * 1024))
            data.write_bytes(b"self-authored data".ljust(2 * 1024 * 1024, b"\0"))
            identity = uuid.uuid4()
            result = usb.write_disk(esp, output, data, identity)
            self.assertEqual(result["data_partition"]["partuuid"], str(identity))
            self.assertGreater(result["data_partition"]["start_lba"], result["esp_end_lba"])
            with output.open("rb") as stream:
                stream.seek(2 * 512 + 128)
                entry = stream.read(128)
                self.assertEqual(uuid.UUID(bytes_le=entry[:16]), usb.LINUX_GUID)
                self.assertEqual(uuid.UUID(bytes_le=entry[16:32]), identity)
                stream.seek(result["data_partition"]["start_lba"] * 512)
                self.assertEqual(stream.read(data.stat().st_size), data.read_bytes())

    def test_partuuid_selection_is_explicit_and_canonical(self):
        self.assertIsNone(usb_data.requested_uuid("console=tty0"))
        identity = str(uuid.uuid4())
        self.assertEqual(usb_data.requested_uuid("venfire.data_partuuid=" + identity), identity)
        for value in ("bad", identity.replace("-", ""), identity + " venfire.data_partuuid=" + identity):
            with self.assertRaises(ValueError):
                usb_data.requested_uuid("venfire.data_partuuid=" + value)

    def test_only_usb_descendant_partitions_are_probed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sys_root = root / "sys"
            usb_node = sys_root / "devices/pci/usb1/1-1"
            partition = usb_node / "host/target/block/sda/sda2"
            partition.mkdir(parents=True)
            (partition / "partition").write_text("2\n")
            bus = sys_root / "bus/usb"
            (bus / "devices").mkdir(parents=True)
            internal = sys_root / "devices/pci/nvme/nvme0n1/nvme0n1p2"
            internal.mkdir(parents=True)
            (internal / "partition").write_text("2\n")
            try:
                (usb_node / "subsystem").symlink_to(bus, target_is_directory=True)
                (bus / "devices/1-1").symlink_to(usb_node, target_is_directory=True)
            except OSError:
                self.skipTest("Host cannot create sysfs fixture symlinks")
            observed = []
            identity = str(uuid.uuid4())
            def probe(path):
                observed.append(path)
                return identity
            selected = usb_data.select_partition(identity, sys_root=sys_root, dev_root=root / "dev", probe=probe)
            self.assertEqual(selected.name, "sda2")
            self.assertEqual([item.name for item in observed], ["sda2"])
            duplicate = usb_node / "host/target/block/sdb/sdb2"
            duplicate.mkdir(parents=True)
            (duplicate / "partition").write_text("2\n")
            with self.assertRaises(ValueError):
                usb_data.select_partition(identity, sys_root=sys_root, dev_root=root / "dev", probe=probe)

    def test_default_boot_does_not_discover_or_mount_data(self):
        with patch.object(usb_data, "select_partition") as select, patch.object(usb_data.subprocess, "run") as run:
            self.assertIsNone(usb_data.mount_selected("console=tty0", "release"))
        select.assert_not_called()
        run.assert_not_called()

    def test_mismatched_marker_is_unmounted_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            device = SimpleNamespace(stat=lambda: SimpleNamespace(st_rdev=7))
            target = root / "data"
            identity = str(uuid.uuid4())
            commands = []
            def run(command, **kwargs):
                commands.append(command)
                if command[1] == "mount":
                    (target / "VENFIRE_DATA.json").write_text(json.dumps({
                        "schema": 1, "partuuid": identity, "profile": "wrong-profile"}))
            with patch.object(usb_data, "select_partition", return_value=device), patch.object(usb_data.subprocess, "run", side_effect=run):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    usb_data.mount_selected("venfire.data_partuuid=" + identity, "release", target=target)
            self.assertEqual([cmd[1] for cmd in commands], ["mount", "umount"])
            self.assertIn("ro,noload,nodev,nosuid", commands[0])

    def test_network_configuration_requires_live_ram_environment(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(network, "RUN", Path(directory)), patch.object(network.subprocess, "run") as run:
            with self.assertRaises(FileNotFoundError):
                network.configure_dhcp("eth0")
            run.assert_not_called()

    def test_usb_sysfs_identity_must_match_actual_block_node(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sys_partition = root / "sys/sda2"
            sys_partition.mkdir(parents=True)
            identity = str(uuid.uuid4())
            (sys_partition / "dev").write_text("8:18\n")
            info = SimpleNamespace(st_mode=0o060600, st_rdev=123)
            with patch.object(usb_data, "usb_partition_paths", return_value=[sys_partition]), \
                 patch.object(Path, "lstat", return_value=info), \
                 patch.object(usb_data.os, "major", return_value=8, create=True), \
                 patch.object(usb_data.os, "minor", return_value=17, create=True), \
                 patch.object(usb_data.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=identity + "\n")) as run:
                with self.assertRaisesRegex(ValueError, "found 0"):
                    usb_data.select_partition(identity, dev_root=root / "dev")
                run.assert_not_called()
                (sys_partition / "dev").write_text("8:17\n")
                self.assertEqual(usb_data.select_partition(identity, dev_root=root / "dev").name, "sda2")
                run.assert_called_once()

    def test_dhcp_values_are_addresses_not_shell_or_dns_config_text(self):
        values = {"interface": "eth0", "ip": "10.0.2.15", "subnet": "255.255.255.0", "router": "10.0.2.2", "dns": "10.0.2.3"}
        self.assertEqual(dhcp.lease_parameters(values)["address"], "10.0.2.15/24")
        for name, bad in (("interface", "eth0;reboot"), ("ip", "10.0.2.15/8"),
                          ("subnet", "255.0.255.0"), ("dns", "10.0.2.3\nsearch evil")):
            with self.assertRaises(ValueError):
                dhcp.lease_parameters(dict(values, **{name: bad}))

    def test_wired_network_enumeration_excludes_loopback_and_wifi(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, kind in (("lo", "772"), ("eth0", "1"), ("wlan0", "1")):
                (root / name).mkdir()
                (root / name / "type").write_text(kind)
                (root / name / "carrier").write_text("1")
            (root / "wlan0/wireless").mkdir()
            self.assertEqual(network.interfaces(root), [{"name": "eth0", "carrier": True}])

    def test_network_autotest_requires_explicit_build_option(self):
        self.assertNotIn("venfire.network_test=1", usb.grub_config("release"))
        self.assertIn("venfire.network_test=1", usb.grub_config("release", network_autotest=True))
        self.assertNotIn(b"\r\n", (SOURCE / "usb/dhcp_hook.py").read_bytes())


if __name__ == "__main__":
    unittest.main()
