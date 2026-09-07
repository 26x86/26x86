//! Nextcore APLS-Sandbox bridge: Apple Silicon boot mode, VSK policy, the
//! Golden Gate (macOS 27) graphics service-cell and the guest virtualization
//! boundary. Everything here fails closed: no config parse, envelope shape or
//! probe authorizes macOS boot.

pub mod mode;
pub mod sgpu;
pub mod vf_abi;
pub mod vf_policy;
pub mod guest;
pub mod runner;

pub const APLS_VERSION: &str = env!("CARGO_PKG_VERSION");
