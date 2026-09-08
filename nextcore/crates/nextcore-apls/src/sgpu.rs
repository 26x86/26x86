use std::collections::HashMap;

use thiserror::Error;

use nextcore_gpu::canonical_spec::{GpuCapabilities, GpuVendor, MetalVersion};
use nextcore_gpu::virtual_device::{
    CommandBuffer, GpuCommand, VirtualMetalDevice,
};

use crate::vf_abi::{
    VfMsgHeader, VF_FAMILY_SGPU, VF_MSG_BYTES, VF_SGPU_CREATE_RESOURCE,
    VF_SGPU_DESTROY_RESOURCE, VF_SGPU_PRESENT, VF_SGPU_QUERY_CAPS,
    VF_SGPU_SUBMIT_COMMAND_LIST, VfError,
};

/// Golden Gate (macOS 27) graphics service-cell bridge. SGPU family requests
/// from the VSK ABI are translated into the Nextcore GPU command surface and
/// executed on the local software backend. An envelope or an abstraction
/// receipt never constitutes Metal support; only actual backend execution
/// counts, and it reports exactly what it ran.
#[derive(Debug, Error)]
pub enum SgpuError {
    #[error("resource not found: {0}")]
    ResourceNotFound(u64),
    #[error("resource already exists: {0}")]
    ResourceExists(u64),
    #[error("GPU backend error: {0}")]
    Gpu(String),
    #[error("ABI error: {0}")]
    Vf(#[from] VfError),
    #[error("payload decode error")]
    Payload,
}

pub type Result<T> = core::result::Result<T, SgpuError>;

#[derive(Debug, Clone, PartialEq)]
pub struct SgpuCaps {
    pub vendor: GpuVendor,
    pub metal_version: MetalVersion,
    pub vram_bytes: u64,
    pub max_threads_per_threadgroup: u32,
    pub has_compute_shaders: bool,
    pub software_accelerated: bool,
}

impl SgpuCaps {
    pub fn encode(&self) -> [u8; 40] {
        let mut out = [0u8; 40];
        out[0] = self.vendor as u8;
        out[4] = self.metal_version as u8;
        out[8..16].copy_from_slice(&self.vram_bytes.to_le_bytes());
        out[16..20].copy_from_slice(&self.max_threads_per_threadgroup.to_le_bytes());
        out[20] = self.has_compute_shaders as u8;
        out[24] = self.software_accelerated as u8;
        out
    }

