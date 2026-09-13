#!/usr/bin/env python3
"""Prove authored fileset entry provenance through the existing OVMF EFI trace."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from build_arm64_handoff_probe import image, PAGE, PHYSICAL, VIRTUAL, ENTRY_OFFSET

ASSEMBLY = """.text
.global _start
_start:
    mov x0, #0x1111
    mov x2, #0xaaaa
    mov x3, #0x111
outer_loop: b outer_loop
.org 64
member_entry:
    mov x0, #0x2222
    mov x2, #0xbbbb
    mov x3, #0x222
member_loop: b member_loop
.org 128
alternate_member:
    mov x0, #0x4444
    mov x2, #0xdddd
    mov x3, #0x444
alternate_loop: b alternate_loop
.org 192
base_entry:
    mov x0, #0x3333
    mov x2, #0xcccc
    mov x3, #0x333
base_loop: b base_loop
"""
# Existing authored fixture: three outer segment commands before ARM_THREAD_STATE64.
OUTER_PC_FIELD = 32 + 3 * 72 + 272
MEMBER_THREAD = PAGE + 32 + 2 * 72
MEMBER_PC_FIELD = MEMBER_THREAD + 272
MINIMUM_VIRTUAL = VIRTUAL - PAGE
KERNEL_PHYSICAL = PHYSICAL - PAGE
BUDGET = 64


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def property_bytes(name, value):
    return name.encode().ljust(32, b'\0') + struct.pack('<I', len(value)) + value.ljust((len(value) + 3) & ~3, b'\0')


def fixture(code):
    data = bytearray(image(code))
    # A real mapped executable canary precedes the header in virtual memory.
    data.extend(bytes(4 * PAGE - len(data)))
    data[3 * PAGE:3 * PAGE + 16] = code[192:208]
    count, size = struct.unpack_from('<II', data, 16)
    lower = struct.pack('<II16sQQQQIIII', 0x19, 72, b'__BASE_CANARY',
                        MINIMUM_VIRTUAL, PAGE, 3 * PAGE, PAGE, 5, 5, 0, 0)
    data[32 + size:32 + size + 72] = lower
    struct.pack_into('<II', data, 16, count + 1, size + 72)
    thread = bytearray(struct.pack('<IIII', 5, 288, 6, 68) + bytes(272))
    struct.pack_into('<Q', thread, 272, VIRTUAL + ENTRY_OFFSET + 64)
    data[MEMBER_THREAD:MEMBER_THREAD + len(thread)] = thread
    struct.pack_into('<II', data, PAGE + 16, 3, 2 * 72 + len(thread))
    assert struct.unpack_from('<Q', data, OUTER_PC_FIELD)[0] == VIRTUAL + ENTRY_OFFSET
    return bytes(data)


def run_case(name, payload, entry, expected, efi, out, tools):
    case = out / name
    case.mkdir()
    kernel = case / 'authored.kc'
    kernel.write_bytes(payload)
    dt = out / 'diagnostic.dt'
    command = [
        sys.executable, str(tools / 'trace_deep_arm_jit_ovmf.py'),
        '--tools', str(tools), '--efi', str(efi), '--kernel', str(kernel),
        '--device-tree', str(dt), '--output', str(case / 'firmware'),
        '--physical-base', hex(PHYSICAL - 0x2000000),
        '--virtual-base', hex(VIRTUAL - 0x2000000),
        '--memory-size', str(64 * 1024 * 1024), '--kernel-physical', hex(KERNEL_PHYSICAL),
        '--instruction-budget', str(BUDGET), '--platform-profile', 'nextcore-irq-compat-v1',
        '--allow-incomplete-sptm-prefix', '--timeout', '60',
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=80)
    (case / 'runner.log').write_text(result.stdout + result.stderr)
    report_path = case / 'firmware/report.json'
    receipt = json.loads(report_path.read_text()) if report_path.exists() else {}
    execution = receipt.get('execution') or {}
    registers = execution.get('registers') or {}
    memory = execution.get('memory') or {}
    entered = next((m for m in receipt.get('markers', []) if m.startswith('NXARMJIT: TRACE_ENTER ')), '')
    pc = re.search(r'\bentry=(0x[0-9a-f]+)\b', entered)
    x1 = re.search(r'\bx1=(0x[0-9a-f]+)\b', entered)
    physical_entry = KERNEL_PHYSICAL + entry - MINIMUM_VIRTUAL
    checks = {
        'diagnostic_completed': result.returncode == 0 and receipt.get('diagnostic_completed') is True,
        'entry_pc': bool(pc) and int(pc.group(1), 16) == physical_entry,
        'exact_budget_return': execution.get('status') == 5 and execution.get('retired') == BUDGET,
        'exact_loop_pc': execution.get('pc') == physical_entry + 12,
        'canary_registers': tuple(registers.get(key) for key in ('x0', 'x2', 'x3')) == expected,
        'boot_argument_preserved': bool(x1) and registers.get('x1') == int(x1.group(1), 16),
        'memory_provider': memory.get('provider_status') == 0 and memory.get('fetch_requests') == BUDGET
            and memory.get('data_requests') == 0 and memory.get('completed_data_operations') == 0,
        'inputs_preserved': receipt.get('original_inputs_preserved') is True
            and receipt.get('esp_copies_preserved') is True
            and receipt.get('tool_sources_preserved') is True
            and hashlib.sha256(payload).hexdigest() == digest(kernel),
    }
    return dict(name=name, passed=all(checks.values()), checks=checks, command=command,
                fixture_sha256=digest(kernel), entry_virtual=entry, entry_physical=physical_entry,
                expected_registers=expected, observed_execution=execution, entered=entered)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    efi = args.efi.resolve(strict=True)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    sources = [efi, Path(__file__).resolve(), tools / 'build_arm64_handoff_probe.py',
               tools / 'trace_deep_arm_jit_ovmf.py', tools / 'verify_arm_jit_ovmf.py']
    before = {str(path): digest(path) for path in sources}
    (out / 'canaries.S').write_text(ASSEMBLY)
    commands = [
        ['clang', '--target=aarch64-none-elf', '-c', str(out / 'canaries.S'), '-o', str(out / 'canaries.o')],
        ['llvm-objcopy', '-O', 'binary', '--only-section=.text', str(out / 'canaries.o'), str(out / 'canaries.bin')],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, timeout=30)
    code = (out / 'canaries.bin').read_bytes()
    if len(code) != 208:
        raise ValueError('Unexpected authored assembly layout')
    baseline = fixture(code)
    (out / 'diagnostic.dt').write_bytes(
        struct.pack('<II', 1, 1) + property_bytes('name', b'\0') +
        struct.pack('<II', 3, 0) + property_bytes('name', b'chosen\0') +
        property_bytes('dram-base', struct.pack('<Q', PHYSICAL - 0x2000000)) +
        property_bytes('dram-size', struct.pack('<Q', 64 * 1024 * 1024)))
    outer = VIRTUAL + ENTRY_OFFSET
    member = outer + 64
    definitions = [
        ('outer-entry', None, None, outer, (0x1111, 0xaaaa, 0x111)),
        ('outer-selects-member', OUTER_PC_FIELD, member, member, (0x2222, 0xbbbb, 0x222)),
        ('member-metadata-changes', MEMBER_PC_FIELD, outer + 128, outer, (0x1111, 0xaaaa, 0x111)),
        ('outer-selects-image-base', OUTER_PC_FIELD, MINIMUM_VIRTUAL, MINIMUM_VIRTUAL, (0x3333, 0xcccc, 0x333)),
    ]
    cases = []
    for name, field, value, selected, expected in definitions:
        payload = bytearray(baseline)
        if field is not None:
            struct.pack_into('<Q', payload, field, value)
            differences = [i for i, (a, b) in enumerate(zip(baseline, payload)) if a != b]
            if not differences or any(not field <= i < field + 8 for i in differences):
                raise ValueError('Mutation escaped the selected PC field')
        else:
            differences = []
        case = run_case(name, bytes(payload), selected, expected, efi, out, tools)
        case['mutation_byte_offsets'] = differences
        case['mutated_pc_field_offset'] = field
        cases.append(case)
        print(json.dumps({'case': name, 'passed': case['passed'], 'checks': case['checks']}), flush=True)
    stable = before == {str(path): digest(path) for path in sources}
    receipt = dict(schema='nextcore.authored-entry-provenance.v1',
                   passed=stable and all(case['passed'] for case in cases),
                   source_inputs_preserved=stable, source_hashes=before, assembly_commands=commands,
                   image_base_virtual=MINIMUM_VIRTUAL, outer_entry_virtual=outer,
                   member_entry_virtual=member, cases=cases,
                   apple_assets_used=False, normal_startup_verified=False, macos_boot_verified=False)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
