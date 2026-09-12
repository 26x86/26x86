#!/usr/bin/env python3
"""Execute authored instruction families through the existing x86 EFI consumer."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from build_arm64_handoff_probe import image, PHYSICAL, VIRTUAL, ENTRY_OFFSET

ASSEMBLY = """.text
.global _start
_start:
    mov x0, #0x1234
    lsl x0, x0, #16
    lsr x0, x0, #8
    ubfx x0, x0, #8, #8
    mov x2, #0xffff
    ubfiz x2, x2, #12, #4
    mov x3, #0x1234
    ubfx w3, w3, #4, #8
1:  b 1b
"""

EXTENDED_ASSEMBLY = """.text
.global _start
_start:
    mov x0, #1
    mov x2, #0xff
    add x0, x0, w2, sxtb
    cmp x0, w2, uxtb
    b.hs failure
    mov x3, #0x1234
    add x3, x3, w2, uxtb #4
    sub x2, x3, w2, sxtb
    cmp x2, w2, uxtb #1
    b.lo failure
done: b done
failure:
    mov x0, #1
    b done
"""

SELECT_ASSEMBLY = """.text
.global _start
_start:
    mov x0, #0x11
    mov x2, #0x22
    cmp x0, x0
    csel x3, x0, x2, eq
    csinc x0, x0, x2, ne
    csinv x2, x0, x3, ne
    csneg w3, w0, w3, eq
