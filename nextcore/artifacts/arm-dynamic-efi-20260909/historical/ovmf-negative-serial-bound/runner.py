#!/usr/bin/env python3
"""Actual x86 OVMF dynamic MMU-enable proof; synthetic inputs only."""
import argparse, hashlib, json, math, platform, re, shutil, struct, subprocess, time
from pathlib import Path

RAM=0x40000000; TABLE=0x10000000; SCTLR=0x30d00802
ISB=0xd5033fdf; DSB=0xd5033f9f; TLBI=0xd508871f; HLT=0xd4400000
NAMES=('roundtrip','fetch-translation','data-translation')
IDENTITIES=[(n,str(g)) for g in (4096,16384) for n in NAMES]
CASE_KEYS=set('name granule status provider retired blocks fetch data completed control table_reads tlbi_reads esr far elr spsr pstate pc x0 x1 x2 x3 sp version bytes tag revision epoch invalidations arch effective tcr ttbr0 ttbr1 mair transition protocol ram tables ram_host table_host jit_host ram_sha table_before_sha table_after_sha pass'.split())
DATA_KEYS=set('name granule index pc address operation width count sctlr epoch reply value0 value1 esr fsc far'.split())
CONTROL_KEYS=set('name granule index phase operation selector pc operand request_revision request_epoch reply tag token revision epoch invalidations arch effective'.split())
FLAGS={'transition','protocol','ram','tables','pass'}
HASHES={'ram_sha','table_before_sha','table_after_sha'}
ROLES={'efi_probe','ovmf_code','ovmf_vars','runner'}
SCHEMA='nextcore.authored-dynamic-efi.v1'
ENTRY='NXDYN: ENTRY host=x86_64 authored=true profile=nextcore-stage1-enable-nc-v1'
PASS='NXDYN: PASS cases=6 macos_boot_verified=false'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(blob):return hashlib.sha256(blob).hexdigest()
def markers(path):
    if not path.exists():return []
    text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',path.read_text(errors='replace'))
    return [line for line in text.splitlines() if line.startswith('NXDYN:')]
def uint(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)',value):raise ValueError('noncanonical integer')
    n=int(value,0) if value.startswith('0x') else int(value)
    if not 0<=n<1<<64:raise ValueError('integer outside u64')
    return n

def parsed(row,keys,exclude=()):
    if not isinstance(row,dict) or set(row)!=keys:raise ValueError('missing/extra row keys')
    return {key:uint(value) for key,value in row.items() if key not in {'name',*exclude}}

def tail(kind):
    return ([0xd5381000,0xf9400023,0x91000463,0xf9000023,0xa9000c22,0xa9400823,
             DSB,TLBI,DSB,ISB,0xf9400020,HLT] if kind==0 else [0xf9400023,HLT])

def expected_data(g,kind):
    entry=RAM+g-12;post=RAM+g;data_va=RAM+3*g-8 if kind==0 else RAM+2*g
    result=[]
    def event(pc,op,address,width,count,value0=0,value1=0,fault=False):
        before=pc<post
        result.append(dict(index=len(result),pc=pc,address=address,operation=op,width=width,count=count,
            sctlr=SCTLR if before else SCTLR|1,epoch=1 if before else 2,reply=int(fault),
            value0=value0,value1=value1,esr=(0x86000007 if op==1 else 0x96000007) if fault else 0,
            fsc=7 if fault else 0,far=address if fault else 0))
    for i,word in enumerate((0x91000442,0xd5181000,ISB)):event(entry+4*i,1,entry+4*i,4,1,word)
    if kind==1:event(post,1,post,4,1,fault=True);return result
    for i,word in enumerate(tail(kind)):
        pc=post+4*i;event(pc,1,pc,4,1,word)
        if kind==2:
            event(pc,2,data_va,8,1,fault=True);break
        if i==1:event(pc,2,data_va,8,1,41)
        if i==3:event(pc,3,data_va,8,1)
        if i==4:event(pc,3,data_va,8,2)
        if i==5:event(pc,2,data_va,8,2,9,42)
        if i==10:event(pc,2,data_va,8,1,9)
    return result

