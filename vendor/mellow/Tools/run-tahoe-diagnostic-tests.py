#!/usr/bin/env python3
"""Test actual diagnostic protocol with synthetic memory callbacks; no IOKit runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cxx', default=shutil.which('g++') or shutil.which('clang++'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    if not args.cxx or out.exists() or out == ROOT or out in ROOT.parents:
        parser.error('compiler required; --out must be a new scratch directory')
    out.mkdir(parents=True)
    inputs = [*sorted((ROOT/'Mellow').glob('TahoeDiagnostic*')),
              ROOT/'Mellow/XeMemory.hpp', ROOT/'Mellow/RuntimeReadiness.hpp',
              ROOT/'tests/tahoe_diagnostic_test.cpp', Path(__file__).resolve()]
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}
    report = {'status':'FAIL', 'scope':'production diagnostic protocol with simulated memory callbacks',
              'iokit_runtime_tested':False,'physical_gpu_tested':False,'metal_tested':False,
              'source_sha256':before,'sanitizers_requested':args.sanitize}
    try:
        binary = out / ('diagnostic-tests.exe' if sys.platform == 'win32' else 'diagnostic-tests')
        command = [args.cxx,'-std=c++17','-O1','-g','-Wall','-Wextra','-Werror','-pedantic']
        if args.sanitize: command += ['-fsanitize=address,undefined','-fno-omit-frame-pointer']
        command += [str(ROOT/'Mellow/TahoeDiagnosticProtocol.cpp'),str(ROOT/'tests/tahoe_diagnostic_test.cpp'),'-o',str(binary)]
        build = subprocess.run(command,capture_output=True,text=True,timeout=120)
        report['compile'] = {'command':command,'returncode':build.returncode,'stdout':build.stdout,'stderr':build.stderr}
        if build.returncode: raise ValueError('host compilation failed')
        report['binary_sha256'] = digest(binary)
        run = subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
        report['execution'] = {'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
        if run.returncode: raise ValueError('host tests failed')
        result = json.loads(run.stdout.strip())
        if (result.get('status') != 'PASS_TAHOE_DIAGNOSTIC_PROTOCOL_HOST' or
                type(result.get('checks')) is not int or result['checks'] <= 0 or
                any(result.get(k) is not False for k in ('iokit_runtime_tested','physical_gpu_tested','metal_tested'))):
            raise ValueError('missing or contradictory acceptance result')
        after = {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}
        report['source_hashes_unchanged'] = before == after
        report['binary_unchanged'] = report['binary_sha256'] == digest(binary)
        if not report['source_hashes_unchanged'] or not report['binary_unchanged']:
            raise ValueError('inputs changed during verification')
        report['result'] = result
        report['status'] = result['status']
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        report['error'] = str(error)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':report.get('result',{}).get('checks',0),'report':str(out/'report.json')}))
    return 0 if report['status']=='PASS_TAHOE_DIAGNOSTIC_PROTOCOL_HOST' else 1
if __name__=='__main__': raise SystemExit(main())
