#!/usr/bin/env python3
"""Build/reuse the frozen scalar EFI and replay11 cases plus a failing sign control."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    bundle=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--runtime-checkout",type=Path,required=True,help="isolated ISE checkout at the recorded scalar revision")
    parser.add_argument("--output",type=Path,required=True,help="new persistent output directory")
    parser.add_argument("--efi",type=Path,help="optional original EFI binary with recorded SHA256")
    parser.add_argument("--offline",action="store_true")
    args=parser.parse_args();repo=args.repo.resolve(strict=True);runtime=args.runtime_checkout.resolve(strict=True)
    proof=json.loads((bundle/"provenance.json").read_text())
    revision=subprocess.check_output(["git","-C",str(runtime),"rev-parse","HEAD"],text=True).strip()
    if revision!=proof["runtime_revision"]:parser.error("runtime checkout must match provenance runtime_revision")
    for name,digest in proof["runtime_source_sha256"].items():
        if sha(runtime/name)!=digest:parser.error("runtime source hash mismatch: "+name)
    for name,key in [("arm64_scalar_probe.S","fixture_sha256"),("verify_scalar_ovmf.py","verifier_sha256")]:
        if sha(bundle/name)!=proof[key]:parser.error("authored source changed: "+name)
    for tool in ["clang","llvm-ar","llvm-nm","llvm-objcopy","llvm-objdump","qemu-system-x86_64"]:
        if shutil.which(tool) is None:parser.error("missing tool: "+tool)
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","NEXTCORE_PREOS_RUNTIME":str(runtime/"runtime"),"CARGO_TARGET_DIR":str(output/"target")}
    commands=[]
    def run(label,command):
        commands.append({"label":label,"argv":command});(output/"commands.json").write_text(json.dumps(commands,indent=2)+"\n")
        print(label,flush=True)
        with (output/(label+".log")).open("w") as log:
            return subprocess.run(command,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    if args.efi:
        efi=args.efi.resolve(strict=True)
        if sha(efi)!=proof["efi_sha256"]:parser.error("--efi does not match historical binary hash")
    else:
        cargo=shutil.which("cargo") or str(Path.home()/".cargo/bin/cargo")
        command=[cargo,"build","--locked","--release","--manifest-path",str(repo/"nextcore/Cargo.toml"),"-p","nextcore-efi","--bin","NXARMJIT","--target","x86_64-unknown-uefi","--features","arm-jit-probe,arm-jit-trace"]
        if args.offline:command.append("--offline")
        if run("build",command)!=0:raise RuntimeError("EFI build failed; inspect build.log")
        efi=output/"target/x86_64-unknown-uefi/release/NXARMJIT.efi"
    command=[sys.executable,str(bundle/"verify_scalar_ovmf.py"),"--efi",str(efi),"--tools",str(repo/"nextcore/tools")]
    positive_status=run("positive",command+["--output",str(output/"positive")])
    negative_status=run("negative",command+["--output",str(output/"negative"),"--negative-control"])
    positive=json.loads((output/"positive/report.json").read_text());negative=json.loads((output/"negative/report.json").read_text())
    failures=[key for key,value in negative["cases"][0]["checks"].items() if not value]
    rejected=negative_status==1 and not negative["passed"] and len(negative["cases"])==1 and failures==["x1_value"]
    preserved=all(sha(runtime/name)==digest for name,digest in proof["runtime_source_sha256"].items())
    summary={"schema":"nextcore.bp29-scalar-efi-replay.v1","runtime_revision":revision,"efi_sha256":sha(efi),"historical_efi_binary_equal":sha(efi)==proof["efi_sha256"],"positive_cases":len(positive["cases"]),"negative_control_rejected":rejected,"runtime_sources_preserved":preserved,"passed":positive_status==0 and positive["passed"] and len(positive["cases"])==11 and rejected and preserved,"far_observed":False,"guest_ram_after_fault_observed":False,"physical_host_efi_verified":False,"macos_boot_verified":False,"metal_verified":False}
    (output/"report.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary),flush=True)
    return 0 if summary["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
