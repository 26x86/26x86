#!/usr/bin/env python3
"""Compile the actual Xcode target and link with a genuine Darwin kext linker.

The Windows LLVM linker does not implement MH_KEXT_BUNDLE. Pass --darwin-linker
and --wsl-distro to use an extracted cctools-port ld64 in existing WSL instead.
No EFI, system extension directory, kernel collection, or firmware is modified.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import plistlib
import importlib.util
import shutil
from pathlib import Path


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return {"command": [str(x) for x in args], "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def linux_path(path):
    path = Path(path).resolve()
    if not path.drive or len(path.drive) != 2:
        raise ValueError("WSL conversion requires an absolute Windows drive path")
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def expand_plist(value, replacements):
    if isinstance(value, dict):
        return {expand_plist(k, replacements): expand_plist(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_plist(v, replacements) for v in value]
    if isinstance(value, str):
        for key, replacement in replacements.items():
            value = value.replace("$(" + key + ")", replacement)
    return value


def sources_from_project(root):
    project = (root / "Mellow.xcodeproj/project.pbxproj").read_text(encoding="utf-8")
    block = project.split("/* Begin PBXSourcesBuildPhase section */", 1)[1]
    block = block.split("/* End PBXSourcesBuildPhase section */", 1)[0]
    names = re.findall(r"/\* ([A-Za-z0-9_]+\.cpp) in Sources \*/", block)
    paths = []
    for name in names:
        candidates = [root / "Mellow" / name,
                      root / "Lilu.kext/Contents/Resources/Library" / name]
        matches = [p for p in candidates if p.is_file()]
        if len(matches) != 1:
            raise RuntimeError(f"Ambiguous/missing Xcode target source: {name}")
        paths.append(matches[0])
    if not paths or len(paths) != len(set(paths)):
        raise RuntimeError("Empty or duplicated Xcode target source list")
    return paths


def input_hashes(root):
    paths = []
    for folder in ("Mellow", "Drivers/PortedXe", "Lilu.kext/Contents/Resources", "MacKernelSDK"):
        paths.extend(p for p in (root / folder).rglob("*") if p.is_file())
    paths.append(root / "Mellow.xcodeproj/project.pbxproj")
    return {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def macho_header(path):
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError("Truncated Mach-O header")
    magic, cpu, subcpu, kind, commands, size, flags, reserved = struct.unpack_from("<8I", data)
    if magic != 0xFEEDFACF or cpu != 0x01000007:
        raise ValueError("Expected a little-endian x86_64 Mach-O")
    return {"cpu_type": hex(cpu), "filetype": kind, "ncmds": commands,
            "sizeofcmds": size, "flags": hex(flags), "size": len(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-bin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--configuration", choices=["Debug", "Release"], default="Debug")
    parser.add_argument("--darwin-linker", type=Path,
                        help="Actual Apple/cctools-port ld64, never LLVM ld64.lld")
    parser.add_argument("--wsl-distro", help="Existing WSL distro to run Linux cctools-port")
    parser.add_argument("--compile-only", action="store_true",
                        help="Return success for all target objects; never claims a linked driver")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    dest = args.output.resolve()
    if dest == root or dest in root.parents:
        parser.error("Build output cannot be the source root or its ancestor")
    dest.mkdir(parents=True, exist_ok=True)
    exe = ".exe" if (args.llvm_bin / "clang.exe").is_file() else ""
    clang = args.llvm_bin.resolve() / ("clang" + exe)
    linker = args.llvm_bin.resolve() / ("ld64.lld" + exe)
    version = run([clang, "--version"])
    resource = run([clang, "-print-resource-dir"])
    if resource["returncode"]:
        raise RuntimeError(resource["stderr"])
    sources = sources_from_project(root)
    build_input_hashes = input_hashes(root)
    includes = Path(resource["stdout"].strip()) / "include"
    info = plistlib.loads((root / "Mellow/Info.plist").read_bytes())
    version_number = info["CFBundleVersion"]
    bundle_id = info["CFBundleIdentifier"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9.]*", bundle_id):
        raise ValueError("Bundle identifier cannot be used in KMOD_EXPLICIT_DECL")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}(?:[a-z][0-9]+)?", version_number):
        raise ValueError("Unexpected module version")
    flags = ["-target", "x86_64-apple-macos13", "-std=c++17", "-mkernel", "-fapple-kext",
             "-nostdinc", "-isystem", str(includes), "-I", str(root / "MacKernelSDK/Headers"),
             "-I", str(root / "Lilu.kext/Contents/Resources"),
             "-DKERNEL", "-DKERNEL_PRIVATE", "-DPRODUCT_NAME=Mellow", f"-DMODULE_VERSION={version_number}",
             "-fno-exceptions", "-fno-rtti", "-fno-builtin", "-fno-common",
             "-fno-asynchronous-unwind-tables", "-fvisibility=hidden",
             "-fno-register-global-dtors-with-atexit", "-fno-use-cxa-atexit",
             "-mllvm", "-disable-atexit-based-global-dtor-lowering",
             "-Wall", "-Wextra", "-Wno-unknown-warning-option", "-Wno-ossharedptr-misuse", "-Wno-vla"]
    # Kernel calling convention is retained: no SIMD/autovectorization switches.
    # The original Xcode target explicitly overrides its kernel defaults with
    # SSE options. Native build must reconcile those upstream flags separately.
    if args.configuration == "Debug":
        flags += ["-DDEBUG=1", "-DAPPLE_KEXT_ASSERTIONS=1", "-O0"]
    else:
        flags += ["-O3"]
    report = {"scope": "cross build and structural validation only; not load or Metal validation",
              "configuration": args.configuration, "compiler": version, "units": [],
              "kext_linked": False, "kernel_load_tested": False, "metal_tested": False,
              "target_tahoe_kpi_exports_validated": False, "lilu_exports_validated": False,
              "input_sha256": build_input_hashes}
    objects = []
    for source in sources:
        obj = dest / (source.stem + ".o")
        source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        result = run([clang, *flags, "-c", source, "-o", obj])
        result["source"] = str(source.relative_to(root))
        result["source_sha256"] = source_sha256
        if source_sha256 != hashlib.sha256(source.read_bytes()).hexdigest():
            raise RuntimeError("Source changed during compilation; rerun on settled source")
        if result["returncode"] == 0:
            result["object"] = macho_header(obj)
            if result["object"]["filetype"] != 1:
                raise RuntimeError("Compiler did not emit MH_OBJECT")
            result["object_sha256"] = hashlib.sha256(obj.read_bytes()).hexdigest()
            objects.append(obj)
        report["units"].append(result)
        print(f'{"PASS" if result["returncode"] == 0 else "FAIL"} {source.name}', flush=True)
        if result["returncode"]:
            print(result["stderr"], flush=True)
    all_pass = len(objects) == len(sources)
    report["all_target_objects_compiled"] = all_pass
    if all_pass and not args.compile_only:
        metadata = dest / "module_info.c"
        metadata.write_text('''/* Standard KMOD metadata bound to real Lilu entrypoints. */
#include <mach/mach_types.h>
#include <mach/kmod.h>
extern kern_return_t _start(kmod_info_t *, void *);
extern kern_return_t _stop(kmod_info_t *, void *);
extern kern_return_t Mellow_kern_start(kmod_info_t *, void *);
extern kern_return_t Mellow_kern_stop(kmod_info_t *, void *);
KMOD_EXPLICIT_DECL(%s, "%s", _start, _stop)
__private_extern__ kmod_start_func_t *_realmain = Mellow_kern_start;
__private_extern__ kmod_stop_func_t *_antimain = Mellow_kern_stop;
__private_extern__ int _kext_apple_cc = __APPLE_CC__;
''' % (bundle_id, version_number), encoding="utf-8")
        metadata_object = dest / "module_info.o"
        cflags = [flag for flag in flags if flag not in ("-std=c++17", "-fapple-kext", "-fno-rtti")]
        report["module_metadata"] = run([clang, *cflags, "-c", metadata, "-o", metadata_object])
        if report["module_metadata"]["returncode"]:
            raise RuntimeError(report["module_metadata"]["stderr"])
        objects.append(metadata_object)
        # Ask for genuine kext semantics. Do not replace this with -bundle, and
        # do not patch the Mach-O filetype after linking an ordinary executable.
        binary = dest / "Mellow.link-attempt"
        if args.darwin_linker:
            linker = args.darwin_linker.resolve()
        linkflags = ["-arch", "x86_64", "-kext", "-static", "-undefined", "dynamic_lookup"]
        if args.wsl_distro:
            if not args.darwin_linker:
                raise ValueError("--wsl-distro requires --darwin-linker")
            invocation = ["wsl.exe", "-d", args.wsl_distro, "--", linux_path(linker)]
            linkargs = [*linkflags, "-o", linux_path(binary), *[linux_path(x) for x in objects],
                        linux_path(root / "MacKernelSDK/Library/x86_64/libkmod.a")]
        else:
            invocation = [linker]
            linkargs = [*linkflags, "-o", binary, *objects, root / "MacKernelSDK/Library/x86_64/libkmod.a"]
        report["linker_version"] = run([*invocation, "-v"])
        result = run([*invocation, *linkargs])
        if binary.is_file() and result["returncode"] == 0:
            result["header"] = macho_header(binary)
            if result["header"]["filetype"] == 11:
                module_spec = importlib.util.spec_from_file_location("mellow_macho_validator", root / "Tools/validate-macho.py")
                validator = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(validator)
                validation = validator.inspect_binary(binary)
                report["macho_validation"] = validation
                report["kext_linked"] = validation["structural_validation_passed"]
                if report["kext_linked"]:
                    bundle = dest / "Mellow.kext"
                    (bundle / "Contents/MacOS").mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(binary, bundle / "Contents/MacOS/Mellow")
                    expanded = expand_plist(info, {"PRODUCT_BUNDLE_IDENTIFIER": bundle_id,
                                                  "PRODUCT_NAME:rfc1034identifier": "Mellow", "PRODUCT_NAME": "Mellow"})
                    if "$(" in json.dumps(expanded):
                        raise RuntimeError("Unexpanded Xcode variable in plist")
                    (bundle / "Contents/Info.plist").write_bytes(plistlib.dumps(expanded))
                    report["bundle"] = str(bundle)
        report["link_attempt"] = result
        print(result["stderr"], flush=True)
        if not report["kext_linked"]:
            report["blocker"] = "Link failed or binary violates structural/runtime-import checks; see link and validation detail."
    if input_hashes(root) != build_input_hashes:
        raise RuntimeError("Build input changed during compilation/link; rerun before using any artifact")
    report["build_inputs_unchanged"] = True
    report["build_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (dest / "cross-build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report: {dest / 'cross-build-report.json'}")
    return 0 if all_pass and (args.compile_only or report["kext_linked"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
