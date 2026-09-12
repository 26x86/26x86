#!/usr/bin/env python3
"""Authored actual EFI acceptance for immutable mapped profile3 and native reuse.

Contract: both current binaries must execute the same long65536 fixture through
the canonical mapped service, preserve inputs, and report identical execution
and request windows. Low physical boot args encode revision2/version2. High ADR,
unaligned transfers, XPACI, and disabled PACDA are checked by the guest. The old
binary must not satisfy mapped acknowledgements; host rejection alone is never
reported as proof that old firmware parsed and rejected the new selector.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from build_arm64_handoff_probe import image, PHYSICAL, VIRTUAL, ENTRY_OFFSET

BUDGET = 65536
VALUE = 0x1122334455667788


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prop(name, value):
    return name.encode().ljust(32, b'\0') + struct.pack('<I', len(value)) + value.ljust((len(value) + 3) & ~3, b'\0')


def observations(report):
    markers = report['markers']
    summaries = [m for m in markers if m.startswith('NXARMJIT: TRACE_MEMORY_OBSERVATION ')]
    requests = [m for m in markers if m.startswith('NXARMJIT: TRACE_MEMORY_REQUEST ')]
    parsed = []
    for row in requests:
        match = re.fullmatch(r'NXARMJIT: TRACE_MEMORY_REQUEST sequence=(\d+) operation=(\d+) '
            r'pc=(0x[0-9a-f]+) address=(0x[0-9a-f]+) width=(\d+) count=(\d+) result=(\d+)', row)
        if not match:
            raise ValueError('invalid memory observation')
        parsed.append(dict(zip(('sequence', 'operation', 'pc', 'address', 'width', 'count', 'result'),
            (int(v, 0) for v in match.groups()))))
    summary = re.fullmatch(r'NXARMJIT: TRACE_MEMORY_OBSERVATION total=(\d+) retained=(\d+)', summaries[0]) if len(summaries) == 1 else None
    return {'summary': list(map(int, summary.groups())) if summary else None, 'requests': parsed}


def protection(report):
    rows = [m for m in report['markers'] if m.startswith('NXARMJIT: TRACE_PROTECTION_CALLS ')]
    match = re.fullmatch(r'NXARMJIT: TRACE_PROTECTION_CALLS writable=(\d+) executable=(\d+) failures=(\d+) includes_restore=true', rows[0]) if len(rows) == 1 else None
    if not match:
        raise ValueError('one actual protection count with restore is required')
    return dict(zip(('writable', 'executable', 'failures'), map(int, match.groups())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cached-efi', 'uncached-efi', 'old-efi', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--unobserved-efi', type=Path)
    args = parser.parse_args()
    tools = Path(__file__).resolve().parent
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    bins = {mode: getattr(args, mode + '_efi').resolve(strict=True) for mode in ('cached', 'uncached', 'old')}
    if args.unobserved_efi:
        bins['unobserved'] = args.unobserved_efi.resolve(strict=True)
    source = tools / 'mapped_trace_probe.S'
    inputs = [*bins.values(), source, Path(__file__).resolve(), tools / 'build_arm64_handoff_probe.py',
        tools / 'trace_deep_arm_jit_ovmf.py', tools / 'verify_arm_jit_ovmf.py']
    before = {str(p): sha(p) for p in inputs}
    commands = []
    def run(command, timeout=30):
        p = subprocess.run(list(map(str, command)), capture_output=True, text=True, timeout=timeout)
        commands.append({'argv': list(map(str, command)), 'returncode': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return p
    obj, binary = out / 'probe.o', out / 'probe.bin'
    for command in [['clang', '--target=aarch64-none-elf', '-c', source, '-o', obj],
        ['ld.lld', '-Ttext', hex(VIRTUAL + ENTRY_OFFSET), '-e', '_start', '--oformat=binary', obj, '-o', binary]]:
        p = run(command)
        if p.returncode:
            raise RuntimeError(p.stderr)
    symbols = run([shutil.which('llvm-nm') or shutil.which('llvm-nm-18') or 'nm', '--defined-only', obj])
    if symbols.returncode:
        raise RuntimeError(symbols.stderr)
    offsets = {m.group(2): int(m.group(1), 16) for m in re.finditer(r'^([0-9a-fA-F]+)\s+\w\s+(\w+)$', symbols.stdout, re.M)}
    loop = offsets['mapped_loop']
    data = VIRTUAL + ENTRY_OFFSET + offsets['mapped_data']
    expected_pc = VIRTUAL + ENTRY_OFFSET + loop + 4 * ((BUDGET - loop // 4) % 5)
    payload = binary.read_bytes()
    if not payload or len(payload) > 16384 - 1024:
        raise ValueError('authored code extent')
    kernel, dt = out / 'probe.kc', out / 'diagnostic.dt'
    kernel.write_bytes(image(payload))
    dt.write_bytes(struct.pack('<II', 1, 1) + prop('name', b'\0') + struct.pack('<II', 3, 0)
        + prop('name', b'chosen\0') + prop('dram-base', struct.pack('<Q', PHYSICAL - 0x2000000))
        + prop('dram-size', struct.pack('<Q', 64 * 1024 * 1024)))
    authored_hashes = {str(p): sha(p) for p in (kernel, dt, binary)}
    runs = {}
    for mode, efi in bins.items():
        folder = out / mode
        command = [sys.executable, tools / 'trace_deep_arm_jit_ovmf.py', '--tools', tools,
            '--efi', efi, '--kernel', kernel, '--device-tree', dt, '--output', folder,
            '--physical-base', hex(PHYSICAL - 0x2000000), '--virtual-base', hex(VIRTUAL - 0x2000000),
            '--memory-size', str(64 * 1024 * 1024), '--kernel-physical', hex(PHYSICAL),
            '--instruction-budget', str(BUDGET), '--long-diagnostic', '--mapped-diagnostic',
            '--platform-profile', 'nextcore-irq-compat-v1', '--allow-incomplete-sptm-prefix', '--timeout', '180']
        p = run(command, 210)
        report = json.loads((folder / 'report.json').read_text())
        if mode == 'old':
            rejected = p.returncode != 0 and not report['requested_checks_completed'] and not report['mapped_profile']['validated']
            errors = [m for m in report['markers'] if 'CONFIG' in m and ('ERROR' in m or 'INVALID' in m or 'FAILED' in m)]
            runs[mode] = {'rejected': rejected, 'efi_parse_error_markers': errors,
                'classification': 'firmware-config-error-observed' if errors else 'required-mapped-acknowledgements-not-satisfied',
                'execution': report['execution'], 'mapped_profile': report['mapped_profile']}
            continue
        execution = report.get('execution') or {}
        memory = execution.get('memory') or {}
        obs = observations(report)
        requests = obs['requests']
        total = memory.get('fetch_requests', 0) + memory.get('data_requests', 0)
        checks = {
            'actual_mapped_diagnostic': p.returncode == 0 and report['requested_checks_completed'] and report['mapped_profile']['validated'],
            'exact_retirement_and_pc': execution.get('status') == 5 and execution.get('retired') == BUDGET and execution.get('pc') == expected_pc,
            'guest_assertions': execution.get('registers') == {'x0': 0x20002, 'x1': data, 'x2': VALUE, 'x3': data},
            'canonical_provider': memory.get('abi') == 2 and memory.get('provider_status') == 0 and memory.get('data_requests', 0) == memory.get('completed_data_operations') and memory.get('data_requests', 0) > 10000,
            'complete_chronological_window': obs['summary'] == [total, 64] and len(requests) == 64 and [r['sequence'] for r in requests] == list(range(total - 63, total + 1)),
            'high_alias_unaligned_data_observed': any(r['operation'] == 2 and r['address'] == data + 4 and r['width'] == 8 for r in requests) and any(r['operation'] == 3 and r['address'] == data + 4 and r['width'] == 8 for r in requests),
            'request_success': all(r['result'] == 0 for r in requests),
            'inputs_preserved': report['original_inputs_preserved'] and report['esp_copies_preserved'] and report['tool_sources_preserved'],
        }
        if mode == 'unobserved':
            for name in ('complete_chronological_window', 'high_alias_unaligned_data_observed', 'request_success'):
                del checks[name]
            checks['observation_absent'] = obs == {'summary': None, 'requests': []}
        runs[mode] = {'checks': checks, 'execution': execution, 'observation': obs, 'protection': protection(report)}
    cached, uncached = runs['cached'], runs['uncached']
    checks = {
        'both_authored_runs_pass': all(all(runs[m]['checks'].values()) for m in ('cached', 'uncached')),
        'full_reported_execution_and_window_equal': cached['execution'] == uncached['execution'] and cached['observation'] == uncached['observation'],
        'uncached_exact_protection': uncached['protection'] == {'writable': BUDGET + 1, 'executable': BUDGET, 'failures': 0},
        'cached_fewer_real_transitions': 0 < cached['protection']['executable'] < BUDGET,
        'cached_balanced_restore': cached['protection']['writable'] == cached['protection']['executable'] + 1 and cached['protection']['failures'] == 0,
        'old_build_not_accepted': runs['old']['rejected'],
        'sources_and_binaries_preserved': before == {str(p): sha(p) for p in inputs},
        'authored_inputs_preserved': authored_hashes == {str(p): sha(p) for p in (kernel, dt, binary)},
    }
    if 'unobserved' in runs:
        checks['observer_preserves_execution'] = all(runs['unobserved']['checks'].values()) and cached['execution'] == runs['unobserved']['execution']
        checks['observer_preserves_protection'] = cached['protection'] == runs['unobserved']['protection']
    receipt = {'schema': 'nextcore.authored-mapped-trace-efi.v1', 'passed': all(checks.values()),
        'checks': checks, 'runs': runs, 'source_sha256': before, 'authored_sha256': authored_hashes,
        'expected': {'budget': BUDGET, 'pc': expected_pc, 'data_va': data, 'boot_args_word': 0x20002},
        'original_images_used': False, 'original_entry_abi_verified': False,
        'physical_boot_verified': False, 'macos_boot_verified': False}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': receipt['passed'], 'checks': checks}))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
