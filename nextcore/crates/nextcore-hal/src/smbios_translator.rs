#[derive(Debug, Clone)]
pub struct SmbiosTable {
    pub manufacturer: String,
    pub product_name: String,
    pub serial_number: String,
    pub uuid: String,
    pub bios_vendor: String,
    pub bios_version: String,
    pub system_version: String,
    pub family: String,
}

#[derive(Debug, Clone)]
pub struct MacSmbios {
    pub manufacturer: String,
    pub product_name: String,
    pub serial_number: String,
    pub uuid: String,
    pub system_version: String,
    pub board_id: String,
    pub model_identifier: String,
}

#[derive(Debug, Clone)]
pub struct MacProfile {
    pub model: String,
    pub board_id: String,
}

impl MacProfile {
    pub fn macbookpro_16_1() -> Self {
        Self { model: "MacBookPro16,1".into(), board_id: "Mac-06F11F11946D27C5".into() }
    }
    pub fn macpro_6_1() -> Self {
        Self { model: "MacPro6,1".into(), board_id: "Mac-F60DEB81FF30ACF6".into() }
    }
    pub fn imac_19_1() -> Self {
        Self { model: "iMac19,1".into(), board_id: "Mac-AA95B1DDAB278B95".into() }
    }
    pub fn macbookair_9_1() -> Self {
        Self { model: "MacBookAir9,1".into(), board_id: "Mac-3EEFFF2CF7E31087".into() }
    }
    pub fn macmini_8_1() -> Self {
        Self { model: "Macmini8,1".into(), board_id: "Mac-7BA5B2DFE22DDD8D".into() }
    }

    pub fn all() -> Vec<MacProfile> {
        vec![
            Self::macbookpro_16_1(),
            Self::macpro_6_1(),
            Self::imac_19_1(),
            Self::macbookair_9_1(),
            Self::macmini_8_1(),
        ]
    }
}

pub fn generate_serial(profile: &MacProfile) -> String {
    let hash = simple_hash(profile.model.as_bytes());
    format!("{:04X}{:04X}", hash & 0xFFFF, (hash >> 16) & 0xFFFF)
}

fn simple_hash(data: &[u8]) -> u32 {
    let mut h: u32 = 0x811c9dc5;
    for &b in data {
        h = h.wrapping_mul(0x01000193) ^ (b as u32);
    }
    h
}

pub struct SmbiosTranslator;

impl SmbiosTranslator {
    pub fn new() -> Self {
        Self
    }

    pub fn translate(real: &SmbiosTable, profile: &MacProfile) -> MacSmbios {
        let serial = if real.serial_number.is_empty() {
            generate_serial(profile)
        } else {
            real.serial_number.clone()
        };

        let uuid = if real.uuid.is_empty() {
            generate_uuid_from_serial(&serial)
        } else {
            real.uuid.clone()
        };

        MacSmbios {
            manufacturer: "Apple Inc.".to_string(),
            product_name: profile.model.clone(),
            serial_number: serial,
            uuid,
            system_version: profile.model.clone(),
            board_id: profile.board_id.clone(),
            model_identifier: profile.model.clone(),
        }
    }
}

fn generate_uuid_from_serial(serial: &str) -> String {
    let hash = simple_hash(serial.as_bytes());
    let h2 = simple_hash(&hash.to_le_bytes());
    format!(
        "{:08X}-{:04X}-{:04X}-{:04X}-{:08X}{:04X}",
        hash,
        0x4000 | (h2 & 0x0FFF),
        0x8000 | ((h2 >> 12) & 0x3FFF),
        (h2 >> 28) & 0xFFFF,
        h2,
        hash & 0xFFFF,
    )
}

impl Default for SmbiosTranslator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_translate_to_mac() {
        let real = SmbiosTable {
            manufacturer: "Dell Inc.".to_string(),
            product_name: "XPS 15".to_string(),
            serial_number: "ABC123".to_string(),
            uuid: "1234-5678".to_string(),
            bios_vendor: "Dell".to_string(),
            bios_version: "1.0.0".to_string(),
            system_version: "1.0".to_string(),
            family: "XPS".to_string(),
        };

        let mac = SmbiosTranslator::translate(&real, &MacProfile::macpro_6_1());
        assert_eq!(mac.manufacturer, "Apple Inc.");
        assert_eq!(mac.serial_number, "ABC123");
        assert_eq!(mac.uuid, "1234-5678");
    }
}
