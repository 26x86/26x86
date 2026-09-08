use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HalError {
    PatchLengthMismatch { expected: usize, actual: usize },
    PatchOutOfBounds { offset: usize, length: usize, dsdt_len: usize },
    Truncated { need: usize, have: usize },
    Invalid { reason: &'static str },
}

impl fmt::Display for HalError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            HalError::PatchLengthMismatch { expected, actual } => {
                write!(
                    f,
                    "Patch replace length mismatch: expected {} bytes, got {}",
                    expected, actual
                )
            }
            HalError::PatchOutOfBounds {
                offset,
                length,
                dsdt_len,
            } => {
                write!(
                    f,
                    "Patch out of bounds: offset={}, length={}, dsdt_size={}",
                    offset, length, dsdt_len
                )
            }
            HalError::Truncated { need, have } => {
                write!(f, "Buffer too short: need {} bytes, have {}", need, have)
            }
            HalError::Invalid { reason } => {
                write!(f, "Invalid firmware table: {}", reason)
            }
        }
    }
}

impl std::error::Error for HalError {}