done: b done
"""

REGISTER_MEMORY_ASSEMBLY = """.text
.global _start
_start:
    adr x4, data
    mov x5, #2
    ldrh w0, [x4, x5, lsl #1]
    movn w6, #1
    add x7, x4, #8
    ldrsh x2, [x7, w6, sxtw #1]
    mov x6, #1
    strh w0, [x4, x6, lsl #1]
    ldrh w3, [x4, x6, lsl #1]
done: b done
.balign 8
data: .hword 0x1111, 0x2222, 0x80fe, 0x4444
"""

TEST_BIT_ASSEMBLY = """.text
.global _start
_start:
    mov x0, #0
    mov x2, #0
    mov x3, #0
    mov x4, #1
    tbz x4, #0, failure
    tbnz x4, #0, one
    b failure
one:
    mov x0, #0x11
    mov x4, #0x8000000000000000
    tbz x4, #63, failure
    tbnz x4, #63, high
    b failure
high:
    mov x2, #0x22
    tbz xzr, #63, zero
    b failure
zero:
    mov x3, #0x33
    mov x5, #2
loop:
    sub x5, x5, #1
    tbnz x5, #0, loop
    tbz x5, #0, done
    b failure
done: b done
failure:
    mov x0, #0xff
    b done
"""

MULTIPLY_ASSEMBLY = """.text
.global _start
_start:
    mov x4, #0xffff
    mov x5, #1
    movk x5, #1, lsl #16
    mov x6, #2
    cmp x6, x6
    madd x0, x4, x5, x6
    msub w2, w4, w5, w6
    mul x3, x4, x5
    mneg w3, w3, w6
    b.ne failure
done: b done
failure:
    mov x0, #0
    b done
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prop(name, value):
    return name.encode().ljust(32, b'\0') + struct.pack('<I', len(value)) + value.ljust((len(value) + 3) & ~3, b'\0')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--instruction-family', choices=['ubfm', 'extended', 'select', 'register-memory', 'test-bit', 'multiply'], default='ubfm')
    args = parser.parse_args()
    efi = args.efi.resolve(strict=True)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    inputs = [efi, Path(__file__).resolve(), tools / 'build_arm64_handoff_probe.py',
              tools / 'trace_deep_arm_jit_ovmf.py', tools / 'verify_arm_jit_ovmf.py']
    before = {str(p): sha(p) for p in inputs}
    assembly, expected_registers, loop_offset = {
        'ubfm': (ASSEMBLY, (0x34, 0xf000, 0x23), 32),
        'extended': (EXTENDED_ASSEMBLY, (0, 0x2225, 0x2224), 40),
        'select': (SELECT_ASSEMBLY, (0x23, 0xffffffffffffffee, 0x23), 28),
        'register-memory': (REGISTER_MEMORY_ASSEMBLY, (0x80fe, 0xffffffffffff80fe, 0x80fe), 36),
        'test-bit': (TEST_BIT_ASSEMBLY, (0x11, 0x22, 0x33), 84),
        'multiply': (MULTIPLY_ASSEMBLY, (0x100000001, 3, 2), 40),
    }[args.instruction_family]
    expected_data = 4 if args.instruction_family == 'register-memory' else 0
    (out / 'probe.S').write_text(assembly)
    commands = [
        ['clang', '--target=aarch64-none-elf', '-c', str(out / 'probe.S'), '-o', str(out / 'probe.o')],
        ['llvm-objcopy', '-O', 'binary', '--only-section=.text', str(out / 'probe.o'), str(out / 'probe.bin')],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, timeout=30)
    (out / 'probe.kc').write_bytes(image((out / 'probe.bin').read_bytes()))
    # Authored bounded RAM metadata is diagnostic, never a complete platform DT.
    (out / 'diagnostic.dt').write_bytes(struct.pack('<II', 1, 1) + prop('name', b'\0')
        + struct.pack('<II', 3, 0) + prop('name', b'chosen\0')
        + prop('dram-base', struct.pack('<Q', PHYSICAL - 0x2000000))
        + prop('dram-size', struct.pack('<Q', 64 * 1024 * 1024)))
    command = [sys.executable, str(tools / 'trace_deep_arm_jit_ovmf.py'),
        '--tools', str(tools), '--efi', str(efi), '--kernel', str(out / 'probe.kc'),
        '--device-tree', str(out / 'diagnostic.dt'), '--output', str(out / 'firmware'),
        '--physical-base', hex(PHYSICAL - 0x2000000),
        '--virtual-base', hex(VIRTUAL - 0x2000000), '--memory-size', str(64 * 1024 * 1024),
        '--kernel-physical', hex(PHYSICAL), '--instruction-budget', '64',
        '--platform-profile', 'nextcore-irq-compat-v1', '--allow-incomplete-sptm-prefix', '--timeout', '60']
    commands.append(command)
    result = subprocess.run(command, capture_output=True, text=True, timeout=80)
    (out / 'firmware.log').write_text(result.stdout + result.stderr)
    receipt = json.loads((out / 'firmware/report.json').read_text())
    execution = receipt.get('execution') or {}
    registers = execution.get('registers') or {}
    memory = execution.get('memory') or {}
    entered = next((m for m in receipt['markers'] if m.startswith('NXARMJIT: TRACE_ENTER ')), '')
    x1 = re.search(r' x1=(0x[0-9a-f]+) ', entered)
    checks = {
        'completed': result.returncode == 0 and receipt['diagnostic_completed'],
        'exact_retirement': execution.get('status') == 5 and execution.get('retired') == 64,
        'final_loop_pc': execution.get('pc') == PHYSICAL + ENTRY_OFFSET + loop_offset,
        'arithmetic_results': (registers.get('x0'), registers.get('x2'), registers.get('x3')) == expected_registers,
        'boot_argument_preserved': bool(x1) and registers.get('x1') == int(x1.group(1), 16),
        'memory_provider': memory.get('provider_status') == 0 and memory.get('fetch_requests') == 64
            and memory.get('data_requests') == expected_data and memory.get('completed_data_operations') == expected_data,
        'inputs_preserved': before == {str(p): sha(p) for p in inputs} and receipt['original_inputs_preserved'] and receipt['esp_copies_preserved'],
    }
    summary = dict(schema='nextcore.arithmetic-existing-efi-consumer.v1', instruction_family=args.instruction_family,
                   passed=all(checks.values()), checks=checks,
                   commands=commands, source_hashes=before, original_images_used=False, macos_boot_verified=False)
    (out / 'receipt.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'passed': summary['passed'], 'checks': checks}))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
