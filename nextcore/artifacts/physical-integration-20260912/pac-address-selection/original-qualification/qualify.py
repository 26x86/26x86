import pathlib,json,subprocess,hashlib
out=pathlib.Path('/tmp/nextcore-pac-frac-qualification-20260913-r1');m=json.loads((out/'manifest.json').read_text())
src=r'''#![allow(dead_code)]
mod pauth;
// Address-field placement oracle only: the cipher is the already checked runtime
// QARMA5 primitive, not an independent cipher implementation.
fn arm_add(p:u64,t:u64,k:usize,s:&pauth::PauthState)->u64 {
 let upper=p>>63!=0; let tsz=if upper {(t>>16)&63} else {t&63};
 let bottom=64-tsz; let mut canonical=p; let mut any=false;let mut all=true;
 for bit in bottom..64 {let set=p&(1<<bit)!=0;any|=set;all&=set;
  if upper {canonical|=1<<bit;}else{canonical&=!(1<<bit);}}
 let mut pac=pauth::qarma5(canonical,0x9876,s.keys[k]);
 if any&&!all {pac^=1<<62;}
 let mut result=p;
 for bit in bottom..64 {let set=if bit==55 {upper}else{pac&(1<<bit)!=0};
  if set {result|=1<<bit;}else{result&=!(1<<bit);}}
 result
}
fn main(){let mut s=pauth::PauthState::reset();
s.keys=[pauth::Key{lo:0x48ad369c24681357,hi:0xb752c963db97eca8};5];
'''
for r in m['rows']:
 src+=f'{{let p={r["pointer"]}u64;let t={r["tcr"]}u64;let k={r["key"]};let v=arm_add(p,t,k,&s);println!("{{:016x}} {{:016x}} {{:016x}}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}}\n'
src+='}\n';(out/'arm_address_reference.rs').write_text(src)
p=subprocess.run(['/home/developer/.cargo/bin/rustc','--edition=2021',str(out/'arm_address_reference.rs'),'-o',str(out/'arm_address_reference')],capture_output=True,timeout=30);(out/'arm-reference-build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
p=subprocess.run([str(out/'arm_address_reference')],capture_output=True,timeout=10);assert p.returncode==0;(out/'arm-address-results.txt').write_bytes(p.stdout)
curr=[[int(x,16) for x in l.split()] for l in (out/'rust-results.txt').read_text().splitlines()];ref=[[int(x,16) for x in l.split()] for l in p.stdout.decode().splitlines()]
diff=[dict(index=i,input=r,current_signed=hex(curr[i][0]),arm_address_reference_signed=hex(ref[i][0]),current_auth_signed=hex(curr[i][1]),arm_auth_signed=hex(ref[i][1])) for i,r in enumerate(m['rows']) if curr[i][0]!=ref[i][0]]
receipt=dict(scope='Address selection only; shared QARMA5 primitive. Not independent cipher oracle.',primary='Arm DDI0596 ID121321; physical PDF pages2944/2950/2955/2964',vectors=48,sign_mismatch_count=len(diff),mismatches=diff,production_changed=False)
(out/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
