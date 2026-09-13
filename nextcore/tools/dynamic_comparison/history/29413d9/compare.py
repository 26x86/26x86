#!/usr/bin/env python3
"""Replay six frozen actual Arm transitions through canonical native C/Rust."""
from pathlib import Path
import argparse,copy,hashlib,json,os,platform,struct,subprocess

PUBLIC_SHA="29ccd46ff85dd9da2f8ee8023f86362bfb469e461b04a26d4a07bb7ae0b990cc"
FREEZE_SHA="557bf4cb1e531941b375f65e7b1aab1b19591e0faac099ce4fb058c8ca593ddc"
RESULT=["status","abi","size","provider","fetches","data_requests","completed","last_address","guest_far",
        "reply_result","reply_fault","reply_fsc","reply_level","reply_address","reply_esr","reply_value0",
        "state_tag","revision","epoch","invalidations","software_table_reads"]
STATE=["sctlr","ttbr0","ttbr1","tcr","mair","hcr","scr","reserved"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
def elf_info(path):
 b=path.read_bytes();need(len(b)>=64 and b[:6]==b"\x7fELF\x02\x01","ELF64LE required")
 h=struct.unpack_from("<16sHHIQQQIHHHHHH",b);need(h[2]==183 and h[9]==56 and h[11]==64,"AArch64 ELF shape")
 def take(at,n):
  need(0<=at<=len(b) and 0<=n<=len(b)-at,"ELF range");return b[at:at+n]
 sections=[struct.unpack("<IIQQQQIIQQ",take(h[6]+i*h[11],64)) for i in range(h[12])]
 symbols={}
 for s in sections:
  if s[1]!=2:continue
  need(s[6]<len(sections) and s[9]==24 and s[5]%24==0,"symbol table shape")
  ns=sections[s[6]];names=take(ns[4],ns[5])
  for at in range(s[4],s[4]+s[5],24):
   n,info,other,index,value,size=struct.unpack("<IBBHQQ",take(at,24));need(n<len(names),"symbol name")
   end=names.find(b"\0",n);need(end>=n,"symbol terminator");label=names[n:end].decode("ascii")
   if label:symbols[label]=(value,size)
 segments=[struct.unpack("<IIQQQQQQ",take(h[5]+i*h[9],56)) for i in range(h[10])]
 def read(pa,n):
  for kind,flags,off,va,physical,filesz,memsz,align in segments:
   if kind==1 and physical<=pa and n<=filesz and pa-physical<=filesz-n:return take(off+pa-physical,n)
  raise ValueError("payload outside captured ELF")
 return symbols,read

def load_observed(text):
 rows={}
 for line in text.splitlines():
  p=line.split();need(len(p)>=3 and p[0] in ("CPU","RESULT","STATE"),"unexpected native output")
  key=(p[0],p[1]);need(key not in rows,"duplicate native record");rows[key]=[int(v,16) for v in p[2:]]
 return rows

def compare(case,actual,ram,expected_ram):
 i=case["observed_input"];o=case["observed"];kind=i["kind"];cpu=actual["cpu"];r=actual["result"]
 va=i["code_va"];success=kind==0
 status=8 if success else 16 if kind==1 else 17
 pc=va+40 if success else o["elr"]
 retirements=12 if success else 2 if kind==1 else 4
 expected_counters=(13,3,3) if success else (3,0,0) if kind==1 else (5,1,0)
 expected_state={k:i[k] for k in ("ttbr0","ttbr1","tcr","mair")}
 expected_state.update(sctlr=o["final_sctlr"],hcr=0,scr=0,reserved=0)
 checks={
  "native_boundary_status":r["status"]==status and cpu[47]==status,
  "run_abi":(r["abi"],r["size"],r["provider"])==(3,512,0),
  "original_pc_boundary":cpu[32]==pc,
  "authored_retirement_boundary":cpu[33]==retirements,
  "current_el_and_pstate":cpu[34]==1 and cpu[35]==o["spsr"],
  "post_sctlr_witness":cpu[10]==o["post_sctlr"],
  "post_pc_witness":cpu[11]==o["post_pc"],
  "captured_loaded_value":cpu[12]==o["loaded"],
  "captured_stored_readback":cpu[13]==o["readback"],
  "captured_marker":cpu[14]==o["marker"],
  "final_sctlr":cpu[40]==o["final_sctlr"],
  "control_snapshots":actual["architectural"]==expected_state and actual["effective"]==expected_state,
  "control_revisions":(r["state_tag"],r["revision"],r["epoch"],r["invalidations"])==(2,2,2,1 if success else 0),
  "native_compiled_blocks":cpu[45]==(13 if success else 2 if kind==1 else 5),
  "native_callback_counts":(r["fetches"],r["data_requests"],r["completed"])==expected_counters,
  "native_full_backing_authored_effect":ram==expected_ram,
 }
 if not success:
  checks.update(guest_esr=cpu[36]==o["esr"],guest_far=cpu[37]==o["far"] and r["guest_far"]==o["far"],
                guest_elr=cpu[38]==o["elr"],guest_spsr=cpu[39]==o["spsr"])
  checks["reply_fault"]=(r["reply_result"],r["reply_fault"],r["reply_fsc"],r["reply_level"],r["reply_address"])==(1,4,7,3,o["far"])
  checks["reply_esr"]=r["reply_esr"]==o["esr"]
 else:
  checks["unaltered_hvc_fetched"]=(r["reply_result"],r["reply_fault"],r["reply_value0"],r["last_address"])==(0,0,0xd4000682,va+40)
  checks["native_unsupported_bookkeeping"]=(cpu[36],cpu[37],cpu[38],cpu[39],cpu[46],r["guest_far"])==(0x02000000,0,va+40,0x3c5,1,0)
 return {"name":case["name"],"comparison_scope":("guaranteed post-ISB effects before unchanged HVC, plus separate native unsupported-boundary policy" if success else "actual Arm translation fault ESR/FAR/ELR/SPSR and prior effects"),"expected_native_status":status,"expected_native_retired":retirements,
         "actual":actual,"checks":checks,"passed":all(checks.values())}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ("oracle","runtime","output"):ap.add_argument("--"+n,type=Path,required=True)
 ap.add_argument("--source-freeze",type=Path,default=Path(__file__).with_name("source-freeze.json"))
 ap.add_argument("--rustc",default="rustc");ap.add_argument("--clang",default="clang");a=ap.parse_args()
 need((platform.system(),platform.machine())==("Linux","x86_64"),"native Linux x86_64 required")
 src=Path(__file__).resolve().parent;oracle=a.oracle.resolve();runtime=a.runtime.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 need(sha(oracle/"manifest.json")==PUBLIC_SHA,"original public manifest identity")
 manifest=json.loads((oracle/"manifest.json").read_text())["files"]
 original={p:sha(oracle/p) for p in manifest};need(all(original[p]==v["sha256"] for p,v in manifest.items()),"original public bytes changed")
 freeze=a.source_freeze.resolve();need(sha(freeze)==FREEZE_SHA,"owner runtime freeze identity")
 frozen=json.loads(freeze.read_text())["files"];before={p:sha(runtime/p) for p in frozen};need(before==frozen,"canonical runtime differs from freeze")
 (out/"source-freeze.json").write_bytes(freeze.read_bytes())
 tool_inputs=["compare.py","observer.c","native_replay.rs","contract.md","test_compare.py"]
 tool_before={p:sha(src/p) for p in tool_inputs}
 for p in tool_inputs:(out/p).write_bytes((src/p).read_bytes())
 raw=(oracle/"captured/normal.log").read_text().splitlines()
 need([s for s in raw if s.startswith("HCR ")]==["HCR 0000000080000000 "],"actual HCR must be RW-only")
 need([s for s in raw if s.startswith("CURRENT_EL ")]==["CURRENT_EL 0000000000000008 "],"actual controller EL2")
 report=json.loads((oracle/"captured/report.json").read_text());need(report["passed"] and report["normal_case_count"]==6,"actual oracle scope")
 elf=oracle/"captured/normal.elf";need(sha(elf)==report["executable_sha256"]["normal"],"captured ELF identity")
 symbols,read=elf_info(elf)
 for label,size in [("tables",0x80000),("transition",0x8000),("target",0x4000),("data",0x4000)]:
  need(symbols[label][1]==size,"authored array size "+label)
 table_base=symbols["tables"][0];base=symbols["transition"][0];target=symbols["target"][0];data=symbols["data"][0]
 need(base==table_base+0x80000 and target==base+0x8000 and data==target+0x4000,"actual array contiguity")
 payloads={}
 for label,end in [("transition_words","transition_end"),("target_words","target_end"),("decoy_words","decoy_end")]:
  start=symbols[label][0];length=symbols[end][0]-start;need(0<length<=256 and length%4==0,"payload extent")
  payloads[label]=read(start,length)
 need(payloads["transition_words"]==struct.pack("<II",0xd5181000,0xd5033fdf),"actual transition words")
 need(len(payloads["target_words"])==48 and struct.unpack_from("<I",payloads["target_words"],40)[0]==0xd4000682,"actual HVC boundary")
 stack=symbols["el1_stack_top"][0];rust_cases=[];inputs=[];expected={}
 for case in report["cases"]:
  i=case["observed_input"];o=case["observed"];name=case["name"];g=i["granule"]
  need(case["passed"] and all(case["checks"].values()) and o["spsr"]==0x3c5,"captured origin profile")
  need(i["code_pa"]==target and i["data_pa"]==data and i["entry"]==base+g-8 and i["code_va"]==base+g,"captured array addresses")
  ram=bytearray(0x10000);ram[g-8:g]=payloads["transition_words"]
  ram[g:g+len(payloads["decoy_words"])]=payloads["decoy_words"]
  ram[target-base:target-base+len(payloads["target_words"])]=payloads["target_words"]
  struct.pack_into("<QQ",ram,data-base,i["seed"],i["data_before"])
  tables=bytearray(0x80000);seen=set()
  for t in case["observed_tables"]:
   addr=t["base"];need(addr not in seen and addr%16384==0 and table_base<=addr<=base-16384,"captured table allocation");seen.add(addr)
   for index,value in t["entries"].items():
    at=int(index);need(0<=at<g//8 and value!=0,"captured sparse descriptor")
    struct.pack_into("<Q",tables,addr-table_base+8*at,value)
  need(len(seen)==i["tables_used"],"captured table count")
  ram_path=out/(name+".ram-before.bin");table_path=out/(name+".tables.bin");ram_path.write_bytes(ram);table_path.write_bytes(tables)
  expect=bytearray(ram);struct.pack_into("<QQ",expect,data-base,i["data_after0"],i["data_after1"]);expected[name]=expect
  controls=dict(abi_version=3,struct_size=80,profile=2,reserved=0,sctlr=i["sctlr_before"],ttbr0=i["ttbr0"],ttbr1=i["ttbr1"],tcr=i["tcr"],mair=i["mair"],hcr=0,scr=0,epoch=1)
  fmt=lambda d:",".join(k+":"+str(v) for k,v in d.items())
  rust_cases.append("Case{name:"+json.dumps(name)+",ram:"+json.dumps(str(ram_path))+",tables:"+json.dumps(str(table_path))+",base:"+str(base)+",table_base:"+str(table_base)+",entry:"+str(i["entry"])+",stack:"+str(stack)+",pstate:"+str(o["spsr"])+",data_va:"+str(i["data_va"])+",store:"+str(i["store_operand"])+",controls:m::Controls{"+fmt(controls)+"}}")
  inputs.append({"name":name,"controls_original_capture":{k:i[k] for k in ("sctlr_before","ttbr0","ttbr1","tcr","mair")},"adapted_controls":controls,"captured_hcr":1<<31,"adapted_hcr":0,"pstate_preserved":o["spsr"],"stack_from_elf":stack,"ram_base":base,"ram_bytes":len(ram),"table_base":table_base,"table_bytes":len(tables),"ram_before_sha256":sha(ram_path),"tables_sha256":sha(table_path),"captured_input":i,"captured_observation":o,"captured_tables":case["observed_tables"]})
 (out/"inputs.json").write_text(json.dumps(inputs,indent=2)+"\n")
 (out/"cases.rs").write_text("fn cases()->Vec<Case>{vec![\n"+",\n".join(rust_cases)+"\n]}\n")
 native=(src/"native_replay.rs").read_text().replace("@RUNTIME@",str(runtime));(out/"native_replay.rs").write_text(native)
 commands=[]
 def run(argv,log=None):
  argv=list(map(str,argv));p=subprocess.run(argv,capture_output=True,text=True,timeout=60)
  record={"argv":argv,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr};commands.append(record)
  (out/"commands.json").write_text(json.dumps(commands,indent=2)+"\n")
  if log:log.write_text(p.stdout)
  need(p.returncode==0,"native build/execution failed: "+p.stderr[-3000:])
  return p.stdout
 lib=out/"libservice.rlib";run([a.rustc,"--edition=2021","--crate-type=rlib","--crate-name=nextcore_memory_service","-Copt-level=2",runtime/"memory-service/src/lib.rs","-o",lib])
 objects=[]
 for name in ("jit","arch","boot_jit","memory_boot","memory_boot_v2","memory_dynamic"):
  obj=out/(name+".o");run([a.clang,"-std=c11","-D_GNU_SOURCE","-O2","-Wall","-Wextra","-Werror","-c",runtime/(name+".c"),"-o",obj]);objects.append(obj)
 obj=out/"observer.o";run([a.clang,"-std=c11","-O2","-Wall","-Wextra","-Werror","-I",runtime,"-c",src/"observer.c","-o",obj]);objects.append(obj)
 exe=out/"native_replay";run([a.rustc,"--edition=2021","-Copt-level=2",out/"native_replay.rs","--extern",f"nextcore_memory_service={lib}","-o",exe,*["-Clink-arg="+str(o) for o in objects]])
 rows=load_observed(run([exe,out],out/"actual.tsv"));cases=[]
 for case in report["cases"]:
  name=case["name"];cpu=rows.pop(("CPU",name));values=rows.pop(("RESULT",name));states=rows.pop(("STATE",name))
  need(len(cpu)==48 and len(values)==len(RESULT) and len(states)==16,"native output field counts")
  actual={"cpu":cpu,"result":dict(zip(RESULT,values)),"architectural":dict(zip(STATE,states[:8])),"effective":dict(zip(STATE,states[8:]))}
  after_ram=(out/(name+".ram-after.bin")).read_bytes();cases.append(compare(case,actual,after_ram,expected[name]))
 need(not rows,"unexpected native cases")
 fault=next(c for c in report["cases"] if c["name"]=="g4096_fetch_unmapped")
 changed=copy.deepcopy(fault);changed["observed"]["esr"]^=1
 positive=next(c for c in cases if c["name"]==fault["name"])
 negative=compare(changed,positive["actual"],(out/(fault["name"]+".ram-after.bin")).read_bytes(),expected[fault["name"]])
 negative_detected=not negative["passed"] and {k for k,v in negative["checks"].items() if not v}=={"guest_esr","reply_esr"}
 (out/"negative-control.json").write_text(json.dumps({"expected_failure":True,"change":"Copy one captured fault expectation and xor only expected ESR bit0; captured report and actual execution unchanged","comparison":negative,"detected":negative_detected},indent=2)+"\n")
 after={p:sha(runtime/p) for p in frozen};original_after={p:sha(oracle/p) for p in manifest};tool_after={p:sha(src/p) for p in tool_inputs}
 passed=all(c["passed"] for c in cases) and negative_detected and after==before and original_after==original and tool_before==tool_after
 result={"schema":"nextcore.bp34-captured-arm-native-dynamic-comparison.v1","passed":passed,"case_count":6,"cases":cases,
    "negative_control_detected":negative_detected,"runtime_source_freeze_sha256":sha(freeze),"runtime_source_sha256_before":before,"runtime_source_sha256_after":after,
    "original_public_manifest_sha256":sha(oracle/"manifest.json"),"original_public_preserved":original==original_after,"tool_sha256_before":tool_before,"tool_sha256_after":tool_after,
    "actual_native_executable_sha256":sha(exe),"captured_arm_elf_sha256":sha(elf),"native_generated_x86_executed":True,"canonical_dynamic_service_used":True,
    "hvc_supported":False,"hvc_boundary":"Original HVC0x34 remains at codeVA+40. Compare guaranteed post-ISB effects before it. Native status8/undefined with exact ESR0x02000000, ELR at HVC and SPSR3c5 is separately asserted diagnostic policy, not equality to the actual Arm HVC-to-EL2 completion state; HVC is not retired by native.",
    "initial_adapter_correction":"run1 preserved: two success cases failed guessed native status13/empty ELR-SPSR. Canonical source and actual execution establish status8/undefined and exception-bank bookkeeping at unchanged HVC. No architecture expectation, input or runtime was changed.",
    "entry_adaptations":{"hcr":"Captured RW-only0x80000000 checked; inactive native/service HCR0, with no stage2 or TGE bits removed.","scr":"Uncaptured EL3 state represented as inactive0; no equality claimed.","pstate":"Exact captured3c5 retained; entry ERET/SPSR source establishes this state and payload has no flag/state writes. No masking.","stack":"Original SP_EL1 symbol from ELF/start.S setup; no payload SP access. EL2 setup/handlers are not executed by native.","other_registers":"Authored x0-x3 and initially zero x10-x14 are initialized from entry source. Only captured witness registers x10-x14 are compared to Arm; unobserved caller registers are reset to zero without equality claims."},
    "backing_provenance":{"direct_capture":"All used table page addresses/nonzero entries, initial EL1 controls, target VAs/PAs and initial/final two data words.","reconstruction":"Explicitly zeroed full512KiB table allocation and64KiB transition/target/data arrays; original ELF payload bytes copied at captured offsets.","whole_ram_comparison":"Native unchanged bytes outside the authored store are checked against source-based reconstruction; original Arm capture directly samples only two data words."},
    "pre_isb_timing_compared":False,"hardware_tlb_refill_observed":False,"physical_arm_verified":False,"efi_executed":False,"original_os_boot_verified":False,"guest_metal_verified":False,
    "rustc_version":run([a.rustc,"--version"]).strip(),"clang_version":run([a.clang,"--version"]).splitlines()[0]}
 (out/"receipt.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({"passed":passed,"case_count":6,"negative_detected":negative_detected,"failures":[{"name":c["name"],"status":c["actual"]["result"]["status"],"pc":hex(c["actual"]["cpu"][32]),"failed_checks":[k for k,v in c["checks"].items() if not v]} for c in cases if not c["passed"]]},indent=2))
 return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())
