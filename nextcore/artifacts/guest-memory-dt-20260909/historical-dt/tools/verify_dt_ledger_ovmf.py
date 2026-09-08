#!/usr/bin/env python3
"""Run authored owned-DT/JIT integration on x86 OVMF; no original OS input."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import time

NAMES = ('roundtrip', 'invalid-dt')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def markers(path):
    if not path.exists(): return []
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', path.read_text(errors='replace'))
    return [line for line in text.splitlines() if line.startswith('NXDT:')]

def decode(blob, template):
    """Independent strict decoder for the exact authored single-root schema."""
    if len(blob) < 8: raise ValueError('short header')
    count, children = struct.unpack_from('<II', blob)
    if (count, children) != (2, 0): raise ValueError('unexpected root header')
    cursor, properties = 8, {}
    for _ in range(count):
        if cursor + 36 > len(blob): raise ValueError('short property')
        key = blob[cursor:cursor + 32]
        end = key.find(b'\0')
        if end < 1 or any(key[end:]): raise ValueError('noncanonical key')
        name = key[:end].decode('ascii')
        raw, = struct.unpack_from('<I', blob, cursor + 32)
        size, flagged = raw & 0x7fffffff, bool(raw >> 31)
        start = cursor + 36
        cursor = (start + size + 3) & ~3
        if cursor > len(blob) or any(blob[start + size:cursor]): raise ValueError('size/padding')
        if name in properties: raise ValueError('duplicate property')
        properties[name] = (blob[start:start + size], start, flagged)
    if cursor != len(blob) or set(properties) != {'name', 'authored-aperture'}:
        raise ValueError('trailing data or wrong properties')
    if properties['name'] != (b'\0', 44, False): raise ValueError('wrong literal name')
    if properties['authored-aperture'][2] != template: raise ValueError('wrong template flag')
    return properties

def program(offset):
    words = [0x91000063]
    for out, value in enumerate((0, 4, offset, offset + 4, offset + 8, offset + 12)):
        words.extend((0xb9400002 | ((value // 4) << 10), 0xb9000022 | (out << 10)))
    words.extend((0x52800002 | (0xabcd << 5), 0xb9000022 | (6 << 10), 0xd4400000))
    return struct.pack('<16I', *words)

def validate_case(case, data):
    keys = {'name','granule','upper','status','provider','retired','blocks','fetch','data','completed',
            'esr','far','reply','fsc','pc','x2','stale','ram','tables','ram_pa','ram_bytes','code_pa',
            'dt_pa','stack_pa','output_pa','entry','dt_va','output_va','sp','ram_host','table_host','jit_host','pass'}
    data_keys = {'name','granule','upper','source','wire','output','value_offset','ram_sha',
                 'tables_before_sha','tables_after_sha'}
    try:
        if set(case) != keys or set(data) != data_keys: raise ValueError('missing/extra keys')
        if any(case[k] != data[k] for k in ('name','granule','upper')): raise ValueError('identity mismatch')
        if case['name'] not in NAMES or case['granule'] not in ('4096','16384') or case['upper'] not in ('false','true'):
            raise ValueError('unknown case')
        flags = {'upper','stale','ram','tables','pass'}
        if any(case[k] not in ('true','false') for k in flags): raise ValueError('invalid boolean')
        actual = {k:int(case[k],0) for k in keys - flags - {'name'}}
        g = actual['granule']; invalid = case['name'] == 'invalid-dt'
        va = 0xffff800020000000 if case['upper'] == 'true' else 0x20000000
        expected = dict(granule=g,status=17 if invalid else 1,provider=0,retired=1 if invalid else 16,
            blocks=2 if invalid else 16,fetch=2 if invalid else 16,data=1 if invalid else 13,
            completed=0 if invalid else 13,esr=0x96000007 if invalid else 0,far=va+2*g if invalid else 0,
            reply=1 if invalid else 0,fsc=7 if invalid else 0,pc=va+g+(4 if invalid else 64),
            x2=0x13579bdf if invalid else 0xabcd,ram_pa=0x10000000,ram_bytes=16*g,
            code_pa=0x10000000+g,dt_pa=0x10000000+2*g,stack_pa=0x10000000+3*g,
            output_pa=0x10000000+4*g,entry=va+g,dt_va=va+2*g,output_va=va+4*g,sp=va+4*g)
        for k,v in expected.items():
            if actual[k] != v: raise ValueError(f'{k}: actual {actual[k]} != expected {v}')
        hosts = [(actual['ram_host'],16*g),(actual['table_host'],16*g),(actual['jit_host'],65536)]
        if any(base <= 0 or base % 16384 for base,size in hosts): raise ValueError('host alignment')
        for i,(a,n) in enumerate(hosts):
            for b,m in hosts[i+1:]:
                if a < b+m and b < a+n: raise ValueError('host alias')
        source, wire, output = (bytes.fromhex(data[k]) for k in ('source','wire','output'))
        src, dt = decode(source, True), decode(wire, False)
        if src['authored-aperture'][0] != b'opaque/observed-extent()\0': raise ValueError('unexpected authored source')
        value, offset, _ = dt['authored-aperture']
        if value != struct.pack('<QQ',actual['ram_pa'],actual['ram_bytes']): raise ValueError('unobserved property value')
        if int(data['value_offset']) != offset: raise ValueError('property offset mismatch')
        expected_output = bytes([0xa5])*28 if invalid else wire[:8]+value+struct.pack('<I',0xabcd)
        if output != expected_output: raise ValueError('guest serialized readback mismatch')
        expected_ram = bytearray([0xa5]) * actual['ram_bytes']
        code = program(offset)
        expected_ram[g:g+len(code)] = code
        expected_ram[2*g:2*g+len(wire)] = wire
        if not invalid: expected_ram[4*g:4*g+28] = expected_output
        if data['ram_sha'] != digest(expected_ram): raise ValueError('complete RAM/guard digest mismatch')
        if not re.fullmatch('[0-9a-f]{64}',data['tables_before_sha']) or data['tables_before_sha'] != data['tables_after_sha']:
            raise ValueError('table mutation or invalid digest')
        if any(case[k] != 'true' for k in ('stale','ram','tables','pass')): raise ValueError('firmware assertion failed')
        return {'passed':True,'expected_numeric':expected,'decoded_value':list(struct.unpack('<QQ',value)),
                'full_ram_sha256':digest(expected_ram),'output_bytes':len(output)}
    except (ValueError, KeyError, TypeError, struct.error) as error:
        return {'passed':False,'error':str(error)}

def parse_records(lines):
    cases, data, errors, seen = [], [], [], None
    duplicates=0
    for line in lines:
        if line == seen: duplicates+=1; continue
        seen=line
        category = next((key for key in ('CASE','DATA') if line.startswith('NXDT: '+key+' ')), None)
        if category is None: continue
        pairs=[word.split('=',1) for word in line.split()[2:]]
        if any(len(p)!=2 for p in pairs): errors.append('invalid token');continue
        fields=dict(pairs)
        if len(fields)!=len(pairs): errors.append('duplicate key')
        (cases if category=='CASE' else data).append(fields)
    return cases,data,errors,duplicates

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi-probe',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--qemu',default='qemu-system-x86_64')
    parser.add_argument('--ovmf-code',type=Path,default=Path('/usr/share/OVMF/OVMF_CODE_4M.fd'))
    parser.add_argument('--ovmf-vars',type=Path,default=Path('/usr/share/OVMF/OVMF_VARS_4M.fd'))
    parser.add_argument('--timeout',type=float,default=60)
    args=parser.parse_args()
    if not 0 < args.timeout <= 60: parser.error('timeout must be in (0,60]')
    inputs={'efi_probe':args.efi_probe.resolve(strict=True),'ovmf_code':args.ovmf_code.resolve(strict=True),
            'ovmf_vars':args.ovmf_vars.resolve(strict=True),'runner':Path(__file__).resolve()}
    output=args.output.resolve()
    if any(',' in str(p) for p in [*inputs.values(),output]) or any(not p.is_file() for p in inputs.values()): parser.error('invalid input path')
    before={role:sha(path) for role,path in inputs.items()};output.mkdir(parents=True,exist_ok=False)
    boot=output/'esp/EFI/BOOT';boot.mkdir(parents=True);shutil.copyfile(inputs['efi_probe'],boot/'BOOTX64.EFI')
    variables=output/'vars.fd';shutil.copyfile(inputs['ovmf_vars'],variables);serial=output/'serial.log'
    command=[args.qemu,'-machine','q35,accel=tcg,smm=off','-cpu','Nehalem','-m','256','-smp','1',
        '-display','none','-vga','std','-monitor','none','-serial',f'file:{serial}','-net','none','-no-reboot',
        '-drive',f"if=pflash,format=raw,readonly=on,file={inputs['ovmf_code']}",
        '-drive',f'if=pflash,format=raw,file={variables}','-drive',f"format=raw,file=fat:rw:{output/'esp'}"]
    (output/'command.json').write_text(json.dumps(command,indent=2)+'\n');start=time.monotonic()
    with (output/'stdout.log').open('wb') as out,(output/'stderr.log').open('wb') as err:
        process=subprocess.Popen(command,stdout=out,stderr=err)
        try:
            while process.poll() is None and time.monotonic()-start < args.timeout:
                if any(line.startswith(('NXDT: PASS','NXDT: FAIL')) for line in markers(serial)): break
                time.sleep(.1)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    lines=markers(serial);cases,data,errors,duplicates=parse_records(lines)
    identity=lambda row:tuple(row.get(k) for k in ('name','granule','upper'))
    expected={(n,str(g),str(u).lower()) for n in NAMES for g in (4096,16384) for u in (False,True)}
    datamap={identity(row):row for row in data}
    validations=[validate_case(row,datamap.get(identity(row),{})) for row in cases]
    after={role:sha(path) for role,path in inputs.items()}
    passed=(len(cases)==len(data)==8 and set(map(identity,cases))==set(datamap)==expected
        and all(v['passed'] for v in validations) and not errors and before==after
        and 'NXDT: PASS cases=8 macos_boot_verified=false' in lines
        and not any(line.startswith('NXDT: FAIL') for line in lines))
    report={'schema':'nextcore.authored-owned-dt-efi.v1','passed':passed,'host_architecture':platform.machine(),
        'cases':cases,'data':data,'host_validations':validations,'markers':lines,'parse_errors':errors,
        'adjacent_transport_duplicate_lines':duplicates,'input_paths':{k:str(v) for k,v in inputs.items()},
        'input_sha256_before':before,'input_sha256_after':after,'elapsed_seconds':round(time.monotonic()-start,3),
        'qemu_exit_code':process.returncode,'normal_boot_verified':False,'original_inputs_used':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':passed,'cases':len(cases),'report':str(output/'report.json')}))
    return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
