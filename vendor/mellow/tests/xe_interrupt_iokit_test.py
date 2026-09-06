#!/usr/bin/env python3
"""Compile production adapter method bodies against an explicit fake OS boundary.

Only includes/macros are supplied by the shim; actual adapter methods are copied
byte-for-byte. This is not a Darwin linker/runtime test or hardware execution.
"""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',default=shutil.which('g++') or shutil.which('clang++'));p.add_argument('--report',type=pathlib.Path);a=p.parse_args()
if not a.compiler:raise SystemExit('No host compiler; not tested')
inputs=[]
with tempfile.TemporaryDirectory(prefix='xe-irq-iokit-') as temp:
    td=pathlib.Path(temp)
    shutil.copyfile(root/'tests/xe_interrupt_iokit_shim.hpp',td/'shim.hpp')
    for base in ['XeInterruptIOKit','XeFenceIOKit']:
        hp=root/'Mellow'/f'{base}.hpp';cp=root/'Mellow'/f'{base}.cpp';inputs += [hp,cp]
        content=hp.read_text()
        for inc in ['#include "XeMmioIOKit.hpp"','#include <IOKit/IOFilterInterruptEventSource.h>','#include <IOKit/IOWorkLoop.h>','#include <IOKit/IOMemoryDescriptor.h>']:
            content=content.replace(inc,'')
        (td/hp.name).write_text('#include "shim.hpp"\n'+content)
        shutil.copyfile(cp,td/cp.name)
    test=root/'tests/xe_interrupt_iokit_tests.cpp';shutil.copyfile(test,td/test.name)
    inputs += [test,root/'tests/xe_interrupt_iokit_shim.hpp',root/'Mellow/XeInterrupt.cpp',root/'Mellow/XeFence.cpp']
    exe=td/('adapter.exe' if os.name=='nt' else 'adapter')
    sources=[td/'XeInterruptIOKit.cpp',td/'XeFenceIOKit.cpp',td/test.name,root/'Mellow/XeInterrupt.cpp',root/'Mellow/XeFence.cpp']
    b=subprocess.run([a.compiler,'-std=c++17','-Wall','-Wextra','-Werror','-I'+str(td),'-I'+str(root/'Mellow'),*map(str,sources),'-o',str(exe)],capture_output=True,text=True)
    if b.returncode:raise SystemExit(b.stdout+b.stderr)
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
    if run.returncode:raise SystemExit(run.stdout+run.stderr)
    result=json.loads(run.stdout)
result['scope']='Production IOKit adapter method bodies; fake OS allocation, provider, map and event-source boundary. No actual IRQ synchronization or DMA tested.'
result['source_sha256']={str(x.relative_to(root)).replace('\\','/'):hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs}
if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
