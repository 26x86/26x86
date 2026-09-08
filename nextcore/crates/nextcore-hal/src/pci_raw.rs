//! Raw PCI config-space decoder.
//!
//! The pre-existing [`crate::pci_translator::PciTranslator`] takes an already
//! decoded [`crate::pci_translator::PciDevice`]. This additive module decodes
//! the exact 64-byte config-space header dumped from a live QEMU q35 boot
//! (via port CF8/CFC) into that struct so the translator can run over real
//! vendor/device IDs.

use crate::error::HalError;
use crate::pci_translator::PciDevice;

/// Decode a Type 0 64-byte PCI config-space header into a [`PciDevice`].
///
/// Layout (little-endian): vendor@0x00, device@0x02, revision@0x08,
/// prog-if@0x09, subclass@0x0A, class@0x0B, subsystem vendor@0x2C,
/// subsystem device@0x2E. A vendor of 0xFFFF means "no device".
/// Header Type bit 7 denotes multifunction; other layout codes are rejected
/// because their headers do not carry subsystem IDs at these offsets.
pub fn decode_config_space(bytes: &[u8]) -> Result<PciDevice, HalError> {
    if bytes.len() < 64 {
        return Err(HalError::Truncated {
            need: 64,
            have: bytes.len(),
        });
    }
    let vendor_id = u16::from_le_bytes([bytes[0], bytes[1]]);
    if vendor_id == 0xFFFF {
        return Err(HalError::Invalid {
            reason: "empty PCI slot (vendor 0xFFFF)",
        });
    }
    if bytes[0x0E] & 0x7F != 0 {
        return Err(HalError::Invalid {
            reason: "unsupported PCI header layout (only Type 0 is decoded)",
        });
    }
    Ok(PciDevice {
        vendor_id,
        device_id: u16::from_le_bytes([bytes[2], bytes[3]]),
        revision: bytes[8],
        prog_if: bytes[9],
        subclass: bytes[10],
        class_code: bytes[11],
        subsystem_vendor_id: u16::from_le_bytes([bytes[44], bytes[45]]),
        subsystem_device_id: u16::from_le_bytes([bytes[46], bytes[47]]),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decodes_q35_host_bridge_shape() {
        let mut cfg = vec![0u8; 64];
        cfg[0..2].copy_from_slice(&0x8086u16.to_le_bytes());
        cfg[2..4].copy_from_slice(&0x29C0u16.to_le_bytes());
        cfg[8] = 0x02;
        cfg[11] = 0x06;
        let dev = decode_config_space(&cfg).unwrap();
        assert_eq!(dev.vendor_id, 0x8086);
        assert_eq!(dev.device_id, 0x29C0);
        assert_eq!(dev.class_code, 0x06);
    }

    #[test]
    fn rejects_empty_slot_and_truncation() {
        assert!(decode_config_space(&[0xFFu8; 64]).is_err());
        assert!(decode_config_space(&[0u8; 16]).is_err());
    }
}