    pub fn decode(bytes: &[u8]) -> Result<Self> {
        if bytes.len() < 40 {
            return Err(SgpuError::Payload);
        }
        let vendor = match bytes[0] {
            0 => GpuVendor::AMD,
            1 => GpuVendor::NVIDIA,
            2 => GpuVendor::Intel,
            _ => GpuVendor::Unknown,
        };
        let metal_version = match bytes[4] {
            0 => MetalVersion::V2_0,
            1 => MetalVersion::V3_0,
            2 => MetalVersion::V3_1,
            _ => MetalVersion::V3_2,
        };
        let vram_bytes = u64::from_le_bytes(bytes[8..16].try_into().unwrap());
        let max_threads = u32::from_le_bytes(bytes[16..20].try_into().unwrap());
        Ok(Self {
            vendor,
            metal_version,
            vram_bytes,
            max_threads_per_threadgroup: max_threads,
            has_compute_shaders: bytes[20] != 0,
            software_accelerated: bytes[24] != 0,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SgpuResource {
    pub sgp_handle: u64,
    pub gpu_handle: u64,
    pub size: u64,
}

#[derive(Debug, Clone, PartialEq)]
pub enum SgpuCommand {
    CopyBuffer { src: u64, dst: u64, size: u64 },
    RenderClear { color: [f32; 4] },
    ComputeDispatch { kernel_id: u32, grid: (u32, u32, u32), block: (u32, u32, u32) },
    Present { buffer: u64 },
}

impl SgpuCommand {
    pub fn tag(&self) -> u8 {
        match self {
            SgpuCommand::CopyBuffer { .. } => 1,
            SgpuCommand::RenderClear { .. } => 2,
            SgpuCommand::ComputeDispatch { .. } => 3,
            SgpuCommand::Present { .. } => 4,
        }
    }

    pub fn encode(&self) -> Vec<u8> {
        let mut out = vec![self.tag()];
        match self {
            SgpuCommand::CopyBuffer { src, dst, size } => {
                out.extend_from_slice(&src.to_le_bytes());
                out.extend_from_slice(&dst.to_le_bytes());
                out.extend_from_slice(&size.to_le_bytes());
            }
            SgpuCommand::RenderClear { color } => {
                for c in color {
                    out.extend_from_slice(&c.to_le_bytes());
                }
            }
            SgpuCommand::ComputeDispatch { kernel_id, grid, block } => {
                out.extend_from_slice(&kernel_id.to_le_bytes());
                for v in [grid.0, grid.1, grid.2, block.0, block.1, block.2] {
                    out.extend_from_slice(&v.to_le_bytes());
                }
            }
            SgpuCommand::Present { buffer } => {
                out.extend_from_slice(&buffer.to_le_bytes());
            }
        }
        out
    }

    pub fn decode(bytes: &[u8]) -> Result<Self> {
        if bytes.is_empty() {
            return Err(SgpuError::Payload);
        }
        match bytes[0] {
            1 => {
                if bytes.len() < 25 {
                    return Err(SgpuError::Payload);
                }
                Ok(SgpuCommand::CopyBuffer {
                    src: u64::from_le_bytes(bytes[1..9].try_into().unwrap()),
                    dst: u64::from_le_bytes(bytes[9..17].try_into().unwrap()),
                    size: u64::from_le_bytes(bytes[17..25].try_into().unwrap()),
                })
            }
            2 => {
                if bytes.len() < 17 {
                    return Err(SgpuError::Payload);
                }
                let mut color = [0f32; 4];
                for (i, c) in color.iter_mut().enumerate() {
                    *c = f32::from_le_bytes(bytes[1 + i * 4..5 + i * 4].try_into().unwrap());
                }
                Ok(SgpuCommand::RenderClear { color })
            }
            3 => {
                if bytes.len() < 29 {
                    return Err(SgpuError::Payload);
                }
                let kernel_id = u32::from_le_bytes(bytes[1..5].try_into().unwrap());
                let vals = (0..6)
                    .map(|i| u32::from_le_bytes(bytes[5 + i * 4..9 + i * 4].try_into().unwrap()))
                    .collect::<Vec<_>>();
                Ok(SgpuCommand::ComputeDispatch {
                    kernel_id,
                    grid: (vals[0], vals[1], vals[2]),
                    block: (vals[3], vals[4], vals[5]),
                })
            }
            4 => {
                if bytes.len() < 9 {
                    return Err(SgpuError::Payload);
                }
                Ok(SgpuCommand::Present {
                    buffer: u64::from_le_bytes(bytes[1..9].try_into().unwrap()),
                })
            }
            _ => Err(SgpuError::Payload),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct SgpuCommandList {
    pub cmds: Vec<SgpuCommand>,
}

impl SgpuCommandList {
    pub fn encode(&self) -> Vec<u8> {
        let mut out = (self.cmds.len() as u32).to_le_bytes().to_vec();
        for c in &self.cmds {
            out.extend_from_slice(&c.encode());
        }
        out
    }

    pub fn decode(bytes: &[u8]) -> Result<Self> {
        if bytes.len() < 4 {
            return Err(SgpuError::Payload);
        }
        let count = u32::from_le_bytes(bytes[0..4].try_into().unwrap());
        let mut p = 4usize;
        let mut cmds = Vec::with_capacity(count as usize);
        for _ in 0..count {
            if p >= bytes.len() {
                return Err(SgpuError::Payload);
            }
            let tag = bytes[p];
            let len = match tag {
                1 => 25,
                2 => 17,
                3 => 29,
                4 => 9,
                _ => return Err(SgpuError::Payload),
            };
            if p + len > bytes.len() {
                return Err(SgpuError::Payload);
            }
            cmds.push(SgpuCommand::decode(&bytes[p..p + len])?);
            p += len;
        }
        if p != bytes.len() {
            return Err(SgpuError::Payload);
        }
        Ok(SgpuCommandList { cmds })
    }
}

/// A complete SGPU transfer unit: 64-byte VF header plus bounded payload.
#[derive(Debug, Clone, PartialEq)]
pub struct SgpuFrame {
    pub header: VfMsgHeader,
    pub payload: Vec<u8>,
}

impl SgpuFrame {
    pub fn to_wire(&self) -> Vec<u8> {
        let mut out = self.header.encode().to_vec();
        // Padding to message_bytes keeps the wire format fixed-length for a
        // request id; the payload region starts right after the header.
        let total = (self.header.message_bytes as usize).max(VF_MSG_BYTES as usize);
        out.resize(total, 0);
        if !self.payload.is_empty() {
            // payload_offset is relative to the end of the 64-byte header.
            let start = (VF_MSG_BYTES as usize) + self.header.payload_offset as usize;
            let end = start + self.payload.len();
            if end <= out.len() {
                out[start..end].copy_from_slice(&self.payload);
            }
        }
        out
    }

    pub fn from_wire(bytes: &[u8]) -> Result<Self> {
        if bytes.len() < VF_MSG_BYTES as usize {
            return Err(SgpuError::Payload);
        }
        let header = VfMsgHeader::decode(&bytes[..VF_MSG_BYTES as usize])
            .map_err(|e| SgpuError::Vf(e))?;
        header.validate_shape()?;
        let payload_end_rel = header.payload_end().map_err(|e| SgpuError::Vf(e))?;
        let start = (VF_MSG_BYTES as usize) + header.payload_offset as usize;
        let end = (VF_MSG_BYTES as usize) + payload_end_rel as usize;
        let payload = if end > start && end <= bytes.len() {
            bytes[start..end].to_vec()
        } else {
            Vec::new()
        };
        Ok(SgpuFrame { header, payload })
    }
}

/// SGPU service-cell session translating to the Nextcore GPU backend.
#[derive(Debug)]
pub struct SgpuSession {
    pub device: VirtualMetalDevice,
    resources: HashMap<u64, SgpuResource>,
    next_resource_id: u64,
}

impl SgpuSession {
    pub fn new(caps: GpuCapabilities) -> Self {
        Self {
            device: VirtualMetalDevice::new(caps),
            resources: HashMap::new(),
            next_resource_id: 1,
        }
    }

    pub fn query_caps(&self) -> SgpuCaps {
        SgpuCaps {
            vendor: self.device.spec.vendor,
            metal_version: self.device.spec.metal_version,
            vram_bytes: self.device.spec.vram_size,
            max_threads_per_threadgroup: self.device.spec.max_threads,
            // This session has no shader/binding registration or compute backend.
            has_compute_shaders: false,
            software_accelerated: self.device.is_software_accelerated(),
        }
    }

    pub fn create_resource(&mut self, size: u64) -> Result<SgpuResource> {
        if size == 0 {
            return Err(SgpuError::Payload);
        }
        let gpu = self.device.allocate_buffer(size);
        let res = SgpuResource {
            sgp_handle: self.next_resource_id,
            gpu_handle: gpu.handle,
            size: gpu.size,
        };
        self.next_resource_id += 1;
        self.resources.insert(res.sgp_handle, res.clone());
        Ok(res)
    }

    pub fn destroy_resource(&mut self, handle: u64) -> Result<()> {
        let res = self.resources.remove(&handle).ok_or(SgpuError::ResourceNotFound(handle))?;
        self.device.memory.free(res.gpu_handle).map_err(|e| SgpuError::Gpu(e.to_string()))?;
        Ok(())
    }

    pub fn gpu_handle(&self, sgp_handle: u64) -> Result<u64> {
        self.resources.get(&sgp_handle).map(|r| r.gpu_handle).ok_or(SgpuError::ResourceNotFound(sgp_handle))
    }

    pub fn submit(&mut self, list: &SgpuCommandList) -> Result<usize> {
        let mut gpu_cmds = Vec::with_capacity(list.cmds.len());
        for cmd in &list.cmds {
            match cmd {
                SgpuCommand::CopyBuffer { src, dst, size } => {
                    let src_gpu = self.gpu_handle(*src)?;
                    let dst_gpu = self.gpu_handle(*dst)?;
                    gpu_cmds.push(GpuCommand::CopyBuffer { src: src_gpu, dst: dst_gpu, size: *size });
                }
                SgpuCommand::RenderClear { color } => {
                    gpu_cmds.push(GpuCommand::RenderClear { color: *color });
                }
                SgpuCommand::ComputeDispatch { kernel_id, grid, block } => {
                    gpu_cmds.push(GpuCommand::ComputeKernel { kernel_id: *kernel_id, grid: *grid, block: *block });
                }
                SgpuCommand::Present { buffer } => {
                    let gpu = self.gpu_handle(*buffer)?;
                    gpu_cmds.push(GpuCommand::PresentSwapchain { buffer: gpu });
                }
            }
        }
        self.device
            .write_command_buffer(CommandBuffer { cmds: gpu_cmds })
            .map_err(|e| SgpuError::Gpu(e.to_string()))?;
        self.device.flush().map_err(|e| SgpuError::Gpu(e.to_string()))?;
        Ok(list.cmds.len())
    }

    pub fn present(&mut self, resource: u64) -> Result<()> {
        self.submit(&SgpuCommandList {
            cmds: vec![SgpuCommand::Present { buffer: resource }],
        })?;
        Ok(())
    }

    /// Deliver an SGPU request frame to the session and produce a response
    /// frame. This is the transport-level bridge: envelope decode → opcode
    /// dispatch → backend execution → response envelope.
    pub fn dispatch(&mut self, frame: &SgpuFrame) -> Result<SgpuFrame> {
        if frame.header.family != VF_FAMILY_SGPU {
            return Err(SgpuError::Vf(VfError::Eabi("not an SGPU family frame")));
        }

        let resp = |opcode: u16, request_id: u64, payload: Vec<u8>| -> SgpuFrame {
            let mut header = VfMsgHeader::new(VF_FAMILY_SGPU, opcode);
            header.request_id = request_id;
            header.payload_offset = 0;
            header.payload_bytes = payload.len() as u32;
            header.message_bytes = VF_MSG_BYTES + header.payload_bytes;
            SgpuFrame { header, payload }
        };

        match frame.header.opcode {
            VF_SGPU_QUERY_CAPS => {
                let caps = self.query_caps();
                Ok(resp(VF_SGPU_QUERY_CAPS, frame.header.request_id, caps.encode().to_vec()))
            }
            VF_SGPU_CREATE_RESOURCE => {
                if frame.payload.len() < 8 {
                    return Err(SgpuError::Payload);
                }
                let size = u64::from_le_bytes(frame.payload[0..8].try_into().unwrap());
                let res = self.create_resource(size)?;
                Ok(resp(VF_SGPU_CREATE_RESOURCE, frame.header.request_id, res.sgp_handle.to_le_bytes().to_vec()))
            }
            VF_SGPU_DESTROY_RESOURCE => {
                if frame.payload.len() < 8 {
                    return Err(SgpuError::Payload);
                }
                let handle = u64::from_le_bytes(frame.payload[0..8].try_into().unwrap());
                self.destroy_resource(handle)?;
                Ok(resp(VF_SGPU_DESTROY_RESOURCE, frame.header.request_id, Vec::new()))
            }
            VF_SGPU_SUBMIT_COMMAND_LIST => {
                let list = SgpuCommandList::decode(&frame.payload).map_err(|_| SgpuError::Payload)?;
                let completed = self.submit(&list)?;
                Ok(resp(VF_SGPU_SUBMIT_COMMAND_LIST, frame.header.request_id, (completed as u32).to_le_bytes().to_vec()))
            }
            VF_SGPU_PRESENT => {
                if frame.payload.len() < 8 {
                    return Err(SgpuError::Payload);
                }
                let res = u64::from_le_bytes(frame.payload[0..8].try_into().unwrap());
                self.present(res)?;
                Ok(resp(VF_SGPU_PRESENT, frame.header.request_id, Vec::new()))
            }
            _ => Err(SgpuError::Vf(VfError::Eabi("unknown SGPU opcode"))),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use nextcore_gpu::canonical_spec::GpuCapabilities;

    fn software_caps() -> GpuCapabilities {
        GpuCapabilities::software_fallback(GpuVendor::AMD, 4 << 20)
    }

    #[test]
    fn caps_roundtrip() {
        let caps = SgpuCaps {
            vendor: GpuVendor::AMD,
            metal_version: MetalVersion::V3_1,
            vram_bytes: 4 << 20,
            max_threads_per_threadgroup: 1,
            has_compute_shaders: false,
            software_accelerated: true,
        };
        assert_eq!(SgpuCaps::decode(&caps.encode()).unwrap(), caps);
    }

    #[test]
    fn command_roundtrip_all_variants() {
        let cmds = SgpuCommandList {
            cmds: vec![
                SgpuCommand::CopyBuffer { src: 1, dst: 2, size: 256 },
                SgpuCommand::RenderClear { color: [1.0, 0.5, 0.25, 0.0] },
                SgpuCommand::ComputeDispatch { kernel_id: 7, grid: (64, 1, 1), block: (8, 8, 1) },
                SgpuCommand::Present { buffer: 3 },
            ],
        };
        let decoded = SgpuCommandList::decode(&cmds.encode()).unwrap();
        assert_eq!(decoded, cmds);
        let trunc = cmds.encode();
        assert!(SgpuCommandList::decode(&trunc[..trunc.len() - 1]).is_err());
    }

    #[test]
    fn copy_buffer_executes_on_software_backend() {
        let mut session = SgpuSession::new(software_caps());
        let src = session.create_resource(256).unwrap();
        let dst = session.create_resource(256).unwrap();
        // Write pattern into source GPU buffer directly.
        session.device.memory.write(src.gpu_handle, 0, &[0xEEu8; 256]).unwrap();
        session
            .submit(&SgpuCommandList {
                cmds: vec![SgpuCommand::CopyBuffer { src: src.sgp_handle, dst: dst.sgp_handle, size: 256 }],
            })
            .unwrap();
        let data = session.device.memory.read(dst.gpu_handle, 0, 256).unwrap();
        assert!(data.iter().all(|&b| b == 0xEE));
    }

    #[test]
    fn dispatch_query_caps_through_vf_frame() {
        let mut session = SgpuSession::new(software_caps());
        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_QUERY_CAPS);
        h.request_id = 42;
        h.payload_offset = 0;
        h.message_bytes = VF_MSG_BYTES;
        h.payload_bytes = 0;
        let req = SgpuFrame { header: h, payload: Vec::new() };
        let resp = session.dispatch(&req).unwrap();
        assert_eq!(resp.header.request_id, 42);
        assert_eq!(resp.header.opcode, VF_SGPU_QUERY_CAPS);
        assert!(resp.header.message_bytes >= VF_MSG_BYTES);
        let caps = SgpuCaps::decode(&resp.payload).unwrap();
        assert!(caps.software_accelerated);
        assert_eq!(caps.vendor, GpuVendor::AMD);
    }

    #[test]
    fn dispatch_create_and_copy_via_wire_roundtrip() {
        let mut session = SgpuSession::new(software_caps());

        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_CREATE_RESOURCE);
        h.request_id = 1;
        h.payload_offset = 0;
        h.payload_bytes = 8;
        h.message_bytes = VF_MSG_BYTES + 8;
        let req = SgpuFrame { header: h, payload: 256u64.to_le_bytes().to_vec() };
        let wire = req.to_wire();
        let back = SgpuFrame::from_wire(&wire).unwrap();
        let resp = session.dispatch(&back).unwrap();
        let src = u64::from_le_bytes(resp.payload[0..8].try_into().unwrap());

        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_CREATE_RESOURCE);
        h.request_id = 2;
        h.payload_offset = 0;
        h.payload_bytes = 8;
        h.message_bytes = VF_MSG_BYTES + 8;
        let req = SgpuFrame { header: h, payload: 256u64.to_le_bytes().to_vec() };
        let resp = session.dispatch(&req).unwrap();
        let dst = u64::from_le_bytes(resp.payload[0..8].try_into().unwrap());

        session.device.memory.write(session.gpu_handle(src).unwrap(), 0, &[0xABu8; 256]).unwrap();

        let list = SgpuCommandList { cmds: vec![SgpuCommand::CopyBuffer { src, dst, size: 256 }] };
        let payload = list.encode();
        let mut h = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_SUBMIT_COMMAND_LIST);
        h.request_id = 3;
        h.payload_offset = 0;
        h.payload_bytes = payload.len() as u32;
        h.message_bytes = VF_MSG_BYTES + h.payload_bytes;
        let req = SgpuFrame { header: h, payload };
        let resp = session.dispatch(&req).unwrap();
        assert_eq!(u32::from_le_bytes(resp.payload[0..4].try_into().unwrap()), 1);

        let data = session.device.memory.read(session.gpu_handle(dst).unwrap(), 0, 256).unwrap();
        assert!(data.iter().all(|&b| b == 0xAB));
    }

    #[test]
    fn present_without_backend_is_rejected() {
        let mut session = SgpuSession::new(software_caps());
        let res = session.create_resource(64).unwrap();
        assert!(matches!(session.present(res.sgp_handle), Err(SgpuError::Gpu(_))));
    }

    #[test]
    fn unsupported_dispatch_has_no_success_frame_or_partial_copy() {
        let mut session = SgpuSession::new(GpuCapabilities::default_amd());
        assert!(!session.query_caps().has_compute_shaders);
        assert!(!session.device.supports_metal());
        let src = session.create_resource(4).unwrap();
        let dst = session.create_resource(4).unwrap();
        session.device.memory.write(src.gpu_handle, 0, &[1, 2, 3, 4]).unwrap();
        for unsupported in [
            SgpuCommand::ComputeDispatch { kernel_id: 7, grid: (1, 1, 1), block: (1, 1, 1) },
            SgpuCommand::RenderClear { color: [1.0; 4] },
            SgpuCommand::Present { buffer: dst.sgp_handle },
        ] {
            let payload = SgpuCommandList { cmds: vec![
                SgpuCommand::CopyBuffer { src: src.sgp_handle, dst: dst.sgp_handle, size: 4 },
                unsupported,
            ] }.encode();
            let mut header = VfMsgHeader::new(VF_FAMILY_SGPU, VF_SGPU_SUBMIT_COMMAND_LIST);
            header.payload_bytes = payload.len() as u32;
            header.message_bytes = VF_MSG_BYTES + header.payload_bytes;
            let decoded = SgpuFrame::from_wire(&SgpuFrame { header, payload }.to_wire()).unwrap();
            assert!(matches!(session.dispatch(&decoded), Err(SgpuError::Gpu(_))));
            assert_eq!(session.device.memory.read(dst.gpu_handle, 0, 4).unwrap(), [0; 4]);
        }
    }

    #[test]
    fn unknown_opcode_rejected() {
        let mut session = SgpuSession::new(software_caps());
        let h = VfMsgHeader::new(VF_FAMILY_SGPU, 0xF0);
        let frame = SgpuFrame { header: h, payload: Vec::new() };
        assert!(session.dispatch(&frame).is_err());
    }

    #[test]
    fn unknown_resource_rejected() {
        let mut session = SgpuSession::new(software_caps());
        let list = SgpuCommandList { cmds: vec![SgpuCommand::CopyBuffer { src: 99, dst: 100, size: 1 }] };
        assert!(matches!(session.submit(&list), Err(SgpuError::ResourceNotFound(99))));
    }
}
