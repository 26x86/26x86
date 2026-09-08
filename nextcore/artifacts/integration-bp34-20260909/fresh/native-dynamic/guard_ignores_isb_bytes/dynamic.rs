//! Transactional control owner; reuses the parent's backing and canonical walker.
use super::{controls_valid,offset,Error,MemoryServiceV2};
use crate::abi::{FETCH,STORE};
use crate::abi_v2 as m;
use crate::dynamic_abi as c;
use crate::exception_level::ExceptionLevel;
use crate::mmu::{Access,MemoryAttributes,TableReadError,TranslationFailureKind,VfMmu};
use core::ffi::c_void;
use core::sync::atomic::{AtomicU64,Ordering};
const ISB_WORD:u32=0xd5033fdf;
const PA_LIMIT:u64=1<<48;
static NEXT_TOKEN:AtomicU64=AtomicU64::new(1);

fn mapped(s:c::Snapshot)->m::Controls {let mut v=s.controls(1);v.abi_version=2;v.profile=1;v.sctlr|=1;v}
pub fn controls_valid_dynamic(v:&m::Controls)->bool {
    v.abi_version==3 && v.struct_size==80 && v.profile==2 && v.reserved==0 && v.epoch!=0 &&
        controls_valid(&mapped(c::Snapshot::from_controls(*v)))
}
#[derive(Clone,Copy)]
struct Prepared {request:c::Request,reply:c::Reply,mmu:VfMmu,enable_pc:Option<u64>}
pub struct MemoryServiceDynamic<'a> {
    inner:MemoryServiceV2<'a>,architectural:c::Snapshot,effective:c::Snapshot,
    revision:u64,epoch:u64,invalidations:u64,prepared:Option<Prepared>,enable_pc:Option<u64>,table_reads:u64,
}
impl<'a> MemoryServiceDynamic<'a> {
    pub fn new(ram:&'a mut[u8],ram_base:u64,tables:&'a[u8],table_base:u64,controls:m::Controls)->Result<Self,Error> {
        if !controls_valid_dynamic(&controls) || controls.epoch!=1 || controls.sctlr&1!=0 {return Err(Error::InvalidControls);}
        if ram_base>=PA_LIMIT || ram.len()as u64>PA_LIMIT-ram_base || table_base>=PA_LIMIT || tables.len()as u64>PA_LIMIT-table_base {return Err(Error::InvalidRange);}
        let snapshot=c::Snapshot::from_controls(controls);
        let inner=MemoryServiceV2::new(ram,ram_base,tables,table_base,mapped(snapshot))?;
        Ok(Self{inner,architectural:snapshot,effective:snapshot,revision:1,epoch:1,invalidations:0,
            prepared:None,enable_pc:None,table_reads:0})
    }
    pub fn effective_controls(&self)->m::Controls {self.effective.controls(self.epoch)}
    pub fn table_reads(&self)->u64 {self.table_reads}
    pub fn final_state(&self)->c::Reply {
        c::Reply{abi_version:1,struct_size:192,state_tag:c::KNOWN,revision:self.revision,epoch:self.epoch,
            invalidations:self.invalidations,architectural:self.architectural,effective:self.effective,..Default::default()}
    }
    fn error(&self,q:&c::Request,result:u32,detail:u32)->c::Reply {
        c::Reply{abi_version:1,struct_size:192,result,detail,phase:if q.phase<=3 {q.phase}else{0},
            operation:if q.operation<=4 {q.operation}else{0},selector:if q.selector<=5 {q.selector}else{0},..Default::default()}
    }
    fn guard(&self,pc:u64,candidate:c::Snapshot)->Result<u64,(u32,u32)> {
        let next=pc.checked_add(4).filter(|v|v.checked_add(3).is_some()).ok_or((c::UNSUPPORTED,c::WRAP))?;
        let index=offset(next,4,self.inner.ram_base,self.inner.ram.len()).ok_or((c::UNAVAILABLE,c::BACKING))?;
        if false && u32::from_le_bytes(self.inner.ram[index..index+4].try_into().unwrap())!=ISB_WORD {return Err((c::UNSUPPORTED,c::BYTES));}
        let mut walker=self.inner.mmu;
        if !walker.configure_strict_nc(candidate.ttbr0,candidate.ttbr1,candidate.tcr) {return Err((c::UNSUPPORTED,c::CONTROL));}
        for byte in 0..4 {
            let translated=walker.translate_detailed(next,Access::Execute,ExceptionLevel::El1,|pa| {
                let at=offset(pa,8,self.inner.table_base,self.inner.tables.len()).ok_or(TableReadError::Unavailable)?;
                Ok(u64::from_le_bytes(self.inner.tables[at..at+8].try_into().unwrap()))
            }).map_err(|e|if matches!(e.kind,TranslationFailureKind::TableRead(_)) {(c::UNAVAILABLE,c::BACKING)}else{(c::UNSUPPORTED,c::MAPPING)})?;
            if translated.pa.checked_add(byte)!=next.checked_add(byte) ||
                translated.attributes!=Some(MemoryAttributes{attr_index:0,shareability:0,mair:0x44}) {
                return Err((c::UNSUPPORTED,c::MAPPING));
            }
            // Preflight each byte even though the aligned four-byte instruction
            // cannot cross a 4K/16K page. Backing ownership is checked independently.
            if offset(translated.pa+byte,1,self.inner.ram_base,self.inner.ram.len())!=Some(index+byte as usize) {
                return Err((c::UNAVAILABLE,c::BACKING));
            }
        }
        Ok(next)
    }
    pub fn control(&mut self,q:&c::Request)->c::Reply {
        if q.abi_version!=1 || q.struct_size!=192 || !(1..=3).contains(&q.phase) || !(1..=4).contains(&q.operation) ||
            q.current_el!=1 || q.pc&3!=0 || q.flags!=0 || q.reserved!=0 || q.before.reserved!=0 || q.candidate.reserved!=0 ||
            (q.operation==c::WRITE && !(1..=5).contains(&q.selector)) || (q.operation!=c::WRITE && q.selector!=0) {
            return self.error(q,c::INVALID,c::MALFORMED);
        }
        if q.before!=self.architectural || q.revision!=self.revision || q.epoch!=self.epoch {return self.error(q,c::INVALID,c::STALE);}
        if q.phase!=c::PREPARE {
            let Some(p)=self.prepared else{return self.error(q,c::INVALID,c::TOKEN)};
            let mut original=*q;original.phase=c::PREPARE;original.operand=p.request.operand;
            if q.operand!=p.reply.token || original!=p.request {return self.error(q,c::INVALID,c::TOKEN);}
            self.prepared=None;
            if q.phase==c::CANCEL {
                let mut out=self.final_state();out.phase=c::CANCEL;out.operation=q.operation;out.selector=q.selector;return out;
            }
            if q.operation==c::DSB {core::sync::atomic::fence(Ordering::SeqCst);}
            self.architectural=p.reply.architectural;self.effective=p.reply.effective;
            self.revision=p.reply.revision;self.epoch=p.reply.epoch;self.invalidations=p.reply.invalidations;
            self.inner.controls=mapped(self.effective);self.inner.mmu=p.mmu;self.enable_pc=p.enable_pc;
            let mut out=p.reply;out.phase=c::COMMIT;out.state_tag=c::KNOWN;out.token=0;return out;
        }
        if self.prepared.is_some() {return self.error(q,c::INVALID,c::TOKEN);}
        if self.enable_pc.is_some() && (q.operation!=c::ISB || self.enable_pc!=Some(q.pc)) {return self.error(q,c::UNSUPPORTED,c::PENDING);}
        let mut out=self.final_state();out.phase=c::PREPARE;out.operation=q.operation;out.selector=q.selector;out.state_tag=c::PROPOSED;
        let mut walker=self.inner.mmu;let mut enable_pc=self.enable_pc;
        if q.operation==c::WRITE {
            if self.architectural.sctlr&1!=0 {return self.error(q,c::UNSUPPORTED,c::CONTROL);}
            let mut expected=self.architectural;
            match q.selector {c::SCTLR=>expected.sctlr=q.operand,c::TTBR0=>expected.ttbr0=q.operand,c::TTBR1=>expected.ttbr1=q.operand,
                c::TCR=>expected.tcr=q.operand,c::MAIR=>expected.mair=q.operand,_=>unreachable!()}
            if q.candidate!=expected {return self.error(q,c::INVALID,c::MALFORMED);}
            let granule_ips=(3<<14)|(3<<30)|(7u64<<32);
            if !controls_valid(&mapped(expected)) || (expected.tcr^self.effective.tcr)&granule_ips!=0 {return self.error(q,c::UNSUPPORTED,c::CONTROL);}
            if q.selector==c::SCTLR {
                if q.operand!=self.architectural.sctlr|1 || self.architectural!=self.effective {return self.error(q,c::UNSUPPORTED,c::PENDING);}
                match self.guard(q.pc,expected) {Ok(next)=>enable_pc=Some(next),Err((result,detail))=>return self.error(q,result,detail)}
            }
            let Some(revision)=self.revision.checked_add(1)else{return self.error(q,c::UNSUPPORTED,c::OVERFLOW)};
            out.architectural=expected;out.revision=revision;
        } else {
            if q.candidate!=self.architectural || q.operand!=0 {return self.error(q,c::INVALID,c::MALFORMED);}
            if q.operation==c::ISB && self.architectural!=self.effective {
                let Some(epoch)=self.epoch.checked_add(1)else{return self.error(q,c::UNSUPPORTED,c::OVERFLOW)};
                if !walker.configure_strict_nc(self.architectural.ttbr0,self.architectural.ttbr1,self.architectural.tcr) {return self.error(q,c::UNSUPPORTED,c::CONTROL);}
                out.effective=self.architectural;out.epoch=epoch;enable_pc=None;
            } else if q.operation==c::TLBI {
                let Some(generation)=self.invalidations.checked_add(1)else{return self.error(q,c::UNSUPPORTED,c::OVERFLOW)};
                walker.invalidate();out.invalidations=generation;
            }
        }
        let Ok(token)=NEXT_TOKEN.fetch_update(Ordering::Relaxed,Ordering::Relaxed,|v|v.checked_add(1))else{return self.error(q,c::UNSUPPORTED,c::OVERFLOW)};
        out.token=token;self.prepared=Some(Prepared{request:*q,reply:out,mmu:walker,enable_pc});out
    }
    fn data_error(&self,result:u32,address:u64)->m::Reply {
        m::Reply{abi_version:3,struct_size:128,result,address,level:m::NO_LEVEL,epoch:self.epoch,..Default::default()}
    }
    pub fn execute(&mut self,q:&m::Request)->m::Reply {
        if q.abi_version!=3 || q.controls!=self.effective_controls() || q.current_el!=1 || self.prepared.is_some() {
            return self.data_error(m::INVALID_REQUEST,0);
        }
        let mut normalized=*q;normalized.abi_version=2;normalized.controls=self.inner.controls;
        if !self.inner.request_valid(&normalized) {return self.data_error(m::INVALID_REQUEST,0);}
        if self.architectural!=self.effective && q.pstate&0xc0!=0xc0 {return self.data_error(m::UNSUPPORTED,q.address);}
        if let Some(next)=self.enable_pc {
            if q.operation!=FETCH || q.pc!=next {return self.data_error(m::UNSUPPORTED,q.address);}
        }
        if self.effective.sctlr&1!=0 {
            let mut out=self.inner.execute_counted(&normalized,&mut self.table_reads);out.abi_version=3;out.epoch=self.epoch;return out;
        }
        if q.address&(u64::from(q.width)-1)!=0 {
            let mut out=self.data_error(m::GUEST_FAULT,q.address);out.context=m::INPUT;
            if q.operation==FETCH {out.fault=m::PC_ALIGNMENT;out.esr=0x8a000000;}
            else {out.fault=m::DATA_ALIGNMENT;out.fsc=0x21;out.esr=0x96000021|if q.operation==STORE {64}else{0};}
            return out;
        }
        let bytes=(q.width*q.count)as usize;
        if q.address.checked_add(bytes as u64-1).is_none() || q.address>=PA_LIMIT || bytes as u64>PA_LIMIT-q.address {
            return self.data_error(m::UNSUPPORTED,q.address);
        }
        let mut places=[(false,0usize);16];
        for (byte,place)in places[..bytes].iter_mut().enumerate() {
            let pa=q.address+byte as u64;
            if let Some(index)=offset(pa,1,self.inner.ram_base,self.inner.ram.len()) {*place=(false,index);}
            else if let Some(index)=offset(pa,1,self.inner.table_base,self.inner.tables.len()) {
                if q.operation==STORE {return self.data_error(m::UNSUPPORTED,pa);}*place=(true,index);
            } else {let mut out=self.data_error(m::UNAVAILABLE,pa);out.output_pa=pa;out.metadata_flags=m::HAS_OUTPUT;return out;}
        }
        let mut values=[0u64;2];
        for (byte,&(table,index))in places[..bytes].iter().enumerate() {
            let element=byte/q.width as usize;let shift=(byte%q.width as usize)*8;
            if q.operation==STORE {self.inner.ram[index]=(if element==0 {q.value0}else{q.value1}>>shift)as u8;}
            else {values[element]|=u64::from(if table {self.inner.tables[index]}else{self.inner.ram[index]})<<shift;}
        }
        if self.enable_pc.is_some() && values[0]!=u64::from(ISB_WORD) {return self.data_error(m::UNSUPPORTED,q.address);}
        let mut out=self.data_error(m::OK,0);out.value0=values[0];out.value1=values[1];out
    }
}

