#!/usr/bin/env python3
"""Validate structural kext properties, not kernel compatibility or GPU operation."""
import argparse
import hashlib
import json
import plistlib
import struct
from pathlib import Path

MH_MAGIC_64 = 0xFEEDFACF
CPU_X86_64 = 0x01000007
MH_KEXT_BUNDLE = 11
N_STAB, N_TYPE, N_EXT, N_UNDF = 0xE0, 0x0E, 1, 0


def inspect_binary(path):
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError("Truncated Mach-O header")
    magic, cpu, subtype, kind, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<8I", data)
    if magic != MH_MAGIC_64 or cpu != CPU_X86_64:
        raise ValueError("Expected thin little-endian x86_64 Mach-O")
    if sizeofcmds > len(data) - 32 or ncmds > sizeofcmds // 8:
        raise ValueError("Invalid Mach-O load command bounds")
    report = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
              "filetype": kind, "cpu_type": hex(cpu), "cpu_subtype": subtype,
              "flags": hex(flags), "load_commands": [], "defined_symbols": [],
              "undefined_symbols": [], "sections": [], "errors": [], "runtime_tested": False}
    if kind != MH_KEXT_BUNDLE:
        report["errors"].append(f"filetype {kind} is not MH_KEXT_BUNDLE (11)")
    # A kernel extension must not require the user-space dyld loader or dylibs.
    forbidden = {0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER",
                 0xF: "LC_ID_DYLINKER", 0x80000018: "LC_LOAD_WEAK_DYLIB",
                 0x8000001F: "LC_REEXPORT_DYLIB", 0x20: "LC_LAZY_LOAD_DYLIB",
                 0x80000023: "LC_LOAD_UPWARD_DYLIB", 0x80000028: "LC_MAIN"}
    offset = 32
    symtab = None
    segments = []
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", data, offset)
        if size < 8 or size % 8 or offset + size > 32 + sizeofcmds:
            raise ValueError("Invalid load command size")
        report["load_commands"].append(hex(cmd))
        if cmd in forbidden:
            report["errors"].append("User-space load command " + forbidden[cmd])
        if cmd == 2:
            if size != 24 or symtab is not None:
                raise ValueError("Invalid or duplicated LC_SYMTAB")
            symtab = struct.unpack_from("<4I", data, offset + 8)
        if cmd == 0x19:
            if size < 72:
                raise ValueError("Truncated LC_SEGMENT_64")
            name, addr, vmsize, fileoff, filesize, maxprot, initprot, nsects, segflags = struct.unpack_from("<16s4Q4I", data, offset + 8)
            if fileoff + filesize > len(data) or 72 + nsects * 80 != size:
                raise ValueError("Invalid segment/section bounds")
            segments.append((addr, fileoff, filesize))
            for index in range(nsects):
                sec = struct.unpack_from("<16s16sQQ8I", data, offset + 72 + index * 80)
                secname, segname, secaddr, secsize, secoff, align, reloff, nreloc, secflags, *_ = sec
                if reloff + nreloc * 8 > len(data):
                    raise ValueError("Section relocation table extends beyond file")
                report["sections"].append({"segment": segname.rstrip(b"\0").decode(),
                                            "name": secname.rstrip(b"\0").decode(),
                                            "size": secsize, "type": secflags & 0xFF,
                                            "relocations": nreloc})
        if cmd == 0xB:
            if size != 80:
                raise ValueError("Invalid LC_DYSYMTAB size")
            values = struct.unpack_from("<18I", data, offset + 8)
            extreloff, nextrel, locreloff, nlocrel = values[14:18]
            if extreloff + nextrel * 8 > len(data) or locreloff + nlocrel * 8 > len(data):
                raise ValueError("Dynamic relocation table extends beyond file")
            report["relocations"] = {"external": nextrel, "local": nlocrel}
        offset += size
    if offset != 32 + sizeofcmds:
        raise ValueError("Load command size mismatch")
    if symtab is None:
        report["errors"].append("Missing LC_SYMTAB")
    else:
        symoff, nsyms, stroff, strsize = symtab
        if symoff + nsyms * 16 > len(data) or stroff + strsize > len(data):
            raise ValueError("Symbol or string table extends beyond file")
        strings = data[stroff:stroff + strsize]
        for index in range(nsyms):
            strx, ntype, section, desc, value = struct.unpack_from("<IBBHQ", data, symoff + index * 16)
            if strx >= len(strings):
                raise ValueError("Symbol string offset out of bounds")
            end = strings.find(b"\0", strx)
            if end < 0:
                raise ValueError("Unterminated symbol name")
            if ntype & N_STAB:
                continue
            name = strings[strx:end].decode("utf-8", errors="replace")
            if ntype & N_TYPE == N_UNDF:
                report["undefined_symbols"].append(name)
            else:
                report["defined_symbols"].append(name)
                if name == "_kmod_info":
                    for vmaddr, fileoff, filesize in segments:
                        if vmaddr <= value and value + 144 <= vmaddr + filesize:
                            pos = fileoff + value - vmaddr
                            report["kmod_identifier"] = data[pos + 16:pos + 80].split(b"\0", 1)[0].decode()
                            report["kmod_version"] = data[pos + 80:pos + 144].split(b"\0", 1)[0].decode()
                            break
        for required in ("_kmod_info", "_Mellow_kern_start", "_Mellow_kern_stop"):
            if required not in report["defined_symbols"]:
                report["errors"].append("Missing module definition " + required)
        for user_symbol in ("_main", "dyld_stub_binder", "_dyld_stub_binder", "___cxa_atexit", "_atexit",
                            "___dso_handle", "___memcpy_chk", "___memmove_chk", "___strncpy_chk"):
            if user_symbol in report["undefined_symbols"]:
                report["errors"].append("Unexpected user-space import " + user_symbol)
    for section in ("__mod_init_func", "__mod_term_func"):
        if not any(s["name"] == section and s["size"] > 0 for s in report["sections"]):
            report["errors"].append("Mellow static lifecycle section missing: " + section)
    report["structural_validation_passed"] = not report["errors"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Mellow.kext bundle or thin Mach-O executable")
    parser.add_argument("--output", type=Path, help="Write detailed JSON including full import inventory")
    args = parser.parse_args()
    source = args.input.resolve()
    plist = None
    if source.is_dir():
        with (source / "Contents/Info.plist").open("rb") as handle:
            plist = plistlib.load(handle)
        executable = plist["CFBundleExecutable"]
        if not isinstance(executable, str) or Path(executable).name != executable:
            raise ValueError("Invalid CFBundleExecutable")
        source = source / "Contents/MacOS" / executable
    report = inspect_binary(source)
    if plist is not None:
        report["bundle_identifier"] = plist.get("CFBundleIdentifier")
        report["bundle_version"] = plist.get("CFBundleVersion")
        report["bundle_dependencies"] = plist.get("OSBundleLibraries", {})
        if plist.get("CFBundlePackageType") != "KEXT":
            report["errors"].append("CFBundlePackageType is not KEXT")
        if "$(" in json.dumps(plist):
            report["errors"].append("Unexpanded Xcode build variables in Info.plist")
        if "as.vit9696.Lilu" not in plist.get("OSBundleLibraries", {}):
            report["errors"].append("Missing Lilu bundle dependency")
        if report.get("kmod_identifier") != plist.get("CFBundleIdentifier"):
            report["errors"].append("KMOD identifier does not match Info.plist")
        if report.get("kmod_version") != plist.get("CFBundleVersion"):
            report["errors"].append("KMOD version does not match Info.plist")
        report["structural_validation_passed"] = not report["errors"]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: val for key, val in report.items()
                      if key not in ("defined_symbols", "undefined_symbols")}, indent=2))
    print(f"Defined: {len(report['defined_symbols'])}; unresolved: {len(report['undefined_symbols'])}")
    print("Structural validation does not validate imports against Tahoe KPI/Lilu exports, loadability, or Metal.")
    return 0 if report["structural_validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
