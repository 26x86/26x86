#!/usr/bin/env python3
"""Run the authored NXMMU image on an x86 OVMF computer with TCG.

Arm execution is supplied by the EFI image's native x86 JIT and Rust provider.
This tool starts no ARM emulator and accepts no original OS input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markers(path):
    if not path.exists():
        return []
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", path.read_text(errors="replace"))
    return [line for line in text.splitlines() if line.startswith("NXMMU:")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi-probe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error("timeout must be in (0,60]")
    paths = [args.efi_probe.resolve(strict=True), args.ovmf_code.resolve(strict=True), args.ovmf_vars.resolve(strict=True)]
    output = args.output.resolve()
    if any("," in str(p) for p in [*paths, output]) or not all(p.is_file() for p in paths):
        parser.error("inputs must be files and QEMU paths must not contain a comma")
    output.mkdir(parents=True, exist_ok=False)
    before = {p.name: sha(p) for p in paths}
    boot = output / "esp/EFI/BOOT"
    boot.mkdir(parents=True)
    shutil.copyfile(paths[0], boot / "BOOTX64.EFI")
    variables = output / "vars.fd"
    shutil.copyfile(paths[2], variables)
    serial = output / "serial.log"
    command = [args.qemu, "-machine", "q35,accel=tcg,smm=off", "-cpu", "Nehalem", "-m", "256", "-smp", "1",
               "-display", "none", "-vga", "std", "-monitor", "none", "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
               "-drive", f"if=pflash,format=raw,readonly=on,file={paths[1]}",
               "-drive", f"if=pflash,format=raw,file={variables}",
               "-drive", f"format=raw,file=fat:rw:{output / 'esp'}"]
    (output / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    start = time.monotonic()
    with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        try:
            while process.poll() is None and time.monotonic() - start < args.timeout:
                if any(line.startswith(("NXMMU: PASS", "NXMMU: FAIL")) for line in markers(serial)):
                    break
                time.sleep(.1)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    actual = markers(serial)
    cases = []
    previous = None
    transport_duplicates = 0
    for line in actual:
        # report() writes ConsoleOut and Serial; OVMF can mirror ConsoleOut to
        # the same serial port. Collapse only identical adjacent transport lines.
        # Nonadjacent repeats or conflicting fields still fail identity checks.
        if line == previous:
            transport_duplicates += 1
            continue
        previous = line
        if line.startswith("NXMMU: CASE "):
            fields = dict(token.split("=", 1) for token in line.split()[2:])
            cases.append(fields)
    identities = [(c["name"], c["granule"], c["upper"]) for c in cases]
    names = ["strb", "ldrb", "ldrsb-w", "ldrsb-x", "strh", "ldrh", "ldrsh-w", "ldrsh-x",
             "str-w", "ldr-w", "ldrsw", "str-x", "ldr-x", "pair-offset", "pair-pre", "pair-post",
             "pair-store-translation", "pair-load-translation", "pair-store-af", "pair-load-af",
             "pair-store-backing", "pair-load-backing", "pair-store-attribute", "pair-load-attribute",
             "pair-store-permission", "fetch-translation", "fetch-permission"]
    expected = {(name, granule, upper) for name in names
                for granule in ["4096", "16384"] for upper in ["false", "true"]}
    after = {p.name: sha(p) for p in paths}
    passed = (len(cases) == 108 and set(identities) == expected
              and all(c["pass"] == "true" for c in cases)
              and "NXMMU: PASS cases=108 macos_boot_verified=false" in actual
              and not any(line.startswith("NXMMU: FAIL") for line in actual)
              and before == after)
    report = {"schema": "nextcore.authored-stage1-efi.v1", "passed": passed,
              "host_architecture": platform.machine(), "cases": cases, "markers": actual,
              "adjacent_transport_duplicate_lines": transport_duplicates,
              "input_sha256_before": before, "input_sha256_after": after,
              "elapsed_seconds": round(time.monotonic() - start, 3),
              "qemu_exit_code": process.returncode,
              "normal_boot_verified": False, "original_inputs_used": False}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": passed, "cases": len(cases), "report": str(output / 'report.json')}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
