#!/usr/bin/env python3
"""Build and audit the single-image EFI-integrated Rust micro-preOS gate."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BUILD = ROOT / "build"
PREOS = ROOT / "preos"
EFI_RUST_TARGET = "x86_64-pc-windows-msvc"


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_output(command):
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


def cargo_target_present():
    installed = subprocess.check_output(["rustup", "target", "list", "--installed"], text=True)
    if EFI_RUST_TARGET not in installed.splitlines():
        raise RuntimeError(
            f"Rust target {EFI_RUST_TARGET} is required; run: rustup target add {EFI_RUST_TARGET}"
        )


def build_rust_staticlibs():
    cargo_target_present()
    run(["cargo", "test", "--manifest-path", str(PREOS / "Cargo.toml")])
    host_target = BUILD / "cargo-host"
    efi_target = BUILD / "cargo-efi"
    run([
        "cargo", "build", "--manifest-path", str(PREOS / "Cargo.toml"), "--release",
        "--target-dir", str(host_target),
    ])
    run([
        "cargo", "build", "--manifest-path", str(PREOS / "Cargo.toml"), "--target", EFI_RUST_TARGET,
        "--release", "--target-dir", str(efi_target),
    ])
    host_staticlib = host_target / "release" / "libvenfire_preos.a"
    efi_staticlib = efi_target / EFI_RUST_TARGET / "release" / "venfire_preos.lib"
    if not host_staticlib.is_file() or not efi_staticlib.is_file():
        raise RuntimeError("Cargo did not emit the expected no_std static libraries")
    return host_staticlib, efi_staticlib


def validate_machine_contract():
    return json_output([
        sys.executable, str(ROOT / "verify_m1_machine_contract.py"), "--compact",
    ])


def build_efi(staticlib):
    flags = [
        "--target=x86_64-pc-win32-coff", "-DVF_EFI_BUILD", "-std=c11", "-ffreestanding",
        "-fshort-wchar", "-fno-stack-protector", "-fno-builtin", "-mno-red-zone", "-mno-avx",
        "-mno-avx2", "-msse4.2", "-O2", "-Wall", "-Wextra", "-Werror",
    ]
    sources = ["jit.c", "main.c", "preos_bridge.c", "../devices/aic_v1.c"]
    outputs = []
    for name, test in [("BOOTX64.EFI", False), ("TESTX64.EFI", True)]:
        objects = []
        for source in sources:
            obj = BUILD / (name + "." + pathlib.Path(source).name + ".obj")
            run([
                "clang", *flags, *(["-DVF_QEMU_TEST"] if test else []), "-c", str(ROOT / source),
                "-o", str(obj),
            ])
            objects.append(str(obj))
        map_file = BUILD / (name + ".map")
        output = BUILD / name
        run([
            "lld-link", "/subsystem:efi_application", "/entry:efi_main", "/nodefaultlib", "/machine:x64",
            "/dynamicbase", "/nxcompat", "/timestamp:0", "/map:" + str(map_file),
            "/out:" + str(output), *objects, str(staticlib),
        ])
        outputs.append((output, map_file))
    return outputs


def build_native_tests(host_staticlib):
    # Keep the existing C JIT regression distinct from the C/Rust integration
    # test: a bridge failure should not be reported as a translator regression.
    run([
        "clang", "-D_GNU_SOURCE", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-msse4.2",
        "-mno-avx", str(ROOT / "jit.c"), str(ROOT / "test_jit.c"), "-o", str(BUILD / "test-jit"),
    ])
    native = json_output([str(BUILD / "test-jit")])
    run([
        "clang", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-msse4.2", "-mno-avx",
        str(ROOT / "jit.c"), str(ROOT / "preos_bridge.c"), str(ROOT / "preos_host_test.c"),
        str(host_staticlib), "-o", str(BUILD / "test-preos"),
    ])
    ffi = json_output([str(BUILD / "test-preos")])
    return native, ffi


def audit_linked_image(image, map_file):
    forbidden = [b"rust_eh_personality", b"rust_begin_unwind", b"_Unwind_", b"__rust_alloc", b"__rdl_"]
    image_bytes = image.read_bytes()
    map_bytes = map_file.read_bytes()
    found = [token.decode("ascii") for token in forbidden if token in image_bytes or token in map_bytes]
    if found:
        raise RuntimeError(f"forbidden Rust unwind/allocator symbol(s) linked into EFI: {found}")
    return {
        "passed": True,
        "forbidden_symbols": [token.decode("ascii") for token in forbidden],
        "found": found,
        "scope": "linked EFI image and lld-link map; archive-only unused objects are excluded",
    }


def source_hashes():
    paths = [
        ROOT / "jit.c", ROOT / "jit.h", ROOT / "main.c", ROOT / "uefi.h", ROOT / "handoff.h",
        ROOT / "preos_abi.h", ROOT / "preos_bridge.h", ROOT / "preos_bridge.c", ROOT / "test_jit.c",
        ROOT / "preos_host_test.c", ROOT / "verify_ovmf.py", ROOT / "build.py",
        ROOT / "verify_m1_machine_contract.py", ROOT / "m1-machine-contract.json",
        PREOS / "Cargo.toml", PREOS / "Cargo.lock", PREOS / "src" / "lib.rs",
        PREOS / "src" / "machine.rs",
    ]
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def main():
    BUILD.mkdir(exist_ok=True)
    machine_contract = validate_machine_contract()
    host_staticlib, efi_staticlib = build_rust_staticlibs()
    native, ffi = build_native_tests(host_staticlib)
    artifacts = build_efi(efi_staticlib)
    production, production_map = artifacts[0]
    instrumented, instrumented_map = artifacts[1]
    baseline_path = ROOT / "phase0-baseline.json"
    baseline = json.loads(baseline_path.read_text())
    audit = audit_linked_image(production, production_map)
    test_audit = audit_linked_image(instrumented, instrumented_map)
    old_bytes = baseline["artifact"]["bytes"]
    report = {
        "schema": 2,
        "artifact": "BOOTX64.EFI",
        "kind": "efi-integrated-rust-preos-a64-subset-jit",
        "sha256": sha256(production),
        "bytes": production.stat().st_size,
        "minimum_cpu": ["x86_64", "sse4.1", "sse4.2"],
        "avx_required": False,
        "capabilities": [
            "rust-no_std-staticlib", "c-owned-uefi-lifecycle", "c-owned-jit-wx",
            "bounded-a64-diagnostic-guest", "m1-diagnostic-policy-seed",
            "phase2-vfmachine", "fixed-ram-region-registry", "static-mmio-registry",
            "machine-reset-hook", "unsupported-cpu-system-feature-gate",
        ],
        "native_unit": native,
        "rust_unit": {"passed": True, "runner": "cargo test --manifest-path sandbox/efi/preos/Cargo.toml"},
        "c_rust_abi_unit": ffi,
        "linked_image_audit": audit,
        "instrumented_image_audit": test_audit,
        "measurements": {
            "phase0_c_only_efi": baseline["artifact"],
            "rust_linked_efi": {"bytes": production.stat().st_size, "sha256": sha256(production)},
            "increase_bytes": production.stat().st_size - old_bytes,
            "separate_companion_executables": 0,
            "separate_rust_efi_images": 0,
            "separate_kernel_images": 0,
            "separate_os_boot_protocols": 0,
            "rust_static_library": {"path": str(efi_staticlib.relative_to(ROOT)), "bytes": efi_staticlib.stat().st_size},
            "fixed_guest_ram_bytes": 65536,
            "jit_code_buffer_bytes": 16384,
            "fixed_stack_requirement": "not measured",
            "rust_runtime_dynamic_allocation": {
                "count": 0,
                "bytes": 0,
                "evidence": "no_std crate with no alloc dependency/global allocator plus linked-image allocator-symbol audit",
                "runtime_measured": False,
            },
            "boot_services_allocations": {
                "value": "not measured during build",
                "runtime_evidence": "verify_ovmf.py parses VF: EFI_ALLOCATIONS markers",
            },
            "host_os_dependency": 0,
            "external_qemu_process_dependency": 0,
        },
        "machine_seed": {
            "profile": "VF_MACHINE_PROFILE_M1_DIAGNOSTIC",
            "ram_regions": 1,
            "mmio_regions": 0,
            "ram_registry_capacity": 4,
            "mmio_registry_capacity": 8,
            "reset_hook": "called before MACHINE_READY; topology preserved",
            "devices": "none (explicit; synthetic diagnostic MMIO covered by Rust unit test)",
            "guest_physical_address_space": "fixed 0x00000000..0x0000ffff RAM; overlap and overflow checked",
            "native_machine_layer": "phase-2 descriptor core implemented; M1 graph not claimed",
            "physical_m1_compatibility": False,
        },
        "cpu_system_capabilities": {
            "base_aarch64_subset": "runtime-tested",
            "exception_model": "explicitly unsupported and fail-closed",
            "privileged_state": "explicitly unsupported and fail-closed",
            "system_registers": "explicitly unsupported and fail-closed",
            "mmu": "explicitly unsupported and fail-closed",
            "tlb": "explicitly unsupported and fail-closed",
            "atomics": "explicitly unsupported and fail-closed",
            "smp": "explicitly unsupported and fail-closed",
            "timer_counter": "explicitly unsupported and fail-closed",
            "pauth": "explicitly unsupported and fail-closed",
        },
        "m1_machine_contract": machine_contract,
        "macos_boot_verified": False,
        "iboot_supported": False,
        "aic_supported": False,
        "opencore_handoff_version": 1,
        "source_sha256": source_hashes(),
        "device_source_sha256": {
            path.name: sha256(path) for path in sorted((ROOT.parent / "devices").glob("aic_v1.*"))
        },
        "firmware_requirement": "EFI_MEMORY_ATTRIBUTE_PROTOCOL or EFI_CPU_ARCH_PROTOCOL with verified CR0.WP/EFER.NXE and RW/NX page permissions",
        "rust_target": EFI_RUST_TARGET,
        "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip(),
        "compiler": subprocess.check_output(["clang", "--version"], text=True).splitlines()[0],
        "instrumented_artifact": {"sha256": sha256(instrumented), "bytes": instrumented.stat().st_size},
    }
    (BUILD / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
