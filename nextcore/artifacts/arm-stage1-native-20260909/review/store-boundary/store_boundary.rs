//! Authored Linux x86 proof: generated x86 invokes canonical translated memory.
use core::ffi::c_void;
use nextcore_memory_service::{abi::{FETCH,LOAD,STORE},abi_v2::*,stage1::{MemoryServiceV2,vf_memory_service_step_v2}};
#[path="/home/sharh/work/bp32-ise-native-mmu/runtime/preos/src/platform.rs"]mod platform;
#[path="/home/sharh/work/bp32-ise-native-mmu/runtime/memory_boot.rs"]mod memory_boot;
#[path="/home/sharh/work/bp32-ise-native-mmu/runtime/memory_boot_v2.rs"]mod memory_boot_v2;
use memory_boot_v2::MemoryRunResultV2 as Run;
type Protect=unsafe extern "C" fn(*mut c_void,usize,i32,*mut c_void)->i32;
unsafe extern "C" {
    fn vf_stage1_layout(out:*mut u64,capacity:usize)->usize;
    fn vf_stage1_controls_probe(controls:*const Controls)->i32;
    fn mmap(p:*mut c_void,n:usize,prot:i32,flags:i32,fd:i32,off:isize)->*mut c_void;
    fn mprotect(p:*mut c_void,n:usize,prot:i32)->i32;
    fn munmap(p:*mut c_void,n:usize)->i32;
    fn vf_boot_run_memory_v2(base:u64,size:u64,entry:u64,args:u64,stack:u64,
        code:*mut u8,code_bytes:usize,budget:u64,protect:Option<Protect>,opaque:*mut c_void,
        initial:*const u64,options:*const platform::BootOptionsV2,controls:*const Controls,
        callback:Option<Callback>,owner:*mut c_void,result:*mut Run)->i32;
}
unsafe extern "C" fn protect(p:*mut c_void,n:usize,x:i32,_:*mut c_void)->i32 {unsafe{mprotect(p,n,if x!=0 {5}else{3})}}
struct Code(*mut u8);
impl Code {fn new()->Self {let p=unsafe{mmap(core::ptr::null_mut(),4096,3,0x22,-1,0)};assert_ne!(p as isize,-1);Self(p.cast())}}
impl Drop for Code {fn drop(&mut self){assert_eq!(unsafe{munmap(self.0.cast(),4096)},0);}}
struct Owner<'a>{service:MemoryServiceV2<'a>,requests:Vec<Request>,corruption:u32}
unsafe extern "C" fn callback(owner:*mut c_void,q:*const Request,out:*mut Reply)->i32 {
    let owner=unsafe{&mut *owner.cast::<Owner<'_>>()};let q=unsafe{*q};owner.requests.push(q);
    let status=unsafe{vf_memory_service_step_v2((&mut owner.service as *mut MemoryServiceV2<'_>).cast(),&q,out)};
    if status!=0{return status;}
    let r=unsafe{&mut *out};match owner.corruption {9 if q.operation==STORE=>r.epoch+=1,
        1=>r.epoch+=1,2=>r.reserved[4]=1,3=>r.esr|=1<<7,4=>r.value1=1,
        5 if q.operation!=FETCH=>r.esr^=64,6 if q.operation!=FETCH=>r.level=0,
        7 if q.operation!=FETCH=>r.address=r.descriptor_pa,8=>r.context=3,
        _=>{}
    }0
}
const RAM:u64=0x40000000;const TABLES:u64=0x10000000;const VA:u64=0x10000;const HLT:u32=0xd4400000;
fn scalar(size:u32,opc:u32,rn:u32,rt:u32)->u32 {0x39000000|size<<30|opc<<22|rn<<5|rt}
fn pair(wide:bool,read:bool,mode:u32,imm:i32,rn:u32,rt:u32,rt2:u32)->u32 {
    0x28000000|u32::from(wide)<<31|u32::from(read)<<22|mode<<23|((imm as u32)&127)<<15|rt2<<10|rn<<5|rt
}
fn fixture(sixteen:bool,words:&[u32])->(Controls,Vec<u8>,Vec<u8>,usize,usize) {
    let step=if sixteen {0x4000}else{0x1000};let mut tables=vec![0;step*4];let mut ram=vec![0xa5;step*4];
    let (start,bits,page)=if sixteen {(1,11,14)}else{(0,9,12)};let mut leaf=0;
    for level in start..=3 {
        let n=level-start;let index=((VA>>(page+bits*(3-level)))&((1<<bits)-1))as usize;let at=n*step+index*8;
        let value=if level==3 {leaf=at;RAM|0x403}else{TABLES+((n+1)*step)as u64|3};
        tables[at..at+8].copy_from_slice(&value.to_le_bytes());
    }
    tables[leaf+8..leaf+16].copy_from_slice(&(RAM+(3*step)as u64|0x403).to_le_bytes());
    tables[leaf+16..leaf+24].copy_from_slice(&(RAM+step as u64|0x403).to_le_bytes());
    for(i,w)in words.iter().enumerate(){ram[4*i..4*i+4].copy_from_slice(&w.to_le_bytes());}
    let tcr=if sixteen {17|(17<<16)|(2<<14)|(1<<30)|(5<<32)}else{16|(16<<16)|(2<<30)|(5<<32)};
    let c=Controls{abi_version:2,struct_size:80,profile:1,sctlr:0x30d00803,ttbr0:TABLES,ttbr1:TABLES,tcr,mair:0x44,epoch:1,..Controls::default()};
    (c,tables,ram,step,leaf)
}
fn run(c:Controls,tables:&[u8],ram:&mut[u8],entry:u64,initial:[u64;4],corruption:u32)->(Run,Vec<Request>) {
    run_with_options(c,tables,ram,entry,initial,corruption,None)
}
fn run_with_options(c:Controls,tables:&[u8],ram:&mut[u8],entry:u64,initial:[u64;4],corruption:u32,options:Option<&platform::BootOptionsV2>)->(Run,Vec<Request>) {
    let code=Code::new();let size=ram.len()as u64;
    let mut owner=Owner{service:MemoryServiceV2::new(ram,RAM,tables,TABLES,c).unwrap(),requests:Vec::new(),corruption};
    let mut result=Run::default();let status=unsafe{vf_boot_run_memory_v2(RAM,size,entry,initial[0],VA+0x400,
        code.0,4096,32,Some(protect),core::ptr::null_mut(),initial.as_ptr(),options.map_or(core::ptr::null(),|v|v),&c,
        Some(callback),(&mut owner as *mut Owner<'_>).cast(),&mut result)};
    assert_eq!(status as u32,result.base.execution.base.status);
    assert_eq!((result.base.abi_version,result.base.struct_size),(2,320));(result,owner.requests)
}
#[test]fn actual_c_rust_abi_and_control_validation_match_all_fields() {
    use core::mem::{size_of,align_of,offset_of};
    macro_rules! layout {($t:ty;$($f:ident),+)=>{[size_of::<$t>()as u64,align_of::<$t>()as u64,$(offset_of!($t,$f)as u64),+]};}
    let mut expected=layout!(Controls;abi_version,struct_size,profile,reserved,sctlr,ttbr0,ttbr1,tcr,mair,hcr,scr,epoch).to_vec();
    expected.extend(layout!(Request;abi_version,struct_size,operation,flags,width,count,current_el,reserved0,pc,address,value0,value1,pstate,controls,reserved1));
    expected.extend(layout!(Reply;abi_version,struct_size,result,fault,level,context,fsc,metadata_flags,value0,value1,address,esr,epoch,descriptor_pa,output_pa,reserved));
    expected.extend(layout!(Run;base,last_reply));expected.push(888);
    let mut actual=vec![u64::MAX;expected.len()];assert_eq!(unsafe{vf_stage1_layout(actual.as_mut_ptr(),actual.len())},expected.len());assert_eq!(actual,expected);
    for sixteen in [false,true] {let(c,_,_,_,_)=fixture(sixteen,&[HLT]);
        for field in 0..8 {for bit in 0..64 {
            let mut candidate=c;match field {0=>candidate.sctlr^=1<<bit,1=>candidate.ttbr0^=1<<bit,
                2=>candidate.ttbr1^=1<<bit,3=>candidate.tcr^=1<<bit,4=>candidate.mair^=1<<bit,
                5=>candidate.hcr^=1<<bit,6=>candidate.scr^=1<<bit,_=>candidate.epoch^=1<<bit};
            assert_eq!(unsafe{vf_stage1_controls_probe(&candidate)}!=0,nextcore_memory_service::stage1::controls_valid(&candidate));
        }}
    }
}
#[test]fn readonly_controls_and_unsupported_changes_preserve_fixed_regime() {
    let(c,tables,mut ram,_,_)=fixture(false,&[0xd5381000,0xd5382001,0xd5382042,0xd538a203,HLT]);
    let(r,_)=run(c,&tables,&mut ram,VA,[0;4],0);let b=r.base.execution.base;
    assert_eq!((b.status,b.retired,b.x0,b.x1,b.x2,b.x3),(1,5,c.sctlr,c.ttbr0,c.tcr,c.mair));
    for word in [0xd5181000,0xd5182000,0xd5182020,0xd5182040,0xd518a200,0xd5033fdf,0xd5033f9f,0xd5033fbf,0xd508871f] {
        let(c,tables,mut ram,_,_)=fixture(false,&[word,HLT]);let before=ram.clone();
        let(r,requests)=run(c,&tables,&mut ram,VA,[c.sctlr,1,2,3],0);let b=r.base.execution.base;
        assert_eq!((b.status,b.retired,b.pc,b.x0,r.base.provider_status),(13,0,VA,c.sctlr,0));
        assert_eq!(requests.len(),1);assert_eq!(requests[0].controls,c);assert_eq!(ram,before);
    }
}
#[test]fn alignment_priority_lower_el_and_irq_vector_boundaries_are_precise() {
    let(c,mut tables,mut ram,step,_)=fixture(false,&[scalar(3,1,1,0),HLT]);
    let(r,_)=run(c,&tables,&mut ram,VA,[1,VA+step as u64+1,2,3],0);
    assert_eq!((r.base.execution.base.status,r.base.execution.esr,r.base.execution.base.retired),(12,0x96000021,0));
    tables[..8].fill(0);
    let(r,requests)=run(c,&tables,&mut ram,VA+1,[1,2,3,4],0);
    assert_eq!((r.base.execution.base.status,r.base.execution.esr,r.base.guest_far),(16,0x8a000000,VA+1));
    assert_eq!((r.base.execution.base.retired,r.base.execution.base.compiled_blocks,requests.len()),(0,0,1));
    let(c,tables,mut ram,step,_)=fixture(false,&[scalar(3,1,1,0),HLT]);
    let options=platform::BootOptionsV2{abi_version:2,struct_size:64,initial_pstate:0x3c0,..Default::default()};
    let(r,_)=run_with_options(c,&tables,&mut ram,VA,[1,VA+step as u64,2,3],0,Some(&options));
    assert_eq!((r.base.execution.base.status,r.base.execution.esr,r.base.execution.base.compiled_blocks),(17,0x9200000f,1));
    for fiq in [false,true] {for mode in [0u64,4,5] {
        let pstate=(0x3c0|mode)&!(if fiq {64}else{128});
        let options=platform::BootOptionsV2{abi_version:2,struct_size:64,platform_profile:1,initial_pstate:pstate,vbar:VA+0x800,
            irq_level:(!fiq)as u64,fiq_level:fiq as u64,..Default::default()};
        let(r,requests)=run_with_options(c,&tables,&mut ram,VA,[1,2,3,4],0,Some(&options));
        let vector=VA+0x800+(if mode==0 {0x400}else if mode==4 {0}else{0x200})+if fiq {0x100}else{0x80};
        assert_eq!((r.base.execution.base.status,r.base.execution.base.retired,r.base.execution.base.pc),(if fiq {18}else{15},0,vector));
        assert_eq!((r.base.execution.elr,r.base.execution.spsr,r.base.execution.esr),(VA,pstate,0));assert!(requests.is_empty());
    }}
}
#[test]fn nonidentity_native_alu_scalar_and_pair_use_actual_rust_callbacks() {
    for sixteen in [false,true] {
        let words=[0xd2800540,scalar(3,0,1,0),scalar(3,1,1,2),0x91001443,HLT];
        let(c,tables,mut ram,step,_)=fixture(sixteen,&words);
        let(r,requests)=run(c,&tables,&mut ram,VA,[0,VA+step as u64,0,0],0);let b=r.base.execution.base;
        assert_eq!((b.status,b.retired,b.compiled_blocks,b.x0,b.x2,b.x3),(1,5,5,42,42,47));
        assert_eq!((r.base.provider_status,r.base.fetch_requests,r.base.data_requests),(0,5,2));
        assert_eq!(&ram[3*step..3*step+8],&42u64.to_le_bytes());
        assert_eq!(requests.iter().map(|q|q.operation).collect::<Vec<_>>(),[FETCH,FETCH,STORE,FETCH,LOAD,FETCH,FETCH]);
        assert!(requests.iter().all(|q|q.controls==c && q.pc>=VA && q.pc<VA+32));
        let words=[pair(true,false,2,0,1,0,2),0xd2800000,0xd2800002,pair(true,true,2,0,1,0,2),HLT];
        let(c,tables,mut ram,step,_)=fixture(sixteen,&words);let address=VA+(2*step)as u64-8;
        let(r,_)=run(c,&tables,&mut ram,VA,[0x123456789abcdef0,address,0x8123456789abcdef,0],0);
        assert_eq!((r.base.execution.base.status,r.base.execution.base.x0,r.base.execution.base.x2),(1,0x123456789abcdef0,0x8123456789abcdef));
        assert_eq!(&ram[step..step+8],&0x8123456789abcdefu64.to_le_bytes());
    }
}
#[test]fn translated_scalar_width_and_sign_families_keep_native_register_semantics() {
    for sixteen in [false,true] {for size in 0..4 {for opc in 0..4 {
        if opc>=2&&(size==3 || (size==2&&opc==3)){continue;}
        let(c,tables,mut ram,step,_)=fixture(sixteen,&[scalar(size,opc,1,0),HLT]);
        let raw=0x8123456789abcdefu64;ram[3*step..3*step+8].copy_from_slice(&raw.to_le_bytes());
        let(r,_)=run(c,&tables,&mut ram,VA,[0xfedcba9876543210,VA+step as u64,0,0],0);
        assert_eq!((r.base.execution.base.status,r.base.execution.base.retired,r.base.provider_status),(1,2,0));
        let width=1usize<<size;let mask=if width==8 {u64::MAX}else{(1u64<<(width*8))-1};
        if opc==0 {assert_eq!(&ram[3*step..3*step+width],&0xfedcba9876543210u64.to_le_bytes()[..width]);}
        else {let mut expected=raw&mask;if opc>=2 {expected=((expected<<(64-width*8))as i64>>(64-width*8))as u64;}
            if opc==3 {expected=expected as u32 as u64;}assert_eq!(r.base.execution.base.x0,expected);}
    }}}
}
#[test]fn second_page_abort_and_bad_replies_preserve_architectural_state() {
    for sixteen in [false,true] {
        let(c,mut tables,mut ram,step,leaf)=fixture(sixteen,&[pair(true,false,1,2,1,0,2),HLT]);
        tables[leaf+16..leaf+24].copy_from_slice(&(RAM+step as u64|0x483).to_le_bytes());
        let before=ram.clone();let address=VA+(2*step)as u64-8;
        let(r,_)=run(c,&tables,&mut ram,VA,[1,address,2,0],0);let b=r.base.execution.base;
        assert_eq!((b.status,b.retired,b.compiled_blocks,r.base.provider_status),(17,0,1,0));
        assert_eq!((b.pc,b.x0,b.x1,b.x2),(VA,1,address,2));assert_eq!(ram,before);
        assert_eq!((r.base.guest_far,r.base.execution.esr,r.last_reply.level),(address+8,0x9600004f,3));
    }
    for corruption in 1..=8 {
        let(c,mut tables,mut ram,step,leaf)=fixture(false,&[scalar(3,1,1,0),HLT]);
        if (5..=7).contains(&corruption){tables[leaf+8..leaf+16].fill(0);}
        let before=ram.clone();let(r,_)=run(c,&tables,&mut ram,VA,[1,VA+step as u64,2,3],corruption);
        assert_eq!((r.base.execution.base.status,r.base.execution.base.retired,r.base.provider_status),(4,0,3));
        assert_eq!(r.base.execution.esr,0);assert_eq!(r.base.execution.base.fault_instruction,0);assert_eq!(ram,before);
    }
}

#[test] fn review_store_malformed_after_commit() {
let(c,tables,mut ram,step,_)=fixture(false,&[scalar(3,0,1,0),HLT]);
let before=ram.clone();let(r,_)=run(c,&tables,&mut ram,VA,[42,VA+step as u64,2,3],9);
println!("status={} provider={} retired={} completed={} old={:?} new={:?}",r.base.execution.base.status,r.base.provider_status,r.base.execution.base.retired,r.base.completed_data_operations,&before[3*step..3*step+8],&ram[3*step..3*step+8]);
assert_eq!((r.base.execution.base.status,r.base.provider_status,r.base.execution.base.retired,r.base.completed_data_operations),(4,3,0,0));
assert_ne!(ram,before);assert_eq!(&ram[3*step..3*step+8],&42u64.to_le_bytes());
}
