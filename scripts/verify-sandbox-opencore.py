#!/usr/bin/env python3
"""Exercise a built OpenCore's real 64-byte LoadOptions handoff to production EFI.

Uses a labeled own-code fixture, not an Apple boot input.  The Phase-1 EFI
engine returns EFI_SUCCESS only after its bounded Rust/JIT diagnostic path;
this does not claim iBoot, XNU, or macOS execution.
"""
import argparse
import hashlib
import json
import plistlib
import re
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
ALLOCATION_PATTERN = re.compile(
    r"VF: EFI_ALLOCATIONS count=(0x[0-9a-f]+) bytes=(0x[0-9a-f]+)", re.IGNORECASE
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def effective_config(config, diagnostic_fixture):
    """Return bytes for the ESP and metadata without mutating the input plist."""
    original = config.read_bytes()
    if not diagnostic_fixture:
        document = plistlib.loads(original)
        if not isinstance(document, dict):
            raise ValueError("OpenCore configuration must be a plist dictionary")
        sandbox = document.get("AppleSiliconSandbox")
        misc = document.get("Misc")
        security = misc.get("Security", {}) if isinstance(misc, dict) else {}
        if not isinstance(security, dict):
            security = {}
        preconditions = {
            "sandbox_enabled": isinstance(sandbox, dict) and sandbox.get("Enabled") is True,
            "vault_mode": security.get("Vault"),
        }
        preconditions["ready_for_handoff"] = preconditions["sandbox_enabled"] and preconditions["vault_mode"] != "Secure"
        return original, {
            "mode": "provided",
            "input_sha256": sha_bytes(original),
            "effective_sha256": sha_bytes(original),
            "input_unchanged": True,
            "preconditions": preconditions,
            "overrides": {},
        }

    document = plistlib.loads(original)
    if not isinstance(document, dict):
        raise ValueError("OpenCore configuration must be a plist dictionary")
    sandbox = document.get("AppleSiliconSandbox")
    if not isinstance(sandbox, dict):
        raise ValueError("diagnostic fixture requires an AppleSiliconSandbox dictionary")
    smbios = document.setdefault("SandboxSMBIOS", {})
    if not isinstance(smbios, dict):
        raise ValueError("diagnostic fixture requires a SandboxSMBIOS dictionary")
    misc = document.setdefault("Misc", {})
    if not isinstance(misc, dict):
        raise ValueError("diagnostic fixture requires a Misc dictionary")
    security = misc.setdefault("Security", {})
    if not isinstance(security, dict):
        raise ValueError("diagnostic fixture requires a Misc.Security dictionary")
    debug = misc.setdefault("Debug", {})
    if not isinstance(debug, dict):
        raise ValueError("diagnostic fixture requires a Misc.Debug dictionary")
    sandbox.update(
        Enabled=True,
        IBootPath="\\EFI\\26x86\\Fixtures\\iboot.fixture",
    )
    smbios.update(
        SystemProductName="Synthetic-26x86",
        SystemSerialNumber="TEST-ONLY-26X86",
        SystemUUID="00112233-4455-6677-8899-aabbccddeeff",
        BoardProduct="Synthetic-Board",
    )
    # The source sample uses a Secure vault and a critical-error halt level.
    # Those defaults are correct for ordinary OpenCore, but would stop a
    # self-contained diagnostic handoff before the Sandbox image starts.
    security["Vault"] = "Optional"
    security["HaltLevel"] = 0
    debug["DisplayLevel"] = 0x800000FF
    effective = plistlib.dumps(document, sort_keys=False)
    return effective, {
        "mode": "synthetic-diagnostic-fixture",
        "input_sha256": sha_bytes(original),
        "effective_sha256": sha_bytes(effective),
        "input_unchanged": True,
        "preconditions": {
            "sandbox_enabled": True,
            "vault_mode": "Optional",
            "ready_for_handoff": True,
        },
        "overrides": {
            "AppleSiliconSandbox.Enabled": True,
            "AppleSiliconSandbox.IBootPath": "\\EFI\\26x86\\Fixtures\\iboot.fixture",
            "SandboxSMBIOS": "synthetic identity only",
            "Misc.Security.Vault": "Optional",
            "Misc.Security.HaltLevel": 0,
            "Misc.Debug.DisplayLevel": "0x800000ff",
        },
    }


def main(opencore, config, output, bootstrap=None, require_caller_return=False,
         diagnostic_fixture=False):
    binary = opencore.read_bytes()
    # Reject accidentally selected upstream/stale builds before starting a VM.
    # Runtime StartImage/ABI markers below remain the actual integration proof.
    required = [b"AppleSiliconSandbox", b"SandboxSMBIOS", b"OCSB: StartImage ABI v1"]
    if any(marker not in binary for marker in required):
        raise ValueError("OpenCore binary lacks Sandbox implementation; inspect the native build source path")
    config_bytes, config_report = effective_config(config, diagnostic_fixture)
    output = output.resolve()
    if not config_report["preconditions"]["ready_for_handoff"]:
        output.mkdir(parents=True, exist_ok=False)
        report = {
            "schema": 2,
            "passed": False,
            "production_opencore": True,
            "production_engine": False,
            "cpu_model": "Nehalem",
            "regular_bootstrap_used": bootstrap is not None,
            "caller_return_required": require_caller_return,
            "caller_return_verified": False,
            "opencore_boot_completion_verified": False,
            "handoff_only": True,
            "handoff_storage_released_marker": False,
            "boot_services_allocations": None,
            "input_hashes": {},
            "inputs_unchanged": True,
            "configuration": config_report,
            "configuration_precondition_failure": True,
            "markers": {},
            "expected_engine_status": "EFI_SUCCESS (Phase-1 diagnostic only)",
            "layer_status": {
                "firmware_efi": "blocked: configuration precondition",
                "rust_preos": "not attempted",
                "aarch64_jit": "not attempted",
                "native_machine": "not attempted",
                "apple_boot_chain": "blocked",
                "macos": "not attempted",
            },
            "macos_boot_verified": False,
            "apple_boot_input_used": False,
            "physical_mac_verified": False,
            "stderr": "",
            "qmp": [],
        }
        (output / "handoff-report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 1
    output.mkdir(parents=True, exist_ok=False)
    esp = output / "esp"
    for name in ["EFI/BOOT", "EFI/OC", "EFI/26x86/Fixtures"]:
        (esp / name).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bootstrap or opencore, esp / "EFI/BOOT/BOOTX64.EFI")
    shutil.copyfile(opencore, esp / "EFI/OC/OpenCore.efi")
    (esp / "EFI/OC/config.plist").write_bytes(config_bytes)
    # This fixture directly launches OpenCore as removable fallback, without the
    # separate Bootstrap executable. OpenCore resolves config beside its image.
    if bootstrap is None:
        (esp / "EFI/BOOT/config.plist").write_bytes(config_bytes)
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
                terminal = "OC: Sandbox engine returned - Success" if require_caller_return else "OCSB: StartImage returned - Success"
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
               "AIC/iBoot handoff validated", "VF: RUST_ENTER", "VF: MACHINE_READY", "VF: JIT_ENTER",
               "VF: GUEST_HALT", "VF: RUST_RETURN_OK", "VF: EFI_RETURN_OK",
               "OCSB: StartImage returned - Success"]
    if require_caller_return:
        markers.append("OC: Sandbox engine returned - Success")
        if b"OCSB: Handoff storage released" in binary:
            markers.append("OCSB: Handoff storage released")
    unchanged = hashes == {str(p.relative_to(esp)): sha(p) for p in esp.rglob("*") if p.is_file()}
    passed = unchanged and all(m in log for m in markers)
    allocation = ALLOCATION_PATTERN.search(log)
    boot_services_allocations = None if allocation is None else {
        "count": int(allocation.group(1), 16),
        "bytes": int(allocation.group(2), 16),
    }
    report = {"schema": 2, "passed": passed,
              "production_opencore": True, "production_engine": True, "cpu_model": "Nehalem",
              "regular_bootstrap_used": bootstrap is not None,
              "caller_return_required": require_caller_return,
              "caller_return_verified": "OC: Sandbox engine returned - Success" in log,
              "opencore_boot_completion_verified": "OC: Failed to boot" not in log,
              "handoff_only": True,
              "handoff_storage_released_marker": "OCSB: Handoff storage released" in log,
              "boot_services_allocations": boot_services_allocations,
              "input_hashes": hashes, "inputs_unchanged": unchanged,
              "configuration": config_report,
              "markers": {m: m in log for m in markers}, "expected_engine_status": "EFI_SUCCESS (Phase-1 diagnostic only)",
              "layer_status": {
                  "firmware_efi": "passed" if passed else "failed",
                  "rust_preos": "passed" if all(m in log for m in ["VF: RUST_ENTER", "VF: MACHINE_READY", "VF: RUST_RETURN_OK"]) else "failed",
                  "aarch64_jit": "passed" if all(m in log for m in ["VF: JIT_ENTER", "VF: GUEST_HALT"]) else "failed",
                  "native_machine": "partial: one RAM region and empty MMIO registry",
                  "apple_boot_chain": "not attempted",
                  "macos": "not attempted",
              },
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
    parser.add_argument(
        "--diagnostic-fixture",
        action="store_true",
        help="derive an enabled, synthetic, non-Apple handoff config without modifying --config",
    )
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    raise SystemExit(main(a.opencore, a.config, a.output, a.bootstrap,
                          a.require_caller_return, a.diagnostic_fixture))
