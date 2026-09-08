//! Caller-owned, allocation-free physical and stage-1 services for the x86 EFI JIT.
//! The mapped profiles share the canonical walker; no panic handler, executable
//! buffer, copied walker, or host-pointer reply is introduced.
#![no_std]
#[cfg(test)] extern crate std;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory-service/src/abi.rs"] pub mod abi;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory-service/src/abi_v2.rs"] pub mod abi_v2;
pub mod stage1;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory-service/src/dynamic_abi.rs"] pub mod dynamic_abi;
pub use stage1::dynamic;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/exception_level.rs"] mod exception_level;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/mmu.rs"] mod mmu;
use abi::*;
use core::ffi::c_void;

pub struct MemoryService<'a> {ram:&'a mut[u8],base:u64}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Error {InvalidRange}
impl<'a> MemoryService<'a> {
    pub fn new(ram:&'a mut[u8],base:u64)->Result<Self,Error> {
        if ram.len()<8 || base.checked_add(ram.len() as u64).is_none() {return Err(Error::InvalidRange);}
        Ok(Self{ram,base})
    }
    pub fn base(&self)->u64 {self.base}
    pub fn size(&self)->u64 {self.ram.len() as u64}
    pub fn execute(&mut self,r:&Request)->Reply {
        let mut out=Reply{abi_version:ABI_VERSION,struct_size:80,result:INVALID_REQUEST,..Reply::default()};
        if r.abi_version!=ABI_VERSION || r.struct_size!=80 || r.flags!=0 || r.reserved!=0 || r.epoch!=0 ||
            !matches!(r.operation,FETCH|LOAD|STORE) || !matches!(r.width,1|2|4|8) || !matches!(r.count,1|2) ||
            (r.count==2 && !matches!(r.width,4|8)) ||
            (r.operation==FETCH && (r.width!=4 || r.count!=1 || r.address!=r.pc)) ||
            (r.operation!=STORE && (r.value0!=0 || r.value1!=0)) ||
            (r.count==1 && r.value1!=0) {return out;}
        let mask=if r.width==8 {u64::MAX} else {(1u64<<(r.width*8))-1};
        if r.value0&!mask!=0 || r.value1&!mask!=0 {return out;}
        if r.current_el>1 || r.sctlr&1!=0 ||
            r.sctlr&(1u64<<if r.current_el==0 {24} else {25})!=0 {
            out.result=UNSUPPORTED;out.address=r.address;return out;
        }
        if r.address&u64::from(r.width-1)!=0 {
            out.result=GUEST_FAULT;out.address=r.address;
            if r.operation==FETCH {out.fault=PC_ALIGNMENT;out.esr=0x8a000000;}
            else {out.fault=DATA_ALIGNMENT;
                out.esr=((0x24+u64::from(r.current_el))<<26)|(1<<25)|0x21|
                    if r.operation==STORE {64} else {0};}
            return out;
        }
        let mut offsets=[0usize;2];
        for element in 0..r.count as usize {
            let address=r.address.wrapping_add(element as u64*u64::from(r.width));
            let offset=r.address.checked_add(element as u64*u64::from(r.width))
                .and_then(|pa|pa.checked_sub(self.base)).and_then(|v|usize::try_from(v).ok())
                .filter(|offset|self.ram.len()>=r.width as usize && *offset<=self.ram.len()-r.width as usize);
            let Some(offset)=offset else {out.result=UNSUPPORTED;out.address=address;return out;};
            offsets[element]=offset;
        }
        // Every element is preflighted before any transfer, including stores.
        let mut values=[0u64;2];
        for element in 0..r.count as usize {
            let at=offsets[element];
            if r.operation==STORE {
                let value=if element==0 {r.value0} else {r.value1};
                for byte in 0..r.width as usize {self.ram[at+byte]=(value>>(byte*8)) as u8;}
            } else {
                for byte in 0..r.width as usize {values[element]|=u64::from(self.ram[at+byte])<<(byte*8);}
            }
        }
        out.result=OK;out.value0=values[0];out.value1=values[1];out
    }
}

