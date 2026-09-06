#!/usr/bin/env python3
"""Read-only x86_64 bundle ABI inventory. Presence is never GPU/Metal success."""
import argparse
import hashlib
import json
import plistlib
import re
import struct
from pathlib import Path

COMPONENTS = {
    "framebuffer": ("AppleIntelTGLGraphicsFramebuffer.kext", True),
    "accelerator": ("AppleIntelTGLGraphics.kext", True),
    "metal_plugin": ("AppleIntelTGLGraphicsMTLDriver.bundle", True),
    "ioaccelerator_family": ("IOAcceleratorFamily2.kext", True),
    "metal_framework": ("Metal.framework", True),
    "gl_plugin": ("AppleIntelTGLGraphicsGLDriver.bundle", False),
    "video_plugin": ("AppleIntelTGLGraphicsVADriver.bundle", False),
}


def bounded(data, offset, size):
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ValueError("Out-of-bounds binary field")
    return data[offset:offset + size]


def cstring(data, offset):
    if offset < 0 or offset >= len(data):
        raise ValueError("Invalid string offset")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("Unterminated binary string")
    return data[offset:end].decode("utf-8", errors="replace")


def macho_inventory(data):
    """Handle thin/fat x86_64 Mach-O; do not execute/load any input."""
    whole_hash = hashlib.sha256(data).hexdigest()
    slices = []
    if data[:4] in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        fat64 = data[:4] == b"\xca\xfe\xba\xbf"
        count = struct.unpack(">I", bounded(data, 4, 4))[0]
        stride = 32 if fat64 else 20
        bounded(data, 8, count * stride)
        for i in range(count):
            fields = struct.unpack(">IIQQII" if fat64 else ">IIIII", bounded(data, 8 + i * stride, stride))
            cpu, subtype, offset, size = fields[:4]
            bounded(data, offset, size)
            slices.append({"cpu_type": cpu, "offset": offset, "size": size})
        target = [s for s in slices if s["cpu_type"] == 0x01000007]
        if len(target) != 1:
            raise ValueError("No unique x86_64 slice in universal binary")
        data = bounded(data, target[0]["offset"], target[0]["size"])
    fields = struct.unpack("<8I", bounded(data, 0, 32))
    magic, cpu, subtype, kind, count, commands_size, flags, _ = fields
    if magic != 0xFEEDFACF or cpu != 0x01000007:
        raise ValueError("Expected x86_64 Mach-O")
    bounded(data, 32, commands_size)
    if count > commands_size // 8:
        raise ValueError("Invalid load-command count")
    output = {"sha256": whole_hash, "x86_64_slice_sha256": hashlib.sha256(data).hexdigest(),
              "universal_slices": slices, "filetype": kind, "load_commands": [],
              "dylib_dependencies": [], "rpaths": [], "exports": [], "imports": [],
              "objc_classes": [], "symbol_table_present": False}
    offset = 32
    symtab = None
    for _ in range(count):
        cmd, size = struct.unpack("<II", bounded(data, offset, 8))
        if size < 8 or size % 8 or offset + size > 32 + commands_size:
            raise ValueError("Invalid load-command bounds")
        command = bounded(data, offset, size)
        output["load_commands"].append(hex(cmd))
        if cmd in (0xC, 0x80000018, 0x8000001F, 0x20, 0x80000023):
            if size < 24:
                raise ValueError("Truncated dylib command")
            nameoff, stamp, current, compat = struct.unpack_from("<4I", command, 8)
            output["dylib_dependencies"].append({"path": cstring(command, nameoff),
                                                "current_version_raw": current, "compatible_version_raw": compat})
        if cmd == 0x8000001C:
            output["rpaths"].append(cstring(command, struct.unpack_from("<I", command, 8)[0]))
        if cmd == 0x1B:
            output["uuid"] = bounded(command, 8, 16).hex()
        if cmd == 0x32:
            output["build_version_raw"] = list(struct.unpack("<4I", bounded(command, 8, 16)))
        if cmd == 2:
            if size != 24 or symtab is not None:
                raise ValueError("Invalid LC_SYMTAB")
            symtab = struct.unpack_from("<4I", command, 8)
        offset += size
    if offset != 32 + commands_size:
        raise ValueError("Load-command length mismatch")
    if symtab:
        symoff, nsyms, stroff, strsize = symtab
        symbols = bounded(data, symoff, nsyms * 16)
        strings = bounded(data, stroff, strsize)
        output["symbol_table_present"] = True
        for index in range(nsyms):
            strx, ntype, section, desc, value = struct.unpack_from("<IBBHQ", symbols, index * 16)
            if ntype & 0xE0:
                continue
            name = cstring(strings, strx)
            if not name:
                continue
            if ntype & 0x0E == 0:
                output["imports"].append(name)
            elif ntype & 1:
                output["exports"].append(name)
            if name.startswith("_OBJC_CLASS_$_"):
                output["objc_classes"].append(name[len("_OBJC_CLASS_$_"):])
    # A stripped symbol table does not prove that private methods are absent.
    output["private_abi_verified"] = False
    return output


