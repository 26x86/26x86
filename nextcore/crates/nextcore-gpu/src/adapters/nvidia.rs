use crate::canonical_spec::{GpuCapabilities, GpuVendor, MetalVersion};
use super::GpuAdapter;

pub struct NvidiaAdapter {
    device_id: u16,
}

impl NvidiaAdapter {
    pub fn new(device_id: u16) -> Self {
        Self { device_id }
    }

    pub fn detect_device(device_id: u16) -> Option<GpuCapabilities> {
        match device_id {
            0x1180 => Some(GpuCapabilities {
                vendor: GpuVendor::NVIDIA,
                metal_version: MetalVersion::V3_2,
                vram_size: 4096 * 1024 * 1024,
                max_threads: 2048,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            0x1187 => Some(GpuCapabilities {
                vendor: GpuVendor::NVIDIA,
                metal_version: MetalVersion::V3_2,
                vram_size: 2048 * 1024 * 1024,
                max_threads: 2048,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            0x1284 => Some(GpuCapabilities {
                vendor: GpuVendor::NVIDIA,
                metal_version: MetalVersion::V3_0,
                vram_size: 2048 * 1024 * 1024,
                max_threads: 512,
                has_tessellation: true,
                has_compute_shaders: true,
                display_outputs: vec![],
            }),
            _ => None,
        }
    }
}

impl GpuAdapter for NvidiaAdapter {
    fn detect() -> Option<Self> {
        None
    }

    fn to_canonical(&self) -> GpuCapabilities {
        Self::detect_device(self.device_id).unwrap_or_else(GpuCapabilities::default_nvidia)
    }
}
