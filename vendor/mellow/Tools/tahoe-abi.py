#!/usr/bin/env python3
"""Read-only Tahoe KC/dyld inventory and declared-provider symbol eligibility.

No binaries are rebuilt, loaded, patched, or installed. A static pass is not
runtime linkage, private ABI compatibility, GPU execution, or Metal support.
"""
import argparse
import contextlib
import hashlib
import json
import mmap
import plistlib
import re
import struct
from pathlib import Path


def check(data, offset, size):
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ValueError("Binary field outside file")


def unpack(fmt, data, offset):
    check(data, offset, struct.calcsize(fmt))
    return struct.unpack_from(fmt, data, offset)


def string(data, offset, limit=None):
    end_limit = len(data) if limit is None else limit
    if not 0 <= offset < end_limit <= len(data):
        raise ValueError("String outside bounded region")
    end = data.find(b"\0", offset, end_limit)
    if end < 0 or end - offset > 65536:
        raise ValueError("Unterminated/oversized string")
    return data[offset:end].decode("utf-8", errors="strict")


def commands(data, base=0):
    h = unpack("<8I", data, base)
    if h[0] != 0xFEEDFACF or h[1] != 0x01000007:
        raise ValueError("Expected x86_64 Mach-O header")
    count, size = h[4:6]
    check(data, base + 32, size)
    if not 0 < count <= min(16384, size // 8):
        raise ValueError("Invalid Mach-O command count")
    cursor, result = base + 32, []
    for _ in range(count):
        kind, length = unpack("<II", data, cursor)
        if length < 8 or length % 8 or cursor + length > base + 32 + size:
            raise ValueError("Invalid Mach-O command bounds")
        result.append((kind, cursor, length))
        cursor += length
    if cursor != base + 32 + size:
        raise ValueError("Mach-O command size mismatch")
    return h, result


def thin_x86(data):
    if data[:4] not in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        return data
    is64 = data[:4] == b"\xca\xfe\xba\xbf"
    count = unpack(">I", data, 4)[0]
    stride = 32 if is64 else 20
    if not 0 < count <= 64:
        raise ValueError("Invalid universal slice count")
    check(data, 8, count * stride)
    candidates = []
    for i in range(count):
        fields = unpack(">IIQQII" if is64 else ">IIIII", data, 8 + i * stride)
        cpu, sub, offset, size = fields[:4]
        check(data, offset, size)
        if cpu == 0x01000007:
            candidates.append((offset, size))
    if len(candidates) != 1:
        raise ValueError("No unique x86_64 slice")
    offset, size = candidates[0]
    return data[offset:offset + size]


def uleb(data, offset):
    value = 0
    for index in range(10):
        check(data, offset, 1)
        byte = data[offset]
        offset += 1
        if index == 9 and byte > 1:
            raise ValueError("ULEB128 overflow")
        value |= (byte & 127) << (7 * index)
        if byte < 128:
            return value, offset
    raise ValueError("Unterminated ULEB128")


def export_trie(data):
    pending, result, visits = [(0, "", frozenset())], {}, 0
    while pending:
        cursor, prefix, ancestry = pending.pop()
        if cursor in ancestry or len(prefix) > 65536 or visits > 200000:
            raise ValueError("Export trie cycle/limit exceeded")
        visits += 1
        ancestry = ancestry | {cursor}
        terminal_size, cursor = uleb(data, cursor)
        check(data, cursor, terminal_size)
        children = cursor + terminal_size
        if terminal_size:
            flags, position = uleb(data, cursor)
            value, position = uleb(data, position)
            entry = {"flags": flags}
            if flags & 8:
                entry.update(reexport_ordinal=value, imported_name=string(data, position, children))
            else:
                entry["address_offset"] = value
                if flags & 16:
                    entry["resolver_offset"], position = uleb(data, position)
                if position > children:
                    raise ValueError("Export terminal exceeds declared size")
            if prefix in result:
                raise ValueError("Duplicate export trie terminal")
            result[prefix] = entry
        check(data, children, 1)
        child_count, cursor = data[children], children + 1
        for _ in range(child_count):
            edge = string(data, cursor)
            if not edge:
                raise ValueError("Empty export trie edge")
            cursor += len(edge.encode("utf-8")) + 1
            child, cursor = uleb(data, cursor)
            check(data, child, 1)
            pending.append((child, prefix + edge, ancestry))
    return result


def macho(data, base=0):
    header, cmds = commands(data, base)
    report = {"header_offset": base, "filetype": header[3], "flags": header[6],
              "segments": [], "sections": [], "dependencies": [], "definitions": {},
              "imports": [], "export_trie": {}, "private_abi_verified": False}
    symtab = None
    for kind, pos, length in cmds:
        if kind == 0x19:
            if length < 72:
                raise ValueError("Truncated segment")
            name = data[pos + 8:pos + 24].rstrip(b"\0").decode()
            vm, vs, offset, size, maxprot, initprot, count, flags = unpack("<4Q4I", data, pos + 24)
            if length != 72 + count * 80:
                raise ValueError("Segment section count mismatch")
            check(data, offset, size)
            report["segments"].append({"name": name, "vmaddr": vm, "vmsize": vs, "fileoff": offset, "filesize": size})
            for i in range(count):
                p = pos + 72 + 80 * i
                section_name = data[p:p + 16].rstrip(b"\0").decode()
                address, section_size, section_offset = unpack("<QQI", data, p + 32)
                section_flags = unpack("<I", data, p + 64)[0]
                if section_flags & 255 not in (1, 12, 18):
                    check(data, section_offset, section_size)
                report["sections"].append({"segment": name, "name": section_name, "address": address,
                    "size": section_size, "offset": section_offset, "type": section_flags & 255})
        elif kind == 2:
            if length != 24 or symtab is not None:
                raise ValueError("Invalid/duplicate symbol table")
            symtab = unpack("<4I", data, pos + 8)
        elif kind in (0xC, 0x80000018, 0x8000001F, 0x20, 0x80000023):
            if length < 24:
                raise ValueError("Truncated dylib dependency")
            nameoff, timestamp, current, compat = unpack("<4I", data, pos + 8)
            if nameoff < 24:
                raise ValueError("Invalid dylib dependency string")
            report["dependencies"].append({"path": string(data, pos + nameoff, pos + length),
                "kind": kind, "current_version_raw": current, "compatible_version_raw": compat})
        elif kind == 0x1B:
            if length != 24:
                raise ValueError("Invalid UUID command")
            report["uuid"] = data[pos + 8:pos + 24].hex()
        elif kind == 0x32:
            report["build_version_raw"] = list(unpack("<4I", data, pos + 8))
        elif kind == 0x80000033:
            offset, size = unpack("<II", data, pos + 8)
            check(data, offset, size)
            report["export_trie"] = export_trie(data[offset:offset + size])
    if symtab:
        offset, count, strings, string_size = symtab
        if count > 2000000:
            raise ValueError("Symbol count exceeds inventory limit")
        check(data, offset, count * 16)
        check(data, strings, string_size)
        for index in range(count):
            nameoff, kind, section, desc, value = unpack("<IBBHQ", data, offset + index * 16)
            if kind & 0xE0:
                continue
            name = string(data, strings + nameoff, strings + string_size)
            if not name:
                continue
            if kind & 0x0E == 0:
                report["imports"].append(name)
            elif kind & 0x0E in (2, 14):
                report["definitions"][name] = {"value": value, "n_type": kind,
                    "external": bool(kind & 1), "private_external": bool(kind & 16)}
        report["symbol_count"] = count
    return report


def read_kc(path):
    with path.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        header, cmds = commands(data)
        if header[3] != 12:
            raise ValueError("Expected MH_FILESET kernel collection")
        outer = macho(data)
        report = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "uuid": outer.get("uuid"), "images": {}, "metadata": {}}
        for segment in outer["segments"]:
            if segment["name"] == "__PRELINK_INFO":
                content = data[segment["fileoff"]:segment["fileoff"] + segment["filesize"]].rstrip(b"\0")
                info = plistlib.loads(content)
                for item in info["_PrelinkInfoDictionary"]:
                    report["metadata"][item["CFBundleIdentifier"]] = item
        for kind, pos, length in cmds:
            if kind != 0x80000035:
                continue
            if length < 32:
                raise ValueError("Truncated fileset entry")
            vmaddr, offset, nameoff, reserved = unpack("<QQII", data, pos + 8)
            if nameoff < 32:
                raise ValueError("Invalid fileset name offset")
            name = string(data, pos + nameoff, pos + length)
            if name in report["images"]:
                raise ValueError("Duplicate fileset ID")
            image = macho(data, offset)
            image["fileset_vmaddr"] = vmaddr
            report["images"][name] = image
            if name == "com.apple.kernel":
                for section in image["sections"]:
                    if (section["segment"], section["name"]) == ("__LINKINFO", "__symbolsets"):
                        check(data, section["offset"], section["size"])
                        payload = data[section["offset"]:section["offset"] + section["size"]]
                        report["symbol_sets"] = plistlib.loads(payload)
                        report["symbol_sets_sha256"] = hashlib.sha256(payload).hexdigest()
        return report


