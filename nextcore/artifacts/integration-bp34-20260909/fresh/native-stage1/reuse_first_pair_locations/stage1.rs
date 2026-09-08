//! Immutable Normal-NC stage-1 profile using the canonical preos walker.
use crate::abi::{FETCH,LOAD,STORE};
use crate::abi_v2::*;
use crate::exception_level::ExceptionLevel;
use crate::mmu::{Access,Fault,FaultContext,MemoryAttributes,TableReadError,
    TranslationFailure,TranslationFailureKind,VfMmu};
use core::ffi::c_void;
#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory-service/src/dynamic.rs"]pub mod dynamic;

#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Error {InvalidRange,InvalidControls}

pub fn controls_valid(c:&Controls)->bool {
    let allowed_tcr=0x3fu64|(1<<7)|(3<<14)|(0x3f<<16)|(1<<23)|(3<<30)|(7<<32);
    if c.abi_version!=VERSION || c.struct_size!=80 || c.profile!=PROFILE_FIXED_NC ||
        c.reserved!=0 || c.epoch!=1 || c.mair!=0x44 || c.hcr!=0 || c.scr!=0 ||
        c.sctlr&!0x18!=0x30d00803 || c.tcr&!allowed_tcr!=0 || (c.tcr>>32)&7>5 {return false;}
    let tg0=(c.tcr>>14)&3;let tg1=(c.tcr>>30)&3;
    let (min,max,alignment)=match (tg0,tg1) {(0,2)=>(16,39,0x1000),(2,1)=>(17,47,0x4000),_=>return false};
    let t0=c.tcr&63;let t1=(c.tcr>>16)&63;
    if !(min..=max).contains(&t0) || !(min..=max).contains(&t1) {return false;}
    let mask=0x0000ffffffffffffu64&!(alignment-1);
    c.ttbr0&!mask==0 && c.ttbr1&!mask==0
}

