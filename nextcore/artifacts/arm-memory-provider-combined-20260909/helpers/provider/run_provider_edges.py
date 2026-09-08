#!/usr/bin/env python3
"""Execute authored provider boundary cases in x86 OVMF, with serial assertions."""
import argparse, hashlib, json, os, struct, subprocess, sys
from pathlib import Path
from verify_provider_results import observation

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prop(n,v):return n.encode().ljust(32,b"\0")+struct.pack("<I",len(v))+v.ljust((len(v)+3)&~3,b"\0")
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument("--efi",type=Path,required=True);a.add_argument("--tools",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True);a.add_argument("--transport-failure",action="store_true",help="requires separately authored callback-failure binary")
    args=a.parse_args();args.efi=args.efi.resolve(strict=True);args.tools=args.tools.resolve(strict=True)
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);sys.dont_write_bytecode=True;sys.path.insert(0,str(args.tools))
    from build_arm64_handoff_probe import image,PHYSICAL,ENTRY_OFFSET
    source=Path(__file__).with_name("arm64_provider_edges.S");inputs=[source,args.efi,Path(__file__).resolve(),Path(__file__).with_name("verify_provider_results.py"),args.tools/"trace_arm_jit_ovmf.py",args.tools/"build_arm64_handoff_probe.py"]
    before={str(p):digest(p) for p in inputs};dt=output/"diagnostic.dt"
    dt.write_bytes(struct.pack("<II",1,1)+prop("name",b"\0")+struct.pack("<II",3,0)+prop("name",b"chosen\0")+prop("dram-base",struct.pack("<Q",0x40000000))+prop("dram-size",struct.pack("<Q",67108864)))
    cases=[("transport-failure","PROBE_TRANSPORT")] if args.transport_failure else [("missing-load","PROBE_LOAD"),("missing-store","PROBE_STORE"),("pair-second-load","PROBE_PAIR_LOAD"),("pair-second-store","PROBE_PAIR_STORE"),("pc-alignment","PROBE_PC_ALIGNMENT"),("missing-fetch","PROBE_MISSING_FETCH")]
    results=[];commands=[]
    for name,definition in cases:
        obj,raw,kernel=[output/(name+s) for s in [".o",".bin",".kc"]]
        cmds=[["clang","--target=aarch64-none-elf","-c",str(source),"-D"+definition,"-o",str(obj)],["llvm-objcopy","-O","binary","--only-section=.text",str(obj),str(raw)]]
        for cmd in cmds:commands.append(cmd);subprocess.run(cmd,check=True)
        symbols={f[2]:int(f[0],16) for line in subprocess.check_output(["llvm-nm","-n",str(obj)],text=True).splitlines() if len(f:=line.split())==3}
        (output/(name+".disassembly.txt")).write_text(subprocess.check_output(["llvm-objdump","-d",str(obj)],text=True))
        kernel.write_bytes(image(raw.read_bytes()));folder=output/name
        cmd=[sys.executable,str(args.tools/"trace_arm_jit_ovmf.py"),"--efi",str(args.efi),"--kernel",str(kernel),"--device-tree",str(dt),"--output",str(folder),"--physical-base","0x40000000","--virtual-base","0xfffffe0000000000","--memory-size","67108864","--kernel-physical","0x42000000","--instruction-budget","64","--platform-profile","nextcore-irq-compat-v1","--allow-incomplete-sptm-prefix","--host-memory-mib","256","--timeout","30"]
        commands.append(cmd);rc=subprocess.run(cmd,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}).returncode
        receipt=json.loads((folder/"report.json").read_text());e=receipt.get("execution") or {};regs=e.get("registers") or {};exc=e.get("exception") or {};m,marker=observation(folder)
        fetch_fault=name in ["pc-alignment","missing-fetch"];pair=name.startswith("pair-second-")
        retired=symbols["probe_fault"]//4+int(fetch_fault)
        target=0x40000002 if name=="pc-alignment" else 0x43000000 if args.transport_failure else 0x44000000
        base=target-8 if pair else target
        expected_status=16 if name=="pc-alignment" else 4
        expected_esr=0x8a000000 if name=="pc-alignment" else 0
        expected_provider={"abi":1,"provider_status":0 if name=="pc-alignment" else 4 if args.transport_failure else 1,
            "guest_far":target if name=="pc-alignment" else 0,"last_address":target,
            "fetch_requests":retired+1,"data_requests":0 if fetch_fault else 1,"completed_data_operations":0}
        expected_pc=target if fetch_fault else PHYSICAL+ENTRY_OFFSET+symbols["probe_fault"]
        checks={"diagnostic_completed":rc==0 and receipt.get("diagnostic_completed") is True,"provider_marker":marker,"provider_result":bool(m),
            "native_executed":receipt.get("native_execution_observed") is True,"inputs_preserved":receipt.get("original_inputs_preserved") is True and receipt.get("esp_copies_preserved") is True,
            "status":e.get("status")==expected_status,"retirement":e.get("retired")==retired,"fault_pc":e.get("pc")==expected_pc,
            "native_entry_count":e.get("compiled_blocks")==retired+(0 if fetch_fault else 1),"no_fabricated_fault_instruction":e.get("fault_instruction")==0,
            "x0_unchanged":regs.get("x0")==0x55,"x1_unchanged":regs.get("x1")==0x66,"base_no_writeback":regs.get("x2")==base,
            "marker":regs.get("x3")==0x70,"esr":exc.get("esr")==expected_esr,"elr":exc.get("elr")== (target if name=="pc-alignment" else 0),
            "no_exception_vector":exc.get("vector")==0}
        checks.update({"provider_"+k:m.get(k)==v for k,v in expected_provider.items()})
        result={"name":name,"passed":all(checks.values()),"checks":checks,"execution":e,"provider":m,"expected_provider":expected_provider,"kernel_sha256":digest(kernel),"serial_sha256":digest(folder/"serial.log")}
        results.append(result);print(json.dumps({"name":name,"passed":result["passed"],"failed_checks":[k for k,v in checks.items() if not v]}),flush=True)
    after={str(p):digest(p) for p in inputs};passed=before==after and all(r["passed"] for r in results)
    report={"schema":"nextcore.efi-provider-edges.v1","passed":passed,"cases":results,"transport_failure_variant":args.transport_failure,"input_sha256_before":before,"input_sha256_after":after,"commands":commands,"guest_ram_after_fault_observed":False,"physical_machine_efi_verified":False,"macos_boot_verified":False,"guest_metal_verified":False}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n");return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())