#[cfg(test)]#[path="/home/sharh/work/integration-validation-bp34-20260909/26x86/nextcore/crates/nextcore-ise/runtime/memory-service/src/dynamic_tests.rs"]mod tests;

/// Owner, request and reply are complete/aligned/disjoint for the call, with
/// exclusive owner access and no reentry, aliases, retention or host mutation.
#[no_mangle]pub unsafe extern "C" fn vf_memory_dynamic_control_v1(owner:*mut c_void,q:*const c::Request,out:*mut c::Reply)->i32 {
    if owner.is_null() || q.is_null() || out.is_null() || (owner as usize)%8!=0 || (q as usize)%8!=0 || (out as usize)%8!=0 {return -1;}
    let q=unsafe{*q};let result=unsafe{(&mut *owner.cast::<MemoryServiceDynamic<'_>>()).control(&q)};unsafe{out.write(result)};0
}
/// Same complete-record, lifetime and exclusive-owner rules as control_v1.
#[no_mangle]pub unsafe extern "C" fn vf_memory_dynamic_step_v1(owner:*mut c_void,q:*const m::Request,out:*mut m::Reply)->i32 {
    if owner.is_null() || q.is_null() || out.is_null() || (owner as usize)%8!=0 || (q as usize)%8!=0 || (out as usize)%8!=0 {return -1;}
    let q=unsafe{*q};let result=unsafe{(&mut *owner.cast::<MemoryServiceDynamic<'_>>()).execute(&q)};unsafe{out.write(result)};0
}
