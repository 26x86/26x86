"""Own-source guest test of isolated Reims/TCG VMApple device integration."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--variant', choices=('baseline', 'final-graphics', 'final-headless'), default='baseline')
parser.add_argument('--binary', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
variant = args.variant
root = args.output
graphics = variant != 'final-headless'
project = PROJECT
sys.path.insert(0, str(project))
from venfire.conformance import parse_serial, verify_guest

binary = args.binary
guest = verify_guest('vmapple')
output = root / ('qemu-startup-probe' if variant == 'baseline' else 'qemu-startup-probe-' + variant)
output.mkdir(exist_ok=False)
aux, disk = output / 'synthetic-aux.bin', output / 'synthetic-root.bin'
aux.write_bytes(bytes(1024 * 1024))
disk.write_bytes(bytes(1024 * 1024))
environment = dict(os.environ)
for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR'):
    environment.pop(key, None)
environment.setdefault('VK_DRIVER_FILES', '/usr/share/vulkan/icd.d/lvp_icd.json')
environment['TMPDIR'] = str(root / 'tmp')
command = [str(binary), '-accel', 'tcg', '-cpu', 'max,pauth-qarma5=on,cntfrq=24000000',
           '-M', 'vmapple,research-headless=on,research-graphics=' + ('on' if graphics else 'off'),
           '-m', '128M', '-smp', '1', '-display', 'none', '-monitor', 'none',
           '-serial', 'stdio', '-net', 'none', '-bios', str(guest),
           '-semihosting-config', 'enable=on,target=native',
           '-drive', 'if=pflash,unit=0,format=raw,readonly=on,file=' + str(aux).replace(',', ',,'),
           '-drive', 'if=pflash,unit=1,format=raw,readonly=on,file=' + str(disk).replace(',', ',,'),
           '-trace', 'enable=reims_vgpu_mmio_realize']
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (binary, guest, aux, disk)}
start = time.monotonic()
timed_out = False
try:
    run = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=40)
    stdout, stderr, returncode = run.stdout, run.stderr, run.returncode
except subprocess.TimeoutExpired as exc:
    def decode(value):
        return value.decode('utf-8', 'replace') if isinstance(value, bytes) else value or ''
    stdout, stderr, returncode = decode(exc.stdout), decode(exc.stderr), None
    timed_out = True
report = {
    'command': command, 'seconds': time.monotonic() - start,
    'display_environment_removed': ['DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR'],
    'vulkan_driver': environment['VK_DRIVER_FILES'],
    'binary_and_inputs_sha256': hashes,
    'files_unchanged': all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest
                           for p, digest in hashes.items()),
    'returncode': returncode, 'timed_out': timed_out,
    'device_realized_with_vulkan': 'reims_vgpu_mmio_realize' in stderr and 'backend=vulkan' in stderr,
    'graphics_requested': graphics,
    'self_authored_guest': parse_serial(stdout, returncode=returncode, timed_out=timed_out),
    'macos_boot_verified': False, 'guest_gpu_protocol_verified': False,
}
report['passed'] = (report['files_unchanged'] and report['device_realized_with_vulkan'] == graphics
                    and report['self_authored_guest']['passed'])
(output / 'serial.log').write_text(stdout)
(output / 'stderr.log').write_text(stderr)
name = 'qemu-startup-result.json' if variant == 'baseline' else 'qemu-startup-result-' + variant + '.json'
(root / name).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
if not report['passed']:
    print(stderr[-5000:])
raise SystemExit(0 if report['passed'] else 1)
