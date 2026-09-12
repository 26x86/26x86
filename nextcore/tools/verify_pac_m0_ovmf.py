#!/usr/bin/env python3
"""Actual enabled-PAC M0 EFI qualification against a preserved adapted APA1 oracle.

The EFI guest executes the original asymmetric TCR for every operation. Only the
separately captured QEMU oracle adapted TCR during PAC. No Apple input is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
import sys
import time

from build_arm64_handoff_probe import image, PHYSICAL, VIRTUAL, ENTRY_OFFSET

BUDGET = 65536


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prop(name, value):
    return name.encode().ljust(32, b'\0') + struct.pack('<I', len(value)) + value.ljust((len(value) + 3) & ~3, b'\0')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('efi', 'old-efi', 'oracle', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    tools = Path(__file__).resolve().parent
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    oracle = args.oracle.resolve(strict=True)
    evidence = json.loads((oracle / 'receipt.json').read_text())
    assert evidence['passed'] and evidence['adapted_qemu_test_model'] and evidence['all_control_input_key_readbacks_match']
    assert evidence['rows'] == 48 and evidence['results_compared'] == 288
    assert int(evidence['qemu_guest_isar1'], 16) >> 4 & 15 == 1
    for name in ('manifest.json', 'results.bin'):
        assert sha(oracle / name) == evidence['artifact_hashes'][name]
    manifest = json.loads((oracle / 'manifest.json').read_text())
    assert len(manifest['rows']) == 48
    raw = (oracle / 'results.bin').read_bytes()
    assert len(raw) == (4 + 48 * 19) * 8
    words = struct.unpack('<916Q', raw)
    assert words[0] == 4 and words[3] == 48
    include = []
    for i, row in enumerate(manifest['rows']):
        result = words[4 + i * 19: 23 + i * 19]
        assert result[0] == result[7] == row['tcr']
        assert result[3] == result[9] == row['pointer']
        assert result[4] == result[10] == row['modifier'] == 0x9876
        assert result[5] == result[11] == 0x48ad369c24681357
        assert result[6] == result[12] == 0xb752c963db97eca8
        assert result[2] == result[8] == 0xf8d02800
        record = [row['tcr'], row['pointer'], row['key'], *result[13:19]]
        include.append('    .quad ' + ', '.join(hex(x) for x in record))
    table = out / 'pac_m0_vectors.inc'
    table.write_text('// Derived from hashed, adapted-control APA1 observations.\n' + '\n'.join(include) + '\n')
    for name in ('receipt.json', 'manifest.json', 'results.bin'):
        shutil.copyfile(oracle / name, out / ('oracle-' + name))
    source = tools / 'pac_m0_probe.S'
    bins = {'current': args.efi.resolve(strict=True), 'old': args.old_efi.resolve(strict=True)}
    inputs = [source, Path(__file__).resolve(), tools / 'trace_deep_arm_jit_ovmf.py',
        tools / 'verify_arm_jit_ovmf.py', tools / 'build_arm64_handoff_probe.py', *bins.values(),
        oracle / 'receipt.json', oracle / 'manifest.json', oracle / 'results.bin']
    before = {str(p): sha(p) for p in inputs}
    commands = []

    def run(argv, timeout=30):
        command = list(map(str, argv))
        start = time.monotonic()
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        forced = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            forced = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                stdout, stderr = proc.communicate(timeout=5)
        entry = dict(argv=command, returncode=proc.returncode, elapsed_seconds=time.monotonic() - start,
            forced=forced, reaped=proc.poll() is not None, stdout=stdout.decode(errors='replace'), stderr=stderr.decode(errors='replace'))
        commands.append(entry)
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        assert not forced, entry
        return entry

    obj, binary = out / 'probe.o', out / 'probe.bin'
    for cmd in [['clang-18', '--target=aarch64-none-elf', '-I', out, '-c', source, '-o', obj],
        ['ld.lld-18', '-Ttext', hex(PHYSICAL + ENTRY_OFFSET), '-e', '_start', '--oformat=binary', obj, '-o', binary]]:
        result = run(cmd)
        assert result['returncode'] == 0, result
    symbols = run(['llvm-nm-18', '--defined-only', obj])
    assert symbols['returncode'] == 0
    offsets = {m.group(2): int(m.group(1), 16) for m in re.finditer(r'^([0-9a-fA-F]+)\s+\w\s+(\w+)$', symbols['stdout'], re.M)}
    payload = binary.read_bytes()
    assert 0 < len(payload) <= 16384 - 1024
    kernel, dt = out / 'probe.kc', out / 'diagnostic.dt'
    kernel.write_bytes(image(payload))
    dt.write_bytes(struct.pack('<II', 1, 1) + prop('name', b'\0') + struct.pack('<II', 3, 0)
        + prop('name', b'chosen\0') + prop('dram-base', struct.pack('<Q', PHYSICAL - 0x2000000))
        + prop('dram-size', struct.pack('<Q', 64 * 1024 * 1024)))
    authored = {str(p): sha(p) for p in (kernel, dt, binary, table)}
    runs = {}
    for mode, efi in bins.items():
        folder = out / mode
        command = [sys.executable, tools / 'trace_deep_arm_jit_ovmf.py', '--tools', tools,
            '--efi', efi, '--kernel', kernel, '--device-tree', dt, '--output', folder,
            '--physical-base', hex(PHYSICAL - 0x2000000), '--virtual-base', hex(VIRTUAL - 0x2000000),
            '--memory-size', str(64 * 1024 * 1024), '--kernel-physical', hex(PHYSICAL),
            '--instruction-budget', str(BUDGET), '--long-diagnostic',
            '--platform-profile', 'nextcore-irq-compat-v1', '--allow-incomplete-sptm-prefix', '--timeout', '180']
        result = run(command, timeout=200)
        report = json.loads((folder / 'report.json').read_text())
        execution = report.get('execution') or {}
        memory = execution.get('memory') or {}
        terminal = any(re.fullmatch(rb'NXARMJIT: ERROR status=ABORTED\r?', line) for line in
            (folder / 'serial.log').read_bytes().split(b'\n')[:-1])
        shared = dict(actual_m0=report['requested_checks_completed'] and result['returncode'] == 0
            and not report['mapped_profile']['requested'] and memory.get('abi') == 1,
            exact_budget=execution.get('status') == 5 and execution.get('retired') == BUDGET,
            provider_success=memory.get('provider_status') == 0 and memory.get('fetch_requests') == BUDGET
                and memory.get('data_requests') == memory.get('completed_data_operations'),
            inputs_preserved=report['original_inputs_preserved'] and report['esp_copies_preserved'] and report['tool_sources_preserved'],
            complete_terminal=terminal, inner_process_returned=report['qemu_exit_code'] is not None and report['failure'] is None)
        if mode == 'current':
            shared['all_288_guest_comparisons'] = execution.get('registers') == {'x0': 0x504143, 'x1': 48, 'x2': 288, 'x3': 1}
            shared['exact_success_pc'] = execution.get('pc') == PHYSICAL + ENTRY_OFFSET + offsets['pac_success_loop']
            shared['exact_data'] = memory.get('data_requests') == 432
        else:
            shared['distinct_old_sign_assertion'] = execution.get('registers') == {'x0': 0xbad, 'x1': 4, 'x2': 0, 'x3': 0xff36800000000130}
            shared['exact_failure_pc'] = execution.get('pc') == PHYSICAL + ENTRY_OFFSET + offsets['pac_failure_loop']
            shared['exact_data'] = memory.get('data_requests') == 40
        runs[mode] = dict(checks=shared, execution=execution, elapsed_seconds=report['elapsed_seconds'], qemu_exit_code=report['qemu_exit_code'])
    checks = dict(current_enabled_pac_efi_pass=all(runs['current']['checks'].values()),
        old_efi_distinct_assertion=all(runs['old']['checks'].values()),
        sources_binaries_oracle_preserved=before == {str(p): sha(p) for p in inputs},
        authored_inputs_preserved=authored == {str(p): sha(p) for p in (kernel, dt, binary, table)},
        all_outer_processes_reaped=all(x['reaped'] and not x['forced'] for x in commands))
    receipt = dict(schema='nextcore.enabled-pac-m0-efi.v1', passed=all(checks.values()), checks=checks, runs=runs,
        source_sha256=before, authored_sha256=authored, oracle_scope='Adapted-control APA1 QEMU expected values; EFI uses original asymmetric TCR.',
        vectors=48, numeric_assertions=288, original_images_used=False, physical_boot_verified=False, macos_boot_verified=False)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': receipt['passed'], 'checks': checks, 'runs': runs}))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
