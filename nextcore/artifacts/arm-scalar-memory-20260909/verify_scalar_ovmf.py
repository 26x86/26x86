#!/usr/bin/env python3
"""Run authored integer scalar fixtures through the existing native x86 EFI JIT."""
from __future__ import annotations
import argparse, hashlib, json, os, struct, subprocess, sys
from pathlib import Path

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def prop(name,value):
    return name.encode().ljust(32,b"\0")+struct.pack("<I",len(value))+value.ljust((len(value)+3)&~3,b"\0")

CASES=[("byte-signed","PROBE_BYTE"),("half-signed","PROBE_HALF"),
       ("word-signed","PROBE_WORD"),("quad-zr","PROBE_QUAD"),
       ("a0-device-load","PROBE_DATA_LOAD"),("a0-device-store","PROBE_DATA_STORE"),
       ("sp-load","PROBE_SP_LOAD"),("sp-store","PROBE_SP_STORE"),
       ("simd-rejected","PROBE_SIMD"),("reserved-rejected","PROBE_RESERVED"),
       ("prefetch-rejected","PROBE_PRFM")]
FORMS=["STRB","LDRB","LDRSB_X","LDRSB_W","STRH","LDRH","LDRSH_X","LDRSH_W",
       "STR_W","LDR_W","LDRSW_X","STR_X","LDR_X"]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi",type=Path,required=True)
    parser.add_argument("--tools",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--negative-control",action="store_true",help="execute a wrong zero-extending byte load; expected failure")
    args=parser.parse_args();args.efi=args.efi.resolve(strict=True);args.tools=args.tools.resolve(strict=True)
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    sys.dont_write_bytecode=True;sys.path.insert(0,str(args.tools))
    from build_arm64_handoff_probe import image,PHYSICAL,ENTRY_OFFSET
    source=Path(__file__).resolve().with_name("arm64_scalar_probe.S")
    inputs=[args.efi,source,Path(__file__).resolve(),args.tools/"trace_arm_jit_ovmf.py",
            args.tools/"verify_arm_jit_ovmf.py",args.tools/"build_arm64_handoff_probe.py"]
    before={str(f):digest(f) for f in inputs}
    dt=output/"diagnostic.dt"
    dt.write_bytes(struct.pack("<II",1,1)+prop("name",b"\0")+struct.pack("<II",3,0)
                   +prop("name",b"chosen\0")+prop("dram-base",struct.pack("<Q",0x40000000))
                   +prop("dram-size",struct.pack("<Q",67108864)))
    results=[];commands=[];initial_sp=None
    for index,(name,definition) in enumerate(CASES[:1] if args.negative_control else CASES):
        obj,raw,kernel=(output/f"{name}.{suffix}" for suffix in ("o","bin","kc"))
        command=["clang","--target=aarch64-none-elf","-c",str(source),"-o",str(obj),f"-D{definition}"]
        if args.negative_control:command.append("-DPROBE_BAD_SIGN")
        commands.append(command);subprocess.run(command,check=True)
        command=["llvm-objcopy","-O","binary","--only-section=.text",str(obj),str(raw)]
        commands.append(command);subprocess.run(command,check=True)
        (output/f"{name}.disassembly.txt").write_text(subprocess.check_output(["llvm-objdump","-d",str(obj)],text=True))
        symbols={fields[2]:int(fields[0],16) for line in subprocess.check_output(["llvm-nm","-n",str(obj)],text=True).splitlines()
                 if len(fields:=line.split())==3}
        kernel.write_bytes(image(raw.read_bytes()));case_output=output/name
        command=[sys.executable,str(args.tools/"trace_arm_jit_ovmf.py"),"--efi",str(args.efi),"--kernel",str(kernel),
                 "--device-tree",str(dt),"--output",str(case_output),"--physical-base","0x40000000",
                 "--virtual-base","0xfffffe0000000000","--memory-size","67108864","--kernel-physical","0x42000000",
                 "--instruction-budget","64","--platform-profile","nextcore-irq-compat-v1",
                 "--allow-incomplete-sptm-prefix","--host-memory-mib","256","--timeout","30"]
        commands.append(command);(output/"commands.json").write_text(json.dumps(commands,indent=2)+"\n")
        status=subprocess.run(command,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},check=False).returncode
        report=json.loads((case_output/"report.json").read_text());e=report.get("execution") or {}
        regs=e.get("registers") or {};platform=e.get("platform") or {};exc=e.get("exception") or {}
        checks={"diagnostic_completed":status==0 and report["diagnostic_completed"],
                "native_blocks_executed":report["native_execution_observed"] and e.get("compiled_blocks",0)>0,
                "marker":regs.get("x3")==0x53,"no_async_vector":exc.get("vector")==0,
                "no_pending_lines":platform.get("pending")==0,
                "inputs_preserved":report["original_inputs_preserved"] and report["esp_copies_preserved"]}
        if index<4:
            offset=symbols["probe_success"]
            checks.update(halt=e.get("status")==1,complete_retirement=e.get("retired")==offset//4+1,
                          no_fault_word=e.get("fault_instruction")==0,no_exception=exc.get("esr")==0)
            expected={"PROBE_BYTE":(0x81,0xffffffffffffff81,0xffffff81),
                      "PROBE_HALF":(0x8001,0xffffffffffff8001,0xffff8001)}
            if definition in expected:
                for register,value in zip(("x0","x1","x2"),expected[definition]): checks[register+"_value"]=regs.get(register)==value
            elif definition=="PROBE_WORD":
                checks.update(x0_value=regs.get("x0")==0x80000005,x1_value=regs.get("x1")==0xffffffff80000005,
                              stack_restored=regs.get("x2")==platform.get("sp"))
            else:
                checks.update(x0_value=regs.get("x0")==0x1234567880000005,x2_zero=regs.get("x2")==0,
                              stack_restored=regs.get("x1")==platform.get("sp"))
            if initial_sp is None:initial_sp=platform.get("sp")
            checks["same_initial_stack"]=platform.get("sp")==initial_sp
        else:
            offset=symbols["probe_fault"];word=struct.unpack_from("<I",raw.read_bytes(),offset)[0]
            checks.update(no_fault_retirement=e.get("retired")==offset//4,
                          precise_fault_pc=e.get("pc")==PHYSICAL+ENTRY_OFFSET+offset,
                          precise_fault_word=e.get("fault_instruction")==word,
                          x0_preserved=regs.get("x0")==0xaaaa000000007777,
                          x1_preserved=regs.get("x1")==0xbbbb000000008888)
            if definition in ("PROBE_DATA_LOAD","PROBE_DATA_STORE"):
                checks.update(alignment_status=e.get("status")==12,
                    alignment_esr=exc.get("esr")==(0x96000021 if definition=="PROBE_DATA_LOAD" else 0x96000061),
                    base_preserved=regs.get("x2")==initial_sp+1,stack_unchanged=platform.get("sp")==initial_sp)
            elif definition in ("PROBE_SP_LOAD","PROBE_SP_STORE"):
                checks.update(sp_alignment_status=e.get("status")==19,sp_alignment_esr=exc.get("esr")==0x9a000000,
                    base_preserved=regs.get("x2")==initial_sp,sp_preserved_at_fault=platform.get("sp")==initial_sp+8)
            else:
                checks.update(undefined_status=e.get("status")==8,undefined_esr=exc.get("esr")==0,
                    base_preserved=regs.get("x2")==initial_sp,stack_unchanged=platform.get("sp")==initial_sp)
        result={"name":name,"passed":all(checks.values()),"checks":checks,"execution":e,
                "fixture_sha256":digest(kernel),"raw_sha256":digest(raw),"receipt":str(case_output/"report.json")}
        results.append(result);print(json.dumps(result),flush=True)
    after={str(f):digest(f) for f in inputs}
    receipt={"schema":"nextcore.efi-scalar-memory.v1","cases":results,"forms":FORMS if not args.negative_control else ["deliberately_wrong_LDRB_instead_of_LDRSB_X"],
             "negative_control":args.negative_control,"passed":before==after and all(r["passed"] for r in results),
             "input_sha256_before":before,"input_sha256_after":after,"far_observed":False,
             "guest_ram_after_fault_observed":False,"physical_host_efi_verified":False,
             "sptm_provided":False,"macos_boot_verified":False,"metal_verified":False}
    (output/"report.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"report":str(output/"report.json"),"passed":receipt["passed"]}),flush=True)
    return 0 if receipt["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
