use thiserror::Error;

/// Wire constants and the 64-byte message envelope for the VSK service-cell
/// ABI (VF-SPEC-001 v0.1 section 16). The layout mirrors `sandbox/vsk/include/vf_abi.h`
/// `struct vf_msg_header`: a known namespace/opcode never implies an implemented
/// operation. All decode is copy-in little-endian; this layer never dereferences
/// a reported physical address and never authenticates a caller.

pub const VF_MSG_MAGIC: u32 = 0x314D_4656;
pub const VF_ABI_MAJOR: u16 = 1;
pub const VF_MSG_BYTES: u32 = 64;
pub const VF_PAYLOAD_MAX: u32 = 16_777_216;

pub const VF_FAMILY_ROOT: u16 = 1;
pub const VF_FAMILY_BLOCK: u16 = 2;
pub const VF_FAMILY_SGPU: u16 = 3;

pub const VF_OP_CAP_DUP_RESTRICTED: u16 = 1;
pub const VF_OP_GRANT_CREATE: u16 = 2;
pub const VF_OP_GRANT_REVOKE: u16 = 3;
pub const VF_OP_CELL_NOTIFY: u16 = 4;
pub const VF_OP_DEVICE_MAP_MMIO: u16 = 5;
pub const VF_OP_DEVICE_DMA_MAP: u16 = 6;
pub const VF_OP_DEVICE_DMA_UNMAP: u16 = 7;
pub const VF_OP_DEVICE_IRQ_BIND: u16 = 8;
pub const VF_OP_DEVICE_QUIESCE_RESET: u16 = 9;

pub const VF_BLOCK_READ: u16 = 1;
pub const VF_BLOCK_WRITE: u16 = 2;
pub const VF_BLOCK_FLUSH: u16 = 3;

pub const VF_SGPU_QUERY_CAPS: u16 = 1;
pub const VF_SGPU_CREATE_RESOURCE: u16 = 2;
pub const VF_SGPU_DESTROY_RESOURCE: u16 = 3;
pub const VF_SGPU_CREATE_PIPELINE: u16 = 4;
pub const VF_SGPU_SUBMIT_COMMAND_LIST: u16 = 5;
pub const VF_SGPU_QUERY_OR_WAIT_TIMELINE: u16 = 6;
pub const VF_SGPU_PRESENT: u16 = 7;

#[derive(Debug, Error, Clone, Copy, PartialEq, Eq)]
pub enum VfError {
    #[error("invalid argument")]
    Einval,
    #[error("ABI mismatch: {0}")]
    Eabi(&'static str),
    #[error("operation not supported")]
    Enotsup,
    #[error("capability or grant denied")]
    Eperm,
    #[error("out of range")]
    Erange,
    #[error("busy")]
    Ebusy,
    #[error("object not found")]
    Enoent,
}

pub type Result<T> = core::result::Result<T, VfError>;

/// 64-byte VSK message envelope, byte-for-byte compatible with
/// `vf_msg_header` in `sandbox/vsk/include/vf_abi.h`.
#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VfMsgHeader {
    pub magic: u32,
    pub abi_major: u16,
    pub header_bytes: u16,
    pub message_bytes: u32,
    pub family: u16,
    pub opcode: u16,
    pub request_id: u64,
    pub object: u64,
    pub payload_grant: u64,
    pub payload_offset: u64,
    pub payload_bytes: u32,
    pub flags: u32,
    pub reserved0: u64,
}

impl Default for VfMsgHeader {
    fn default() -> Self {
        Self {
            magic: VF_MSG_MAGIC,
            abi_major: VF_ABI_MAJOR,
            header_bytes: VF_MSG_BYTES as u16,
            message_bytes: VF_MSG_BYTES,
            family: 0,
            opcode: 0,
            request_id: 0,
            object: 0,
            payload_grant: 0,
            payload_offset: 0,
            payload_bytes: 0,
            flags: 0,
            reserved0: 0,
        }
    }
}

impl VfMsgHeader {
    pub const SIZE: usize = 64;

