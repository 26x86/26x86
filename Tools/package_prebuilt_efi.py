#!/usr/bin/env python3
"""Build and verify the mandatory source-pinned website EFI archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import zipfile


FILES = {"EFI/BOOT/BOOTX64.EFI", "diagnostics/NXARMJIT.efi", "EFI/OC/config.plist", "README.txt", "manifest.json"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pe_validate(data):
    if len(data) < 512 or data[:2] != b"MZ":
        raise ValueError("not a complete PE executable")
    pe = struct.unpack_from("<I", data, 60)[0]
    if pe < 64 or pe + 24 > len(data) or data[pe:pe+4] != b"PE\0\0":
        raise ValueError("invalid PE signature")
    machine, sections = struct.unpack_from("<HH", data, pe + 4)
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    if machine != 0x8664 or not 0 < sections <= 96 or optional_size < 112 or opt + optional_size + sections*40 > len(data):
        raise ValueError("invalid AMD64 PE layout")
    if struct.unpack_from("<H", data, opt)[0] != 0x20b or struct.unpack_from("<H", data, opt+68)[0] != 10:
        raise ValueError("not a PE32+ EFI application")
    entry = struct.unpack_from("<I", data, opt+16)[0]
    executable_entry = False
    for index in range(sections):
        section = opt + optional_size + index*40
        virtual_size, address, size, offset = struct.unpack_from("<IIII", data, section+8)
        flags = struct.unpack_from("<I", data, section+36)[0]
        if size and (offset == 0 or offset+size > len(data)):
            raise ValueError("truncated PE section")
        if flags & 0x20000000 and address <= entry < address + min(virtual_size, size):
            executable_entry = True
    if not entry or not executable_entry:
        raise ValueError("entry point is not backed by executable bytes")


def verify_archive(path, expected_commit):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(FILES) or set(names) != FILES or archive.testzip() is not None:
            raise ValueError("unexpected ZIP inventory or CRC")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest["source_commit"] != expected_commit or set(manifest["files"]) != FILES - {"manifest.json"}:
            raise ValueError("manifest identity or inventory mismatch")
        for name, record in manifest["files"].items():
            data = archive.read(name)
            if record != {"sha256": sha(data), "size": len(data)}:
                raise ValueError("ZIP content digest mismatch: " + name)
            if name.lower().endswith(".efi"):
                pe_validate(data)
        config = plistlib.loads(archive.read("EFI/OC/config.plist"))
        if config != {"Misc": {"Boot": {"ShowPicker": True}, "Entries": []}}:
            raise ValueError("package must not select a guest or disk automatically")
        if manifest["normal_startup"] != "NOT_READY" or manifest["physical_desktop_verified"] is not False:
            raise ValueError("invalid readiness claim")
    return manifest


def run(command, cwd=None, env=None, timeout=1800):
    return subprocess.check_output(command, cwd=cwd, env=env, text=True, timeout=timeout).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--target-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    revision = spec["source_commit"]
    if not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("source pin must be a full immutable Git SHA")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", spec["rust_toolchain"]):
        raise ValueError("toolchain must be an exact release version")
    if spec["target"] != "x86_64-unknown-uefi" or spec["archive"] != "prebuiltefi.zip":
        raise ValueError("unsupported package contract")
    args.output = args.output.resolve()
    if args.verify_only:
        verify_archive(args.output, revision)
        sidecar = json.loads(args.output.with_suffix(".json").read_text())
        if sidecar["sha256"] != sha(args.output.read_bytes()) or sidecar["source_commit"] != revision or sidecar["size"] != args.output.stat().st_size:
            raise ValueError("archive sidecar mismatch")
        print("Verified source-pinned prebuiltefi.zip")
        return
    if args.source is None or args.target_dir is None:
        parser.error("build requires --source and --target-dir")
    source = args.source.resolve()
    if run(["git", "rev-parse", "HEAD"], source) != revision:
        raise ValueError("runtime checkout does not match source pin")
    if run(["git", "status", "--porcelain", "--untracked-files=all"], source):
        raise ValueError("runtime checkout must be clean")
    submodules = run(["git", "submodule", "status", "--recursive"], source)
    # Preserve the leading status character: check each expected module explicitly.
    raw = subprocess.check_output(["git", "submodule", "status", "--recursive"], cwd=source, text=True)
    if not raw.strip() or any(line[0] != " " for line in raw.splitlines()):
        raise ValueError("submodules missing or different from pinned gitlinks")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("NEXTCORE_", "CARGO_", "RUSTFLAGS"))}
    env["CARGO_TARGET_DIR"] = str(args.target_dir.resolve())
    cargo = ["cargo", "+" + spec["rust_toolchain"]]
    rustc = run(["rustc", "+" + spec["rust_toolchain"], "--version"], env=env)
    binaries = {}
    commands = []
    for name, features, destination in [("BOOTX64", [], "EFI/BOOT/BOOTX64.EFI"),
            ("NXARMJIT", spec["diagnostic_features"], "diagnostics/NXARMJIT.efi")]:
        command = cargo + ["build", "--locked", "--release", "--target", spec["target"],
                           "-p", "nextcore-efi", "--bin", name, "--no-default-features"]
        if features:
            command += ["--features", ",".join(features)]
        run(command, source / "nextcore", env)
        commands.append(command)
        data = (args.target_dir.resolve() / spec["target"] / "release" / (name + ".efi")).read_bytes()
        pe_validate(data)
        binaries[destination] = data
    if run(["git", "status", "--porcelain", "--untracked-files=all"], source):
        raise ValueError("build modified the source checkout")
    binaries["EFI/OC/config.plist"] = plistlib.dumps({"Misc": {"Boot": {"ShowPicker": True}, "Entries": []}})
    binaries["README.txt"] = ("""NextCore prebuilt EFI development package