def cache_index(data):
    if data[:16] != b"dyld_v1  x86_64\0":
        raise ValueError("Expected x86_64 dyld cache")
    mapping_offset, mapping_count = unpack("<II", data, 16)
    if mapping_offset < 456 or mapping_offset > 4096 or not 0 < mapping_count <= 64:
        raise ValueError("Unsupported dyld header/mapping count")
    check(data, 0, mapping_offset)
    mappings = []
    for index in range(mapping_count):
        address, size, offset, maxprot, initprot = unpack("<3Q2I", data, mapping_offset + index * 32)
        check(data, offset, size)
        if any(address < prior["address"] + prior["size"] and prior["address"] < address + size for prior in mappings):
            raise ValueError("Overlapping cache mappings")
        mappings.append({"address": address, "size": size, "offset": offset})
    image_offset, image_count = unpack("<II", data, 448)
    if image_count > 100000:
        raise ValueError("Cache image count exceeds limit")
    check(data, image_offset, image_count * 32)
    images = []
    for index in range(image_count):
        address, mtime, inode, nameoff, pad = unpack("<3Q2I", data, image_offset + index * 32)
        images.append({"path": string(data, nameoff), "address": address})
    suboff, subcount = unpack("<II", data, 392)
    if subcount > 64:
        raise ValueError("Cache subfile count exceeds limit")
    # This modern header uses dyld_subcache_entry2: UUID, VM offset, suffix.
    if subcount and mapping_offset < 464:
        raise ValueError("Old cache subentry format is unsupported")
    subfiles = []
    for index in range(subcount):
        p = suboff + index * 56
        check(data, p, 56)
        suffix = string(data, p + 24, p + 56)
        if re.fullmatch(r"\.[A-Za-z0-9]+", suffix) is None:
            raise ValueError("Unsafe cache subfile suffix")
        subfiles.append({"suffix": suffix, "uuid": data[p:p + 16].hex()})
    return {"uuid": data[88:104].hex(), "mappings": mappings, "images": images, "subfiles": subfiles,
            "os_version_raw": unpack("<I", data, 364)[0]}


