//! Actual native mapped execution using the canonical Rust memory and PAC providers.
use super::*;
#[path="/mnt/c/Users/Admin/Documents/Codex/2026-09-12/git/work/26x86/nextcore/crates/nextcore-ise/runtime/preos/src/pauth.rs"]mod canonical_pauth;
#[repr(C)]#[derive(Clone,Copy)]
struct Pac {x:[u64;31],sp:u64,pc:u64,sctlr:u64,tcr:u64,keys:[[u64;2];5],el:u32,reserved:u32}
type Pauth=unsafe extern "C" fn(*mut Pac,u32)->i32;
unsafe extern "C" {
    fn vf_preos_pauth_step(context:*mut Pac,instruction:u32)->i32;
    fn vf_boot_run_memory_pauth_v2(base:u64,size:u64,entry:u64,args:u64,stack:u64,
        code:*mut u8,code_bytes:usize,budget:u64,protect:Option<Protect>,opaque:*mut c_void,
        initial:*const u64,pauth:Option<Pauth>,options:*const platform::BootOptionsV2,controls:*const Controls,
        callback:Option<Callback>,owner:*mut c_void,result:*mut Run)->i32;
    fn test_mapped_cpu_size()->usize;
    fn test_mapped_stack_state(snapshot:*const u8,c:*const Controls)->i32;
    fn test_mapped_snapshot(c:*const Controls,code:*mut u8,capacity:usize,budget:u64,
        protect:Protect,protect_owner:*mut c_void,callback:Callback,owner:*mut c_void,
        initial:*const u64,pauth:Option<Pauth>,change_el:u32,snapshot:*mut u8,result:*mut Run)->i32;
}
unsafe extern "C" fn hostile(context:*mut Pac,instruction:u32)->i32 {
    let c=unsafe{&mut *context};c.x[0]=0xdead;c.pc+=4;c.keys[0][0]=0xbeef;
    match instruction&3 {0=>c.sctlr^=2,1=>c.tcr^=1,2=>c.el=0,_=>c.reserved=1}0
}
fn controls(sixteen:bool,words:&[u32])->(Controls,Vec<u8>,Vec<u8>) {
    let(mut c,t,r,_,_)=fixture(sixteen,words);c.profile=3;c.sctlr=0x30d00801;(c,t,r)
}
fn pac_run(c:Controls,tables:&[u8],ram:&mut[u8],initial:[u64;4],pauth:Option<Pauth>)->(Run,Vec<Request>) {
    let code=Code::new();let size=ram.len()as u64;
    let mut owner=Owner{service:MemoryServiceV2::new(ram,RAM,tables,TABLES,c).unwrap(),requests:Vec::new(),corruption:0};
    let mut result=Run::default();let status=unsafe{vf_boot_run_memory_pauth_v2(RAM,size,VA,initial[0],VA+0x400,
        code.0,4096,32,Some(protect),core::ptr::null_mut(),initial.as_ptr(),pauth,core::ptr::null(),&c,
        Some(callback),(&mut owner as *mut Owner<'_>).cast(),&mut result)};
    assert_eq!(status as u32,result.base.execution.base.status);(result,owner.requests)
}
#[test]fn mapped_xpac_generic_and_disabled_pac_use_canonical_provider() {
    assert_eq!(core::mem::size_of::<Pac>(),368);
    for sixteen in [false,true] {
        let bits=if sixteen {47}else{48};let tagged=if sixteen {0xbf36800000000130}else{0xbf36000000000130};
        let(c,t,mut ram)=controls(sixteen,&[0xdac143e0,HLT]);
        let(r,q)=pac_run(c,&t,&mut ram,[tagged,0,0,0],Some(vf_preos_pauth_step));
        assert_eq!((r.base.execution.base.status,r.base.execution.base.retired,r.base.execution.base.x0),(1,2,0x130));
        assert_eq!(q.len(),2);assert_eq!((c.tcr&63)as usize,64-bits);
        // PACGA zero-key/data/modifier vector from the existing actual QEMU capture.
        let(c,t,mut ram)=controls(sixteen,&[0x9ac23020,HLT]);
        let(r,q)=pac_run(c,&t,&mut ram,[42,0,0,0],Some(vf_preos_pauth_step));
        assert_eq!((r.base.execution.base.status,r.base.execution.base.retired,r.base.execution.base.x0),(1,2,0x76243b9500000000));
        assert_eq!(q.len(),2);
        for instruction in [0xdac10020,0xdac11020] {
            let(c,t,mut ram)=controls(sixteen,&[instruction,HLT]);let before=ram.clone();
            let(r,_)=pac_run(c,&t,&mut ram,[tagged,0x9876,2,3],Some(vf_preos_pauth_step));
            assert_eq!((r.base.execution.base.status,r.base.execution.base.retired,r.base.execution.base.x0),(1,2,tagged));
            assert_eq!(ram,before);
        }
    }
}
#[test]fn old_entry_and_null_callback_do_not_gain_pac() {
    let(c,t,mut ram)=controls(true,&[0xdac143e0,HLT]);let before=ram.clone();
    let(old,_)=run(c,&t,&mut ram,VA,[0xbf36800000000130,2,3,4],0);
    assert_eq!(old.base.execution.base.retired,0);assert_ne!(old.base.execution.base.status,1);
    let(null,q)=pac_run(c,&t,&mut ram,[1,2,3,4],None);
    assert_eq!(null.base.execution.base.retired,0);assert!(q.is_empty());assert_eq!(ram,before);
}
#[test]fn hostile_pac_cannot_commit_any_register_or_immutable_control_change() {
    for selector in 0..4 {
        let(c,t,mut ram)=controls(true,&[0xdac143e0|selector,HLT]);let before=ram.clone();
        let(r,q)=pac_run(c,&t,&mut ram,[11,22,33,44],Some(hostile));let b=r.base.execution.base;
        assert_eq!((b.retired,b.pc,b.x0,b.x1,b.x2,b.x3),(0,VA,11,22,33,44));
        assert_ne!(b.status,1);assert_eq!(q.len(),1);assert_eq!(ram,before);
    }
}
struct Recorder<'a>{service:MemoryServiceV2<'a>,events:Vec<u8>,fetches:u64,failure:bool}
unsafe extern "C" fn recorded(owner:*mut c_void,q:*const Request,r:*mut Reply)->i32 {
    let o=unsafe{&mut *owner.cast::<Recorder<'_>>()};let request=unsafe{&*q};
    if request.operation==FETCH {o.fetches+=1;}
    let status=if o.failure&&o.fetches==5 {-1}else{unsafe{vf_memory_service_step_v2((&mut o.service as *mut MemoryServiceV2<'_>).cast(),q,r)}};
    // ABI records contain only explicitly initialized scalar fields, no pointers.
    o.events.extend_from_slice(unsafe{core::slice::from_raw_parts(q.cast::<u8>(),core::mem::size_of::<Request>())});
    o.events.extend_from_slice(unsafe{core::slice::from_raw_parts(r.cast::<u8>(),core::mem::size_of::<Reply>())});
    o.events.extend_from_slice(&status.to_le_bytes());status
}
struct Permissions {calls:u64,fail:u64}
unsafe extern "C" fn counted(p:*mut c_void,n:usize,x:i32,owner:*mut c_void)->i32 {
    let o=unsafe{&mut *owner.cast::<Permissions>()};o.calls+=1;
    if o.calls==o.fail {-1}else{unsafe{mprotect(p,n,if x!=0 {5}else{3})}}
}
#[cfg(nextcore_mapped_snapshot)]
#[test]fn complete_cached_uncached_snapshots_with_canonical_memory() {
    let directory=std::env::var_os("NEXTCORE_MAPPED_SNAPSHOTS").expect("snapshot runner supplies output directory");
    for kind in 0..9 {
        let words=match kind {1=>vec![0x14000000],2=>vec![0x91000442,0xb9000020,0x17fffffe],
            3=>{let mut v=vec![0x10000004;65];v.push(0x17ffffbf);v},
            4=>vec![0xb340fc22,0x17ffffff],8=>vec![0xd538d080,0x17ffffff],_=>vec![0x91000442,0xf9000022,0x17fffffe]};
        let(c,t,mut ram)=controls(true,&words);let code=Code::new();let size=unsafe{test_mapped_cpu_size()};
        let initial=if kind==2 {[0x91000842,VA,17,3]}else{[1,VA+0x4000,17,3]};
        let mut recorder=Recorder{service:MemoryServiceV2::new(&mut ram,RAM,&t,TABLES,c).unwrap(),events:Vec::new(),fetches:0,failure:kind==1};
        let mut p=Permissions{calls:0,fail:if kind==6 {1}else if kind==7 {2}else{0}};
        let capacity=if kind==5 {512}else{4096};let mut cpu=vec![0u8;size];let mut r=Run::default();
        let status=unsafe{test_mapped_snapshot(&c,code.0,capacity,264,counted,(&mut p as *mut Permissions).cast(),
            recorded,(&mut recorder as *mut Recorder<'_>).cast(),initial.as_ptr(),Some(vf_preos_pauth_step),u32::from(kind==8),cpu.as_mut_ptr(),&mut r)};
        if kind==1 {assert_eq!((status,r.base.execution.base.retired),(4,4));}
        else if kind==8 {assert_eq!((status,r.base.execution.base.retired),(8,2));}
        else if kind>=6 {assert_eq!((status,r.base.execution.base.retired),(7,0));}
        else {assert_eq!((status,r.base.execution.base.retired),(5,264));}
        let mut bytes=cpu;bytes.extend_from_slice(unsafe{core::slice::from_raw_parts((&r as *const Run).cast::<u8>(),core::mem::size_of::<Run>())});
        bytes.extend_from_slice(&recorder.events);drop(recorder);bytes.extend_from_slice(&ram);
        std::fs::write(std::path::Path::new(&directory).join(format!("case-{kind}.bin")),bytes).unwrap();
        std::fs::write(std::path::Path::new(&directory).join(format!("case-{kind}.calls")),p.calls.to_string()).unwrap();
    }
}

#[cfg(nextcore_mapped_snapshot)]
#[test]fn mapped_spsel_banks_preserve_controls_and_following_stack_memory() {
    // MSR SPSel,#0/#1; STR/LDR using SP. Encodings checked with LLVM AArch64 assembler.
    let words=[0xd50041bf,0xd50040bf,0xf90003e0,0xf94003e2,0xd50040bf,
               0xd50041bf,0xf90003e0,0xf94003e3,0xd50041bf,HLT];
    for (program,mode,retired) in [(&words[..],2,10),(&[0xd50042bf,HLT][..],2,0),(&[0xd50040bf,HLT][..],3,0)] {
        let(c,t,mut ram)=controls(true,program);let before=ram.clone();let code=Code::new();
        let mut recorder=Recorder{service:MemoryServiceV2::new(&mut ram,RAM,&t,TABLES,c).unwrap(),events:Vec::new(),fetches:0,failure:false};
        let mut permissions=Permissions{calls:0,fail:0};let mut cpu=vec![0u8;unsafe{test_mapped_cpu_size()}];let mut result=Run::default();
        let initial=[0x1122334455667788,22,33,44];
        let status=unsafe{test_mapped_snapshot(&c,code.0,4096,32,counted,(&mut permissions as *mut Permissions).cast(),
            recorded,(&mut recorder as *mut Recorder<'_>).cast(),initial.as_ptr(),Some(vf_preos_pauth_step),mode,cpu.as_mut_ptr(),&mut result)};
        let execution=result.base.execution.base;
        assert_eq!(execution.retired,retired);assert_eq!(recorder.fetches,if retired==10 {10}else{1});
        if retired==10 {
            assert_eq!((status,execution.x2,execution.x3),(1,initial[0],initial[0]));
            assert_eq!(unsafe{test_mapped_stack_state(cpu.as_ptr(),&c)},1);
        } else {assert_eq!(status,if mode==3 {9}else{13}); // EL0 privilege fault / reserved system-register trap.
            assert_eq!((execution.x0,execution.x1,execution.x2,execution.x3),(initial[0],22,33,44));}
        drop(recorder);
        if retired==10 {for offset in [0x400,0x800] {assert_eq!(&ram[offset..offset+8],&initial[0].to_le_bytes());}}
        else {assert_eq!(ram,before);}
    }
}

#[test]fn matrix_ids(){for id in [0u32,1]{for pac in [false,true]{for sentinel in [false,true]{let word=if id==0{0xd5380620}else{0xd5380700};let(c,t,mut ram)=controls(true,&[word,HLT]);let before=ram.clone();let code=Code::new();let mut owner=Owner{service:MemoryServiceV2::new(&mut ram,RAM,&t,TABLES,c).unwrap(),requests:Vec::new(),corruption:0};let mut result=Run::default();let mut snapshot=vec![0u8;unsafe{test_mapped_cpu_size()}];let initial=[0xfeed,22,33,44];let status=unsafe{test_mapped_snapshot(&c,code.0,4096,32,protect,core::ptr::null_mut(),callback,(&mut owner as *mut Owner<'_>).cast(),initial.as_ptr(),if pac{Some(vf_preos_pauth_step)}else{None},if sentinel{100}else{0},snapshot.as_mut_ptr(),&mut result)};let requests=owner.requests.len();drop(owner);let b=result.base.execution.base;println!("id={} mapped_pac={} sentinel={} status={} x0={:x} pc={:x} retired={} fetch={} data={} requests={} ram_equal={}",id,pac,sentinel,status,b.x0,b.pc,b.retired,result.base.fetch_requests,result.base.data_requests,requests,ram==before);}}}}
