#!/usr/bin/env python3
"""Exercise a built OpenCore's real 64-byte LoadOptions handoff to production EFI.

Uses a labeled own-code fixture, not an Apple boot input; expected result is
EFI_UNSUPPORTED while the native iBoot platform is incomplete.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(opencore, config, output, bootstrap=None, require_caller_return=False):
    binary = opencore.read_bytes()
    # Reject accidentally selected upstream/stale builds before starting a VM.
    # Runtime StartImage/ABI markers below remain the actual integration proof.
    required = [b"AppleSiliconSandbox", b"SandboxSMBIOS", b"OCSB: StartImage ABI v1"]
    if any(marker not in binary for marker in required):
        raise ValueError("OpenCore binary lacks Sandbox implementation; inspect the native build source path")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    esp = output / "esp"
    for name in ["EFI/BOOT", "EFI/OC", "EFI/26x86/Fixtures"]:
        (esp / name).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bootstrap or opencore, esp / "EFI/BOOT/BOOTX64.EFI")
    shutil.copyfile(opencore, esp / "EFI/OC/OpenCore.efi")
    shutil.copyfile(config, esp / "EFI/OC/config.plist")
    # This fixture directly launches OpenCore as removable fallback, without the
    # separate Bootstrap executable. OpenCore resolves config beside its image.
    if bootstrap is None:
        shutil.copyfile(config, esp / "EFI/BOOT/config.plist")
    engine = ROOT / "sandbox/efi/build/BOOTX64.EFI"
    build = json.loads((engine.parent / "build-report.json").read_text())
    if sha(engine) != build["sha256"]:
        raise ValueError("Production engine build hash mismatch")
    shutil.copyfile(engine, esp / "EFI/26x86/Sandbox.efi")
    (esp / "EFI/26x86/Fixtures/iboot.fixture").write_bytes(
        b"26x86 OWN-CODE HANDOFF FIXTURE. NOT APPLE IBOOT. NOT EXECUTABLE.\n")
    hashes = {str(p.relative_to(esp)): sha(p) for p in esp.rglob("*") if p.is_file()}
    serial = output / "serial.log"
    qmp_log = []
    with tempfile.TemporaryDirectory(prefix="26x86-oc-handoff-") as tmp:
        p = Path(tmp)
        shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", p / "vars.fd")
        command = ["qemu-system-x86_64", "-machine", "q35,accel=tcg", "-cpu", "Nehalem",
                   "-m", "512", "-smp", "1", "-display", "none", "-serial", f"file:{serial}",
                   "-monitor", "none", "-qmp", f"unix:{p / 'qmp.sock'},server=on,wait=off",
                   "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
                   "-drive", f"if=pflash,format=raw,file={p / 'vars.fd'}",
                   "-device", "qemu-xhci,id=xhci", "-drive", f"if=none,id=media,format=raw,readonly=on,file=fat:{esp}",
                   "-device", "usb-storage,bus=xhci.0,drive=media,removable=on,bootindex=0",
                   "-net", "none", "-no-reboot"]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and process.poll() is None:
                log = serial.read_text(errors="replace") if serial.exists() else ""
                terminal = "OC: Sandbox engine returned - Unsupported" if require_caller_return else "OCSB: StartImage returned - Unsupported"
                if any(marker in log for marker in [terminal, "Failed to load configuration!", "Halting on critical error"]):
                    break
                time.sleep(0.1)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect(str(p / "qmp.sock"))
                f = sock.makefile("rwb", buffering=0)
                qmp_log.append(json.loads(f.readline()))
                for request in [{"execute": "qmp_capabilities"},
                                {"execute": "screendump", "arguments": {"filename": str(output / "screen.ppm")}},
                                {"execute": "quit"}]:
                    f.write(json.dumps(request).encode() + b"\n")
                    while line := f.readline():
                        result = json.loads(line)
                        qmp_log.append(result)
                        if "return" in result or "error" in result:
                            break
            process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            stderr = process.stderr.read()
    log = serial.read_text(errors="replace")
    markers = ["OCSB: StartImage ABI v1 size=64 target=26 AIC iBoot",
               "26x86 Apple Silicon Sandbox - native EFI JIT", "AIC WIRED IRQ SELFTEST PASS",
               "AIC/iBoot handoff validated", "OCSB: StartImage returned - Unsupported"]
    if require_caller_return:
        markers.append("OC: Sandbox engine returned - Unsupported")
        if b"OCSB: Handoff storage released" in binary:
            markers.append("OCSB: Handoff storage released")
    unchanged = hashes == {str(p.relative_to(esp)): sha(p) for p in esp.rglob("*") if p.is_file()}
    report = {"schema": 1, "passed": unchanged and all(m in log for m in markers),
              "production_opencore": True, "production_engine": True, "cpu_model": "Nehalem",
              "regular_bootstrap_used": bootstrap is not None,
              "caller_return_required": require_caller_return,
              "caller_return_verified": "OC: Sandbox engine returned - Unsupported" in log,
              "handoff_storage_released_marker": "OCSB: Handoff storage released" in log,
              "input_hashes": hashes, "inputs_unchanged": unchanged,
              "markers": {m: m in log for m in markers}, "expected_engine_status": "EFI_UNSUPPORTED",
              "macos_boot_verified": False, "apple_boot_input_used": False,
              "physical_mac_verified": False, "stderr": stderr, "qmp": qmp_log}
    (output / "handoff-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opencore", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path)
    parser.add_argument("--require-caller-return", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    raise SystemExit(main(a.opencore, a.config, a.output, a.bootstrap, a.require_caller_return))
