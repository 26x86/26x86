use thiserror::Error;

use crate::decoder::{DecodedInstruction, OpcodeName, Operand};

#[derive(Error, Debug)]
pub enum EmulatorError {
    #[error("unsupported instruction: opcode {0:#x}")]
    UnsupportedInstruction(u32),
    #[error("invalid register index: {0}")]
    InvalidRegister(u32),
    #[error("division by zero")]
    DivisionByZero,
    #[error("unsupported instruction name")]
    UnsupportedName,
    #[error("memory not supported in emulator")]
    MemoryUnsupported,
}

pub type Result<T> = core::result::Result<T, EmulatorError>;

#[derive(Debug, Clone)]
pub struct Registers {
    pub rax: u64,
    pub rbx: u64,
    pub rcx: u64,
    pub rdx: u64,
    pub rsi: u64,
    pub rdi: u64,
    pub rsp: u64,
    pub rbp: u64,
    pub r8: u64,
    pub r9: u64,
    pub r10: u64,
    pub r11: u64,
    pub r12: u64,
    pub r13: u64,
    pub r14: u64,
    pub r15: u64,
    pub xmm: [u128; 16],
    pub ymm: [u128; 16],
    pub rflags: u64,
}

const FLAG_CF: u64 = 1 << 0;
const FLAG_ZF: u64 = 1 << 6;
const FLAG_SF: u64 = 1 << 7;
const FLAG_OF: u64 = 1 << 11;

impl Default for Registers {
    fn default() -> Self {
        Self::new()
    }
}

impl Registers {
    pub fn new() -> Self {
        Self {
            rax: 0, rbx: 0, rcx: 0, rdx: 0,
            rsi: 0, rdi: 0, rsp: 0, rbp: 0,
            r8: 0, r9: 0, r10: 0, r11: 0,
            r12: 0, r13: 0, r14: 0, r15: 0,
            xmm: [0u128; 16],
            ymm: [0u128; 16],
            rflags: 0,
        }
    }

    pub fn get_gpr(&self, index: u32) -> Result<u64> {
        match index {
            0 => Ok(self.rax),
            1 => Ok(self.rcx),
            2 => Ok(self.rdx),
            3 => Ok(self.rbx),
            4 => Ok(self.rsp),
            5 => Ok(self.rbp),
            6 => Ok(self.rsi),
            7 => Ok(self.rdi),
            8 => Ok(self.r8),
            9 => Ok(self.r9),
            10 => Ok(self.r10),
            11 => Ok(self.r11),
            12 => Ok(self.r12),
            13 => Ok(self.r13),
            14 => Ok(self.r14),
            15 => Ok(self.r15),
            _ => Err(EmulatorError::InvalidRegister(index)),
        }
    }

    pub fn set_gpr(&mut self, index: u32, value: u64) -> Result<()> {
        match index {
            0 => self.rax = value,
            1 => self.rcx = value,
            2 => self.rdx = value,
            3 => self.rbx = value,
            4 => self.rsp = value,
            5 => self.rbp = value,
            6 => self.rsi = value,
            7 => self.rdi = value,
            8 => self.r8 = value,
            9 => self.r9 = value,
            10 => self.r10 = value,
            11 => self.r11 = value,
            12 => self.r12 = value,
            13 => self.r13 = value,
            14 => self.r14 = value,
            15 => self.r15 = value,
            _ => return Err(EmulatorError::InvalidRegister(index)),
        }
        Ok(())
    }

    pub fn get_xmm(&self, index: u32) -> Result<u128> {
        if index < 16 {
            Ok(self.xmm[index as usize])
        } else {
            Err(EmulatorError::InvalidRegister(index))
        }
    }

    pub fn set_xmm(&mut self, index: u32, value: u128) -> Result<()> {
        if index < 16 {
            self.xmm[index as usize] = value;
            Ok(())
        } else {
            Err(EmulatorError::InvalidRegister(index))
        }
    }
}

pub struct Emulator;

#[derive(Clone, Copy)]
enum BinOp {
    Add,
    Sub,
    Xor,
    And,
    Or,
}

impl Emulator {
    pub fn new() -> Self {
        Self
    }

