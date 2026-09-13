// Independent expected rows: leaf AP outer index, accumulated parent AP inner index.
// Tuple: EL1 write, EL0 read, EL0 write, EL1 execute; EL1 read and EL0 execute are true before XN.
const HP:[[(bool,bool,bool,bool);4];4]=[
 [(true,false,false,true),(true,false,false,true),(false,false,false,true),(false,false,false,true)],
 [(true,true,true,false),(true,false,false,true),(false,true,false,true),(false,false,false,true)],
 [(false,false,false,true);4],
 [(false,true,false,true),(false,false,false,true),(false,true,false,true),(false,false,false,true)]];
fn hp_allowed(ap:usize,parent:usize,el:u32,op:u32,pxn:bool,uxn:bool)->bool{
 let(w,r0,w0,x1)=HP[ap][parent];match(op,el){(FETCH,0)=>!uxn,(FETCH,_)=>x1&&!pxn,(LOAD,0)=>r0,(LOAD,_)=>true,(STORE,0)=>w0,_=>w}
}
fn hp_request(c:Controls,address:u64,el:u32,op:u32)->Request{
 Request{abi_version:2,struct_size:160,operation:op,width:if op==FETCH{4}else{8},count:1,current_el:el,pstate:if el==0{0x3c0}else{0x3c5},pc:address,address,controls:c,..Request::default()}
}
fn hp_fixture(sixteen:bool,profile:u32,level:usize,ancestor:usize,ap:usize,parent:usize,xn:u32,upper:bool)->(Controls,Vec<u8>,Vec<u8>,u64,u64,usize){
 let step=if sixteen{0x4000}else{0x1000};let start=if sixteen{1}else{0};let bits=if sixteen{11}else{9};let page=if sixteen{14}else{12};
 let mut tables=vec![0u8;step*4];let mut ram=vec![0x55u8;0x20000];let mut leaf=0;
 for l in start..=level{let at=(l-start)*step+(((VA>>(page+bits*(3-l)))&((1<<bits)-1))as usize)*8;
 let d=if l==level{leaf=at;RAM|0x400|(if level==3{3}else{1})|((ap as u64)<<6)|((u64::from(xn&1!=0))<<53)|((u64::from(xn&2!=0))<<54)}else{TABLES+((l-start+1)*step)as u64|3|if l==ancestor{((parent as u64)<<61)|((u64::from(xn&4!=0))<<59)|((u64::from(xn&8!=0))<<60)}else{0}};
 tables[at..at+8].copy_from_slice(&d.to_le_bytes());}
 let address=VA|if upper{!0u64<<(if sixteen{47}else{48})}else{0};let offset=if level==3{0}else{VA as usize};ram[offset..offset+4].copy_from_slice(&HLT.to_le_bytes());
 let tcr=if sixteen{17|(17<<16)|(2<<14)|(1<<30)|(5<<32)}else{16|(16<<16)|(2<<30)|(5<<32)};
 let c=Controls{abi_version:2,struct_size:80,profile,sctlr:if profile==1{0x30d00803}else{0x30d00801},ttbr0:TABLES|(127<<48),ttbr1:TABLES|(255<<48),tcr:tcr|(1<<22),mair:0x44,epoch:1,..Default::default()};(c,tables,ram,address,RAM+offset as u64,leaf)
}
#[test]fn hierarchy_complete_permissions_cold_warm_both_regimes(){
 let mut cases=0;let mut matrix=String::new();
 for sixteen in [false,true]{for profile in [1,3]{for upper in [false,true]{for level in (if sixteen{2}else{1})..=3{for ancestor in (if sixteen{1}else{0})..level{for ap in 0..4{for parent in 0..4{for xn in [0,1,2,4,8,5,10,15]{
 let(c,t,mut ram,va,pa,leaf)=hp_fixture(sixteen,profile,level,ancestor,ap,parent,xn,upper);
 let before=ram.clone();let mut svc=MemoryServiceV2::new(&mut ram,RAM,&t,TABLES,c).unwrap();
 // Reuse same cache across EL and operation changes; a denial does not poison later allowed access.
 for el in [1,0,1]{for op in [FETCH,LOAD,STORE]{for _ in 0..2{let mut q=hp_request(c,va,el,op);if op==STORE{q.value0=u64::from_le_bytes(before[(pa-RAM)as usize..(pa-RAM)as usize+8].try_into().unwrap());}
 let reply=svc.execute(&q);let allowed=hp_allowed(ap,parent,el,op,xn&5!=0,xn&10!=0);
 assert_eq!(reply.result,if allowed{OK}else{GUEST_FAULT},"16k{sixteen} profile{profile} L{level} ancestor{ancestor} ap{ap} parent{parent} xn{xn} EL{el} op{op}");
 if !allowed{let ec=if op==FETCH{0x20+el}else{0x24+el};assert_eq!((reply.fault,reply.level,reply.fsc,reply.address,reply.descriptor_pa,reply.output_pa),(PERMISSION,level as u32,12+level as u32,va,TABLES+leaf as u64,pa));assert_eq!(reply.esr,((ec as u64)<<26)|(1<<25)|(12+level as u64)|if op==STORE{64}else{0});}
 if profile==3 && !upper && level==3{matrix.push_str(&format!("{},{ancestor},{ap},{parent},{xn},{el},{op},{},{},{}\n",if sixteen{16384}else{4096},reply.result,reply.fault,reply.esr));}
 assert_eq!(svc.controls(),c);cases+=1;
 }}}
 drop(svc);assert_eq!(ram,before);
 }}}}}}}}
 let mut path=std::env::var_os("NEXTCORE_HIERARCHY_SNAPSHOT").unwrap();path.push(".matrix");std::fs::write(path,matrix).unwrap();
 println!("hierarchy_matrix_requests={cases}");
}
#[test]fn hierarchy_priority_and_split_ancestors(){
 for sixteen in [false,true]{for profile in [1,3]{let start=if sixteen{1}else{0};
 for failure in 0..4{let(mut c,mut t,mut ram,va,pa,leaf)=hp_fixture(sixteen,profile,3,start,1,3,12,false);let before=ram.clone();
 let word=match failure{0=>0,1=>(1u64<<40)|0x443,2=>RAM|0x43,_=>RAM|0x443};if failure==1{c.tcr=(c.tcr&!(7<<32))|(2<<32);}
 t[leaf..leaf+8].copy_from_slice(&word.to_le_bytes());
 let table_slice=if failure==3{&t[..leaf]}else{&t[..]};let mut svc=MemoryServiceV2::new(&mut ram,RAM,table_slice,TABLES,c).unwrap();let reply=svc.execute(&hp_request(c,va,0,STORE));
 if failure==3{assert_eq!(reply.result,UNAVAILABLE);}else{assert_eq!(reply.result,GUEST_FAULT);assert_eq!(reply.level,3);assert_eq!(reply.fault,match failure{0=>TRANSLATION,1=>ADDRESS_SIZE,_=>ACCESS_FLAG});}
 assert_eq!(reply.descriptor_pa,TABLES+leaf as u64);drop(svc);assert_eq!(ram,before);let _=pa;
 }
 // Distinct ancestors contribute independent restrictions rather than replacing an earlier one.
 let(c,mut t,mut ram,va,_,_)=hp_fixture(sixteen,profile,3,start,1,1,4,false);let step=if sixteen{0x4000}else{0x1000};let d=u64::from_le_bytes(t[step..step+8].try_into().unwrap())|(1<<62)|(1<<60);t[step..step+8].copy_from_slice(&d.to_le_bytes());
 let mut svc=MemoryServiceV2::new(&mut ram,RAM,&t,TABLES,c).unwrap();for(el,op)in[(0,LOAD),(0,FETCH),(1,STORE),(1,FETCH)]{assert_eq!(svc.execute(&hp_request(c,va,el,op)).fault,PERMISSION);}
 }}
}
#[test]fn hierarchy_native_fetch_uses_effective_permissions(){
 let mut snapshot=Vec::new();
 for sixteen in [false,true]{for profile in [1,3]{for upper in [false,true]{for el in [0,1]{for ap in 0..4{for parent in 0..4{for xn in [0,4,8]{
 let(c,t,mut ram,va,_,_)=hp_fixture(sixteen,profile,3,if sixteen{1}else{0},ap,parent,xn,upper);let before=ram.clone();
 let opts=platform::BootOptionsV2{abi_version:2,struct_size:64,initial_pstate:if el==0{0x3c0}else{0x3c5},..Default::default()};
 let(r,q)=run_with_options(c,&t,&mut ram,va,[11,22,33,44],0,Some(&opts));let b=r.base.execution.base;let allow=hp_allowed(ap,parent,el,FETCH,xn&5!=0,xn&10!=0);
 assert_eq!(b.retired,if allow{1}else{0});assert_eq!(b.status,if allow{1}else{16});assert_eq!((b.x0,b.x1,b.x2,b.x3),(11,22,33,44));assert_eq!(ram,before);assert_eq!(q.len(),1);assert_eq!(q[0].current_el,el);assert_eq!(q[0].controls,c);
 snapshot.extend_from_slice(unsafe{core::slice::from_raw_parts((&r as *const Run).cast::<u8>(),core::mem::size_of::<Run>())});
 }}}}}}}
 std::fs::write(std::env::var_os("NEXTCORE_HIERARCHY_SNAPSHOT").unwrap(),snapshot).unwrap();
}