    pub fn new(family: u16, opcode: u16) -> Self {
        let mut h = Self::default();
        h.family = family;
        h.opcode = opcode;
        h
    }

    /// Copy-in little-endian decode. Requires exactly 64 bytes.
    pub fn decode(bytes: &[u8]) -> Result<Self> {
        if bytes.len() != Self::SIZE {
            return Err(VfError::Erange);
        }
        let mut h = Self::default();
        h.magic = u32::from_le_bytes(bytes[0..4].try_into().unwrap());
        h.abi_major = u16::from_le_bytes(bytes[4..6].try_into().unwrap());
        h.header_bytes = u16::from_le_bytes(bytes[6..8].try_into().unwrap());
        h.message_bytes = u32::from_le_bytes(bytes[8..12].try_into().unwrap());
        h.family = u16::from_le_bytes(bytes[12..14].try_into().unwrap());
        h.opcode = u16::from_le_bytes(bytes[14..16].try_into().unwrap());
        h.request_id = u64::from_le_bytes(bytes[16..24].try_into().unwrap());
        h.object = u64::from_le_bytes(bytes[24..32].try_into().unwrap());
        h.payload_grant = u64::from_le_bytes(bytes[32..40].try_into().unwrap());
        h.payload_offset = u64::from_le_bytes(bytes[40..48].try_into().unwrap());
        h.payload_bytes = u32::from_le_bytes(bytes[48..52].try_into().unwrap());
        h.flags = u32::from_le_bytes(bytes[52..56].try_into().unwrap());
        h.reserved0 = u64::from_le_bytes(bytes[56..64].try_into().unwrap());
        Ok(h)
    }

    /// Little-endian copy-out. Always 64 bytes.
    pub fn encode(&self) -> [u8; 64] {
        let mut out = [0u8; 64];
        out[0..4].copy_from_slice(&self.magic.to_le_bytes());
        out[4..6].copy_from_slice(&self.abi_major.to_le_bytes());
        out[6..8].copy_from_slice(&self.header_bytes.to_le_bytes());
        out[8..12].copy_from_slice(&self.message_bytes.to_le_bytes());
        out[12..14].copy_from_slice(&self.family.to_le_bytes());
        out[14..16].copy_from_slice(&self.opcode.to_le_bytes());
        out[16..24].copy_from_slice(&self.request_id.to_le_bytes());
        out[24..32].copy_from_slice(&self.object.to_le_bytes());
        out[32..40].copy_from_slice(&self.payload_grant.to_le_bytes());
        out[40..48].copy_from_slice(&self.payload_offset.to_le_bytes());
        out[48..52].copy_from_slice(&self.payload_bytes.to_le_bytes());
        out[52..56].copy_from_slice(&self.flags.to_le_bytes());
        out[56..64].copy_from_slice(&self.reserved0.to_le_bytes());
        out
    }

    /// Shape validation. Mirrors `vf_validate_header_shape`: envelope shape is
    /// separated from root-owned capability/grant identity, permissions,
    /// lifetime and range checks. Never authenticates anything.
    pub fn validate_shape(&self) -> Result<()> {
        if self.magic != VF_MSG_MAGIC {
            return Err(VfError::Eabi("bad magic"));
        }
        if self.abi_major != VF_ABI_MAJOR {
            return Err(VfError::Eabi("unsupported abi major"));
        }
        if self.header_bytes != VF_MSG_BYTES as u16 {
            return Err(VfError::Eabi("bad header size"));
        }
        if self.message_bytes < VF_MSG_BYTES {
            return Err(VfError::Eabi("message smaller than header"));
        }
        if self.payload_bytes > VF_PAYLOAD_MAX {
            return Err(VfError::Erange);
        }
        match self.family {
            VF_FAMILY_ROOT | VF_FAMILY_BLOCK | VF_FAMILY_SGPU => Ok(()),
            _ => Err(VfError::Eabi("unknown family")),
        }
    }

