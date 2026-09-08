#!/usr/bin/env python3
"""Independent authored Arm one-way MMU enable and guaranteed post-ISB effects."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess

NAMES = [f"g{g}_{k}" for g in (4096,16384)
         for k in ("success","fetch_unmapped","data_unmapped")]
FIELDS = {"granule","kind","entry","isb_pc","code_va","code_pa","data_va","data_pa",
          "guard_descriptor","code_descriptor","data_descriptor","msr_word","isb_word",
          "seed","data_before","store_operand","ttbr0","ttbr1","tcr","sctlr_before",
          "mair","tables_used","data_after0","data_after1"}
RESULT = ["esr","far","elr","taken","spsr","post_sctlr","post_pc","loaded",
          "readback","marker","final_sctlr","return_pc","handler_el"]
SEED=0x1122334455667788
STORED=0x8877665544332211
CANARY=0xa5a5a5a5a5a5a5a5
OFF=0x30d00802
ON=0x30d00803
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def parse(text):
    records={}
    for line in text.splitlines():
        parts=line.split()
        if not parts: continue
        if parts[0] in records: raise ValueError("duplicate record "+parts[0])
        if not all(re.fullmatch(r"[0-9a-f]{16}",v) for v in parts[1:]):
            raise ValueError("malformed numeric line "+line)
        records[parts[0]]=[int(v,16) for v in parts[1:]]
    if records.pop("HCR") != [1<<31] or records.pop("CURRENT_EL") != [8]:
        raise ValueError("wrong actual EL2 regime")
    cases=[]
    for name in NAMES:
        values=records.pop(name)
        if len(values)!=len(RESULT): raise ValueError("malformed result "+name)
        observed=dict(zip(RESULT,values));captured={}
        for key in FIELDS:
            row=records.pop(name+"."+key)
            if len(row)!=1: raise ValueError("malformed field "+key)
            captured[key]=row[0]
        tables=[]
        count=captured["tables_used"]
        if not 1<=count<=32: raise ValueError("table count outside allocation")
        for t in range(count):
            row=records.pop(f"{name}.table{t}.base")
            if len(row)!=1 or row[0]%16384: raise ValueError("bad table base")
            table={"base":row[0],"entries":{}}
            prefix=f"{name}.table{t}.entry"
            for key in list(records):
                if key.startswith(prefix):
                    index_text=key[len(prefix):]
                    if not re.fullmatch(r"0|[1-9][0-9]*",index_text):raise ValueError("bad table index")
                    index=int(index_text);v=records.pop(key)
                    if index>=captured["granule"]//8 or len(v)!=1 or v[0]==0:
                        raise ValueError("invalid sparse table capture")
                    table["entries"][str(index)]=v[0]
            tables.append(table)
        g=int(name.split("_")[0][1:]);kind=NAMES.index(name)%3
        c=captured;o=observed;va=c["code_va"];tsz=16 if g==4096 else 17
        esr=0 if kind==0 else 0x86000007 if kind==1 else 0x96000007
        far=0 if kind==0 else va if kind==1 else c["data_va"]
        elr=0 if kind==0 else va+(8 if kind==2 else 0)
        checks={
            "granule_kind":c["granule"]==g and c["kind"]==kind,
            "flat_guard_span":c["entry"]%g==g-8 and c["isb_pc"]==c["entry"]+4
                              and va==c["entry"]+8
                              and c["guard_descriptor"]==(c["entry"]&~(g-1))|0x403,
            "next_fetch_nonidentity":va%g==0 and c["code_pa"]%g==0 and va!=c["code_pa"],
            "data_nonidentity":c["data_va"]==0x60000000 and c["data_pa"]%g==0
                               and c["data_va"]!=c["data_pa"],
            "msr_word":c["msr_word"]==0xd5181000,
            "isb_word":c["isb_word"]==0xd5033fdf,
            "code_mapping":c["code_descriptor"]==(0 if kind==1 else c["code_pa"]|0x403),
            "data_mapping":c["data_descriptor"]==(0 if kind==2 else c["data_pa"]|0x403),
            "roots":c["ttbr0"]==tables[0]["base"] and c["ttbr1"]==tables[1]["base"],
            "tcr":c["tcr"]==(tsz|(tsz<<16)|((2<<14)|(1<<30) if g==16384 else 2<<30)),
            "mair":c["mair"]==0x44,
            "initial_m_off":c["sctlr_before"]==OFF,
            "final_m_on":o["final_sctlr"]==ON,
            "origin_state":o["spsr"]==0x3c5,
            "handler_el2":o["handler_el"]==8,
            "exception_taken":o["taken"]==int(kind!=0),
            "exact_esr":o["esr"]==esr,
            "exact_far":o["far"]==far,
            "exact_elr":o["elr"]==elr,
            "post_isb_sctlr":o["post_sctlr"]==(0 if kind==1 else ON),
            "post_isb_pc":o["post_pc"]==(0 if kind==1 else va+4),
            "loaded_value":o["loaded"]==(SEED if kind==0 else 0),
            "stored_readback":o["readback"]==(STORED if kind==0 else 0),
            "completion_marker":o["marker"]==(0x34 if kind==0 else 0),
            "input_data":c["seed"]==SEED and c["data_before"]==CANARY and c["store_operand"]==STORED,
            "physical_seed_unchanged":c["data_after0"]==SEED,
            "physical_store_effect":c["data_after1"]==(STORED if kind==0 else CANARY),
        }
        cases.append({"name":name,"observed_input":c,"observed_tables":tables,
                      "observed":o,"expected":{"esr":esr,"far":far,"elr":elr},
                      "checks":checks,"passed":all(checks.values())})
    if records:raise ValueError("unexpected records "+str(list(records)[:8]))
    return cases

def negative_detected(cases,variant):
    altered=[c for c in cases if c["name"].endswith("_success")]
    preserved=[c for c in cases if not c["name"].endswith("_success")]
    if len(altered)!=2 or len(preserved)!=4 or not all(c["passed"] for c in preserved):return False
    expected_failures = {
        "omit-enable": {"msr_word","final_m_on","post_isb_sctlr","post_isb_pc",
                        "loaded_value","stored_readback","completion_marker","physical_store_effect"},
        "omit-code-mapping": {"code_mapping","exception_taken","exact_esr","exact_far","exact_elr",
                              "post_isb_sctlr","post_isb_pc","loaded_value","stored_readback",
                              "completion_marker","physical_store_effect"},
    }
    if variant not in expected_failures:raise ValueError(variant)
    for c in altered:
        o=c["observed"];i=c["observed_input"]
        if c["passed"] or {k for k,v in c["checks"].items() if not v} != expected_failures[variant]:return False
        if variant=="omit-enable":
            if not (i["msr_word"]==0xd503201f and o["final_sctlr"]==OFF
                    and o["taken"]==0 and o["esr"]==0 and o["far"]==0 and o["elr"]==0
                    and o["marker"]==0xbad and o["post_sctlr"]==0 and o["post_pc"]==0
                    and o["loaded"]==0 and o["readback"]==0
                    and i["data_after0"]==SEED and i["data_after1"]==CANARY):return False
        elif variant=="omit-code-mapping":
            if not (i["msr_word"]==0xd5181000 and i["code_descriptor"]==0 and o["final_sctlr"]==ON
                    and o["taken"]==1 and o["esr"]==0x86000007 and o["far"]==i["code_va"]
                    and o["elr"]==i["code_va"] and o["marker"]==0 and o["post_sctlr"]==0
                    and o["post_pc"]==0 and o["loaded"]==0 and o["readback"]==0
                    and i["data_after0"]==SEED and i["data_after1"]==CANARY):return False
        else:raise ValueError(variant)
        if o["spsr"]!=0x3c5 or o["handler_el"]!=8:return False
    return True

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args();source=Path(__file__).resolve().parent;out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs=[source/n for n in ("start.S","payload.S","oracle.c","oracle.ld","contract.md","probe_enable.py","test_reader.py")]
    before={p.name:sha(p) for p in inputs}
    for p in inputs:(out/p.name).write_bytes(p.read_bytes())
    commands=[];variants={};executable={}
    def run(argv,log=None):
        if log:
            with log.open("w") as f:
                try:p=subprocess.run(argv,stdout=f,stderr=f,text=True,timeout=30)
                except subprocess.TimeoutExpired:
                    commands.append({"argv":argv,"timeout":30,"log":log.name})
                    (out/"commands.json").write_text(json.dumps(commands,indent=2)+"\n");raise
            text=log.read_text();record={"argv":argv,"returncode":p.returncode,"log":log.name,"log_sha256":sha(log)}
        else:
            p=subprocess.run(argv,capture_output=True,text=True,timeout=30);text=p.stdout+p.stderr
            record={"argv":argv,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
        commands.append(record);(out/"commands.json").write_text(json.dumps(commands,indent=2)+"\n")
        if p.returncode:raise RuntimeError("command failed "+str(argv))
        return text
    common=["clang","--target=aarch64-none-elf","-ffreestanding","-fno-builtin","-mgeneral-regs-only","-O2","-Wall","-Wextra","-Werror"]
    for n in ("start.S","payload.S"):
        run(common+["-c",str(source/n),"-o",str(out/(n+".o"))])
    disassembly=run(["llvm-objdump","-d",str(out/"payload.S.o")])
    (out/"payload-disassembly.txt").write_text(disassembly)
    macros={"normal":[],"omit-enable":["-DOMIT_ENABLE"],"omit-code-mapping":["-DOMIT_CODE_MAPPING"]}
    for variant,macro in macros.items():
        run(common+macro+["-c",str(source/"oracle.c"),"-o",str(out/(variant+".o"))])
        run(["ld.lld","-T",str(source/"oracle.ld"),str(out/"start.S.o"),str(out/"payload.S.o"),str(out/(variant+".o")),"-o",str(out/(variant+".elf"))])
        executable[variant]=sha(out/(variant+".elf"))
        text=run(["qemu-system-aarch64","-machine","virt,virtualization=on","-cpu","max","-m","128","-nographic","-monitor","none","-serial","none","-net","none","-semihosting-config","enable=on,target=native","-kernel",str(out/(variant+".elf"))],out/(variant+".log"))
        variants[variant]=parse(text)
    after={p.name:sha(p) for p in inputs};neg={n:negative_detected(variants[n],n) for n in macros if n!="normal"}
    report={"schema":"nextcore.stage1-enable-actual-arm-oracle.v1",
            "passed":before==after and all(c["passed"] for c in variants["normal"]) and all(neg.values()),
            "normal_case_count":len(variants["normal"]),"cases":variants["normal"],"negative_controls":{n:{"detected":neg[n],"cases":variants[n]} for n in neg},
            "source_sha256_before":before,"source_sha256_after":after,"executable_sha256":executable,
            "qemu_version":run(["qemu-system-aarch64","--version"]).splitlines()[0],
            "clang_version":run(["clang","--version"]).splitlines()[0],
            "source_preserved":before==after,"guaranteed_observation":"Only after the identity-mapped next ISB; immediate following fetch is nonidentity.",
            "pre_isb_effect_visibility_compared":False,"table_refill_observed":False,"hardware_tlbi_refill_claimed":False,
            "immutable_table_tlbi_note":"Actual DSB/TLBI/DSB/ISB sequence and data reread execute, but unchanged tables do not prove eviction/refill. Native service table-reader counters are separate evidence.",
            "native_x86_jit_executed":False,"efi_executed":False,"physical_arm_verified":False,"original_os_boot_verified":False,"apple_assets_used":False,
            "normative_references":["https://documentation-service.arm.com/static/5efa1d23dbdee951c1ccdec5 section3.4 and4.2","https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/memory-access-ordering-part-3---memory-access-ordering-in-the-arm-architecture"]}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"passed":report["passed"],"normal_case_count":len(variants["normal"]),
                      "negative_controls":neg,"failures":[{"name":c["name"],"failed_checks":[k for k,v in c["checks"].items() if not v]} for c in variants["normal"] if not c["passed"]]},indent=2))
    return 0 if report["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