// Give code a separate, unrestricted ancestor chain in the opposite VA half.
fn hp_code(sixteen:bool,c:&mut Controls,t:&mut Vec<u8>,ram:&mut [u8],upper_data:bool,words:&[u32])->u64{
 let step=if sixteen{0x4000}else{0x1000};let start=if sixteen{1}else{0};let bits=if sixteen{11}else{9};let page=if sixteen{14}else{12};let base=t.len();t.resize(base+4*step,0);
 for l in start..=3{let at=base+(l-start)*step+(((VA>>(page+bits*(3-l)))&((1<<bits)-1))as usize)*8;let d=if l==3{RAM+0x18000|0x403}else{TABLES+(base+(l-start+1)*step)as u64|3};t[at..at+8].copy_from_slice(&d.to_le_bytes());}
 if upper_data{c.ttbr0=TABLES+base as u64|(127<<48);}else{c.ttbr1=TABLES+base as u64|(255<<48);}
 for(i,w)in words.iter().enumerate(){ram[0x18000+4*i..0x18004+4*i].copy_from_slice(&w.to_le_bytes());}
 VA|if upper_data{0}else{!0u64<<(if sixteen{47}else{48})}
}
#[test]fn hierarchy_native_data_matrix_and_pair_failure_are_transactional(){
 let mut cases=0;let mut snapshots=Vec::new();
 for sixteen in [false,true]{for profile in [1,3]{for upper in [false,true]{for el in [0,1]{for ap in 0..4{for parent in 0..4{for load in [false,true]{
 let(mut c,mut t,mut ram,va,_,_)=hp_fixture(sixteen,profile,3,if sixteen{1}else{0},ap,parent,0,upper);
 let entry=hp_code(sixteen,&mut c,&mut t,&mut ram,upper,&[scalar(3,u32::from(load),1,0),HLT]);let before=ram.clone();let opts=platform::BootOptionsV2{abi_version:2,struct_size:64,initial_pstate:if el==0{0x3c0}else{0x3c5},..Default::default()};
 let(r,q)=run_with_options(c,&t,&mut ram,entry,[0x11223344,va,22,33],0,Some(&opts));let b=r.base.execution.base;let allow=hp_allowed(ap,parent,el,if load{LOAD}else{STORE},false,false);
 assert_eq!((b.status,b.retired),(if allow{1}else{17},if allow{2}else{0}));assert_eq!((b.x1,b.x2,b.x3),(va,22,33));assert_eq!(b.x0,if load&&allow{u64::from_le_bytes(before[..8].try_into().unwrap())}else{0x11223344});
 let mut expected=before.clone();if !load&&allow{expected[..8].copy_from_slice(&0x11223344u64.to_le_bytes());}assert_eq!(ram,expected);assert_eq!(q.len(),if allow{3}else{2});assert_eq!(q[1].operation,if load{LOAD}else{STORE});assert_eq!(q[1].controls,c);hp_snapshot(&mut snapshots,&r,&q);cases+=1;
 }}}}}}}
 // The first pair word is writable; only the second crosses into a different RO ancestor.
 for sixteen in [false,true]{for profile in [1,3]{for upper in [false,true]{for load in [false,true]{
 let step=if sixteen{0x4000usize}else{0x1000};let start=if sixteen{1}else{0};let(mut c,mut t,mut ram,_,_,old_leaf)=hp_fixture(sixteen,profile,3,start,1,0,0,upper);
 t[old_leaf..old_leaf+8].fill(0);let last=(3-start)*step+step-8;t[last..last+8].copy_from_slice(&(RAM|0x443).to_le_bytes());
 let extra=t.len();t.resize(extra+step,0);t[extra..extra+8].copy_from_slice(&(RAM+step as u64|0x443).to_le_bytes());let next_parent=(2-start)*step+8;t[next_parent..next_parent+8].copy_from_slice(&(TABLES+extra as u64|3|(1<<62)).to_le_bytes());
 let boundary=(step*step/8)as u64;let va=boundary-8|if upper{!0u64<<(if sixteen{47}else{48})}else{0};
 let entry=hp_code(sixteen,&mut c,&mut t,&mut ram,upper,&[pair(true,load,1,2,1,0,2),HLT]);let before=ram.clone();
 // Reads are denied by no-EL0 data permission in the second ancestor; stores by RO.
 if load{let d=u64::from_le_bytes(t[next_parent..next_parent+8].try_into().unwrap())|(1<<61);t[next_parent..next_parent+8].copy_from_slice(&d.to_le_bytes());}
 let opts=platform::BootOptionsV2{abi_version:2,struct_size:64,initial_pstate:if load{0x3c0}else{0x3c5},..Default::default()};
 let(r,q)=run_with_options(c,&t,&mut ram,entry,[11,va,22,33],0,Some(&opts));let b=r.base.execution.base;
 assert_eq!((b.status,b.retired,b.pc,b.x0,b.x1,b.x2,b.x3),(17,0,entry,11,va,22,33));assert_eq!(ram,before);assert_eq!(q.len(),2);assert_eq!((q[1].width,q[1].count,q[1].address),(8,2,va));assert_eq!(r.base.guest_far,va+8);assert_eq!(r.base.execution.esr&0x7f,15|if load{0}else{64});hp_snapshot(&mut snapshots,&r,&q);
 }}}}
 let mut path=std::env::var_os("NEXTCORE_HIERARCHY_SNAPSHOT").unwrap();path.push(".data");std::fs::write(path,snapshots).unwrap();
 println!("hierarchy_native_data_cases={cases}");
}

fn hp_snapshot(bytes:&mut Vec<u8>,result:&Run,requests:&[Request]){
 bytes.extend_from_slice(unsafe{core::slice::from_raw_parts((result as *const Run).cast::<u8>(),core::mem::size_of::<Run>())});
 bytes.extend_from_slice(&(requests.len()as u64).to_le_bytes());
 for q in requests{bytes.extend_from_slice(unsafe{core::slice::from_raw_parts((q as *const Request).cast::<u8>(),core::mem::size_of::<Request>())});}
}
