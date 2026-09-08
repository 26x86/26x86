#!/usr/bin/env python3
"""Authored A64 conditional-compare oracle and deliberately incorrect controls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CONDITIONS="eq ne cs cc mi pl vs vc hi ls ge lt gt le al nv".split()

def holds(cond,nzcv):
    n,z,c,v=[bool(nzcv&(1<<bit)) for bit in [3,2,1,0]]
    # An independent full truth table; runtime condition code is not imported.
    return [z,not z,c,not c,n,not n,v,not v,c and not z,not c or z,
            n==v,n!=v,not z and n==v,z or n!=v,True,True][cond]

def arithmetic(a,b,width,subtract):
    mask=(1<<width)-1;sign=1<<(width-1);a&=mask;b&=mask
    unbounded=a-b if subtract else a+b;value=unbounded&mask
    carry=a>=b if subtract else unbounded>mask
    signed=lambda x:x-(1<<width) if x&sign else x
    signed_result=signed(a)-signed(b) if subtract else signed(a)+signed(b)
    overflow=not (-sign<=signed_result<sign)
    return (int(bool(value&sign))<<3)|(int(value==0)<<2)|(int(carry)<<1)|int(overflow)

def cases():
    result=[]
    edge=[0,1,31,0x7fffffff,0x80000000,0xffffffff,0x7fffffffffffffff,0x8000000000000000,0xffffffffffffffff]
    for width in [32,64]:
      for subtract in [False,True]:
       for immediate in [False,True]:
        for condition in range(16):
         for flags in range(16):
          a=edge[(condition+flags)%len(edge)];b=(condition+flags)%32 if immediate else edge[(condition*3+flags+1)%len(edge)]
          wanted=arithmetic(a,b,width,subtract)
          result.append((width,subtract,immediate,a,b,condition,flags,wanted^15,False,False))
        for fallback in range(16):
          result.append((width,subtract,immediate,0x98765432,3,1,4,fallback,False,False))
       for imm in range(32):
        for a in edge:
          result.append((width,subtract,True,a,imm,14,0,15,False,False))
       for a in edge:
        for b in edge:
          result.append((width,subtract,False,a,b,15,0,15,False,False))
       for rn,rm in [(True,False),(False,True),(True,True)]:
        result.append((width,subtract,False,0xfedcba9876543210,0x123456789abcdef0,14,0,15,rn,rm))
       result.append((width,subtract,True,0xffffffffffffffff,31,14,0,15,True,False))
    return result

def constant(reg,value):
    return [f"movz {reg}, #{value&65535}"]+[f"movk {reg}, #{value>>shift&65535}, lsl #{shift}" for shift in [16,32,48]]

def program(items,control):
    lines=[".section .text", ".global _start","_start:","adr x22, stack_top","mov sp,x22","mov x19,#0"]
    for index,(width,sub,imm,a,b,cond,old,fallback,zrn,zrm) in enumerate(items):
        av=0 if zrn else a;bv=b if imm or not zrm else 0
        execute=holds(cond,old) and not(control=="nv_never" and cond==15)
        expected=arithmetic(av,bv,width,sub) if execute else fallback
        if control=="wrong_flags" and index==0:expected^=1
        reg="x" if width==64 else "w";rn=reg+"zr" if zrn else reg+"0"
        operand=f"#{b}" if imm else reg+"zr" if zrm else reg+"1"
        lines+=constant("x0",a)+constant("x1",b)+["mov x20,x0","mov x21,x1",f"mov x9, #{old<<28}","msr nzcv,x9",
            f"{'ccmp' if sub else 'ccmn'} {rn}, {operand}, #{fallback}, {CONDITIONS[cond]}","mrs x10,nzcv",
            f"mov x11, #{expected<<28}","cmp x10,x11","b.ne fail","cmp x0,x20","b.ne fail","cmp x1,x21","b.ne fail",
            "mov x9,sp","cmp x9,x22","b.ne fail","add x19,x19,#1"]
    lines += ["adr x1,success","mov x0,#4","hlt #0xf000","mov x9,#0","b exit","fail:","adr x1,failure","mov x0,#4","hlt #0xf000","mov x9,#1",
        "exit:","adr x1,exit_block","str x9,[x1,#8]","mov x0,#0x20","hlt #0xf000","b .",
        f'success: .asciz "CONDITIONAL_COMPARE_ORACLE: PASS {len(items)} cases\\n"',
        'failure: .asciz "CONDITIONAL_COMPARE_ORACLE: FAIL\\n"',".balign 8","exit_block: .quad 0x20026,0",".balign 16",".zero 4096","stack_top:"]
    return "\n".join(lines)+"\n"

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--work-dir",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();work=args.work_dir.resolve();work.mkdir(parents=True,exist_ok=True);records=[];items=cases()
    source=Path(__file__).resolve();before=hashlib.sha256(source.read_bytes()).hexdigest()
    for control in ["correct","nv_never","wrong_flags"]:
        assembly=work/(control+".S");obj=work/(control+".o");elf=work/(control+".elf");assembly.write_text(program(items,control))
        commands=[["clang","--target=aarch64-none-elf","-c",str(assembly),"-o",str(obj)],["ld.lld","-Ttext=0x40080000","-e","_start",str(obj),"-o",str(elf)],
            ["qemu-system-aarch64","-machine","virt","-cpu","max","-m","128","-nographic","-monitor","none","-serial","none","-net","none","-semihosting-config","enable=on,target=native","-kernel",str(elf)]]
        for index,command in enumerate(commands):
            r=subprocess.run(command,capture_output=True,text=True,timeout=45);record={"case":control,"command":command,"returncode":r.returncode,"stdout":r.stdout,"stderr":r.stderr};records.append(record)
            expected=1 if index==2 and control!="correct" else 0
            assert r.returncode==expected,record
        assert ("PASS" if control=="correct" else "FAIL") in records[-1]["stderr"]+records[-1]["stdout"]
    rejected=[]
    for instruction in ["ccmp sp,x1,#0,al","ccmn x0,sp,#0,al","ccmp w0,#32,#0,al","ccmn x0,#1,#16,al"]:
        assembly=work/"invalid.S";assembly.write_text(instruction+"\n");command=["clang","--target=aarch64-none-elf","-c",str(assembly),"-o",str(work/"invalid.o")]
        r=subprocess.run(command,capture_output=True,text=True,timeout=20);assert r.returncode!=0
        rejected.append({"instruction":instruction,"returncode":r.returncode,"stderr":r.stderr})
    assert before==hashlib.sha256(source.read_bytes()).hexdigest()
    result={"schema":"nextcore.conditional-compare-oracle/1","passed":True,"cases":len(items),"conditions":16,"incoming_nzcv":16,"immediate_values":32,"fallback_values":16,"source_sha256":before,
        "negative_controls_detected":["nv_never","wrong_flags"],"invalid_assembly_rejected":rejected,"records":records,"apple_assets_used":False,"macos_boot_verified":False}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"passed":True,"cases":len(items),"receipt":str(args.output)}))
if __name__=="__main__":main()
