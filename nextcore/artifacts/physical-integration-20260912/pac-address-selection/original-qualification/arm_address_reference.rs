#![allow(dead_code)]
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
{let p=0x130u64;let t=0x540118010u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540118010u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540118010u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540118010u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540118010u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540118010u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540118010u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540118010u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540118010u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540118010u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540118010u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540118010u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540118010u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540118010u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540118010u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540118010u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540118010u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540118010u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540118010u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540118010u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540118010u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540118010u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540118010u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540118010u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540108011u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540108011u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540108011u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540108011u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540108011u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540108011u64;let k=0;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540108011u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540108011u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540108011u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540108011u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540108011u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540108011u64;let k=1;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540108011u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540108011u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540108011u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540108011u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540108011u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540108011u64;let k=2;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x130u64;let t=0x540108011u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x800000000130u64;let t=0x540108011u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff800000000130u64;let t=0x540108011u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xffff000000000130u64;let t=0x540108011u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0x80000000000130u64;let t=0x540108011u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
{let p=0xff7f800000000130u64;let t=0x540108011u64;let k=3;let v=arm_add(p,t,k,&s);println!("{:016x} {:016x} {:016x}",v,s.authenticate(v,0x9876,k,t).unwrap(),pauth::PauthState::strip(v,t).unwrap());}
}
