"""Actual qtest MMIO -> Rust EFI copy -> QMP PPM readback; no guest runs."""
import hashlib
import argparse
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

PROBES = Path(__file__).resolve().parent
project = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--binary', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
root = args.output
sys.path.insert(0, str(project))
from venfire.conformance import verify_guest

spec = importlib.util.spec_from_file_location('venfire_barrier_probe', PROBES / 'qtest.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
QTest = module.QTest

output = root / 'firmware-console-probe'
output.mkdir(exist_ok=False)
binary = args.binary
guest = verify_guest('vmapple')
aux, disk = output / 'synthetic-aux.bin', output / 'synthetic-root.bin'
aux.write_bytes(bytes(1024 * 1024))
disk.write_bytes(bytes(1024 * 1024))
inputs = (binary, guest, aux, disk)
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
environment = dict(os.environ)
for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR'):
    environment.pop(key, None)
environment.setdefault('VK_DRIVER_FILES', '/usr/share/vulkan/icd.d/lvp_icd.json')
environment['TMPDIR'] = str(root / 'tmp')
parent_socket, child_socket = socket.socketpair()
parent_socket.settimeout(20)
command = [str(binary), '-accel', 'tcg', '-S', '-cpu', 'max,pauth-qarma5=on,cntfrq=24000000',
           '-M', 'vmapple,research-headless=on,research-graphics=on', '-m', '128M',
           '-smp', '1', '-display', 'none', '-serial', 'none', '-net', 'none',
           '-bios', str(guest), '-qtest', 'stdio', '-qtest-log', '/dev/null',
           '-chardev', f'socket,id=gpu_qmp,fd={child_socket.fileno()}',
           '-mon', 'chardev=gpu_qmp,mode=control',
           '-drive', 'if=pflash,unit=0,format=raw,readonly=on,file=' + str(aux).replace(',', ',,'),
           '-drive', 'if=pflash,unit=1,format=raw,readonly=on,file=' + str(disk).replace(',', ',,'),
           '-trace', 'enable=reims_vgpu_mmio_*']
qmp_buffer = b''

def qmp_receive():
    global qmp_buffer
    while b'\n' not in qmp_buffer:
        chunk = parent_socket.recv(65536)
        if not chunk:
            raise RuntimeError('QEMU closed QMP')
        qmp_buffer += chunk
    line, qmp_buffer = qmp_buffer.split(b'\n', 1)
    return json.loads(line)

def qmp(execute, arguments=None):
    request = {'execute': execute, 'id': execute}
    if arguments is not None:
        request['arguments'] = arguments
    parent_socket.sendall((json.dumps(request) + '\n').encode())
    while True:
        reply = qmp_receive()
        if reply.get('id') != execute:
            continue
        if 'error' in reply:
            raise RuntimeError(str(reply['error']))
        return reply['return']

def screen(name):
    image = output / (name + '.ppm')
    qmp('screendump', {'filename': str(image), 'format': 'ppm'})
    data = image.read_bytes()
    magic, dimensions, maximum, pixels = data.split(b'\n', 3)
    assert magic == b'P6' and dimensions == b'1920 1080' and maximum == b'255'
    assert len(pixels) == 1920 * 1080 * 3
    return pixels

W, H, FB = 1920, 1080, 0x72000000
STRIDE = W * 4 + 64
SPAN = (H - 1) * STRIDE + W * 4
GFX = 0x30200000
colors = [(17, 34, 204, 255), (37, 211, 19, 255),
          (223, 53, 43, 255), (61, 157, 241, 255)]  # BGRA
rows = [bytes(colors[0]) * (W // 2) + bytes(colors[1]) * (W // 2),
        bytes(colors[2]) * (W // 2) + bytes(colors[3]) * (W // 2)]
source_pixels = ((rows[0] + bytes([0xAA]) * 64) * (H // 2)
                 + (rows[1] + bytes([0xAA]) * 64) * (H // 2))
rgb = [bytes((c[2], c[1], c[0])) for c in colors]
expected = ((rgb[0] * (W // 2) + rgb[1] * (W // 2)) * (H // 2)
            + (rgb[2] * (W // 2) + rgb[3] * (W // 2)) * (H // 2))
report = {'command': command, 'binary_and_inputs_sha256': hashes, 'cases': [],
          'guest_code_executed': False, 'macos_graphics_verified': False,
          'layer': 'synthetic guest RAM/MMIO -> Rust EFI copy -> QEMU display surface'}
start = time.monotonic()
with (output / 'qemu-stderr.log').open('wb') as log:
    process = subprocess.Popen(command, env=environment, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=log,
                               pass_fds=(child_socket.fileno(),))
    child_socket.close()
    try:
        assert 'QMP' in qmp_receive()
        qmp('qmp_capabilities')
        assert qmp('query-status')['running'] is False
        qt = QTest(process, 120)
        assert qt.read(GFX + 0x1204, 4) == 1
        assert qt.read(GFX + 0x120c, 4) == (W << 16) | H
        initial = screen('initial-black')
        assert initial == bytes(len(initial))
        report['cases'].append({'name': 'unprogrammed_black', 'passed': True})
        for offset in range(0, len(source_pixels), 65536):
            qt.memory_write(FB + offset, source_pixels[offset:offset + 65536])

        def configure(overrides=None):
            fields = {0x1210: (FB, 8), 0x1228: (STRIDE, 4),
                      0x1218: (32, 4), 0x1214: (SPAN, 4)}
            fields.update(overrides or {})
            qt.write(GFX + 0x1210, 0, 8)
            for register in (0x1228, 0x1218, 0x1214, 0x1210):
                value, size = fields[register]
                qt.write(GFX + register, value, size)

        configure()
        pixels = screen('padded-bgra-quadrants')
        assert pixels == expected, 'QMP RGB output differs from all synthetic BGRA source pixels'
        report['cases'].append({'name': 'padded_bgra_full_pixel_readback', 'passed': True,
                                'pixels': W * H, 'source_stride': STRIDE,
                                'rgb_sha256': hashlib.sha256(pixels).hexdigest()})
        invalid = [
            ('zero_address', {0x1210: (0, 8)}),
            ('short_stride', {0x1228: (W * 4 - 1, 4)}),
            ('over_policy_stride', {0x1228: (8192 * 4 + 4, 4)}),
            ('unsupported_depth', {0x1218: (16, 4)}),
            ('short_declared_length', {0x1214: (SPAN - 1, 4)}),
            ('address_overflow', {0x1210: (2**64 - 32, 8)}),
            ('self_mmio_address', {0x1210: (GFX, 8)}),
            ('cross_ram_end', {0x1210: (0x77FFF000, 8)}),
        ]
        changed = bytes((91, 82, 73, 255))
        for name, overrides in invalid:
            qt.write(GFX + 0x1210, 0, 8)
            qt.memory_write(FB, bytes(colors[0]))
            configure(overrides)
            qt.memory_write(FB, changed)
            actual = screen(name)
            assert actual == expected, name + ' changed the last valid frame'
            report['cases'].append({'name': name, 'passed': True,
                                    'last_valid_frame_preserved': True})
        configure()
        resumed_expected = bytes((73, 82, 91)) + expected[3:]
        assert screen('valid-frame-resumed') == resumed_expected
        report['cases'].append({'name': 'valid_frame_resumes_after_refusals', 'passed': True})
        assert qmp('query-status')['running'] is False
        qmp('quit')
        process.wait(timeout=10)
        assert process.returncode == 0
        report['passed'] = True
    except Exception as exc:
        report['passed'] = False
        report['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        process.stdin.close()
        process.stdout.close()
        parent_socket.close()
report['files_unchanged'] = all(hashlib.sha256(p.read_bytes()).hexdigest() == hashes[str(p)] for p in inputs)
report['passed'] = report['passed'] and report['files_unchanged']
report['seconds'] = time.monotonic() - start
report['case_count'] = len(report['cases'])
(root / 'firmware-console-result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
if not report['passed']:
    print((output / 'qemu-stderr.log').read_text()[-6000:])
raise SystemExit(0 if report['passed'] else 1)
