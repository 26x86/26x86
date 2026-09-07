#[derive(Debug, Clone)]
pub struct PciDevice {
    pub vendor_id: u16,
    pub device_id: u16,
    pub class_code: u8,
    pub subclass: u8,
    pub prog_if: u8,
    pub revision: u8,
    pub subsystem_vendor_id: u16,
    pub subsystem_device_id: u16,
}

#[derive(Debug, Clone)]
pub struct MacPciDevice {
    pub inner: PciDevice,
    pub recognized: bool,
    pub brand_name: String,
}

pub struct PciTranslator;

const MAC_RECOGNIZED_DEVICES: &[(u16, u16, &str)] = &[
    (0x1002, 0x67DF, "Radeon RX 570/580"),
    (0x1002, 0x687F, "Radeon RX Vega 64"),
    (0x10DE, 0x1180, "GeForce GTX 680"),
    (0x8086, 0x0166, "HD Graphics 4000"),
];

impl PciTranslator {
    pub fn new() -> Self {
        Self
    }

    pub fn translate_device(real: &PciDevice) -> MacPciDevice {
        let mut translated = real.clone();

        match real.vendor_id {
            0x8086 => {
                translated.subsystem_vendor_id = 0x8086;
                translated.subsystem_device_id = real.device_id;
            }
            0x1002 => {
                translated.subsystem_vendor_id = 0x1002;
                translated.subsystem_device_id = real.device_id;
            }
            0x10DE => {
                translated.subsystem_vendor_id = 0x10DE;
                translated.subsystem_device_id = real.device_id;
            }
            _ => {}
        }

        let (recognized, brand_name) = lookup_mac_brand(real.vendor_id, real.device_id);
        if recognized {
            log::info!(
                "PCI device {:#06x}:{:#06x} recognized as {}",
                real.vendor_id,
                real.device_id,
                brand_name
            );
        } else {
            log::warn!(
                "PCI device {:#06x}:{:#06x} not recognized by macOS (software rendering path)",
                real.vendor_id,
                real.device_id
            );
        }

        MacPciDevice {
            inner: translated,
            recognized,
            brand_name: brand_name.to_string(),
        }
    }

    pub fn is_mac_recognizable(vendor_id: u16, device_id: u16) -> bool {
        MAC_RECOGNIZED_DEVICES
            .iter()
            .any(|&(v, d, _)| v == vendor_id && d == device_id)
    }

    pub fn lookup_vendor_devices(vendor_id: u16) -> Vec<(u16, &'static str)> {
        MAC_RECOGNIZED_DEVICES
            .iter()
            .filter(|&&(v, _, _)| v == vendor_id)
            .map(|&(_, d, name)| (d, name))
            .collect()
    }
}

fn lookup_mac_brand(vendor_id: u16, device_id: u16) -> (bool, &'static str) {
    MAC_RECOGNIZED_DEVICES
        .iter()
        .find(|&&(v, d, _)| v == vendor_id && d == device_id)
        .map(|&(_, _, name)| (true, name))
        .unwrap_or((false, ""))
}

impl Default for PciTranslator {
    fn default() -> Self {
        Self::new()
    }
}
