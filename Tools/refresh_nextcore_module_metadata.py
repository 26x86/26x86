#!/usr/bin/env python3
"""Refresh development metadata and public file hashes in a Nextcore module."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def refresh(root: Path) -> None:
    root = root.resolve(strict=True)
    manifest = tomllib.loads((root / "Cargo.toml").read_text())
    metadata_path = root / "repository.json"
    old = json.loads(metadata_path.read_text())
    provenance = old.get("release_provenance", old)
    dependencies = {}
    for section in ("dependencies", "build-dependencies", "dev-dependencies"):
        for name, specification in manifest.get(section, {}).items():
            if name.startswith("nextcore-") and isinstance(specification, dict):
                if "path" in specification or not specification.get("git") or not specification.get("rev"):
                    raise ValueError(f"{name}: independent modules require git URL and immutable rev")
                dependencies[specification["git"].removesuffix(".git")] = specification["rev"]
    metadata = {
        "schema": "26x86.repository/2", "name": old["name"],
        "owner": "26x86", "public": True, "role": "nextcore-module",
        "crate": manifest["package"]["name"], "description": old["description"],
        "development": {
            "branch": git(root, "branch", "--show-current").decode().strip(),
            "base_commit": old.get("development", {}).get("base_commit") or git(root, "rev-parse", "HEAD").decode().strip(),
            "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "dependency_revisions": dependencies,
            "integration": "Git submodule with an immutable gitlink; workspace source patches for local development",
        },
        "release_provenance": provenance,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    paths = sorted(set(git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").decode().split("\0")) - {"", "repository-files.json"})
    files = []
    for relative in paths:
        path = root / relative
        if "_isolated" in Path(relative).parts:
            raise ValueError(f"private path in module inventory: {relative}")
        if not path.exists():
            continue
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"inventory requires ordinary files: {relative}")
        data = path.read_bytes()
        files.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (root / "repository-files.json").write_text(json.dumps({"schema": "26x86.repository-files/1", "files": files}, indent=2) + "\n")
    print(f"{metadata['name']}: inventoried {len(files)} public files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    refresh(parser.parse_args().module)
