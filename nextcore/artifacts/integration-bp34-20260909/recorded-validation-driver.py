from pathlib import Path
import subprocess, json, os, sys, time, concurrent.futures
from validate_nextcore_modules_bp34 import ROOT, env
OUT=Path('/home/sharh/work/integration-validation-bp34-20260909')
OUT.mkdir(exist_ok=True)
CLONE=OUT/'26x86'
log=OUT/'setup.log'
with log.open('w') as stream:
 if not CLONE.exists():
  subprocess.run(['git','clone','--no-local','--recurse-submodules',str(ROOT),str(CLONE)],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['git','remote','set-url','origin','https://github.com/26x86/26x86.git'],cwd=CLONE,check=True)
print('Fresh recursive clone ready',flush=True)
records=[]
normal=os.environ.copy();normal['CARGO_HTTP_MULTIPLEXING']='false'
def run(name,args):
 started=time.time()
 with (OUT/(name+'.log')).open('w') as stream:
  result=subprocess.run(args,cwd=CLONE,env=normal,stdout=stream,stderr=subprocess.STDOUT)
 record={'name':name,'command':args,'exit_code':result.returncode,'seconds':round(time.time()-started,3)}
 records.append(record);print(name,result.returncode,flush=True)
 if result.returncode:raise RuntimeError(name+' failed')
