#![cfg_attr(not(feature = "std"), no_std)]

extern crate alloc;

#[cfg(feature = "std")]
pub mod acpi;
pub mod boot_config;
#[cfg(feature = "std")]
pub mod config;
#[cfg(feature = "std")]
pub mod device_props;
#[cfg(feature = "std")]
pub mod error;
pub mod flat_dt;
#[cfg(feature = "std")]
pub mod handoff;
pub mod kc_staging;
pub mod kc_fixup_audit;
pub mod kc_classic_rebase;
pub mod kernel_collection;
#[cfg(feature = "std")]
pub mod kext;
#[cfg(feature = "macho")]
pub mod mach_o;
pub mod macho_image;
pub mod xnu_boot_args;

pub const VERSION: &str = env!("CARGO_PKG_VERSION");

pub fn version() -> &'static str {
    VERSION
}
