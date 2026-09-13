import pathlib,json,hashlib,subprocess
out=pathlib.Path('/tmp/nextcore-pac-frac-qualification-20260913-r1');out.mkdir(exist_ok=True)
src=pathlib.Path('/mnt/c/Users/Admin/Documents/Codex/2026-09-12/git/work/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/pauth.rs')
(out/'pauth.rs').write_bytes(src.read_bytes())
ptrs=[0x130,0x0000800000000130,0xffff800000000130,0xffff000000000130,0x0080000000000130,0xff7f800000000130]
rows=[]
for t0,t1 in [(16,17),(17,16)]:
 for k in range(4):
  for p in ptrs: rows.append(dict(t0sz=t0,t1sz=t1,tcr=hex((5<<32)|(1<<30)|(2<<14)|(t1<<16)|t0),key=k,pointer=hex(p),modifier='0x9876'))
manifest=dict(key_lo='0x48ad369c24681357',key_hi='0xb752c963db97eca8',rows=rows,header=['CurrentEL','ISAR1','ISAR2','vector_count'],record=['TCR','SCTLR','signed','auth_signed','xpac_original','xpac_signed','auth_corrupted_bit54','auth_original'],sctlr=hex(0x30d00800|(1<<31)|(1<<30)|(1<<27)|(1<<13)))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def mov(r,v):return [f'movz {r}, #{v&65535}']+[f'movk {r}, #{(v>>n)&65535}, lsl #{n}' for n in [16,32,48]]
asm=['.arch armv8.3-a','.text','.global _start','_start:']+mov('x18',0x40100000)+['mrs x19, CurrentEL','str x19,[x18],#8','mrs x19, ID_AA64ISAR1_EL1','str x19,[x18],#8','mrs x19, S3_0_C0_C6_2','str x19,[x18],#8','mov x19,#48','str x19,[x18],#8','adr x19,vectors','msr VBAR_EL1,x19','isb']
for name in ['APIA','APIB','APDA','APDB']:
 asm+=mov('x10',int(manifest['key_lo'],16))+mov('x11',int(manifest['key_hi'],16))+[f'msr {name}KeyLo_EL1,x10',f'msr {name}KeyHi_EL1,x11']
for row in rows:
 k=row['key'];pac=['pacia','pacib','pacda','pacdb'][k];aut=['autia','autib','autda','autdb'][k];xp='xpaci' if k<2 else 'xpacd'
 asm+=mov('x10',int(row['tcr'],16))+['msr TCR_EL1,x10']+mov('x10',int(manifest['sctlr'],16))+['msr SCTLR_EL1,x10','isb','mrs x19,TCR_EL1','str x19,[x18],#8','mrs x19,SCTLR_EL1','str x19,[x18],#8']+mov('x1',int(row['pointer'],16))+mov('x2',0x9876)+['mov x3,x1',f'{pac} x3,x2','str x3,[x18],#8','mov x4,x3',f'{aut} x4,x2','str x4,[x18],#8','mov x4,x1',f'{xp} x4','str x4,[x18],#8','mov x4,x3',f'{xp} x4','str x4,[x18],#8','eor x4,x3,#0x0040000000000000',f'{aut} x4,x2','str x4,[x18],#8','mov x4,x1',f'{aut} x4,x2','str x4,[x18],#8']
asm+=['mov x0,#0x64e','done: b done','.balign 2048','vectors:']
for i in range(16):asm+=['b trapped','.space 124']
asm+=['trapped:','mrs x20,ESR_EL1','mrs x21,ELR_EL1','mov x0,#0xbad','failed: b failed']
(out/'probe.S').write_text('\n'.join(asm)+'\n')
rust=['#![allow(dead_code)]','mod pauth;','fn main(){','let mut s=pauth::PauthState::reset();','s.keys=[pauth::Key{lo:0x48ad369c24681357,hi:0xb752c963db97eca8};5];']
for row in rows:
 p=row['pointer'];t=row['tcr'];k=row['key']
 rust+=[f'{{let p={p}u64;let t={t}u64;let k={k};let a=s.sign(p,0x9876,k,t).unwrap(); println!("{{:016x}} {{:016x}} {{:016x}} {{:016x}} {{:016x}} {{:016x}}",a,s.authenticate(a,0x9876,k,t).unwrap(),pauth::PauthState::strip(p,t).unwrap(),pauth::PauthState::strip(a,t).unwrap(),s.authenticate(a^(1<<54),0x9876,k,t).unwrap(),s.authenticate(p,0x9876,k,t).unwrap());}}']
rust+=['}'];(out/'rust_probe.rs').write_text('\n'.join(rust)+'\n')
p=subprocess.run(['/home/developer/.cargo/bin/rustc','--edition=2021',str(out/'rust_probe.rs'),'-o',str(out/'rust_probe')],capture_output=True,timeout=30);(out/'rust-build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
p=subprocess.run([str(out/'rust_probe')],capture_output=True,timeout=10);assert p.returncode==0;(out/'rust-results.txt').write_bytes(p.stdout)
assert src.read_bytes()==(out/'pauth.rs').read_bytes()
print(json.dumps({'rows':len(rows),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'assembly_sha256':hashlib.sha256((out/'probe.S').read_bytes()).hexdigest()}))
