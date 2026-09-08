#!/usr/bin/env python3
"""Verify the authored public layout on LP64 host and Darwin ARM64 compiler."""
import argparse
import hashlib
import json
import pathlib
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=pathlib.Path)
parser.add_argument('--cc', default='cc')
parser.add_argument('--clang', default='clang-18')
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
source = pathlib.Path(__file__).resolve().with_name('layout_fixture.c')
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {'source_sha256_before': digest(source), 'commands': [], 'guest_executed': False}
commands = [
    ('darwin-arm64', [args.clang, '-target', 'arm64-apple-macos27', '-ffreestanding', '-fsyntax-only', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source)]),
    ('host-build', [args.cc, '-DHOST_LAYOUT_REPORT', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(out / 'layout')]),
    ('host-run', [str(out / 'layout')]),
]
try:
    for name, command in commands:
        process = subprocess.run(command, capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
        (out / (name + '.stdout')).write_bytes(process.stdout)
        (out / (name + '.stderr')).write_bytes(process.stderr)
        receipt['commands'].append({'name': name, 'argv': command, 'exit_code': process.returncode})
        if process.returncode:
            raise RuntimeError(name + ' failed')
    actual = json.loads((out / 'host-run.stdout').read_text())
    expected = {'size': 1152, 'alignment': 8, 'offsets': [0, 2, 8, 16, 24, 32, 40, 88, 96, 104, 108, 1136, 1144]}
    if actual != expected:
        raise RuntimeError('host layout output differs')
    receipt.update(passed=True, layout=actual, host_binary_sha256=digest(out / 'layout'))
except Exception as error:
    receipt.update(passed=False, error=str(error))
receipt['source_sha256_after'] = digest(source)
receipt['source_unchanged'] = receipt['source_sha256_before'] == receipt['source_sha256_after']
receipt['passed'] = receipt.get('passed', False) and receipt['source_unchanged']
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt['passed'] else 1)
