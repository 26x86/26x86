#!/usr/bin/env python3
"""Compile actual production function bodies against explicit host-only mocks.

This checks return propagation and binary-edit boundaries, not Darwin ABI or GPU
execution. No kernel, PCI, firmware, or installed EFI is accessed.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def extract(source, signature):
    start = source.index(signature)
    # Count braces after blanking comments and strings, preserving offsets.
    tokens = r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    cleaned = re.sub(tokens, lambda m: ' ' * len(m[0]), source)
    op = cleaned.index('{', start)
    depth, end = 1, op + 1
    while depth:
        depth += (cleaned[end] == '{') - (cleaned[end] == '}')
        end += 1
    return source[start:end]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', default=shutil.which('g++') or shutil.which('clang++'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not args.compiler:
        raise SystemExit('A native C++ compiler is required; no tests ran.')
    gen11 = (ROOT/'Mellow/kern_gen11.cpp').read_text(encoding='utf-8')
    genx = (ROOT/'Mellow/kern_genx.cpp').read_text(encoding='utf-8')
    dyld = (ROOT/'Mellow/DYLDPatches.cpp').read_text(encoding='utf-8')
    functions = '\n\n'.join(extract(gen11, sig) for sig in [
        'static int getV142SubmitBlitMode()',
        'uint8_t Gen11::deviceStart(',
        'unsigned long Gen11::submitBlit(',
        'bool Gen11::wrapIGScheduler4IsGpuIdle(',
        'bool Gen11::wrapIGScheduler5IsGpuIdle(',
        'void *Gen11::wrapIgBufferWithOptions(',
        'unsigned long Gen11::loadGuCBinary(',
        'IOReturn Gen11::wrapPavpSessionCallback(',
        'uint8_t Gen11::barrierSubmission(',
    ]) + '\n' + extract(genx, 'static bool patchStolenMemoryFormula(')
    source = (ROOT/'tests/accel_contracts_harness.cpp').read_text(encoding='utf-8')
    source = source.replace('// PRODUCTION_FUNCTIONS', functions)
    with tempfile.TemporaryDirectory(prefix='mellow-accel-tests-') as temp:
        temp = Path(temp)
        cpp = temp/'accel_contracts.cpp'
        exe = temp/('accel_contracts.exe' if __import__('os').name == 'nt' else 'accel_contracts')
        cpp.write_text(source, encoding='utf-8')
        build = subprocess.run([args.compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                                '-I'+str(ROOT/'tests/accel_hde'), str(cpp),
                                str(ROOT/'tests/accel_hde/hde64.c'), '-o', str(exe)],
                               capture_output=True, text=True)
        if build.returncode:
            raise SystemExit(build.stdout + build.stderr)
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        if run.returncode:
            raise SystemExit(run.stdout + run.stderr)
        result = json.loads(run.stdout)

    # These are integration guards, separate from the native behavior tests.
    assert 'getKernelVersion() != KernelVersion::Sonoma' in dyld
    assert '!checkKernelArgument("-mellowlegacydyld")' in dyld
    assert 'f_accesscomplete_' not in dyld
    assert 'f_devstart' not in gen11
    assert 'gGfxAccelStartDone = ret != 0' in gen11
    result.update(integration_guards=5, scope='host mocks; not GPU or macOS execution',
                  compiler=args.compiler, status='passed')
    rendered = json.dumps(result, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered+'\n', encoding='utf-8')
    print(rendered)


if __name__ == '__main__':
    main()
