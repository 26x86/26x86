#!/usr/bin/env python3
"""Build the authored macOS-ABI ARM fixture for the x86 EFI translation runtime."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from build_arm64_handoff_probe import image, sha256, PHYSICAL, ENTRY_OFFSET
MARKER = b"NEXTCORE_AUTHORED_ARM64_JIT_V1"
PAC_MARKER = b"NEXTCORE_AUTHORED_ARM64E_JIT_PAC_V1"
def build_probe(output: Path, pac: bool = False) -> dict:
    source=Path(__file__).with_name("arm64_jit_probe.S").resolve(strict=True)
    before=sha256(source);output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    obj,binary=output/"probe.o",output/"probe.bin"
    commands=[["clang","--target=aarch64-none-elf","-march=armv8.3-a",*(["-DNEXTCORE_PAC"] if pac else []),"-c",str(source),"-o",str(obj)],
              ["ld.lld","-Ttext",hex(PHYSICAL+ENTRY_OFFSET),"-e","_start","--oformat=binary",str(obj),"-o",str(binary)]]
    for command in commands:subprocess.run(command,check=True,capture_output=True,text=True,timeout=30)
    code=binary.read_bytes()
    if not code or len(code)>4096 or code.count(PAC_MARKER if pac else MARKER)!=1:raise ValueError("invalid authored payload")
    fixture=output/"probe.kc";fixture.write_bytes(image(code,subtype=2 if pac else 0))
    if sha256(source)!=before:raise RuntimeError("source changed during build")
    receipt={"schema":"nextcore.arm-jit-fixture.v1","image":str(fixture),"image_sha256":sha256(fixture),"source_sha256":before,"code_sha256":sha256(binary),"code_bytes":len(code),"commands":commands,"expected_retired":45 if pac else 25,"pac":pac,"apple_assets_used":False,"xnu_executed":False}
    (output/"fixture.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8");return receipt
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path);parser.add_argument("--pac",action="store_true")
    args=parser.parse_args();print(json.dumps(build_probe(args.output,args.pac),indent=2))