def read_cache(path):
    with contextlib.ExitStack() as stack:
        def open_cache(file):
            handle = stack.enter_context(file.open("rb"))
            data = stack.enter_context(mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ))
            return data, cache_index(data)
        main_data, main = open_cache(path)
        files = [(path, main_data, main)]
        for sub in main["subfiles"]:
            subpath = path.with_name(path.name + sub["suffix"])
            data, parsed = open_cache(subpath)
            if parsed["uuid"] != sub["uuid"]:
                raise ValueError("Dyld subcache UUID mismatch")
            files.append((subpath, data, parsed))
        report = {"files": [{"path": str(file), "sha256": hashlib.sha256(data).hexdigest(),
                            "uuid": parsed["uuid"], "mappings": parsed["mappings"]} for file, data, parsed in files],
                  "images": main["images"], "selected_images": {}, "os_version_raw": main["os_version_raw"]}
        for image in main["images"]:
            if not any(text in image["path"] for text in ("/Metal.framework/", "/IOAccelerator.framework/", "/CoreDisplay.framework/", "AppleIntel", "MTLDriver")):
                continue
            matches = [(file, data, mapping) for file, data, parsed in files for mapping in parsed["mappings"]
                       if mapping["address"] <= image["address"] < mapping["address"] + mapping["size"]]
            if len(matches) != 1:
                raise ValueError("No unique mapping for selected cache image")
            file, data, mapping = matches[0]
            offset = mapping["offset"] + image["address"] - mapping["address"]
            parsed = macho(data, offset)
            parsed["cache_file"] = str(file)
            parsed["objc_method_name_strings"] = []
            for section in parsed["sections"]:
                if section["name"] == "__objc_methname":
                    content = data[section["offset"]:section["offset"] + section["size"]]
                    parsed["objc_method_name_strings"] = sorted(set(s.decode("utf-8") for s in content.split(b"\0") if s))
            report["selected_images"][image["path"]] = parsed
        return report


