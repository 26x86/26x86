#!/usr/bin/env python3
"""Export the core checkout into the declared public module repositories.

The command only writes a fresh output directory. It never removes or mutates
the working tree and it never talks to GitHub. Publishing is a separate,
explicit command in ``sync_github_repositories.py``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
VENFIRE = ROOT / "research" / "venfire"
QEMU_PATCHES = VENFIRE / "patches"
QEMU_TOOLS = {
    "backend_audit.py",
    "build_backend.py",
    "verify.py",
    "verify_arm_timer.py",
    "verify_arm_timer_math.py",
    "verify_barrier.py",
    "verify_bdif_storage.py",
    "verify_optional_rpc.py",
    "verify_recovery.py",
    "verify_storage.py",
}
QEMU_DOCS = {
    "backend.md",
    "graphics.md",
    "kernel-watchdog.md",
    "storage-barrier.md",
    "storage.md",
    "target.md",
}


def copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "build", "dist", "verification-*"))
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def copy_named(source_root: Path, destination_root: Path, names: list[str]) -> None:
    for name in names:
        source = source_root / name
        if source.exists():
            copy_path(source, destination_root / name)


def git_head() -> str:
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _git_config(key: str, fallback: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), "config", key],
                            capture_output=True, text=True)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else fallback


def init_module_repository(destination: Path, *, tag: str) -> None:
    """Give the exported tree its own initial commit and module tag."""
    name = _git_config("user.name", "26x86 release tooling")
    email = _git_config("user.email", "release@localhost")
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(destination), *args],
                       check=True, capture_output=True, text=True)
    git("init", "-b", "main")
    git("add", "-A")
    git("-c", f"user.name={name}", "-c", f"user.email={email}",
        "commit", "-m", f"Initial module export ({tag})")
    git("tag", tag)


def file_inventory(root: Path) -> list[dict[str, object]]:
    entries = []
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == "repository.json":
            continue
        entries.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "bytes": path.stat().st_size})
    return entries


def write_repository_metadata(destination: Path, *, name: str, role: str,
                              description: str, depends_on: list[str], source: str,
                              tag: str) -> None:
    document = {
        "schema": "26x86.repository/1",
        "name": name,
        "owner": "26x86",
        "public": True,
        "role": role,
        "description": description,
        "source_path": source,
        "source_commit": git_head(),
        "source_worktree_may_be_dirty": True,
        "depends_on": depends_on,
        "initial_tag": tag,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (destination / "repository.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    (destination / "repository-files.json").write_text(
        json.dumps({"schema": "26x86.repository-files/1", "files": file_inventory(destination)},
                   indent=2) + "\n", encoding="utf-8")


def venfire_readme(destination: Path) -> None:
    (destination / "README.md").write_text(
        "# VenFire\n\n"
        "User-space ARM64 VMApple/TCG conformance, storage-integrity and "
        "recovery policy for [26x86](https://github.com/26x86/26x86).\n\n"
        "Layer: x86_64 Linux/WSL host -> QEMU TCG -> AArch64 guest. "
        "Virtualization.framework, HVF and Apple hardware are not required "
        "for this software-emulation layer.\n\n"
        "The companion backend is [VenFire-QEMU](https://github.com/"
        "26x86/VenFire-QEMU). A synthetic guest PASS is not a macOS "
        "boot claim. The UART evidence gate requires caller-supplied original "
        "signed Golden Gate inputs and target-matching XNU/userspace markers.\n\n"
        "See `DEVELOPMENT_POLICY.md` for release gating and `repository.json` "
        "for the publication relationship.\n", encoding="utf-8")


def qemu_readme(destination: Path) -> None:
    (destination / "README.md").write_text(
        "# VenFire-QEMU\n\n"
        "Reproducible QEMU VMApple TCG/headless backend for the "
        "[VenFire](https://github.com/26x86/VenFire) control plane. The source is pinned to `ff1d2d19d7e24893e2012d879f8e73077e17b9bd` "
        "and the patch order is recorded in `patches/series`.\n\n"
        "This is the host emulator/device-model layer. It does not contain "
        "Apple firmware or guest disks, and it does not claim macOS boot. "
        "Use `tools/build_backend.py` for a fresh build and `tools/backend_audit.py` "
        "for the source relationship audit.\n", encoding="utf-8")


def write_common_files(destination: Path) -> None:
    (destination / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n.pytest_cache/\nbuild/\ndist/\n*.egg-info/\n", encoding="utf-8")
    (destination / ".gitattributes").write_text(
        "* text=auto\n*.S text eol=lf\n*.patch text eol=lf\n*.bin binary\n*.elf binary\n",
        encoding="utf-8")


def write_ci(destination: Path, kind: str) -> None:
    workflow = destination / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    if kind == "venfire":
        body = """name: VenFire CI
