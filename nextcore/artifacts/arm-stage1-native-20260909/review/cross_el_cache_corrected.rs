#[path="/home/sharh/work/bp32-ise-native-mmu/runtime/preos/src/exception_level.rs"] mod exception_level;
#[path="/home/sharh/work/bp32-ise-native-mmu/runtime/preos/src/mmu.rs"] mod mmu;
use mmu::{VfMmu,Access};use exception_level::ExceptionLevel::*;
fn tables(pa:u64)->Option<u64>{match pa{0x1000=>Some(0x2003),0x2000=>Some(0x3003),0x3000=>Some(0x4003),0x4000=>Some(0x8403),_=>None}}
fn main(){for strict in [false,true]{
let mut cold=VfMmu::disabled();let mut hot=VfMmu::disabled();
if strict{assert!(cold.configure_strict_nc(0x1000,0,16));assert!(hot.configure_strict_nc(0x1000,0,16));}else{assert!(cold.configure(0x1000,16,0));assert!(hot.configure(0x1000,16,0));}
let prime=hot.translate(0,Access::Execute,El0,tables);assert!(prime.is_ok());
let cw=cold.translate(8,Access::Write,El1,tables);
let hw=hot.translate(8,Access::Write,El1,|_|panic!("unexpected table reread"));
println!("strict={strict} cold_EL1_write={cw:?} after_EL0_fetch={hw:?}");assert_eq!(cw,hw);
}}
