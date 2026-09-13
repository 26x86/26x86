// Executed inside the real GuestCpuState module; expected rows are independent.
#[test]fn hierarchy_reference_cross_regime_cache_does_not_leak(){
 use crate::mmu::{VfMmu,Access,Fault};
 for sixteen in [false,true]{let step=if sixteen{0x4000u64}else{0x1000};let start=if sixteen{1}else{0};let tcr=if sixteen{17|(2<<14)}else{16};
 let entries:Vec<(u64,u64)>=(start..=3).map(|l|{let pa=step*(l-start+1);(pa,if l==3{0x40000443}else{pa+step|3|if l==start{1<<62}else{0}})}).collect();
 let mut mmu=VfMmu::disabled();assert!(mmu.configure_tcr(step,0,tcr,127));
 let mut reads=0;let read=|pa|entries.iter().find(|e|e.0==pa).map(|e|e.1);
 assert!(mmu.translate(0,Access::Read,ExceptionLevel::El1,|pa|{reads+=1;read(pa)}).is_ok());let cold=reads;assert!(cold>0);
 assert!(mmu.translate(0,Access::Read,ExceptionLevel::El0,|_|panic!("EL0/1 must share cache")).is_ok());
 assert_eq!(mmu.translate(0,Access::Write,ExceptionLevel::El1,|_|panic!("cached")),Err(Fault::Permission));
 for el in [ExceptionLevel::El2,ExceptionLevel::El3]{let mut more=0;assert!(mmu.translate(0,Access::Write,el,|pa|{more+=1;read(pa)}).is_ok());if el==ExceptionLevel::El2{assert!(more>0);}else{assert_eq!(more,0);}}
 assert_eq!(mmu.translate(0,Access::Write,ExceptionLevel::El1,read),Err(Fault::Permission));assert_eq!(mmu.asid,127);
 }
}
#[test]fn hierarchy_reference_instruction_fetch_matrix(){
 // Leaf AP01: parent00 denies EL1 fetch; parent01/10/11 remove effective EL0 writes.
 for sixteen in [false,true]{for parent in 0..4u64{for el in [ExceptionLevel::El0,ExceptionLevel::El1]{
 let step=if sixteen{0x4000usize}else{0x1000};let start=if sixteen{1}else{0};let mut ram=vec![0u8;0x20000];
 for level in start..=3{let pa=step*(level-start+1);let d=if level==3{0x10000u64|0x443}else{(pa+step)as u64|3|if level==start{parent<<61}else{0}};ram[pa..pa+8].copy_from_slice(&d.to_le_bytes());}
 ram[0x10000..0x10004].copy_from_slice(&0x91000400u32.to_le_bytes());let mut cpu=GuestCpuState::reset(0);cpu.current_el=el;cpu.pstate=if el==ExceptionLevel::El0{0x3c0}else{0x3c5};cpu.sys.ttbr0_el1=step as u64;cpu.sys.tcr_el1=if sixteen{17|(2<<14)}else{16};cpu.sys.sctlr_el1=0x30d00803;cpu.sys.mair_el1=0x44;cpu.sync_mmu().unwrap();cpu.x[0]=10;
 let before=ram.clone();let result=cpu.execute_one(&mut RamBus{ram:&mut ram,base:0});let allowed=el==ExceptionLevel::El0||parent!=0;
 if allowed{assert_eq!(result,StepResult::Continue);assert_eq!((cpu.x[0],cpu.pc),(11,4));}else{assert!(matches!(result,StepResult::Exception(_)));assert_eq!((cpu.x[0],cpu.pc),(10,0));}assert_eq!(ram,before);
 }}}
}

#[test]fn hierarchy_reference_all_ap_and_xn_rows(){
 use crate::mmu::{VfMmu,Access,Fault};
 let rows=[[(true,false,false,true),(true,false,false,true),(false,false,false,true),(false,false,false,true)],[(true,true,true,false),(true,false,false,true),(false,true,false,true),(false,false,false,true)],[(false,false,false,true);4],[(false,true,false,true),(false,false,false,true),(false,true,false,true),(false,false,false,true)]];
 for sixteen in [false,true]{for upper in [false,true]{for ap in 0..4{for parent in 0..4{for xn in [0u64,1,2,4,8,5,10,15]{
 let step=if sixteen{0x4000u64}else{0x1000};let start=if sixteen{1}else{0};let tcr=if sixteen{17|(17<<16)|(2<<14)|(1<<30)}else{16|(16<<16)|(2<<30)};let va=if upper{!0u64<<(if sixteen{47}else{48})}else{0};
 let entries:Vec<(u64,u64)>=(start..=3).map(|l|{let pa=step*(l-start+1);(pa,if l==3{0x40000403|((ap as u64)<<6)|((u64::from(xn&1!=0))<<53)|((u64::from(xn&2!=0))<<54)}else{pa+step|3|if l==start{((parent as u64)<<61)|((u64::from(xn&4!=0))<<59)|((u64::from(xn&8!=0))<<60)}else{0}})}).collect();
 let mut mmu=VfMmu::disabled();assert!(mmu.configure_tcr(step,step,tcr,255));let(w,r0,w0,x1)=rows[ap][parent];
 for el in [ExceptionLevel::El1,ExceptionLevel::El0,ExceptionLevel::El1]{for access in [Access::Read,Access::Write,Access::Execute]{for _ in 0..2{
 let allowed=match (el,access){(ExceptionLevel::El0,Access::Read)=>r0,(ExceptionLevel::El0,Access::Write)=>w0,(ExceptionLevel::El0,Access::Execute)=>xn&10==0,(_,Access::Read)=>true,(_,Access::Write)=>w,(_,Access::Execute)=>x1&&xn&5==0};
 let result=mmu.translate(va,access,el,|pa|entries.iter().find(|e|e.0==pa).map(|e|e.1));assert_eq!(result.is_ok(),allowed,"ap{ap} parent{parent} xn{xn} {el:?} {access:?}");if !allowed{assert_eq!(result,Err(Fault::Permission));}assert_eq!(mmu.asid,255);
 }}}
 }}}}}
}
