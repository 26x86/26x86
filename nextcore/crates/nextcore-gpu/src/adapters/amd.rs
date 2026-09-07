use crate::canonical_spec::{GpuCapabilities, GpuVendor, MetalVersion};
use super::GpuAdapter;

pub struct AmdAdapter {
    device_id: u16,
}

impl AmdAdapter {
    pub fn new(device_id: u16) -> Self {
        Self { device_id }
    }

    pub fn detect_device(device_id: u16) -> Option<GpuCapabilities> {
        match device_id {
            0x67DF => Some(GpuCapabilities {
                vendor: GpuVendor::AMD,
                metal_version: MetalVersion::V3_1,
                vram_size: 8192 * 1024 * 1024,
                max_threads: 1024,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            0x67C7 => Some(GpuCapabilities {
                vendor: GpuVendor::AMD,
                metal_version: MetalVersion::V3_1,
                vram_size: 4096 * 1024 * 1024,
                max_threads: 1024,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            0x687F => Some(GpuCapabilities {
                vendor: GpuVendor::AMD,
                metal_version: MetalVersion::V3_1,
                vram_size: 8192 * 1024 * 1024,
                max_threads: 2048,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            _ => None,
        }
    }
}

impl GpuAdapter for AmdAdapter {
    fn detect() -> Option<Self> {
        None
    }

    fn to_canonical(&self) -> GpuCapabilities {
        Self::detect_device(self.device_id).unwrap_or_else(GpuCapabilities::default_amd)
    }
}
