#!/usr/bin/env python3
"""Build exactly the reviewed upstream commit plus the 26x86 host-side patch.

Run on x86_64 macOS/Linux (Windows development: inside WSL). Does not install
globally, overwrite existing source, or access any Apple guest image.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

UPSTREAM = "https://github.com/qemu/qemu.git"
COMMIT = "ff1d2d19d7e24893e2012d879f8e73077e17b9bd"
PROJECT = Path(__file__).resolve().parents[1]


def patch_series():
    names = (PROJECT / "patches/series").read_text().splitlines()
    if not names or len(set(names)) != len(names):
        raise ValueError("Patch series must be nonempty and contain unique entries")
    if any(Path(name).name != name or not name.endswith(".patch") for name in names):
        raise ValueError("Invalid patch series path")
    return [PROJECT / "patches" / name for name in names]


def run(command, *, cwd=None, stdout=None):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, check=True, stdout=stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 2, 12))
    args = parser.parse_args()
    if platform.machine().lower() not in ("x86_64", "amd64") or os.name == "nt":
        parser.error("Use x86_64 macOS/Linux; on Windows invoke through WSL")
    if not 1 <= args.jobs <= 256:
        parser.error("jobs must be 1..256")
    # Check the OS exposes AVX2 before emitting code that requires it.
    if platform.system() == "Darwin":
        features = subprocess.check_output(["/usr/sbin/sysctl", "-n", "machdep.cpu.leaf7_features"], text=True)
    else:
        features = Path("/proc/cpuinfo").read_text()
    if "avx2" not in features.lower().split():
        parser.error("AVX2 is the minimum build/runtime host requirement")
    work = args.work.absolute()
    work.mkdir(parents=True, exist_ok=True)
    source, build = work / "qemu-source", work / "qemu-build"
    patches = patch_series()
    if source.exists() or build.exists():
        parser.error("Choose a fresh work directory; existing source/build will not be overwritten")
    run(["git", "init", source])
    run(["git", "remote", "add", "origin", UPSTREAM], cwd=source)
    run(["git", "fetch", "--depth=1", "origin", COMMIT], cwd=source)
    run(["git", "checkout", "--detach", COMMIT], cwd=source)
    for patch in patches:
        run(["git", "apply", "--check", patch], cwd=source)
        run(["git", "apply", patch], cwd=source)
    build.mkdir()
    configure = [source / "configure", "--target-list=aarch64-softmmu", "--enable-tcg",
                 "--disable-kvm", "--disable-hvf", "--disable-docs", "--disable-gtk",
                 "--disable-sdl", "--disable-opengl", "--disable-vnc", "--disable-tools",
                 "--disable-werror", "--extra-cflags=-mavx2"]
    run(configure, cwd=build)
    run(["ninja", "-j", args.jobs, "qemu-system-aarch64"], cwd=build)
    binary = build / "qemu-system-aarch64"
    evidence = {"upstream": UPSTREAM, "commit": COMMIT,
                "patches": [{"name": patch.name, "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()}
                            for patch in patches],
                "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "configure": [str(x) for x in configure],
                "host_system": platform.system(), "host_arch": platform.machine(),
                "minimum_cpu": "AVX2", "binary": str(binary),
                "macos_boot_verified": False}
    (build / "venfire-build.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