    pub fn emulate_ise(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        match inst.name {
            OpcodeName::Add => Self::emulate_binary(inst, regs, BinOp::Add),
            OpcodeName::Sub => Self::emulate_binary(inst, regs, BinOp::Sub),
            OpcodeName::Xor => Self::emulate_binary(inst, regs, BinOp::Xor),
            OpcodeName::And => Self::emulate_binary(inst, regs, BinOp::And),
            OpcodeName::Or => Self::emulate_binary(inst, regs, BinOp::Or),
            OpcodeName::Mov => Self::emulate_mov(inst, regs),
            OpcodeName::Cmp => Self::emulate_cmp(inst, regs),
            OpcodeName::Shl => Self::emulate_shift(inst, regs, true),
            OpcodeName::Shr => Self::emulate_shift(inst, regs, false),
            OpcodeName::Popcnt => Self::emulate_popcnt(inst, regs),
            OpcodeName::Pclmulqdq => Self::emulate_pclmulqdq(inst, regs),
            OpcodeName::Pmovsxbw => Self::emulate_pmovsxbw(inst, regs),
            OpcodeName::Movdqa | OpcodeName::Movdqu => Self::emulate_mov_xmm(inst, regs),
            OpcodeName::VzeroUpper => Self::emulate_vzeroupper(regs),
            OpcodeName::Vaddps => Self::emulate_vaddps(inst, regs),
            OpcodeName::Nop => Ok(()),
            OpcodeName::Unknown => Err(EmulatorError::UnsupportedName),
        }
    }

    fn read_operand(inst: &DecodedInstruction, regs: &Registers, which: usize) -> Result<u64> {
        match inst.operands.get(which) {
            Some(Operand::Register(r)) => regs.get_gpr(*r),
            Some(Operand::Immediate(v)) => Ok(*v),
            Some(Operand::Memory(_)) => Err(EmulatorError::MemoryUnsupported),
            None => Ok(0),
        }
    }

    fn write_dst(inst: &DecodedInstruction, regs: &mut Registers, which: usize, value: u64) -> Result<()> {
        match inst.operands.get(which) {
            Some(Operand::Register(r)) => regs.set_gpr(*r, value),
            Some(Operand::Memory(_)) => Err(EmulatorError::MemoryUnsupported),
            Some(Operand::Immediate(_)) | None => Err(EmulatorError::UnsupportedName),
        }
    }

    fn emulate_mov(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let host = Self::read_operand(inst, regs, 1)?;
        Self::write_dst(inst, regs, 0, host)
    }

    fn emulate_binary(inst: &DecodedInstruction, regs: &mut Registers, op: BinOp) -> Result<()> {
        let lhs = Self::read_operand(inst, regs, 0)?;
        let rhs = Self::read_operand(inst, regs, 1)?;
        let (result, cf, of, zf, sf) = match op {
            BinOp::Add => {
                let (r, cf) = lhs.overflowing_add(rhs);
                let of = ((lhs ^ rhs) & !(lhs ^ r) & (1 << 63)) != 0;
                (r, cf, of, r == 0, (r >> 63) & 1 == 1)
            }
            BinOp::Sub => {
                let (r, cf) = lhs.overflowing_sub(rhs);
                let of = ((lhs ^ rhs) & (lhs ^ r) & (1 << 63)) != 0;
                (r, cf, of, r == 0, (r >> 63) & 1 == 1)
            }
            BinOp::Xor => {
                let r = lhs ^ rhs;
                (r, false, false, r == 0, (r >> 63) & 1 == 1)
            }
            BinOp::And => {
                let r = lhs & rhs;
                (r, false, false, r == 0, (r >> 63) & 1 == 1)
            }
            BinOp::Or => {
                let r = lhs | rhs;
                (r, false, false, r == 0, (r >> 63) & 1 == 1)
            }
        };
        Self::write_dst(inst, regs, 0, result)?;
        Self::update_flags(regs, cf, zf, sf, of);
        Ok(())
    }

