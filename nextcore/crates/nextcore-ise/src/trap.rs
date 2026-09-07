use thiserror::Error;

use crate::decoder::DecodedInstruction;

#[derive(Error, Debug)]
pub enum TrapError {
    #[error("fatal trap: {0}")]
    Fatal(String),
    #[error("unsupported trap type")]
    UnsupportedTrap,
}

pub type Result<T> = core::result::Result<T, TrapError>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TrapType {
    InvalidOpcode,
    GeneralProtectionFault,
}

#[derive(Debug)]
pub enum TrapAction {
    Emulate(DecodedInstruction),
    Passthrough,
    Fatal(String),
}

pub struct TrapHandler;

impl TrapHandler {
    pub fn new() -> Self {
        Self
    }

    pub fn handle_trap(trap_type: TrapType, inst_bytes: &[u8]) -> Result<TrapAction> {
        match trap_type {
            TrapType::InvalidOpcode => Self::handle_invalid_opcode(inst_bytes),
            TrapType::GeneralProtectionFault => {
                Ok(TrapAction::Fatal("GP fault not recoverable".into()))
            }
        }
    }

    fn handle_invalid_opcode(inst_bytes: &[u8]) -> Result<TrapAction> {
        if inst_bytes.is_empty() {
            return Ok(TrapAction::Fatal("empty instruction bytes".into()));
        }

        let is_vex = inst_bytes[0] == 0xC5 || inst_bytes[0] == 0xC6;

        if is_vex {
            match crate::decoder::InstructionDecoder::decode(inst_bytes, 0) {
                Ok(inst) => Ok(TrapAction::Emulate(inst)),
                Err(_) => Ok(TrapAction::Fatal("failed to decode VEX instruction".into())),
            }
        } else {
            Ok(TrapAction::Passthrough)
        }
    }
}

impl Default for TrapHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_handle_vex_invalid_opcode() {
        let inst_bytes = [0xC5, 0xF1, 0x58];
        let result = TrapHandler::handle_trap(TrapType::InvalidOpcode, &inst_bytes);
        assert!(result.is_ok());
        match result.unwrap() {
            TrapAction::Emulate(inst) => assert!(inst.is_avx),
            _ => panic!("expected Emulate"),
        }
    }

    #[test]
    fn test_handle_gp_fault() {
        let result = TrapHandler::handle_trap(TrapType::GeneralProtectionFault, &[]);
        assert!(result.is_ok());
        assert!(matches!(result.unwrap(), TrapAction::Fatal(_)));
    }

    #[test]
    fn test_handle_non_vex_passthrough() {
        let inst_bytes = [0x90];
        let result = TrapHandler::handle_trap(TrapType::InvalidOpcode, &inst_bytes);
        assert!(result.is_ok());
        assert!(matches!(result.unwrap(), TrapAction::Passthrough));
    }
}
