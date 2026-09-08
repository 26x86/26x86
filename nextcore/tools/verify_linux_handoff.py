#!/usr/bin/env python3
"""Hand off from OUR BOOTX64 loader to a real Ubuntu vmlinuz EFI stub in OVMF.

Reuses the established harness patterns (OVMF code/vars copies, serial log
polling, command.json, report.json with pre/post input hashes). The foreign
kernel is a public Ubuntu archive image, booted via the existing generic
LoadImage->StartImage path with a serial-console command line. Success is the
foreign kernel's own "Linux version ..." banner on the same serial log after
our NEXTCORE: IMAGE_START marker. This is a Linux handoff observation, not an
XNU/macOS boot claim.

Use a fresh Linux-owned output directory (for example /tmp or the mounted
nextcore/artifacts path) when running in WSL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import re
import shutil
import struct
import subprocess
import time
from pathlib import Path

REQUIRED_ORDER = [
    "NEXTCORE: EFI_ENTRY",
    "NEXTCORE: CONFIG_PARSED",
    "NEXTCORE: IMAGE_START",
]

DEFAULT_CMDLINE = (
    "console=ttyS0,115200 earlycon=uart,io,0x3f8 efi=debug "
    "root=/dev/ram0 ro nokaslr loglevel=7"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_vmlinuz_stub(data: bytes) -> dict:
    """Light validation that the foreign image is a PE32+ EFI application."""
    if data[:2] != b"MZ":
        raise ValueError("vmlinuz input is not MZ-terminated (not an EFI stub image)")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
        raise ValueError("vmlinuz PE signature missing")
    opt_magic = struct.unpack_from("<H", data, e_lfanew + 4 + 20)[0]
    if opt_magic != 0x20B:
        raise ValueError(f"vmlinuz is not PE32+ (opt magic {opt_magic:#x})")
    subsystem = struct.unpack_from("<H", data, e_lfanew + 4 + 20 + 68)[0]
    if subsystem != 10:
        raise ValueError(f"vmlinuz subsystem is {subsystem}, not EFI application (10)")
    return {"pe_offset": e_lfanew, "opt_magic": opt_magic, "subsystem": subsystem}


def log_lines(serial: Path) -> list[str]:
    log = serial.read_text(encoding="utf-8", errors="replace") if serial.exists() else ""
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log).splitlines()


def ordered(lines: list[str], required: list[str]) -> bool:
    after = 0
    for marker in required:
        found = next((i for i in range(after, len(lines)) if lines[i] == marker), None)
        if found is None:
            return False
        after = found + 1
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True, help="OUR BOOTX64.efi")
    parser.add_argument("--vmlinuz", type=Path, required=True, help="Ubuntu vmlinuz EFI stub image")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", required=True, help="Exact official Ubuntu archive URL fetched")
    parser.add_argument("--version", required=True, help="Kernel version string")
    parser.add_argument("--cmdline", default=DEFAULT_CMDLINE)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--mem", default="1024", help="Guest RAM in MB")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if not 0 < args.timeout <= 300:
        parser.error("--timeout must be in (0, 300] seconds")
    args.qemu = shutil.which(args.qemu) or args.qemu
    for field in ("efi", "vmlinuz", "ovmf_code", "ovmf_vars"):
        path = getattr(args, field).resolve(strict=True)
        if not path.is_file() or "," in str(path):
            parser.error(f"{field} must be a regular file without a comma in its path")
        setattr(args, field, path)
    output = args.output.resolve()
    if "," in str(output):
        parser.error("output path cannot contain a comma")
    if args.efi.read_bytes()[:2] != b"MZ":
        parser.error("EFI input is not a PE executable (build it for x86_64-unknown-uefi)")
    vmlinuz_bytes = args.vmlinuz.read_bytes()
    try:
        stub = check_vmlinuz_stub(vmlinuz_bytes)
    except ValueError as error:
        parser.error(str(error))
    if not args.cmdline or "console=ttyS0" not in args.cmdline:
        parser.error("cmdline must be non-empty and direct the kernel to ttyS0")
    if len(args.cmdline.encode("utf-16-le")) // 2 > 4096:
        parser.error("cmdline exceeds the loader's 4096 UTF-16-unit bound")

    before = {str(path): sha256(path) for path in (args.efi, args.vmlinuz, args.ovmf_code, args.ovmf_vars)}
    version = subprocess.run(
        [args.qemu, "--version"], check=True, capture_output=True, text=True, timeout=10
    ).stdout.splitlines()[0]
    output.mkdir(parents=True, exist_ok=False)

    esp = output / "esp"
    boot = esp / "EFI/BOOT"
    boot.mkdir(parents=True)
    ubuntu = esp / "EFI/UBUNTU"
    ubuntu.mkdir()
    oc = esp / "EFI/OC"
    oc.mkdir()
    shutil.copyfile(args.efi, boot / "BOOTX64.EFI")
    shutil.copyfile(args.vmlinuz, ubuntu / "VMLINUZ.EFI")
    config = plistlib.dumps(
        {"Misc": {"Entries": [{"Enabled": True, "Path": "\\EFI\\UBUNTU\\VMLINUZ.EFI", "Arguments": args.cmdline}]}},
        fmt=plistlib.FMT_XML,
    )
    (oc / "config.plist").write_bytes(config)

    variables = output / "vars.fd"
    shutil.copyfile(args.ovmf_vars, variables)
    serial = output / "serial.log"
    command = [
        args.qemu, "-machine", "q35,accel=tcg", "-cpu", "Nehalem", "-m", args.mem,
        "-smp", "1", "-display", "none", "-monitor", "none",
        "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
        "-drive", f"if=pflash,format=raw,readonly=on,file={args.ovmf_code}",
        "-drive", f"if=pflash,format=raw,file={variables}",
        "-drive", f"format=raw,file=fat:rw:{esp}",
    ]
    (output / "command.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    (output / "config.plist").write_bytes(config)

    started = time.monotonic()
    stopped_by_harness = True
    banner_lines: list[str] = []
    cmdline_echo = ""
    poll_observation_errors: list[str] = []

    def poll_lines() -> list[str]:
        try:
            return log_lines(serial)
        except OSError as error:
            # Same host-observation race the kernel-probe harness guards:
            # reading the QEMU serial file while it is being appended can
            # raise ENODATA on some filesystems. This is not guest evidence.
            poll_observation_errors.append(f"{type(error).__name__}: {error}")
            return []

    with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        try:
            banner_at: float | None = None
            while process.poll() is None and time.monotonic() - started < args.timeout:
                lines = poll_lines()
                hits = [line for line in lines if "Linux version" in line]
                if hits and banner_at is None:
                    banner_at = time.monotonic()
                    banner_lines = hits
                if banner_at is not None and time.monotonic() - banner_at > 5:
                    break
                time.sleep(0.2)
            lines = poll_lines()
            banner_lines = [line for line in lines if "Linux version" in line]
            cmdline_echo = next((line for line in lines if "Command line:" in line), "")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            else:
                stopped_by_harness = False
                process.wait()
    elapsed = round(time.monotonic() - started, 3)
    # The guest is gone here, but the 9P/serial file can still race once.
    # Retry the final readback briefly instead of failing the receipt.
    lines: list[str] = []
    for _ in range(50):
        try:
            lines = log_lines(serial)
            break
        except OSError as error:
            poll_observation_errors.append(f"{type(error).__name__}: {error}")
            time.sleep(0.1)
    if not lines and serial.exists():
        lines = poll_lines()
    banner_final = [line for line in lines if "Linux version" in line]
    if banner_final:
        banner_lines = banner_final
        if not cmdline_echo:
            cmdline_echo = next((line for line in lines if "Command line:" in line), "")
    chain_ok = ordered(lines, REQUIRED_ORDER)
    banner_ok = len(banner_lines) > 0
    # The foreign banner must come after OUR handoff marker, not before it.
    banner_after_handoff = False
    if banner_ok and "NEXTCORE: IMAGE_START" in lines:
        start_idx = lines.index("NEXTCORE: IMAGE_START")
        banner_after_handoff = any(
            i > start_idx for i, line in enumerate(lines) if "Linux version" in line
        )
    no_return_expected = "NEXTCORE: IMAGE_RETURN" not in lines
    passed = bool(chain_ok and banner_ok and banner_after_handoff and no_return_expected)
    outcome = "passed" if passed else "failed"
    after = {str(path): sha256(path) for path in (args.efi, args.vmlinuz, args.ovmf_code, args.ovmf_vars)}
    efi_sha = sha256(args.efi)
    vmlinuz_sha = sha256(args.vmlinuz)
    report = {
        "schema": "nextcore.linux-handoff.v1",
        "layer": "OUR UEFI loader -> foreign Linux EFI stub via LoadImage/StartImage",
        "inputs": {
            "name": f"Ubuntu vmlinuz {args.version} (EFI stub)",
            "url": args.url,
            "version": args.version,
            "sha256": vmlinuz_sha,
            "image_bytes": len(vmlinuz_bytes),
            "pe_subsystem": stub["subsystem"],
            "kernel_cmdline": args.cmdline,
        },
        "qemu_cmdline": command,
        "qemu_version": version,
        "efi_binary_sha256": efi_sha,
        "serial_log_path": str(serial),
        "outcome": outcome,
        "passed": passed,
        "duration_s": elapsed,
        "linux_banner_lines": banner_lines,
        "linux_command_line": cmdline_echo,
        "chain_markers_ordered": chain_ok,
        "banner_after_image_start": banner_after_handoff,
        "image_return_absent": no_return_expected,
        "qemu_exit_code": process.returncode,
        "process_terminated": process.poll() is not None,
        "stopped_by_harness": stopped_by_harness,
        "guest_memory_mb": args.mem,
        "poll_observation_errors": poll_observation_errors,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "original_inputs_preserved": before == after,
        "xnu_executed": False,
        "macos_boot_verified": False,
        "metal_verified": False,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return 0 if passed and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
