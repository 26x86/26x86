#!/usr/bin/env python3
"""Real Intel OpenCL C -> SPIR-V/Zebin/EU compilation, never Metal or GPU execution.

Uses locally extracted, hash-pinned Intel Ubuntu 24.04 packages in existing WSL.
No dpkg install, system driver loading, device access, or global configuration.
"""
import argparse
import hashlib
import json
import platform
import shutil
import struct
import subprocess
import urllib.request
from pathlib import Path

PACKAGES = [
    {"name": "intel-ocloc_26.27.39122.11-0_amd64.deb", "size": 533464,
     "url": "https://github.com/intel/compute-runtime/releases/download/26.27.39122.11/intel-ocloc_26.27.39122.11-0_amd64.deb",
     "sha256": "794a77217b3fd4c3f1381c2bb2c3c11a7f81e338b55b8a11e6c3b5070d138f98"},
    {"name": "intel-igc-core-2_2.38.2+22051_amd64.deb", "size": 36148132,
     "url": "https://github.com/intel/intel-graphics-compiler/releases/download/v2.38.2/intel-igc-core-2_2.38.2%2B22051_amd64.deb",
     "sha256": "3dbcbe4e716d62e9bd43a4a476d724cf772b4581dbcdd096d70df382e7ccad7e"},
    {"name": "intel-igc-opencl-2_2.38.2+22051_amd64.deb", "size": 52592076,
     "url": "https://github.com/intel/intel-graphics-compiler/releases/download/v2.38.2/intel-igc-opencl-2_2.38.2%2B22051_amd64.deb",
     "sha256": "e265d191590efd5491bfbbd148c144fdd40aea51e0b57f8651130d2da20b8186"},
]
EXPECTED_PRODUCT_CONFIG = 0x03118000  # Compiler-selected mtl-u-a0, 12.70.0.


def sha256(path):
    with Path(path).open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
        return digest.hexdigest()


def bounded(data, offset, size):
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ValueError("Out-of-bounds ELF field")
    return data[offset:offset + size]


def cstring(data, offset):
    if offset < 0 or offset >= len(data):
        raise ValueError("Invalid ELF string offset")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("Unterminated ELF string")
    return data[offset:end].decode("utf-8", errors="strict")


