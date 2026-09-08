#!/usr/bin/env python3
"""Recognize only the authored compiled-enable-omission boundary, never any failure."""
import argparse, json, math, re, struct
from pathlib import Path
import verify_dynamic_ovmf as v

def validate(report):
    try:
        keys=set('schema passed host_architecture cases data controls host_validations markers parse_errors adjacent_transport_duplicate_lines input_paths input_sha256_before input_sha256_after serial_sha256 elapsed_seconds qemu_exit_code normal_boot_verified original_inputs_used'.split())
        if not isinstance(report,dict) or set(report)!=keys:raise ValueError('invalid envelope')
        if report['schema']!=v.SCHEMA or report['passed'] is not False or report['host_architecture'] not in ('x86_64','AMD64'):raise ValueError('not the failed authored execution')
        if report['normal_boot_verified'] is not False or report['original_inputs_used'] is not False or report['parse_errors']!=[]:raise ValueError('scope/parse error')
        if type(report['elapsed_seconds']) not in (int,float) or not math.isfinite(report['elapsed_seconds']) or not 0<=report['elapsed_seconds']<=90:raise ValueError('invalid elapsed time')
        if type(report['qemu_exit_code']) is not int or not -(1<<31)<=report['qemu_exit_code']<(1<<31):raise ValueError('invalid process status')
        if type(report['adjacent_transport_duplicate_lines']) is not int or report['adjacent_transport_duplicate_lines']<0:raise ValueError('invalid transport count')
        for field in ('input_paths','input_sha256_before','input_sha256_after'):
            if not isinstance(report[field],dict) or set(report[field])!=v.ROLES:raise ValueError('missing input roles')
        if any(not isinstance(s,str) or not s for s in report['input_paths'].values()):raise ValueError('invalid input path')
        for field in ('input_sha256_before','input_sha256_after'):
            if any(not isinstance(s,str) or not re.fullmatch('[0-9a-f]{64}',s) for s in report[field].values()):raise ValueError('invalid input digest')
        if report['input_sha256_before']!=report['input_sha256_after']:raise ValueError('mutated inputs')
        if not isinstance(report['serial_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',report['serial_sha256']):raise ValueError('invalid serial digest')
        if not isinstance(report['markers'],list):raise ValueError('missing raw markers')
        cases,data,controls,errors,clean,duplicates=v.parse_lines(report['markers'])
        if errors or (cases,data,controls)!=(report['cases'],report['data'],report['controls']) or duplicates!=report['adjacent_transport_duplicate_lines']:raise ValueError('raw capture mismatch')
        if len(cases)!=1 or len(data)!=4 or len(controls)!=2 or len(clean)!=9:raise ValueError('wrong event count')
        if clean[0]!=v.ENTRY or clean[-1]!='NXDYN: FAIL case=0 status=COMPROMISED_DATA':raise ValueError('wrong terminal boundary')
        for line,category,row in zip(clean[1:-1],['DATA']*4+['CONTROL']*2+['CASE'],data+controls+cases):
            if not line.startswith('NXDYN: '+category+' ') or dict(t.split('=',1) for t in line.split()[2:])!=row:raise ValueError('wrong event order')
        case=cases[0];a=v.parsed(case,v.CASE_KEYS,v.FLAGS|v.HASHES)
        if case['name']!='roundtrip' or any(case[k] != ('true' if k=='tables' else 'false') for k in v.FLAGS):raise ValueError('wrong authored assertions')
        if any(not isinstance(case[k],str) or not re.fullmatch('[0-9a-f]{64}',case[k]) for k in v.HASHES):raise ValueError('invalid memory digest')
        g=4096;post=v.RAM+g
        expected=dict(granule=g,status=8,provider=0,retired=3,blocks=4,fetch=4,data=0,completed=0,control=2,table_reads=0,tlbi_reads=0,esr=0,far=0,elr=post,spsr=0x3c5,pstate=0x3c5,pc=post,x0=v.SCTLR|1,x1=v.RAM+3*g-8,x2=9,x3=99,sp=v.RAM+0x400,version=3,bytes=512,tag=2,revision=1,epoch=1,invalidations=0,arch=v.SCTLR,effective=v.SCTLR,tcr=0x580100010,ttbr0=v.TABLE,ttbr1=v.TABLE,mair=0x44)
        if any(a[k]!=value for k,value in expected.items()):raise ValueError('wrong CPU/provider boundary')
        spans=[(a['ram_host'],8*g),(a['table_host'],8*g),(a['jit_host'],65536)]
        for i,(base,size) in enumerate(spans):
            if base==0 or base%16384 or base+size>=1<<64:raise ValueError('invalid host span')
            if any(base<other+length and other<base+size for other,length in spans[i+1:]):raise ValueError('overlapping backing')
        for i,(row,word) in enumerate(zip(data,[0x91000442,0x91000000,v.ISB,0xd4000002])):
            if (row.get('name'),row.get('granule'))!=('roundtrip','4096'):raise ValueError('wrong data owner')
            actual=v.parsed(row,v.DATA_KEYS);actual.pop('granule')
            pc=post-12+i*4
            want=dict(index=i,pc=pc,address=pc,operation=1,width=4,count=1,sctlr=v.SCTLR,epoch=1,reply=0,value0=word,value1=0,esr=0,fsc=0,far=0)
            if actual!=want:raise ValueError('wrong physical fetch')
        token=v.uint(controls[0].get('token',''))
        if token==0:raise ValueError('zero proposal token')
        for i,row in enumerate(controls):
            if (row.get('name'),row.get('granule'))!=('roundtrip','4096'):raise ValueError('wrong control owner')
            actual=v.parsed(row,v.CONTROL_KEYS);actual.pop('granule')
            want=dict(index=i,phase=i+1,operation=2,selector=0,pc=post-4,operand=token if i else 0,request_revision=1,request_epoch=1,reply=0,tag=i+1,token=0 if i else token,revision=1,epoch=1,invalidations=0,arch=v.SCTLR,effective=v.SCTLR)
            if actual!=want:raise ValueError('wrong ISB-only protocol')
        ram=bytearray([0xa5])*(8*g)
        ram[g-12:g]=struct.pack('<3I',0x91000442,0x91000000,v.ISB)
        ram[g:g+4]=struct.pack('<I',0xd4000002)
        payload=struct.pack('<12I',*v.tail(0));ram[3*g:3*g+len(payload)]=payload
        ram[5*g-8:5*g]=struct.pack('<Q',41)
        if case['ram_sha']!=v.digest(ram) or case['table_before_sha']!=case['table_after_sha']:raise ValueError('RAM/guard or table mutation')
        if report['host_validations']!=[v.validate_case(case,data,controls)]:raise ValueError('stale success-harness validation')
        return {'passed':True,'expected_failure':'actual M0 physical HVC unsupported boundary','status':8,'retired':3,'blocks':4,'fetch':4,'data':0,'control':2,'ram_sha256':v.digest(ram),'normal_boot_verified':False}
    except (ValueError,TypeError,KeyError,IndexError) as error:return {'passed':False,'error':str(error)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--serial',type=Path);a=p.parse_args()
    report=json.loads(a.report.read_text());result=validate(report)
    if result['passed']:
        binding=v.validate_serial_binding(report,a.serial or a.report.parent/'serial.log')
        if not binding['passed']:result=binding
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
