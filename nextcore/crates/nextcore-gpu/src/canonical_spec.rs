use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GpuVendor {
    AMD,
    NVIDIA,
    Intel,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum MetalVersion {
    V2_0,
    V3_0,
    V3_1,
    V3_2,
}

impl MetalVersion {
    pub fn minimum() -> Self {
        MetalVersion::V2_0
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplayOutput {
    pub name: String,
    pub max_resolution: (u32, u32),
    pub connector_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GpuCapabilities {
    pub vendor: GpuVendor,
    pub metal_version: MetalVersion,
    pub vram_size: u64,
    pub max_threads: u32,
    pub has_tessellation: bool,
    pub has_compute_shaders: bool,
    pub display_outputs: Vec<DisplayOutput>,
}

impl GpuCapabilities {
    pub fn validate(&self) -> bool {
        if self.vendor == GpuVendor::Unknown {
            return false;
        }
        if self.vram_size == 0 {
            return false;
        }
        if self.max_threads == 0 {
            return false;
        }
        true
    }

    pub fn software_fallback(vendor: GpuVendor, detected_vram: u64) -> Self {
        Self {
            vendor,
            metal_version: MetalVersion::minimum(),
            vram_size: detected_vram,
            max_threads: 1,
            has_compute_shaders: false,
            has_tessellation: false,
            display_outputs: vec![],
        }
    }

    pub fn default_intel() -> Self {
        Self {
            vendor: GpuVendor::Intel,
            metal_version: MetalVersion::V3_0,
            vram_size: 1536 * 1024 * 1024,
            max_threads: 512,
            has_tessellation: true,
            has_compute_shaders: true,
            display_outputs: vec![],
        }
    }

    pub fn default_amd() -> Self {
        Self {
            vendor: GpuVendor::AMD,
            metal_version: MetalVersion::V3_1,
            vram_size: 4096 * 1024 * 1024,
            max_threads: 1024,
            has_tessellation: true,
            has_compute_shaders: true,
            display_outputs: vec![],
        }
    }

    pub fn default_nvidia() -> Self {
        Self {
            vendor: GpuVendor::NVIDIA,
            metal_version: MetalVersion::V3_2,
            vram_size: 8192 * 1024 * 1024,
            max_threads: 2048,
            has_tessellation: true,
            has_compute_shaders: true,
            display_outputs: vec![],
        }
    }
}
