#!/usr/bin/env python3
"""Execute the x86 EFI ARM JIT, real boot-argument readback and GOP scanout.

QEMU models only the x86 test computer; ARM instructions execute in the EFI
image's native x86 code generator. No host ARM QEMU/OS backend is invoked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import re
import shutil
import struct
import subprocess
import time
from build_arm64_jit_probe import build_probe, MARKER
from build_arm64_handoff_probe import PAGE, ENTRY_OFFSET, sha256

ENTRY="NXARMJIT: EFI_ENTRY host=x86_64 guest=arm64"
PARSED="NXARMJIT: CONFIG_PARSED"
VALID="NXARMJIT: KC_VALIDATED "
STAGED="NXARMJIT: STAGING_VERIFIED "
JIT="NXARMJIT: JIT_ENTER host_boot_services=active"
SUCCESS="NXARMJIT: AUTHORED_HANDOFF_OK xnu_executed=false macos_boot_verified=false metal_verified=false"

def lines(path:Path)->list[str]:
    data=path.read_text(encoding="utf-8",errors="replace") if path.exists() else ""
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]","",data).splitlines()
def ordered(actual:list[str],required:list[str])->bool:
    position=0
    for marker in required:
        found=next((index for index in range(position,len(actual)) if actual[index].startswith(marker)),None)
        if found is None:return False
        position=found+1
    return True
def definitions(image:bytes,pac_image:bytes)->list[dict]:
    missing=bytearray(image);missing[missing.index(MARKER)]^=1
    subtype=bytearray(image);struct.pack_into("<I",subtype,8,2);struct.pack_into("<I",subtype,PAGE+8,2)
    wrong=bytearray(image);struct.pack_into("<I",wrong,ENTRY_OFFSET,0xd2800001) # mov x1,#0
    positive=[ENTRY,PARSED,VALID,STAGED,"NXARMJIT: GUEST_ENTRY_READY ",JIT,"NXARMJIT: JIT_RETURN status=1 retired=25 ","NXARMJIT: BOOT_ARGS_READBACK_OK","NXARMJIT: GUEST_FRAMEBUFFER_OK","NXARMJIT: GOP_READBACK_OK pixels=16",SUCCESS]
    pac_positive=[mark.replace("retired=25 ","retired=45 ") for mark in positive]
    pac_positive.insert(8,"NXARMJIT: ARM64E_PAC_READBACK_OK")
    def rejected(name,payload,expected,profile="x86-efi-arm64-jit-probe",binary="probe"):
        return {"name":name,"image":payload,"expected":[ENTRY]+expected,"forbidden":[JIT,SUCCESS],"profile":profile,"binary":binary}
    return [
        {"name":"jit-positive","image":image,"expected":positive,"forbidden":["NXARMJIT: ERROR"],"profile":"x86-efi-arm64-jit-probe","binary":"probe"},
        {"name":"arm64e-pac-positive","image":pac_image,"expected":pac_positive,"forbidden":["NXARMJIT: ERROR"],"profile":"x86-efi-arm64-jit-probe","binary":"probe"},
        rejected("production-gate",image,[PARSED,VALID,STAGED,"NXARMJIT: PROVIDERS_PENDING","NXARMJIT: ERROR status=NOT_READY"],binary="default"),
        rejected("arm64e-production-staging",bytes(subtype),[PARSED,"NXARMJIT: KC_VALIDATED subtype=0x2",STAGED,"NXARMJIT: PROVIDERS_PENDING","NXARMJIT: ERROR status=NOT_READY"],profile="xnu-arm64-uefi"),
        rejected("arm64e-probe-rejected",bytes(subtype),[PARSED,VALID,"NXARMJIT: FIXTURE_REJECTED","NXARMJIT: ERROR status=UNSUPPORTED"]),
        rejected("unmarked-image",bytes(missing),[PARSED,VALID,"NXARMJIT: FIXTURE_REJECTED","NXARMJIT: ERROR status=UNSUPPORTED"]),
        rejected("truncated-image",image[:31],[PARSED,"NXARMJIT: KC_INVALID","NXARMJIT: ERROR status=LOAD_ERROR"]),
        rejected("intel-profile-rejected",image,["NXARMJIT: CONFIG_INVALID reason=UNSUPPORTED_KERNEL_PROFILE","NXARMJIT: ERROR status=INVALID_PARAMETER"],profile="xnu-12377-pstart32"),
        {"name":"guest-data-corruption","image":bytes(wrong),"expected":positive[:7]+["NXARMJIT: ERROR status=COMPROMISED_DATA"],"forbidden":["NXARMJIT: BOOT_ARGS_READBACK_OK",SUCCESS],"profile":"x86-efi-arm64-jit-probe","binary":"probe"},
    ]
def run_case(args,output:Path,spec:dict)->dict:
    directory=output/spec["name"];boot=directory/"esp/EFI/BOOT";boot.mkdir(parents=True)
    oc=directory/"esp/EFI/OC";oc.mkdir();payload=directory/"esp/EFI/NEXTCORE";payload.mkdir()
    shutil.copyfile(args.efi_probe if spec["binary"]=="probe" else args.efi_default,boot/"BOOTX64.EFI")
    (payload/"probe.kc").write_bytes(spec["image"])
    (oc/"config.plist").write_bytes(plistlib.dumps({"Nextcore":{"Kernel":{"Profile":spec["profile"],"Path":"\\EFI\\NEXTCORE\\probe.kc","Arguments":"-v"}}}))
    variables=directory/"vars.fd";shutil.copyfile(args.ovmf_vars,variables);serial=directory/"serial.log"
    command=[args.qemu,"-machine","q35,accel=tcg,smm=off","-cpu","Nehalem","-m","256","-smp","1","-display","none","-vga","std","-monitor","none","-serial",f"file:{serial}","-net","none","-no-reboot",
             "-drive",f"if=pflash,format=raw,readonly=on,file={args.ovmf_code}","-drive",f"if=pflash,format=raw,file={variables}","-drive",f"format=raw,file=fat:rw:{directory/'esp'}"]
    (directory/"command.json").write_text(json.dumps(command,indent=2)+"\n",encoding="utf-8")
    start=time.monotonic();stopped=False
    with (directory/"stdout.log").open("wb") as stdout,(directory/"stderr.log").open("wb") as stderr:
        process=subprocess.Popen(command,stdout=stdout,stderr=stderr)
        try:
            while process.poll() is None and time.monotonic()-start<args.timeout:
                if ordered(lines(serial),spec["expected"]):break
                time.sleep(.1)
        finally:
            if process.poll() is None:
                stopped=True;process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    actual=lines(serial);forbidden=[mark for mark in spec["forbidden"] if any(line.startswith(mark) for line in actual)]
    passed=ordered(actual,spec["expected"]) and not forbidden and process.poll() is not None
    return {"name":spec["name"],"passed":passed,"expected":spec["expected"],"forbidden_observed":forbidden,
            "markers":[line for line in actual if line.startswith("NXARMJIT:")],"qemu_pid":process.pid,"qemu_exit_code":process.returncode,"process_terminated":process.poll() is not None,"stopped_by_harness":stopped,
            "elapsed_seconds":round(time.monotonic()-start,3),"serial_log":str(serial),"fixture_sha256":hashlib.sha256(spec["image"]).hexdigest(),"xnu_executed":False,"macos_boot_verified":False,"metal_verified":False}
def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi-probe",type=Path,required=True);parser.add_argument("--efi-default",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--qemu",default="qemu-system-x86_64");parser.add_argument("--ovmf-code",type=Path,default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"));parser.add_argument("--ovmf-vars",type=Path,default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"));parser.add_argument("--timeout",type=float,default=30);parser.add_argument("--cases")
    args=parser.parse_args()
    if not 0<args.timeout<=60:parser.error("--timeout must be in (0,60]")
    args.qemu=shutil.which(args.qemu) or args.qemu
    fields=["efi_probe","efi_default","ovmf_code","ovmf_vars"]
    for field in fields:
        path=getattr(args,field).resolve(strict=True)
        if not path.is_file() or "," in str(path):parser.error(f"{field} must be a regular path without comma")
        setattr(args,field,path)
    output=args.output.resolve()
    if "," in str(output):parser.error("output must not contain comma")
    output.mkdir(parents=True,exist_ok=False)
    inputs=[getattr(args,f) for f in fields]+[Path(__file__).resolve(),Path(__file__).with_name("arm64_jit_probe.S").resolve()]
    before={str(p):sha256(p) for p in inputs};cases=[];failure=None
    try:
        fixture=build_probe(output/"fixture");pac_fixture=build_probe(output/"fixture-pac",pac=True)
        specs=definitions(Path(fixture["image"]).read_bytes(),Path(pac_fixture["image"]).read_bytes())
        if args.cases:
            names=args.cases.split(",")
            if len(names)!=len(set(names)) or not set(names)<={s["name"] for s in specs}:raise ValueError("unknown or duplicate case")
            specs=[s for s in specs if s["name"] in names]
        for spec in specs:
            result=run_case(args,output,spec);cases.append(result);print(json.dumps(result),flush=True)
    except Exception as error:failure=f"{type(error).__name__}: {error}"
    after={str(p):sha256(p) for p in inputs}
    passed=bool(cases) and all(c["passed"] for c in cases) and before==after and failure is None
    receipt={"schema":"nextcore.x86-efi-arm-jit.v1","host_architecture":platform.machine(),"layer":"x86 EFI native ARM translation + guest boot_args + GOP readback","cases":cases,"failure":failure,"input_sha256_before":before,"input_sha256_after":after,"original_inputs_preserved":before==after,"passed":passed,"xnu_executed":False,"macos_boot_verified":False,"metal_verified":False}
    (output/"report.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":str(output/"report.json"),"passed":passed,"failure":failure}));return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())