def inventory_bundle(path):
    path = path.resolve()
    plist_paths = [path / "Contents/Info.plist", path / "Resources/Info.plist",
                   path / "Versions/Current/Resources/Info.plist"]
    plist_path = next((p for p in plist_paths if p.is_file()), None)
    if plist_path is None:
        raise ValueError("Bundle Info.plist not found")
    info = plistlib.loads(plist_path.read_bytes())
    if not isinstance(info, dict) or not isinstance(info.get("OSBundleLibraries", {}), dict) or not isinstance(info.get("IOKitPersonalities", {}), dict):
        raise ValueError("Malformed bundle metadata")
    executable = info.get("CFBundleExecutable", "")
    if not isinstance(executable, str) or not executable or "/" in executable or "\\" in executable or executable in (".", ".."):
        raise ValueError("Unsafe/missing CFBundleExecutable")
    candidates = [path / "Contents/MacOS" / executable, path / executable,
                  path / "Versions/Current" / executable]
    binary = next((p for p in candidates if p.is_file()), None)
    output = {"path": str(path), "identifier": info.get("CFBundleIdentifier"),
              "version": info.get("CFBundleVersion"), "package_type": info.get("CFBundlePackageType"),
              "bundle_dependencies": info.get("OSBundleLibraries", {}),
              "personalities": info.get("IOKitPersonalities", {}),
              "code_signature_verified": False, "runtime_loaded": False}
    if binary is None:
        output["status"] = "binary_unavailable_or_dyld_cache_only"
        return output
    resolved = binary.resolve()
    if path not in resolved.parents:
        raise ValueError("Bundle executable symlink escapes bundle")
    output["binary"] = str(resolved)
    output["macho"] = macho_inventory(resolved.read_bytes())
    expected_types = (11,) if path.suffix == ".kext" else ((6,) if path.suffix == ".framework" else (6, 8))
    if output["macho"]["filetype"] not in expected_types:
        raise ValueError("Mach-O filetype does not match bundle role")
    output["status"] = "x86_64_binary_inventoried"
    return output


def create_report(search_roots):
    report = {"schema_version": 1, "scope": "read-only artifact inventory", "components": {},
              "metal_available": False, "private_abi_verified": False, "load_authorized": False,
              "gate": "BLOCKED", "blockers": [], "runtime_tests_run": False}
    for role, (name, required) in COMPONENTS.items():
        candidates = []
        for root in search_roots:
            root = root.resolve()
            if root.name == name and root.is_dir():
                candidates.append(root)
            for relative in (name, "Library/Extensions/" + name, "System/Library/Extensions/" + name,
                             "Library/GPUBundles/" + name, "System/Library/Frameworks/" + name):
                candidate = root / relative
                if candidate.is_dir():
                    candidates.append(candidate.resolve())
        candidates = sorted(set(candidates))
        items = []
        for candidate in candidates:
            try:
                items.append(inventory_bundle(candidate))
            except (ValueError, OSError, plistlib.InvalidFileException, struct.error) as error:
                items.append({"path": str(candidate), "status": "invalid", "error": str(error)})
        report["components"][role] = {"name": name, "required": required, "matches": items}
        valid = [item for item in items if item.get("status") == "x86_64_binary_inventoried"]
        if required and not valid:
            report["blockers"].append(f"{role}: required x86_64 executable unavailable")
        if len(valid) > 1:
            report["blockers"].append(f"{role}: ambiguous multiple binaries; choose one snapshot")
    report["required_artifacts_present"] = not report["blockers"]
    # Structural evidence only: private layouts/selector semantics cannot be
    # established by a bundle version or a matching exported symbol name.
    valid_items = [item for component in report["components"].values() for item in component["matches"]
                   if item.get("status") == "x86_64_binary_inventoried"]
    by_identifier = {}
    for item in valid_items:
        identifier = item.get("identifier")
        if isinstance(identifier, str):
            by_identifier.setdefault(identifier, []).append(item)
    dependency_evidence = []
    for item in valid_items:
        for identifier, minimum in item["bundle_dependencies"].items():
            providers = by_identifier.get(identifier, [])
            satisfied = None
            def numeric_version(value):
                if not isinstance(value, str) or re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,3}", value) is None:
                    return None
                fields = tuple(map(int, value.split(".")))
                return fields + (0,) * (4 - len(fields))
            required = numeric_version(minimum)
            actual = numeric_version(providers[0].get("version")) if len(providers) == 1 else None
            if required is not None and actual is not None:
                satisfied = actual >= required
            dependency_evidence.append({"consumer": item.get("identifier"), "dependency": identifier,
                                        "minimum_version": minimum, "provider_paths": [p["path"] for p in providers],
                                        "numeric_minimum_satisfied": satisfied, "runtime_abi_resolved": False})
    report["bundle_dependency_evidence"] = dependency_evidence
    report["target_kernel_kpi_exports_checked"] = False
    report["lilu_exports_checked"] = False
    report["search_roots"] = [{"path": str(root.resolve()), "exists": root.is_dir()} for root in search_roots]
    # Even all names/symbols present does not validate private vtables, selectors,
    # user-client structures, resource ABI, compiler interface or hardware ISA.
    report["blockers"].append("IOAccelerator/Metal private ABI has not been validated against exact Tahoe binaries")
    report["blockers"].append("No target-correlated completed compute/render evidence in this inventory")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = create_report(args.search_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "components"}, indent=2))
    return 2  # inventory cannot authorize activation even when every file exists


if __name__ == "__main__":
    raise SystemExit(main())