def inspect_zebin(data, product_config=EXPECTED_PRODUCT_CONFIG):
    """Bounds-checked ELF/IntelGT metadata inventory, NOT a runtime loader.

    This verifies the pinned evidence kernel's container and compiler product
    metadata. It cannot prove actual hardware stepping or instruction safety.
    """
    header = struct.unpack("<16sHHIQQQIHHHHHH", bounded(data, 0, 64))
    ident, kind, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phcount, shsize, shcount, shnames = header
    if ident[:7] != b"\x7fELF\x02\x01\x01" or machine != 205 or version != 1:
        raise ValueError("Expected ELF64 little-endian IntelGT")
    if kind not in (1, 0xFF11, 0xFF12, 0xFF13) or ehsize != 64 or shsize != 64:
        raise ValueError("Unsupported Zebin ELF layout")
    if phoff or phcount or not 1 <= shcount <= 4096 or not 0 < shnames < shcount:
        raise ValueError("Invalid/unsupported program or section table")
    raw = bounded(data, shoff, shcount * shsize)
    sections = []
    for i in range(shcount):
        name, stype, sflags, addr, offset, size, link, info, align, stride = struct.unpack_from("<IIQQQQIIQQ", raw, i * 64)
        if align and align & (align - 1):
            raise ValueError("Invalid section alignment")
        if stype != 8:  # NOBITS has no file payload.
            bounded(data, offset, size)
        sections.append({"index": i, "name_offset": name, "type": stype, "flags": sflags,
                         "offset": offset, "size": size, "link": link, "info": info, "entry_size": stride})
    name_section = sections[shnames]
    if name_section["type"] != 3:
        raise ValueError("Section-name table is not STRTAB")
    names = bounded(data, name_section["offset"], name_section["size"])
    by_name = {}
    for section in sections:
        name = cstring(names, section.pop("name_offset"))
        if name in by_name:
            raise ValueError("Duplicate ELF section name")
        section["name"] = name
        by_name[name] = section

    def payload(name, expected_type):
        section = by_name.get(name)
        if not section or section["type"] != expected_type or not section["size"]:
            raise ValueError("Missing/invalid " + name)
        return bounded(data, section["offset"], section["size"])

    machine_code = payload(".text.mellow_evidence", 1)
    ze_info = payload(".ze_info", 0xFF000011).decode("utf-8", errors="strict")
    if "name:            mellow_evidence" not in ze_info:
        raise ValueError("Evidence kernel metadata missing")
    spirv = payload(".spv", 0xFF000009)
    if len(spirv) < 20 or len(spirv) % 4 or spirv[:4] != b"\x03\x02\x23\x07":
        raise ValueError("Invalid embedded SPIR-V header")
    notes = payload(".note.intelgt.compat", 7)
    cursor, decoded = 0, {}
    while cursor < len(notes):
        namesize, descsize, note_type = struct.unpack("<III", bounded(notes, cursor, 12))
        cursor += 12
        owner = bounded(notes, cursor, namesize)
        cursor += (namesize + 3) & ~3
        descriptor = bounded(notes, cursor, descsize)
        cursor += (descsize + 3) & ~3
        if cursor > len(notes) or owner != b"IntelGT\0" or note_type in decoded:
            raise ValueError("Malformed/duplicate IntelGT compatibility note")
        decoded[note_type] = int.from_bytes(descriptor, "little") if descsize == 4 else descriptor.rstrip(b"\0").decode("ascii")
    if decoded.get(6) != product_config:
        raise ValueError("Compiler product configuration does not match mtl-u-a0")
    symbols, relocations = [], []
    for section in sections:
        if section["type"] == 2:
            if section["entry_size"] != 24 or section["size"] % 24 or section["link"] >= shcount:
                raise ValueError("Invalid symbol table")
            strings_section = sections[section["link"]]
            if strings_section["type"] != 3:
                raise ValueError("Invalid symbol string table")
            strings = bounded(data, strings_section["offset"], strings_section["size"])
            content = bounded(data, section["offset"], section["size"])
            for offset in range(0, len(content), 24):
                name, info, other, shindex, value, size = struct.unpack_from("<IBBHQQ", content, offset)
                symbols.append({"name": cstring(strings, name), "info": info, "section_index": shindex,
                                "value": value, "size": size})
        if section["type"] == 9:
            if section["entry_size"] != 16 or section["size"] % 16 or section["link"] >= shcount or section["info"] >= shcount:
                raise ValueError("Invalid relocation table")
            if sections[section["link"]]["type"] != 2:
                raise ValueError("Relocations lack symbol table")
            target = sections[section["info"]]
            content = bounded(data, section["offset"], section["size"])
            for offset in range(0, len(content), 16):
                address, info = struct.unpack_from("<QQ", content, offset)
                if address >= target["size"] or info >> 32 >= sections[section["link"]]["size"] // 24:
                    raise ValueError("Relocation points outside target or symbols")
                relocations.append({"section": target["name"], "offset": address,
                                    "symbol_index": info >> 32, "type": info & 0xFFFFFFFF})
    return {"filetype": kind, "machine": machine, "sections": sections, "symbols": symbols,
            "relocations": relocations, "intelgt_compatibility_notes": decoded, "ze_info": ze_info,
            "machine_code_bytes": len(machine_code), "machine_code_sha256": hashlib.sha256(machine_code).hexdigest(),
            "embedded_spirv_sha256": hashlib.sha256(spirv).hexdigest(), "runtime_relocations_applied": False,
            "instructions_executed": False, "hardware_stepping_verified": False}


