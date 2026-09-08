#!/usr/bin/env python3
"""Build the pinned native EFI runtime and replay sixteen authored cases."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_repo(bundle: Path) -> Path | None:
    for parent in bundle.parents:
        if (parent / "nextcore/Cargo.toml").is_file() and (parent / ".gitmodules").is_file():
            return parent
    return None


def main() -> int:
    bundle = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=find_repo(bundle), help="parent repository; inferred when installed in its artifacts")
    parser.add_argument("--output", type=Path, required=True, help="fresh persistent build/evidence directory")
    parser.add_argument("--runtime-checkout", type=Path, help="optional isolated checkout of the same pinned ISE commit")
    parser.add_argument("--efi", type=Path, help="reuse the recorded historical binary, verifying its SHA256")
    args = parser.parse_args()
    if args.repo is None:
        parser.error("--repo is required outside the parent repository")
    repo = args.repo.resolve(strict=True)
    runtime = (args.runtime_checkout or repo / "nextcore/crates/nextcore-ise").resolve(strict=True)
    provenance = json.loads((bundle / "provenance.json").read_text())
    head = subprocess.check_output(["git", "-C", str(runtime), "rev-parse", "HEAD"], text=True).strip()
    if head != provenance["runtime_revision"]:
        parser.error("ISE checkout must match the immutable runtime_revision in provenance.json")
    for relative, expected in provenance["runtime_source_sha256"].items():
        if sha256(runtime / relative) != expected:
            parser.error(f"ISE runtime source changed: {relative}")
    if sha256(bundle / "arm64_pair_probe.S") != provenance["authored_fixture_sha256"]:
        parser.error("authored fixture changed")
    for tool in ["clang", "llvm-ar", "llvm-objcopy", "llvm-nm", "qemu-system-x86_64"]:
        if shutil.which(tool) is None:
            parser.error(f"required executable missing: {tool}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                   "NEXTCORE_PREOS_RUNTIME": str(runtime / "runtime"),
                   "CARGO_TARGET_DIR": str(output / "target")}
    commands = []

    def run(label: str, command: list[str]) -> None:
        commands.append({"label": label, "argv": command})
        (output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        print(label, flush=True)
        with (output / f"{label}.log").open("w") as log:
            subprocess.run(command, cwd=repo, env=environment, stdout=log,
                           stderr=subprocess.STDOUT, check=True)

    if args.efi:
        efi = args.efi.resolve(strict=True)
        if sha256(efi) != provenance["efi_sha256"]:
            parser.error("--efi must match the recorded historical binary; omit it to rebuild")
    else:
        cargo = shutil.which("cargo") or str(Path.home() / ".cargo/bin/cargo")
        run("build", [cargo, "build", "--locked", "--release", "--manifest-path",
                      str(repo / "nextcore/Cargo.toml"), "-p", "nextcore-efi", "--bin", "NXARMJIT",
                      "--target", "x86_64-unknown-uefi", "--features", "arm-jit-probe,arm-jit-trace"])
        efi = output / "target/x86_64-unknown-uefi/release/NXARMJIT.efi"
    tools = repo / "nextcore/tools"
    run("pair", [sys.executable, str(bundle / "verify_pair_ovmf.py"), "--efi", str(efi),
                 "--tools", str(tools), "--output", str(output / "pair")])
    run("platform", [sys.executable, str(tools / "verify_arm_platform_irq_ovmf.py"),
                     "--efi", str(efi), "--output", str(output / "platform")])
    run("pac-gop", [sys.executable, str(tools / "verify_arm_jit_ovmf.py"), "--efi-probe", str(efi),
                    "--efi-default", str(efi), "--output", str(output / "pac-gop"),
                    "--cases", "jit-positive,arm64e-pac-positive"])
    suites = {name: json.loads((output / name / "report.json").read_text())
              for name in ["pair", "platform", "pac-gop"]}
    preserved = all(sha256(runtime / path) == digest
                    for path, digest in provenance["runtime_source_sha256"].items())
    report = {"schema": "nextcore.bp28-replay.v1", "runtime_revision": head,
              "efi_sha256": sha256(efi), "case_count": sum(len(r["cases"]) for r in suites.values()),
              "runtime_sources_preserved": preserved,
              "passed": preserved and all(r["passed"] for r in suites.values()),
              "macos_boot_verified": False, "metal_verified": False}
    report["passed"] = report["passed"] and report["case_count"] == 16
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
