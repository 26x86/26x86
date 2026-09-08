#!/usr/bin/env python3
"""Check gitlink ownership and Cargo resolution for the seven NextCore modules."""
from __future__ import annotations
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("Core", "EFI", "Tool", "ISE", "GPU", "HAL", "APLS")

def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

def verify(cargo: bool = False, clean: bool = False) -> dict:
    config = configparser.ConfigParser()
    config.read(ROOT / ".gitmodules")
    expected = {"nextcore-" + name.lower(): name for name in MODULES}
    if set(config.sections()) != {f'submodule "{crate}"' for crate in expected}:
        raise ValueError(".gitmodules must describe exactly the seven NextCore modules")
    receipts = []
    for crate, name in expected.items():
        path = f"nextcore/crates/{crate}"
        url = f"https://github.com/26x86/Nextcore-{name}.git"
        section = config[f'submodule "{crate}"']
        if section.get("path") != path or section.get("url") != url:
            raise ValueError(f"{crate}: unexpected path or remote")
        entries = run("git", "ls-files", "--stage", "--", path).splitlines()
        if len(entries) != 1:
            raise ValueError(f"{crate}: sources must belong to the submodule, not the parent index")
        metadata, entry_path = entries[0].split("\t", 1)
        mode, pinned, stage = metadata.split()
        if (mode, stage, entry_path) != ("160000", "0", path):
            raise ValueError(f"{crate}: expected one stage-zero gitlink")
        absolute = ROOT / path
        if not (absolute / ".git").exists():
            raise ValueError(f"{crate}: run git submodule update --init --recursive")
        head = run("git", "-C", str(absolute), "rev-parse", "HEAD")
        if head != pinned:
            raise ValueError(f"{crate}: checkout does not match parent gitlink")
        if run("git", "-C", str(absolute), "remote", "get-url", "origin") != url:
            raise ValueError(f"{crate}: origin differs from .gitmodules")
        if clean and run("git", "-C", str(absolute), "status", "--porcelain"):
            raise ValueError(f"{crate}: uncommitted module changes")
        tracked = subprocess.check_output(
            ["git", "-C", str(absolute), "ls-files", "-z"], text=True
        ).split("\0")
        if any("_isolated" in Path(p).parts for p in tracked):
            raise ValueError(f"{crate}: private assets are tracked")
        receipts.append({"crate": crate, "path": path, "url": url, "commit": head})
    heads = {entry["crate"]: entry["commit"] for entry in receipts}
    for entry in receipts:
        absolute = ROOT / entry["path"]
        manifest = tomllib.loads((absolute / "Cargo.toml").read_text())
        for section_name in ("dependencies", "build-dependencies", "dev-dependencies"):
            for dependency, specification in manifest.get(section_name, {}).items():
                if dependency not in expected:
                    continue
                expected_url = f"https://github.com/26x86/Nextcore-{expected[dependency]}.git"
                if (not isinstance(specification, dict) or "path" in specification
                        or specification.get("git") != expected_url
                        or specification.get("rev") != heads[dependency]):
                    raise ValueError(f'{entry["crate"]}: {dependency} must pin the integrated remote revision')
        if clean:
            inventory = json.loads((absolute / "repository-files.json").read_text())
            tracked_files = set(subprocess.check_output(
                ["git", "-C", str(absolute), "ls-files", "-z"], text=True
            ).split("\0")) - {"", "repository-files.json", "repository.json"}
            inventoried_files = {item["path"] for item in inventory["files"]} - {"repository.json"}
            if tracked_files != inventoried_files or len(inventory["files"]) != len({item["path"] for item in inventory["files"]}):
                raise ValueError(f'{entry["crate"]}: inventory does not cover the tracked public files exactly')
            for item in inventory["files"]:
                relative = Path(item["path"])
                if relative.is_absolute() or ".." in relative.parts or "_isolated" in relative.parts:
                    raise ValueError(f'{entry["crate"]}: invalid inventory path')
                data = (absolute / relative).read_bytes()
                if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError(f'{entry["crate"]}: stale inventory for {relative}')
    if cargo:
        host = next(line.removeprefix("host: ") for line in run("rustc", "-vV").splitlines() if line.startswith("host: "))
        metadata = json.loads(run("cargo", "metadata", "--locked", "--format-version", "1", "--filter-platform", host,
                                  "--manifest-path", str(ROOT / "nextcore/Cargo.toml")))
        members = set(metadata["workspace_members"])
        packages = [p for p in metadata["packages"] if p["name"] in expected]
        if len(packages) != len(expected):
            raise ValueError("Cargo resolved missing or duplicate NextCore packages")
        for package in packages:
            manifest = ROOT / "nextcore/crates" / package["name"] / "Cargo.toml"
            if (Path(package["manifest_path"]).resolve() != manifest.resolve()
                    or package["source"] is not None or package["id"] not in members):
                raise ValueError(f'{package["name"]}: Cargo did not resolve the local submodule')
    return {"schema": "nextcore-submodules/1", "modules": receipts,
            "cargo_local_resolution_checked": cargo, "clean_required": clean}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cargo", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.cargo, args.require_clean), indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"submodule verification failed: {error}\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
