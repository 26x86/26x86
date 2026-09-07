#!/usr/bin/env python3
"""Run the layered VenFire boot/runtime verification harness.

The harness joins evidence that is otherwise easy to confuse:

* the x86-64 EFI/preOS/JIT package under OVMF;
* the pinned VMApple QEMU TCG machine and self-authored ARM64 guest;
* an optional unchanged caller-supplied AVPBooter + macosvm.json bundle; and
* the UART evidence gate for iBoot, XNU, and macOS userspace.

It never manufactures Apple inputs, changes a guest image, or turns a QEMU
exit/help line into a macOS boot result.  Without the original signed
AVPBooter and a provisioned, hardware-model-matched AUX/root pair the Apple
boot-chain portion is reported as ``blocked`` with an explicit input contract.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
EFI_ROOT = ROOT / "sandbox" / "efi"
RESEARCH_ROOT = ROOT / "research" / "venfire"
# Running ``python Tools/verify_boot_runtime.py`` puts ``Tools/`` (rather than
# the repository root) on sys.path.  The runtime control plane lives in the
# root ``x86`` package, so make that layer explicit before the optional TCG
# import below.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MAX_FIRMWARE_BYTES = 1 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular(path: str | Path | None, label: str, *, maximum: int | None = None) -> Path:
    if path is None or not str(path):
        raise ValueError(f"missing required {label} input")
    supplied = Path(path).expanduser()
    if supplied.is_symlink():
        raise ValueError(f"{label} must not be a symlink: {supplied}")
    candidate = supplied.resolve(strict=True)
    if not candidate.is_file():
        raise ValueError(f"{label} must be a regular file: {candidate}")
    size = candidate.stat().st_size
    if size <= 0:
        raise ValueError(f"{label} must not be empty: {candidate}")
    if maximum is not None and size > maximum:
        raise ValueError(f"{label} exceeds {maximum} bytes: {candidate}")
    return candidate


def _new_output(value: str | Path) -> Path:
    output = Path(value).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError(f"output must be a new directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    return output


def _run_step(name: str, argv: Sequence[str], output: Path, *, timeout: float) -> dict[str, Any]:
    """Run one bounded step and preserve stdout/stderr as evidence files."""
    stdout_path = output / f"{name}.stdout.log"
    stderr_path = output / f"{name}.stderr.log"
    try:
        completed = subprocess.run(
            list(argv), cwd=ROOT, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8", errors="replace")
        stderr_path.write_text(completed.stderr, encoding="utf-8", errors="replace")
        return {
            "name": name, "command": list(argv), "returncode": completed.returncode,
            "passed": completed.returncode == 0,
            "stdout": str(stdout_path), "stderr": str(stderr_path),
        }
    except (OSError, subprocess.SubprocessError) as error:
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"{type(error).__name__}: {error}\n", encoding="utf-8")
        return {
            "name": name, "command": list(argv), "returncode": None,
            "passed": False, "error": f"{type(error).__name__}: {error}",
            "stdout": str(stdout_path), "stderr": str(stderr_path),
        }


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _load_last_json(path: Path) -> dict[str, Any] | None:
    """Read the last JSON line from a compact verifier output."""
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return None
    for line in reversed(lines):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _copy_report(source: Path, destination: Path) -> dict[str, Any] | None:
    report = _load_json(source)
    if report is not None:
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _external_contract(args: argparse.Namespace) -> dict[str, Any]:
    """Describe the inputs required to make the Apple path runnable."""
    requirements = [
        {
            "name": "qemu-system-aarch64",
            "purpose": "patched VMApple machine with TCG, research-headless, and BDIF COW gate",
            "source": "Tools/build_vmapple_tcg.py and research/venfire/patches/series",
        },
        {
            "name": "qemu-img",
            "purpose": "new qcow2 overlays for guest writes; source AUX/root remain read-only",
            "source": "x86/vmapple_tcg.py StorageSession",
        },
        {
            "name": "AVPBooter firmware",
            "purpose": "original caller-supplied signed VMApple firmware, not modified by VenFire",
            "source": "caller-owned macOS Virtualization.framework bundle",
        },
        {
            "name": "macosvm.json",
            "purpose": "atomic ECID, hardwareModel, AUX, and root relationship",
            "source": "caller-owned Apple VM bundle",
        },
        {
            "name": "provisioned AUX/root pair",
            "purpose": "hardware-model-matched macOS 26/27 storage; zero fixtures are not install targets",
            "source": "Apple installer/restore process",
        },
        {
            "name": "target-matching UART evidence",
            "purpose": "iBoot Stage2 -> Darwin/XNU -> launchd/loginwindow/WindowServer markers",
            "source": "guest serial transcript; ACKs and process exit are insufficient",
        },
    ]
    supplied = {
        "qemu": args.qemu,
        "qemu_img": args.qemu_img,
        "firmware": args.firmware,
        "vm_json": args.vm_json,
    }
    present: dict[str, Any] = {}
    missing: list[str] = []
    for name, value in supplied.items():
        if not value:
            missing.append(name)
            present[name] = {"supplied": False}
            continue
        try:
            limit = MAX_FIRMWARE_BYTES if name == "firmware" else None
            if name in {"qemu", "qemu_img"}:
                # Host tools are often installed through a symlinked wrapper;
                # the guest firmware/storage inputs below still use the strict
                # no-symlink regular-file rule.
                path = Path(value).expanduser().resolve(strict=True)
                if not path.is_file():
                    raise ValueError(f"{name} must resolve to a regular file: {path}")
            else:
                path = _regular(value, name, maximum=limit)
            present[name] = {
                "supplied": True, "path": str(path), "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        except (OSError, ValueError) as error:
            present[name] = {"supplied": True, "valid": False,
                             "error": f"{type(error).__name__}: {error}"}
            missing.append(name)
    # A full run can only start when all four caller-owned/process inputs are
    # present.  A missing qemu-img is not silently replaced by a raw writable
    # drive because that would violate the image-integrity contract.
    runnable = not missing
    return {
        "runnable": runnable,
        "missing": missing,
        "supplied": present,
        "requirements": requirements,
        "native_m1_requirements": [
            "Darwin arm64 host with genuine Apple Silicon hardware",
            "Virtualization.framework VMApple support",
            "Apple-signed VM bundle and matching hardwareModel/AUX/root",
            "independent UART or console evidence of iBoot, XNU, and userspace",
        ],
    }


def _status_from_efi(efi: dict[str, Any] | None, ovmf: dict[str, Any] | None, key: str) -> str:
    if efi is None or ovmf is None:
        return "not-attempted"
    if not efi.get("passed", False) or not ovmf.get("passed", False):
        return "failed"
    if key == "firmware_efi":
        return "passed"
    report = efi.get("report") if isinstance(efi.get("report"), dict) else {}
    if key == "rust_preos":
        return "passed" if report.get("rust_unit", {}).get("passed") else "failed"
    if key == "aarch64_jit":
        return "passed" if report.get("native_unit", {}).get("passed") else "failed"
    return "not-attempted"


def _handoff_contract_for_tcg(tcg: dict[str, Any], *, target_major: int) -> dict[str, Any]:
    """Adapt one TCG result to the offline iBoot/XNU handoff contract.

    The adapter does not add evidence.  It only maps the TCG runner's flat
    observation fields to the contract's direct-boot shape so the same
    anti-claim verifier is applied to native and TCG reports.
    """
    from x86.iboot_handoff import verify_handoff_report

    observation = {
        "xnu_executed": tcg.get("xnu_executed") is True,
        "macos_userspace_reached": tcg.get("macos_userspace_reached") is True,
        "guest_kernel_major": tcg.get("guest_kernel_major"),
        "guest_target_match": tcg.get("guest_target_match") is True,
        "observed_markers": tcg.get("observed_markers", {}),
    }
    candidate = {
        "schema": "26x86.vmapple-tcg/1",
        "machine_type": "iBoot(AArch64)",
        "guest_os": "macOS",
        "target_major": target_major,
        "input_integrity": tcg.get("input_integrity") is True,
        "runtime_started": tcg.get("tcg_runtime_started") is True,
        "xnu_executed": tcg.get("xnu_executed") is True,
        "macos_boot_verified": tcg.get("macos_boot_verified") is True,
        "direct_boot": {
            "requested": True,
            "selection": "macos",
            "dfu_entered": False,
            "observation": observation,
        },
    }
    return verify_handoff_report(candidate, expected_target_major=target_major)


def verify(args: argparse.Namespace) -> dict[str, Any]:
    output = _new_output(args.output)
    report: dict[str, Any] = {
        "schema": "26x86.boot-runtime/1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "layer": "EFI/preOS -> QEMU VMApple TCG -> AVPBooter/iBoot -> XNU -> macOS userspace",
        "host": {"system": platform.system(), "architecture": platform.machine()},
        "checks": {},
        "external_input_contract": _external_contract(args),
        "synthetic_guest": None,
        "tcg_runtime": None,
        "layer_status": {},
        "macos_boot_verified": False,
        "full_iboot_xnu_userspace_chain_verified": False,
        "physical_m1_compatibility": False,
        "physical_mac_verified": False,
        "errors": [],
    }

    if not args.skip_contracts:
        for name, script in (
            ("m1_machine_contract", EFI_ROOT / "verify_m1_machine_contract.py"),
            ("vmapple_tcg_contract", EFI_ROOT / "verify_vmapple_tcg_contract.py"),
            ("vmapple_tcg_source_manifest", EFI_ROOT / "verify_vmapple_tcg_source_manifest.py"),
        ):
            step = _run_step(name, [sys.executable, str(script), "--compact"], output, timeout=60)
            step["report"] = _load_last_json(output / f"{name}.stdout.log")
            report["checks"][name] = step
            if not step["passed"]:
                report["errors"].append(f"{name} failed")

    efi_step: dict[str, Any] | None = None
    ovmf_step: dict[str, Any] | None = None
    if not args.skip_efi:
        efi_step = _run_step("efi_build", [sys.executable, str(EFI_ROOT / "build.py")], output, timeout=args.efi_timeout)
        efi_step["report"] = _copy_report(EFI_ROOT / "build" / "build-report.json", output / "efi-build-report.json")
        report["checks"]["efi_build"] = efi_step
        if not efi_step["passed"]:
            report["errors"].append("EFI/preOS build failed")
    if not args.skip_ovmf:
        ovmf_step = _run_step("ovmf_runtime", [sys.executable, str(EFI_ROOT / "verify_ovmf.py")], output, timeout=args.efi_timeout)
        ovmf_step["report"] = _copy_report(EFI_ROOT / "build" / "ovmf-report.json", output / "ovmf-report.json")
        report["checks"]["ovmf_runtime"] = ovmf_step
        if not ovmf_step["passed"]:
            report["errors"].append("OVMF EFI/preOS runtime failed")

    if args.run_synthetic:
        if args.qemu:
            synthetic_dir = output / "synthetic"
            step = _run_step(
                "synthetic_guest",
                [sys.executable, str(RESEARCH_ROOT / "tools" / "verify.py"),
                 "--qemu", str(args.qemu), "--output", str(synthetic_dir)],
                output, timeout=args.synthetic_timeout,
            )
            summary = _load_json(synthetic_dir / "summary.json")
            step["report"] = summary
            report["synthetic_guest"] = summary or step
            report["checks"]["synthetic_guest"] = step
            if not step["passed"]:
                report["errors"].append("synthetic guest conformance failed")
        else:
            report["synthetic_guest"] = {"passed": False, "blocked": "qemu path is required"}
            report["errors"].append("synthetic guest requested without qemu path")

    contract = report["external_input_contract"]
    if contract["runnable"] and not args.skip_tcg:
        tcg_dir = output / "tcg"
        try:
            # Import only after static checks so a plain contracts-only run has
            # no dependency on the QEMU control plane.
            from x86.vmapple_tcg import TCGVMappleConfig, run_tcg_macosvm

            tcg_report = run_tcg_macosvm(TCGVMappleConfig(
                target_major=args.target,
                qemu=args.qemu,
                qemu_img=args.qemu_img,
                firmware=args.firmware,
                vm_json=args.vm_json,
                output=str(tcg_dir),
                memory_mib=args.memory_mib,
                smp=args.smp,
                display="none",
                duration=args.duration,
                observation_timeout=args.observation_timeout,
                research_only=True,
            ))
            report["tcg_runtime"] = tcg_report
            try:
                handoff = _handoff_contract_for_tcg(tcg_report, target_major=args.target)
                report["checks"]["iboot_xnu_handoff"] = {
                    "passed": bool(handoff.get("valid")),
                    "report": handoff,
                }
                if not handoff.get("valid"):
                    report["errors"].append("iBoot/XNU handoff contract rejected TCG report")
                (output / "iboot-xnu-handoff.json").write_text(
                    json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            except (TypeError, ValueError, RuntimeError) as error:
                report["checks"]["iboot_xnu_handoff"] = {
                    "passed": False,
                    "error": f"{type(error).__name__}: {error}",
                }
                report["errors"].append("iBoot/XNU handoff contract rejected TCG report")
            tcg_check = {
                "passed": bool(tcg_report.get("tcg_runtime_started")) and bool(tcg_report.get("input_integrity")),
                # The VMApple runner's durable report is launch.json; keep
                # this path explicit so consumers do not mistake the outer
                # harness report for the guest-run evidence.
                "report": str(tcg_dir / "launch.json"),
            }
            report["checks"]["vmapple_tcg_runtime"] = tcg_check
            if not tcg_check["passed"]:
                report["errors"].append("VMApple TCG runtime did not start with intact inputs")
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
            report["tcg_runtime"] = {
                "passed": False, "error": f"{type(error).__name__}: {error}",
                "macos_boot_verified": False,
            }
            report["errors"].append(f"VMApple TCG runtime failed: {type(error).__name__}")
    elif not args.skip_tcg:
        report["tcg_runtime"] = {
            "passed": False,
            "blocked": "original firmware, qemu, qemu-img, and macosvm.json are required",
            "missing": contract["missing"],
            "macos_boot_verified": False,
        }

    efi_report = efi_step.get("report") if efi_step else None
    ovmf_report = ovmf_step.get("report") if ovmf_step else None
    report["layer_status"].update({
        "firmware_efi": _status_from_efi(efi_step, ovmf_step, "firmware_efi"),
        "rust_preos": _status_from_efi(efi_step, ovmf_step, "rust_preos"),
        "aarch64_jit": _status_from_efi(efi_step, ovmf_step, "aarch64_jit"),
        "native_machine": (
            "partial" if report["checks"].get("vmapple_tcg_contract", {}).get("passed")
            else "blocked"
        ),
        "apple_boot_chain": "not-attempted",
        "macos": "not-attempted",
    })
    del efi_report, ovmf_report  # names kept above for readability while assembling statuses
    tcg = report.get("tcg_runtime")
    if isinstance(tcg, dict):
        boot_chain = tcg.get("boot_chain_evidence")
        if not isinstance(boot_chain, dict):
            # Current and older runners place this under direct observation;
            # accept both shapes without upgrading a missing marker.
            direct = tcg.get("direct_boot")
            observation = direct.get("observation") if isinstance(direct, dict) else None
            boot_chain = observation.get("boot_chain_evidence") if isinstance(observation, dict) else None
        full_chain = bool(
            isinstance(boot_chain, dict)
            and boot_chain.get("iboot_to_xnu_handoff_verified")
            and boot_chain.get("xnu_to_userspace_handoff_verified")
            and boot_chain.get("xnu_executed")
            and boot_chain.get("macos_userspace_reached")
            and boot_chain.get("guest_target_match")
        )
        report["full_iboot_xnu_userspace_chain_verified"] = full_chain
        if full_chain:
            report["layer_status"]["apple_boot_chain"] = "runtime-tested"
        elif tcg.get("tcg_runtime_started"):
            report["layer_status"]["apple_boot_chain"] = "blocked"
        report["macos_boot_verified"] = bool(tcg.get("macos_boot_verified"))
        report["layer_status"]["macos"] = "runtime-tested" if report["macos_boot_verified"] else "blocked"
    elif not contract["runnable"] and not args.skip_tcg:
        report["layer_status"]["apple_boot_chain"] = "blocked"
        report["layer_status"]["macos"] = "blocked"

    report["passed"] = (
        not report["errors"]
        and report["layer_status"]["firmware_efi"] in {"passed", "not-attempted"}
        and report["layer_status"]["rust_preos"] in {"passed", "not-attempted"}
        and report["layer_status"]["aarch64_jit"] in {"passed", "not-attempted"}
    )
    if args.require_tcg and (
        not isinstance(tcg, dict)
        or tcg.get("tcg_runtime_started") is not True
        or tcg.get("input_integrity") is not True
    ):
        report["passed"] = False
        report["errors"].append("required TCG runtime did not start")
    if args.require_macos and not report["macos_boot_verified"]:
        report["passed"] = False
        report["errors"].append("required target-matching macOS boot evidence was not observed")
    report["output"] = str(output)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new evidence directory")
    parser.add_argument("--target", type=int, choices=[26, 27], default=27)
    parser.add_argument("--qemu", help="patched qemu-system-aarch64 binary")
    parser.add_argument("--qemu-img", help="qemu-img used to create COW overlays")
    parser.add_argument("--firmware", help="original caller-supplied AVPBooter binary")
    parser.add_argument("--vm-json", help="caller-supplied macosvm.json bundle descriptor")
    parser.add_argument("--memory-mib", type=int, default=4096)
    parser.add_argument("--smp", type=int, default=2)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--observation-timeout", type=float, default=60.0)
    parser.add_argument("--efi-timeout", type=float, default=900.0)
    parser.add_argument("--synthetic-timeout", type=float, default=300.0)
    parser.add_argument("--skip-contracts", action="store_true")
    parser.add_argument("--skip-efi", action="store_true")
    parser.add_argument("--skip-ovmf", action="store_true")
    parser.add_argument("--skip-tcg", action="store_true")
    parser.add_argument("--run-synthetic", action="store_true")
    parser.add_argument("--require-tcg", action="store_true")
    parser.add_argument("--require-macos", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = verify(args)
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"passed": False, "error": f"{type(error).__name__}: {error}"}, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.require_macos and not report.get("macos_boot_verified"):
        return 3
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