    fn emulate_cmp(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let lhs = Self::read_operand(inst, regs, 0)?;
        let rhs = Self::read_operand(inst, regs, 1)?;
        let (r, cf) = lhs.overflowing_sub(rhs);
        let of = ((lhs ^ rhs) & (lhs ^ r) & (1 << 63)) != 0;
        Self::update_flags(regs, cf, r == 0, (r >> 63) & 1 == 1, of);
        Ok(())
    }

    fn emulate_shift(inst: &DecodedInstruction, regs: &mut Registers, left: bool) -> Result<()> {
        let value = Self::read_operand(inst, regs, 0)?;
        let count = Self::read_operand(inst, regs, 1)? as u32 & 0x3F;

        let (result, cf) = if left {
            if count == 0 {
                (value, false)
            } else {
                let cf = (value >> (64 - count)) & 1 == 1;
                (value << count, cf)
            }
        } else {
            if count == 0 {
                (value, false)
            } else {
                let cf = (value >> (count - 1)) & 1 == 1;
                (value >> count, cf)
            }
        };

        Self::write_dst(inst, regs, 0, result)?;
        Self::update_flags(regs, cf, result == 0, (result >> 63) & 1 == 1, false);
        Ok(())
    }

    fn update_flags(regs: &mut Registers, cf: bool, zf: bool, sf: bool, of: bool) {
        regs.rflags &= !(FLAG_CF | FLAG_ZF | FLAG_SF | FLAG_OF);
        if cf {
            regs.rflags |= FLAG_CF;
        }
        if zf {
            regs.rflags |= FLAG_ZF;
        }
        if sf {
            regs.rflags |= FLAG_SF;
        }
        if of {
            regs.rflags |= FLAG_OF;
        }
    }

    fn emulate_popcnt(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let src = Self::read_operand(inst, regs, 1)?;
        let result = src.count_ones() as u64;
        Self::write_dst(inst, regs, 0, result)?;

        regs.rflags &= !(FLAG_CF | FLAG_OF | FLAG_SF | FLAG_ZF);
        if result == 0 {
            regs.rflags |= FLAG_ZF;
        }
        Ok(())
    }

    fn emulate_vzeroupper(regs: &mut Registers) -> Result<()> {
        for reg in regs.ymm.iter_mut() {
            *reg = 0;
        }
        Ok(())
    }

    fn emulate_vaddps(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let count = if inst.operand_size == crate::decoder::OperandSize::Size256 {
            8
        } else {
            4
        };
        let dst = inst.reg_index;
        let src = inst.rm_index;
        let a = regs.get_xmm(dst)?;
        let b = if let Some(Operand::Register(r)) = inst.operands.get(1) {
            regs.get_xmm(*r)?
        } else {
            regs.get_xmm(src)?
        };
        let mut out = [0u32; 8];
        for i in 0..count {
            let ai = f32::from_bits(((a >> (i * 32)) & 0xFFFFFFFF) as u32);
            let bi = f32::from_bits(((b >> (i * 32)) & 0xFFFFFFFF) as u32);
            out[i] = (ai + bi).to_bits();
        }
        let mut result = 0u128;
        for i in 0..count {
            result |= (out[i] as u128) << (i * 32);
        }
        regs.set_xmm(dst, result)?;
        Ok(())
    }

    fn emulate_mov_xmm(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let dst = inst.reg_index;
        let src = inst.rm_index;
        let v = regs.get_xmm(src)?;
        regs.set_xmm(dst, v)
    }

    fn emulate_pmovsxbw(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let dst = inst.reg_index;
        let src = inst.rm_index;
        let s = regs.get_xmm(src)?;
        let mut result = 0u128;
        for i in 0..8 {
            let byte = ((s >> (i * 8)) & 0xFF) as i8;
            let word = byte as u16;
            result |= (word as u128) << (i * 16);
        }
        regs.set_xmm(dst, result)
    }

