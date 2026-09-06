#!/usr/bin/env python3
"""Reproduce the 0.4 runtime host tests; never loads or accesses a GPU driver."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
# Exact production translation units linked by each new native host harness.
SPECS = [
    ('xe_context_tests', ['XeContext.cpp', 'XeMemory.cpp']),
    ('xe_dispatch_tests', ['XeDispatch.cpp', 'XeContext.cpp', 'XeMemory.cpp', 'XeZebin.cpp']),
    ('xe_context_execution_tests', ['XeContextExecution.cpp', 'XeContext.cpp',
        'XeDispatch.cpp', 'XeMemory.cpp', 'XeZebin.cpp', 'XeGuCTransport.cpp',
        'XeFirmware.cpp', 'XeFence.cpp']),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths = []
    for directory in ('Mellow', 'Drivers/PortedXe', 'tests', 'Userspace'):
        paths.extend(path for path in (ROOT / directory).rglob('*')
                     if path.is_file() and path.suffix in ('.cpp', '.hpp', '.h', '.inc', '.inl', '.py'))
    paths.extend((ROOT / 'Tools').glob('*.py'))
    paths.append(ROOT / 'compiler-evidence/mellow_evidence_mtl.bin')
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(set(paths))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cxx', default=shutil.which('g++') or shutil.which('clang++'),
                        help='Host C++17 compiler executable; g++ or clang++')
    parser.add_argument('--out', type=Path, required=True,
                        help='Scratch binaries and aggregate runtime-tests.json directory')
    parser.add_argument('--firmware', type=Path, required=True,
                        help='Original pinned mtl_guc_70.bin; metadata/emulator tests only')
    parser.add_argument('--baseline', action='store_true',
                        help='Also invoke the existing Tools/run-xe-tests.py suite')
    args = parser.parse_args()
    if not args.cxx:
        parser.error('--cxx is required when no compiler is on PATH')
    if not args.firmware.is_file():
        parser.error('--firmware must name the original Intel firmware file')
    args.out = args.out.resolve()
    args.firmware = args.firmware.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    temporary = args.out / 'temporary'
    temporary.mkdir(exist_ok=True)
    reports = args.out / 'components'
    reports.mkdir(exist_ok=True)
    # The existing Metal lifecycle test writes its report in this directory.
    (ROOT / 'validation').mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(TMP=str(temporary), TEMP=str(temporary), TMPDIR=str(temporary),
               PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    before = source_hashes()
    results = []

    def execute(label, command, component_report=None):
        command = [str(value) for value in command]
        started = time.monotonic()
        item = dict(name=label, command=command, cwd=str(ROOT), returncode=None,
                    hardware_executed=False)
        try:
            run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                 text=True, encoding='utf-8', errors='replace', timeout=240)
            item.update(returncode=run.returncode, stdout=run.stdout, stderr=run.stderr)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''
            item.update(error='Timeout after 240 seconds', stdout=decoded(error.stdout),
                        stderr=decoded(error.stderr))
        except OSError as error:
            item.update(error=str(error), stdout='', stderr='')
        item['elapsed_seconds'] = round(time.monotonic() - started, 3)
        if item['returncode'] == 0 and component_report is not None:
            try:
                item['component_report'] = json.loads(component_report.read_text(encoding='utf-8-sig'))
                if item['component_report'].get('passed') is False:
                    item['error'] = 'Component reported passed=false despite exit zero'
            except (OSError, ValueError, AttributeError) as error:
                item['error'] = 'Missing/invalid component report: ' + str(error)
        results.append(item)
        ok = item['returncode'] == 0 and 'error' not in item
        print(label + ': ' + ('PASS' if ok else 'FAIL'), flush=True)
        if not ok:
            print(item.get('error', '') + '\n' + item.get('stdout', '') + item.get('stderr', ''), flush=True)
        return ok

    execute('compiler_version', [args.cxx, '--version'])
    for name, sources in SPECS:
        if 'XeMemory.cpp' in sources:
            sources = [*sources, 'PortedXeBindings.cpp']
        binary = args.out / (name + ('.exe' if os.name == 'nt' else ''))
        command = [args.cxx, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                   '-I' + str(ROOT / 'Mellow'), ROOT / 'tests' / (name + '.cpp'),
                   *[ROOT / 'Mellow' / source for source in sources], '-o', binary]
        if execute(name + '_compile', command):
            arguments = [] if name == 'xe_context_tests' else [ROOT / 'compiler-evidence/mellow_evidence_mtl.bin']
            execute(name, [binary, *arguments])

    for label, script in (
        ('guc_transport', 'xe_guc_test.py'),
        ('guc_firmware', 'xe_guc_firmware_test.py'),
        ('interrupt_fence', 'xe_interrupt_test.py'),
        ('interrupt_fence_iokit', 'xe_interrupt_iokit_test.py'),
    ):
        destination = reports / (label + '.json')
        command = [sys.executable, ROOT / 'tests' / script, '--compiler', args.cxx,
                   '--report', destination]
        if label == 'guc_firmware':
            command += ['--firmware', args.firmware]
        execute(label, command, destination)
    execute('metal_session', [sys.executable, ROOT / 'tests/metal_session_tests.py'],
            ROOT / 'validation/metal-session-tests.json')
    if args.baseline:
        baseline = args.out / 'baseline'
        execute('xe_baseline', [sys.executable, ROOT / 'Tools/run-xe-tests.py',
            '--cxx', args.cxx, '--out', baseline, '--firmware', args.firmware], baseline / 'xe-tests.json')

    after = source_hashes()
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    report = dict(schema_version=1, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        host=platform.platform(), python=sys.version, compiler=str(args.cxx),
        passed=bool(results) and not changed and all(item['returncode'] == 0 and 'error' not in item for item in results),
        hardware_executed=False, native_metal_executed=False, driver_loaded=False,
        scope='Real production source with explicit host MMIO, DMA, OS and GPU-peer simulations; no physical GPU, IRQ, firmware upload or Metal execution',
        baseline_included=args.baseline, firmware_sha256=digest(args.firmware),
        source_sha256=before, source_changed_during_run=changed,
        production_sources={name: ['Mellow/' + source for source in
            (sources + ['PortedXeBindings.cpp'] if 'XeMemory.cpp' in sources else sources)]
            for name, sources in SPECS},
        results=results)
    target = args.out / 'runtime-tests.json'
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Aggregate: ' + ('PASS' if report['passed'] else 'FAIL') + ' -> ' + str(target), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
