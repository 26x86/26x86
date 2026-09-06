#!/usr/bin/env python3
"""Generate an isolated, explicitly nonredistributable local lab tree."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

PROJECT = Path(__file__).resolve().parents[1]
COPY_DIRECTORIES = ("venfire", "guests", "tools", "usb", "tests", "docs", "patches")
COPY_FILES = ("pyproject.toml", "venfire_build_backend.py", "MANIFEST.in", "README.md",
              "DEVELOPMENT_POLICY.md", ".gitignore", ".gitattributes")


def _reject_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if (stat.S_ISLNK(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
        raise ValueError("Developer paths cannot contain symlinks or reparse points")


def _check_components(path):
    for part in [*reversed(path.parents), path]:
        _reject_link(part)


def create_developer_tree(source, destination):
    source = Path(source).absolute()
    _check_components(source)
    source = source.resolve(strict=True)
    requested = Path(destination).absolute()
    _check_components(requested)
    destination = requested.resolve(strict=False)
    if destination == source or source in destination.parents:
        raise ValueError("Use a separate work directory outside the release checkout")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Developer output must be a fresh directory")
    for top in (*COPY_DIRECTORIES, *COPY_FILES):
        candidate = source / top
        _reject_link(candidate)
        if candidate.exists():
            if candidate.is_dir():
                for directory, subdirs, files in os.walk(candidate, followlinks=False):
                    # Inspect each child before walk can descend into a junction.
                    for name in (*subdirs, *files):
                        _reject_link(Path(directory) / name)
    destination.mkdir(parents=True)
    for name in COPY_DIRECTORIES:
        path = source / name
        if path.is_dir():
            shutil.copytree(path, destination / name,
                            ignore=shutil.ignore_patterns("__pycache__", "verification-*", "*.pyc"))
    for name in COPY_FILES:
        if (source / name).is_file():
            shutil.copy2(source / name, destination / name)
    (destination / "venfire" / "_build_profile.py").write_text(
        '# PRIVATE LAB COPY. REDISTRIBUTION PROHIBITED BY PROJECT POLICY.\n'
        'BUILD_PROFILE = "developer-nonredistributable"\n', encoding="utf-8")
    marker = {"schema": 1, "build_profile": "developer-nonredistributable",
              "distribution_status": "NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT",
              "redistribution_permitted": False, "developer_host_bypass_available": True,
              "intel_avx2_required": True, "guest_trust_bypassed": False,
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "source": str(source),
              "policy_sha256": hashlib.sha256((source / "DEVELOPMENT_POLICY.md").read_bytes()).hexdigest()}
    (destination / "DEVELOPMENT_ONLY.json").write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    return marker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(create_developer_tree(PROJECT, args.output), indent=2))


if __name__ == "__main__":
    main()
