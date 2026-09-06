"""Bounded, read-only executable discovery. Capability is not boot evidence."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def resolve_qemu(path: str | None = None) -> str:
    candidate = path or shutil.which("qemu-system-aarch64")
    if not candidate:
        raise ValueError("qemu-system-aarch64 not found; build the pinned backend first")
    executable = Path(candidate).resolve(strict=True)
    if not executable.is_file():
        raise ValueError("QEMU executable must be a regular file")
    return str(executable)


def probe_backend(path: str | None = None) -> dict:
    executable = resolve_qemu(path)
    outputs = {}
    for key, arguments in (("version", ["--version"]),
                           ("machines", ["-machine", "help"]),
                           ("accelerators", ["-accel", "help"])):
        result = subprocess.run([executable, *arguments], capture_output=True,
                                text=True, timeout=15, check=False)
        if result.returncode:
            raise ValueError(f"QEMU {key} probe failed: {result.stderr.strip()}")
        outputs[key] = result.stdout
    machines = {line.split()[0] for line in outputs["machines"].splitlines()
                if line.strip()}
    has_vmapple = "vmapple" in machines
    research = False
    graphics = False
    bdif_writes = False
    if has_vmapple:
        result = subprocess.run([executable, "-machine", "vmapple,help"],
                                capture_output=True, text=True, timeout=15)
        research = result.returncode == 0 and "research-headless" in result.stdout
        graphics = result.returncode == 0 and "research-graphics" in result.stdout
        result = subprocess.run([executable, "-device", "vmapple-bdif,help"],
                                capture_output=True, text=True, timeout=15)
        bdif_writes = result.returncode == 0 and "allow-block-writes" in result.stdout
    return {"executable": executable, "version": outputs["version"].splitlines()[0],
            "tcg": "tcg" in outputs["accelerators"].split(),
            "virt": "virt" in machines, "vmapple": has_vmapple,
            "research_headless": research,
            "research_graphics": graphics,
            "bdif_block_writes": bdif_writes,
            "macos_boot_verified": False,
            "note": "Listed features require runtime conformance; help output is not execution evidence."}
