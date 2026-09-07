#!/usr/bin/env python3
"""Run the actual Nextcore UEFI image; report firmware I/O, never macOS boot."""
from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
from pathlib import Path
import re
import shutil
import subprocess
import struct
import time


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(args, output: Path, name: str, payload: bytes | None, expected: list[str], child: bool | str = False) -> dict:
    directory = output / name
    boot = directory / "esp/EFI/BOOT"
    boot.mkdir(parents=True)
    shutil.copyfile(args.efi, boot / "BOOTX64.EFI")
    if child:
        child_image = bytearray(args.child.read_bytes())
        if child == "driver":
            # Mutate only a copy of our authored fixture to EFI boot driver.
            optional_header = struct.unpack_from("<I", child_image, 0x3C)[0] + 24
            struct.pack_into("<H", child_image, optional_header + 68, 11)
        (boot / "NXTEST.EFI").write_bytes(child_image)
    if payload is not None:
        config = directory / "esp/EFI/OC/config.plist"
        config.parent.mkdir()
        config.write_bytes(payload)
    variables = directory / "vars.fd"
    shutil.copyfile(args.ovmf_vars, variables)
    serial = directory / "serial.log"
    command = [
        args.qemu, "-machine", "q35,accel=tcg", "-cpu", "Nehalem", "-m", "256",
        "-smp", "1", "-display", "none", "-monitor", "none",
        "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
        "-drive", f"if=pflash,format=raw,readonly=on,file={args.ovmf_code}",
        "-drive", f"if=pflash,format=raw,file={variables}",
        "-drive", f"format=raw,file=fat:rw:{directory / 'esp'}",
    ]
    (directory / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    started = time.monotonic()
    stopped_by_harness = False
    log = ""
    with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        try:
            while process.poll() is None and time.monotonic() - started < args.timeout:
                log = serial.read_text(errors="replace") if serial.exists() else ""
                if expected[-1] in log:
                    break
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                stopped_by_harness = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    log = serial.read_text(errors="replace") if serial.exists() else ""
    # Only application-generated, line-delimited markers count. Firmware text
    # and the subprocess exit code alone are not EFI or guest-boot evidence.
    lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log).splitlines()
    entry = "NEXTCORE: EFI_ENTRY" in lines
    end = expected[-1] in lines
    loaded = any(line.startswith("NEXTCORE: CONFIG_READ bytes=") for line in lines)
    expected_read = payload is not None and 0 < len(payload) <= 1024 * 1024
    correct_length = not expected_read or f"NEXTCORE: CONFIG_READ bytes={len(payload)}" in lines
    required = ["NEXTCORE: EFI_ENTRY"] + expected
    positions = [lines.index(marker) if marker in lines else -1 for marker in required]
    ordered = all(index >= 0 for index in positions) and positions == sorted(set(positions))
    child_observed = "NXTEST: EFI_ENTRY" in lines
    child_expected = any(marker.startswith("NXTEST:") for marker in expected)
    return {
        "name": name,
        "passed": bool(ordered and loaded == expected_read and correct_length and child_observed == child_expected),
        "efi_entry_observed": entry,
        "config_read_observed": loaded,
        "terminal_observed": end,
        "markers_expected": expected,
        "child_entry_observed": child_observed,
        "child_options_verified": any(marker in lines for marker in ("NXTEST: OPTIONS_OK", "NXTEST: OPTIONS_EMPTY", "NXTEST: OPTIONS_UTF16")),
        "process_terminated": process.poll() is not None,
        "qemu_exit_code": process.returncode,
        "stopped_by_harness": stopped_by_harness,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "serial_log": str(serial),
        "macos_boot_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--child", type=Path, help="Authored NXTEST.EFI enables actual child execution cases")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error("--timeout must be greater than zero and at most 60 seconds per case")
    args.qemu = shutil.which(args.qemu) or args.qemu
    fields = ["efi", "config", "ovmf_code", "ovmf_vars"] + (["child"] if args.child else [])
    for field in fields:
        path = getattr(args, field).resolve(strict=True)
        if not path.is_file() or "," in str(path):
            parser.error(f"{field} must be a regular file with no comma in its path")
        setattr(args, field, path)
    if args.efi.read_bytes()[:2] != b"MZ":
        parser.error("EFI input is not a PE executable (build it for x86_64-unknown-uefi)")
    config = args.config.read_bytes()
    if not 0 < len(config) <= 1024 * 1024:
        parser.error("reference config must have 1..1048576 bytes")
    # The reference config intentionally has no enabled boot target.
    reference = plistlib.loads(config)
    if any(entry.get("Enabled", False) for entry in reference.get("Misc", {}).get("Entries", [])):
        parser.error("reference config must not have an enabled Misc.Entries item")
    output = args.output.resolve()
    if "," in str(output):
        parser.error("output path must not contain a comma")
    before = {str(getattr(args, field)): sha256(getattr(args, field)) for field in fields}
    version = subprocess.run([args.qemu, "--version"], check=True, capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    def target(path: str, arguments: str = "") -> bytes:
        return plistlib.dumps({"Misc": {"Entries": [{"Enabled": True, "Path": path, "Arguments": arguments}]}}, fmt=plistlib.FMT_XML)

    definitions = [
        ("config-present", config, ["NEXTCORE: NO_BOOT_TARGET"], False),
        ("config-missing", None, ["NEXTCORE: CONFIG_ERROR status=NOT_FOUND"], False),
        ("config-empty", b"", ["NEXTCORE: CONFIG_ERROR status=BAD_BUFFER_SIZE"], False),
        ("config-oversized", b"x" * (1024 * 1024 + 1), ["NEXTCORE: CONFIG_ERROR status=BAD_BUFFER_SIZE"], False),
        ("config-malformed", b"<plist><dict>", ["NEXTCORE: CONFIG_INVALID reason=INVALID_XML"], False),
        ("target-missing", target("\\EFI\\BOOT\\MISSING.EFI"), ["NEXTCORE: CONFIG_PARSED", "NEXTCORE: IMAGE_LOAD_ERROR status=NOT_FOUND"], False),
        ("target-self", target("/efi/boot/bootx64.efi"), ["NEXTCORE: CONFIG_PARSED", "NEXTCORE: TARGET_REJECTED reason=SELF_REFERENCE", "NEXTCORE: IMAGE_LOAD_ERROR status=INVALID_PARAMETER"], False),
    ]
    if args.child:
        for name, options, marker, status in [
            ("child-success", "nextcore-child-success 한글", "OPTIONS_OK", "SUCCESS"),
            ("child-error", "nextcore-child-error", "OPTIONS_OK", "ABORTED"),
            ("child-empty-options", "", "OPTIONS_EMPTY", "SUCCESS"),
            ("child-utf16-options", "nextcore-child-utf16 🚀", "OPTIONS_UTF16", "SUCCESS"),
        ]:
            definitions.append((name, target("\\EFI\\BOOT\\NXTEST.EFI", options), ["NEXTCORE: CONFIG_PARSED", "NEXTCORE: IMAGE_START", "NXTEST: EFI_ENTRY", f"NXTEST: {marker}", f"NEXTCORE: IMAGE_RETURN status={status}"], True))
        definitions.append(("driver-rejected", target("\\EFI\\BOOT\\NXTEST.EFI", "nextcore-child-success 한글"), ["NEXTCORE: CONFIG_PARSED", "NEXTCORE: TARGET_REJECTED reason=NOT_APPLICATION", "NEXTCORE: IMAGE_OPTIONS_ERROR status=UNSUPPORTED"], "driver"))
    for name, payload, expected, child in definitions:
        case = run_case(args, output, name, payload, expected, child)
        cases.append(case)
        print(json.dumps(case), flush=True)
    after = {path: sha256(Path(path)) for path in before}
    report = {
        "schema": "nextcore.ovmf-chainload.v2",
        "layer": "x86_64 UEFI configuration / LoadImage / StartImage / LoadOptions",
        "qemu_version": version,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "original_inputs_preserved": before == after,
        "cases": cases,
        "passed": all(case["passed"] for case in cases) and before == after,
        "plist_parse_verified": all(case["passed"] for case in cases if case["name"] in ("config-present", "config-malformed", "target-missing", "target-self")),
        "child_handoff_verified": bool(args.child) and all(case["passed"] for case in cases if case["name"].startswith("child-")),
        "xnu_executed": False,
        "macos_boot_verified": False,
        "metal_verified": False,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