def validate_case(case,data,controls):
    try:
        a=parsed(case,CASE_KEYS,FLAGS|HASHES)
        if case['name'] not in NAMES or a['granule'] not in (4096,16384):raise ValueError('unknown case')
        if any(case[k]!='true' for k in FLAGS):raise ValueError('firmware assertion not true')
        if any(not isinstance(case[k],str) or not re.fullmatch('[0-9a-f]{64}',case[k]) for k in HASHES):raise ValueError('invalid digest')
        g=a['granule'];kind=NAMES.index(case['name']);post=RAM+g;entry=post-12;data_va=RAM+3*g-8 if kind==0 else RAM+2*g
        tsz=17 if g==16384 else 16
        tcr=tsz|(tsz<<16)|(5<<32)|((2<<14)|(1<<30) if g==16384 else 2<<30)
        expected=dict(granule=g,status=(1,16,17)[kind],provider=0,retired=15 if kind==0 else 3,
            blocks=(15,3,4)[kind],fetch=15 if kind==0 else 4,data=(5,0,1)[kind],completed=5 if kind==0 else 0,
            control=12 if kind==0 else 4,esr=(0,0x86000007,0x96000007)[kind],
            far=(0,post,data_va)[kind],elr=0 if kind==0 else post,spsr=0 if kind==0 else 0x3c5,
            pstate=0x3c5,pc=post+48 if kind==0 else post,x0=9 if kind==0 else SCTLR|1,x1=data_va,
            x2=42 if kind==0 else 9,x3=9 if kind==0 else 99,sp=RAM+0x400,
            version=3,bytes=512,tag=2,revision=2,epoch=2,invalidations=int(kind==0),arch=SCTLR|1,
            effective=SCTLR|1,tcr=tcr,ttbr0=TABLE,ttbr1=TABLE,mair=0x44)
        for k,v in expected.items():
            if a[k]!=v:raise ValueError(f'{k}: actual {a[k]} expected {v}')
        if a['table_reads']==0 or (kind==0 and not 0<a['tlbi_reads']<a['table_reads']) or (kind!=0 and a['tlbi_reads']!=0):
            raise ValueError('missing table walk/invalidation witness')
        spans=[(a['ram_host'],8*g),(a['table_host'],8*g),(a['jit_host'],65536)]
        for i,(base,size) in enumerate(spans):
            if base==0 or base%16384 or base+size>=1<<64:raise ValueError('invalid host span')
            for other,length in spans[i+1:]:
                if base<other+length and other<base+size:raise ValueError('aliased host spans')
        expected_events=expected_data(g,kind)
        if len(data)!=len(expected_events):raise ValueError('wrong data event count')
        for row,want in zip(data,expected_events):
            if (row.get('name'),row.get('granule'))!=(case['name'],case['granule']):raise ValueError('wrong data event owner')
            actual=parsed(row,DATA_KEYS);actual.pop('granule')
            if actual!=want:raise ValueError(f'data event {want["index"]} mismatch')
        operations=[(entry+4,1,1),(entry+8,2,0)]
        if kind==0:operations.extend(((post+24,3,0),(post+28,4,0),(post+32,3,0),(post+36,2,0)))
        if len(controls)!=2*len(operations):raise ValueError('wrong control event count')
        tokens=[]
        for i,(pc,op,selector) in enumerate(operations):
            request_revision=1 if i==0 else 2;request_epoch=1 if i<=1 else 2
            epoch=1 if i==0 else 2;invalidations=int(kind==0 and i>=3)
            pair=controls[2*i:2*i+2];token=uint(pair[0].get('token',''))
            if token==0 or token in tokens:raise ValueError('invalid/reused proposal token')
            tokens.append(token)
            for j,row in enumerate(pair):
                if (row.get('name'),row.get('granule'))!=(case['name'],case['granule']):raise ValueError('wrong control owner')
                actual=parsed(row,CONTROL_KEYS);actual.pop('granule')
                want=dict(index=2*i+j,phase=j+1,operation=op,selector=selector,pc=pc,
                    operand=token if j else (SCTLR|1 if i==0 else 0),request_revision=request_revision,
                    request_epoch=request_epoch,reply=0,tag=j+1,token=0 if j else token,revision=2,
                    epoch=epoch,invalidations=invalidations,arch=SCTLR|1,effective=SCTLR if i==0 else SCTLR|1)
                if actual!=want:raise ValueError(f'control event {2*i+j} mismatch')
        ram=bytearray([0xa5])*(8*g)
        ram[g-12:g]=struct.pack('<3I',0x91000442,0xd5181000,ISB)
        ram[g:g+4]=struct.pack('<I',0xd4000002)
        payload=struct.pack('<'+'I'*len(tail(kind)),*tail(kind));ram[3*g:3*g+len(payload)]=payload
        ram[5*g-8:5*g]=struct.pack('<Q',9 if kind==0 else 41)
        if kind==0:ram[2*g:2*g+8]=struct.pack('<Q',42)
        if case['ram_sha']!=digest(ram):raise ValueError('complete RAM/guard mismatch')
        if case['table_before_sha']!=case['table_after_sha']:raise ValueError('immutable table changed')
        return {'passed':True,'expected_numeric':expected,'data_events':len(data),'control_events':len(controls),
                'proposal_tokens':tokens,'ram_sha256':digest(ram)}
    except (ValueError,KeyError,TypeError,IndexError) as error:return {'passed':False,'error':str(error)}

