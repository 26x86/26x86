#!/usr/bin/env python3
"""Revalidate a complete actual report, then require copied-evidence mutations to fail."""
import argparse,copy,json,tempfile
from pathlib import Path
from verify_dynamic_ovmf import validate_capture,validate_case,sha

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--serial',type=Path,help='raw serial file; defaults to the report sibling serial.log')
    a=ap.parse_args();original=json.loads(a.report.read_text());serial=a.serial or a.report.parent/'serial.log'
    accepted=validate_capture(original,serial)
    if not accepted['passed']:raise SystemExit('invalid capture: '+accepted['error'])
    checks=[]
    def mutate(name,fn):
        report=copy.deepcopy(original);fn(report);result=validate_capture(report,serial)
        if result['passed']:raise RuntimeError('undetected mutation: '+name)
        checks.append({'name':name,'rejected':True,'error':result['error']})
    mutate('false_envelope',lambda r:r.update(passed=False))
    mutate('missing_envelope',lambda r:r.pop('schema'))
    mutate('nan_elapsed',lambda r:r.update(elapsed_seconds=float('nan')))
    mutate('boolean_process_status',lambda r:r.update(qemu_exit_code=True))
    mutate('missing_case',lambda r:r['cases'].pop())
    mutate('duplicate_case',lambda r:r['cases'].__setitem__(1,r['cases'][0]))
    mutate('reordered_cases',lambda r:r['cases'].reverse())
    mutate('conflicting_terminal',lambda r:r['markers'].append('NXDYN: FAIL forced=true'))
    mutate('parse_error',lambda r:r.update(parse_errors=['bad input']))
    mutate('missing_hash_role',lambda r:r['input_paths'].pop('runner'))
    mutate('changed_input_hash',lambda r:r['input_sha256_after'].update(efi_probe='00'*32))
    mutate('wrong_scope',lambda r:r.update(normal_boot_verified=True))
    mutate('forged_host_validation',lambda r:r['host_validations'][0].update(passed=False))
    mutate('missing_data_event',lambda r:r['data'].pop())
    mutate('missing_control_event',lambda r:r['controls'].pop())
    mutate('forged_serial_digest',lambda r:r.update(serial_sha256='00'*32))
    with tempfile.TemporaryDirectory(prefix='raw-serial-controls-',dir=a.output.parent) as temp:
        missing=Path(temp)/'missing.log'
        modified=Path(temp)/'modified.log';modified.write_bytes(serial.read_bytes()+b'\n')
        changed=Path(temp)/'changed-marker.log';changed.write_bytes(serial.read_bytes().replace(b'NXDYN: ENTRY',b'NXDYN: ALTERED',1))
        for name,path,update_digest in [('missing_raw_serial',missing,False),('changed_raw_serial',modified,False),('digest_rebound_wrong_markers',changed,True)]:
            report=copy.deepcopy(original)
            if update_digest:report['serial_sha256']=sha(path)
            result=validate_capture(report,path)
            if result['passed']:raise RuntimeError('undetected raw mutation: '+name)
            checks.append({'name':name,'rejected':True,'error':result['error']})
    case=original['cases'][0]
    d=[row for row in original['data'] if row['name']==case['name'] and row['granule']==case['granule']]
    c=[row for row in original['controls'] if row['name']==case['name'] and row['granule']==case['granule']]
    for name,target,index,key,value in [
        ('bad_retirement','case',0,'retired','16'),('bad_esr','case',0,'esr','1'),
        ('bad_ram_digest','case',0,'ram_sha','00'*32),('bad_table_digest','case',0,'table_after_sha','00'*32),
        ('u64_host_overflow','case',0,'ram_host',str(1<<64)),
        ('host_span_wrap','case',0,'ram_host',str((1<<64)-16384)),
        ('wrong_post_isb_epoch','data',3,'epoch','1'),('fabricated_next_fetch','data',3,'value0','0'),
        ('invalid_control_token','control',0,'token','0'),('wrong_isb_effective','control',2,'effective',str(0x30d00802)),
        ('wrong_commit_revision','control',3,'revision','1'),
    ]:
        row,dd,cc=copy.deepcopy(case),copy.deepcopy(d),copy.deepcopy(c)
        destination={'case':row,'data':dd[index] if target=='data' else None,'control':cc[index] if target=='control' else None}[target]
        destination[key]=value;result=validate_case(row,dd,cc)
        if result['passed']:raise RuntimeError('undetected case mutation: '+name)
        checks.append({'name':name,'rejected':True,'error':result['error']})
    a.output.write_text(json.dumps({'passed':True,'actual_validation':accepted,'negative_cases':checks,
        'input_report':str(a.report.resolve()),'input_serial':str(serial.resolve())},indent=2)+'\n')
    print(json.dumps({'passed':True,'negative_cases':len(checks)}))
if __name__=='__main__':main()
