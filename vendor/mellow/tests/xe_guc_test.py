#!/usr/bin/env python3
"""Compile the actual GuC protocol engine and execute native wire/lifecycle tests."""
import argparse, hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--compiler',default=shutil.which('g++') or shutil.which('clang++'))
p.add_argument('--report',type=Path)
a=p.parse_args()
if not a.compiler: raise SystemExit('C++ compiler unavailable: tests not run')
with tempfile.TemporaryDirectory(prefix='mellow-xe-guc-') as tmp:
    exe=Path(tmp)/('guc.exe' if os.name=='nt' else 'guc')
    sources=[root/'Mellow/XeGuCTransport.cpp',root/'tests/xe_guc_tests.cpp']
    build=subprocess.run([a.compiler,'-std=c++17','-Wall','-Wextra','-Werror','-I'+str(root/'Mellow'),*map(str,sources),'-o',str(exe)],capture_output=True,text=True)
    if build.returncode: raise SystemExit(build.stdout+build.stderr)
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
    if run.returncode: raise SystemExit(run.stdout+run.stderr)
    result=json.loads(run.stdout)
result['scope']='Native actual protocol source with emulated peer/MMIO callbacks; no GPU upload, authentication, CTB, IRQ or execution tested on hardware'
result['source_sha256']={str(s.relative_to(root)):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources}
text=json.dumps(result,indent=2)
if a.report:a.report.write_text(text+'\n',encoding='utf-8')
print(text)
