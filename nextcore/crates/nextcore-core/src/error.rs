use thiserror::Error;

#[derive(Debug, Error)]
pub enum CoreError {
    #[error("plist parse error: {0}")]
    Plist(#[from] plist::Error),

    #[error("config validation failed: {0}")]
    ConfigValidation(String),

    #[error("ACPI table not found: {0}")]
    AcpiNotFound(&'static str),

    #[error("ACPI table invalid: {0}")]
    AcpiInvalid(&'static str),

    #[error("kext scan error: {0}")]
    KextScan(String),

    #[error("kext Info.plist parse error: {0}")]
    KextPlist(String),

    #[error("device properties error: {0}")]
    DeviceProps(String),

    #[error("handoff error: {0}")]
    Handoff(String),

    #[error("mach-o parse error: {0}")]
    MachO(String),

    #[error("mach-o not found")]
    MachONotFound,

    #[error("buffer too short: need {need} bytes, have {have}")]
    BufferTooShort { need: usize, have: usize },

    #[error("invalid magic: expected 0x{expected:x}, got 0x{got:x}")]
    InvalidMagic { expected: u32, got: u32 },
}

pub type Result<T> = core::result::Result<T, CoreError>;
