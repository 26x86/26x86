import pathlib,subprocess,hashlib,json,re
r=pathlib.Path('/mnt/c/Users/Admin/Documents/Codex/2026-09-12/git/work/26x86/nextcore/crates/nextcore-ise/runtime');o=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in r.rglob('*')if p.is_file()and p.suffix in('.rs','.c','.h','.inc')and'target'not in p.parts);before={str(p.relative_to(r)):sha(p)for p in files};commands=[]
def run(cmd,log):
 cmd=list(map(str,cmd));commands.append(cmd);p=subprocess.run(cmd,capture_output=True,timeout=180);(o/log).write_bytes(p.stdout+p.stderr);assert p.returncode==0,(log,p.stdout[-1000:],p.stderr[-1000:])
objects=[]
for name in ['jit','arch','boot_jit','memory_boot','memory_boot_v2','memory_layout','memory_layout_v2']:
 obj=o/(name+'.o');run(['clang-18','-std=c11','-D_GNU_SOURCE','-O2','-c',r/(name+'.c'),'-o',obj],name+'.log');objects.append(obj)
run(['clang-18','-std=c11','-D_GNU_SOURCE','-O2','-I',r,o/'direct.c',*objects,'-o',o/'direct'],'direct-build.log');run([o/'direct'],'direct.log')
# Scratch-only perturbation of the authored observer; canonical runtime unchanged.
snap=(r/'test_mapped_snapshot.c').read_text().replace('#include <string.h>','#include <string.h>\n#include <stdio.h>')
snap=snap.replace('cpu.pauth_step=pauth;','cpu.pauth_step=pauth;if(change_el==100)cpu.id_aa64isar1=0x123456789abcdef0ULL;')
snap=snap.replace('int status=vf_run_memory_provider_pauth_v2(', 'int status=(pauth?vf_run_memory_provider_pauth_v2:vf_run_memory_provider_v2)(')
snap=snap.replace('cpu.pauth_step=0;memcpy','uint64_t value=0;vf_cpu_read_sysreg(&cpu,0x4031,&value);printf("stored_isar1=%llx\\n",(unsigned long long)value);cpu.pauth_step=0;memcpy')
(o/'snapshot.c').write_text(snap);run(['clang-18','-std=c11','-D_GNU_SOURCE','-O2','-I',r,'-c',o/'snapshot.c','-o',o/'snapshot.o'],'snapshot-build.log');objects.append(o/'snapshot.o')
service=o/'libservice.rlib';run(['rustc','--edition=2021','--crate-name=nextcore_memory_service','--crate-type=rlib',r/'memory-service/src/lib.rs','-o',service],'service.log')
base=(r/'test_stage1_provider.rs').read_text();base=re.sub(r'#\[path="([^"]+)"\]',lambda m:'#[path='+json.dumps(str(r/m[1]))+']',base);base=base.replace(str(r/'test_mapped_provider.rs'),str(o/'mapped.rs'))
mapped=(r/'test_mapped_provider.rs').read_text();mapped=mapped.replace('"preos/src/pauth.rs"',json.dumps(str(r/'preos/src/pauth.rs')));(o/'mapped.rs').write_text(mapped+'\n'+(o/'mapped-extra.rs').read_text());(o/'provider.rs').write_text(base+'\n'+(o/'controls-extra.rs').read_text())
run(['rustc','--edition=2021','--test',o/'provider.rs','--extern','nextcore_memory_service='+str(service),'-o',o/'provider',*['-Clink-arg='+str(x)for x in objects]],'provider-build.log');run([o/'provider','matrix_','--nocapture','--test-threads=1'],'provider.log')
(o/'arch-reference.rs').write_text((r/'preos/src/arch.rs').read_text().split('#[cfg(test)]',1)[0]+'\n'+(o/'reference-extra.rs').read_text())
wrapper='\n'.join('#[path='+json.dumps(str(r/'preos/src'/(n+'.rs')))+']mod '+n+';'for n in ['mmu','pauth','exception_level','platform'])+'\n#[path="arch-reference.rs"]mod arch;';(o/'reference.rs').write_text(wrapper)
run(['rustc','--edition=2021','--test',o/'reference.rs','-o',o/'reference'],'reference-build.log');run([o/'reference','--nocapture','--test-threads=1'],'reference.log')
assert before=={str(p.relative_to(r)):sha(p)for p in files}
receipt=dict(completed=True,source_sha256=before,sources_preserved=True,commands=commands,logs={n:sha(o/n)for n in ['direct.log','provider.log','reference.log']},original_inputs_used=False,physical_boot_verified=False,scope='Observed path/profile matrix; not architectural conformance')
(o/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(o/'receipt.json')
