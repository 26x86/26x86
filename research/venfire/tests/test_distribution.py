"""Project release-policy regressions, using only isolated disposable copies.

These checks do not amend upstream licenses or claim to prevent source forks.
No test edits the checkout's generated profile or publishes a build artifact.
"""

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

import venfire_build_backend as release_backend


PROJECT = Path(__file__).resolve().parents[1]
PROFILE = Path("venfire/_build_profile.py")


def _load_creator():
    specification = importlib.util.spec_from_file_location(
        "venfire_test_developer_tree_creator", PROJECT / "tools/create_developer_tree.py")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _copy_build_source(destination):
    destination.mkdir()
    for name in ("venfire", "guests"):
        shutil.copytree(PROJECT / name, destination / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "venfire_build_backend.py", "MANIFEST.in",
                 "README.md", "DEVELOPMENT_POLICY.md"):
        shutil.copy2(PROJECT / name, destination / name)
    return destination


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="venfire-release-policy-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / PROFILE).parent.mkdir()
        (self.root / PROFILE).write_text('BUILD_PROFILE = "release"\n', encoding="utf-8")

    def test_explicit_literal_release_profile_passes(self):
        release_backend.check_release_tree(self.root)

    def test_missing_malformed_nonliteral_and_duplicate_markers_rejected(self):
        (self.root / PROFILE).unlink()
        with self.assertRaises(RuntimeError):
            release_backend.check_release_tree(self.root)
        malformed = (
            'BUILD_PROFILE = "developer-nonredistributable"\n',
            'BUILD_PROFILE = "rel" + "ease"\n',
            'BUILD_PROFILE = "release"\nBUILD_PROFILE = "release"\n',
            'BUILD_PROFILE = None\nBUILD_PROFILE = "release"\n',
            'BUILD_PROFILE = "release"\nraise RuntimeError("must not execute")\n',
            'BUILD_PROFILE =\n',
            'BUILD_PROFILE = True\n',
        )
        for contents in malformed:
            with self.subTest(contents=contents):
                (self.root / PROFILE).write_text(contents, encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    release_backend.check_release_tree(self.root)

    def test_external_developer_marker_always_blocks_even_relabelled_profile(self):
        for content in ("{}", '{"build_profile":"release"}', "malformed JSON"):
            with self.subTest(content=content):
                (self.root / "DEVELOPMENT_ONLY.json").write_text(content, encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    release_backend.check_release_tree(self.root)

    def test_dangling_developer_marker_is_still_a_marker(self):
        marker = self.root / "DEVELOPMENT_ONLY.json"
        try:
            marker.symlink_to(self.root / "missing.json")
        except OSError:
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(RuntimeError):
            release_backend.check_release_tree(self.root)

    def test_symlink_build_profile_is_rejected(self):
        original = self.root / "release.py"
        original.write_text('BUILD_PROFILE = "release"\n', encoding="utf-8")
        (self.root / PROFILE).unlink()
        try:
            (self.root / PROFILE).symlink_to(original)
        except OSError:
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(RuntimeError):
            release_backend.check_release_tree(self.root)

    def test_backend_cannot_check_its_release_tree_while_building_another_tree(self):
        (self.root / PROFILE).write_text('BUILD_PROFILE = "developer-nonredistributable"\n', encoding="utf-8")
        delegate = Mock()
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(sys.modules, {"setuptools": SimpleNamespace(build_meta=delegate)}):
                with self.assertRaises(RuntimeError):
                    release_backend.build_wheel(str(self.root / "wheel-output"))
        finally:
            os.chdir(previous)
        delegate.build_wheel.assert_not_called()


class DeveloperTreeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="venfire-private-tree-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = _copy_build_source(self.root / "release")
        self.creator = _load_creator()

    def test_generated_tree_is_labelled_isolated_and_release_rejected(self):
        original = (self.source / PROFILE).read_bytes()
        target = self.root / "developer"
        marker = self.creator.create_developer_tree(self.source, target)
        self.assertEqual((self.source / PROFILE).read_bytes(), original)
        self.assertEqual(marker["build_profile"], "developer-nonredistributable")
        self.assertFalse(marker["redistribution_permitted"])
        self.assertTrue(marker["intel_avx2_required"])
        self.assertFalse(marker["guest_trust_bypassed"])
        self.assertEqual(json.loads((target / "DEVELOPMENT_ONLY.json").read_text()), marker)
        self.assertIn("developer-nonredistributable", (target / PROFILE).read_text())
        with self.assertRaises(RuntimeError):
            release_backend.check_release_tree(target)

    def test_existing_destination_and_in_checkout_destination_are_rejected(self):
        for target in (self.source, self.source / "nested-developer"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    self.creator.create_developer_tree(self.source, target)
        existing = self.root / "existing"
        existing.mkdir()
        retained = existing / "retained.txt"
        retained.write_text("unchanged", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.creator.create_developer_tree(self.source, existing)
        self.assertEqual(retained.read_text(), "unchanged")

    def test_destination_parent_symlink_is_rejected_before_resolving(self):
        actual_parent = self.root / "actual-parent"
        actual_parent.mkdir()
        linked_parent = self.root / "linked-parent"
        try:
            linked_parent.symlink_to(actual_parent, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(ValueError):
            self.creator.create_developer_tree(self.source, linked_parent / "developer")
        self.assertEqual(list(actual_parent.iterdir()), [])

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics")
    def test_source_junction_is_rejected_before_copying_external_tree(self):
        import _winapi

        external = self.root / "external"
        external.mkdir()
        (external / "outside-source.txt").write_text("must not be copied", encoding="utf-8")
        junction = self.source / "venfire/external-junction"
        try:
            _winapi.CreateJunction(str(external), str(junction))
        except OSError:
            self.skipTest("Junction creation unavailable")
        self.assertFalse(junction.is_symlink(), "This fixture must exercise junction rather than symlink semantics")
        destination = self.root / "developer"
        with self.assertRaises(ValueError):
            self.creator.create_developer_tree(self.source, destination)
        self.assertFalse(destination.exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics")
    def test_destination_parent_junction_is_rejected_before_resolving(self):
        import _winapi

        actual_parent = self.root / "actual-parent"
        actual_parent.mkdir()
        junction_parent = self.root / "junction-parent"
        try:
            _winapi.CreateJunction(str(actual_parent), str(junction_parent))
        except OSError:
            self.skipTest("Junction creation unavailable")
        with self.assertRaises(ValueError):
            self.creator.create_developer_tree(self.source, junction_parent / "developer")
        self.assertEqual(list(actual_parent.iterdir()), [])

    def test_actual_cli_release_flag_rejects_and_lab_flag_follows_cpu_evidence(self):
        target = self.root / "developer"
        self.creator.create_developer_tree(self.source, target)
        release = subprocess.run([sys.executable, "-m", "venfire", "doctor", "--developer-host-bypass"],
                                 cwd=self.source, text=True, capture_output=True, timeout=45)
        self.assertNotEqual(release.returncode, 0)
        self.assertIn("NONREDISTRIBUTABLE", json.loads(release.stdout)["error"])
        actual = subprocess.run([sys.executable, "-m", "venfire", "doctor", "--developer-host-bypass"],
                                cwd=target, text=True, capture_output=True, timeout=45)
        report = json.loads(actual.stdout)
        if actual.returncode == 0:
            self.assertTrue(report["host"]["cpu_eligible"])
            self.assertTrue(report["developer_host_bypass"])
            self.assertFalse(report["cpu_requirements_waived"])
            self.assertIn("NONREDISTRIBUTABLE", report["distribution_status"])
        else:
            # CPU-ineligible CI machines remain denied even in this lab fixture.
            self.assertEqual(actual.returncode, 2)
            self.assertFalse(report["host"]["cpu_eligible"])


@unittest.skipUnless(importlib.util.find_spec("pip") and importlib.util.find_spec("setuptools"),
                     "Actual PEP 517 packaging requires installed pip and setuptools")
class Pep517PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="venfire-pep517-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = _copy_build_source(self.root / "source")
        self.original_profile_hash = hashlib.sha256((PROJECT / PROFILE).read_bytes()).hexdigest()
        self.addCleanup(self.assert_checkout_profile_unchanged)

    def assert_checkout_profile_unchanged(self):
        self.assertEqual(hashlib.sha256((PROJECT / PROFILE).read_bytes()).hexdigest(), self.original_profile_hash)

    def build(self):
        return subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-cache-dir",
             "--no-build-isolation", "--disable-pip-version-check", "--wheel-dir", "dist", "."],
            cwd=self.source, capture_output=True, text=True, timeout=90,
        )

    def test_actual_release_wheel_contains_release_profile_and_bundled_guests(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-6000:])
        wheels = list((self.source / "dist").glob("*.whl"))
        self.assertEqual(len(wheels), 1)
        with zipfile.ZipFile(wheels[0]) as archive:
            metadata = ast.parse(archive.read("venfire/_build_profile.py"))
            values = [ast.literal_eval(node.value) for node in metadata.body
                      if isinstance(node, ast.Assign) and len(node.targets) == 1
                      and isinstance(node.targets[0], ast.Name)
                      and node.targets[0].id == "BUILD_PROFILE"]
            self.assertEqual(values, ["release"])
            self.assertFalse(any(name.endswith("DEVELOPMENT_ONLY.json") for name in archive.namelist()))
            for guest in ("virt.elf", "vmapple.bin", "manifest.json"):
                self.assertTrue(any(name.endswith("/share/venfire/guests/" + guest) for name in archive.namelist()))

    def test_actual_developer_wheel_is_rejected_before_output(self):
        (self.source / PROFILE).write_text('BUILD_PROFILE = "developer-nonredistributable"\n', encoding="utf-8")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NONREDISTRIBUTABLE", result.stdout + result.stderr)
        self.assertEqual(list((self.source / "dist").glob("*.whl")), [])

    def test_future_timestamp_developer_staging_cannot_leak_into_release_wheel(self):
        stale = self.source / "build/lib/venfire/_build_profile.py"
        stale.parent.mkdir(parents=True)
        stale.write_text('BUILD_PROFILE = "developer-nonredistributable"\n', encoding="utf-8")
        future = time.time() + 3600
        os.utime(stale, (future, future))
        result = self.build()
        # Policy requires rejecting a contaminated build tree, not relabelling it.
        self.assertNotEqual(result.returncode, 0, "PEP 517 packaged stale developer staging as a release")
        self.assertEqual(list((self.source / "dist").glob("*.whl")), [])


if __name__ == "__main__":
    unittest.main()
