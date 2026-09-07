#!/usr/bin/env python3
"""Build a reproducible Linux/Windows-host TCG VMApple binary.

The upstream VMApple machine is normally hidden behind the macOS HVF Kconfig
gate.  26x86 keeps the guest inputs untouched and applies the reviewed
``research/venfire/patches/series`` to a pinned QEMU checkout.  This is an
emulator build step, not a Virtualization.framework or Apple-hardware
requirement.

The output directory is created by this script and is never removed or reused
implicitly.  A receipt records the exact source commit, patch digest, command
lines, and resulting binary digest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Sequence


QEMU_REPOSITORY = "https://github.com/qemu/qemu.git"
QEMU_COMMIT = "ff1d2d19d7e24893e2012d879f8e73077e17b9bd"
PROJECT = Path(__file__).resolve().parents[1]
PATCH_SERIES = PROJECT / "research" / "venfire" / "patches" / "series"
PATCH_ROOT = PATCH_SERIES.parent


def _run(argv: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), cwd=cwd, check=True, text=True)


def _capture(argv: Sequence[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(list(argv), cwd=cwd, text=True).strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _patch_series() -> list[Path]:
    if not PATCH_SERIES.is_file():
        raise ValueError(f"missing patch series: {PATCH_SERIES}")
    names = [line.strip() for line in PATCH_SERIES.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not names or len(names) != len(set(names)):
        raise ValueError("QEMU patch series must be nonempty and contain unique entries")
    patches = []
    for name in names:
        path = PATCH_ROOT / name
        if Path(name).name != name or path.suffix != ".patch" or not path.is_file():
            raise ValueError(f"invalid QEMU patch series entry: {name}")
        patches.append(path)
    return patches


def _new_output(value: str | None) -> Path:
    if value:
        output = Path(value).expanduser().absolute()
        if output.exists() or output.is_symlink():
            raise ValueError(f"output must be a new directory: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir()
        return output
    output = Path.cwd() / f"26x86-vmapple-tcg-{QEMU_COMMIT[:12]}"
    if output.exists() or output.is_symlink():
        raise ValueError(f"output must be a new directory: {output}")
    output.mkdir()
    return output


def _clone(source: str | None, checkout: Path) -> None:
    if source:
        source_path = Path(source).expanduser().resolve(strict=True)
        if not (source_path / ".git").exists():
            raise ValueError(f"source is not a git checkout: {source_path}")
        if _capture(["git", "-C", str(source_path), "rev-parse", "HEAD"]) != QEMU_COMMIT:
            raise ValueError(f"source must be pinned at QEMU commit {QEMU_COMMIT}")
        dirty = _capture(["git", "-C", str(source_path), "status", "--porcelain"])
        if dirty:
            raise ValueError("source checkout is dirty; use a clean checkout")
        _run(["git", "clone", "--no-local", "--no-hardlinks", str(source_path), str(checkout)])
    else:
        _run(["git", "clone", "--filter=blob:none", QEMU_REPOSITORY, str(checkout)])
    _run(["git", "checkout", "--detach", QEMU_COMMIT], cwd=checkout)


def _configure(source: Path) -> list[str]:
    return [
        "./configure",
        "--target-list=aarch64-softmmu",
        "--enable-tcg",
        "--disable-werror",
        "--disable-docs",
        "--disable-gtk",
        "--disable-sdl",
        "--disable-spice",
        "--disable-opengl",
        "--disable-vnc",
        "--disable-kvm",
        "--disable-hvf",
        "--disable-libssh",
        "--disable-libnfs",
        "--disable-libiscsi",
        "--disable-seccomp",
        "--disable-capstone",
    ]


def build(*, output: str | None, source: str | None, jobs: int) -> dict[str, object]:
    if type(jobs) is not int or not 1 <= jobs <= 256:
        raise ValueError("jobs must be between 1 and 256")
    patches = _patch_series()
    destination = _new_output(output)
    source_dir = destination / "qemu"
    _clone(source, source_dir)
    for patch in patches:
        _run(["git", "apply", "--check", str(patch)], cwd=source_dir)
        _run(["git", "apply", str(patch)], cwd=source_dir)
    configure = _configure(source_dir)
    _run(configure, cwd=source_dir)
    ninja = ["ninja", "-C", "build", "-j", str(jobs), "qemu-system-aarch64"]
    _run(ninja, cwd=source_dir)
    binary = source_dir / "build" / "qemu-system-aarch64"
    if not binary.is_file():
        raise RuntimeError("QEMU build did not produce qemu-system-aarch64")
    version = _capture([str(binary), "--version"])
    machines = _capture([str(binary), "-machine", "help"])
    accelerators = _capture([str(binary), "-accel", "help"])
    if not any(line.split() and line.split()[0] == "vmapple" for line in machines.splitlines()):
        raise RuntimeError("built QEMU does not expose the vmapple machine")
    if "tcg" not in accelerators.split():
        raise RuntimeError("built QEMU does not expose TCG")
    machine_help = _capture([str(binary), "-machine", "vmapple,help"])
    if "research-headless" not in machine_help:
        raise RuntimeError("built QEMU does not expose explicit research-headless VMApple mode")
    bdif_help = _capture([str(binary), "-device", "vmapple-bdif,help"])
    if "allow-block-writes" not in bdif_help:
        raise RuntimeError("built QEMU does not expose the BDIF write gate")
    receipt: dict[str, object] = {
        "schema": "26x86.vmapple-tcg-build/1",
        "host_layer": "non-Apple host software emulation",
        "source": {
            "repository": QEMU_REPOSITORY,
            "commit": QEMU_COMMIT,
            "checkout": str(source_dir),
        },
        "patch_series": {
            "path": str(PATCH_SERIES),
            "patches": [{"path": str(patch), "sha256": _sha256(patch)} for patch in patches],
        },
        "configure": configure,
        "build": ninja,
        "binary": {
            "path": str(binary),
            "sha256": _sha256(binary),
            "bytes": binary.stat().st_size,
            "version": version.splitlines()[0] if version else "",
        },
        "capabilities": {
            "machine": "vmapple",
            "accelerator": "tcg",
            "virtualization_framework": False,
            "apple_hardware": False,
            "graphics": "headless serial/recovery only",
        },
        "guest_inputs_modified": False,
    }
    (destination / "build-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="new build directory")
    parser.add_argument("--source", help="clean checkout already at the pinned commit")
    parser.add_argument("--jobs", type=int, default=max(1, os.cpu_count() or 1))
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(output=args.output, source=args.source, jobs=args.jobs), indent=2))
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
