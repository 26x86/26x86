#!/usr/bin/env python3
"""Replay the authored x86 OVMF provider proof with three separately built EFIs."""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for option in ["provider-efi","direct-efi","transport-efi","tools","output"]:parser.add_argument("--"+option,type=Path,required=True)
    args=parser.parse_args();script=Path(__file__).resolve().parent;output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    binaries=[args.provider_efi.resolve(strict=True),args.direct_efi.resolve(strict=True),args.transport_efi.resolve(strict=True)]
    tools=args.tools.resolve(strict=True);inputs=binaries+list(script.glob("*.py"))+list(script.glob("*.S"));before={str(p):digest(p) for p in inputs};records=[]
    def run(name,command,expected=0):
        result=subprocess.run(command,text=True,capture_output=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        (output/(name+".log")).write_text(result.stdout+result.stderr)
        records.append({"name":name,"command":command,"returncode":result.returncode,"expected_returncode":expected})
        print(json.dumps({"phase":name,"returncode":result.returncode}),flush=True)
        if result.returncode!=expected:raise RuntimeError("Unexpected exit for "+name)
    passed=False
    try:
        for kind in ["scalar","pair"]:
            run(kind,[sys.executable,str(script/("verify_"+kind+"_ovmf.py")),"--efi",str(binaries[0]),"--tools",str(tools),"--output",str(output/kind)])
        run("observations",[sys.executable,str(script/"verify_provider_results.py"),"--scalar",str(output/"scalar"),"--pair",str(output/"pair"),"--output",str(output/"observations.json")])
        run("edges",[sys.executable,str(script/"run_provider_edges.py"),"--efi",str(binaries[0]),"--tools",str(tools),"--output",str(output/"edges")])
        run("transport",[sys.executable,str(script/"run_provider_edges.py"),"--efi",str(binaries[2]),"--tools",str(tools),"--output",str(output/"transport"),"--transport-failure"])
        commands=json.loads((output/"scalar/commands.json").read_text());command=next(c for c in commands if any("trace_arm_jit_ovmf.py" in arg for arg in c))
        command[command.index("--efi")+1]=str(binaries[1]);command[command.index("--output")+1]=str(output/"bypass")
        run("bypass",command)
        run("bypass-negative",[sys.executable,str(script/"verify_provider_results.py"),"--byte-case",str(output/"bypass"),"--output",str(output/"bypass-negative.json")],1)
        result=json.loads((output/"bypass/report.json").read_text())["execution"]
        assert (result["status"],result["retired"],result["registers"]["x0"],result["registers"]["x1"],result["registers"]["x2"])==(1,18,129,0xffffffffffffff81,0xffffff81),"Direct path must independently retain the authored byte result"
        passed=True
    finally:
        after={str(p):digest(p) for p in inputs};report={"schema":"nextcore.efi-memory-provider-replay.v1","passed":passed and before==after,
            "positive_provider_cases":23 if passed else None,"transport_failure_cases":1 if passed else None,"actual_direct_bypass_negative_detected":passed,
            "commands":records,"input_sha256_before":before,"input_sha256_after":after,
            "physical_machine_efi_verified":False,"mmu_enabled_verified":False,"guest_ram_after_fault_observed":False,"macos_boot_verified":False,"guest_metal_verified":False}
        (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    return 0 if report["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
