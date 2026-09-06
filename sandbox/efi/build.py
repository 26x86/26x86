#!/usr/bin/env python3
"""Build freestanding x64 UEFI binaries with clang/lld (Linux/macOS/WSL)."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
BUILD = ROOT / "build"


def main():
    BUILD.mkdir(exist_ok=True)
    flags = ["--target=x86_64-pc-win32-coff", "-std=c11", "-ffreestanding",
             "-fshort-wchar", "-fno-stack-protector", "-fno-builtin", "-mno-red-zone",
             "-mno-avx", "-mno-avx2", "-msse4.2", "-O2", "-Wall", "-Wextra", "-Werror"]
    for name, test in [("BOOTX64.EFI", False), ("TESTX64.EFI", True)]:
        objects = []
        for source in ["jit.c", "main.c", "../devices/aic_v1.c"]:
            obj = BUILD / (name + "." + pathlib.Path(source).name + ".obj")
            subprocess.run(["clang", *flags, *( ["-DVF_QEMU_TEST"] if test else []),
                            "-c", str(ROOT / source), "-o", str(obj)], check=True)
            objects.append(str(obj))
        subprocess.run(["lld-link", "/subsystem:efi_application", "/entry:efi_main",
                        "/nodefaultlib", "/machine:x64", "/dynamicbase", "/nxcompat", "/timestamp:0",
                        "/out:" + str(BUILD / name), *objects], check=True)
    subprocess.run(["clang", "-D_GNU_SOURCE", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-msse4.2", "-mno-avx", str(ROOT / "jit.c"), str(ROOT / "test_jit.c"),
                    "-o", str(BUILD / "test-jit")], check=True)
    native = json.loads(subprocess.check_output([str(BUILD / "test-jit")], text=True))
    report = {"schema": 1, "artifact": "BOOTX64.EFI", "kind": "efi-native-a64-subset-jit",
              "sha256": hashlib.sha256((BUILD / "BOOTX64.EFI").read_bytes()).hexdigest(),
              "bytes": (BUILD / "BOOTX64.EFI").stat().st_size,
              "minimum_cpu": ["x86_64", "sse4.1", "sse4.2"], "avx_required": False,
              "capabilities": ["native-a64-subset-jit", "bounded-guest-ram", "instruction-budget",
                               "uefi-memory-attribute-wx", "raw-own-code-guest", "aic_v1_wired_model"],
              "native_unit": native, "macos_boot_verified": False,
              "iboot_supported": False, "aic_supported": False,
              "opencore_handoff_version": 1,
              "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(ROOT.iterdir()) if p.suffix in {".c", ".h", ".py"}},
              "device_source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted((ROOT.parent / "devices").glob("aic_v1.*"))},
              "firmware_requirement": "EFI_MEMORY_ATTRIBUTE_PROTOCOL or EFI_CPU_ARCH_PROTOCOL with verified CR0.WP/EFER.NXE and RW/NX page permissions",
              "compiler": subprocess.check_output(["clang", "--version"], text=True).splitlines()[0]}
    (BUILD / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