/// # Safety
/// Host supplies a live, uniquely borrowed MemoryService owner and separate
/// aligned full request/reply records. None overlaps RAM/code or each other.
/// These objects remain valid and cannot be reentered until the call returns.
#[no_mangle]
pub unsafe extern "C" fn vf_memory_service_step(owner:*mut c_void,request:*const Request,reply:*mut Reply)->i32 {
    if owner.is_null() || request.is_null() || reply.is_null() ||
        (owner as usize)%core::mem::align_of::<MemoryService>()!=0 ||
        (request as usize)%core::mem::align_of::<Request>()!=0 ||
        (reply as usize)%core::mem::align_of::<Reply>()!=0 {return -1;}
    let request=unsafe{*request};
    let result=unsafe{(&mut *owner.cast::<MemoryService<'_>>()).execute(&request)};
    unsafe{reply.write(result)};0
}

#[cfg(test)]
mod tests {
    use super::*;
    fn request(op:u32,width:u32,count:u32,address:u64)->Request {
        Request{abi_version:1,struct_size:80,operation:op,width,count,address,pc:address,current_el:1,..Request::default()}
    }
    #[test]
    fn all_widths_and_counts_preflight_and_transfer_raw_elements() {
        for width in [1u32,2,4,8] {for count in 1..=2 {if count==2 && width<4 {continue;}
            let mut ram=[0xa5;64];let mut service=MemoryService::new(&mut ram,0x4000).unwrap();
            let mask=if width==8 {u64::MAX} else {(1u64<<(width*8))-1};
            let mut store=request(STORE,width,count,0x4010);store.value0=0xfedcba9876543280&mask;
            store.value1=if count==2 {0x89abcdef&mask} else {0};
            assert_eq!(service.execute(&store).result,OK);
            let read=service.execute(&request(LOAD,width,count,0x4010));
            assert_eq!((read.result,read.value0,read.value1),(OK,store.value0,store.value1));
        }}
    }
    #[test]
    fn rejected_pair_never_partially_writes_the_first_element() {
        for width in [4u32,8] {
            let mut ram=[0xa5;64];let before=ram;
            let mut r=request(STORE,width,2,0x4000+64-u64::from(width));r.value0=0x42;r.value1=0x43;
            let out=MemoryService::new(&mut ram,0x4000).unwrap().execute(&r);
            assert_eq!((out.result,out.address,out.esr),(UNSUPPORTED,0x4040,0));assert_eq!(ram,before);
        }
    }
    #[test]
    fn malformed_requests_are_rejected_without_effects() {
        for kind in 0..14 {
            let mut ram=[0xa5;64];let before=ram;let mut r=request(STORE,4,1,0x4010);
            match kind {0=>r.abi_version=2,1=>r.struct_size=79,2=>r.flags=1,3=>r.epoch=1,4=>r.reserved=1,
                5=>r.operation=0,6=>r.width=3,7=>r.count=3,8=>{r.count=2;r.width=1},
                9=>r.value0=1<<32,10=>r.value1=1,11=>{r.operation=LOAD;r.value0=1},
                12=>{r.operation=FETCH;r.address+=4},_=>{r.operation=FETCH;r.width=8}}
            let out=MemoryService::new(&mut ram,0x4000).unwrap().execute(&r);
            assert_eq!((out.result,out.fault,out.address,out.esr),(INVALID_REQUEST,0,0,0));assert_eq!(ram,before);
        }
    }
    #[test]
    fn device_alignment_and_pc_alignment_have_exact_syndromes() {
        for el in 0..2 {for a in [0,2] {for op in [FETCH,LOAD,STORE] {
            let mut ram=[0xa5;64];let before=ram;let mut r=request(op,4,1,0x4001);r.current_el=el;r.sctlr=a;
            let out=MemoryService::new(&mut ram,0x4000).unwrap().execute(&r);
            let esr=if op==FETCH {0x8a000000} else {((0x24+u64::from(el))<<26)|(1<<25)|0x21|if op==STORE {64} else {0}};
            assert_eq!((out.result,out.address,out.esr),(GUEST_FAULT,0x4001,esr));assert_eq!(ram,before);
        }}}
    }
    #[test]
    fn unsupported_modes_and_backing_do_not_invent_guest_faults() {
        for kind in 0..5 {
            let mut ram=[0xa5;64];let before=ram;let mut r=request(STORE,8,1,0x4010);
            match kind {0=>r.sctlr=1,1=>r.current_el=2,2=>r.sctlr=1<<25,3=>r.address=0x4040,_=>r.address=0x3ff8}
            let out=MemoryService::new(&mut ram,0x4000).unwrap().execute(&r);
            assert_eq!((out.result,out.fault,out.esr),(UNSUPPORTED,0,0));assert_eq!(out.address,r.address);assert_eq!(ram,before);
        }
        let mut short=[0;7];assert!(MemoryService::new(&mut short,0).is_err());
        let mut ram=[0;8];assert!(MemoryService::new(&mut ram,u64::MAX-7).is_err());
    }
}
