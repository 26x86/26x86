#![allow(dead_code)]
#[path="/tmp/nextcore-pac-frac-qualification-20260913-r1/pauth.rs"] mod pauth;
fn main(){
 let s=pauth::PauthState::reset();let base=0x540118010u64;let mut n=0;
 for t in [base|(1<<37),base|(1<<38),base|(1<<59),(base&!0x3f)|18,(base&!(0x3f<<16))|(18<<16)] {
  for p in [0x130u64,0xffff800000000130] {
   for k in 0..4 {
    let a=s.sign(p,0x9876,k,t);let b=s.authenticate(p,0x9876,k,t);let c=pauth::PauthState::strip(p,t);
    println!("tcr={t:016x} ptr={p:016x} key={k} sign={a:?} auth={b:?} strip={c:?}");n+=1;
   }
  }
 }
 assert!(s.sign(0x130,0,4,base).is_err());assert!(s.authenticate(0x130,0,4,base).is_err());
 println!("record_count={n} invalid_key_rejected=true");
}
