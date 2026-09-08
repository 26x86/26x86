//! External adapter; the canonical C JIT and Rust service execute original bytes.
use core::ffi::c_void;
use nextcore_memory_service::{abi_v2 as m,dynamic_abi as c,
    dynamic::{MemoryServiceDynamic,vf_memory_dynamic_step_v1,vf_memory_dynamic_control_v1}};
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/platform.rs"]mod platform;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory_boot.rs"]mod memory_boot;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory_boot_v2.rs"]mod memory_boot_v2;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory_dynamic.rs"]mod memory_dynamic;
use memory_dynamic::MemoryRunResultDynamic as Run;
type Protect=unsafe extern "C" fn(*mut c_void,usize,i32,*mut c_void)->i32;
unsafe extern "C" {
 fn mmap(p:*mut c_void,n:usize,prot:i32,flags:i32,fd:i32,off:isize)->*mut c_void;
 fn mprotect(p:*mut c_void,n:usize,prot:i32)->i32;
 fn munmap(p:*mut c_void,n:usize)->i32;
 fn run_captured(controls:*const m::Controls,base:u64,entry:u64,stack:u64,pstate:u64,data_va:u64,store:u64,
    code:*mut u8,bytes:usize,protect:Option<Protect>,memory:Option<m::Callback>,control:Option<c::Callback>,
    owner:*mut c_void,out:*mut Run,observed:*mut u64)->i32;
}
unsafe extern "C" fn protect(p:*mut c_void,n:usize,x:i32,_:*mut c_void)->i32{unsafe{mprotect(p,n,if x!=0{5}else{3})}}
struct Code(*mut u8);
impl Code{fn new()->Self{let p=unsafe{mmap(core::ptr::null_mut(),4096,3,0x22,-1,0)};assert_ne!(p as isize,-1);Self(p.cast())}}
impl Drop for Code{fn drop(&mut self){assert_eq!(unsafe{munmap(self.0.cast(),4096)},0);}}
struct Case{ name:&'static str,ram:&'static str,tables:&'static str,base:u64,table_base:u64,
    entry:u64,stack:u64,pstate:u64,data_va:u64,store:u64,controls:m::Controls}
include!("cases.rs");
struct Owner<'a>{service:MemoryServiceDynamic<'a>,events:Vec<String>}
unsafe extern "C" fn memory(owner:*mut c_void,q:*const m::Request,out:*mut m::Reply)->i32{
 let o=unsafe{&mut *owner.cast::<Owner<'_>>()};let q=unsafe{*q};
 let status=unsafe{vf_memory_dynamic_step_v1((&mut o.service as *mut MemoryServiceDynamic<'_>).cast(),&q,out)};
 let r=unsafe{*out};
 o.events.push(format!("DATA {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x}",
    q.operation,q.pc,q.address,q.width,q.count,q.controls.sctlr,q.controls.epoch,q.pstate,r.result,r.value0,r.fault,r.esr,r.address));status
}
unsafe extern "C" fn control(owner:*mut c_void,q:*const c::Request,out:*mut c::Reply)->i32{
 let o=unsafe{&mut *owner.cast::<Owner<'_>>()};let q=unsafe{*q};
 let status=unsafe{vf_memory_dynamic_control_v1((&mut o.service as *mut MemoryServiceDynamic<'_>).cast(),&q,out)};
 let r=unsafe{*out};
 o.events.push(format!("CONTROL {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x}",
    q.phase,q.operation,q.pc,q.selector,q.revision,q.epoch,r.result,r.state_tag,r.revision,r.epoch,r.architectural.sctlr,r.effective.sctlr));status
}
fn emit_snapshot(s:c::Snapshot){for v in [s.sctlr,s.ttbr0,s.ttbr1,s.tcr,s.mair,s.hcr,s.scr,s.reserved]{print!(" {:x}",v)}}
fn main(){
 let outdir=std::env::args().nth(1).expect("output directory");
 for case in cases(){
  let mut ram=std::fs::read(case.ram).unwrap();let tables=std::fs::read(case.tables).unwrap();let code=Code::new();
  let mut owner=Owner{service:MemoryServiceDynamic::new(&mut ram,case.base,&tables,case.table_base,case.controls).unwrap(),events:vec![]};
  let mut out=Run::default();let mut observed=[0u64;48];
  let status=unsafe{run_captured(&case.controls,case.base,case.entry,case.stack,case.pstate,case.data_va,case.store,
      code.0,4096,Some(protect),Some(memory),Some(control),(&mut owner as *mut Owner<'_>).cast(),&mut out,observed.as_mut_ptr())};
  print!("CPU {}",case.name);for v in observed{print!(" {:x}",v)}println!();
  let b=out.memory.base;print!("RESULT {}",case.name);
  for v in [status as u64,b.abi_version as u64,b.struct_size as u64,b.provider_status as u64,
    b.fetch_requests,b.data_requests,b.completed_data_operations,b.last_address,b.guest_far,
    out.memory.last_reply.result as u64,out.memory.last_reply.fault as u64,out.memory.last_reply.fsc as u64,
    out.memory.last_reply.level as u64,out.memory.last_reply.address,out.memory.last_reply.esr,out.memory.last_reply.value0,
    out.final_control.state_tag as u64,out.final_control.revision,out.final_control.epoch,out.final_control.invalidations,
    owner.service.table_reads()]{print!(" {:x}",v)}println!();
  print!("STATE {}",case.name);emit_snapshot(out.final_control.architectural);emit_snapshot(out.final_control.effective);println!();
  assert_eq!(out.final_control,owner.service.final_state());
  std::fs::write(format!("{outdir}/{}.events",case.name),owner.events.join("\n")+"\n").unwrap();
  drop(owner);
  std::fs::write(format!("{outdir}/{}.ram-after.bin",case.name),&ram).unwrap();
 }
}
