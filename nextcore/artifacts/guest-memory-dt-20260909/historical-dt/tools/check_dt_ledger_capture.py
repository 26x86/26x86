#!/usr/bin/env python3
"""Check an actual authored capture and prove the reader rejects tampered evidence."""
import argparse
import copy
import json
from pathlib import Path
from verify_dt_ledger_ovmf import validate_case, parse_records

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    report=json.loads(args.report.read_text())
    identity=lambda c:tuple(c[k] for k in ('name','granule','upper'))
    data={identity(c):c for c in report['data']}
    assert len(report['cases'])==8
    assert all(validate_case(c,data[identity(c)])['passed'] for c in report['cases'])
    case=next(c for c in report['cases'] if c['name']=='roundtrip')
    blob=data[identity(case)]
    mutations=[]
    for name,target,key,value in [
        ('pass_true_wrong_retirement','case','retired','17'),
        ('pass_true_wrong_far','case','far','1'),
        ('pass_true_wrong_ram_digest','data','ram_sha','00'*32),
        ('pass_true_table_mutation','data','tables_after_sha','00'*32),
        ('wrong_property_offset','data','value_offset','80'),
        ('missing_field','case','completed',None),
        ('extra_field','case','fabricated','true'),
    ]:
        c,d=copy.deepcopy(case),copy.deepcopy(blob)
        row=c if target=='case' else d
        if value is None:row.pop(key)
        else:row[key]=value
        result=validate_case(c,d)
        assert not result['passed'], name
        mutations.append({'name':name,'rejected':True,'error':result['error']})
    _,_,errors,_=parse_records(['NXDT: CASE name=roundtrip name=invalid-dt'])
    assert errors==['duplicate key']
    record={'passed':True,'actual_cases_checked':8,'tampered_case_rejections':mutations,
            'duplicate_key_rejected':True,'input_capture':str(args.report.resolve())}
    args.output.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'passed':True,'negative_cases':len(mutations)+1}))
if __name__=='__main__':main()