pub struct MemoryServiceV2<'a> {
    ram:&'a mut[u8],ram_base:u64,tables:&'a[u8],table_base:u64,
    controls:Controls,mmu:VfMmu,
}
fn overlaps(a:u64,n:u64,b:u64,m:u64)->bool {a<b+m && b<a+n}
fn offset(address:u64,width:usize,base:u64,length:usize)->Option<usize> {
    address.checked_sub(base).and_then(|x|usize::try_from(x).ok())
        .filter(|&x|width<=length && x<=length-width)
}
impl<'a> MemoryServiceV2<'a> {
    pub fn new(ram:&'a mut[u8],ram_base:u64,tables:&'a[u8],table_base:u64,controls:Controls)->Result<Self,Error> {
        if ram.len()<8 || tables.len()<8 || table_base&7!=0 || tables.len()&7!=0 ||
            ram_base.checked_add(ram.len() as u64).is_none() || table_base.checked_add(tables.len() as u64).is_none() ||
            overlaps(ram_base,ram.len() as u64,table_base,tables.len() as u64) {return Err(Error::InvalidRange);}
        // Safe Rust already prevents mutable aliasing; retain explicit checked
        // host span checks for callers constructing the borrowed slices via FFI.
        let rp=ram.as_ptr() as usize;let tp=tables.as_ptr() as usize;
        if rp.checked_add(ram.len()).is_none() || tp.checked_add(tables.len()).is_none() ||
            overlaps(rp as u64,ram.len() as u64,tp as u64,tables.len() as u64) {return Err(Error::InvalidRange);}
        if !controls_valid(&controls) {return Err(Error::InvalidControls);}
        let mut mmu=VfMmu::disabled();
        if !mmu.configure_strict_nc(controls.ttbr0,controls.ttbr1,controls.tcr) {return Err(Error::InvalidControls);}
        Ok(Self{ram,ram_base,tables,table_base,controls,mmu})
    }
    pub fn controls(&self)->Controls {self.controls}
    pub fn base(&self)->u64 {self.ram_base}
    pub fn size(&self)->u64 {self.ram.len() as u64}
    fn empty(&self,result:u32)->Reply {
        Reply{abi_version:VERSION,struct_size:128,result,level:NO_LEVEL,epoch:self.controls.epoch,..Reply::default()}
    }
    fn failure(&self,r:&Request,va:u64,error:TranslationFailure)->Reply {
        let mut out=self.empty(match error.kind {
            TranslationFailureKind::Architectural(_)=>GUEST_FAULT,
            TranslationFailureKind::TableRead(TableReadError::Unavailable)=>UNAVAILABLE,
            TranslationFailureKind::TableRead(TableReadError::ExternalAbort)|TranslationFailureKind::Unsupported=>UNSUPPORTED,
        });
        out.address=va;out.level=error.level.map(u32::from).unwrap_or(NO_LEVEL);
        out.context=match error.context {FaultContext::Input=>INPUT,FaultContext::Walk=>WALK,
            FaultContext::Leaf=>LEAF,FaultContext::CachedLeaf=>CACHED_LEAF};
        if let Some(pa)=error.descriptor_pa {out.descriptor_pa=pa;out.metadata_flags|=HAS_DESCRIPTOR;}
        if let Some(pa)=error.output_pa {out.output_pa=pa;out.metadata_flags|=HAS_OUTPUT;}
        if let TranslationFailureKind::Architectural(fault)=error.kind {
            let level=error.level.map(u32::from).unwrap_or(0);
            let (kind,fsc)=match fault {Fault::AddressSize=>(ADDRESS_SIZE,level),
                Fault::Translation=>(TRANSLATION,4+level),Fault::Permission=>(PERMISSION,12+level),
                Fault::AccessFlag=>(ACCESS_FLAG,8+level),Fault::Alignment=>(PC_ALIGNMENT,0)};
            out.fault=kind;out.fsc=fsc;
            out.esr=if kind==PC_ALIGNMENT {0x8a000000} else {
                let ec=if r.operation==FETCH {0x20+r.current_el} else {0x24+r.current_el};
                (u64::from(ec)<<26)|(1<<25)|u64::from(fsc)|if r.operation==STORE {64} else {0}
            };
        }
        out
    }
    fn request_valid(&self,r:&Request)->bool {
        let mode=r.pstate&15;
        if r.abi_version!=VERSION || r.struct_size!=160 || r.flags!=0 || r.reserved0!=0 || r.reserved1!=0 ||
            r.controls!=self.controls || !matches!(r.operation,FETCH|LOAD|STORE) ||
            !matches!(r.width,1|2|4|8) || !matches!(r.count,1|2) || (r.count==2 && r.width<4) ||
            (r.operation==FETCH && (r.width!=4 || r.count!=1 || r.address!=r.pc)) ||
            (r.operation!=STORE && (r.value0!=0 || r.value1!=0)) || (r.count==1 && r.value1!=0) ||
            r.pstate&!0xf00003cf!=0 || !((r.current_el==0 && mode==0) || (r.current_el==1 && (mode==4 || mode==5))) {
            return false;
        }
        let mask=if r.width==8 {u64::MAX} else {(1u64<<(r.width*8))-1};
        r.value0&!mask==0 && r.value1&!mask==0
    }
    pub fn execute(&mut self,r:&Request)->Reply {self.execute_counted(r,&mut 0)}
    fn execute_counted(&mut self,r:&Request,table_reads:&mut u64)->Reply {
        if !self.request_valid(r) {return self.empty(INVALID_REQUEST);}
        if r.address&(u64::from(r.width)-1)!=0 {
            let mut out=self.empty(GUEST_FAULT);out.address=r.address;out.context=INPUT;
            if r.operation==FETCH {out.fault=PC_ALIGNMENT;out.esr=0x8a000000;}
            else {out.fault=DATA_ALIGNMENT;out.fsc=0x21;
                out.esr=((0x24+u64::from(r.current_el))<<26)|(1<<25)|0x21|if r.operation==STORE {64} else {0};}
            return out;
        }
        let bytes=(r.width*r.count) as usize;
        if r.address.checked_add(bytes as u64-1).is_none() {
            let mut out=self.empty(UNSUPPORTED);out.address=r.address;return out;
        }
        let el=ExceptionLevel::from_u8(r.current_el as u8).unwrap();
        let access=match r.operation {FETCH=>Access::Execute,STORE=>Access::Write,_=>Access::Read};
        let mut places=[(false,0usize);16];
        for (byte,place) in places[..bytes].iter_mut().enumerate() {
            let va=r.address+byte as u64;
            let table_base=self.table_base;let tables=self.tables;
            // Instruction fetch alignment is checked once above. Translate
            // the aligned instruction start, then use its validated page span.
            let query=if r.operation==FETCH {r.address} else {va};
            let result=self.mmu.translate_detailed(query,access,el,|pa| {
                *table_reads=table_reads.saturating_add(1);
                let i=offset(pa,8,table_base,tables.len()).ok_or(TableReadError::Unavailable)?;
                Ok(u64::from_le_bytes(tables[i..i+8].try_into().unwrap()))
            });
            let translated=match result {Ok(value)=>value,Err(error)=>return self.failure(r,query,error)};
            if translated.attributes!=Some(MemoryAttributes{attr_index:0,shareability:0,mair:0x44}) {
                let mut out=self.empty(UNSUPPORTED);out.address=va;return out;
            }
            let pa=if r.operation==FETCH {translated.pa+byte as u64} else {translated.pa};
            if let Some(i)=offset(pa,1,self.ram_base,self.ram.len()) {*place=(false,i);}
            else if let Some(i)=offset(pa,1,self.table_base,self.tables.len()) {
                if r.operation==STORE {let mut out=self.empty(UNSUPPORTED);out.address=va;out.output_pa=pa;out.metadata_flags=HAS_OUTPUT;return out;}
                *place=(true,i);
            } else {
                let mut out=self.empty(UNAVAILABLE);out.address=va;out.output_pa=pa;out.metadata_flags=HAS_OUTPUT;return out;
            }
        }
        if r.count==2 { for byte in 0..r.width as usize { places[r.width as usize+byte]=places[byte]; } } let mut values=[0u64;2];
        for (byte,&(table,index)) in places[..bytes].iter().enumerate() {
            let element=byte/r.width as usize;let shift=(byte%r.width as usize)*8;
            if r.operation==STORE {
                let value=if element==0 {r.value0} else {r.value1};self.ram[index]=(value>>shift) as u8;
            } else {let value=if table {self.tables[index]} else {self.ram[index]};values[element]|=u64::from(value)<<shift;}
        }
        let mut out=self.empty(OK);out.value0=values[0];out.value1=values[1];out
    }
}

/// # Safety
/// Owner is one live, exclusively borrowed MemoryServiceV2; request and reply
/// are separate aligned complete records, disjoint from owner, RAM, tables and
/// executable buffers. No reentrancy, concurrent mutation or pointer retention.
#[no_mangle]
pub unsafe extern "C" fn vf_memory_service_step_v2(owner:*mut c_void,request:*const Request,reply:*mut Reply)->i32 {
    if owner.is_null() || request.is_null() || reply.is_null() ||
        (owner as usize)%core::mem::align_of::<MemoryServiceV2>()!=0 ||
        (request as usize)%core::mem::align_of::<Request>()!=0 ||
        (reply as usize)%core::mem::align_of::<Reply>()!=0 {return -1;}
    let request=unsafe{*request};
    let result=unsafe{(&mut *owner.cast::<MemoryServiceV2<'_>>()).execute(&request)};
    unsafe{reply.write(result)};0
}

#[cfg(test)]#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory-service/src/stage1_tests.rs"] mod tests;
