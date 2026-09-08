from pathlib import Path
import subprocess,json,os,time,shutil,hashlib,concurrent.futures
from validate_nextcore_modules_bp35 import ROOT,env
OUT=Path('/home/sharh/work/integration-validation-bp35-20260909');OUT.mkdir(exist_ok=False);CLONE=OUT/'26x86';records=[]
with (OUT/'setup.log').open('w') as log:subprocess.run(['git','clone','--no-local','--recurse-submodules',str(ROOT),str(CLONE)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run(['git','remote','set-url','origin','https://github.com/26x86/26x86.git'],cwd=CLONE,check=True)
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=CLONE,text=True).strip();assert sha==json.loads(Path('/home/sharh/work/publish-bp35-20260909/root-source.json').read_text())['commit']
normal=os.environ.copy();normal['CARGO_HTTP_MULTIPLEXING']='false'
def run(name,args):
 start=time.time()
 with (OUT/(name+'.log')).open('w') as log:p=subprocess.run(args,cwd=CLONE,env=normal,stdout=log,stderr=subprocess.STDOUT)
 records.append({'name':name,'command':args,'exit_code':p.returncode,'seconds':round(time.time()-start,2)});assert p.returncode==0,records[-1];print(name,'PASS',flush=True)
run('submodules',['python3','Tools/verify_nextcore_submodules.py','--cargo','--require-clean'])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(run,'workspace',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','--workspace']),pool.submit(run,'python',['/home/sharh/.venvs/nextcore/bin/python','-m','unittest','discover','-s','tests','-v'])]
 for future in futures:future.result()
run('core-no-default',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-core','--no-default-features'])
run('deep-cli-help',['python3','nextcore/tools/trace_deep_arm_jit_ovmf.py','--tools','nextcore/tools','--help'])
build=['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','--release','-p','nextcore-efi','--target','x86_64-unknown-uefi','--bin','NXARMJIT']
run('efi-tiered',build+['--features','arm-jit-memory-provider,arm-jit-tiered-trace']);binary=CLONE/'nextcore/target/x86_64-unknown-uefi/release/NXARMJIT.efi';tiered=OUT/'NXARMJIT-tiered.efi';shutil.copyfile(binary,tiered)
run('efi-deep',build+['--features','arm-jit-deep-trace']);deep=OUT/'NXARMJIT-deep.efi';shutil.copyfile(binary,deep)
clamped=Path('/home/sharh/work/bp35-canonical-deep-proof/clamped-efi/target/x86_64-unknown-uefi/release/NXARMJIT.efi')
run('deep-authored',['python3','nextcore/tools/verify_deep_budget_ovmf.py','--tools','nextcore/tools','--efi',str(deep),'--default-efi',str(tiered),'--clamped-efi',str(clamped),'--core-source','nextcore/crates/nextcore-core','--efi-source','nextcore/crates/nextcore-efi','--output',str(OUT/'deep-authored')])
run('debug-nxapfs',['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-efi','--target','x86_64-unknown-uefi','--all-features','--bin','NXAPFS'])
run('memory-service',['cargo','test','--manifest-path','nextcore/crates/nextcore-ise/runtime/memory-service/Cargo.toml'])
run('package-policy',['python3','tests/test_nextcore_package_policy.py','-v'])
run('clippy-host',['cargo','clippy','--locked','--manifest-path','nextcore/Cargo.toml','--workspace','--exclude','nextcore-efi','--all-targets'])
run('clippy-efi',['cargo','clippy','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-efi','--target','x86_64-unknown-uefi','--all-features'])
run('submodules-final',['python3','Tools/verify_nextcore_submodules.py','--cargo','--require-clean'])
assert not subprocess.check_output(['git','status','--porcelain'],cwd=CLONE)
proof=json.loads((OUT/'deep-authored/report.json').read_text());assert proof['passed'] and len(proof['cases'])==34
receipt={'schema':'nextcore.targeted-fresh-integration/1','passed':True,'integration_commit':sha,'recursive_modules':True,'working_tree_clean':True,'commands':records,'scope':'Targeted explicit-deep integration after BP34 full53-command suite; unchanged native/Arm/GPU suites are not relabeled as rerun here. Existing full CI remains.','actual_firmware_cases':5,'fresh_integrated_firmware_cases':4,'separately_compiled_canonical_clamp_cases':1,'cli_rejections':28,'receipt_only_negative':1,'clamp_sha256':hashlib.sha256(clamped.read_bytes()).hexdigest(),'clamp_source_provenance':'/home/sharh/work/bp35-canonical-deep-proof/mutation.json','clone_transport':'committed local repositories with temporary URL maps; canonical network publication separate'}
(OUT/'report.json').write_text(json.dumps(receipt,indent=2)+'\n');print('BP35 TARGETED INTEGRATION PASS',sha,len(records),flush=True)
