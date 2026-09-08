#!/usr/bin/env python3
"""Frozen actual Arm observations to canonical Rust service; no source mutations."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
FROZEN={'report.json':'61ada4442287b044e5f2dc0c0dbc16ea463127ed4a3092091585e1148095f8eb','normal.log':'28b8f3f37859628f8fd3b1be039ca9dbc589fd255e0e419233de633b59e5305b','operation_oracle.c':'0105e3d82e6e9c44c33c1e50c1ebcadabe781f88548c9a0a57ef94668f524692','operation_start.S':'9dce34271e0f8a8525d40761202cc7462cc850c412195b7af4e0db97d9381ec6'}
FROZEN_ERET={'report.json': '14c01bbae5f9fb1bce4545857f85a4e544e9dc2d2ddad7969b74b140f4a0fd6a', 'normal.log': 'c5f3f97663098ed8d2dddd6872eed4faa5c925eee0bc5fa741b717dfc0c0e324', 'operation_oracle.c': '4fcabed2149ab0c5a69a543bc34f52339d2e34386687ca2335b9b33d771a23d4', 'operation_start.S': '74f8a277460abd832036349bfcbd9fed91a1f9e1b398efe340a4b6c6e6301990'}
RUNTIME_FILES=['memory-service/src/lib.rs','memory-service/src/abi.rs','memory-service/src/abi_v2.rs','memory-service/src/stage1.rs','preos/src/mmu.rs','preos/src/exception_level.rs']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,why):
 if not ok:raise ValueError(why)
def elf_info(path):
 b=path.read_bytes();require(b[:6]==b'\x7fELF\x02\x01','ELF64LE required')
 h=struct.unpack_from('<16sHHIQQQIHHHHHH',b);require(h[2]==183,'AArch64 required')
 def take(at,n):
  require(0<=at<=len(b) and 0<=n<=len(b)-at,'ELF bounds');return b[at:at+n]
 sections=[struct.unpack('<IIQQQQIIQQ',take(h[6]+i*h[11],64)) for i in range(h[12])]
 symbols={}
 for s in sections:
  if s[1]!=2:continue
  names=sections[s[6]];names=take(names[4],names[5]);require(s[9]==24,'symbol size')
  for at in range(s[4],s[4]+s[5],24):
   name,info,other,index,value,size=struct.unpack('<IBBHQQ',take(at,24));require(name<len(names),'name bounds')
   end=names.find(b'\0',name);require(end>=name,'name terminator');label=names[name:end].decode('ascii')
   if label:symbols[label]=(value,size)
 segments=[struct.unpack('<IIQQQQQQ',take(h[5]+i*h[9],56)) for i in range(h[10])]
 def word(pa):
  for kind,flags,off,va,physical,filesz,memsz,align in segments:
   if kind==1 and physical<=pa and pa+4<=physical+filesz:return int.from_bytes(take(off+pa-physical,4),'little')
  raise ValueError('instruction outside ELF')
 return symbols,word
def expected(c):
 if not c['expected_fault']:return dict(result=0,fault=0,level=0xffffffff,fsc=0,esr=0,address=0)
 esr=c['esr'];ec=esr>>26;fsc=esr&63
 if ec==0x22:kind,level,code=1,0xffffffff,0
 elif fsc==0x21:kind,level,code=2,0xffffffff,0x21
 else:
  kind={4:4,8:6,12:5}.get(fsc&~3);require(kind is not None,'unexpected FSC');level=fsc&3;code=fsc
 return dict(result=1,fault=kind,level=level,fsc=code,esr=esr,address=c['far'])
def compare(c,actual,unsupported=False,mutate=False):
 e=expected(c)
 if unsupported:e=dict(result=4,fault=0,level=0xffffffff,fsc=0,esr=0,address=0)
 if mutate:e['esr']^=1
 checks={k:actual[k]==v for k,v in e.items()}
 checks['no_values_on_failure']=actual['result']==0 or actual['value0']==actual['value1']==0
 if actual['result']==0:checks['authored_read_value']=actual['value0']==(0xd65f03c0 if c['access']==2 else 0) and actual['value1']==0
 checks['original_zero_store_backing_unchanged']=actual['ram_unchanged']==1
 return dict(name=c['name'],expected=e,actual=actual,checks=checks,passed=all(checks.values()))
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for flag in ['oracle-run','oracle-elf','runtime','output']:p.add_argument('--'+flag,type=Path,required=True)
 p.add_argument('--rustc',default='rustc');p.add_argument('--oracle-kind',choices=['original428','eret78'],default='original428');a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);oracle=a.oracle_run.resolve();runtime=a.runtime.resolve()
 before={f:sha(runtime/f) for f in RUNTIME_FILES}
 source_freeze=Path(__file__).with_name('source-freeze.json')
 require(before==json.loads(source_freeze.read_text())['source_sha256'],'canonical runtime differs from approved source freeze')
 (out/'source-freeze.json').write_bytes(source_freeze.read_bytes())
 frozen=FROZEN if a.oracle_kind=='original428' else FROZEN_ERET
 required_count=428 if a.oracle_kind=='original428' else 78
 (out/'replay.py').write_bytes(Path(__file__).read_bytes())
 for f,h in frozen.items():require(sha(oracle/f)==h,'frozen input changed: '+f)
 report=json.loads((oracle/'report.json').read_text());require(report['passed'] and report['case_count']==required_count,'oracle scope')
 require(sha(a.oracle_elf)==report['executable_sha256']['normal'],'captured ELF hash')
 require(report['observed_regimes']['normal']=={'HCR':1<<31,'CURRENT_EL':8},'HCR must be RW only')
 symbols,word=elf_info(a.oracle_elf);base=symbols['tables'][0];code=symbols['code'][0];data=symbols['data'][0]
 require(all(symbols[n][1]==0x10000 for n in ('tables','code','data')),'array sizes')
 require(code==base+0x10000 and data==code+0x10000,'array layout')
 operations={0:('load64',0xf9400002,2,8,1),1:('store64',0xf900001f,3,8,1),3:('pair_load32',0x29401002,2,4,2),4:('pair_store32',0x29007c1f,3,4,2),5:('pair_load64',0xa9401002,2,8,2),6:('pair_store64',0xa9007c1f,3,8,2)}
 raw={}
 for line in (oracle/'normal.log').read_text().splitlines():
  parts=line.split()
  if parts and '.' not in parts[0] and parts[0].startswith('g'):
   require(parts[0] not in raw and len(parts)==9,'raw capture shape');raw[parts[0]]=[int(x,16) for x in parts[1:]]
 rows=[];inputs=[]
 for c in report['cases']:
  q=c['observed_input'];capture=raw[c['name']]
  require(c['passed'] and all(c['checks'].values()) and c['esr']==c['expected_esr'],'failed source case')
  require(capture[:3]==[c['esr'],c['far'],c['elr']] and capture[4:7]==[c['spsr'],c['handler_el'],q['va']],'raw/report mismatch')
  require(q['access']==c['access'] and q['target_el']==c['el'],'operation mismatch')
  require([q[f'table{i}'] for i in range(4)]==[base+i*0x4000 for i in range(4)],'captured table bases')
  require(q['ttbr1']==base+c['start']*0x4000 and q['ttbr0']==code+c['start']*0x4000,'roots')
  require(q['sctlr']==0x30d00803 and q['mair']==0x44,'controls')
  require(c['spsr']&~0xf0000bcf==0 and (c['spsr']&15)==(5 if c['el']==1 else 0),'PSTATE shape')
  if c['access']==2:op,width,count,pc,instruction=1,4,1,q['va'],0xd65f03c0
  else:
   label,instruction,op,width,count=operations[c['access']];pc=symbols[label][0];require(word(pc)==instruction,'operation word')
  require(capture[7]==pc and (not c['expected_fault'] or c['elr']==pc),'captured PC')
  unsupported=bool(c['spsr']&0x800);require(not unsupported or c['access']==2,'unexpected BTYPE')
  fields={k:q[k] for k in ['ttbr0','ttbr1','tcr','sctlr','mair']}
  fields.update(pstate=c['spsr'],el=c['el'],pc=pc,va=q['va'],op=op,width=width,count=count,granule=c['granule'],second=q['second_page'])
  rows.append('Case{name:'+json.dumps(c['name'])+','+','.join(f'{k}:{v}' for k,v in fields.items())+',tables:['+','.join(str(q[f'value{i}']) for i in range(4))+']}')
  inputs.append(dict(name=c['name'],request=fields,instruction_word=instruction,original_hcr=1<<31,adapted_hcr=0,captured_pstate=c['spsr'],adapted_pstate=c['spsr'],profile_state_supported=not unsupported,table_values=[q[f'value{i}'] for i in range(4)]))
 (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
 declaration="struct Case{name:&'static str,ttbr0:u64,ttbr1:u64,tcr:u64,sctlr:u64,mair:u64,pstate:u64,el:u32,pc:u64,va:u64,op:u32,width:u32,count:u32,granule:u32,second:u64,tables:[u64;4]}\n"
 (out/'cases.rs').write_text(declaration+'const CASES:&[Case]=&[\n'+',\n'.join(rows)+'\n];\n'+f'const TABLE_BASE:u64={base};const CODE_BASE:u64={code};const RAM_BASE:u64={data};\n')
 runner=Path(__file__).with_name('service_replay.rs');(out/'service_replay.rs').write_bytes(runner.read_bytes())
 commands=[]
 def run(cmd):
  r=subprocess.run(cmd,text=True,capture_output=True,timeout=180);commands.append(dict(command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');require(r.returncode==0,'command failed\n'+r.stdout+r.stderr);return r.stdout
 lib=out/'libnextcore_memory_service.rlib'
 run([a.rustc,'--edition=2021','--crate-type=rlib','--crate-name=nextcore_memory_service','-Copt-level=2',str(runtime/'memory-service/src/lib.rs'),'-o',str(lib)])
 run([a.rustc,'--edition=2021','-Copt-level=2',str(out/'service_replay.rs'),'--extern','nextcore_memory_service='+str(lib),'-o',str(out/'service_replay')])
 text=run([str(out/'service_replay')]);(out/'actual.tsv').write_text(text)
 keys=['result','fault','level','fsc','esr','address','value0','value1','ram_unchanged'];actual={}
 for line in text.splitlines():
  fields=line.split();require(len(fields)==10 and fields[0] not in actual,'service output shape');actual[fields[0]]=dict(zip(keys,map(int,fields[1:])))
 require(list(actual)==[c['name'] for c in report['cases']],'service case list')
 results=[compare(c,actual[c['name']],not i['profile_state_supported']) for c,i in zip(report['cases'],inputs)]
 negative=compare(report['cases'][0],actual[report['cases'][0]['name']],False,True)
 require(not negative['passed'] and [k for k,v in negative['checks'].items() if not v]==['esr'],'negative control')
 (out/'negative-control.json').write_text(json.dumps(dict(passed=False,expected_failure=True,change='first expected observed ESR xor1 only; actual execution unchanged',case=negative),indent=2)+'\n')
 after={f:sha(runtime/f) for f in RUNTIME_FILES}
 result=dict(schema='nextcore.captured-arm-stage1-service-comparison.v1',passed=all(c['passed'] for c in results) and before==after,oracle_kind=a.oracle_kind,oracle_case_count=required_count,exact_profile_comparisons=sum(i['profile_state_supported'] for i in inputs),captured_btype_profile_rejections=sum(not i['profile_state_supported'] for i in inputs),all_compared_cases_architectural_matches=all(i['profile_state_supported'] for i in inputs) and all(c['passed'] for c in results),source_preserved=before==after,source_sha256_before=before,source_sha256_after=after,oracle_sha256=frozen,control_metadata=dict(abi_version=2,struct_size=80,profile=1,epoch=1,scr=dict(captured=None,service=0,reason='Inactive service profile field; original EL2 fixture did not capture SCR_EL3. No equality asserted.')),tool_sha256={n:sha(out/n) for n in ['replay.py','service_replay.rs','source-freeze.json']},oracle_elf_sha256=sha(a.oracle_elf),hcr_adaptation=dict(captured=1<<31,service=0,reason='Only harness RW differs; VM/TGE/all other captured bits zero; service has no EL2.'),backing_provenance=dict(directly_captured='Upper table base/first entry/second page, TTBR/TCR/MAIR/SCTLR, VA/access/SPSR and printed instruction PC',reconstructed_from_authored_source='Original arrays zeroed; lower code table writes from C and ELF symbols; RET at data+0x230; STORE operands XZR/WZR.',elf_symbols={n:symbols[n] for n in ('tables','code','data')},ram_scope='Exact64KiB original data array; block cases fault before missing backing. No replacement mappings.'),native_jit_executed=False,physical_arm_executed=False,original_os_boot_verified=False,negative_control_detected=True,known_12_pc_priority_cases_excluded=True,original_a0_negative_excluded=True,cases=results)
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['passed','exact_profile_comparisons','captured_btype_profile_rejections','all_compared_cases_architectural_matches']}))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
