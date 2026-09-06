"""Exercise Rust capture_at_producer -> real current-vCPU register callback."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

PROBES = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--variant', choices=('v2', 'final'), default='v2')
parser.add_argument('--binary', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
variant = args.variant
root = args.output
output = root / ('mapper-handoff-probe-' + variant)
output.mkdir(exist_ok=False)
source, linker = PROBES / 'mapper_handoff.S', PROBES / 'mapper_handoff.ld'
obj, elf, guest = (output / name for name in ('mapper.o', 'mapper.elf', 'mapper.bin'))
commands = [
    ['aarch64-linux-gnu-as', '-o', str(obj), str(source)],
    ['aarch64-linux-gnu-ld', '-T', str(linker), '-o', str(elf), str(obj)],
    ['aarch64-linux-gnu-objcopy', '-O', 'binary', str(elf), str(guest)],
]
for command in commands:
    subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
aux, disk = output / 'synthetic-aux.bin', output / 'synthetic-root.bin'
aux.write_bytes(bytes(1024 * 1024))
disk.write_bytes(bytes(1024 * 1024))
binary = args.binary
paths = (source, linker, guest, binary, aux, disk)
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
environment = dict(os.environ)
for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR'):
    environment.pop(key, None)
environment.setdefault('VK_DRIVER_FILES', '/usr/share/vulkan/icd.d/lvp_icd.json')
environment['TMPDIR'] = str(root / 'tmp')
command = [str(binary), '-accel', 'tcg', '-cpu', 'max,pauth-qarma5=on,cntfrq=24000000',
           '-M', 'vmapple,research-headless=on,research-graphics=on', '-m', '128M',
           '-smp', '1', '-display', 'none', '-monitor', 'none', '-serial', 'stdio',
           '-net', 'none', '-bios', str(guest), '-semihosting-config', 'enable=on,target=native',
           '-drive', 'if=pflash,unit=0,format=raw,readonly=on,file=' + str(aux).replace(',', ',,'),
           '-drive', 'if=pflash,unit=1,format=raw,readonly=on,file=' + str(disk).replace(',', ',,'),
           '-trace', 'enable=reims_vgpu_mmio_*']
start = time.monotonic()
timed_out = False
try:
    run = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=40)
except subprocess.TimeoutExpired as exc:
    def decode(value):
        return value.decode('utf-8', 'replace') if isinstance(value, bytes) else value or ''
    run = subprocess.CompletedProcess(command, -1, decode(exc.stdout), decode(exc.stderr))
    timed_out = True
values = [(int(cpu), int(register), int(value, 16)) for cpu, register, value in
          re.findall(r'reims_vgpu_mmio_read_xreg cpu=(\d+) x(\d+)=0x([a-fA-F0-9]+)', run.stderr)]
expected = [(0, 19, 0xfffffe0011223344), (0, 21, 1), (0, 22, 0x5566778899aabbcc)]
report = {
    'command': command, 'build_commands': commands, 'seconds': time.monotonic() - start,
    'returncode': run.returncode, 'timed_out': timed_out,
    'current_vcpu_registers': values, 'expected_registers': expected,
    'guest_returned_from_mmio': run.stdout == 'VENFIRE_GPU|MAPPER_MMIO_RETURNED\n',
    'iosfc_producer_write_traced': 'reims_vgpu_mmio_iosfc_write offset=0x1018 val=0x1' in run.stderr,
    'binary_and_inputs_sha256': hashes,
    'files_unchanged': all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest
                           for p, digest in hashes.items()),
    'self_authored_guest_only': True, 'macos_boot_verified': False,
    'mapper_identity_or_page_mapping_verified': False,
}
report['passed'] = (run.returncode == 0 and report['guest_returned_from_mmio']
                    and report['iosfc_producer_write_traced'] and values == expected
                    and report['files_unchanged'])
(output / 'serial.log').write_text(run.stdout)
(output / 'stderr.log').write_text(run.stderr)
name = 'mapper-handoff-result.json' if variant == 'v2' else 'mapper-handoff-result-final.json'
(root / name).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
if not report['passed']:
    print(run.stderr[-6000:])
raise SystemExit(0 if report['passed'] else 1)