    fn emulate_pclmulqdq(inst: &DecodedInstruction, regs: &mut Registers) -> Result<()> {
        let dst = inst.reg_index;
        let src = inst.rm_index;
        let imm = match inst.operands.last() {
            Some(Operand::Immediate(v)) => *v,
            _ => 0,
        };
        let src_lane = (imm & 1) as usize;
        let dst_lane = ((imm >> 4) & 1) as usize;
        let a = regs.get_xmm(dst)?;
        let b = regs.get_xmm(src)?;
        let a_lo = (a >> (dst_lane * 64)) & 0xFFFF_FFFF_FFFF_FFFF;
        let b_lo = (b >> (src_lane * 64)) & 0xFFFF_FFFF_FFFF_FFFF;
        let product = a_lo * b_lo;
        regs.set_xmm(dst, product)
    }
}

impl Default for Emulator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::decoder::{InstructionDecoder, OperandSize};

    fn dec(data: &[u8]) -> DecodedInstruction {
        InstructionDecoder::decode(data, 0).unwrap()
    }

    #[test]
    fn test_vzeroupper() {
        let mut regs = Registers::new();
        regs.ymm[0] = 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF;
        let inst = dec(&[0xC5, 0xF8, 0x77]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.ymm[0], 0);
    }

    #[test]
    fn test_popcnt_gpr() {
        let mut regs = Registers::new();
        regs.rax = 0xFF;
        // F3 0F B8 C0: POPCNT eax, eax
        let inst = dec(&[0xF3, 0x0F, 0xB8, 0xC0]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 8);
    }

    #[test]
    fn test_xor_reg() {
        let mut regs = Registers::new();
        regs.rax = 0xAAAA_AAAA_AAAA_AAAA;
        // 31 C0: XOR eax, eax
        let inst = dec(&[0x31, 0xC0]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 0);
        assert_ne!(regs.rflags & FLAG_ZF, 0);
    }

    #[test]
    fn test_add_reg() {
        let mut regs = Registers::new();
        regs.rax = 5;
        regs.rcx = 3;
        // 01 C8: ADD eax, ecx
        let inst = dec(&[0x01, 0xC8]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 8);
    }

    #[test]
    fn test_add_imm() {
        let mut regs = Registers::new();
        regs.rax = 10;
        // 83 C0 05: ADD eax, 5
        let inst = dec(&[0x83, 0xC0, 0x05]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 15);
    }

    #[test]
    fn test_cmp_flags() {
        let mut regs = Registers::new();
        regs.rax = 5;
        regs.rcx = 5;
        // 39 C8: CMP eax, ecx
        let inst = dec(&[0x39, 0xC8]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_ne!(regs.rflags & FLAG_ZF, 0);
        // rax unchanged
        assert_eq!(regs.rax, 5);
    }

    #[test]
    fn test_mov() {
        let mut regs = Registers::new();
        regs.rcx = 0x1234;
        // 89 C8: MOV eax, ecx
        let inst = dec(&[0x89, 0xC8]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 0x1234);
    }

    #[test]
    fn test_shl_imm() {
        let mut regs = Registers::new();
        regs.rax = 1;
        // D1 E0: SHL eax, 1
        let inst = dec(&[0xD1, 0xE0]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 2);
    }

    #[test]
    fn test_and_imm() {
        let mut regs = Registers::new();
        regs.rax = 0xFFFF;
        // 83 E0 0F: AND eax, 0x0F
        let inst = dec(&[0x83, 0xE0, 0x0F]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        assert_eq!(regs.rax, 0x0F);
    }

    #[test]
    fn test_vaddps_simple() {
        let mut regs = Registers::new();
        regs.set_xmm(0, (1.0f32).to_bits() as u128).unwrap();
        regs.set_xmm(1, (2.0f32).to_bits() as u128).unwrap();
        // C5 F0 58 C1: VADDPS xmm0, xmm1, xmm0
        let inst = dec(&[0xC5, 0xF0, 0x58, 0xC1]);
        Emulator::emulate_ise(&inst, &mut regs).unwrap();
        let lo = regs.get_xmm(0).unwrap() as u32;
        assert_eq!(lo, (3.0f32).to_bits());
    }

    #[test]
    fn test_sub_mem_unsupported() {
        let mut regs = Registers::new();
        // 2B 05 00 00 00 00 : SUB eax, [rip+0]
        let inst = dec(&[0x2B, 0x05, 0x00, 0x00, 0x00, 0x00]);
        assert!(Emulator::emulate_ise(&inst, &mut regs).is_err());
    }
}
