"""Explicit commands with JSON evidence and nonzero failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from .artifacts import create_manifest, load_manifest, verify_manifest, write_manifest
from .backend import probe_backend
from .host import HostEligibilityError, detect_host
from .media import inspect_restore
from .policy import authorize_host, load_build_profile


def emit(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="venfire", description=
                                    "26x86 ARM64 platform bring-up. macOS boot is unverified.")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Read-only genuine Intel Mac + AVX2 eligibility check")
    doctor.add_argument("--developer-host-bypass", action="store_true",
                        help="Private developer build only: waive Apple platform checks, retain Intel/AVX2")
    backend = commands.add_parser("backend", help="Inspect QEMU's declared capabilities")
    backend.add_argument("--qemu")
    manifest = commands.add_parser("manifest", help="Hash original regular files without modifying them")
    manifest.add_argument("--output", required=True)
    manifest.add_argument("files", nargs="+")
    verify = commands.add_parser("verify", help="Check original files against a saved manifest")
    verify.add_argument("manifest")
    restore = commands.add_parser("inspect-restore", help="Read IPSW BuildManifest in place")
    restore.add_argument("path")
    restore.add_argument("--sha256", action="store_true", help="Also hash the complete archive")
    conformance = commands.add_parser("conformance", help="Run only the bundled self-authored ARM64 guest")
    conformance.add_argument("--qemu", default="qemu-system-aarch64")
    conformance.add_argument("--output", required=True)
    conformance.add_argument("--target", choices=("virt", "vmapple"), default="virt")
    conformance.add_argument("--timeout", type=int, default=20)
    boot = commands.add_parser("boot-probe", help="Host-gated bounded read-only firmware experiment")
    for name in ("qemu", "firmware", "aux", "disk", "output"):
        boot.add_argument("--" + name, required=True)
    boot.add_argument("--uuid", required=True, type=lambda x: int(x, 0), help="Existing VM's numeric SDOM identity")
    boot.add_argument("--aux-offset", type=lambda x: int(x, 0), default=0,
                      help="Explicit read-only raw byte-view offset; never trims the source")
    boot.add_argument("--seconds", type=int, default=20)
    boot.add_argument("--recovery-socket", help="Explicit local Unix socket for the real recovery USB transport")
    boot.add_argument("--developer-host-bypass", action="store_true",
                      help="Private developer build only; CPU and guest trust checks remain enabled")
    storage = commands.add_parser("storage-create", help="Create separate persistent COW files over immutable raw images")
    for name in ("aux", "disk", "directory"):
        storage.add_argument("--" + name, required=True)
    storage.add_argument("--qemu-img", default="qemu-img")
    storage.add_argument("--aux-offset", type=lambda x: int(x, 0), default=0)
    session = commands.add_parser("boot-session", help="Run VMApple with persistent guest writes to separate COW files")
    for name in ("qemu", "firmware", "directory", "output"):
        session.add_argument("--" + name, required=True)
    session.add_argument("--uuid", required=True, type=lambda x: int(x, 0))
    session.add_argument("--seconds", type=int, help="Omit to run until guest exits or user interrupts")
    session.add_argument("--developer-host-bypass", action="store_true")
    session.add_argument("--recovery-socket")
    session.add_argument("--graphics", choices=("auto", "on", "off"), default="auto")
    chain = commands.add_parser("restore-chain", help="Run one original-preserving ROM/iBSS/iBEC/restore chain; boot remains unverified")
    for name in ("qemu", "profile", "output"):
        chain.add_argument("--" + name, required=True)
    chain.add_argument("--qemu-img", default="qemu-img")
    chain.add_argument("--helper", default="/usr/bin/venfire-tss-request")
    chain.add_argument("--developer-host-bypass", action="store_true")
    recovery = commands.add_parser("recovery-probe", help="Read actual USB descriptor/DFU replies over a local recovery socket")
    recovery.add_argument("socket")
    recovery.add_argument("--timeout", type=float, default=5)
    recovery.add_argument("--developer-host-bypass", action="store_true")
    personalize = commands.add_parser("personalize-ibss", help="Ask Apple TSS to personalize original iBSS for this live VM")
    for name in ("socket", "manifest", "ibss", "helper", "output"):
        personalize.add_argument("--" + name, required=True)
    personalize.add_argument("--developer-host-bypass", action="store_true")
    firmware = commands.add_parser("personalize-firmware", help="Ask Apple TSS for original iBSS or iBEC for the live VM")
    for name in ("socket", "manifest", "firmware", "helper", "output"):
        firmware.add_argument("--" + name, required=True)
    firmware.add_argument("--component", choices=("iBSS", "iBEC"), required=True)
    firmware.add_argument("--include-restore-policy", action="store_true", help="Request Apple-signed standard restore policy bound to the iBEC ticket")
    firmware.add_argument("--developer-host-bypass", action="store_true")
    upload = commands.add_parser("dfu-upload", help="Transfer a verified local image to the virtual DFU device")
    upload.add_argument("--socket", required=True)
    upload.add_argument("--image", required=True)
    upload.add_argument("--sha256", required=True, help="Required SHA-256 of the reviewed input")
    upload.add_argument("--output", required=True, help="Fresh JSON evidence file")
    upload.add_argument("--timeout", type=float, default=5)
    upload.add_argument("--total-timeout", type=float, default=300)
    upload.add_argument("--reset", action="store_true", help="Issue virtual USB bus reset after complete transfer")
    upload.add_argument("--developer-host-bypass", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            if args.developer_host_bypass:
                emit(authorize_host(developer_host_bypass=True).to_dict())
                return 0
            report = detect_host()
            emit({**report.to_dict(), "build_profile": load_build_profile()})
            return 0 if report.eligible else 2
        if args.command == "backend":
            report = probe_backend(args.qemu)
            emit(report)
            return 0 if report["research_headless"] and report["tcg"] else 2
        if args.command == "manifest":
            report = create_manifest(args.files)
            write_manifest(report, args.output)
            emit(report.to_dict())
            return 0
        if args.command == "verify":
            report = verify_manifest(load_manifest(args.manifest))
            emit(report.to_dict())
            return 0 if report.valid else 3
        if args.command == "inspect-restore":
            emit(inspect_restore(args.path, hash_archive=args.sha256))
            return 0
        if args.command == "conformance":
            from .conformance import run_conformance
            report = run_conformance(args.qemu, Path(args.output), timeout=args.timeout, target=args.target)
            emit(report)
            return 0 if report.get("passed") else 4
        if args.command == "boot-probe":
            from .boot import boot_probe
            report = boot_probe(qemu=args.qemu, firmware=args.firmware, aux=args.aux, disk=args.disk,
                                uuid=args.uuid, output=args.output, seconds=args.seconds,
                                aux_offset=args.aux_offset,
                                developer_host_bypass=args.developer_host_bypass, recovery_socket=args.recovery_socket)
            emit(report)
            # A probe cannot return a successful installation/boot status.
            return 5 if report["input_integrity"]["valid"] else 3
        if args.command == "storage-create":
            from .storage import prepare_storage
            storage = prepare_storage(aux=args.aux, disk=args.disk, directory=args.directory,
                                      qemu_img=args.qemu_img, aux_offset=args.aux_offset)
            emit({"storage_session": str(storage.directory), "base_images_read_only": True,
                  "guest_writes": "separate qcow2 overlays", "macos_boot_verified": False})
            return 0
        if args.command == "boot-session":
            from .boot import boot_session
            report = boot_session(qemu=args.qemu, firmware=args.firmware, directory=args.directory,
                                  uuid=args.uuid, output=args.output, seconds=args.seconds,
                                  developer_host_bypass=args.developer_host_bypass, recovery_socket=args.recovery_socket,
                                  graphics=args.graphics)
            emit(report)
            return 5 if report["input_integrity"]["valid"] else 3
        if args.command == "restore-chain":
            from .restore_chain import boot_restore_chain
            report = boot_restore_chain(qemu=args.qemu, qemu_img=args.qemu_img,
                profile_path=args.profile, helper=args.helper, output=args.output,
                developer_host_bypass=args.developer_host_bypass,
                progress=lambda stage: print("VENFIRE_RESTORE|STAGE|" + stage, flush=True))
            emit(report)
            # Zero means the bounded chain operation completed, never macOS boot.
            return 0 if report["chain_completed"] else 1
        if args.command == "recovery-probe":
            from .recovery import probe_recovery
            authorize_host(developer_host_bypass=args.developer_host_bypass)
            emit(probe_recovery(args.socket, args.timeout))
            return 0
        if args.command == "personalize-ibss":
            from .personalization import personalize_ibss
            emit(personalize_ibss(socket_path=args.socket, build_manifest=args.manifest,
                                  ibss=args.ibss, helper=args.helper, output=args.output,
                                  developer_host_bypass=args.developer_host_bypass))
            return 0
        if args.command == "dfu-upload":
            from .recovery import send_dfu_file, RecoveryUploadError
            from pathlib import Path
            authorization = authorize_host(developer_host_bypass=args.developer_host_bypass)
            import re
            if re.fullmatch(r"[a-fA-F0-9]{64}", args.sha256) is None:
                raise ValueError("A 64-digit SHA-256 is required")
            with Path(args.output).open("x", encoding="utf-8") as destination:
                report = {"schema": 1, "transfer_complete": False, "macos_boot_verified": False}
                try:
                    report = send_dfu_file(args.socket, args.image, timeout=args.timeout,
                                           total_timeout=args.total_timeout, reset=args.reset,
                                           expected_sha256=args.sha256)
                    code = 0
                except RecoveryUploadError as exc:
                    report, code = exc.report, 1
                except BaseException as exc:
                    report = getattr(exc, "recovery_report", report)
                    report["error"] = f"{type(exc).__name__}: {exc}"
                    raise
                finally:
                    report["host_authorization"] = authorization.to_dict()
                    json.dump(report, destination, indent=2)
                    destination.write("\n")
            emit(report)
            return code
        if args.command == "personalize-firmware":
            from .personalization import personalize_firmware
            emit(personalize_firmware(socket_path=args.socket, build_manifest=args.manifest,
                firmware=args.firmware, component=args.component, helper=args.helper,
                output=args.output, developer_host_bypass=args.developer_host_bypass,
                include_restore_policy=args.include_restore_policy))
            return 0
    except HostEligibilityError as exc:
        emit({"error": str(exc), "host": exc.report.to_dict()})
        return 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        emit({"error": str(exc), "command": args.command})
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
