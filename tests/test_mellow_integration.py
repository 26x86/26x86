"""Cross-platform deployment boundaries; these are not macOS boot tests."""
import ast
import logging
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from x86.mellow import integration as m
from x86.execution import HostFacts, resolve_execution

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "payloads/Mellow"


def efi_fixture(root):
    bundle = root / "OC/Kexts/Lilu.kext/Contents"
    (bundle / "MacOS").mkdir(parents=True)
    (bundle / "MacOS/Lilu").write_bytes(b"dependency fixture, not executable")
    (bundle / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "as.vit9696.Lilu",
        "CFBundleVersion": "1.7.1", "CFBundleExecutable": "Lilu"}))
    config = {"Kernel": {"Add": [{"Enabled": True, "Arch": "Any", "BundlePath": "Lilu.kext",
        "PlistPath": "Contents/Info.plist", "ExecutablePath": "Contents/MacOS/Lilu"}]},
        "NVRAM": {"Add": {m.APPLE_GUID: {"boot-args": "-v keepsyms=1"}}}}
    (root / "OC/config.plist").write_bytes(plistlib.dumps(config))
    return config


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.efi = self.root / "EFI"
        self.config = efi_fixture(self.efi)
        environment = {k: v for k, v in os.environ.items() if not k.startswith("X86_")}
        environment["APPDATA"] = str(self.root / "appdata")
        self.env = patch.dict(os.environ, environment, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.host = patch("x86.execution.detect_host", return_value=HostFacts("Windows", "AMD64"))
        self.host.start()
        self.addCleanup(self.host.stop)

    def plan(self, **kwargs):
        kwargs.setdefault("deployment", "efi")
        return m.plan(efi=self.efi, payload_dir=PAYLOAD, settings={}, **kwargs)

    def save(self):
        (self.efi / "OC/config.plist").write_bytes(plistlib.dumps(self.config))

    def test_root_plan_uses_data_driver_path_and_never_claims_metal(self):
        self.config["Kernel"]["Add"][0]["Enabled"] = False
        self.save()
        result = self.plan(mode="x86", deployment="root-patch")
        self.assertFalse(result["root_patch_executed"])
        self.assertFalse(result["native_metal_verified"])
        self.assertTrue(result["efi_supplied_not_boot_attested"])
        self.assertIn("/Library/Extensions", result["patches"]["Mellow"]["Overwrite Data Volume"])
        self.assertIn("-mellowdiag", result["required_boot_args"])

    def test_sandbox_rejects_before_payload_read(self):
        with patch("x86.mellow.payload.load_payload", side_effect=AssertionError("read")):
            with self.assertRaises(ValueError):
                self.plan(mode="apple-silicon-sandbox")

    def test_conflicting_environment_cannot_be_overridden(self):
        with patch.dict(os.environ, {"X86_EXECUTION_MODE": "apple-silicon-sandbox"}):
            with self.assertRaises(ValueError):
                self.plan(mode="x86")

    def test_missing_lilu(self):
        self.config["Kernel"]["Add"][0]["Enabled"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "Lilu must be enabled"):
            self.plan()

    def test_lilu_version_arch_range_binary(self):
        entry = self.config["Kernel"]["Add"][0]
        for key, value in [("Arch", "arm64"), ("MinKernel", "26.0.0"), ("MaxKernel", "24.99.99")]:
            with self.subTest(key=key):
                old = entry.get(key)
                entry[key] = value
                self.save()
                with self.assertRaises(ValueError):
                    self.plan()
                if old is None:
                    del entry[key]
                else:
                    entry[key] = old
        self.save()
        (self.efi / "OC/Kexts/Lilu.kext/Contents/MacOS/Lilu").unlink()
        with self.assertRaisesRegex(ValueError, "executable missing"):
            self.plan()

    def test_duplicate_dependency_rejected(self):
        self.config["Kernel"]["Add"].append(dict(self.config["Kernel"]["Add"][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.plan()

    def test_path_escape_rejected(self):
        for invalid in ("../../../../foreign.kext", "C:/foreign.kext", "foo\\bar.kext"):
            self.config["Kernel"]["Add"][0]["BundlePath"] = invalid
            self.save()
            with self.assertRaises(ValueError):
                self.plan()

    def test_copy_readback_dependency_order_no_source_changes(self):
        before = {str(p.relative_to(self.efi)): p.read_bytes() for p in self.efi.rglob("*") if p.is_file()}
        output = self.root / "prepared"
        result = m.prepare_efi(self.efi, output, payload_dir=PAYLOAD, settings={})
        self.assertEqual(result["status"], "efi_prepared_not_booted")
        self.assertEqual(before, {str(p.relative_to(self.efi)): p.read_bytes() for p in self.efi.rglob("*") if p.is_file()})
        _, config, enabled, indices = m.inspect_efi(output)
        self.assertEqual(indices, [1])
        self.assertGreater(enabled[m.MELLOW_ID]["index"], enabled["as.vit9696.Lilu"]["index"])
        self.assertEqual(config["NVRAM"]["Add"][m.APPLE_GUID]["boot-args"], "-v keepsyms=1 -mellowdiag")
        for p in (PAYLOAD / "root/Library/Extensions/Mellow.kext").rglob("*"):
            if p.is_file():
                q = output / "OC/Kexts/Mellow.kext" / p.relative_to(PAYLOAD / "root/Library/Extensions/Mellow.kext")
                self.assertEqual(p.read_bytes(), q.read_bytes())
        with self.assertRaisesRegex(ValueError, "already enabled"):
            m.plan(efi=output, payload_dir=PAYLOAD, settings={})

    def test_existing_or_nested_output_refused(self):
        for output in (self.efi, self.efi / "new", self.root):
            with self.assertRaises(ValueError):
                m.prepare_efi(self.efi, output, payload_dir=PAYLOAD, settings={})

    def test_efi_only_lilu_is_not_a_kernel_collection_link_input(self):
        self.config["Kernel"]["Add"][0]["Enabled"] = False
        self.save()
        extensions = self.root / "Library/Extensions"
        extensions.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "on-disk Lilu"):
            m.validate_disk_lilu(self.efi, extensions)
        shutil.copytree(self.efi / "OC/Kexts/Lilu.kext", extensions / "Lilu.kext")
        m.validate_disk_lilu(self.efi, extensions)
        binary = extensions / "Lilu.kext/Contents/MacOS/Lilu"
        binary.write_bytes(b"different dependency build")
        with self.assertRaisesRegex(ValueError, "differ"):
            m.validate_disk_lilu(self.efi, extensions)

    def test_duplicate_disk_lilu_is_rejected(self):
        self.config["Kernel"]["Add"][0]["Enabled"] = False
        self.save()
        extensions = self.root / "Library/Extensions"
        for name in ("Lilu.kext", "Renamed.kext"):
            shutil.copytree(self.efi / "OC/Kexts/Lilu.kext", extensions / name)
        with self.assertRaisesRegex(ValueError, "one existing"):
            m.validate_disk_lilu(self.efi, extensions)

    def test_root_efi_preparation_disables_dependency_injection(self):
        with self.assertRaisesRegex(ValueError, "disk-only"):
            self.plan(deployment="root-patch")
        out = self.root / "root-patch-efi"
        report = m.prepare_efi(self.efi, out, payload_dir=PAYLOAD, settings={}, deployment="root-patch")
        self.assertEqual(report["lilu_route"], "disk-only")
        self.assertEqual(report["deployment"], "root-patch")
        _, config, enabled, mellow = m.inspect_efi(out)
        self.assertNotIn("as.vit9696.Lilu", enabled)
        self.assertFalse(mellow)
        self.assertIn("-mellowdiag", config["NVRAM"]["Add"][m.APPLE_GUID]["boot-args"])
        self.assertTrue(m.inspect_efi(self.efi)[1]["Kernel"]["Add"][0]["Enabled"])

    def test_nearby_kdk_cannot_approve_mellow(self):
        c = SimpleNamespace(detected_os_build="25A354", detected_os_version="26.0")
        kdk = SimpleNamespace(success=True, kdk_url_build="25A353", kdk_installed_path="")
        module = SimpleNamespace(KernelDebugKitObject=lambda *a, **kw: kdk)
        with patch.dict(sys.modules, {"opencore_legacy_patcher.support.kdk_handler": module}):
            with self.assertRaisesRegex(ValueError, "exact-build"):
                m.validate_kdk(c)
            kdk.kdk_url_build = c.detected_os_build
            m.validate_kdk(c)

    def test_cli_sandbox_no_native_imports(self):
        result = subprocess.run([sys.executable, "-m", "x86.cli", "mellow", "plan", "--mode",
            "apple-silicon-sandbox", "--efi", str(self.efi)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        self.assertIn('"status": "mellow_rejected"', result.stdout)

    def test_live_gate_rejects_windows_without_importing_native_modules(self):
        with self.assertRaises(ValueError):
            m.validate_live(SimpleNamespace(execution_mode="x86"))


def engine_method(name, **globals_extra):
    """Execute real orchestrator method with fake APFS/KC services on Windows."""
    tree = ast.parse((ROOT / "opencore_legacy_patcher/sys_patch/sys_patch.py").read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PatchSysVolume")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {"logging": logging, **globals_extra}
    exec(compile(ast.Module(body=[method], type_ignores=[]), "actual_engine_method", "exec"), namespace)
    return namespace[name]


class OrchestratorTests(unittest.TestCase):
    def test_failed_patch_metadata_is_not_success(self):
        helper = SimpleNamespace(SysPatchHelpers=lambda c: SimpleNamespace(generate_patchset_plist=lambda *a: False))
        obj = SimpleNamespace(constants=SimpleNamespace(), mount_location="/fake", kdk_path=None, metallib_path=None)
        with self.assertRaisesRegex(RuntimeError, "metadata"):
            engine_method("_write_patchset", sys_patch_helpers=helper, CORE_SERVICES_PATH="/System/Library/CoreServices",
                PATCHSET_FILENAME="OpenCore-Legacy-Patcher.plist")(obj, {"Mellow": {}})

    def test_failed_rsync_rejects_even_with_preexisting_libkern(self):
        tree = ast.parse((ROOT / "opencore_legacy_patcher/sys_patch/utilities/kdk_merge.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_merge_kdk")
        services = SimpleNamespace(run_as_root=lambda *a, **kw: SimpleNamespace(returncode=23), log=lambda r: None)
        namespace = {"logging": logging, "subprocess_wrapper": services, "subprocess": subprocess, "Path": Path}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "actual_kdk_merge", "exec"), namespace)
        with tempfile.TemporaryDirectory() as temp:
            libkern = Path(temp) / "System/Library/Extensions/System.kext/PlugIns/Libkern.kext/Libkern"
            libkern.parent.mkdir(parents=True)
            libkern.write_bytes(b"old partial KDK file")
            with self.assertRaisesRegex(RuntimeError, "rsync failed"):
                namespace["_merge_kdk"](SimpleNamespace(mount_location=temp), "/fake/KDK.kdk")

    def test_kdk_merge_error_is_not_swallowed(self):
        obj = SimpleNamespace(constants=SimpleNamespace(mellow_deployment="root-patch", detected_os_build="25A354"),
            mount_location="/fake", skip_root_kmutil_requirement=False)
        merger = lambda *a: SimpleNamespace(merge=lambda *a: (_ for _ in ()).throw(IOError("KDK copy failed")))
        with self.assertRaisesRegex(IOError, "KDK copy failed"):
            engine_method("_merge_kdk_with_root", KernelDebugKitMerge=merger, Path=Path)(obj)
        wrong = lambda *a: SimpleNamespace(merge=lambda *a: "/Library/Developer/KDKs/KDK_26.0_25A353.kdk")
        with self.assertRaisesRegex(RuntimeError, "exact-build"):
            engine_method("_merge_kdk_with_root", KernelDebugKitMerge=wrong, Path=Path)(obj)

    def test_sandbox_constructor_rejects_before_native_snapshot_probe(self):
        c = SimpleNamespace(execution_mode="apple-silicon-sandbox")
        fake = SimpleNamespace(Constants=object)
        with self.assertRaises(ValueError):
            engine_method("__init__", constants=fake)(SimpleNamespace(), "test", c)

    def test_unpatch_retains_journal_until_cache_succeeds(self):
        calls = []
        c = SimpleNamespace(detected_os=25, root_patcher_succeeded=False)
        obj = SimpleNamespace(constants=c, mount_location="/fake", mount_location_data="/fake-data",
            skip_root_kmutil_requirement=False, _clean_skylight_plugins=lambda: None,
            _delete_nonmetal_enforcement=lambda: None, _rebuild_kernel_cache=lambda: False)
        kernel = SimpleNamespace(KernelCacheSupport=lambda **kw: SimpleNamespace(clean_auxiliary_kc=lambda: calls.append("cleanup")))
        snapshot = lambda *a: SimpleNamespace(revert_snapshot=lambda: calls.append("snapshot") or True)
        with patch("x86.mellow.transaction.restore_installed", side_effect=lambda **kw: calls.append(("restore", kw["defer_finalize"])) or True), \
             patch("x86.mellow.transaction.finalize_restore", side_effect=lambda **kw: calls.append("finalize")):
            method = engine_method("_unpatch_root_vol", APFSSnapshot=snapshot, kernelcache=kernel)
            with self.assertRaises(RuntimeError):
                method(obj)
            self.assertNotIn("finalize", calls)
            self.assertFalse(c.root_patcher_succeeded)
            obj._rebuild_kernel_cache = lambda: True
            method(obj)
            self.assertEqual(calls[-1], "finalize")
            self.assertTrue(c.root_patcher_succeeded)

    def test_copy_error_reaches_outer_rollback(self):
        obj = SimpleNamespace(model="fixture", patch_set_dictionary={"Mellow": {}},
            _execute_patchset=lambda p: (_ for _ in ()).throw(IOError("copy failed")))
        with self.assertRaisesRegex(IOError, "copy failed"):
            engine_method("_patch_root_vol")(obj)

    def test_false_kernel_rebuild_never_reports_success(self):
        order = []
        obj = SimpleNamespace(model="fixture", patch_set_dictionary={"Mellow": {}},
            constants=SimpleNamespace(wxpython_variant=False),
            _execute_patchset=lambda p: order.append("copy"),
            _mellow_transaction=SimpleNamespace(installed=lambda: order.append("readback")),
            _rebuild_root_volume=lambda: False)
        with self.assertRaisesRegex(RuntimeError, "rebuild failed"):
            engine_method("_patch_root_vol")(obj)
        self.assertEqual(order, ["copy", "readback"])

    def test_readback_failure_prevents_cache_and_snapshot(self):
        obj = SimpleNamespace(model="fixture", patch_set_dictionary={"Mellow": {}},
            _execute_patchset=lambda p: None,
            _mellow_transaction=SimpleNamespace(installed=lambda: (_ for _ in ()).throw(ValueError("hash"))),
            _rebuild_root_volume=lambda: self.fail("must not rebuild"))
        with self.assertRaisesRegex(ValueError, "hash"):
            engine_method("_patch_root_vol")(obj)


if __name__ == "__main__":
    unittest.main()
