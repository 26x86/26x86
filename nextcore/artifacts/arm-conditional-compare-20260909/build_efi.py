#!/usr/bin/env python3
"""Build frozen EFI sources and a separately identified NV-never negative control.

Callers prepare clean source checkouts using source-provenance.json and the
supplied patches. This script never changes those checkouts or their Git state.
"""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ["core","efi","ise","output"]:parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--cargo",default="cargo")
    args=parser.parse_args();sources={name:getattr(args,name).resolve(strict=True)for name in["core","efi","ise"]}
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    provenance=json.loads((ROOT/"source-provenance.json").read_text())
    def verify():
        for module,root in sources.items():
            for name,wanted in provenance[module]["source_sha256"].items():
                if digest(root/name)!=wanted:raise ValueError(f"Source mismatch: {module}/{name}")
    verify();workspace=output/"workspace";workspace.mkdir()
    for name in["core","efi"]:(workspace/name).symlink_to(sources[name],target_is_directory=True)
    manifest='[workspace]\nresolver="2"\nmembers=["core","efi"]\n\n[patch."https://github.com/26x86/Nextcore-Core.git"]\nnextcore-core={path="core"}\n\n[patch."https://github.com/26x86/Nextcore-ISE.git"]\nnextcore-ise={path='+json.dumps(str(sources["ise"]))+'}\n'
    (workspace/"Cargo.toml").write_text(manifest);shutil.copyfile(ROOT/"Cargo.lock",workspace/"Cargo.lock")
    records=[]
    for name,negative in[("positive",False),("nv-never",True)]:
        runtime=sources["ise"]/"runtime"
        if negative:
            copy=output/"negative-runtime";shutil.copytree(runtime,copy,ignore=shutil.ignore_patterns("target"))
            text=(runtime/"jit.c").read_text();needle="if(condition>=14)return 0;"
            if text.count(needle)!=1:raise ValueError("Negative-control injection point changed")
            (copy/"jit.c").write_text(text.replace(needle,"if(condition==15){b(c,0xe9);size_t p=c->used;u32(c,0);return p;}\n    "+needle));runtime=copy
        env={**os.environ,"NEXTCORE_PREOS_RUNTIME":str(runtime),"CARGO_TARGET_DIR":str(output/("target-"+name)),"CARGO_HTTP_MULTIPLEXING":"false"}
        command=[args.cargo,"build","--locked","--release","--manifest-path",str(workspace/"Cargo.toml"),"-p","nextcore-efi","--bin","NXARMJIT","--target","x86_64-unknown-uefi","--features","arm-jit-probe,arm-jit-trace,arm-jit-tiered-trace"]
        r=subprocess.run(command,env=env,capture_output=True,text=True,timeout=300);(output/(name+".log")).write_text(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError(f"EFI build failed; inspect {name}.log")
        binary=output/("target-"+name)/"x86_64-unknown-uefi/release/NXARMJIT.efi"
        records.append({"case":name,"binary":str(binary),"sha256":digest(binary),"command":command})
        print(name,"EFI build PASS",flush=True)
    verify();(output/"build.json").write_text(json.dumps({"passed":True,"source_preserved":True,"builds":records},indent=2)+"\n")
if __name__=="__main__":main()
