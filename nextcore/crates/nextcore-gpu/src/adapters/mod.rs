use crate::canonical_spec::GpuCapabilities;

pub mod amd;
pub mod intel;
pub mod nvidia;

pub trait GpuAdapter {
    fn detect() -> Option<Self>
    where
        Self: Sized;
    fn to_canonical(&self) -> GpuCapabilities;
}

pub fn adapter_for(vendor_id: u16, device_id: u16) -> Option<Box<dyn GpuAdapter>> {
    match vendor_id {
        0x1002 => Some(Box::new(amd::AmdAdapter::new(device_id))),
        0x10DE => Some(Box::new(nvidia::NvidiaAdapter::new(device_id))),
        0x8086 => Some(Box::new(intel::IntelAdapter::new(device_id))),
        _ => None,
    }
}
