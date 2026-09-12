#!/usr/bin/env python3
"""Verify owned ARM boot-video writes through the real EFI GOP consumer."""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from build_arm64_handoff_probe import image, PHYSICAL, VIRTUAL, ENTRY_OFFSET
from verify_ubfm_consumer_ovmf import prop, sha

# Field offsets follow the pinned public ARM64 boot_args codec, not a private image.
ASSEMBLY = """.text
.global _start
_start:
    mov x0, #0
    ldr x4, [x1, #40]
    ldr x5, [x1, #56]
    ldr x6, [x1, #64]
    ldr x7, [x1, #72]
    ldr x8, [x1, #80]
    ldr x9, [x1, #48]
    ldr x10, [x1, #32]
    cbz x4, done
    cbz x6, done
    cbz x7, done
    cmp x8, #32
    b.ne done
    cmp x9, #1
    b.ne done
    lsl x11, x6, #2
    cmp x5, x11
    b.ne done
    madd x11, x7, x5, x4
    cmp x10, x11
    b.lo done
    mov w12, #0xff0000
    str w12, [x4]
    sub x11, x11, #4
    mov w12, #0xff
    str w12, [x11]
    mov x2, x5
    mul x3, x6, x7
    mov x0, #0x600d
done: b done
"""


def expected_rgb_hash(pixel_count):
    value = 0xcbf29ce484222325
    for index in range(pixel_count):
        pixel = (0, 0, 255) if index == 0 else (255, 0, 0) if index == pixel_count - 1 else (0, 0, 0)
        for byte in pixel:
            value = ((value ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    efi = args.efi.resolve(strict=True)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    inputs = [efi, Path(__file__).resolve(), tools / 'build_arm64_handoff_probe.py',
              tools / 'verify_ubfm_consumer_ovmf.py', tools / 'trace_deep_arm_jit_ovmf.py',
              tools / 'verify_arm_jit_ovmf.py']
    before = {str(p): sha(p) for p in inputs}
    (out / 'probe.S').write_text(ASSEMBLY)
    commands = [
        ['clang', '--target=aarch64-none-elf', '-c', str(out / 'probe.S'), '-o', str(out / 'probe.o')],
        ['llvm-objcopy', '-O', 'binary', '--only-section=.text', str(out / 'probe.o'), str(out / 'probe.bin')],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, timeout=30)
    symbols = subprocess.run(['llvm-nm', '--defined-only', str(out / 'probe.o')],
                             check=True, capture_output=True, text=True, timeout=30).stdout
    loop = re.search(r'^([0-9a-fA-F]+)\s+\w\s+done$', symbols, re.MULTILINE)
    if not loop:
        raise RuntimeError('Authored loop symbol missing')
    (out / 'probe.kc').write_bytes(image((out / 'probe.bin').read_bytes()))
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
        '--platform-profile', 'nextcore-irq-compat-v1', '--allow-incomplete-sptm-prefix',
        '--gop-framebuffer', '--timeout', '60']
    commands.append(command)
    result = subprocess.run(command, capture_output=True, text=True, timeout=80)
    (out / 'firmware.log').write_text(result.stdout + result.stderr)
    receipt = json.loads((out / 'firmware/report.json').read_text())
    execution = receipt.get('execution') or {}
    registers = execution.get('registers') or {}
    memory = execution.get('memory') or {}
    geometry = receipt.get('video', {}).get('geometry') or {}
    readbacks = [m for m in receipt['markers'] if m.startswith('NXARMJIT: TRACE_VIDEO_READBACK ')]
    observed = re.fullmatch(r'NXARMJIT: TRACE_VIDEO_READBACK guest_rgb_hash=(0x[0-9a-f]+) display_rgb_hash=(0x[0-9a-f]+) matched=true first=(0x[0-9a-f]+) last=(0x[0-9a-f]+)', readbacks[0]) if len(readbacks) == 1 else None
    count = geometry.get('width', 0) * geometry.get('height', 0)
    expected_hash = expected_rgb_hash(count) if 1 < count <= 8192 * 8192 else None
    entered = next((m for m in receipt['markers'] if m.startswith('NXARMJIT: TRACE_ENTER ')), '')
    x1 = re.search(r' x1=(0x[0-9a-f]+) ', entered)
    checks = {
        'execution_completed': result.returncode == 0 and receipt['diagnostic_completed'],
        'video_requested_and_presented': receipt.get('requested_checks_completed') and receipt.get('video', {}).get('validated'),
        'exact_retirement': execution.get('status') == 5 and execution.get('retired') == 64,
        'final_loop_pc': execution.get('pc') == PHYSICAL + ENTRY_OFFSET + int(loop.group(1), 16),
        'guest_boot_video_fields': registers.get('x0') == 0x600d and count > 1
            and registers.get('x2') == geometry.get('row_bytes') and registers.get('x3') == count,
        'boot_argument_preserved': bool(x1) and registers.get('x1') == int(x1.group(1), 16),
        'exact_memory_operations': memory.get('provider_status') == 0 and memory.get('fetch_requests') == 64
            and memory.get('data_requests') == 9 and memory.get('completed_data_operations') == 9,
        'full_gop_readback': bool(observed) and expected_hash is not None
            and tuple(int(observed.group(i), 16) for i in range(1, 5)) == (expected_hash, expected_hash, 0xff0000, 0xff),
        'inputs_preserved': before == {str(p): sha(p) for p in inputs}
            and receipt['original_inputs_preserved'] and receipt['esp_copies_preserved'],
    }
    summary = dict(schema='nextcore.boot-framebuffer-efi-consumer.v1', passed=all(checks.values()),
                   checks=checks, geometry=geometry, commands=commands, source_hashes=before,
                   expected_rgb_hash=expected_hash, original_images_used=False,
                   physical_display_verified=False, macos_boot_verified=False,
                   persistent_display_verified=False, graphics_acceleration_verified=False)
    (out / 'receipt.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'passed': summary['passed'], 'checks': checks, 'geometry': geometry}))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