on:
  push:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: python3 -m unittest discover -s tests -v
      - run: python3 -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
"""
    else:
        body = """name: VenFire-QEMU CI
on:
  push:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  source-contract:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y git
      - run: |
          git init "$RUNNER_TEMP/qemu"
          git -C "$RUNNER_TEMP/qemu" remote add origin https://github.com/qemu/qemu.git
          git -C "$RUNNER_TEMP/qemu" fetch --depth=1 origin ff1d2d19d7e24893e2012d879f8e73077e17b9bd
          git -C "$RUNNER_TEMP/qemu" checkout --detach ff1d2d19d7e24893e2012d879f8e73077e17b9bd
          while read -r patch; do
            test -z "$patch" && continue
            git -C "$RUNNER_TEMP/qemu" apply --check "patches/$patch"
            git -C "$RUNNER_TEMP/qemu" apply "patches/$patch"
          done < patches/series
      - run: python3 tools/backend_audit.py --source "$RUNNER_TEMP/qemu" --require-patched
"""
    workflow.write_text(body, encoding="utf-8")


def export(output: Path) -> dict[str, object]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"output must be a fresh directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    venfire = output / "VenFire"
    qemu = output / "VenFire-QEMU"
    venfire.mkdir()
    qemu.mkdir()

    copy_named(VENFIRE, venfire, ["venfire", "guests", "tests", "usb", "docs", "evidence"])
    copy_named(VENFIRE, venfire, ["pyproject.toml", "venfire_build_backend.py", "MANIFEST.in",
                                  "DEVELOPMENT_POLICY.md", ".gitignore", ".gitattributes"])
    copy_named(VENFIRE / "tools", venfire / "tools", [
        name for name in sorted(path.name for path in (VENFIRE / "tools").glob("*.py"))
        if name not in QEMU_TOOLS
    ])
    write_common_files(venfire)
    venfire_readme(venfire)
    write_ci(venfire, "venfire")
    write_repository_metadata(
        venfire, name="VenFire", role="emulation-control-plane",
        description="26x86 ARM64 VMApple/TCG conformance and evidence tooling",
        depends_on=["26x86/VenFire-QEMU"], source="research/venfire",
        tag="26x86-VenFire-v0.1.0")
    init_module_repository(venfire, tag="26x86-VenFire-v0.1.0")

    copy_path(QEMU_PATCHES, qemu / "patches")
    copy_named(VENFIRE / "tools", qemu / "tools", sorted(QEMU_TOOLS))
    copy_named(VENFIRE, qemu, [".gitignore", ".gitattributes"])
    copy_named(VENFIRE / "docs", qemu / "docs", sorted(QEMU_DOCS))
    copy_named(VENFIRE / "evidence", qemu / "evidence", [
        "backend-core4.json", "backend-source-audit.json", "vmapple-machine-help.txt",
        "storage-barrier.json", "readonly-block-view.json", "recovery-lifecycle.json",
    ])
    copy_path(ROOT / "LICENSE.txt", qemu / "LICENSE.txt")
    write_common_files(qemu)
    qemu_readme(qemu)
    write_ci(qemu, "qemu")
    write_repository_metadata(
        qemu, name="VenFire-QEMU", role="qemu-backend",
        description="Reproducible QEMU VMApple TCG/headless patch series and source audit",
        depends_on=["qemu/qemu@ff1d2d19d7e24893e2012d879f8e73077e17b9bd"],
        source="research/venfire/patches", tag="26x86-VenFire-QEMU-v0.1.0")
    init_module_repository(qemu, tag="26x86-VenFire-QEMU-v0.1.0")
    return {"output": str(output), "repositories": [str(venfire), str(qemu)]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.output.absolute()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
