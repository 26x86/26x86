#!/usr/bin/env python3
"""Build actual XeFirmware/XeSubmission source and execute host contract tests."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--firmware',type=Path)
p.add_argument('--report',type=Path)
p.add_argument('--compiler',default=shutil.which('g++') or shutil.which('clang++'))
args=p.parse_args()
if not args.compiler:raise SystemExit('C++ compiler missing; tests not run.')
with tempfile.TemporaryDirectory(prefix='mellow-xe-submission-') as tmp:
    exe=Path(tmp)/('test.exe' if __import__('os').name=='nt' else 'test')
    cmd=[args.compiler,'-std=c++17','-Wall','-Wextra','-Werror','-DMELLOW_XE_TESTS','-I'+str(root/'Mellow'),
         str(root/'Mellow/XeFirmware.cpp'),str(root/'Mellow/XeSubmission.cpp'),
         str(root/'tests/xe_submission_tests.cpp'),'-o',str(exe)]
    build=subprocess.run(cmd,capture_output=True,text=True)
    if build.returncode:raise SystemExit(build.stdout+build.stderr)
    run=subprocess.run([str(exe)]+([str(args.firmware.resolve())] if args.firmware else []),capture_output=True,text=True)
    if run.returncode:raise SystemExit(run.stdout+run.stderr)
    result=json.loads(run.stdout)
if args.firmware:result['firmware']['sha256']=hashlib.sha256(args.firmware.read_bytes()).hexdigest()
result['status']='passed'
result['scope']='host code execution; no GPU firmware load, DMA, IRQ or compute execution'
text=json.dumps(result,indent=2)
if args.report:
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(text+'\n',encoding='utf-8')
print(text)