def linux_path(path):
    path = Path(path).resolve()
    if platform.system() == "Windows":
        if len(path.drive) != 2:
            raise ValueError("WSL paths must be on a Windows drive")
        return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]
    return str(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-root", type=Path, required=True, help="Local scratch directory; no global install")
    parser.add_argument("--output", type=Path, required=True, help="NEW directory, to exclude stale compiler evidence")
    parser.add_argument("--wsl-distro", default="Ubuntu-24.04")
    parser.add_argument("--prepare", action="store_true", help="Download pinned packages if absent and extract locally")
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.output.exists():
        parser.error("output must be a new directory; retained evidence is never deleted or overwritten")
    args.output.mkdir(parents=True)
    args.toolchain_root = args.toolchain_root.resolve()
    packages = args.toolchain_root / "ocloc-packages"
    prefix = args.toolchain_root / "ocloc-prefix"
    packages.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "frontend": "OpenCL C 2.0", "compiler": "Intel IGC 2.38.2",
              "ocloc": "26.27.39122.11", "requested_device_id": "0x7d41",
              "gpu_executed": False, "metal_msl_frontend": False, "metal_driver_abi_implemented": False,
              "offline_compilation_validated": False, "packages": [], "commands": []}
    base = ["wsl.exe", "-d", args.wsl_distro, "--"] if platform.system() == "Windows" else []

    def execute(command, timeout=180):
        result = subprocess.run(base + command, capture_output=True, text=True, errors="replace", timeout=timeout)
        report["commands"].append({"command": base + command, "returncode": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError("Command failed: " + command[0] + "\n" + result.stderr + result.stdout)
        return result.stdout + result.stderr

    try:
        for package in PACKAGES:
            destination = packages / package["name"]
            if not destination.is_file() and args.prepare:
                request = urllib.request.Request(package["url"], headers={"User-Agent": "Mellow-offline-compiler-evidence"})
                temporary = destination.with_suffix(".download")
                with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as target:
                    shutil.copyfileobj(response, target)
                if temporary.stat().st_size != package["size"] or sha256(temporary) != package["sha256"]:
                    raise RuntimeError("Downloaded package hash/size mismatch: " + package["name"])
                temporary.replace(destination)
            if not destination.is_file() or destination.stat().st_size != package["size"] or sha256(destination) != package["sha256"]:
                raise RuntimeError("Missing/unverified package; use --prepare: " + package["name"])
            report["packages"].append(dict(package, verified=True))
            if args.prepare:
                execute(["dpkg-deb", "-x", linux_path(destination), linux_path(prefix)])
        binary = prefix / "usr/bin/ocloc-26.27.1"
        if not binary.is_file():
            raise RuntimeError("Locally extracted ocloc missing; use --prepare")
        # Record every local tool/library input. Hash pins above authenticate the
        # archives; re-extraction with --prepare restores their packaged payload.
        report["local_tool_inputs"] = {str(p.relative_to(prefix)).replace("\\", "/"): sha256(p)
                                      for p in sorted(prefix.rglob("*")) if p.is_file()}
        ocloc = ["env", "LD_LIBRARY_PATH=" + linux_path(prefix / "usr/lib/x86_64-linux-gnu") + ":" + linux_path(prefix / "usr/local/lib"), linux_path(binary)]
        source = Path(__file__).with_name("metal-evidence.cl")
        shutil.copy2(source, args.output / source.name)
        report["source_sha256"] = sha256(source)
        build_log = execute(ocloc + ["compile", "-file", linux_path(source), "-device", "0x7d41",
                                    "-output", "mellow_evidence", "-out_dir", linux_path(args.output),
                                    "-options", "-cl-std=CL2.0 -cl-kernel-arg-info"])
        if "Auto-detected target based on 0x7d41 device id: mtl-u-a0" not in build_log or "Build succeeded." not in build_log:
            raise RuntimeError("Expected explicit target resolution and successful compiler report missing")
        report["compiler_selected_target"] = "mtl-u-a0"
        compiled = args.output / "mellow_evidence_mtl.bin"
        report["zebin"] = inspect_zebin(compiled.read_bytes())
        validation = execute(ocloc + ["validate", "-file", linux_path(compiled)])
        if "VALID" not in validation or "INVALID" in validation:
            raise RuntimeError("Intel binary validator did not report VALID")
        execute(ocloc + ["disasm", "-file", linux_path(compiled), "-dump", linux_path(args.output / "disassembly"), "-device", "0x7d41"])
        assembly = args.output / "disassembly/.text.mellow_evidence.asm"
        if not assembly.is_file() or not assembly.stat().st_size:
            raise RuntimeError("EU disassembly missing")
        report["artifacts"] = {str(p.relative_to(args.output)).replace("\\", "/"): {"bytes": p.stat().st_size, "sha256": sha256(p)}
                               for p in sorted(args.output.rglob("*")) if p.is_file()}
        # Preserve accompanying package license files if present. The compiler
        # DLL/SO payload is intentionally not redistributed in this output.
        licenses = args.output / "licenses"
        licenses.mkdir()
        for path in prefix.rglob("*"):
            if path.is_file() and (path.name == "copyright" or path.name.lower().startswith("license")):
                target = licenses / ("__".join(path.relative_to(prefix).parts))
                shutil.copy2(path, target)
        report["offline_compilation_validated"] = True
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, struct.error) as error:
        report["error"] = str(error)
    (args.output / "compiler-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("commands", "local_tool_inputs", "zebin", "packages", "artifacts")}, indent=2))
    return 0 if report["offline_compilation_validated"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
