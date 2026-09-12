#!/usr/bin/env python3
"""Independent immutable hierarchical permissions and cache proof."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',type=Path);p.add_argument('--expect-old-rejection',action='store_true');p.add_argument('--arm-receipt',type=Path);a=p.parse_args()
 tests=Path(__file__).resolve().parents[1];root=(a.runtime or tests).resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 files=[p for p in root.rglob('*') if p.is_file() and p.suffix in ('.c','.h','.inc','.rs','.py') and 'target' not in p.parts];before={str(p.relative_to(root)):sha(p) for p in files};commands=[]
 src=out/'source';shutil.copytree(root,src,ignore=shutil.ignore_patterns('target','__pycache__'))
 # Canonical sources are copied verbatim; test modules are appended below.
 for n in ['test_hierarchy_provider.rs','test_hierarchy_reference.rs']:shutil.copyfile(tests/n,src/n)
 provider=src/'test_stage1_provider.rs';provider.write_text(provider.read_text()+'\n'+(src/'test_hierarchy_provider.rs').read_text())
 arch=src/'preos/src/arch.rs';arch.write_text(arch.read_text()+'\n'+(src/'test_hierarchy_reference.rs').read_text())
 def run(cmd,log,allow=False,env=None):
  cmd=list(map(str,cmd));commands.append(cmd);z=subprocess.run(cmd,capture_output=True,timeout=180,env=env);(out/log).write_bytes(z.stdout+z.stderr)
  if not allow:assert z.returncode==0,(log,z.stderr[-1600:],z.stdout[-1600:])
  return z
 service=out/'libservice.rlib';run(['rustc','--edition=2021','--crate-name=nextcore_memory_service','--crate-type=rlib','-Copt-level=2',src/'memory-service/src/lib.rs','-o',service],'service.log')
 objects=[]
 for n in ['jit','arch','boot_jit','memory_boot','memory_boot_v2','memory_layout','memory_layout_v2']:
  obj=out/(n+'.o');run(['clang-18','-std=c11','-D_GNU_SOURCE','-O2','-Wall','-Wextra','-Werror','-c',src/(n+'.c'),'-o',obj],n+'.log');objects.append(obj)
 counts={}
 for mode,flags in [('cached',[]),('uncached',['-DNEXTCORE_DISABLE_PROVIDER_CACHE']),('small-slot',['-DNEXTCORE_PROVIDER_CACHE_SLOT_BYTES=64'])]:
  if a.expect_old_rejection and mode!='cached':break
  linked=objects[:]
  if flags:
   obj=out/(mode+'.o');run(['clang-18','-std=c11','-D_GNU_SOURCE','-O2',*flags,'-c',src/'jit.c','-o',obj],mode+'-compile.log');linked[0]=obj
  exe=out/mode;run(['rustc','--edition=2021','--test','-Copt-level=2',provider,'--extern','nextcore_memory_service='+str(service),'-o',exe,*['-Clink-arg='+str(x) for x in linked]],mode+'-build.log')
  cmd=[exe,'--test-threads=1'];
  if a.expect_old_rejection:cmd+=['hierarchy_complete_permissions_cold_warm_both_regimes']
  z=run(cmd,mode+'.log',a.expect_old_rejection,{**os.environ,'NEXTCORE_HIERARCHY_SNAPSHOT':str(out/(mode+'.snapshot'))})
  if a.expect_old_rejection:
   assert z.returncode!=0 and b'hierarchy_complete_permissions_cold_warm_both_regimes' in z.stdout
  else:counts[mode]=int(re.search(rb'test result: ok. (\d+) passed',z.stdout)[1])
 if not a.expect_old_rejection:
  for mode in ['uncached','small-slot']:
   for suffix in ['.snapshot','.snapshot.data','.snapshot.matrix']:assert (out/(mode+suffix)).read_bytes()==(out/('cached'+suffix)).read_bytes()
  wrapper=out/'reference.rs';wrapper.write_text('\n'.join('#[path='+json.dumps(str(src/'preos/src'/(n+'.rs')))+']mod '+n+';' for n in ['mmu','pauth','exception_level','platform','arch','m1']))
  run(['rustc','--edition=2021','--test','-Copt-level=2',wrapper,'-o',out/'reference'],'reference-build.log');z=run([out/'reference','--test-threads=1'],'reference.log');counts['reference']=int(re.search(rb'test result: ok. (\d+) passed',z.stdout)[1])
 if not a.expect_old_rejection:
  mutants={};mmu=src/'preos/src/mmu.rs';original=mmu.read_text()
  replacements={'ignored-hierarchy':('table_permissions |= descriptor & hierarchy_mask;','table_permissions |= 0;'),'leaf-only-implicit-xn':('Self::privileged_execution(current_el,executable_privileged,writable,user_accessible)','Self::privileged_execution(current_el,executable_privileged,ap == 0 || ap == 1,ap == 1 || ap == 3)')}
  for name,(needle,replacement) in replacements.items():
   assert needle in original;mmu.write_text(original.replace(needle,replacement,1))
   library=out/('lib'+name+'.rlib');run(['rustc','--edition=2021','--crate-name=nextcore_memory_service','--crate-type=rlib','-Copt-level=2',src/'memory-service/src/lib.rs','-o',library],name+'-service.log')
   exe=out/name;run(['rustc','--edition=2021','--test','-Copt-level=2',provider,'--extern','nextcore_memory_service='+str(library),'-o',exe,*['-Clink-arg='+str(x) for x in objects]],name+'-build.log')
   z=run([exe,'hierarchy_complete_permissions_cold_warm_both_regimes','--test-threads=1'],name+'.log',True);assert z.returncode!=0 and b'assertion' in z.stdout;mutants[name]='rejected by independent permission matrix'
   mmu.write_text(original)
  (out/'mutants.json').write_text(json.dumps(mutants,indent=2)+'\n')
 assert before=={str(p.relative_to(root)):sha(p) for p in files}
 arm_comparison=None
 if a.arm_receipt and not a.expect_old_rejection:
  arm=json.loads(a.arm_receipt.read_text());assert arm["passed"] and arm["sources_preserved"]
  matrix={}
  for line in (out/"cached.snapshot.matrix").read_text().splitlines():
   v=list(map(int,line.split(",")));key=tuple(v[:7]);val=tuple(v[7:]);assert key not in matrix or matrix[key]==val;matrix[key]=val
  joined=[]
  for group in arm["results"]:
   for row in group["rows"]:
    kind=row["kind"]
    if kind not in (0,1,2,3,4,9,10):continue
    ancestor=0 if kind==9 else 1 if kind==10 else 2
    xn={1:4,2:8,3:1,4:2}.get(kind,0)
    key=(group["granule"],ancestor,row["leaf_ap"],row["parent_ap"],xn,row["el"],{"fetch":1,"read":2,"write":3}[row["access"]])
    result,fault,esr=matrix[key];assert (result==0)==row["success"],(key,result,row)
    if result:assert fault==5 and esr==int(row["esr"],16),(key,esr,row)
    joined.append(dict(key=key,success=result==0,esr=esr))
  arm_comparison=dict(rows=len(joined),receipt_sha256=sha(a.arm_receipt),receipt=str(a.arm_receipt),scope="Canonical immutable service replies compared directly with actual Arm AP/XN rows; different VAs/PAs and CPU models are not equated")
  (out/"arm-comparison.json").write_text(json.dumps(dict(summary=arm_comparison,rows=joined),indent=2)+"\n")
 receipt=dict(arm_comparison=arm_comparison,passed=True,expected_baseline_rejected=a.expect_old_rejection,tests=counts,source_sha256=before,sources_preserved=True,commands=commands,oracle_scope='Explicit independent permission matrix; canonical walker is the implementation under test',original_images_used=False,physical_boot_verified=False)
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['source_sha256','commands']}))
if __name__=='__main__':main()
