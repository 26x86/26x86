#!/usr/bin/env python3
"""Build and audit the single-image EFI-integrated Rust micro-preOS gate."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import re

ROOT = pathlib.Path(__file__).resolve().parent
BUILD = ROOT / "build"
PREOS = ROOT / "preos"
EFI_RUST_TARGET = "x86_64-pc-windows-msvc"


def tool(name):
    """Resolve native or Windows Rust tools without changing the build model.

    The EFI build is normally run on Windows, where the unsuffixed names are
    correct.  WSL can still drive the same Windows Rust toolchain, but the
    binaries are exposed as ``*.exe``.  Environment overrides keep CI and
    cross-toolchain invocations explicit rather than relying on PATH order.
    """
    override = os.environ.get(f"VENFIRE_{name.upper()}_BIN")
    if override:
        return override
    return shutil.which(name) or shutil.which(f"{name}.exe") or name


CARGO = tool("cargo")
RUSTC = tool("rustc")
RUSTUP = tool("rustup")
HOST_RUST_TARGET = os.environ.get("VENFIRE_HOST_RUST_TARGET")


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


_MAP_SECTION = re.compile(
    r"^\s*(?P<segment>[0-9A-Fa-f]{4}):(?P<offset>[0-9A-Fa-f]{8})\s+"
    r"(?P<length>[0-9A-Fa-f]+)H\s+(?P<name>\S+)\s+(?P<class>\S+)\s*$"
)


def map_section_measurements(map_file):
    """Return measured linker section lengths from an lld map file.

    The PE file size includes alignment and headers, so it is not useful to
    infer code/data footprint by subtraction alone.  lld emits the authoritative
    section lengths in the map; parsing those keeps this report measurement-only
    and avoids presenting estimates as allocations.
    """
    sections = {}
    for line in map_file.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _MAP_SECTION.match(line)
        if not match:
            continue
        name = match.group("name")
        sections[name] = {
            "bytes": int(match.group("length"), 16),
            "segment": match.group("segment"),
            "class": match.group("class"),
        }
    if not sections:
        raise RuntimeError(f"linker map contains no section measurements: {map_file}")
    return sections


def footprint_measurement(image, map_file, baseline_artifact):
    """Build a concrete image/section footprint receipt."""
    sections = map_section_measurements(map_file)
    baseline_bytes = baseline_artifact.get("bytes")
    return {
        "baseline_efi_bytes": baseline_bytes if isinstance(baseline_bytes, int) else "unknown",
        "linked_efi_bytes": image.stat().st_size,
        "growth_bytes": (image.stat().st_size - baseline_bytes)
        if isinstance(baseline_bytes, int) else "unknown",
        "linker_sections": sections,
        "section_total_bytes": sum(item["bytes"] for item in sections.values()),
        "measurement_source": "lld-link map section table plus filesystem stat",
    }


def json_output(command):
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


def captured(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def rust_layout_receipt(output):
    prefix = "VF_ABI_LAYOUT "
    receipts = [line[len(prefix):] for line in output.splitlines() if line.startswith(prefix)]
    if len(receipts) != 1:
        raise RuntimeError("Rust ABI layout test did not emit exactly one receipt")
    try:
        return json.loads(receipts[0])
    except json.JSONDecodeError as error:
        raise RuntimeError("Rust ABI layout receipt is not JSON") from error


def cargo_target_present():
    installed = subprocess.check_output([RUSTUP, "target", "list", "--installed"], text=True)
    if EFI_RUST_TARGET not in installed.splitlines():
        raise RuntimeError(
            f"Rust target {EFI_RUST_TARGET} is required; run: {RUSTUP} target add {EFI_RUST_TARGET}"
        )


def build_rust_staticlibs():
    cargo_target_present()
    tests = captured([
        CARGO, "test", "--manifest-path", str(PREOS / "Cargo.toml"), "--", "--nocapture",
    ])
    rust_layout = rust_layout_receipt(tests.stdout + tests.stderr)
    host_target = BUILD / ("cargo-linux" if HOST_RUST_TARGET else "cargo-host")
    efi_target = BUILD / "cargo-efi"
    host_target_args = ["--target", HOST_RUST_TARGET] if HOST_RUST_TARGET else []
    run([
        CARGO, "build", "--manifest-path", str(PREOS / "Cargo.toml"), "--release",
        *host_target_args,
        "--target-dir", str(host_target),
    ])
    run([
        CARGO, "build", "--manifest-path", str(PREOS / "Cargo.toml"), "--target", EFI_RUST_TARGET,
        "--release", "--target-dir", str(efi_target),
    ])
    host_release = host_target / HOST_RUST_TARGET / "release" if HOST_RUST_TARGET else host_target / "release"
    host_staticlib = host_release / "libvenfire_preos.a"
    efi_staticlib = efi_target / EFI_RUST_TARGET / "release" / "venfire_preos.lib"
    if not host_staticlib.is_file() or not efi_staticlib.is_file():
        raise RuntimeError("Cargo did not emit the expected no_std static libraries")
    return host_staticlib, efi_staticlib, rust_layout


def validate_machine_contract():
    return json_output([
        sys.executable, str(ROOT / "verify_m1_machine_contract.py"), "--compact",
    ])


def validate_vmapple_tcg_contract():
    return json_output([
        sys.executable, str(ROOT / "verify_vmapple_tcg_contract.py"), "--compact",
    ])


def validate_vmapple_tcg_source_manifest():
    return json_output([
        sys.executable, str(ROOT / "verify_vmapple_tcg_source_manifest.py"), "--compact",
    ])


def validate_iboot_xnu_handoff_contract():
    """Validate the report-only iBoot -> XNU contract at build time.

    This is an Apple boot-chain contract check, not a boot attempt.  Keeping
    it in the EFI receipt prevents a future build from silently dropping the
    causal evidence gate while still leaving the actual firmware and guest
    inputs caller-owned.
    """
    contract = ROOT / "iboot-xnu-handoff-contract.json"
    if not contract.is_file():
        raise RuntimeError(f"missing iBoot/XNU handoff contract: {contract}")
    document = json.loads(contract.read_text(encoding="utf-8"))
    if document.get("schema") != "26x86.iboot-xnu-handoff/1":
        raise RuntimeError("unexpected iBoot/XNU handoff contract schema")
    if document.get("machine_type") != "iBoot(AArch64)" or document.get("guest_os") != "macOS":
        raise RuntimeError("iBoot/XNU contract must remain macOS-only iBoot(AArch64)")
    if document.get("target_majors") != [26, 27]:
        raise RuntimeError("iBoot/XNU contract must pin macOS target majors 26 and 27")
    safety = document.get("safety")
    if not isinstance(safety, dict) or any(safety.get(key) is not False for key in (
        "allows_synthetic_success", "allows_input_mutation",
        "allows_transport_as_signature_acceptance", "allows_iBoot_panic_as_xnu",
    )):
        raise RuntimeError("iBoot/XNU safety contract was relaxed")
    return {
        "schema": document["schema"],
        "machine_type": document["machine_type"],
        "guest_os": document["guest_os"],
        "target_majors": document["target_majors"],
        "direct_stage_count": len(document.get("direct_stages", [])),
        "recovery_stage_count": len(document.get("recovery_stages", [])),
        "safety": safety,
        "valid": True,
    }


def build_efi(staticlib):
    flags = [
        "--target=x86_64-pc-win32-coff", "-DVF_EFI_BUILD", "-std=c11", "-ffreestanding",
        "-fshort-wchar", "-fno-stack-protector", "-fno-builtin", "-mno-red-zone", "-mno-avx",
        "-mno-avx2", "-msse4.2", "-O2", "-Wall", "-Wextra", "-Werror",
    ]
    sources = ["jit.c", "arch.c", "main.c", "preos_bridge.c", "../devices/aic_v1.c"]
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
        "-mno-avx", str(ROOT / "jit.c"), str(ROOT / "arch.c"), str(ROOT / "test_jit.c"), "-o", str(BUILD / "test-jit"),
    ])
    native = json_output([str(BUILD / "test-jit")])
    run([
        "clang", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-msse4.2", "-mno-avx",
        str(ROOT / "jit.c"), str(ROOT / "arch.c"), str(ROOT / "preos_bridge.c"), str(ROOT / "preos_host_test.c"),
        str(host_staticlib), "-o", str(BUILD / "test-preos"),
    ])
    ffi = json_output([str(BUILD / "test-preos")])
    run([
        "clang", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        str(ROOT / "abi_layout.c"), "-o", str(BUILD / "test-abi-layout"),
    ])
    abi = json_output([str(BUILD / "test-abi-layout")])
    run([
        "clang", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        str(ROOT / "test_wx.c"), "-o", str(BUILD / "test-wx"),
    ])
    wx = json_output([str(BUILD / "test-wx")])
    return native, ffi, abi, wx


def build_aic_test():
    """Exercise the first-party AIC model linked into the EFI image.

    This is a standalone device-model test, not M1 hardware evidence.  The
    EFI entry runs the same model's bounded self-test, while this process
    covers reset, masking, level reassertion, affinity, and bounds without
    requiring an Apple device tree.
    """
    run([
        "clang", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        str(ROOT.parent / "devices" / "aic_v1.c"),
        str(ROOT.parent / "devices" / "test_aic.c"),
        "-o", str(BUILD / "test-aic"),
    ])
    result = captured([str(BUILD / "test-aic")])
    expected = "PASS AIC v1 wired IRQ"
    if expected not in result.stdout:
        raise RuntimeError(f"AIC model test did not emit its pass marker: {result.stdout!r}")
    return {
        "passed": True,
        "stdout": result.stdout.strip(),
        "scope": "standalone AIC v1 model; no M1 device-tree or physical hardware claim",
    }


def compare_abi_layout(c_layout, rust_layout):
    if c_layout != rust_layout:
        raise RuntimeError(
            "C/Rust ABI layout mismatch:\n"
            + json.dumps({"c": c_layout, "rust": rust_layout}, indent=2)
        )
    return {
        "passed": True,
        "values": c_layout,
        "evidence": "C abi_layout.c receipt exactly matched Rust #[repr(C)] unit-test receipt",
        "deployment_executable_count": 0,
    }


def audit_linked_image(image, map_file):
    # `rust_begin_unwind` is the symbol name emitted for a no_std panic
    # handler even when both profiles use `panic = "abort"`.  Its presence is
    # not evidence of an unwind runtime; the actual cross-boundary/unwind and
    # allocator symbols remain forbidden below.
    forbidden = [b"rust_eh_personality", b"_Unwind_", b"__rust_alloc", b"__rdl_"]
    allowed_abort_handler = b"rust_begin_unwind"
    image_bytes = image.read_bytes()
    map_bytes = map_file.read_bytes()
    found = [token.decode("ascii") for token in forbidden if token in image_bytes or token in map_bytes]
    if found:
        raise RuntimeError(f"forbidden Rust unwind/allocator symbol(s) linked into EFI: {found}")
    return {
        "passed": True,
        "forbidden_symbols": [token.decode("ascii") for token in forbidden],
        "found": found,
        "allowed_abort_handler": allowed_abort_handler.decode("ascii")
        if allowed_abort_handler in image_bytes or allowed_abort_handler in map_bytes
        else None,
        "scope": "linked EFI image and lld-link map; archive-only unused objects are excluded",
    }


def source_hashes():
    paths = [
        ROOT / "jit.c", ROOT / "jit.h", ROOT / "arch.c", ROOT / "main.c", ROOT / "uefi.h", ROOT / "handoff.h",
        ROOT / "preos_abi.h", ROOT / "preos_bridge.h", ROOT / "preos_bridge.c", ROOT / "test_jit.c",
        ROOT / "preos_host_test.c", ROOT / "abi_layout.c", ROOT / "test_wx.c", ROOT / "verify_ovmf.py", ROOT / "build.py",
        ROOT / "verify_m1_machine_contract.py", ROOT / "m1-machine-contract.json",
        ROOT / "verify_vmapple_tcg_contract.py", ROOT / "vmapple-tcg-machine-contract.json",
        ROOT / "verify_vmapple_tcg_source_manifest.py", ROOT / "vmapple-tcg-source-port-manifest.json",
        ROOT / "iboot-xnu-handoff-contract.json", ROOT / "verify_iboot_xnu_handoff.py",
        PREOS / "Cargo.toml", PREOS / "Cargo.lock", PREOS / "src" / "lib.rs",
        PREOS / "src" / "machine.rs",
        PREOS / "src" / "arch.rs",
        PREOS / "src" / "mmu.rs",
        PREOS / "src" / "m1.rs",
        PREOS / "src" / "vmapple.rs",
    ]
    patch_root = ROOT.parent.parent / "research" / "venfire" / "patches"
    series = patch_root / "series"
    paths.append(series)
    for name in series.read_text(encoding="utf-8").splitlines():
        name = name.strip()
        if name and not name.startswith("#"):
            paths.append(patch_root / name)
    result = {}
    repository_root = ROOT.parent.parent
    for path in paths:
        try:
            label = path.relative_to(ROOT)
        except ValueError:
            label = path.relative_to(repository_root)
        result[str(label)] = sha256(path)
    return result


def main():
    BUILD.mkdir(exist_ok=True)
    machine_contract = validate_machine_contract()
    vmapple_tcg_contract = validate_vmapple_tcg_contract()
    vmapple_tcg_source_manifest = validate_vmapple_tcg_source_manifest()
    iboot_xnu_handoff_contract = validate_iboot_xnu_handoff_contract()
    host_staticlib, efi_staticlib, rust_layout = build_rust_staticlibs()
    native, ffi, c_layout, wx = build_native_tests(host_staticlib)
    aic = build_aic_test()
    abi_layout = compare_abi_layout(c_layout, rust_layout)
    artifacts = build_efi(efi_staticlib)
    production, production_map = artifacts[0]
    instrumented, instrumented_map = artifacts[1]
    baseline_path = ROOT / "phase0-baseline.json"
    baseline = json.loads(baseline_path.read_text())
    audit = audit_linked_image(production, production_map)
    test_audit = audit_linked_image(instrumented, instrumented_map)
    old_bytes = baseline["artifact"]["bytes"]
    production_footprint = footprint_measurement(production, production_map, baseline["artifact"])
    instrumented_footprint = footprint_measurement(instrumented, instrumented_map, {})
    report = {
        "schema": 2,
        "artifact": "BOOTX64.EFI",
        "kind": "efi-integrated-rust-preos-a64-reference-core-jit",
        "sha256": sha256(production),
        "bytes": production.stat().st_size,
        "minimum_cpu": ["x86_64", "sse4.1", "sse4.2"],
        "avx_required": False,
        "capabilities": [
            "rust-no_std-staticlib", "c-owned-uefi-lifecycle", "c-owned-jit-wx",
            "bounded-a64-diagnostic-guest", "m1-diagnostic-policy-seed",
            "phase2-vfmachine", "fixed-ram-region-registry", "static-mmio-registry",
            "mmio-access-width-and-alignment-gate", "machine-reset-hook",
            "machine-result-budget-gate", "unsupported-cpu-system-feature-gate",
            "aarch64-guest-state-explicit", "aarch64-exception-decision-commit",
            "aarch64-pending-exception-record", "aarch64-fault-class-preservation",
            "aarch64-privileged-state-reference", "aarch64-system-register-bank-reference",
            "aarch64-mmu-4k-16k-ttbr0-ttbr1-reference", "aarch64-asid-tlb-reference",
            "aarch64-generic-timer-reference", "aarch64-smp-exclusive-instructions",
            "aarch64-pauth-explicit-boundary", "aarch64-reference-interpreter-gate",
            "aarch64-guest-bus-mmio-dispatch",
            "m1-only-t8103-machine-graph-contract", "m1-aic-timer-routing-contract",
            "m1-dart-bounded-dma-translation", "m1-caller-owned-storage-backend",
            "m1-recovery-envelope-boundary", "m1-framebuffer-display-mmio-contract",
            "m1-firmware-handoff-boundary",
            "vmapple-tcg-contract-and-source-pin", "vmapple-fixed-device-graph-unit",
            "vmapple-source-port-manifest-contract",
            "vmapple-graph-same-call-reset-gate",
            "m1-graph-same-call-runtime-gate",
            "iboot-xnu-causal-evidence-contract",
        ],
        "native_unit": native,
        "rust_unit": {"passed": True, "runner": "cargo test --manifest-path sandbox/efi/preos/Cargo.toml"},
        "static_abi_unit": abi_layout,
        "c_rust_abi_unit": ffi,
        "wx_attribute_unit": wx,
        "aic_unit": aic,
        "linked_image_audit": audit,
        "instrumented_image_audit": test_audit,
        "measurements": {
            "phase0_c_only_efi": baseline["artifact"],
            "rust_linked_efi": {"bytes": production.stat().st_size, "sha256": sha256(production)},
            "increase_bytes": production.stat().st_size - old_bytes,
            "production_image": production_footprint,
            "instrumented_image": instrumented_footprint,
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
                "count": "not measured during build",
                "bytes": "not measured during build",
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
            "reset_hook": "called before MACHINE_READY; topology and explicit guest-state banks reset",
            "devices": "none (explicit; synthetic diagnostic MMIO covered by Rust unit test)",
            "guest_physical_address_space": "fixed 0x00000000..0x0000ffff RAM; overlap and overflow checked",
            "native_machine_layer": "phase-2 descriptor core plus synchronized M1-only T8103 contract graph and portable VMApple graph; physical M1 register compatibility not claimed",
            "m1_graph": {
                "implemented": True,
                "soc": "T8103 / Apple M1 baseline",
                "cpu_count": 8,
                "components": ["AIC", "generic timer", "DART/DMA", "storage", "recovery", "display", "firmware handoff"],
                "runtime_activation": "same preOS call wires contract-backed interrupt sources to CPU0; the Rust reference core can dispatch guest accesses through the graph-local M1 bus and mirror timer state after committed instructions",
                "physical_register_map_verified": False,
                "apple_signature_chain_verified": False,
            },
            "vmapple_graph": {
                "initialized_in_preos_call": True,
                "reset_hook": "same synchronous reset as VfMachine",
                "guest_visible_descriptor": "bounded VMApple TCG/reference subset",
                "physical_m1_compatibility": False,
            },
            "physical_m1_compatibility": False,
        },
        "cpu_system_capabilities": {
            "base_aarch64_subset": "runtime-tested",
            "exception_model": "bounded Rust reference core with explicit EL/PSTATE banks, vector entry, and C-JIT status/exception commit; no full handler continuation",
            "privileged_state": "reference-tested current-EL/PSTATE privilege boundary and exception-bank state; full privileged instruction set not implemented",
            "system_registers": "reference-tested 34-register EL1/CNT/EL2/EL3 bank with CurrentEL, ID_AA64, physical/virtual timer, EL checks, and MRS/MSR execution",
            "mmu": "reference-tested 4 KiB/16 KiB TTBR0/TTBR1 walk with dynamic start levels, page/block descriptors, AF, AP, PXN, UXN, and fault classes",
            "tlb": "reference-tested fixed 16-entry ASID/page-size-tagged TLB with invalidation on TTBR/TCR/granule changes",
            "atomics": "reference-tested LDXR/LDAXR/STXR/STLXR plus CLREX with physical-address reservations; single-CPU execution",
            "smp": "reference-tested affinity/online-mask/IRQ routing state; preOS execution remains single-CPU",
            "timer_counter": "reference-tested 24 MHz physical and virtual counter/timer state with pending interrupt boundary; no C-JIT timer source",
            "pauth": "explicit unsupported boundary; no pointer-authentication execution",
            "m1_machine_graph": "runtime-tested fixed T8103 graph primitives plus graph-local guest MMIO dispatch; Apple physical MMIO map and signed firmware acceptance remain unverified",
            "m1_dma": "runtime-tested bounded DART-style IOVA to caller-owned guest RAM copies",
            "m1_display": "runtime-tested caller-owned XRGB8888 framebuffer and display MMIO contract; no Metal backend",
            "m1_recovery": "runtime-tested CRC/sequence envelope; opaque payload is not Apple signature verification",
            "m1_handoff": "runtime-tested aligned in-RAM entry/device-tree metadata; signature_verified remains false",
        },
        "m1_machine_contract": machine_contract,
        "vmapple_tcg_machine_contract": vmapple_tcg_contract,
        "vmapple_tcg_source_manifest": vmapple_tcg_source_manifest,
        "iboot_xnu_handoff_contract": iboot_xnu_handoff_contract,
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
        "rustc": subprocess.check_output([RUSTC, "--version"], text=True).strip(),
        "compiler": subprocess.check_output(["clang", "--version"], text=True).splitlines()[0],
        "instrumented_artifact": {"sha256": sha256(instrumented), "bytes": instrumented.stat().st_size},
    }
    (BUILD / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
