use crate::canonical_spec::{GpuCapabilities, GpuVendor, MetalVersion};
use super::GpuAdapter;

pub struct IntelAdapter {
    device_id: u16,
}

impl IntelAdapter {
    pub fn new(device_id: u16) -> Self {
        Self { device_id }
    }

    pub fn detect_device(device_id: u16) -> Option<GpuCapabilities> {
        match device_id {
            0x0166 => Some(GpuCapabilities {
                vendor: GpuVendor::Intel,
                metal_version: MetalVersion::V3_0,
                vram_size: 1536 * 1024 * 1024,
                max_threads: 512,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            0x0412 => Some(GpuCapabilities {
                vendor: GpuVendor::Intel,
                metal_version: MetalVersion::V3_0,
                vram_size: 2048 * 1024 * 1024,
                max_threads: 512,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            0x5912 => Some(GpuCapabilities {
                vendor: GpuVendor::Intel,
                metal_version: MetalVersion::V3_0,
                vram_size: 1536 * 1024 * 1024,
                max_threads: 512,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            _ => None,
        }
    }
}

impl GpuAdapter for IntelAdapter {
    fn detect() -> Option<Self> {
        None
    }

    fn to_canonical(&self) -> GpuCapabilities {
        Self::detect_device(self.device_id).unwrap_or_else(GpuCapabilities::default_intel)
    }
}
