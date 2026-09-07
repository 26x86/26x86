use std::vec::Vec;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DecodeError {
    #[error("insufficient data at offset {0}")]
    InsufficientData(usize),
    #[error("invalid VEX prefix at offset {0}")]
    InvalidVexPrefix(usize),
    #[error("unsupported instruction")]
    Unsupported,
    #[error("bad ModRM at offset {0}")]
    BadModRm(usize),
}

pub type Result<T> = core::result::Result<T, DecodeError>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OperandSize {
    Size8,
    Size16,
    Size32,
    Size64,
    Size128,
    Size256,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OpcodeName {
    Add,
    Sub,
    Xor,
    And,
    Or,
    Mov,
    Cmp,
    Shl,
    Shr,
    Popcnt,
    Pclmulqdq,
    Pmovsxbw,
    Movdqa,
    Movdqu,
    VzeroUpper,
    Vaddps,
    Nop,
    Unknown,
}

#[derive(Debug, Clone)]
pub enum Operand {
    Register(u32),
    Immediate(u64),
    Memory(MemoryOperand),
}

#[derive(Debug, Clone)]
pub struct MemoryOperand {
    pub base: Option<u32>,
    pub index: Option<u32>,
    pub scale: u32,
    pub displacement: i64,
}

#[derive(Debug, Clone)]
pub struct DecodedInstruction {
    pub opcode: u32,
    pub name: OpcodeName,
    pub operand_size: OperandSize,
    pub operands: Vec<Operand>,
    pub is_avx: bool,
    pub is_sse4: bool,
    pub length: usize,
    pub reg_index: u32,
    pub rm_index: u32,
    pub memory: Option<MemoryOperand>,
}

pub struct InstructionDecoder;

impl InstructionDecoder {
    pub fn new() -> Self {
        Self
    }

    pub fn decode(data: &[u8], offset: usize) -> Result<DecodedInstruction> {
        if offset >= data.len() {
            return Err(DecodeError::InsufficientData(offset));
        }

        let first = data[offset];
        if first == 0xC5 {
            return Self::decode_vex2(data, offset);
        }
        if first == 0xC6 {
            return Self::decode_vex3(data, offset);
        }

        // Parse optional prefixes.
        let mut pos = offset;
        let mut rex = 0u8;
        let mut mandatory = 0u8; // 0x66, 0xF2, 0xF3
        loop {
            if pos >= data.len() {
                return Err(DecodeError::InsufficientData(pos));
            }
            let b = data[pos];
            if (0x40..=0x4F).contains(&b) {
                rex = b;
                pos += 1;
            } else if b == 0x66 || b == 0xF2 || b == 0xF3 {
                mandatory = b;
                pos += 1;
            } else {
                break;
            }
        }
        if pos >= data.len() {
            return Err(DecodeError::InsufficientData(pos));
        }

        let opcode = data[pos] as u32;
        pos += 1;

        let rex_w = (rex & 0x08) != 0;
        let rex_b = (rex & 0x01) != 0;
        let rex_r = (rex & 0x04) != 0;

        // 2-piece CRm reg/mem instructions: 0x01/0x03 ADD, 0x29/0x2B SUB,
        // 0x31/0x33 XOR, 0x21/0x23 AND, 0x09/0x0B OR, 0x39/0x3B CMP,
        // 0x89/0x8B MOV. Encoding: /r = ADD r/m, reg (src=modrm.reg, dst=modrm.rm)
        let table = match opcode {
            0x01 | 0x03 => Some(OpcodeName::Add),
            0x29 | 0x2B => Some(OpcodeName::Sub),
            0x31 | 0x33 => Some(OpcodeName::Xor),
            0x21 | 0x23 => Some(OpcodeName::And),
            0x09 | 0x0B => Some(OpcodeName::Or),
            0x39 | 0x3B => Some(OpcodeName::Cmp),
            0x89 | 0x8B => Some(OpcodeName::Mov),
            _ => None,
        };

        if let Some(name) = table {
            let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
            let size = if rex_w {
                OperandSize::Size64
            } else {
                OperandSize::Size32
            };
            let dst = Self::op_from_rm(rm, mem.as_ref());
            let operands = vec![dst, Operand::Register(reg)];
            return Ok(DecodedInstruction {
                opcode,
                name,
                operand_size: size,
                operands,
                is_avx: false,
                is_sse4: false,
                length: newpos - offset,
                reg_index: reg,
                rm_index: rm,
                memory: mem,
            });
        }

        // Immediate ALU forms 0x81 (imm32/64) and 0x83 (imm8 sign-extended).
        if opcode == 0x81 || opcode == 0x83 {
            let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
            let mut imm_len = if opcode == 0x83 {
                1
            } else if rex_w {
                8
            } else {
                4
            };
            let mut ip = newpos;
            if pos + 1 > data.len() {
                return Err(DecodeError::InsufficientData(pos));
            }
            // newpos points after modrm byte; immediate follows.
            let imm = if opcode == 0x83 {
                if ip >= data.len() {
                    return Err(DecodeError::InsufficientData(ip));
                }
                let v = data[ip] as i8 as i64 as u64;
                ip += 1;
                imm_len = 1;
                v
            } else {
                if rex_w {
                    if ip + 8 > data.len() {
                        return Err(DecodeError::InsufficientData(ip));
                    }
                    let v = u64::from_le_bytes(data[ip..ip + 8].try_into().unwrap());
                    ip += 8;
                    v
                } else {
                    if ip + 4 > data.len() {
                        return Err(DecodeError::InsufficientData(ip));
                    }
                    let v = u32::from_le_bytes(data[ip..ip + 4].try_into().unwrap()) as u64;
                    ip += 4;
                    v
                }
            };
            let _ = imm_len;
            let name = match reg {
                0 => OpcodeName::Add,
                5 => OpcodeName::Sub,
                1 => OpcodeName::Or,
                4 => OpcodeName::And,
                6 => OpcodeName::Xor,
                7 => OpcodeName::Cmp,
                _ => OpcodeName::Unknown,
            };
            let size = if rex_w {
                OperandSize::Size64
            } else {
                OperandSize::Size32
            };
            let dst = Self::op_from_rm(rm, mem.as_ref());
            let operands = if name == OpcodeName::Cmp {
                vec![dst, Operand::Immediate(imm)]
            } else {
                vec![dst, Operand::Immediate(imm)]
            };
            return Ok(DecodedInstruction {
                opcode,
                name,
                operand_size: size,
                operands,
                is_avx: false,
                is_sse4: false,
                length: ip - offset,
                reg_index: reg,
                rm_index: rm,
                memory: mem,
            });
        }

        // Shifts 0xD1 (imm=1) and 0xD3 (count=cl), 0xC1 (imm8).
        if opcode == 0xD1 || opcode == 0xC1 || opcode == 0xD3 {
            let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
            let count = if opcode == 0xC1 {
                let mut v = 0u64;
                let mut ip = newpos;
                if ip < data.len() {
                    v = data[ip] as u64 & 0x3F;
                    ip += 1;
                    let operands = vec![Self::op_from_rm(rm, mem.as_ref()), Operand::Immediate(v)];
                    return Ok(DecodedInstruction {
                        opcode,
                        name: if reg == 4 { OpcodeName::Shl } else { OpcodeName::Shr },
                        operand_size: OperandSize::Size32,
                        operands,
                        is_avx: false,
                        is_sse4: false,
                        length: ip - offset,
                        reg_index: reg,
                        rm_index: rm,
                        memory: mem,
                    });
                }
                0
            } else if opcode == 0xD1 {
                1
            } else {
                // D3: count in cl
                0
            };
            let name = if reg == 4 { OpcodeName::Shl } else { OpcodeName::Shr };
            let operands = vec![
                Self::op_from_rm(rm, mem.as_ref()),
                Operand::Immediate(count),
            ];
            return Ok(DecodedInstruction {
                opcode,
                name,
                operand_size: OperandSize::Size32,
                operands,
                is_avx: false,
                is_sse4: false,
                length: newpos - offset,
                reg_index: reg,
                rm_index: rm,
                memory: mem,
            });
        }

        // Two-byte opcode 0x0F
        if opcode == 0x0F {
            if pos >= data.len() {
                return Err(DecodeError::InsufficientData(pos));
            }
            let second = data[pos] as u32;
            pos += 1;
            match second {
                0xB8 => {
                    let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
                    let size = if rex_w {
                        OperandSize::Size64
                    } else {
                        OperandSize::Size32
                    };
                    let src = Self::op_from_rm(rm, mem.as_ref());
                    let operands = vec![Operand::Register(reg), src];
                    return Ok(DecodedInstruction {
                        opcode: 0xB8,
                        name: OpcodeName::Popcnt,
                        operand_size: size,
                        operands,
                        is_avx: false,
                        is_sse4: true,
                        length: newpos - offset,
                        reg_index: reg,
                        rm_index: rm,
                        memory: mem,
                    });
                }
                0x6F | 0x7F => {
                    let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
                    // 66 0F 6F = MOVDQA, F3 0F 6F = MOVDQU
                    let name = if mandatory == 0x66 {
                        OpcodeName::Movdqa
                    } else {
                        OpcodeName::Movdqu
                    };
                    let src = Self::op_from_rm(rm, mem.as_ref());
                    let operands = vec![Operand::Register(reg), src];
                    return Ok(DecodedInstruction {
                        opcode: second,
                        name,
                        operand_size: OperandSize::Size128,
                        operands,
                        is_avx: false,
                        is_sse4: false,
                        length: newpos - offset,
                        reg_index: reg,
                        rm_index: rm,
                        memory: mem,
                    });
                }
                0x38 => {
                    if pos >= data.len() {
                        return Err(DecodeError::InsufficientData(pos));
                    }
                    let third = data[pos] as u32;
                    pos += 1;
                    if third == 0x20 {
                        let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
                        let src = Self::op_from_rm(rm, mem.as_ref());
                        let operands = vec![Operand::Register(reg), src];
                        return Ok(DecodedInstruction {
                            opcode: third,
                            name: OpcodeName::Pmovsxbw,
                            operand_size: OperandSize::Size128,
                            operands,
                            is_avx: false,
                            is_sse4: true,
                            length: newpos - offset,
                            reg_index: reg,
                            rm_index: rm,
                            memory: mem,
                        });
                    }
                    return Err(DecodeError::Unsupported);
                }
                0x3A => {
                    if pos >= data.len() {
                        return Err(DecodeError::InsufficientData(pos));
                    }
                    let third = data[pos] as u32;
                    pos += 1;
                    if third == 0x44 {
                        let (reg, rm, mem, newpos) = Self::read_modrm(data, pos)?;
                        let mut ip = newpos;
                        let imm = if ip < data.len() {
                            let v = data[ip] as u64;
                            ip += 1;
                            v
                        } else {
                            0
                        };
                        let src = Self::op_from_rm(rm, mem.as_ref());
                        let operands = vec![Operand::Register(reg), src, Operand::Immediate(imm)];
                        return Ok(DecodedInstruction {
                            opcode: third,
                            name: OpcodeName::Pclmulqdq,
                            operand_size: OperandSize::Size128,
                            operands,
                            is_avx: false,
                            is_sse4: true,
                            length: ip - offset,
                            reg_index: reg,
                            rm_index: rm,
                            memory: mem,
                        });
                    }
                    return Err(DecodeError::Unsupported);
                }
                _ => return Err(DecodeError::Unsupported),
            }
        }

        match opcode {
            0x90 => Ok(DecodedInstruction {
                opcode,
                name: OpcodeName::Nop,
                operand_size: OperandSize::Size8,
                operands: vec![],
                is_avx: false,
                is_sse4: false,
                length: pos - offset,
                reg_index: 0,
                rm_index: 0,
                memory: None,
            }),
            _ => Err(DecodeError::Unsupported),
        }
    }

    fn op_from_rm(rm: u32, mem: Option<&MemoryOperand>) -> Operand {
        match mem {
            Some(m) => Operand::Memory(m.clone()),
            None => Operand::Register(rm),
        }
    }

    /// Returns (reg_index, rm_index, memory, position after full modrm+sib+disp).
    fn read_modrm(
        data: &[u8],
        pos: usize,
    ) -> Result<(u32, u32, Option<MemoryOperand>, usize)> {
        if pos >= data.len() {
            return Err(DecodeError::InsufficientData(pos));
        }
        let modrm = data[pos];
        let mode = (modrm >> 6) & 3;
        let rm = (modrm & 7) as u32;
        let reg = ((modrm >> 3) & 7) as u32;
        let mut newpos = pos + 1;

        if mode == 3 {
            return Ok((reg, rm, None, newpos));
        }

        let mut base = rm;
        let mut index = None;
        let mut scale = 1u32;
        let mut displacement = 0i64;

        // SIB byte for rm==4
        if rm == 4 {
            if newpos >= data.len() {
                return Err(DecodeError::InsufficientData(newpos));
            }
            let sib = data[newpos];
            newpos += 1;
            scale = (sib >> 6) as u32 + 1;
            let idx = ((sib >> 3) & 7) as u32;
            let mut bs = (sib & 7) as u32;
            if idx != 4 {
                index = Some(idx);
            }
            if mode == 0 && bs == 5 {
                // no base, disp32
                base = u32::MAX;
            }
        }

        if mode == 1 {
            if newpos >= data.len() {
                return Err(DecodeError::InsufficientData(newpos));
            }
            displacement = data[newpos] as i8 as i64;
            newpos += 1;
        } else if mode == 2 {
            if newpos + 4 > data.len() {
                return Err(DecodeError::InsufficientData(newpos));
            }
            displacement = i32::from_le_bytes(data[newpos..newpos + 4].try_into().unwrap()) as i64;
            newpos += 4;
        } else if mode == 0 {
            if rm == 5 && index.is_none() {
                if newpos + 4 > data.len() {
                    return Err(DecodeError::InsufficientData(newpos));
                }
                displacement = i32::from_le_bytes(data[newpos..newpos + 4].try_into().unwrap()) as i64;
                newpos += 4;
                base = u32::MAX;
            }
        }

        let memop = MemoryOperand {
            base: if base == u32::MAX { None } else { Some(base) },
            index,
            scale,
            displacement,
        };

        Ok((reg, rm, Some(memop), newpos))
    }

    fn decode_vex2(data: &[u8], offset: usize) -> Result<DecodedInstruction> {
        if offset + 2 >= data.len() {
            return Err(DecodeError::InsufficientData(offset));
        }
        let byte1 = data[offset + 1];
        let byte2 = data[offset + 2];
        let _r = (byte1 >> 7) & 1;
        let vvvv = ((data[offset + 1] >> 3) & 0xF) as u32;
        let l = (byte1 >> 2) & 1;
        let pp = byte1 & 3;

        let operand_size = if l == 1 {
            OperandSize::Size256
        } else {
            OperandSize::Size128
        };
        let vvvv = ((!vvvv) & 0xF) as u32;
        let reg = 0u32; // VEX.reg from opcode modrm if present; simplified

        let opcode = byte2 as u32;
        let name = if opcode == 0x77 {
            OpcodeName::VzeroUpper
        } else if opcode == 0x58 {
            OpcodeName::Vaddps
        } else {
            OpcodeName::Unknown
        };

        let operands = vec![Operand::Register(reg), Operand::Register(vvvv)];

        Ok(DecodedInstruction {
            opcode,
            name,
            operand_size,
            operands,
            is_avx: true,
            is_sse4: pp == 1,
            length: 3,
            reg_index: reg,
            rm_index: vvvv,
            memory: None,
        })
    }

    fn decode_vex3(data: &[u8], offset: usize) -> Result<DecodedInstruction> {
        if offset + 3 >= data.len() {
            return Err(DecodeError::InsufficientData(offset));
        }
        let byte1 = data[offset + 1];
        let byte2 = data[offset + 2];
        let byte3 = data[offset + 3];

        let _r = (byte1 >> 7) & 1;
        let _x = (byte1 >> 6) & 1;
        let vvvv = ((byte1 >> 3) & 0xF) as u32;
        let l = (byte1 >> 2) & 1;
        let pp = byte1 & 3;
        let _map = byte2;
        let _opcode = byte3 as u32;

        let vvvv = ((!vvvv) & 0xF) as u32;
        let operand_size = if l == 1 {
            OperandSize::Size256
        } else {
            OperandSize::Size128
        };

        Ok(DecodedInstruction {
            opcode: byte3 as u32,
            name: OpcodeName::Unknown,
            operand_size,
            operands: vec![Operand::Register(0), Operand::Register(vvvv)],
            is_avx: true,
            is_sse4: pp == 1,
            length: 4,
            reg_index: 0,
            rm_index: vvvv,
            memory: None,
        })
    }
}

impl Default for InstructionDecoder {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decode_add_reg_mem() {
        // 01 C8 = ADD eax, ecx
        let data = [0x01, 0xC8];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Add);
        assert_eq!(inst.reg_index, 1); // ecx src
        assert_eq!(inst.rm_index, 0); // eax dst
    }

    #[test]
    fn test_decode_mov() {
        // 89 C8 = MOV eax, ecx  (dst=rm=eax, src=reg=ecx)
        let data = [0x89, 0xC8];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Mov);
        assert_eq!(inst.rm_index, 0); // dst eax
        assert_eq!(inst.reg_index, 1); // src ecx
        match &inst.operands[0] {
            Operand::Register(r) => assert_eq!(*r, 0),
            _ => panic!("dst should be register"),
        }
        match &inst.operands[1] {
            Operand::Register(r) => assert_eq!(*r, 1),
            _ => panic!("src should be register"),
        }
    }

    #[test]
    fn test_decode_popcnt() {
        // F3 0F B8 C0 = POPCNT eax, eax
        let data = [0xF3, 0x0F, 0xB8, 0xC0];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Popcnt);
        assert!(inst.is_sse4);
    }

    #[test]
    fn test_decode_vex() {
        // C5 F8 77 = VZEROUPPER
        let data = [0xC5, 0xF8, 0x77];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert!(inst.is_avx);
        assert_eq!(inst.name, OpcodeName::VzeroUpper);
    }

    #[test]
    fn test_decode_shl() {
        // D1 E0 = SHL eax, 1
        let data = [0xD1, 0xE0];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Shl);
    }

    #[test]
    fn test_decode_xor() {
        // 31 C0 = XOR eax, eax
        let data = [0x31, 0xC0];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Xor);
    }

    #[test]
    fn test_decode_add_imm8() {
        // 83 C0 05 = ADD eax, 5
        let data = [0x83, 0xC0, 0x05];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Add);
        assert_eq!(inst.length, 3);
        match &inst.operands[1] {
            Operand::Immediate(v) => assert_eq!(*v, 5),
            _ => panic!("expected immediate"),
        }
    }

    #[test]
    fn test_decode_movdqa() {
        // 66 0F 6F C1 = MOVDQA xmm0, xmm1
        let data = [0x66, 0x0F, 0x6F, 0xC1];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Movdqa);
    }

    #[test]
    fn test_decode_nop() {
        let data = [0x90];
        let inst = InstructionDecoder::decode(&data, 0).unwrap();
        assert_eq!(inst.name, OpcodeName::Nop);
    }

    #[test]
    fn test_decode_unsupported() {
        let data = [0x0F, 0xAA];
        assert!(InstructionDecoder::decode(&data, 0).is_err());
    }
}