    /// Whole-message bounds: payload must fit inside the declared message.
    pub fn payload_end(&self) -> Result<u64> {
        let end = self
            .payload_offset
            .checked_add(self.payload_bytes as u64)
            .ok_or(VfError::Erange)?;
        // A message cannot carry a payload that overruns its own byte count.
        let message_payload_end = (self.message_bytes as u64)
            .checked_sub(VF_MSG_BYTES as u64)
            .ok_or(VfError::Eabi("bad message size"))?;
        if end > message_payload_end {
            return Err(VfError::Erange);
        }
        Ok(end)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use core::mem::offset_of;

    #[test]
    fn layout_matches_vf_abi_header_offsets() {
        assert_eq!(offset_of!(VfMsgHeader, magic), 0);
        assert_eq!(offset_of!(VfMsgHeader, abi_major), 4);
        assert_eq!(offset_of!(VfMsgHeader, header_bytes), 6);
        assert_eq!(offset_of!(VfMsgHeader, message_bytes), 8);
        assert_eq!(offset_of!(VfMsgHeader, family), 12);
        assert_eq!(offset_of!(VfMsgHeader, opcode), 14);
        assert_eq!(offset_of!(VfMsgHeader, request_id), 16);
        assert_eq!(offset_of!(VfMsgHeader, object), 24);
        assert_eq!(offset_of!(VfMsgHeader, payload_grant), 32);
        assert_eq!(offset_of!(VfMsgHeader, payload_offset), 40);
        assert_eq!(offset_of!(VfMsgHeader, payload_bytes), 48);
        assert_eq!(offset_of!(VfMsgHeader, flags), 52);
        assert_eq!(offset_of!(VfMsgHeader, reserved0), 56);
        assert_eq!(core::mem::size_of::<VfMsgHeader>(), 64);
    }

    #[test]
    fn roundtrip() {
        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_SUBMIT_COMMAND_LIST);
        h.request_id = 0x1234;
        h.payload_bytes = 16;
        let bytes = h.encode();
        let back = VfMsgHeader::decode(&bytes).unwrap();
        assert_eq!(h, back);
    }

    #[test]
    fn decode_rejects_wrong_size() {
        assert!(VfMsgHeader::decode(&[0u8; 63]).is_err());
        assert!(VfMsgHeader::decode(&[0u8; 65]).is_err());
    }

    #[test]
    fn validate_shape_rejects_bad_magic() {
        let mut h = VfMsgHeader::new(VF_FAMILY_ROOT, VF_OP_GRANT_CREATE);
        h.magic = 0;
        assert!(matches!(h.validate_shape(), Err(VfError::Eabi(_))));
    }

    #[test]
    fn validate_shape_rejects_bad_family() {
        let mut h = VfMsgHeader::new(VF_FAMILY_ROOT, VF_OP_GRANT_CREATE);
        h.family = 0xF00D;
        assert!(h.validate_shape().is_err());
    }

    #[test]
    fn payload_bounds_checked() {
        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_CREATE_RESOURCE);
        h.message_bytes = 128;
        h.payload_offset = 0;
        h.payload_bytes = 16;
        assert_eq!(h.payload_end().unwrap(), 16);

        // Payload may not overrun the message region after the header.
        h.payload_offset = 64;
        assert!(h.payload_end().is_err());

        h.payload_offset = 0;
        h.payload_bytes = VF_PAYLOAD_MAX + 1;
        assert!(h.validate_shape().is_err());
    }

    #[test]
    fn encode_uses_little_endian() {
        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_QUERY_CAPS);
        h.request_id = 1;
        h.object = 2;
        let bytes = h.encode();
        assert_eq!(u32::from_le_bytes(bytes[0..4].try_into().unwrap()), VF_MSG_MAGIC);
        assert_eq!(u16::from_le_bytes(bytes[12..14].try_into().unwrap()), VF_FAMILY_SGPU);
        assert_eq!(u64::from_le_bytes(bytes[16..24].try_into().unwrap()), 1);
        assert_eq!(u64::from_le_bytes(bytes[24..32].try_into().unwrap()), 2);
    }
}