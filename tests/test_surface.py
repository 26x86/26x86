"""Host isolation, EFI integrity and root patch failure boundary tests."""

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from x86.surface import APPLE_NVRAM_GUID, PROFILE_ID, configure_surface_constants, validate_efi


class SurfaceTests(unittest.TestCase):
    def test_missing_optional_qt_parents_are_not_startup_errors(self):
        from x86.platform import qt_webengine_available
        with patch("importlib.util.find_spec", side_effect=ModuleNotFoundError("optional Qt")):
            self.assertFalse(qt_webengine_available())

    def make_efi(self, root):
        names = ["Lilu.kext", "VirtualSMC.kext", "WhateverGreen.kext", "AppleALC.kext", "AMFIPass.kext", "HoRNDIS.kext"]
        config = {"Kernel": {"Add": [{"Enabled": True, "BundlePath": name, "PlistPath": "Contents/Info.plist", "ExecutablePath": ""} for name in names]},
                  "ACPI": {"Add": []}, "UEFI": {"Drivers": []},
                  "DeviceProperties": {"Add": {}}, "NVRAM": {"Add": {APPLE_NVRAM_GUID: {"csr-active-config": bytes.fromhex("03080000")}}},
                  "Misc": {"Security": {"SecureBootModel": "Disabled"}},
                  "PlatformInfo": {"Generic": {"SystemProductName": "MacBookPro15,2"}}}
        for relative in ["BOOT/BOOTx64.efi", "OC/OpenCore.efi"] + [f"OC/Kexts/{name}/Contents/Info.plist" for name in names]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"test fixture")
        path = root / "OC/config.plist"
        path.write_bytes(plistlib.dumps(config))
        return path, config

    def test_validation_preserves_efi_and_detects_missing_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, _ = self.make_efi(root)
            before = path.read_bytes()
            report = validate_efi(root)
            self.assertTrue(report["ok"])
            self.assertTrue(report["root_patch_ready"])
            self.assertFalse(report["hardware_verified"])
            self.assertEqual(path.read_bytes(), before)
            (root / "OC/Kexts/AppleALC.kext/Contents/Info.plist").unlink()
            self.assertFalse(validate_efi(root)["ok"])

    def test_enabled_path_cannot_escape_efi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, config = self.make_efi(root)
            config["ACPI"]["Add"] = [{"Enabled": True, "Path": "../../../outside.aml"}]
            path.write_bytes(plistlib.dumps(config))
            report = validate_efi(root)
            self.assertFalse(report["ok"])
            self.assertTrue(any("escapes" in error for error in report["errors"]))

    def test_profile_requires_cpu_and_gpu_not_spoofed_smbios(self):
        c = SimpleNamespace(computer=SimpleNamespace(real_model="MacBookPro15,2", cpu=SimpleNamespace(name="Intel Core i7"), gpus=[]))
        with self.assertRaises(ValueError):
            configure_surface_constants(c)
        c.computer.cpu.name = "Intel(R) Core(TM) i5-8250U CPU"
        c.computer.gpus = [SimpleNamespace(vendor_id=0x8086, device_id=0x5917)]
        configure_surface_constants(c)
        self.assertTrue(c.allow_modern_audio)
        self.assertFalse(c.computer.t2_chip)
        self.assertFalse(c.allow_vmware_root_patching)

    def test_non_mac_root_patch_never_loads_engine(self):
        from x86.patch import root
        with patch.object(root, "is_macos", return_value=False), patch.object(root, "_context", side_effect=AssertionError("must not probe")):
            result = root.apply(PROFILE_ID)
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "unsupported_platform")

    def test_rollback_success_cannot_be_reported_as_patch_success(self):
        from x86.patch import root
        constants = SimpleNamespace(computer=SimpleNamespace(real_model="MacBookPro15,2"), root_patcher_succeeded=True)
        engine = SimpleNamespace(start_patch=lambda **kwargs: False)
        module = SimpleNamespace(PatchSysVolume=lambda *args: engine)
        with patch.object(root, "is_macos", return_value=True), patch.object(root, "_context", return_value=constants), \
             patch.object(root, "preflight", return_value={"ok": True, "can_patch": True}), \
             patch.object(root.os, "geteuid", return_value=0, create=True), \
             patch.dict(sys.modules, {"opencore_legacy_patcher.sys_patch.sys_patch": module}):
            result = root.apply(PROFILE_ID)
        self.assertEqual(result["status"], "patch_failed")
        self.assertFalse(result["ok"])

    def test_preflight_reports_nearby_kdk_and_blocks_unrelated_patches(self):
        from x86.patch import root
        with tempfile.TemporaryDirectory() as tmp:
            dmg = Path(tmp) / "Universal-Binaries.dmg"
            dmg.write_bytes(b"fixture")
            c = SimpleNamespace(computer=SimpleNamespace(cpu=SimpleNamespace(name="i5-8250U"),
                gpus=[SimpleNamespace(vendor_id=0x8086, device_id=0x5917)]), detected_os=25,
                detected_os_version="26.0", detected_os_build="25A354", payload_local_binaries_root_path_dmg=dmg)
            detection = SimpleNamespace(patches={"Modern Audio": {}}, can_patch=True,
                device_properties={"Settings: Kernel Debug Kit required": True})
            kdk = SimpleNamespace(success=True, kdk_url_build="25A353", kdk_installed_path="",
                kdk_already_installed=False, kdk_url="https://example.com/kdk.dmg", error_msg="")
            modules = {"opencore_legacy_patcher.sys_patch.patchsets": SimpleNamespace(HardwarePatchsetDetection=lambda c: detection),
                "opencore_legacy_patcher.support.kdk_handler": SimpleNamespace(KernelDebugKitObject=lambda *a, **kw: kdk)}
            # This test injects native services; host-policy rejection has its own
            # cross-platform execution tests and must not mask KDK assertions.
            with patch.object(root, "is_macos", return_value=True), patch.dict(sys.modules, modules), \
                 patch("x86.mellow.integration.validate_live", return_value=None):
                report = root.preflight(PROFILE_ID, constants=c)
                self.assertTrue(report["can_patch"], report)
                self.assertFalse(report["kdk"]["exact_build_match"])
                self.assertTrue(report["warnings"])
                detection.patches["Legacy GPU"] = {}
                report = root.preflight(PROFILE_ID, constants=c)
                self.assertFalse(report["can_patch"])
                self.assertIn("Unexpected patch set", report["blockers"][0])

    @unittest.skipIf(sys.platform == "darwin", "Native macOS probing has platform dependencies")
    def test_preparation_does_not_import_mac_frameworks_or_wx(self):
        code = "from x86.gui.webview_app import smoke_test_bridge; import sys; assert smoke_test_bridge()['ok']; assert not {'Security', 'wx', 'applescript'} & set(sys.modules)"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class BridgeBoundaryTests(unittest.TestCase):
    def test_websites_cannot_launch_local_patch_or_read_efi(self):
        from x86.gui.http_bridge import start_bridge_http_server, wizard_base_url
        bridge = SimpleNamespace(get_app_info=lambda: {"ok": True})
        with tempfile.TemporaryDirectory() as tmp:
            server, _ = start_bridge_http_server(tmp, bridge=bridge)
            try:
                base = wizard_base_url(server)
                data = json.dumps({"method": "validate_surface_efi", "args": ["/"]}).encode()
                request = Request(base + "/api/invoke", data=data, headers={"Content-Type": "application/json", "Origin": "https://example.com"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request, timeout=5)
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/launch_wx_action", timeout=5)
                self.assertEqual(error.exception.code, 404)
                request = Request(base + "/api/invoke", data=b"{}", headers={"Content-Type": "text/plain"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request, timeout=5)
                self.assertEqual(error.exception.code, 415)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