run('submodules',['python3','Tools/verify_nextcore_submodules.py','--cargo','--require-clean'])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 futures=[
 pool.submit(run,'workspace',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','--workspace']),
 pool.submit(run,'python',['/home/sharh/.venvs/nextcore/bin/python','-m','unittest','discover','-s','tests','-v']),
 pool.submit(run,'native-pac',['python3','nextcore/tools/probe_efi_native_pauth.py','--output',str(OUT/'native-pac.json')]),
 ]
 for future in futures:future.result()
run('gui-boundaries',['/home/sharh/.venvs/nextcore/bin/python','-m','unittest','x86.gui.test_bridge_smoke','x86.gui.test_mellow_gui','-v'])
run('cli-utf8',['/home/sharh/.venvs/nextcore/bin/python','-X','utf8','-m','x86','--help'])
base=['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','--release','-p','nextcore-efi','--target','x86_64-unknown-uefi','--bin','NXARMJIT']
run('debug-nxapfs',['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-efi','--target','x86_64-unknown-uefi','--all-features','--bin','NXAPFS'])
run('efi-default',base+['--features','arm-jit'])
import shutil
binary=CLONE/'nextcore/target/x86_64-unknown-uefi/release/NXARMJIT.efi'
default=OUT/'NXARMJIT-default.efi';shutil.copyfile(binary,default)
run('efi-probe',base+['--features','arm-jit-probe,arm-jit-trace'])
probe=OUT/'NXARMJIT-probe.efi';shutil.copyfile(binary,probe)
run('firmware-nine',['python3','nextcore/tools/verify_arm_jit_ovmf.py','--efi-default',str(default),'--efi-probe',str(probe),'--output',str(OUT/'firmware-nine')])
run('firmware-prefix',['python3','nextcore/tools/verify_arm_sptm_prefix_ovmf.py','--efi-default',str(default),'--efi-trace',str(probe),'--output',str(OUT/'firmware-prefix')])
run('firmware-platform',['python3','nextcore/tools/verify_arm_platform_irq_ovmf.py','--efi',str(probe),'--output',str(OUT/'firmware-platform')])
run('firmware-pair',['python3','nextcore/artifacts/arm-pair-memory-20260909/verify_pair_ovmf.py','--tools','nextcore/tools','--efi',str(probe),'--output',str(OUT/'firmware-pair')])
run('firmware-scalar',['python3','nextcore/artifacts/arm-scalar-memory-20260909/verify_scalar_ovmf.py','--tools','nextcore/tools','--efi',str(probe),'--output',str(OUT/'firmware-scalar')])
run('efi-provider',base+['--features','arm-jit-memory-provider'])
provider=OUT/'NXARMJIT-provider.efi';shutil.copyfile(binary,provider)
run('efi-tiered',base+['--features','arm-jit-memory-provider,arm-jit-tiered-trace'])
tiered=OUT/'NXARMJIT-tiered.efi';shutil.copyfile(binary,tiered)
run('firmware-memory-provider',['python3','nextcore/tools/verify_arm_memory_provider_ovmf.py','--provider-efi',str(provider),'--direct-efi',str(probe),'--tiered-efi',str(tiered),'--output',str(OUT/'firmware-memory-provider')])
run('firmware-conditional',['python3','nextcore/tools/verify_arm_conditional_compare_ovmf.py','--efi',str(tiered),'--ise','nextcore/crates/nextcore-ise','--output',str(OUT/'firmware-conditional'),'--require-memory-provider'])
run('efi-stage1',['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','--release','-p','nextcore-efi','--target','x86_64-unknown-uefi','--features','arm-jit-stage1-probe','--bin','NXMMU'])
stage1=OUT/'NXMMU.efi';shutil.copyfile(CLONE/'nextcore/target/x86_64-unknown-uefi/release/NXMMU.efi',stage1)
run('stage1-runner',['python3','-m','unittest','discover','-s','nextcore/crates/nextcore-efi/tools','-p','test_stage1_reader.py','-v'])
run('firmware-stage1',['python3','nextcore/crates/nextcore-efi/tools/verify_stage1_ovmf.py','--efi-probe',str(stage1),'--output',str(OUT/'firmware-stage1')])
run('efi-dt',['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','--release','-p','nextcore-efi','--target','x86_64-unknown-uefi','--features','arm-jit-dt-probe','--bin','NXDT'])
dt=OUT/'NXDT.efi';shutil.copyfile(CLONE/'nextcore/target/x86_64-unknown-uefi/release/NXDT.efi',dt)
run('firmware-dt',['python3','nextcore/crates/nextcore-efi/tools/verify_dt_ledger_ovmf.py','--efi-probe',str(dt),'--output',str(OUT/'firmware-dt')])
run('dt-capture-check',['python3','nextcore/crates/nextcore-efi/tools/check_dt_ledger_capture.py','--report',str(OUT/'firmware-dt/report.json'),'--output',str(OUT/'dt-reader.json')])
run('native-dynamic',['python3','nextcore/crates/nextcore-ise/tools/probe_dynamic_memory.py','--work-dir',str(OUT/'native-dynamic'),'--output',str(OUT/'native-dynamic.json')])
run('efi-dynamic',['cargo','build','--locked','--manifest-path','nextcore/Cargo.toml','--release','-p','nextcore-efi','--target','x86_64-unknown-uefi','--features','arm-jit-dynamic-probe','--bin','NXDYN'])
dynamic=OUT/'NXDYN.efi';shutil.copyfile(CLONE/'nextcore/target/x86_64-unknown-uefi/release/NXDYN.efi',dynamic)
run('firmware-dynamic',['python3','nextcore/crates/nextcore-efi/tools/verify_dynamic_ovmf.py','--efi-probe',str(dynamic),'--output',str(OUT/'firmware-dynamic')])
run('dynamic-capture-check',['python3','nextcore/crates/nextcore-efi/tools/check_dynamic_capture.py','--report',str(OUT/'firmware-dynamic/report.json'),'--output',str(OUT/'dynamic-reader.json')])
run('captured-dynamic-comparison',['python3','-B','nextcore/artifacts/arm-dynamic-comparison-20260909/compare.py','--oracle','nextcore/artifacts/arm-dynamic-oracle-20260909','--runtime','nextcore/crates/nextcore-ise/runtime','--output',str(OUT/'captured-dynamic-comparison'),'--rustc',shutil.which('rustc')])
run('captured-dynamic-reader',['python3','-B','nextcore/artifacts/arm-dynamic-comparison-20260909/test_compare.py','--oracle','nextcore/artifacts/arm-dynamic-oracle-20260909','--evidence',str(OUT/'captured-dynamic-comparison')])
run('core-no-default',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-core','--no-default-features'])
run('core-doctests',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-core','--doc'])
run('native-stage1',['python3','nextcore/crates/nextcore-ise/tools/probe_efi_stage1_provider.py','--work-dir',str(OUT/'native-stage1'),'--output',str(OUT/'native-stage1.json')])
run('memory-service',['cargo','test','--manifest-path','nextcore/crates/nextcore-ise/runtime/memory-service/Cargo.toml'])
run('memory-service-uefi',['cargo','check','--manifest-path','nextcore/crates/nextcore-ise/runtime/memory-service/Cargo.toml','--target','x86_64-unknown-uefi'])
run('native-provider',['python3','nextcore/crates/nextcore-ise/tools/probe_efi_memory_provider.py','--work-dir',str(OUT/'native-provider'),'--output',str(OUT/'native-provider.json')])
run('pc-alignment',['python3','nextcore/crates/nextcore-ise/tools/probe_pc_alignment.py','--work-dir',str(OUT/'pc-alignment'),'--output',str(OUT/'pc-alignment.json')])
run('scalar-oracle',['python3','nextcore/crates/nextcore-ise/tools/probe_scalar_memory.py','--output',str(OUT/'scalar-oracle.json')])
run('architectural-reference',['cargo','test','--manifest-path','nextcore/crates/nextcore-ise/runtime/preos/Cargo.toml'])
run('exact-mmu-at',['python3','nextcore/crates/nextcore-ise/tools/mmu_fault_levels/probe_fault_levels.py','--output',str(OUT/'exact-mmu-at')])
run('exact-mmu-abort',['python3','nextcore/crates/nextcore-ise/tools/mmu_fault_levels/probe_abort_levels.py','--output',str(OUT/'exact-mmu-abort')])
run('exact-mmu-comparison',['python3','nextcore/crates/nextcore-ise/tools/mmu_fault_levels/compare_current_walker.py','--runtime-checkout','nextcore/crates/nextcore-ise','--at-report',str(OUT/'exact-mmu-at/report.json'),'--abort-report',str(OUT/'exact-mmu-abort/report.json'),'--output',str(OUT/'exact-mmu-comparison')])
run('conditional-oracle',['python3','nextcore/crates/nextcore-ise/tools/probe_conditional_compare.py','--work-dir',str(OUT/'conditional-oracle'),'--output',str(OUT/'conditional-oracle.json')])
run('pair-oracle',['python3','nextcore/crates/nextcore-ise/tools/probe_pair_memory.py','--output',str(OUT/'pair-oracle.json')])
run('vulkan',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-gpu','--all-targets','--features','vulkan'])
run('mmu-physical',['python3','nextcore/crates/nextcore-ise/tools/probe_mmu_physical.py','--output',str(OUT/'mmu-physical.json')])
normal['NEXTCORE_VSK_POLICY_ROOT']=str(CLONE/'sandbox/vsk')
run('vsk-policy',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-apls','--test','sgpu_grant','--','--include-ignored'])
run('mmu-oracle',['python3','nextcore/crates/nextcore-ise/tools/probe_mmu_granules.py','--output',str(OUT/'mmu-oracle.json')])
run('legacy-efi',['python3','sandbox/efi/build.py'])
normal['NEXTCORE_TEST_EFI']=str(default)
run('compiled-bundle',['cargo','test','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-tool','--test','bundle_cli','compiled_efi_is_copied_without_changes','--','--ignored','--nocapture'])
run('clippy-host',['cargo','clippy','--locked','--manifest-path','nextcore/Cargo.toml','--workspace','--exclude','nextcore-efi','--all-targets'])
run('clippy-efi',['cargo','clippy','--locked','--manifest-path','nextcore/Cargo.toml','-p','nextcore-efi','--target','x86_64-unknown-uefi','--all-features'])
run('submodules-final',['python3','Tools/verify_nextcore_submodules.py','--cargo','--require-clean'])
status=subprocess.check_output(['git','status','--porcelain'],cwd=CLONE).decode()
assert not status,status
receipt={'schema':'nextcore.fresh-integration/1','passed':True,'integration_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=CLONE).decode().strip(),'clone_transport':'local committed repositories with temporary Git URL mappings; remote publication not asserted','recursive_modules':True,'working_tree_clean':True,'commands':records}
(OUT/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('INTEGRATION PASS',flush=True)