Normal macOS startup: NOT_READY. Physical desktop boot: UNVERIFIED.
Compilation and archive validation do not prove firmware compatibility or macOS boot.

EFI/BOOT/BOOTX64.EFI is the baseline x86_64 UEFI application, built without
selected diagnostic features. EFI/OC/config.plist is its public configuration
path. The supplied empty configuration selects no guest; the baseline displays
the configuration recovery screen. Enter retries this same configuration and
Esc returns to firmware with NOT_FOUND. Required display or input failures return
their actual error. Supply a deliberate, supported entry configuration before
attempting a target; this package cannot install macOS.

Use a separate FAT-formatted removable test volume. The EFI directory is relative
to that volume's root. Preserve your existing system EFI and recovery path; this
archive performs no installation or NVRAM changes. It contains no Apple payload.

diagnostics/NXARMJIT.efi is a separate mapped ARM execution diagnostic, NOT the
normal boot entry. Do not rename it BOOTX64.EFI. Launch it explicitly only with an
authored or locally supplied configuration accepted by the pinned trace contract.
The diagnostic requires its own kernel/DeviceTree/configuration, which are not
included here. Profile selection is not evidence of an original-image entry ABI.

Source pin, exact submodules, commands, tools and per-file hashes: manifest.json.
Archive download hash: prebuiltefi.json beside the ZIP on the website.
Public diagnostic documentation: https://26x86.github.io/26x86/PREFIX_PROGRESS_VALIDATION/
""" + "\nSource commit: " + revision + "\n").encode()
    manifest = dict(schema=1, source_commit=revision, source_repository=spec["source_repository"],
                    submodules=submodules, commands=commands, rustc=rustc,
                    clang=run(["clang", "--version"]).splitlines()[0],
                    normal_startup="NOT_READY", physical_desktop_verified=False,
                    files={name: {"sha256": sha(data), "size": len(data)} for name, data in binaries.items()})
    binaries["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(binaries.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    verify_archive(args.output, revision)
    args.output.with_suffix(".json").write_text(json.dumps(dict(schema=1, source_commit=revision,
        sha256=sha(args.output.read_bytes()), size=args.output.stat().st_size,
        normal_startup="NOT_READY", physical_desktop_verified=False), indent=2) + "\n")
    print("Built and verified " + str(args.output))


if __name__ == "__main__":
    main()
