#!/usr/bin/env python3
"""Execute actual Xe component tests on host mocks; never loads a GPU driver."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cxx',default=shutil.which('g++') or shutil.which('clang++'))
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--firmware',type=Path)
args=parser.parse_args()
if not args.cxx: parser.error('--cxx compiler is required')
args.out.mkdir(parents=True,exist_ok=True)
results=[]
def execute(label,command):
    try:
        run=subprocess.run([str(x) for x in command],capture_output=True,text=True,timeout=180)
        item={'name':label,'command':[str(x) for x in command],'exit':run.returncode,'output':run.stdout+run.stderr}
    except subprocess.TimeoutExpired:
        item={'name':label,'exit':None,'output':'Timeout after 180 seconds'}
    results.append(item)
    print(label,'PASS' if item['exit']==0 else 'FAIL',flush=True)
    if item['output']: print(item['output'].strip(),flush=True)
    return item['exit']==0

specs=[('xe_memory_tests',['XeMemory.cpp']),
       ('xe_page_table_tests',['XeMemory.cpp','XePageTable.cpp']),
       ('xe_mmio_tests',['XeMmioAccess.cpp']),
       ('xe_page_table_iokit_tests',['XeMemory.cpp','XePageTable.cpp','XePageTableIOKit.cpp']),
       ('xe_zebin_tests',['XeMemory.cpp','XeZebin.cpp']),
       ('xe_bridge_tests',['XeMemory.cpp','XeFirmware.cpp','XeSubmission.cpp'])]
for name,sources in specs:
    if 'XeMemory.cpp' in sources:
        sources = [*sources, 'PortedXeBindings.cpp']
    exe=args.out/(name+('.exe' if sys.platform=='win32' else ''))
    if execute(name+' compile',[args.cxx,'-std=c++17','-O2','-Wall','-Wextra','-Werror','-pedantic',
        '-I'+str(root/'Mellow'),*(['-I'+str(root/'tests/iokit_types')] if name=='xe_page_table_iokit_tests' else []),
        root/'tests'/(name+'.cpp'),*[root/'Mellow'/x for x in sources],'-o',exe]):
        extra=[root/'compiler-evidence/mellow_evidence_mtl.bin'] if name=='xe_zebin_tests' else []
        execute(name,[exe.resolve(),*extra])
submission=[sys.executable,root/'tests/xe_submission_test.py','--compiler',args.cxx,
            '--report',args.out/'xe-submission.json']
if args.firmware: submission+=['--firmware',args.firmware.resolve()]
execute('xe_submission_tests',submission)
execute('xe_guc_tests',[sys.executable,root/'tests/xe_guc_test.py','--compiler',args.cxx,
                        '--report',args.out/'xe-guc.json'])
execute('metal_evidence_tests',[sys.executable,root/'tests/metal_evidence_tests.py'])
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'passed':all(x['exit']==0 for x in results),'results':results,
        'scope':'Actual software components with synthetic host backends and optional real firmware metadata; no GPU execution',
        'iokit_pin_runtime_tested':False,'gpu_page_table_publication_tested':False,'guc_authentication_tested':False,'metal_tested':False}
(args.out/'xe-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
