#!/usr/bin/env python3
"""Build and run portable driver contract tests; never loads a GPU driver."""
import argparse
import datetime
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cxx', default=shutil.which('g++') or shutil.which('clang++'))
    parser.add_argument('--out', type=Path, required=True, help='Scratch build/report directory')
    args = parser.parse_args()
    if not args.cxx:
        parser.error('Specify --cxx with an installed C++ compiler')
    root = Path(__file__).resolve().parent.parent
    args.out.mkdir(parents=True, exist_ok=True)
    compiler = subprocess.run([args.cxx, '--version'], capture_output=True, text=True, check=True)
    results = []
    # accel_contracts_harness.cpp requires production function extraction and
    # has its own runner; it must not compile as an independent test program.
    for name in ['HardwareAccessTests.cpp', 'modelTests.cpp', 'patcher_policy_tests.cpp']:
        source = root / 'tests' / name
        binary = args.out / (source.stem + ('.exe' if sys.platform == 'win32' else ''))
        command = [args.cxx, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic', str(source), '-o', str(binary)]
        compile_result = subprocess.run(command, capture_output=True, text=True)
        test = dict(source=source.relative_to(root).as_posix(), compile_exit=compile_result.returncode,
                    compile_output=compile_result.stdout + compile_result.stderr)
        if compile_result.returncode == 0:
            try:
                run = subprocess.run([str(binary.resolve())], capture_output=True, text=True, timeout=30)
                test.update(run_exit=run.returncode, output=run.stdout + run.stderr)
            except subprocess.TimeoutExpired:
                test.update(run_exit=None, output='TIMEOUT after 30 seconds')
        results.append(test)
        print(test['source'], 'PASS' if test.get('run_exit') == 0 else 'FAIL')
        if test.get('output'): print(test['output'].strip())
        if compile_result.returncode: print(test['compile_output'])
    passed = bool(results) and all(x.get('run_exit') == 0 for x in results)
    report = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        host=platform.platform(), compiler=compiler.stdout.splitlines()[0],
        scope='Portable driver helpers and contracts; no IOKit loader, firmware, GPU or Metal execution',
        hardware_execution=False, passed=passed, results=results)
    (args.out / 'host-tests.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