def parse_lines(lines):
    cases=[];data=[];controls=[];errors=[];dedup=[];previous=None;duplicates=0
    for line in lines:
        if not isinstance(line,str):errors.append('non-string marker');continue
        if line==previous:duplicates+=1;continue
        previous=line;dedup.append(line)
        category=next((key for key in ('CASE','DATA','CONTROL') if line.startswith('NXDYN: '+key+' ')),None)
        if not category:continue
        pairs=[token.split('=',1) for token in line.split()[2:]]
        if any(len(pair)!=2 for pair in pairs):errors.append('malformed token');continue
        row=dict(pairs)
        if len(row)!=len(pairs):errors.append('duplicate key')
        {'CASE':cases,'DATA':data,'CONTROL':controls}[category].append(row)
    return cases,data,controls,errors,dedup,duplicates

def validate_report(report):
    try:
        required={'schema','passed','host_architecture','cases','data','controls','host_validations','markers','parse_errors',
            'adjacent_transport_duplicate_lines','input_paths','input_sha256_before','input_sha256_after','serial_sha256',
            'elapsed_seconds','qemu_exit_code','normal_boot_verified','original_inputs_used'}
        if not isinstance(report,dict) or set(report)!=required:raise ValueError('invalid report envelope')
        if report['schema']!=SCHEMA or report['passed'] is not True or report['host_architecture'] not in ('x86_64','AMD64'):
            raise ValueError('failed or foreign envelope')
        if report['normal_boot_verified'] is not False or report['original_inputs_used'] is not False:raise ValueError('wrong scope')
        if report['parse_errors']!=[]:raise ValueError('parse errors')
        if type(report['elapsed_seconds']) not in (int,float) or not math.isfinite(report['elapsed_seconds']) or not 0<=report['elapsed_seconds']<=90:raise ValueError('invalid elapsed time')
        if type(report['qemu_exit_code']) is not int or not -(1<<31)<=report['qemu_exit_code']<(1<<31):raise ValueError('invalid process status')
        if type(report['adjacent_transport_duplicate_lines']) is not int or report['adjacent_transport_duplicate_lines']<0:raise ValueError('invalid transport count')
        for field in ('input_paths','input_sha256_before','input_sha256_after'):
            if not isinstance(report[field],dict) or set(report[field])!=ROLES:raise ValueError('missing input roles')
        if any(not isinstance(v,str) or not v for v in report['input_paths'].values()):raise ValueError('invalid input paths')
        for field in ('input_sha256_before','input_sha256_after'):
            if any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) for v in report[field].values()):raise ValueError('invalid input hash')
        if report['input_sha256_before']!=report['input_sha256_after']:raise ValueError('input mutation')
        if not isinstance(report['serial_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',report['serial_sha256']):raise ValueError('missing serial digest')
        if not isinstance(report['markers'],list):raise ValueError('invalid marker list')
        cases,data,controls,errors,clean,duplicates=parse_lines(report['markers'])
        if errors or (cases,data,controls)!=(report['cases'],report['data'],report['controls']):raise ValueError('marker/row disagreement')
        if duplicates!=report['adjacent_transport_duplicate_lines']:raise ValueError('wrong transport duplicate count')
        if not clean or clean[0]!=ENTRY or clean[-1]!=PASS or any(line.startswith('NXDYN: FAIL') for line in clean):raise ValueError('missing/conflicting terminal marker')
        if clean.count(ENTRY)!=1 or clean.count(PASS)!=1:raise ValueError('repeated terminal marker')
        if [(row.get('name'),row.get('granule')) for row in cases]!=IDENTITIES:raise ValueError('missing/repeated/reordered case')
        # Enforce the entire event order: each case emits its own DATA then CONTROL then CASE.
        cursor=1;validations=[];all_tokens=[]
        for row in cases:
            identity=(row['name'],row['granule'])
            d=[q for q in data if (q.get('name'),q.get('granule'))==identity]
            c=[q for q in controls if (q.get('name'),q.get('granule'))==identity]
            for category,records in (('DATA',d),('CONTROL',c),('CASE',[row])):
                for record in records:
                    if cursor>=len(clean)-1 or not clean[cursor].startswith('NXDYN: '+category+' '):raise ValueError('event order mismatch')
                    pairs=dict(word.split('=',1) for word in clean[cursor].split()[2:])
                    if pairs!=record:raise ValueError('event ownership/order mismatch')
                    cursor+=1
            valid=validate_case(row,d,c)
            if not valid['passed']:raise ValueError(valid['error'])
            validations.append(valid);all_tokens.extend(valid['proposal_tokens'])
        if cursor!=len(clean)-1:raise ValueError('unexpected events')
        if len(all_tokens)!=len(set(all_tokens)):raise ValueError('cross-owner proposal token reuse')
        if validations!=report['host_validations']:raise ValueError('forged/stale host validation')
        return {'passed':True,'cases':len(cases),'data_events':len(data),'control_events':len(controls)}
    except (ValueError,TypeError,KeyError,IndexError) as error:return {'passed':False,'error':str(error)}

def validate_serial_binding(report, serial):
    """Bind a report to actual raw bytes; structural validation alone is not capture evidence."""
    try:
        serial=Path(serial)
        if not serial.is_file():raise ValueError('missing raw serial file')
        if sha(serial)!=report['serial_sha256']:raise ValueError('raw serial digest mismatch')
        if markers(serial)!=report['markers']:raise ValueError('raw serial marker mismatch')
        return {'passed':True,'serial_sha256':sha(serial)}
    except (ValueError,TypeError,KeyError,OSError) as error:return {'passed':False,'error':str(error)}

def validate_capture(report, serial):
    structure=validate_report(report)
    if not structure['passed']:return structure
    binding=validate_serial_binding(report,serial)
    return {**structure,'serial_sha256':binding['serial_sha256']} if binding['passed'] else binding

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--efi-probe',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--qemu',default='qemu-system-x86_64')
    ap.add_argument('--ovmf-code',type=Path,default=Path('/usr/share/OVMF/OVMF_CODE_4M.fd'))
    ap.add_argument('--ovmf-vars',type=Path,default=Path('/usr/share/OVMF/OVMF_VARS_4M.fd'))
    ap.add_argument('--timeout',type=float,default=60);a=ap.parse_args()
    if not 0<a.timeout<=60:ap.error('timeout must be in (0,60]')
    inputs={'efi_probe':a.efi_probe.resolve(strict=True),'ovmf_code':a.ovmf_code.resolve(strict=True),
        'ovmf_vars':a.ovmf_vars.resolve(strict=True),'runner':Path(__file__).resolve()}
    output=a.output.resolve()
    if any(',' in str(p) for p in [*inputs.values(),output]) or any(not p.is_file() for p in inputs.values()):ap.error('invalid input path')
    before={role:sha(path) for role,path in inputs.items()};output.mkdir(parents=True,exist_ok=False)
    boot=output/'esp/EFI/BOOT';boot.mkdir(parents=True);shutil.copyfile(inputs['efi_probe'],boot/'BOOTX64.EFI')
    variables=output/'vars.fd';shutil.copyfile(inputs['ovmf_vars'],variables);serial=output/'serial.log'
    command=[a.qemu,'-machine','q35,accel=tcg,smm=off','-cpu','Nehalem','-m','256','-smp','1','-display','none',
        '-vga','std','-monitor','none','-serial',f'file:{serial}','-net','none','-no-reboot',
        '-drive',f"if=pflash,format=raw,readonly=on,file={inputs['ovmf_code']}",'-drive',f'if=pflash,format=raw,file={variables}',
        '-drive',f"format=raw,file=fat:rw:{output/'esp'}"]
    (output/'command.json').write_text(json.dumps(command,indent=2)+'\n');start=time.monotonic()
    with (output/'stdout.log').open('wb') as out,(output/'stderr.log').open('wb') as err:
        process=subprocess.Popen(command,stdout=out,stderr=err)
        try:
            while process.poll() is None and time.monotonic()-start<a.timeout:
                if any(line.startswith(('NXDYN: PASS','NXDYN: FAIL')) for line in markers(serial)):break
                time.sleep(.1)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    lines=markers(serial);cases,data,controls,errors,clean,duplicates=parse_lines(lines)
    validations=[validate_case(row,[d for d in data if (d.get('name'),d.get('granule'))==(row.get('name'),row.get('granule'))],
        [c for c in controls if (c.get('name'),c.get('granule'))==(row.get('name'),row.get('granule'))]) for row in cases]
    report={'schema':SCHEMA,'passed':True,'host_architecture':platform.machine(),'cases':cases,'data':data,'controls':controls,
        'host_validations':validations,'markers':lines,'parse_errors':errors,'adjacent_transport_duplicate_lines':duplicates,
        'input_paths':{k:str(v) for k,v in inputs.items()},'input_sha256_before':before,
        'input_sha256_after':{k:sha(v) for k,v in inputs.items()},'serial_sha256':sha(serial) if serial.exists() else '',
        'elapsed_seconds':round(time.monotonic()-start,3),'qemu_exit_code':process.returncode,
        'normal_boot_verified':False,'original_inputs_used':False}
    validation=validate_capture(report,serial);report['passed']=validation['passed']
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'cases':len(cases),'report':str(output/'report.json'),'validation':validation}))
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
