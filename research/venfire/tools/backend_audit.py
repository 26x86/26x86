#!/usr/bin/env python3
"""Audit the pinned QEMU VMApple source/patch; this is not a boot test.

No network requests, Apple inputs, guest execution, or source modifications.
Python 3.10+ and git are required. Exit 0 means the source identity and patch
relationship are verified; it never means that macOS or hardware is supported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


UPSTREAM_COMMIT = "ff1d2d19d7e24893e2012d879f8e73077e17b9bd"
UPSTREAM_URL = "https://github.com/qemu/qemu"
PATCH_FILES = {"configs/devices/aarch64-softmmu/default.mak",
               "hw/vmapple/Kconfig", "hw/vmapple/vmapple.c", "hw/vmapple/aes.c"}
SOURCE_PATHS = (
    "configs/devices/aarch64-softmmu/default.mak",
    "hw/vmapple/Kconfig",
    "hw/vmapple/vmapple.c",
    "hw/vmapple/aes.c",
    "hw/vmapple/cfg.c",
    "hw/vmapple/bdif.c",
    "hw/display/Kconfig",
    "hw/display/meson.build",
    "hw/intc/arm_gicv3_common.c",
    "target/arm/cpu64.c",
    "target/arm/tcg/pauth_helper.c",
    "docs/system/arm/vmapple.rst",
)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, timeout=60
    )


def source(root: Path, path: str) -> str:
    result = git(root, "show", f"{UPSTREAM_COMMIT}:{path}")
    if result.returncode:
        raise ValueError(f"Missing pinned source file: {path}")
    return result.stdout.decode("utf-8")


def anchor(text: str, fragment: str) -> int:
    for line, value in enumerate(text.splitlines(), 1):
        if fragment in value:
            return line
    raise ValueError(f"Expected upstream evidence is absent: {fragment}")


def audit(root: Path, patch: Path, require_patched: bool) -> dict:
    version = git(root, "rev-parse", "HEAD")
    head = version.stdout.decode().strip()
    if version.returncode or head != UPSTREAM_COMMIT:
        raise ValueError(f"Expected QEMU {UPSTREAM_COMMIT}; found {head!r}")
    if not patch.is_file():
        raise ValueError(f"Patch file does not exist: {patch}")
    stats = git(root, "apply", "--numstat", str(patch))
    if stats.returncode:
        raise ValueError("Cannot enumerate patch paths")
    patch_paths = {line.split("\t", 2)[2] for line in stats.stdout.decode().splitlines()}
    if not patch_paths:
        raise ValueError("Patch has no file changes")

    sources = {name: source(root, name) for name in SOURCE_PATHS}
    findings = []
    for identifier, name, fragment, finding in (
        ("default-build-disabled", "configs/devices/aarch64-softmmu/default.mak", "CONFIG_VMAPPLE=n",
         "Upstream default aarch64 device configuration explicitly disables VMApple."),
        ("hvf-build-gate", "hw/vmapple/Kconfig", "depends on HVF",
         "Upstream VMApple is excluded from a TCG-only build."),
        ("apple-graphics-build-gate", "hw/vmapple/Kconfig", "select MAC_PVG_MMIO",
         "VMApple unconditionally selects the Apple PV graphics device."),
        ("apple-graphics-framework", "hw/display/meson.build", "CONFIG_MAC_PVG_MMIO",
         "The graphics implementation depends on the host PVG framework."),
        ("host-cpu-default", "hw/vmapple/vmapple.c", 'ARM_CPU_TYPE_NAME("host")',
         "Cross-ISA TCG requires an explicit emulated -cpu; host is the default."),
        ("graphics-realization", "hw/vmapple/vmapple.c", "create_gfx(vms, sysmem)",
         "Upstream always realizes apple-gfx-mmio during machine initialization."),
        ("firmware-entry", "hw/vmapple/vmapple.c", "{ 0x00100000, 0x00100000 }",
         "Firmware starts at 0x00100000 and has a 1 MiB aperture."),
        ("gic-tcg-implementation", "hw/intc/arm_gicv3_common.c", 'return "arm-gicv3"',
         "TCG selects the existing userspace GICv3 implementation."),
        ("aes-builtin-slots", "hw/vmapple/aes.c", "static Key builtin_keys",
         "Upstream fixed AES slot keys implement documented virtual NVRAM semantics; they are not physical UID/GID/SEP keys."),
        ("architectural-pac", "target/arm/tcg/pauth_helper.c", "pauth_computepac_architected",
         "Upstream implements architectural PAC algorithms; this is not proof of Apple arm64e equivalence."),
        ("upstream-guest-limit", "docs/system/arm/vmapple.rst", "12.x",
         "Pinned upstream documentation supports macOS 12.x guests on Apple Silicon/HVF only."),
    ):
        line = anchor(sources[name], fragment)
        findings.append({
            "id": identifier,
            "finding": finding,
            "path": name,
            "line": line,
            "source_url": f"{UPSTREAM_URL}/blob/{UPSTREAM_COMMIT}/{name}#L{line}",
        })

    forward = git(root, "apply", "--check", str(patch))
    reverse = git(root, "apply", "--reverse", "--check", str(patch))
    if reverse.returncode == 0 and forward.returncode != 0:
        patch_state = "applied"
    elif forward.returncode == 0 and reverse.returncode != 0:
        patch_state = "unapplied"
    else:
        raise ValueError("Source tree is neither the clean patch base nor the expected patched state")
    changed = git(root, "diff", "--name-only", "HEAD", "--", ".")
    changed_paths = set(changed.stdout.decode().splitlines())
    if changed_paths - patch_paths:
        raise ValueError(f"Unexpected tracked source modifications: {sorted(changed_paths - patch_paths)}")
    if patch_state == "unapplied" and changed_paths:
        raise ValueError(f"Unpatched baseline has tracked modifications: {sorted(changed_paths)}")
    if require_patched and patch_state != "applied":
        raise ValueError("The research patch is not applied")

    clean = git(root, "diff", "--check")
    if clean.returncode:
        raise ValueError(clean.stdout.decode(errors="replace"))

    # Reverse-apply checks alone allow unrelated edits in the same files.
    # Compare each expected patched file via git's object index in a temporary
    # directory, without touching the checkout or its real index.
    if patch_state == "applied":
        import os
        import tempfile

        with tempfile.TemporaryDirectory(prefix="venfire-audit-") as temp:
            env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / "index"))
            for args in (("read-tree", UPSTREAM_COMMIT),
                         ("apply", "--cached", str(patch))):
                result = subprocess.run(["git", "-C", str(root), *args],
                                        env=env, capture_output=True, timeout=60)
                if result.returncode:
                    raise ValueError(result.stderr.decode(errors="replace"))
            for name in patch_paths:
                result = subprocess.run(["git", "-C", str(root), "show", f":{name}"],
                                        env=env, capture_output=True, timeout=60)
                actual = (root / name).read_bytes().replace(b"\r\n", b"\n")
                if result.returncode or result.stdout != actual:
                    raise ValueError(f"Patched source differs from the delivered patch: {name}")

    return {
        "schema": "venfire.backend-source-audit.v1",
        "status": "source_verified",
        "verification_layer": "host emulator source; no guest execution",
        "upstream_commit": UPSTREAM_COMMIT,
        "patch_state": patch_state,
        "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
        "upstream_source_sha256": {
            name: hashlib.sha256(text.encode()).hexdigest() for name, text in sources.items()
        },
        "findings": findings,
        "aes_provenance_url": "https://lists.nongnu.org/archive/html/qemu-riscv/2024-11/msg00129.html",
        "limits": [
            "This audit does not compile QEMU or execute guest firmware.",
            "It proves neither macOS boot, Metal acceleration, nor real-Mac execution.",
            "QARMA5 is an architectural test algorithm, not a claim about Apple's implementation.",
            "Apple boot assets must be supplied separately and remain unmodified.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--patch", type=Path, help="Override the default complete patches/series")
    parser.add_argument("--require-patched", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.patch:
            report = audit(args.source.resolve(), args.patch.resolve(), args.require_patched)
        else:
            import tempfile
            from build_backend import patch_series
            patches = patch_series()
            with tempfile.TemporaryDirectory(prefix="venfire-patch-series-") as temporary:
                aggregate = Path(temporary) / "series.patch"
                aggregate.write_bytes(b"\n".join(patch.read_bytes() for patch in patches))
                report = audit(args.source.resolve(), aggregate, args.require_patched)
                report["patches"] = [{"name": patch.name, "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()}
                                     for patch in patches]
        code = 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report = {"schema": "venfire.backend-source-audit.v1", "status": "failed",
                  "error": str(exc)}
        code = 1
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
