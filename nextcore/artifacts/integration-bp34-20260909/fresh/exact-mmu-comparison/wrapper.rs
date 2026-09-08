
use std::io::{self, BufRead};
// Both the exception-level type and walker are the canonical runtime source.
#[path = "/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/exception_level.rs"] mod exception_level;
#[path = "/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/mmu.rs"] mod mmu;
use mmu::{VfMmu,Access,TableReadError,TranslationFailureKind};
fn main() {
 for line in io::stdin().lock().lines() {
  let line=line.unwrap();let fields:Vec<_>=line.split_whitespace().collect();let name=fields[0];
  let n:Vec<u64>=fields[1..].iter().map(|s|u64::from_str_radix(s,16).unwrap()).collect();
  let mut mmu=VfMmu::disabled();
  if !mmu.configure_tcr(n[0],n[1],n[2],0) {println!("{} CONFIG_REJECTED",name);continue}
  let access=match n[4] {0=>Access::Read,1=>Access::Write,2=>Access::Execute,_=>panic!()};
  let mut reads=0u64;
  let result=mmu.translate_detailed(n[3],access,exception_level::ExceptionLevel::El1,|pa| {
   reads+=1;
   for i in 0..4 {let base=n[5+i*2];if pa>=base && pa<base+16384 && pa&7==0 {
       return Ok(if pa==base {n[6+i*2]} else {0});
   }}
   Err(TableReadError::Unavailable)
  });
  match result {
   Ok(t)=>println!("{} OK {:x} {}",name,t.pa,reads),
   Err(e)=>{
    let kind=match e.kind {TranslationFailureKind::Architectural(f)=>format!("{:?}",f),TranslationFailureKind::TableRead(t)=>format!("Provider{:?}",t),TranslationFailureKind::Unsupported=>"Unsupported".to_string()};
    println!("{} {} {} {:?} {} {} {}",name,kind,e.level.map_or("none".to_string(),|v|v.to_string()),e.context,
       e.descriptor_pa.map_or("none".to_string(),|v|format!("{:x}",v)),
       e.output_pa.map_or("none".to_string(),|v|format!("{:x}",v)),reads);
   }
  }
 }
}