def version(value):
    if not isinstance(value, str):
        raise ValueError("Version must be text")
    match = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:(d|a|b|fc)(\d+))?", value)
    if not match:
        raise ValueError("Unsupported kext version syntax")
    major, minor, patch, stage, level = match.groups()
    return int(major), int(minor or 0), int(patch or 0), {"d": 1, "a": 3, "b": 5, "fc": 7, None: 9}[stage], int(level or 0)


def resolve_imports(collections, lilu, lilu_info, mellow, mellow_info):
    kernel = next(c for c in collections if "com.apple.kernel" in c["images"])
    kernel_definitions = kernel["images"]["com.apple.kernel"]["definitions"]
    images = {name: image for c in collections for name, image in c["images"].items()}
    metadata = {name: info for c in collections for name, info in c["metadata"].items()}
    images[lilu_info["CFBundleIdentifier"]] = lilu
    metadata[lilu_info["CFBundleIdentifier"]] = lilu_info
    symbolsets = {s["CFBundleIdentifier"]: s for s in kernel["symbol_sets"]["SymbolsSets"]}
    declarations = mellow_info["OSBundleLibraries"]
    providers, dependency_versions = {}, []
    for name, minimum in declarations.items():
        info = symbolsets.get(name, metadata.get(name))
        compatible = False
        if info:
            try:
                compatible = version(info["OSBundleCompatibleVersion"]) <= version(minimum) <= version(info["CFBundleVersion"])
            except (ValueError, KeyError):
                compatible = None
        dependency_versions.append({"identifier": name, "requested": minimum,
            "available_version": info.get("CFBundleVersion") if info else None,
            "oldest_compatible_version": info.get("OSBundleCompatibleVersion") if info else None,
            "declared_version_range_satisfied": compatible})
        if name in symbolsets:
            for symbol in symbolsets[name]["Symbols"]:
                target = symbol.get("AliasTarget", symbol["SymbolName"])
                definition = kernel_definitions.get(target)
                providers.setdefault(symbol["SymbolName"], []).append({"provider": name,
                    "evidence": "kernel __LINKINFO,__symbolsets whitelist plus nlist definition",
                    "alias_target": target, "target_defined": definition is not None,
                    "target_address": definition["value"] if definition else None,
                    "version_range_satisfied": compatible})
        elif name in images:
            for symbol, definition in images[name]["definitions"].items():
                if definition["external"] and not definition["private_external"]:
                    providers.setdefault(symbol, []).append({"provider": name, "evidence": "external non-private nlist definition",
                        "target_defined": True, "target_address": definition["value"], "version_range_satisfied": compatible})
    matches = []
    for symbol in sorted(set(mellow["imports"])):
        candidates = providers.get(symbol, [])
        valid = any(p["target_defined"] and p["version_range_satisfied"] is True for p in candidates)
        matches.append({"symbol": symbol, "static_declared_provider_match": valid, "candidates": candidates})
    missing = [m["symbol"] for m in matches if not m["static_declared_provider_match"]]
    return {"scope": "static dependency/version/export eligibility only", "matches": matches,
            "import_count": len(matches), "matched_count": len(matches) - len(missing), "unmatched": missing,
            "dependencies": dependency_versions, "all_imports_statically_eligible": not missing,
            "kernel_linker_executed": False, "runtime_loaded": False, "private_abi_verified": False,
            "metal_verified": False, "source_kmod_version": mellow_info["CFBundleVersion"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extracted-system", type=Path, required=True, help="Extracted 'macOS Base System' directory")
    parser.add_argument("--lilu", type=Path, required=True, help="Actual Lilu.kext bundle")
    parser.add_argument("--mellow", type=Path, required=True, help="Actual built Mellow.kext bundle")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    library = args.extracted_system.resolve() / "System/Library"
    collections = [read_kc(library / "KernelCollections" / name) for name in ("BootKernelExtensions.kc", "BaseSystemKernelExtensions.kc")]
    def bundle(path):
        info = plistlib.loads((path / "Contents/Info.plist").read_bytes())
        name = info["CFBundleExecutable"]
        if not isinstance(name, str) or Path(name).name != name or name in (".", ".."):
            raise ValueError("Unsafe bundle executable")
        file = path / "Contents/MacOS" / name
        data = file.read_bytes()
        return macho(thin_x86(data)), info, {"path": str(file.resolve()), "sha256": hashlib.sha256(data).hexdigest()}
    lilu, lilu_info, lilu_provenance = bundle(args.lilu)
    mellow, mellow_info, mellow_provenance = bundle(args.mellow)
    result = resolve_imports(collections, lilu, lilu_info, mellow, mellow_info)
    result["inputs"] = {"mellow": mellow_provenance, "lilu": lilu_provenance,
                        "collections": [{"path": c["path"], "sha256": c["sha256"], "uuid": c["uuid"]} for c in collections]}
    cache = read_cache(library / "dyld/dyld_shared_cache_x86_64")
    graphics = {"kernel_images": {}, "cache_images": cache["selected_images"], "private_abi_verified": False}
    inventories = []
    for collection in collections:
        inventory = {"path": collection["path"], "sha256": collection["sha256"], "uuid": collection["uuid"], "images": []}
        for name, image in collection["images"].items():
            info = collection["metadata"].get(name, {})
            inventory["images"].append({"identifier": name, "header_offset": image["header_offset"], "uuid": image.get("uuid"),
                "version": info.get("CFBundleVersion"), "definitions": len(image["definitions"]), "imports": len(image["imports"])})
            if any(s in name for s in ("Graphics", "IOAccelerator", "IOPCIFamily", "IOSurface")):
                graphics["kernel_images"][name] = dict(image, bundle_metadata=info)
        inventories.append(inventory)
    system_version = plistlib.loads((library / "CoreServices/SystemVersion.plist").read_bytes())
    summary = {"system_version": system_version, "kernel_collections": inventories,
        "cache_files": cache["files"], "cache_images": cache["images"], "cache_image_count": len(cache["images"]),
        "kernel_symbol_sets": [{"identifier": s["CFBundleIdentifier"], "symbol_count": len(s["Symbols"])}
                               for c in collections for s in c.get("symbol_sets", {}).get("SymbolsSets", [])],
        "all_mellow_imports_statically_eligible": result["all_imports_statically_eligible"],
        "native_link_load_or_metal_tested": False, "parser_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    def json_default(value):
        if isinstance(value, bytes):
            return {"bytes_hex": value.hex()}
        raise TypeError(type(value).__name__)
    for name, content in [("tahoe-source-inventory.json", summary), ("tahoe-import-resolution.json", result), ("tahoe-graphics-inventory.json", graphics)]:
        (args.output / name).write_text(json.dumps(content, indent=2, default=json_default), encoding="utf-8")
    print(json.dumps({"system_version": system_version, "kernel_images": sum(len(c["images"]) for c in collections),
        "cache_images": len(cache["images"]), "imports": result["import_count"], "static_matches": result["matched_count"],
        "unmatched": result["unmatched"], "runtime_link_load_or_metal_tested": False}, indent=2))
    return 0 if result["all_imports_statically_eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
