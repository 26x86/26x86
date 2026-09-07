use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HalError {
    PatchLengthMismatch { expected: usize, actual: usize },
    PatchOutOfBounds { offset: usize, length: usize, dsdt_len: usize },
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
        }
    }
}

impl std::error::Error for HalError {}
