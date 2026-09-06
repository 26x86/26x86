#!/usr/bin/env python3
"""Boot the test-instrumented EFI under x86 QEMU firmware, never a guest Linux OS."""
import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent


def main():
    results = []
    for cpu_model, own_guest in [("Nehalem", False), ("Nehalem", True), ("Conroe", False)]:
        with tempfile.TemporaryDirectory(prefix="26x86-efi-") as tmp:
            p = pathlib.Path(tmp)
            boot = p / "esp" / "EFI" / "BOOT"
            boot.mkdir(parents=True)
            shutil.copyfile(ROOT / "build/TESTX64.EFI", boot / "BOOTX64.EFI")
            if own_guest:
                guest = p / "esp/EFI/26x86/guest.a64"
                guest.parent.mkdir()
                guest.write_bytes(struct.pack("<4I", 0xd2800140, 0xd1000400, 0xb5ffffe0, 0xd4400000))
            shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", p / "vars.fd")
            command = ["qemu-system-x86_64", "-machine", "q35,accel=tcg", "-cpu", cpu_model,
                       "-m", "512", "-smp", "1", "-display", "none", "-serial", "none", "-monitor", "none",
                       "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
                       "-drive", f"if=pflash,format=raw,file={p / 'vars.fd'}",
                       "-drive", f"format=raw,file=fat:rw:{p / 'esp'}",
                       "-debugcon", f"file:{p / 'debug.log'}", "-device", "isa-debug-exit,iobase=0xf4,iosize=0x04",
                       "-net", "none", "-no-reboot"]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
            log = (p / "debug.log").read_text(errors="replace")
            passed = completed.returncode == 33 and "JIT SELFTEST PASS" in log and "AIC WIRED IRQ SELFTEST PASS" in log
            if own_guest:
                passed = passed and "GUEST HALT" in log
            if cpu_model == "Conroe":
                passed = completed.returncode == 37 and "UNSUPPORTED CPU" in log and "JIT SELFTEST PASS" not in log
            results.append({"cpu_model": cpu_model, "own_code_guest": own_guest, "qemu_exit": completed.returncode,
                            "passed": passed, "log": log, "stderr": completed.stderr})
    report = {"schema": 1, "passed": all(x["passed"] for x in results), "cpu_model": "Nehalem",
              "avx_available": False, "boot_environment": "OVMF UEFI (no Linux guest)",
              "instrumented_artifact_sha256": hashlib.sha256((ROOT / "build/TESTX64.EFI").read_bytes()).hexdigest(),
              "production_artifact_sha256": hashlib.sha256((ROOT / "build/BOOTX64.EFI").read_bytes()).hexdigest(),
              "macos_boot_verified": False, "physical_mac_verified": False, "cases": results}
    (ROOT / "build/ovmf-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
