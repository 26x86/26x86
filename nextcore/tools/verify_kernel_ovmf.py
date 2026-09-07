#!/usr/bin/env python3
"""Observe BOOTX64 -> NXKERNEL -> an authored pstart32 probe in QEMU/OVMF.

This harness deliberately uses q35, SMM off, one CPU, no watchdog device, no
monitor/QMP, and no NMI injection. It does not establish safe NMI/interrupt
transitions on physical machines. A probe success is not XNU/macOS execution.
Use a fresh Linux-owned output directory (for example /tmp) when running in WSL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import time

from build_pstart32_probe import MARKER, build_probe, sha256

CHAIN = ["NEXTCORE: EFI_ENTRY", "NEXTCORE: CONFIG_PARSED", "NEXTCORE: IMAGE_START", "NXKERNEL: EFI_ENTRY"]
PLACED = "NXKERNEL: IMAGE_PLACED base=*"
EBS = "NXKERNEL: EXIT_BOOT_SERVICES"
PROBE_PREFIX = [PLACED, "NXKERNEL: PROBE_ONLY", "NXKERNEL: HANDOFF_READY map_bytes=*", EBS]
PROBE_CHECKS = [
    "NXPROBE: ENTRY", "NXPROBE: CPU_STATE_OK", "NXPROBE: BOOT_ARGS_OK",
    "NXPROBE: MEMORY_MAP_OK", "NXPROBE: DEVICE_TREE_OK", "NXPROBE: DATA_OK",
    "NXPROBE: BSS_OK", "NXPROBE: PSTART32_OK",
]


def matches(line: str, marker: str) -> bool:
    return line.startswith(marker[:-1]) if marker.endswith("*") else line == marker


def log_lines(serial: Path) -> list[str]:
    log = serial.read_text(encoding="utf-8", errors="replace") if serial.exists() else ""
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log).splitlines()


def ordered(lines: list[str], required: list[str]) -> bool:
    after = 0
    for marker in required:
        found = next((i for i in range(after, len(lines)) if matches(lines[i], marker)), None)
        if found is None:
            return False
        after = found + 1
    return True


def config(profile: str = "xnu-12377-pstart32") -> bytes:
    return plistlib.dumps({
        "Misc": {"Entries": [{"Enabled": True, "Path": "\\EFI\\NEXTCORE\\NXKERNEL.EFI", "Arguments": ""}]},
        "Nextcore": {"Kernel": {"Profile": profile, "Path": "\\EFI\\NEXTCORE\\probe.macho", "Arguments": "-v"}},
    }, fmt=plistlib.FMT_XML)


def definitions(image: bytes) -> list[dict]:
    fileset = bytearray(image)
    struct.pack_into("<I", fileset, 12, 0xC)
    main = bytearray(image)
    struct.pack_into("<I", main, 20, 72 * 2 + 24)
    main[176:200] = struct.pack("<IIQQ", 0x80000028, 24, 0x1000, 0)
    damaged = bytearray(image)
    damaged[0x2800] ^= 0x80
    unmarked = bytearray(image)
    unmarked[unmarked.index(MARKER)] ^= 1

    def rejected(name: str, payload: bytes, marker: str, status: str, profile: str = "xnu-12377-pstart32", placed: bool = False) -> dict:
        return {
            "name": name, "image": payload, "profile": profile, "kernel": "probe",
            "expected": ([PLACED] if placed else []) + [marker, f"NXKERNEL: ERROR status={status}", f"NEXTCORE: IMAGE_RETURN status={status}"],
            "forbidden": [EBS, "NXPROBE: *"] + ([] if placed else [PLACED]),
            "exit_code": None,
        }

    return [
        {"name": "probe-positive", "image": image, "kernel": "probe", "expected": PROBE_PREFIX + PROBE_CHECKS,
         "forbidden": ["NXPROBE: FAIL_*", "NXKERNEL: ERROR*", "NEXTCORE: IMAGE_RETURN*"], "exit_code": 33},
        {"name": "production-gate", "image": image, "kernel": "default",
         "expected": [PLACED, "NXKERNEL: PROVIDERS_PENDING", "NXKERNEL: ERROR status=NOT_READY", "NEXTCORE: IMAGE_RETURN status=NOT_READY"],
         "forbidden": [EBS, "NXKERNEL: PROBE_ONLY", "NXPROBE: *"], "exit_code": None},
        rejected("truncated-image", image[:31], "NXKERNEL: MACHO_INVALID reason=MACHO_TRUNCATED", "LOAD_ERROR"),
        rejected("unsupported-fileset", bytes(fileset), "NXKERNEL: MACHO_INVALID reason=MACHO_UNSUPPORTED_FILETYPE", "LOAD_ERROR"),
        rejected("unsupported-profile", image, "NXKERNEL: CONFIG_INVALID reason=UNSUPPORTED_KERNEL_PROFILE", "INVALID_PARAMETER", "unsupported-profile"),
        rejected("main-entry-rejected", bytes(main), "NXKERNEL: PROFILE_UNSUPPORTED reason=ENTRY_KIND", "UNSUPPORTED"),
        # Marker detection is an explicit fixture guard, not authentication.
        {"name": "unmarked-image-rejected", "image": bytes(unmarked), "kernel": "probe",
         "expected": [PLACED, "NXKERNEL: ERROR status=UNSUPPORTED", "NEXTCORE: IMAGE_RETURN status=UNSUPPORTED"],
         "forbidden": [EBS, "NXKERNEL: PROBE_ONLY", "NXPROBE: *"], "exit_code": None},
        # Loader readback succeeds for this altered source, while the independent
        # guest check must detect that its expected initialized DATA was changed.
        {"name": "guest-detects-data-corruption", "image": bytes(damaged), "kernel": "probe",
         "expected": PROBE_PREFIX + PROBE_CHECKS[:5] + ["NXPROBE: FAIL_DATA"],
         "forbidden": ["NXPROBE: DATA_OK", "NXPROBE: BSS_OK", "NXPROBE: PSTART32_OK"], "exit_code": 35},
    ]


def run_case(args, output: Path, case: dict) -> dict:
    directory = output / case["name"]
    boot = directory / "esp/EFI/BOOT"
    boot.mkdir(parents=True)
    kernel = directory / "esp/EFI/NEXTCORE"
    kernel.mkdir()
    oc = directory / "esp/EFI/OC"
    oc.mkdir()
    shutil.copyfile(args.efi, boot / "BOOTX64.EFI")
    shutil.copyfile(args.kernel_probe if case["kernel"] == "probe" else args.kernel_default, kernel / "NXKERNEL.EFI")
    (kernel / "probe.macho").write_bytes(case["image"])
    (oc / "config.plist").write_bytes(config(case.get("profile", "xnu-12377-pstart32")))
    variables, serial = directory / "vars.fd", directory / "serial.log"
    shutil.copyfile(args.ovmf_vars, variables)
    command = [
        args.qemu, "-machine", "q35,accel=tcg,smm=off", "-cpu", "Nehalem", "-m", "256", "-smp", "1",
        "-display", "none", "-monitor", "none", "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
        "-device", "isa-debug-exit,iobase=0xf4,iosize=0x04",
        "-drive", f"if=pflash,format=raw,readonly=on,file={args.ovmf_code}",
        "-drive", f"if=pflash,format=raw,file={variables}",
        "-drive", f"format=raw,file=fat:rw:{directory / 'esp'}",
    ]
    (directory / "command.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    started = time.monotonic()
    stopped = False
    poll_errors = []
    required = CHAIN + case["expected"]
    with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        try:
            while process.poll() is None and time.monotonic() - started < args.timeout:
                try:
                    lines = log_lines(serial)
                except OSError as error:
                    poll_errors.append(str(error))
                    lines = []
                # Natural debug-exit is mandatory for the post-EBS cases. Merely
                # printing the success marker cannot satisfy that requirement.
                if case["exit_code"] is None and ordered(lines, required):
                    break
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                stopped = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            else:
                process.wait()
    lines = log_lines(serial)
    expected_exit = case["exit_code"]
    marker_order = ordered(lines, required)
    forbidden = [marker for marker in case["forbidden"] if any(matches(line, marker) for line in lines)]
    unexpected_probe_failures = [line for line in lines if line.startswith("NXPROBE: FAIL_") and line not in required]
    exit_ok = expected_exit is None or (not stopped and process.returncode == expected_exit)
    success = marker_order and not forbidden and not unexpected_probe_failures and exit_ok and process.poll() is not None
    return {
        "name": case["name"], "passed": success, "markers_expected": required,
        "ordered_markers_observed": marker_order, "forbidden_markers_observed": forbidden,
        "unexpected_probe_failures": unexpected_probe_failures,
        "guest_markers": [line for line in lines if line.startswith("NXPROBE:")],
        "kernel_markers": [line for line in lines if line.startswith("NXKERNEL:")],
        "exit_boot_services_attempted": EBS in lines,
        "post_ebs_guest_observed": "NXPROBE: ENTRY" in lines,
        "authored_probe_verified": "NXPROBE: PSTART32_OK" in lines and process.returncode == 33 and not stopped,
        "qemu_pid": process.pid, "qemu_exit_code": process.returncode, "expected_exit_code": expected_exit,
        "process_terminated": process.poll() is not None, "stopped_by_harness": stopped,
        "elapsed_seconds": round(time.monotonic() - started, 3), "serial_log": str(serial),
        "poll_observation_errors": poll_errors, "fixture_sha256": hashlib.sha256(case["image"]).hexdigest(),
        "xnu_executed": False, "macos_boot_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True, help="BOOTX64.efi")
    parser.add_argument("--kernel-probe", type=Path, required=True, help="NXKERNEL built with kernel-probe")
    parser.add_argument("--kernel-default", type=Path, required=True, help="NXKERNEL default production build")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--assembler", default="as")
    parser.add_argument("--linker", default="ld")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--cases", help="Optional comma-separated subset; report records selected cases")
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error("--timeout must be in (0, 60] seconds per case")
    args.qemu = shutil.which(args.qemu) or args.qemu
    fields = ("efi", "kernel_probe", "kernel_default", "ovmf_code", "ovmf_vars")
    for field in fields:
        path = getattr(args, field).resolve(strict=True)
        if not path.is_file() or "," in str(path):
            parser.error(f"{field} must be a regular file without a comma in its path")
        setattr(args, field, path)
    output = args.output.resolve()
    if "," in str(output):
        parser.error("output path cannot contain a comma")
    paths = [getattr(args, field) for field in fields] + [Path(__file__).resolve(), Path(__file__).with_name("pstart32_probe.S").resolve(), Path(__file__).with_name("build_pstart32_probe.py").resolve()]
    before = {str(path): sha256(path) for path in paths}
    version = subprocess.run([args.qemu, "--version"], check=True, capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
    output.mkdir(parents=True, exist_ok=False)
    cases, failure = [], None
    try:
        fixture = build_probe(output / "fixture", args.assembler, args.linker)
        specs = definitions(Path(fixture["image"]).read_bytes())
        if args.cases:
            selected = args.cases.split(",")
            if len(set(selected)) != len(selected) or not set(selected) <= {case["name"] for case in specs}:
                raise ValueError("--cases contains duplicate or unknown case names")
            specs = [case for case in specs if case["name"] in selected]
        for case in specs:
            result = run_case(args, output, case)
            cases.append(result)
            print(json.dumps(result), flush=True)
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    after = {str(path): sha256(path) for path in paths}
    report = {
        "schema": "nextcore.ovmf-kernel-probe.v1",
        "layer": "UEFI Mach-O placement / authored protected-mode probe / independent handoff validation",
        "qemu_version": version, "input_sha256_before": before, "input_sha256_after": after,
        "original_inputs_preserved": before == after, "cases": cases, "failure": failure,
        "selected_cases": args.cases.split(",") if args.cases else "all",
        "passed": bool(cases) and all(case["passed"] for case in cases) and before == after and failure is None,
        "authored_probe_verified": any(case["name"] == "probe-positive" and case["passed"] for case in cases),
        "nmi_scope": "Controlled QEMU q35 only: SMM off, no watchdog device, no monitor/QMP or NMI injection. Physical-machine NMI safety is unverified.",
        "xnu_executed": False, "macos_boot_verified": False, "metal_verified": False,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output / "report.json"), "passed": report["passed"], "failure": failure}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
