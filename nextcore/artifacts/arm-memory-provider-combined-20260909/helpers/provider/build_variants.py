#!/usr/bin/env python3
"""Build canonical provider, direct, and authored transport-failure x86 EFIs.

Writes only a fresh output directory. Source checkouts are read-only. Root owns
public Git pins; the isolated workspace patches the provided matching sources.
"""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=argparse.ArgumentParser(description=__doc__)
    for option in ["efi-source","ise-source","core-source","output"]:a.add_argument("--"+option,type=Path,required=True)
    a.add_argument("--offline",action="store_true");args=a.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    efi=args.efi_source.resolve(strict=True);ise=args.ise_source.resolve(strict=True);core=args.core_source.resolve(strict=True)
    inputs=[efi/"Cargo.toml",efi/"build.rs",*efi.glob("src/**/*.rs"),ise/"Cargo.toml",*ise.glob("src/**/*.rs"),*ise.glob("runtime/*.c"),*ise.glob("runtime/*.h"),*ise.glob("runtime/*.rs"),*ise.glob("runtime/preos/src/**/*.rs"),ise/"runtime/memory-service/Cargo.toml",*ise.glob("runtime/memory-service/src/**/*.rs"),core/"Cargo.toml",*core.glob("src/**/*.rs")]
    before={str(p):digest(p) for p in inputs};records=[];binaries={};passed=False
    try:
        for variant in ["provider","direct","transport"]:
            workspace=out/("workspace-"+variant);package=workspace/"efi";package.mkdir(parents=True)
            for filename in ["Cargo.toml","build.rs"]:shutil.copyfile(efi/filename,package/filename)
            shutil.copytree(efi/"src",package/"src")
            service=ise/"runtime/memory-service"
            if variant=="transport":
                copied=out/"service-transport";copied.mkdir();shutil.copyfile(service/"Cargo.toml",copied/"Cargo.toml");shutil.copytree(service/"src",copied/"src");service=copied
                source=service/"src/lib.rs";text=source.read_text();needle="    let request=unsafe{*request};"
                assert text.count(needle)==1,"Canonical callback source changed; re-review failure injection"
                source.write_text(text.replace(needle,"    // Authored test variant: real callback transport failure on data requests.\n    if unsafe { (*request).operation } != FETCH { return -7; }\n"+needle))
            workspace.joinpath("Cargo.toml").write_text('[workspace]\nmembers=["efi"]\nresolver="2"\n[profile.release]\npanic="abort"\nlto=true\ncodegen-units=1\nopt-level="s"\n[patch."https://github.com/26x86/Nextcore-Core.git"]\nnextcore-core={path='+json.dumps(str(core))+'}\n[patch."https://github.com/26x86/Nextcore-ISE.git"]\nnextcore-ise={path='+json.dumps(str(ise))+'}\nnextcore-memory-service={path='+json.dumps(str(service))+'}\n')
            lock=Path(__file__).with_name("build-Cargo.lock")
            if lock.exists():shutil.copyfile(lock,workspace/"Cargo.lock")
            target=out/("target-"+variant);env={**os.environ,"NEXTCORE_PREOS_RUNTIME":str(ise/"runtime"),"CARGO_TARGET_DIR":str(target)}
            command=["cargo","build","--locked","--release","--manifest-path",str(workspace/"Cargo.toml"),"-p","nextcore-efi","--bin","NXARMJIT","--target","x86_64-unknown-uefi","--features","arm-jit-trace,arm-jit-probe" if variant=="direct" else "arm-jit-memory-provider"]
            if args.offline:command.append("--offline")
            result=subprocess.run(command,env=env,text=True,capture_output=True);(out/("build-"+variant+".log")).write_text(result.stdout+result.stderr);records.append({"variant":variant,"command":command,"returncode":result.returncode})
            if result.returncode:raise RuntimeError("Build failed: "+variant)
            binary=target/"x86_64-unknown-uefi/release/NXARMJIT.efi";binaries[variant]={"path":str(binary),"sha256":digest(binary)};print(json.dumps(binaries[variant]),flush=True)
        passed=True
    finally:
        after={str(p):digest(p) for p in inputs};report={"schema":"nextcore.efi-memory-provider-build.v1","passed":passed and before==after,"binaries":binaries,"commands":records,"source_sha256_before":before,"source_sha256_after":after}
        (out/"build-report.json").write_text(json.dumps(report,indent=2)+"\n")
    return 0 if report["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
