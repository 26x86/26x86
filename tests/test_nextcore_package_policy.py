import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "Tools"
sys.path.insert(0, str(TOOLS))
from nextcore_package_policy import (
    PACKAGES, PRIMARY_PACKAGES, dependency_revisions, module_manifests,
    validate_auxiliary_inventory, validate_cargo_metadata, validate_workspace,
)

REVISION = "a" * 40
OTHER_REVISION = "b" * 40
ISE_URL = PACKAGES["nextcore-ise"].url


def pin(name, revision=REVISION):
    return {"git": PACKAGES[name].url, "rev": revision}


class PackagePolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name, owner in PACKAGES.items():
            path = self.root / owner.module_path / owner.manifest
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'[package]\nname = "{name}"\nversion = "0.1.0"\n')
        self.heads = {name: REVISION for name in PRIMARY_PACKAGES}

    def workspace(self):
        patches = {}
        for name, owner in PACKAGES.items():
            patches.setdefault(owner.url, {})[name] = {
                "path": (owner.module_path.relative_to("nextcore") / Path(owner.manifest).parent).as_posix()
            }
        return {"workspace": {"members": [owner.module_path.relative_to("nextcore").as_posix()
                                           for owner in PRIMARY_PACKAGES.values()]}, "patch": patches}

    def metadata(self):
        packages = [{"name": name, "id": f"local::{name}", "source": None,
                     "manifest_path": str(self.root / owner.module_path / owner.manifest)}
                    for name, owner in PACKAGES.items()]
        nodes = [{"id": p["id"], "dependencies": [], "features": []} for p in packages]
        efi = next(node for node in nodes if node["id"] == "local::nextcore-efi")
        efi["dependencies"] = ["local::nextcore-memory-service"]
        efi["features"] = ["arm-jit-memory-provider"]
        return {"packages": packages, "workspace_members": [f"local::{name}" for name in PRIMARY_PACKAGES],
                "resolve": {"nodes": nodes}}

    def test_primary_and_auxiliary_share_one_owner_revision(self):
        manifest = {"build-dependencies": {"nextcore-ise": pin("nextcore-ise")},
                    "dependencies": {"nextcore-memory-service": pin("nextcore-memory-service")}}
        self.assertEqual(dependency_revisions(manifest, self.heads), {ISE_URL.removesuffix(".git"): REVISION})

    def test_conflicting_revisions_are_not_overwritten(self):
        for section in ("dependencies", "dev-dependencies", "build-dependencies"):
            with self.subTest(section=section):
                manifest = {section: {"nextcore-memory-service": pin("nextcore-memory-service")},
                            "target": {"cfg(target_os = 'uefi')": {
                                "build-dependencies": {"nextcore-ise": pin("nextcore-ise", OTHER_REVISION)}}}}
                with self.assertRaisesRegex(ValueError, "conflicting"):
                    dependency_revisions(manifest)

    def test_target_alias_resolves_package_identity(self):
        manifest = {"target": {"x86_64-unknown-uefi": {"dependencies": {
            "service": {"package": "nextcore-memory-service", **pin("nextcore-memory-service")}}}}}
        self.assertEqual(dependency_revisions(manifest, self.heads), {ISE_URL.removesuffix(".git"): REVISION})
        manifest["target"]["x86_64-unknown-uefi"]["dependencies"]["service"]["rev"] = OTHER_REVISION
        with self.assertRaisesRegex(ValueError, "integrated"):
            dependency_revisions(manifest, self.heads)

    def test_unknown_names_and_alias_escapes_fail(self):
        cases = [
            {"nextcore-mystery": pin("nextcore-ise")},
            {"service": {"package": "nextcore-mystery", **pin("nextcore-ise")}},
            {"nextcore-core": {"package": "serde", "version": "1"}},
            {"nextcore-core": {"package": "nextcore-ise", **pin("nextcore-ise")}},
            {"Nextcore-ISE": pin("nextcore-ise")},
        ]
        for dependencies in cases:
            with self.subTest(dependencies=dependencies), self.assertRaises(ValueError):
                dependency_revisions({"dependencies": dependencies})

    def test_canonical_url_revision_and_no_path_required(self):
        for change in ({"git": PACKAGES["nextcore-core"].url}, {"rev": "main"},
                       {"rev": 1}, {"rev": OTHER_REVISION}, {"path": "../copy"},
                       {"branch": "main"}, {"tag": "release"}):
            specification = {**pin("nextcore-memory-service"), **change}
            with self.subTest(change=change), self.assertRaises(ValueError):
                dependency_revisions({"dependencies": {"nextcore-memory-service": specification}}, self.heads)

    def test_workspace_dependencies_are_not_an_alias_escape(self):
        inherited = {"package": "nextcore-memory-service", **pin("nextcore-memory-service")}
        manifest = {"workspace": {"dependencies": {"service": inherited}},
                    "dependencies": {"service": {"workspace": True}}}
        self.assertEqual(dependency_revisions(manifest, self.heads), {ISE_URL.removesuffix(".git"): REVISION})
        del manifest["workspace"]
        with self.assertRaisesRegex(ValueError, "unresolved workspace"):
            dependency_revisions(manifest, self.heads)

    def test_auxiliary_path_and_owner_are_exact(self):
        ise = self.root / PACKAGES["nextcore-ise"].module_path
        paths = ["Cargo.toml", PACKAGES["nextcore-memory-service"].manifest]
        self.assertEqual(set(module_manifests(ise, "nextcore-ise", paths).manifests),
                         {"nextcore-ise", "nextcore-memory-service"})
        misplaced = ise / "copied/Cargo.toml"
        misplaced.parent.mkdir()
        misplaced.write_bytes((ise / paths[1]).read_bytes())
        with self.assertRaisesRegex(ValueError, "wrong owner/path"):
            module_manifests(ise, "nextcore-ise", paths + ["copied/Cargo.toml"])
        core = self.root / PACKAGES["nextcore-core"].module_path
        misplaced = core / paths[1]
        misplaced.parent.mkdir(parents=True)
        misplaced.write_bytes((ise / paths[1]).read_bytes())
        with self.assertRaisesRegex(ValueError, "wrong owner/path"):
            module_manifests(core, "nextcore-core", paths)

    def test_unknown_auxiliary_manifest_is_rejected(self):
        ise = self.root / PACKAGES["nextcore-ise"].module_path
        unknown = ise / "runtime/unknown/Cargo.toml"
        unknown.parent.mkdir()
        unknown.write_text('[package]\nname="nextcore-unknown"\nversion="0.1.0"\n')
        with self.assertRaisesRegex(ValueError, "unknown package"):
            module_manifests(ise, "nextcore-ise", ["Cargo.toml", "runtime/memory-service/Cargo.toml",
                                                  "runtime/unknown/Cargo.toml"])

    def test_nested_non_nextcore_package_cannot_hide_nextcore_dependencies(self):
        ise = self.root / PACKAGES["nextcore-ise"].module_path
        nested = ise / "runtime/helper/Cargo.toml"
        nested.parent.mkdir()
        nested.write_text('[package]\nname="helper"\nversion="0.1.0"\n'
                          '[dependencies]\nnextcore-unknown="1"\n')
        with self.assertRaisesRegex(ValueError, "unknown"):
            module_manifests(ise, "nextcore-ise", ["Cargo.toml", "runtime/memory-service/Cargo.toml",
                                                  "runtime/helper/Cargo.toml"])

    def test_auxiliary_inventory_covers_and_hashes_actual_files(self):
        ise = self.root / PACKAGES["nextcore-ise"].module_path
        source = ise / "runtime/memory-service/src/lib.rs"
        source.parent.mkdir()
        source.write_text("#![no_std]\n")
        tracked = {"Cargo.toml", "runtime/memory-service/Cargo.toml", "runtime/memory-service/src/lib.rs"}
        inventory = {"files": [{"path": path, "bytes": len((ise / path).read_bytes()),
                                "sha256": hashlib.sha256((ise / path).read_bytes()).hexdigest()}
                               for path in sorted(tracked)]}
        validate_auxiliary_inventory(ise, "nextcore-ise", tracked, inventory)
        missing = copy.deepcopy(inventory)
        missing["files"] = [item for item in missing["files"] if item["path"] != "runtime/memory-service/src/lib.rs"]
        with self.assertRaisesRegex(ValueError, "cover"):
            validate_auxiliary_inventory(ise, "nextcore-ise", tracked, missing)
        source.write_text("#![no_std]\npub fn changed() {}\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            validate_auxiliary_inventory(ise, "nextcore-ise", tracked, inventory)

    def test_workspace_has_seven_members_and_eight_owned_patches(self):
        manifest = self.workspace()
        validate_workspace(self.root, manifest)
        for mutate in (
            lambda m: m["workspace"]["members"].append("crates/nextcore-ise/runtime/memory-service"),
            lambda m: m["patch"][ISE_URL]["nextcore-memory-service"].update(path="crates/nextcore-core"),
            lambda m: m["patch"][ISE_URL].update({"nextcore-unknown": {"path": "elsewhere"}}),
        ):
            changed = copy.deepcopy(manifest)
            mutate(changed)
            with self.assertRaises(ValueError):
                validate_workspace(self.root, changed)

    def test_cargo_requires_local_auxiliary_and_rejects_remote_duplicate(self):
        metadata = self.metadata()
        self.assertTrue(validate_cargo_metadata(self.root, metadata)["memory_service_local_and_selected"])
        remote = copy.deepcopy(next(p for p in metadata["packages"] if p["name"] == "nextcore-memory-service"))
        remote.update(id="git::memory-service", source=f"git+{ISE_URL}?rev={REVISION}", manifest_path="/remote/Cargo.toml")
        metadata["packages"].append(remote)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_cargo_metadata(self.root, metadata)

    def test_cargo_rejects_unselected_auxiliary_wrong_path_and_eighth_member(self):
        mutations = [
            lambda m: m["workspace_members"].append("local::nextcore-memory-service"),
            lambda m: next(n for n in m["resolve"]["nodes"] if n["id"] == "local::nextcore-efi").update(dependencies=[]),
            lambda m: next(n for n in m["resolve"]["nodes"] if n["id"] == "local::nextcore-efi").update(features=[]),
            lambda m: next(p for p in m["packages"] if p["name"] == "nextcore-memory-service").update(manifest_path=str(self.root / "wrong/Cargo.toml")),
        ]
        for mutation in mutations:
            metadata = self.metadata()
            mutation(metadata)
            with self.assertRaises(ValueError):
                validate_cargo_metadata(self.root, metadata)

    @unittest.skipUnless(shutil.which("cargo") and shutil.which("git"), "Cargo/Git required for actual resolver fixture")
    def test_actual_cargo_resolver_local_auxiliary_and_git_duplicate(self):
        # All packages are independent authored fixtures. The only Git source
        # is a temporary local repository; no network or real pin is changed.
        for name, owner in PACKAGES.items():
            directory = self.root / owner.module_path / Path(owner.manifest).parent
            source = directory / "src/lib.rs"
            source.parent.mkdir()
            source.write_text("#![no_std]\n")
            if name == "nextcore-memory-service":
                with (directory / "Cargo.toml").open("a") as manifest:
                    manifest.write("[workspace]\n")
        workspace = self.root / "nextcore/Cargo.toml"
        members = [owner.module_path.relative_to("nextcore").as_posix() for owner in PRIMARY_PACKAGES.values()]
        workspace.write_text('[workspace]\nresolver="2"\nmembers=' + json.dumps(members)
                             + '\nexclude=["crates/nextcore-ise/runtime/memory-service"]\n')
        remote = self.root / "remote-fixture"
        (remote / "src").mkdir(parents=True)
        (remote / "Cargo.toml").write_text('[package]\nname="nextcore-memory-service"\nversion="0.1.0"\n')
        (remote / "src/lib.rs").write_text("#![no_std]\n")
        subprocess.run(["git", "init", "-q", str(remote)], check=True)
        subprocess.run(["git", "-C", str(remote), "add", "."], check=True)
        subprocess.run(["git", "-C", str(remote), "-c", "commit.gpgsign=false", "-c", "user.name=Policy test", "-c", "user.email=test@example.invalid",
                        "commit", "-q", "-m", "Independent source fixture"], check=True)
        revision = subprocess.check_output(["git", "-C", str(remote), "rev-parse", "HEAD"], text=True).strip()
        efi = self.root / PACKAGES["nextcore-efi"].module_path / "Cargo.toml"
        efi.write_text(efi.read_text() + '[features]\narm-jit-memory-provider=[]\n'
                       '[dependencies]\nnextcore-memory-service={git=' + json.dumps(remote.as_uri())
                       + ',rev=' + json.dumps(revision) + ',version="=0.1.0"}\n')
        with workspace.open("a") as manifest:
            manifest.write('[patch.' + json.dumps(remote.as_uri()) + ']\n'
                           'nextcore-memory-service={path="crates/nextcore-ise/runtime/memory-service"}\n')
        command = ["cargo", "metadata", "--format-version", "1", "--manifest-path", str(workspace),
                   "--features", "nextcore-efi/arm-jit-memory-provider"]
        environment = {**os.environ, "CARGO_HOME": str(self.root / "cargo-cache")}
        positive = subprocess.run(command, text=True, capture_output=True, env=environment)
        self.assertEqual(positive.returncode, 0, positive.stderr)
        self.assertTrue(validate_cargo_metadata(self.root, json.loads(positive.stdout))["memory_service_local_and_selected"])
        (remote / "Cargo.toml").write_text('[package]\nname="nextcore-memory-service"\nversion="0.2.0"\n')
        subprocess.run(["git", "-C", str(remote), "add", "Cargo.toml"], check=True)
        subprocess.run(["git", "-C", str(remote), "-c", "commit.gpgsign=false", "-c", "user.name=Policy test", "-c", "user.email=test@example.invalid",
                        "commit", "-q", "-m", "Independent duplicate fixture"], check=True)
        revision = subprocess.check_output(["git", "-C", str(remote), "rev-parse", "HEAD"], text=True).strip()
        with efi.open("a") as manifest:
            manifest.write('remote-service={package="nextcore-memory-service",git='
                           + json.dumps(remote.as_uri()) + ',rev=' + json.dumps(revision) + ',version="=0.2.0"}\n')
        duplicate = subprocess.run(command, text=True, capture_output=True, env=environment)
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        resolved = json.loads(duplicate.stdout)
        self.assertEqual(sum(p["name"] == "nextcore-memory-service" for p in resolved["packages"]), 2)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_cargo_metadata(self.root, resolved)

    def test_refresher_real_git_fixture_records_one_revision_and_rejects_conflict_without_writes(self):
        root = self.root / PACKAGES["nextcore-efi"].module_path
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "-c", "commit.gpgsign=false", "-c", "user.name=Policy test", "-c", "user.email=test@example.invalid",
                        "commit", "-q", "--allow-empty", "-m", "Fixture"], check=True)
        metadata = root / "repository.json"
        metadata.write_text(json.dumps({"name": "Nextcore-EFI", "description": "Fixture"}))
        manifest = root / "Cargo.toml"
        original = manifest.read_text() + (
            f'[dependencies]\nnextcore-memory-service={{git="{ISE_URL}",rev="{REVISION}"}}\n'
            f'[build-dependencies]\nnextcore-ise={{git="{ISE_URL}",rev="{REVISION}"}}\n')
        manifest.write_text(original)
        command = [sys.executable, str(TOOLS / "refresh_nextcore_module_metadata.py"), str(root)]
        first = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(metadata.read_text())["development"]["dependency_revisions"],
                         {ISE_URL.removesuffix(".git"): REVISION})
        before = {p.name: p.read_bytes() for p in (metadata, root / "repository-files.json")}
        manifest.write_text(original.replace(f'nextcore-ise={{git="{ISE_URL}",rev="{REVISION}"}}',
                                             f'nextcore-ise={{git="{ISE_URL}",rev="{OTHER_REVISION}"}}'))
        rejected = subprocess.run(command, text=True, capture_output=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("conflicting", rejected.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (metadata, root / "repository-files.json")})


if __name__ == "__main__":
    unittest.main()
