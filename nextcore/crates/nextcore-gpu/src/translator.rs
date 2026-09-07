use crate::canonical_spec::{GpuCapabilities, GpuVendor};
use crate::adapters::{amd, intel, nvidia};

#[derive(Debug, Clone)]
pub struct RealGpuInfo {
    pub vendor_id: u16,
    pub device_id: u16,
    pub vram: u64,
    pub revision: u8,
}

#[derive(Debug, Clone)]
pub struct PciEntry {
    pub vendor_id: u16,
    pub device_id: u16,
    pub class_code: u16,
}

pub struct GpuTranslator;

impl GpuTranslator {
    pub fn new() -> Self {
        Self
    }

    pub fn from_pci_ids(vendor_id: u16, device_id: u16, vram_mb: u32) -> Option<GpuCapabilities> {
        let vram_bytes = (vram_mb as u64) * 1024 * 1024;
        let caps = match vendor_id {
            0x1002 => amd::AmdAdapter::detect_device(device_id),
            0x10DE => nvidia::NvidiaAdapter::detect_device(device_id),
            0x8086 => intel::IntelAdapter::detect_device(device_id),
            _ => None,
        };
        caps.map(|mut c| {
            c.vram_size = vram_bytes;
            c
        })
    }

    pub fn from_known_set(entries: &[PciEntry]) -> Vec<GpuCapabilities> {
        entries
            .iter()
            .filter_map(|e| Self::from_pci_ids(e.vendor_id, e.device_id, 0))
            .collect()
    }

    pub fn detect(vendor_known: bool, real_info: &RealGpuInfo) -> GpuCapabilities {
        if vendor_known {
            if let Some(caps) = Self::from_pci_ids(
                real_info.vendor_id,
                real_info.device_id,
                (real_info.vram / (1024 * 1024)) as u32,
            ) {
                return caps;
            }
        }
        let vendor = match real_info.vendor_id {
            0x1002 => GpuVendor::AMD,
            0x10DE => GpuVendor::NVIDIA,
            0x8086 => GpuVendor::Intel,
            _ => GpuVendor::Unknown,
        };
        GpuCapabilities::software_fallback(vendor, real_info.vram)
    }

    pub fn translate(real_info: &RealGpuInfo) -> GpuCapabilities {
        let vendor_known = matches!(real_info.vendor_id, 0x1002 | 0x10DE | 0x8086);
        Self::detect(vendor_known, real_info)
    }
}

impl Default for GpuTranslator {
    fn default() -> Self {
        Self::new()
    }
}
