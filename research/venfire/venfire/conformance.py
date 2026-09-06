"""Execute only the bundled, self-authored bare-metal AArch64 test guests.

This verifies a finite set of emulated CPU semantics, never macOS boot or Apple
hardware compatibility. No third-party firmware is accepted by this interface.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Sequence

from .artifacts import hash_artifact, read_regular

_CHECKOUT_GUESTS = Path(__file__).resolve().parent.parent / "guests"
GUESTS = (_CHECKOUT_GUESTS if _CHECKOUT_GUESTS.is_dir()
          else Path(sys.prefix) / "share" / "venfire" / "guests")
CASES = (
    "el1_entry", "integer_memory", "pauth_roundtrip", "pauth_wrong_context",
    "exception_svc", "mmu_4k_permissions", "mmu_4k_translation",
    "mmu_16k_permissions", "mmu_16k_translation", "timer_deadline", "gicv3_timer_irq",
    "self_modify",
)
LIMITATIONS = [
    "Self-authored guest only; no macOS, XNU, Apple boot chain, or Apple firmware executed.",
    "Single emulated CPU; one GICv3 virtual-timer PPI27 delivery/EOI path is checked.",
    "4KiB/16KiB granules use block mappings, not a complete VM subsystem or stage 2.",
    "16 negative PAC contexts are finite checks, not a cryptographic audit or Apple PAC match.",
    "Self-modifying code checks TCG coherency, not physical CPU cache behavior.",
    "GPU, Metal, SMP, DMA, storage drivers, suspend and real-Mac boot are untested.",
]


def sha256(path: Path) -> str:
    return hash_artifact(path, kind="conformance").sha256


def parse_serial(serial: str, *, returncode: int | None = 0,
                 timed_out: bool = False) -> dict:
    """Fail closed on missing, duplicated, contradictory, or malformed evidence."""
    observed: dict[str, str] = {}
    errors: list[str] = []
    begun = done = False
    order: list[str] = []
    for line in serial.splitlines():
        if not line.startswith("VENFIRE|"):
            continue
        parts = line.strip().split("|")
        if len(parts) != 3:
            errors.append(f"Malformed protocol line: {line}")
            continue
        _, status, name = parts
        if status == "BEGIN":
            if begun or done or name != "1":
                errors.append("Invalid or repeated BEGIN marker")
            begun = True
        elif status == "DONE":
            if not begun or done or name != "1":
                errors.append("Invalid or repeated DONE marker")
            done = True
        elif status in ("PASS", "FAIL", "UNSUPPORTED"):
            if not begun or done:
                errors.append(f"Result outside BEGIN/DONE: {name}")
            if name not in CASES:
                errors.append(f"Unexpected test result: {name}")
            if name in observed:
                errors.append(f"Duplicate test result: {name}")
            observed[name] = status.lower()
            order.append(name)
        else:
            errors.append(f"Unknown protocol status: {status}")
    if not begun:
        errors.append("Guest did not begin")
    if not done:
        errors.append("Guest did not complete")
    if order != list(CASES):
        errors.append("Guest test sequence is missing, duplicated, or out of order")
    if timed_out:
        errors.append("Guest execution timed out")
    if returncode != 0:
        errors.append(f"QEMU exit code: {returncode}")
    cases = [{"name": name, "status": observed.get(name, "missing")} for name in CASES]
    passed = not errors and all(case["status"] == "pass" for case in cases)
    return {"passed": passed, "completed": done, "cases": cases,
            "errors": errors, "passed_count": sum(x["status"] == "pass" for x in cases),
            "case_count": len(CASES)}


def build_guests(destination: Path | None = None, *, tool_prefix: str = "aarch64-linux-gnu-") -> dict:
    """Rebuild both guests using GNU binutils; no network or package installation."""
    destination = Path(destination or GUESTS).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    commands = []
    for target in ("virt", "vmapple"):
        obj, elf = destination / f"{target}.o", destination / f"{target}.elf"
        commands.extend([
            [tool_prefix + "as", "--defsym", f"VMAPPLE={int(target == 'vmapple')}",
             "-o", str(obj), str(GUESTS / "conformance.S")],
            [tool_prefix + "ld", "-T", str(GUESTS / f"{target}.ld"), "-o", str(elf), str(obj)],
        ])
        if target == "vmapple":
            commands.append([tool_prefix + "objcopy", "-O", "binary", str(elf),
                             str(destination / "vmapple.bin")])
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    version = subprocess.run([tool_prefix + "as", "--version"], check=True,
                             capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
    manifest = {"schema": 1, "producer": "self-authored 26x86 conformance guest",
                "assembler": version,
                "sources": {name: sha256(GUESTS / name) for name in
                            ("conformance.S", "virt.ld", "vmapple.ld")},
                "artifacts": {name: sha256(destination / name) for name in
                              ("virt.elf", "vmapple.elf", "vmapple.bin")}}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Object files are intermediate compiler output, not executable deliverables.
    for target in ("virt", "vmapple"):
        (destination / f"{target}.o").unlink()
    return manifest


def verify_guest(target: str) -> Path:
    if target not in ("virt", "vmapple"):
        raise ValueError("target must be virt or vmapple")
    with read_regular(GUESTS / "manifest.json") as stream:
        manifest_bytes = stream.read(65537)
    if len(manifest_bytes) > 65536:
        raise ValueError("Guest manifest exceeds size bound")
    manifest = json.loads(manifest_bytes)
    for name in ("conformance.S", "virt.ld", "vmapple.ld"):
        if manifest.get("sources", {}).get(name) != sha256(GUESTS / name):
            raise ValueError(f"Guest source changed without rebuilding: {name}")
    name = "virt.elf" if target == "virt" else "vmapple.bin"
    path = GUESTS / name
    if manifest.get("artifacts", {}).get(name) != sha256(path):
        raise ValueError(f"Bundled guest hash mismatch: {name}")
    return path


def _command_prefix(qemu: str | os.PathLike | Sequence[str]) -> list[str]:
    if isinstance(qemu, (str, os.PathLike)):
        return [os.fspath(qemu)]
    if not qemu:
        raise ValueError("QEMU command must not be empty")
    return list(qemu)


def run_conformance(qemu: str | os.PathLike | Sequence[str], output_dir: Path,
                    timeout: float = 20, target: str = "virt") -> dict:
    """Run TCG with bounded time and serialize the actual stdout/stderr evidence.

    Invoke Python in the same OS namespace as QEMU (e.g. inside WSL for Linux
    QEMU). A sequence can prefix a launcher when it shares those file paths.
    """
    if not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError("timeout must be finite and between 0 and 300 seconds")
    guest = verify_guest(target)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    prefix = _command_prefix(qemu)
    result = {"schema": 1, "target": target, "acceleration": "tcg",
              "layer": "emulated AArch64 CPU and EL1 MMU",
              "guest_sha256": sha256(guest), "guest_path": str(guest),
              "limitations": LIMITATIONS, "macos_boot_verified": False}
    stdout, stderr, returncode, timed_out = "", "", None, False
    started = time.monotonic()
    attempts = []
    try:
        version_result = subprocess.run(prefix + ["--version"], capture_output=True,
                                        text=True, timeout=min(timeout, 10))
        result["qemu_version"] = version_result.stdout.splitlines()[0] if version_result.stdout else "unknown"
        # Newer QEMU defaults to an implementation-defined non-cryptographic PAC.
        # Explicitly select QARMA5; old releases lack this property and are retried
        # with impdef disabled. The guest additionally requires ID_ISAR1.APA > 0.
        cpu = "max,pauth-qarma5=on"
        base = ["-accel", "tcg", "-m", "128M", "-smp", "1", "-display", "none",
                "-monitor", "none", "-serial", "stdio", "-net", "none",
                "-semihosting-config", "enable=on,target=native"]
        if target == "virt":
            machine = ["-M", "virt,virtualization=off,secure=off,gic-version=3", "-kernel", str(guest)]
        else:
            # These are blank synthetic devices required by the model, never Apple
            # restore assets. QEMU receives them read-only.
            aux = output_dir / "synthetic-aux.bin"
            root = output_dir / "synthetic-root.bin"
            aux.write_bytes(bytes(1024 * 1024))
            root.write_bytes(bytes(1024 * 1024))
            machine = ["-M", "vmapple,research-headless=on", "-bios", str(guest),
                       "-drive", "if=pflash,unit=0,format=raw,readonly=on,file=" + str(aux).replace(",", ",,"),
                       "-drive", "if=pflash,unit=1,format=raw,readonly=on,file=" + str(root).replace(",", ",,")]
        for attempt in range(2):
            command = prefix + base + ["-cpu", cpu] + machine
            result["command"] = command
            result["cpu"] = cpu
            try:
                proc = subprocess.run(command, capture_output=True, text=True,
                                      encoding="utf-8", errors="replace", timeout=timeout)
                stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as exc:
                def decode(value):
                    return value.decode("utf-8", "replace") if isinstance(value, bytes) else value or ""
                stdout, stderr = decode(exc.stdout), decode(exc.stderr)
                timed_out = True
                break
            attempts.append({"cpu": cpu, "returncode": returncode, "stderr": stderr})
            if (attempt == 0 and returncode != 0 and not stdout and
                    "pauth-qarma5" in stderr and "not found" in stderr):
                cpu = "max,pauth-impdef=off"
                continue
            break
    except (OSError, subprocess.SubprocessError) as exc:
        stderr = f"{type(exc).__name__}: {exc}"
    result.update(parse_serial(stdout, returncode=returncode, timed_out=timed_out))
    result.update({"duration_seconds": round(time.monotonic() - started, 6),
                   "returncode": returncode, "timed_out": timed_out, "attempts": attempts})
    (output_dir / "serial.log").write_text(stdout, encoding="utf-8")
    (output_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    result["serial_log"] = str(output_dir / "serial.log")
    result["stderr_log"] = str(output_dir / "stderr.log")
    (output_dir / "report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
