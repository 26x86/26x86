#!/usr/bin/env python3
"""Execute a self-authored AArch64 fixture against QEMU's actual ARM timers.

Linux/WSL only. GDB single stepping with timer suppression disabled and fixed
icount shift=0 exposes one-nanosecond virtual-clock boundaries. QMP's independent
instruction count is the counter oracle until the WFx idle-warp cases at the end.
No Apple firmware, macOS file, physical disk or host network configuration is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[1]
NS = 1_000_000_000
MASK = (1 << 64) - 1


class QMP:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.settimeout(10)
        self.s.connect(str(path))
        self.f = self.s.makefile('rwb', buffering=0)
        self.read()
        self.call('qmp_capabilities')

    def read(self):
        data = self.f.readline(1024 * 1024 + 1)
        if not data or len(data) > 1024 * 1024:
            raise RuntimeError('Invalid QMP response')
        return json.loads(data)

    def call(self, cmd):
        self.f.write(json.dumps({'execute': cmd}).encode() + b'\n')
        while True:
            item = self.read()
            if 'error' in item:
                raise RuntimeError(item['error'])
            if 'return' in item:
                return item['return']

    def icount(self):
        return self.call('query-replay')['icount']

    def close(self):
        self.f.close()
        self.s.close()


class GDB:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.settimeout(10)
        self.s.connect(str(path))
        self.regs = {}
        self._next_reg = 0
        self.command('qSupported:xmlRegisters=aarch64')
        self.xml('target.xml')

    def command(self, command):
        raw = command.encode()
        self.s.sendall(b'$' + raw + b'#' + f'{sum(raw) & 255:02x}'.encode())
        while self.s.recv(1) != b'$':
            pass
        packet = bytearray()
        while True:
            b = self.s.recv(1)
            if not b:
                raise EOFError('GDB disconnected')
            if b == b'#':
                break
            packet.extend(b)
        checksum = self.s.recv(2)
        if len(checksum) != 2 or int(checksum, 16) != sum(packet) & 255:
            raise RuntimeError('GDB checksum mismatch')
        self.s.sendall(b'+')
        decoded = bytearray()
        i = 0
        while i < len(packet):
            b = packet[i]
            i += 1
            if b == ord('}'):
                decoded.append(packet[i] ^ 0x20)
                i += 1
            elif b == ord('*'):
                decoded.extend(bytes([decoded[-1]]) * (packet[i] - 29))
                i += 1
            else:
                decoded.append(b)
        return bytes(decoded)

    def xml(self, name):
        data = b''
        while True:
            block = self.command(f'qXfer:features:read:{name}:{len(data):x},1000')
            if block[:1] not in (b'm', b'l'):
                raise RuntimeError(f'Cannot read GDB register XML {name}')
            data += block[1:]
            if block[:1] == b'l':
                break
        # GDB's target DTD supplies xi:include without an XML namespace.
        for node in ET.fromstring(data.replace(b'xi:include', b'include')).iter():
            if node.tag.endswith('include'):
                self.xml(node.attrib['href'])
            if node.tag == 'reg':
                idx = int(node.attrib.get('regnum', self._next_reg))
                self.regs[node.attrib['name'].lower()] = idx
                self._next_reg = idx + 1

    def read(self, name):
        data = self.command(f'p{self.regs[name.lower()]:x}')
        if not data or data.startswith(b'E'):
            raise RuntimeError(f'Cannot read register {name}: {data!r}')
        return int.from_bytes(bytes.fromhex(data.decode()), 'little')

    def write(self, name, value):
        command = f'P{self.regs[name.lower()]:x}={(value & MASK).to_bytes(8, "little").hex()}'
        if self.command(command) != b'OK':
            raise RuntimeError(f'Cannot write register {name}')

    def step(self, address, argument=None):
        # Continue to the following instruction with a normal breakpoint.
        # GDB single-step defaults suppress timers and are not a clock oracle.
        if self.command(f'Z0,{address + 4:x},4') != b'OK':
            raise RuntimeError('Cannot set instruction boundary breakpoint')
        self.write('pc', address)
        if argument is not None:
            self.write('x0', argument)
        response = self.command('c')
        if self.command(f'z0,{address + 4:x},4') != b'OK':
            raise RuntimeError('Cannot remove instruction boundary breakpoint')
        if not response.startswith((b'T05', b'S05')):
            raise RuntimeError(f'Unexpected GDB stop: {response!r}')


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_frequency(qemu, guest, symbols, frequency, output):
    records = []
    effective = min(frequency or NS, NS)
    with tempfile.TemporaryDirectory(prefix='vftimer-') as temp:
        temp = Path(temp)
        qmp_path, gdb_path = temp / 'qmp', temp / 'gdb'
        cpu = 'max' + (f',cntfrq={frequency}' if frequency else '')
        command = [str(qemu), '-M', 'virt,gic-version=3,virtualization=on,secure=off',
                   '-cpu', cpu, '-accel', 'tcg,thread=single', '-m', '128M', '-smp', '1',
                   '-display', 'none', '-serial', 'none', '-monitor', 'none', '-nic', 'none',
                   '-icount', 'shift=0,align=off,sleep=off', '-kernel', str(guest), '-S',
                   '-qmp', f'unix:{qmp_path},server=on,wait=off',
                   '-gdb', f'unix:{gdb_path},server=on,wait=off']
        log = output / f'{frequency or "default"}.stderr.log'
        with log.open('xb') as err:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL, stderr=err)
            qmp = gdb = None
            try:
                end = time.monotonic() + 10
                while not (qmp_path.exists() and gdb_path.exists()):
                    if process.poll() is not None or time.monotonic() > end:
                        raise RuntimeError('QEMU did not expose diagnostic sockets')
                    time.sleep(.01)
                qmp, gdb = QMP(qmp_path), GDB(gdb_path)
                if gdb.command(f'Z0,{symbols["ready"]:x},4') != b'OK':
                    raise RuntimeError('Cannot insert fixture breakpoint')
                stop = gdb.command('c')
                assert stop.startswith((b'T05', b'S05')), stop
                assert gdb.command(f'z0,{symbols["ready"]:x},4') == b'OK'
                advertised = gdb.read('cntfrq_el0')
                assert advertised == (frequency or NS), advertised
                # Reading the counter is a real MRS; each instruction consumes
                # one virtual ns. It samples after that instruction is counted.
                samples = []
                for _ in range(180):
                    gdb.step(symbols['read_phys'])
                    ns = qmp.icount()
                    actual = gdb.read('x0')
                    expected = ns * effective // NS
                    assert actual == expected, (ns, actual, expected)
                    samples.append({'ns': ns, 'actual_ticks': actual})
                records.append({'case': 'counter_exact_ns', 'passed': True, 'samples': samples})

                for kind, offset, intid in [('p', 0, 30), ('v', 2, 27)]:
                    gdb.step(symbols['set_voff'], offset)
                    now = qmp.icount()
                    target = (now + 100) * effective // NS + 2
                    deadline = (target * NS + effective - 1) // effective
                    gdb.step(symbols[f'set_{kind}_cval'], target - offset)
                    now = qmp.icount()
                    # Timer callbacks run between instructions. The first CTL
                    # MRS starts at deadline-1, the second starts at deadline.
                    nops = deadline - now - 3
                    assert 0 <= nops <= 2048, nops
                    gdb.write('x0', 1)
                    gdb.write('x1', symbols[f'timer_pad_end_{kind}'] - 4 * nops)
                    gdb.write('pc', symbols[f'timer_run_{kind}'])
                    assert gdb.command(f'Z0,{symbols["ready"]:x},4') == b'OK'
                    stop = gdb.command('c')
                    assert stop.startswith((b'T05', b'S05')), stop
                    assert gdb.command(f'z0,{symbols["ready"]:x},4') == b'OK'
                    assert qmp.icount() == deadline + 6, (qmp.icount(), deadline)
                    before_ns, after_ns = deadline - 1, deadline
                    before, after = gdb.read('x2'), gdb.read('x3')
                    assert before & 4 == 0, (before_ns, deadline, before)
                    assert after & 4, (after_ns, deadline, after)
                    assert gdb.read('x5') == (deadline + 3) * effective // NS
                    irq = gdb.read('x4')
                    assert irq == intid, (kind, irq, intid)
                    gdb.step(symbols['read_irq'])
                    drained = gdb.read('x0')
                    assert drained == 1023, drained
                    records.append({'case': f'{kind}_deadline_irq', 'passed': True,
                                    'offset_ticks': offset, 'absolute_target_ticks': target,
                                    'deadline_ns': deadline, 'before_ns': before_ns,
                                    'before_ctl': before, 'after_ns': after_ns,
                                    'after_ctl': after, 'irq': irq, 'after_eoi_irq': drained})

                # Idle warping changes virtual-clock bias, so these are last.
                # The controlled fixture has no other events or unmasked IRQ.
                gdb.step(symbols['set_voff'], 0)
                for instruction in ('wfit', 'wfet'):
                    gdb.step(symbols['clear_event'])
                    gdb.step(symbols['clear_event'] + 4)
                    gdb.step(symbols['read_virt'])
                    before = gdb.read('x0')
                    target = before + max(100, effective // 1000)
                    gdb.write('pc', symbols[f'wait_{instruction}'])
                    gdb.write('x0', target)
                    assert gdb.command(f'Z0,{symbols["ready"]:x},4') == b'OK'
                    stop = gdb.command('c')
                    assert stop.startswith((b'T05', b'S05')), stop
                    assert gdb.command(f'z0,{symbols["ready"]:x},4') == b'OK'
                    gdb.step(symbols['read_virt'])
                    after = gdb.read('x0')
                    assert target <= after <= target + 3, (instruction, before, target, after)
                    records.append({'case': instruction + '_timeout', 'passed': True,
                                    'before_ticks': before, 'target_ticks': target, 'after_ticks': after})
                return {'frequency': frequency or 'default', 'effective_hz': effective,
                        'advertised_hz': advertised, 'passed': True, 'cases': records,
                        'command': command}
            finally:
                if gdb:
                    gdb.s.close()
                if qmp:
                    qmp.close()
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--frequencies', nargs='+', type=int,
                        default=[24000000, 19200000, 62500000, 1000000000, 0])
    args = parser.parse_args()
    if os.name == 'nt':
        parser.error('Run under Linux/WSL alongside the candidate QEMU')
    if any(x < 0 or x > MASK for x in args.frequencies):
        parser.error('Frequencies must fit uint64; 0 tests the CPU default')
    args.output.mkdir(parents=True, exist_ok=False)
    source = PROJECT / 'guests/timer_precision.S'
    obj, guest = args.output / 'timer.o', args.output / 'timer.elf'
    for command in [
        ['aarch64-linux-gnu-as', '-o', str(obj), str(source)],
        ['aarch64-linux-gnu-ld', '-Ttext=0x40080000', '-e', '_start', '-o', str(guest), str(obj)],
    ]:
        subprocess.run(command, check=True, capture_output=True, timeout=30)
    nm = subprocess.check_output(['aarch64-linux-gnu-nm', str(guest)], text=True, timeout=10)
    symbols = {p[2]: int(p[0], 16) for line in nm.splitlines() if len(p := line.split()) == 3}
    report = {'schema': 1, 'passed': False, 'qemu_sha256': sha256(args.qemu),
              'guest_sha256': sha256(guest), 'source_sha256': sha256(source),
              'self_authored_guest_only': True, 'macos_boot_verified': False, 'runs': []}
    try:
        for hz in args.frequencies:
            result = run_frequency(args.qemu.resolve(), guest.resolve(), symbols, hz, args.output)
            report['runs'].append(result)
            print(f'ARM timer {hz or "default"}: {len(result["cases"])} PASS', flush=True)
        report['passed'] = True
    except BaseException as exc:
        report['error_type'], report['error'] = type(exc).__name__, str(exc)
        raise
    finally:
        (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
