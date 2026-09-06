"""Visible live-host menu; startup diagnostics never imply a macOS boot."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path("/opt/venfire")
QEMU = "/usr/bin/qemu-system-aarch64"
DATA = None
NETWORK_OK = False


def emit(message: str) -> None:
    print(message, flush=True)
    try:
        with open("/dev/ttyS0", "w", encoding="utf-8") as stream:
            stream.write(message + "\n")
    except OSError:
        pass


def authorization():
    from venfire.policy import authorize_host
    cmdline = Path("/proc/cmdline").read_text().split()
    return authorize_host(developer_host_bypass="venfire.developer=1" in cmdline)


def diagnostics() -> bool:
    from venfire.conformance import run_conformance
    destination = Path("/run/venfire") / ("conformance-" + str(time.time_ns()))
    report = run_conformance(QEMU, destination, timeout=60, target="vmapple")
    emit("VENFIRE_USB|CONFORMANCE|" + ("PASS" if report["passed"] else "FAIL"))
    emit(f"Self-authored AArch64 guest: {report['passed_count']}/{report['case_count']} passed.")
    emit("This proves synthetic CPU/device execution only. macOS boot: NOT VERIFIED.")
    for line in Path(report["serial_log"]).read_text().splitlines():
        emit(line)
    if not report["passed"]:
        emit(Path(report["stderr_log"]).read_text())
    return report["passed"]


def show_host(verbose=False) -> bool:
    try:
        auth = authorization()
        evidence = auth.to_dict()
        Path("/run/venfire-host.json").write_text(json.dumps(evidence, indent=2) + "\n")
        if verbose:
            emit(json.dumps(evidence, indent=2))
        else:
            emit("Host policy accepted. Intel x86_64 + AVX2 checks remain active.")
        emit("VENFIRE_USB|HOST_POLICY|PASS")
        return True
    except Exception as exc:
        emit(f"Host policy: {type(exc).__name__}: {exc}")
        emit("VENFIRE_USB|HOST_POLICY|DENIED")
        return False


def boot_arguments(profile: dict, output: str, developer: bool) -> list[str]:
    if profile.get("schema") != 1:
        raise ValueError("unsupported boot profile schema")
    session = profile.get("storage_session")
    arguments = [sys.executable, "-m", "venfire", "boot-session" if session else "boot-probe",
                 "--qemu", QEMU, "--firmware", profile["firmware"], "--uuid", str(profile["uuid"]),
                 "--output", output]
    if session:
        arguments.extend(["--directory", session])
        arguments.extend(["--graphics", profile.get("graphics", "auto")])
        if "seconds" in profile:
            arguments.extend(["--seconds", str(profile["seconds"])])
    else:
        arguments.extend(["--aux", profile["aux"], "--disk", profile["disk"],
                          "--aux-offset", str(profile.get("aux_offset", 0))])
    if developer:
        arguments.append("--developer-host-bypass")
    return arguments


def boot_profile() -> None:
    profile_path = (DATA if DATA else ROOT) / "boot-profile.json"
    if not profile_path.is_file():
        emit("macOS start unavailable: no boot-profile.json or matching Apple inputs supplied.")
        emit("VENFIRE_USB|MACOS|MISSING_INPUTS")
        return
    try:
        authorization()
        profile = json.loads(profile_path.read_text())
        developer = "venfire.developer=1" in Path("/proc/cmdline").read_text().split()
        arguments = boot_arguments(profile, "/run/venfire/boot-" + str(time.time_ns()), developer)
        session = bool(profile.get("storage_session"))
        if session:
            emit("Starting configured COW storage session. Ctrl+C stops the session; base images remain read-only.")
        else:
            emit("Starting configured, bounded macOS boot probe. A launch is not a successful boot.")
        result = subprocess.run(arguments, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=None if session else 180)
        emit(result.stdout)
        emit(f"Boot probe process exit: {result.returncode}; inspect its evidence before claiming success.")
    except KeyboardInterrupt:
        emit("Boot process interrupted by user; return to the menu.")
    except Exception as exc:
        emit(f"Boot probe unavailable: {type(exc).__name__}: {exc}")


def network_menu():
    global NETWORK_OK
    from network import interfaces, diagnostics
    if not show_host():
        return
    available = interfaces()
    emit("Explicit live-host network setup. DHCP changes only this RAM boot environment.")
    for index, item in enumerate(available, 1):
        emit(str(index) + "  " + item["name"] + ("  carrier detected" if item["carrier"] else "  carrier not detected"))
    if not available:
        emit("No supported wired interface detected. Wireless is not configured by this menu.")
        return
    emit("VENFIRE_USB|NETWORK_MENU|SELECT")
    selected = input("Interface number for DHCP + authenticated TSS HTTPS test (Enter cancels): ").strip()
    if not selected:
        return
    try:
        index = int(selected) - 1
        if index < 0 or index >= len(available):
            raise ValueError("Choose an interface in the displayed list")
        diagnostics(available[index]["name"], emit)
        NETWORK_OK = True
    except Exception as exc:
        NETWORK_OK = False
        emit(f"Network/TSS test failed: {type(exc).__name__}: {exc}")
        emit("VENFIRE_USB|TSS_HTTPS|FAIL")


def restore_arguments(profile_path, output, developer):
    arguments = [sys.executable, "-m", "venfire", "restore-chain", "--qemu", QEMU,
                 "--qemu-img", "/usr/bin/qemu-img", "--helper", "/usr/bin/venfire-tss-request",
                 "--profile", str(profile_path), "--output", str(output)]
    if developer:
        arguments.append("--developer-host-bypass")
    return arguments


def restore_profile():
    global NETWORK_OK
    try:
        authorization()
        from venfire.restore_chain import load_profile
        selected = (DATA if DATA else ROOT) / "restore-profile.json"
        profile = load_profile(selected)
        if not Path("/usr/bin/venfire-tss-request").is_file():
            raise ValueError("This USB image does not include the trusted TSS helper")
        emit("Standard restore: original ROM -> iBSS -> iBEC/LocalPolicy -> restore components.")
        emit("This action contacts Apple TSS. Every ticket and guest trust check remains active.")
        emit("Graphics device selection: " + profile["graphics"] + "; physical display remains unverified.")
        if not NETWORK_OK:
            from network import automatic_diagnostics
            automatic_diagnostics(emit)
            NETWORK_OK = True
        parent = (DATA / "restore-runs") if DATA else Path("/run/venfire")
        parent.mkdir(parents=True, exist_ok=True)
        output = parent / ("restore-" + str(time.time_ns()))
        developer = "venfire.developer=1" in Path("/proc/cmdline").read_text().split()
        emit("VENFIRE_USB|RESTORE_CHAIN|START")
        emit("Ctrl+C stops the session. Logs, tickets and separate COW files are stored in " + str(output))
        result = subprocess.run(restore_arguments(selected, output, developer), check=False)
        emit("VENFIRE_USB|RESTORE_CHAIN|" + ("COMPLETE_BOOT_UNVERIFIED" if result.returncode == 0 else "FAILED"))
    except KeyboardInterrupt:
        emit("Restore chain interrupted; session cleanup retains input-integrity evidence.")
    except Exception as exc:
        emit(f"Restore chain unavailable: {type(exc).__name__}: {exc}")
        emit("VENFIRE_USB|RESTORE_CHAIN|FAILED")


def main() -> None:
    global DATA, NETWORK_OK
    from venfire._build_profile import BUILD_PROFILE
    emit("\033[2J\033[HVENFIRE / USB LIVE HOST")
    emit("Layer: x86_64 Linux host -> QEMU TCG -> AArch64 guest")
    if BUILD_PROFILE == "developer-nonredistributable":
        emit("DEVELOPER BUILD - NOT FOR REDISTRIBUTION")
        emit("Apple-host exception requires explicit opt-in; Intel + AVX2 checks remain mandatory.")
    else:
        emit("RELEASE POLICY - genuine Apple Intel host + AVX2 required")
    emit("Root filesystem and logs are in RAM. Internal disks are not mounted.")
    emit("macOS boot: NOT VERIFIED. USB startup and synthetic diagnostics are separate checks.")
    emit("VENFIRE_USB|FIRMWARE|" + ("UEFI" if Path("/sys/firmware/efi").is_dir() else "UNKNOWN"))
    emit("VENFIRE_USB|USERSPACE|READY")
    eligible = show_host()
    passed = False
    data_ok = True
    network_ok = True
    if eligible:
        try:
            from data_partition import mount_selected
            DATA = mount_selected(Path("/proc/cmdline").read_text(), BUILD_PROFILE, emit)
        except Exception as exc:
            data_ok = False
            emit(f"USB data partition refused: {type(exc).__name__}: {exc}")
            emit("VENFIRE_USB|DATA|DENIED")
        try:
            passed = diagnostics()
        except Exception as exc:
            emit(f"Startup diagnostics failed: {type(exc).__name__}: {exc}")
            emit("VENFIRE_USB|CONFORMANCE|FAIL")
        if "venfire.network_test=1" in Path("/proc/cmdline").read_text().split():
            try:
                from network import automatic_diagnostics
                automatic_diagnostics(emit)
                NETWORK_OK = True
            except Exception as exc:
                network_ok = False
                emit(f"Explicit network self-test failed: {type(exc).__name__}: {exc}")
                emit("VENFIRE_USB|TSS_HTTPS|FAIL")
    if "venfire.autotest=1" in Path("/proc/cmdline").read_text().split():
        emit("VENFIRE_USB|AUTOTEST|" + ("PASS" if eligible and passed and data_ok and network_ok else "FAIL"))
        subprocess.run(["/bin/busybox", "poweroff", "-f"], check=False)
    while True:
        print("\033[2J\033[H", end="", flush=True)
        emit("VENFIRE / USB LIVE HOST")
        if BUILD_PROFILE == "developer-nonredistributable":
            emit("DEVELOPER BUILD - NOT FOR REDISTRIBUTION")
        else:
            emit("RELEASE POLICY - genuine Apple Intel + AVX2 required")
        emit("USB startup: Linux ready  |  Synthetic ARM checks: " + ("PASS" if passed else "NOT PASSED"))
        emit("macOS boot: NOT VERIFIED  |  Internal storage: not mounted")
        emit("USB data: " + ("explicit PARTUUID mounted at /data" if DATA else "not mounted"))
        emit("Last TSS HTTPS check: " + ("reachable; no ticket requested" if NETWORK_OK else "not passed"))
        emit("\n1  Inspect host policy and CPU")
        emit("2  Run self-authored CPU/MMU/IRQ diagnostics")
        emit("3  Start macOS using an explicitly supplied profile")
        emit("4  Open live-host recovery shell")
        emit("5  Power off")
        emit("6  Configure wired DHCP and test TSS HTTPS")
        emit("7  Run standard restore using restore-profile.json and Apple TSS")
        emit("VENFIRE_USB|MENU_READY|keyboard")
        try:
            choice = input("Select 1-7, then Enter: ").strip()
        except EOFError:
            time.sleep(1)
            continue
        if choice == "1":
            emit("VENFIRE_USB|KEYBOARD|ACCEPTED")
            show_host(verbose=True)
            input("Press Enter to return to the menu: ")
        elif choice == "2":
            if show_host():
                diagnostics()
        elif choice == "3":
            boot_profile()
        elif choice == "4":
            subprocess.run(["/bin/busybox", "sh"], check=False)
        elif choice == "5":
            subprocess.run(["/bin/busybox", "poweroff", "-f"], check=False)
        elif choice == "6":
            network_menu()
            emit("VENFIRE_USB|NETWORK_MENU|DONE")
            input("Press Enter to return to the menu: ")
        elif choice == "7":
            restore_profile()
            input("Press Enter to return to the menu: ")


if __name__ == "__main__":
    main()
