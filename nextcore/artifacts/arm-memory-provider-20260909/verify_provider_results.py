#!/usr/bin/env python3
"""Check real EFI provider observations against authored scalar/pair fixtures.

Legacy fixture scripts remain byte-for-byte copies. This additional verifier
requires the provider ABI result, exact request/commit counts, and data FAR.
SP-alignment FAR is recorded but has no architectural-value assertion here.
"""
import argparse, hashlib, json, re
from pathlib import Path
SCALAR_COUNTS={"byte-signed":6,"half-signed":5,"word-signed":3,"quad-zr":5}
PATTERN=re.compile(r"NXARMJIT: TRACE_MEMORY_RESULT abi=(\d+) provider_status=(\d+) guest_far=(0x[0-9a-f]+) last_address=(0x[0-9a-f]+) fetch_requests=(\d+) data_requests=(\d+) completed_data_operations=(\d+)")
FIELDS=["abi","provider_status","guest_far","last_address","fetch_requests","data_requests","completed_data_operations"]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observation(path):
    serial=(path/"serial.log").read_text(errors="replace")
    matches=PATTERN.findall(serial)
    result={key:int(value,0) for key,value in zip(FIELDS,matches[0])} if len(matches)==1 else {}
    return result, serial.count("NXARMJIT: TRACE_MEMORY_PROVIDER abi=1 mode=m0-only")==1

def check_case(kind,name,path):
    raw=json.loads((path/"report.json").read_text());e=raw.get("execution") or {}
    observed,marker=observation(path);retired=e.get("retired",-1);status=e.get("status")
    regs=e.get("registers") or {};exc=e.get("exception") or {}
    success=status==1
    data=SCALAR_COUNTS.get(name,0) if kind=="scalar" else (12 if name=="pair-readback" else 0)
    if name.startswith("a0-device-"): data=1
    completed=data if success else 0
    fetched=retired+(0 if success else 1)
    expected={"abi":1,"provider_status":0,"fetch_requests":fetched,"data_requests":data,"completed_data_operations":completed}
    if name.startswith("a0-device-"):
        far=regs.get("x2",0)
        if kind=="pair":far-=8 if "load" in name else 16
        expected.update(guest_far=far,last_address=far)
    else:
        expected["last_address"]=e.get("pc",0)-(4 if success else 0)
        if not name.startswith("sp-"):expected["guest_far"]=0
    checks={"diagnostic_completed":raw.get("diagnostic_completed") is True,
            "inputs_preserved":raw.get("original_inputs_preserved") is True and raw.get("esp_copies_preserved") is True,
            "provider_build_marker":marker,"provider_result_present":bool(observed),
            "one_native_entry_per_executed_instruction":e.get("compiled_blocks")==fetched}
    checks.update({"provider_"+key:observed.get(key)==value for key,value in expected.items()})
    return {"kind":kind,"name":name,"passed":all(checks.values()),"checks":checks,
            "expected":expected,"observed":observed,"execution":e,
            "serial_sha256":digest(path/"serial.log"),"report_sha256":digest(path/"report.json")}

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument("--scalar",type=Path);a.add_argument("--pair",type=Path)
    a.add_argument("--byte-case",type=Path,help="one existing byte fixture run; also tests actual direct-path bypass")
    a.add_argument("--output",type=Path,required=True);args=a.parse_args();cases=[];legacy=[]
    for kind,folder in [("scalar",args.scalar),("pair",args.pair)]:
        if folder:
            receipt=json.loads((folder/"report.json").read_text());legacy.append(receipt.get("passed") is True)
            for case in receipt["cases"]:cases.append(check_case(kind,case["name"],folder/case["name"]))
    if args.byte_case:cases.append(check_case("scalar","byte-signed",args.byte_case))
    passed=bool(cases) and all(legacy) and all(c["passed"] for c in cases)
    report={"schema":"nextcore.efi-provider-observations.v1","passed":passed,"cases":cases,
            "legacy_fixture_verifiers_passed":all(legacy),"actual_win64_c_rust_callback_observed":passed,
            "sp_alignment_far_asserted":False,"guest_ram_after_fault_observed":False,
            "physical_machine_efi_verified":False,"mmu_enabled_verified":False,"macos_boot_verified":False,"guest_metal_verified":False}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"passed":passed,"cases":len(cases),"receipt":str(args.output)}));return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())
