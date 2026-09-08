#!/usr/bin/env python3
"""Authored conditional-compare readback in actual x86 OVMF EFI."""
import argparse,hashlib,json,os,struct,subprocess,sys
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(TOOLS))
from build_arm64_handoff_probe import image,PHYSICAL,ENTRY_OFFSET
CASES=[
 ("ccmp-w-reg",0x1234567800000000,1,"ccmp w0,w1,#15,al",0,8),
 ("ccmp-x-reg",0x8000000000000000,1,"ccmp x0,x1,#15,al",0,3),
 ("ccmp-w-imm",1,0,"ccmp w0,#31,#15,al",0,8),
 ("ccmp-x-imm",31,0,"ccmp x0,#31,#15,al",0,6),
 ("ccmn-w-reg",0x7fffffff,1,"ccmn w0,w1,#15,al",0,9),
 ("ccmn-x-reg",0xffffffffffffffff,1,"ccmn x0,x1,#15,al",0,6),
 ("ccmn-w-imm",0xffffffff,0,"ccmn w0,#1,#15,al",0,6),
 ("ccmn-x-imm",0x7fffffffffffffff,0,"ccmn x0,#1,#15,al",0,9),
 ("ccmp-fallback",11,12,"ccmp x0,x1,#11,ne",6,11),
 ("ccmn-fallback",11,12,"ccmn w0,#31,#15,hi",0,15),
 ("ccmp-wzr",11,12,"ccmp wzr,wzr,#15,al",0,6),
 ("ccmn-xzr-nv",11,12,"ccmn xzr,xzr,#15,nv",0,4),
 ("native-chain",31,31,"ccmp x0,x1,#0,al\nccmn w0,w1,#15,ne\nccmp x0,#31,#0,nv\nb.eq probe_success\nmov x3,#0xbad\nhlt #0",0,6),
]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def const(reg,value):return [f"movz {reg},#{value&65535}"]+[f"movk {reg},#{value>>shift&65535},lsl #{shift}" for shift in [16,32,48]]
def prop(name,value):return name.encode().ljust(32,b"\0")+struct.pack("<I",len(value))+value.ljust((len(value)+3)&~3,b"\0")
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--efi",type=Path,required=True);parser.add_argument("--ise",type=Path,required=True);parser.add_argument("--output",type=Path,required=True);parser.add_argument("--negative-control",action="store_true")
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);efi=args.efi.resolve(strict=True)
    ise=args.ise.resolve(strict=True)
    tracked=subprocess.check_output(["git","-C",str(ise),"ls-files","-z","runtime"]).decode().split("\0")
    frozen={name:digest(ise/name) for name in tracked if name}
    if not frozen:raise RuntimeError("No tracked ISE runtime sources were supplied")
    source_commit=subprocess.check_output(["git","-C",str(ise),"rev-parse","HEAD"],text=True).strip()
    inputs=[efi,Path(__file__).resolve(),TOOLS/"trace_arm_jit_ovmf.py",TOOLS/"verify_arm_jit_ovmf.py",TOOLS/"build_arm64_handoff_probe.py"]
    before={str(p):digest(p) for p in inputs};assert all(digest(ise/n)==h for n,h in frozen.items())
    dt=out/"diagnostic.dt";dt.write_bytes(struct.pack("<II",1,1)+prop("name",b"\0")+struct.pack("<II",3,0)+prop("name",b"chosen\0")+prop("dram-base",struct.pack("<Q",0x40000000))+prop("dram-size",struct.pack("<Q",67108864)))
    results=[];commands=[]
    for name,a,b,code,old,expected in (CASES[11:12] if args.negative_control else CASES):
        assembly=out/(name+".S");obj=out/(name+".o");raw=out/(name+".bin");kc=out/(name+".kc")
        assembly.write_text("\n".join([".text",".global _start","_start:",*const("x0",a),*const("x1",b),"add x2,sp,#0","mov x3,#0xcc31",code,"probe_success:","hlt #0"])+"\n")
        subprocess.run(["clang","--target=aarch64-none-elf","-c",str(assembly),"-o",str(obj)],check=True)
        subprocess.run(["llvm-objcopy","-O","binary","--only-section=.text",str(obj),str(raw)],check=True)
        (out/(name+".disassembly.txt")).write_text(subprocess.check_output(["llvm-objdump","-d",str(obj)],text=True))
        symbols={f[2]:int(f[0],16) for line in subprocess.check_output(["llvm-nm","-n",str(obj)],text=True).splitlines() if len(f:=line.split())==3}
        kc.write_bytes(image(raw.read_bytes()));directory=out/name
        command=[sys.executable,str(TOOLS/"trace_arm_jit_ovmf.py"),"--efi",str(efi),"--kernel",str(kc),"--device-tree",str(dt),"--output",str(directory),
            "--physical-base","0x40000000","--virtual-base","0xfffffe0000000000","--memory-size","67108864","--kernel-physical","0x42000000",
            "--instruction-budget","64","--platform-profile","nextcore-irq-compat-v1","--initial-pstate",str(0x3c5|(old<<28)),"--allow-incomplete-sptm-prefix","--host-memory-mib","256","--timeout","30"]
        commands.append(command);r=subprocess.run(command,capture_output=True,text=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},timeout=50)
        (out/(name+".log")).write_text(r.stdout+r.stderr)
        report=json.loads((directory/"report.json").read_text());e=report.get("execution")or{};regs=e.get("registers")or{};platform=e.get("platform")or{};exc=e.get("exception")or{}
        checks={"host_run":r.returncode==0,"completed":report["diagnostic_completed"],"native":report["native_execution_observed"]and e.get("compiled_blocks",0)>0,"halt":e.get("status")==1,
            "retired":e.get("retired")== (15 if name=="native-chain" else 12),"pc":e.get("pc")==PHYSICAL+ENTRY_OFFSET+symbols["probe_success"]+4,
            "x0":regs.get("x0")==a,"x1":regs.get("x1")==b,"sp":regs.get("x2")==platform.get("sp"),"marker":regs.get("x3")==0xcc31,
            "pstate":platform.get("pstate")==0x3c5|(expected<<28),"no_fault":e.get("fault_instruction")==0 and exc.get("esr")==0 and exc.get("vector")==0,
            "inputs_preserved":report["original_inputs_preserved"] and report["esp_copies_preserved"]}
        result={"name":name,"passed":all(checks.values()),"checks":checks,"status":e.get("status"),"retired":e.get("retired"),"native_blocks":e.get("compiled_blocks"),"pstate":platform.get("pstate"),"receipt":str(directory/"report.json")}
        results.append(result);print(json.dumps(result),flush=True)
    after={str(p):digest(p) for p in inputs};preserved=before==after and all(digest(ise/n)==h for n,h in frozen.items())
    result={"schema":"nextcore.efi-conditional-compare/1","passed":preserved and all(r["passed"]for r in results),"source_preserved":preserved,"negative_control":args.negative_control,"cases":results,"commands":commands,"inputs_sha256":before,"ise_source_sha256":frozen,"ise_commit":source_commit,"macos_boot_verified":False,"metal_verified":False}
    (out/"report.json").write_text(json.dumps(result,indent=2)+"\n");return 0 if result["passed"]else 1
if __name__=="__main__":raise SystemExit(main())
