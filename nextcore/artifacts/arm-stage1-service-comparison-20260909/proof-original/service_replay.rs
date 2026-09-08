use nextcore_memory_service::{abi_v2::*,stage1::MemoryServiceV2};
include!("cases.rs");
fn put(bytes:&mut[u8],offset:usize,value:u64){bytes[offset..offset+8].copy_from_slice(&value.to_le_bytes());}
fn main(){for c in CASES {
 let mut tables=vec![0u8;0x20000];let mut ram=vec![0u8;0x10000];
 for i in 0..4{put(&mut tables,i*0x4000,c.tables[i]);}
 put(&mut tables,3*0x4000+8,c.second);
 if c.granule==4096{put(&mut tables,0x10000,CODE_BASE+0x4000|3);put(&mut tables,0x14000+8,0x400004c1);}
 else{put(&mut tables,0x14000,CODE_BASE+0x8000|3);put(&mut tables,0x18000+32*8,0x400004c1);}
 if c.op==1{ram[0x230..0x234].copy_from_slice(&0xd65f03c0u32.to_le_bytes());}
 let before=ram.clone();
 let controls=Controls{abi_version:2,struct_size:80,profile:1,epoch:1,sctlr:c.sctlr,ttbr0:c.ttbr0,ttbr1:c.ttbr1,tcr:c.tcr,mair:c.mair,hcr:0,scr:0,reserved:0};
 let q=Request{abi_version:2,struct_size:160,operation:c.op,width:c.width,count:c.count,current_el:c.el,pc:c.pc,address:c.va,pstate:c.pstate,controls,..Request::default()};
 let r=MemoryServiceV2::new(&mut ram,RAM_BASE,&tables,TABLE_BASE,controls).unwrap().execute(&q);
 println!("{} {} {} {} {} {} {} {} {} {}",c.name,r.result,r.fault,r.level,r.fsc,r.esr,r.address,r.value0,r.value1,u32::from(ram==before));
}}
