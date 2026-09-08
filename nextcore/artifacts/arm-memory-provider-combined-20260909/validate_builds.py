from pathlib import Path
import subprocess,os,json,hashlib,shutil
p=Path(__file__).resolve().parent;efi=p/'efi';env=os.environ.copy();env['PATH']='/home/sharh/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:'+env['PATH'];env['CARGO_HOME']=str(p/'cargo-home');env['CARGO_TARGET_DIR']=str(p/'target');env['CARGO_NET_GIT_FETCH_WITH_CLI']='true'
for key in ['NEXTCORE_PREOS_RUNTIME','RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS']:env.pop(key,None)
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
files=[efi/f for f in subprocess.check_output(['git','-C',str(efi),'ls-files'],text=True).splitlines()];before={str(f.relative_to(efi)):digest(f) for f in files};records=[];passed=False
cases=[('default',[]),('direct',['--bin','NXARMJIT','--features','arm-jit-trace,arm-jit-probe']),('provider',['--bin','NXARMJIT','--features','arm-jit-memory-provider']),('combined',['--bin','NXARMJIT','--features','arm-jit-memory-provider,arm-jit-tiered-trace']),('all-features',['--all-features'])]
try:
 for name,features in cases:
  cmd=['cargo','build','--offline','--locked','--release','--target','x86_64-unknown-uefi']+features
  r=subprocess.run(cmd,cwd=efi,env=env,text=True,capture_output=True);(p/('build-'+name+'.log')).write_text(r.stdout+r.stderr);record={'name':name,'command':cmd,'returncode':r.returncode};records.append(record)
  if r.returncode:print(r.stdout+r.stderr,flush=True);raise RuntimeError('build failed: '+name)
  directory=p/'binaries'/name;directory.mkdir(parents=True)
  names=['BOOTX64','NXKERNEL'] if name=='default' else ['NXARMJIT']
  if name=='all-features':names=[f.stem for f in (p/'target/x86_64-unknown-uefi/release').glob('*.efi')]
  record['binaries']={}
  for binary in names:
   source=p/'target/x86_64-unknown-uefi/release'/(binary+'.efi');target=directory/source.name;shutil.copyfile(source,target);record['binaries'][binary]={'path':str(target),'sha256':digest(target)}
  print(json.dumps(record),flush=True)
 passed=True
finally:
 after={str(f.relative_to(efi)):digest(f) for f in files};result={'schema':'nextcore.combined-efi-standalone-build.v1','passed':passed and before==after,'source_commit':subprocess.check_output(['git','-C',str(efi),'rev-parse','HEAD'],text=True).strip(),'parent_workspace_used':False,'path_patches_used':False,'runtime_override_used':False,'records':records,'source_sha256_before':before,'source_sha256_after':after};(p/'build-results.json').write_text(json.dumps(result,indent=2)+'\n')
