#!/usr/bin/env python3
"""Build/execute typed MSL render frontend tests; no GPU or Apple compiler claim."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ['Runtime/RenderShaderJit.hpp', 'Runtime/RenderShaderJit.cpp',
          'tests/render_fixture.hpp', 'tests/render_shader_tests.cpp', 'Tools/run-render-shader-tests.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cxx', default=shutil.which('g++') or shutil.which('clang++'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    output = args.out.resolve()
    if not args.cxx or output.exists() or output == ROOT or output in ROOT.parents:
        parser.error('A compiler and new scratch output directory are required')
    compiler = shutil.which(args.cxx) or args.cxx
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'FAIL', 'gpu_executed': False, 'apple_compiler_used': False,
              'sanitizers_enabled': args.sanitize,
              'source_sha256': {name: digest(ROOT / name) for name in INPUTS}}
    env = os.environ.copy()
    env['PATH'] = str(Path(compiler).resolve().parent) + os.pathsep + env.get('PATH', '')
    if args.sanitize:
        env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    passed = False
    try:
        binary = output / ('render-shader-tests.exe' if os.name == 'nt' else 'render-shader-tests')
        flags = ['-std=c++17', '-O1' if args.sanitize else '-O2', '-Wall', '-Wextra', '-Werror']
        if args.sanitize:
            flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
        command = [compiler, *flags, str(ROOT / 'Runtime/RenderShaderJit.cpp'),
                   str(ROOT / 'tests/render_shader_tests.cpp'), '-o', str(binary)]
        process = subprocess.run(command, capture_output=True, text=True, env=env, timeout=120)
        report['build'] = {'command': command, 'exit_code': process.returncode,
                           'stdout': process.stdout, 'stderr': process.stderr}
        if process.returncode:
            raise ValueError('Frontend test compilation failed')
        report['binary_sha256'] = digest(binary)
        command = [str(binary), str(output / 'triangle.vert'), str(output / 'gradient.frag')]
        process = subprocess.run(command, capture_output=True, text=True, env=env, timeout=60)
        report['test'] = {'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}
        result = json.loads(process.stdout)
        if process.returncode or result.get('failures') != 0 or type(result.get('checks')) is not int or result['checks'] < 900:
            raise ValueError('Frontend runtime checks failed')
        if result.get('hardware_execution') is not False or result.get('apple_compiler_used') is not False:
            raise ValueError('Frontend test scope mismatch')
        report['result'] = result
        report['generated_glsl_sha256'] = {name: digest(output / name) for name in ['triangle.vert', 'gradient.frag']}
        if report['binary_sha256'] != digest(binary):
            raise ValueError('Test executable changed during execution')
        passed = True
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        report['error'] = str(error)
    report['source_changed'] = [name for name, before in report['source_sha256'].items()
                                if not (ROOT / name).is_file() or digest(ROOT / name) != before]
    passed = passed and not report['source_changed']
    report['status'] = 'PASS_RENDER_SHADER_FRONTEND' if passed else 'FAIL'
    path = output / 'render-shader-tests.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'checks': report.get('result', {}).get('checks', 0), 'report': str(path)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
