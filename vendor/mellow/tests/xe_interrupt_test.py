#!/usr/bin/env python3
"""Actual IRQ/fence core against explicit host MMIO/coherent-memory emulators."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',default=shutil.which('g++') or shutil.which('clang++'))
p.add_argument('--report',type=pathlib.Path)
a=p.parse_args()
if not a.compiler:raise SystemExit('No host compiler; not tested')
sources=[root/'Mellow/XeInterrupt.cpp',root/'Mellow/XeFence.cpp',root/'Mellow/XeGuCTransport.cpp',root/'tests/xe_interrupt_tests.cpp']
with tempfile.TemporaryDirectory(prefix='xe-irq-') as temp:
    exe=pathlib.Path(temp)/('irq.exe' if os.name=='nt' else 'irq')
    b=subprocess.run([a.compiler,'-std=c++17','-Wall','-Wextra','-Werror','-I'+str(root/'Mellow'),*map(str,sources),'-o',str(exe)],capture_output=True,text=True)
    if b.returncode:raise SystemExit(b.stdout+b.stderr)
    x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
    if x.returncode:raise SystemExit(x.stdout+x.stderr)
    result=json.loads(x.stdout)
result['scope']='Actual production IRQ/fence source; emulated MMIO and host memory. No physical GPU interrupt, DMA or completion observed.'
inputs=sources+list((root/'Mellow').glob('XeInterrupt*.hpp'))+list((root/'Mellow').glob('XeFence*.hpp'))
result['source_sha256']={str(s.relative_to(root)).replace('\\','/'):hashlib.sha256(s.read_bytes()).hexdigest() for s in inputs}
if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
