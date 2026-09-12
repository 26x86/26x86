from pathlib import Path
import subprocess, os, json, time
ROOT=Path('/home/sharh/work/bp35-integration')
OUT=Path('/home/sharh/work/module-validation-bp35-integrated-20260909')
OUT.mkdir(exist_ok=True)
MODULES=('Core','EFI','Tool','ISE','GPU','HAL','APLS')
env=os.environ.copy()
env['CARGO_NET_GIT_FETCH_WITH_CLI']='true'
env['CARGO_HTTP_MULTIPLEXING']='false'
env['GIT_TERMINAL_PROMPT']='0'
env['GIT_CONFIG_COUNT']=str(len(MODULES)+1)
for i,name in enumerate(MODULES):
    local=ROOT/'nextcore/crates'/('nextcore-'+name.lower())
    env[f'GIT_CONFIG_KEY_{i}']=f'url.file://{local}.insteadOf'
    env[f'GIT_CONFIG_VALUE_{i}']=f'https://github.com/26x86/Nextcore-{name}.git'
env[f'GIT_CONFIG_KEY_{len(MODULES)}']='protocol.file.allow'
env[f'GIT_CONFIG_VALUE_{len(MODULES)}']='always'

def run(name):
    source=ROOT/'nextcore/crates'/('nextcore-'+name.lower())
    sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip()
    clone=OUT/(name+'-'+sha[:10])
    log=OUT/(name+'.log')
    commands=[]
    with log.open('w') as stream:
      def command(args,cwd=clone):
        started=time.time()
        result=subprocess.run(args,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        commands.append({'command':args,'exit_code':result.returncode,'seconds':round(time.time()-started,2)})
        if result.returncode:raise RuntimeError(f'{name} failed; see {log}')
      if not clone.exists():
        command(['git','clone','--no-local',str(source),str(clone)],cwd=OUT)
      command(['git','checkout','--detach',sha])
      if name=='EFI':
        command(['cargo','build','--release','--target','x86_64-unknown-uefi','--features','arm-jit','--bin','NXARMJIT'])
        command(['cargo','build','--release','--target','x86_64-unknown-uefi','--features','arm-jit-probe','--bin','NXARMJIT'])
        command(['cargo','check','--target','x86_64-unknown-uefi','--all-features'])
      else:
        command(['cargo','test','--all-targets'])
        if name=='Core':command(['cargo','check','--no-default-features'])
        if name=='APLS':
          env['NEXTCORE_VSK_POLICY_ROOT']=str(ROOT/'sandbox/vsk')
          command(['cargo','test','--all-targets','--features','vulkan','--','--include-ignored'])
        if name=='GPU':command(['cargo','test','--all-targets','--features','vulkan'])
        if name=='ISE':
          command(['cargo','test','--manifest-path','runtime/preos/Cargo.toml'])
          command(['python3','tools/probe_efi_native_pauth.py'])
      metadata=subprocess.check_output(['cargo','metadata','--format-version','1','--filter-platform','x86_64-unknown-linux-gnu'],cwd=clone,env=env)
      packages=json.loads(metadata)['packages']
      module_packages=[{'name':v['name'],'source':v['source']} for v in packages if v['name'].startswith('nextcore-')]
      for package in packages:
        if package['name'].startswith('nextcore-') and package['name']!='nextcore-'+name.lower():
          assert package['source'] and package['source'].startswith('git+https://github.com/26x86/'),package
    receipt={'module':name,'commit':sha,'passed':True,'fresh_clone':True,'root_workspace_patches':False,'dependency_transport':'local committed objects via temporary Git URL mapping; remote publication not asserted','commands':commands,'nextcore_packages':module_packages}
    (OUT/(name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print(name,sha,'PASS',flush=True)

if __name__=='__main__':
    import sys
    for name in sys.argv[1:]:run(name)
