//! Raw ACPI byte parsers for real firmware tables.
//!
//! The pre-existing [`crate::acpi_translator::AcpiTranslator`] only patches an
//! opaque DSDT blob. It never parses RSDP/XSDT/SDT headers. This additive
//! module parses the exact bytes dumped from a live OVMF boot (RSDP, XSDT,
//! FACP, APIC/MADT, HPET, MCFG, ...) and reports accept/reject plus a small
//! summary (OEM id, revision, entry counts). QEMU/OVMF tables only; no
//! Apple/private data is produced here.

use crate::error::HalError;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RsdpInfo {
    pub revision: u8,
    pub length: u32,
    pub rsdt_address: u32,
    pub xsdt_address: u64,
    pub checksum_ok: bool,
    pub extended_checksum_ok: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SdtHeader {
    pub signature: [u8; 4],
    pub signature_str: String,
    pub length: u32,
    pub revision: u8,
    pub oem_id: String,
    pub oem_table_id: String,
    pub oem_revision: u32,
    pub checksum_ok: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct MadtSummary {
    pub total_entries: usize,
    pub lapic: usize,
    pub ioapic: usize,
    pub interrupt_override: usize,
    pub nmi: usize,
    pub lapic_address_override: usize,
    pub other: usize,
    pub local_apic_address: u32,
    pub flags: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct McfgSummary {
    pub segment_groups: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FacpSummary {
    pub dsdt: u32,
    pub x_dsdt: u64,
    pub smi_cmd: u32,
    pub acpi_enable: u8,
}

fn checksum_is_zero(bytes: &[u8]) -> bool {
    bytes.iter().fold(0u8, |acc, &b| acc.wrapping_add(b)) == 0
}

fn ascii_lossy(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|&b| {
            if (0x20..0x7f).contains(&b) {
                b as char
            } else {
                '.'
            }
        })
        .collect()
}

#[allow(dead_code)]
fn read_u16_le(data: &[u8], offset: usize) -> Result<u16, HalError> {
    if offset + 2 > data.len() {
        return Err(HalError::Truncated {
            need: offset + 2,
            have: data.len(),
        });
    }
    Ok(u16::from_le_bytes([data[offset], data[offset + 1]]))
}

fn read_u32_le(data: &[u8], offset: usize) -> Result<u32, HalError> {
    if offset + 4 > data.len() {
        return Err(HalError::Truncated {
            need: offset + 4,
            have: data.len(),
        });
    }
    Ok(u32::from_le_bytes([
        data[offset],
        data[offset + 1],
        data[offset + 2],
        data[offset + 3],
    ]))
}

fn read_u64_le(data: &[u8], offset: usize) -> Result<u64, HalError> {
    if offset + 8 > data.len() {
        return Err(HalError::Truncated {
            need: offset + 8,
            have: data.len(),
        });
    }
    Ok(u64::from_le_bytes([
        data[offset],
        data[offset + 1],
        data[offset + 2],
        data[offset + 3],
        data[offset + 4],
        data[offset + 5],
        data[offset + 6],
        data[offset + 7],
    ]))
}

/// Parse an ACPI RSDP (20 bytes for ACPI 1.0, 36 bytes for ACPI 2.0+).
pub fn parse_rsdp(bytes: &[u8]) -> Result<RsdpInfo, HalError> {
    if bytes.len() < 20 {
        return Err(HalError::Truncated {
            need: 20,
            have: bytes.len(),
        });
    }
    if &bytes[0..8] != b"RSD PTR " {
        return Err(HalError::Invalid {
            reason: "RSDP signature mismatch",
        });
    }
    let checksum_ok = checksum_is_zero(&bytes[0..20]);
    if !checksum_ok {
        return Err(HalError::Invalid {
            reason: "RSDP v1 checksum nonzero",
        });
    }
    let revision = bytes[15];
    let rsdt_address = read_u32_le(bytes, 16)?;
    if revision < 2 {
        return Ok(RsdpInfo {
            revision,
            length: 20,
            rsdt_address,
            xsdt_address: 0,
            checksum_ok,
            extended_checksum_ok: true,
        });
    }
    if bytes.len() < 36 {
        return Err(HalError::Truncated {
            need: 36,
            have: bytes.len(),
        });
    }
    let length = read_u32_le(bytes, 20)?;
    if length < 36 {
        return Err(HalError::Invalid {
            reason: "RSDP length below extended header size",
        });
    }
    if bytes.len() < length as usize {
        return Err(HalError::Truncated {
            need: length as usize,
            have: bytes.len(),
        });
    }
    let xsdt_address = read_u64_le(bytes, 24)?;
    let extended_checksum_ok = checksum_is_zero(&bytes[0..length as usize]);
    if !extended_checksum_ok {
        return Err(HalError::Invalid {
            reason: "RSDP extended checksum nonzero",
        });
    }
    Ok(RsdpInfo {
        revision,
        length,
        rsdt_address,
        xsdt_address,
        checksum_ok,
        extended_checksum_ok,
    })
}

/// Parse a 36-byte ACPI SDT header (the prefix of every dumped table).
pub fn parse_sdt_header(bytes: &[u8]) -> Result<SdtHeader, HalError> {
    if bytes.len() < 36 {
        return Err(HalError::Truncated {
            need: 36,
            have: bytes.len(),
        });
    }
    let mut signature = [0u8; 4];
    signature.copy_from_slice(&bytes[0..4]);
    let length = read_u32_le(bytes, 4)?;
    if length < 36 {
        return Err(HalError::Invalid {
            reason: "SDT length below header size",
        });
    }
    if bytes.len() < length as usize {
        return Err(HalError::Truncated {
            need: length as usize,
            have: bytes.len(),
        });
    }
    let table = &bytes[0..length as usize];
    Ok(SdtHeader {
        signature,
        signature_str: ascii_lossy(&signature),
        length,
        revision: table[8],
        oem_id: ascii_lossy(&table[10..16]).trim().to_string(),
        oem_table_id: ascii_lossy(&table[16..24]).trim().to_string(),
        oem_revision: read_u32_le(table, 24)?,
        checksum_ok: checksum_is_zero(table),
    })
}

// The diagnostic header API preserves a checksum flag. Consumers that decode
// addresses or table-specific fields require a valid checksum and may only
// inspect the declared table, never trailing bytes in a larger input buffer.
fn validated_sdt(bytes: &[u8]) -> Result<(SdtHeader, &[u8]), HalError> {
    let header = parse_sdt_header(bytes)?;
    if !header.checksum_ok {
        return Err(HalError::Invalid {
            reason: "SDT checksum nonzero",
        });
    }
    let table = &bytes[..header.length as usize];
    Ok((header, table))
}

/// Entry addresses of a full XSDT image (header + u64 entries).
pub fn parse_xsdt_addresses(xsdt: &[u8]) -> Result<Vec<u64>, HalError> {
    let (header, xsdt) = validated_sdt(xsdt)?;
    if &header.signature != b"XSDT" {
        return Err(HalError::Invalid {
            reason: "XSDT signature mismatch",
        });
    }
    let body = (header.length as usize)
        .checked_sub(36)
        .ok_or(HalError::Invalid {
            reason: "XSDT length below header size",
        })?;
    if body % 8 != 0 {
        return Err(HalError::Invalid {
            reason: "XSDT body not a multiple of 8",
        });
    }
    let mut out = Vec::with_capacity(body / 8);
    for i in 0..body / 8 {
        out.push(read_u64_le(xsdt, 36 + i * 8)?);
    }
    Ok(out)
}

/// Entry addresses of a full RSDT image (header + u32 entries), widened to u64.
pub fn parse_rsdt_addresses(rsdt: &[u8]) -> Result<Vec<u64>, HalError> {
    let (header, rsdt) = validated_sdt(rsdt)?;
    if &header.signature != b"RSDT" {
        return Err(HalError::Invalid {
            reason: "RSDT signature mismatch",
        });
    }
    let body = (header.length as usize)
        .checked_sub(36)
        .ok_or(HalError::Invalid {
            reason: "RSDT length below header size",
        })?;
    if body % 4 != 0 {
        return Err(HalError::Invalid {
            reason: "RSDT body not a multiple of 4",
        });
    }
    let mut out = Vec::with_capacity(body / 4);
    for i in 0..body / 4 {
        out.push(read_u32_le(rsdt, 36 + i * 4)? as u64);
    }
    Ok(out)
}

/// Walk APIC/MADT subtables (44-byte header + type/length records).
pub fn parse_madt_summary(madt: &[u8]) -> Result<MadtSummary, HalError> {
    let (header, madt) = validated_sdt(madt)?;
    if &header.signature != b"APIC" {
        return Err(HalError::Invalid {
            reason: "MADT signature mismatch (expected APIC)",
        });
    }
    if madt.len() < 44 {
        return Err(HalError::Truncated {
            need: 44,
            have: madt.len(),
        });
    }
    let local_apic_address = read_u32_le(madt, 36)?;
    let flags = read_u32_le(madt, 40)?;
    let mut summary = MadtSummary {
        local_apic_address,
        flags,
        ..Default::default()
    };
    let mut offset = 44usize;
    let end = header.length as usize;
    while offset < end {
        if end - offset < 2 {
            return Err(HalError::Truncated {
                need: offset + 2,
                have: end,
            });
        }
        let entry_type = madt[offset];
        let entry_len = madt[offset + 1] as usize;
        if entry_len < 2 {
            return Err(HalError::Invalid {
                reason: "MADT entry length below 2",
            });
        }
        // ACPI 6.6 sections 5.2.12.2 through 5.2.12.8. Other types
        // remain structurally walkable but are not decoded by this summary.
        let minimum_len = match entry_type {
            0 => 8,
            1 => 12,
            2 => 10,
            3 => 8,
            4 => 6,
            5 => 12,
            _ => 2,
        };
        if entry_len < minimum_len {
            return Err(HalError::Invalid {
                reason: "MADT entry shorter than its known record type",
            });
        }
        if entry_len > end - offset {
            return Err(HalError::Truncated {
                need: offset + entry_len,
                have: end,
            });
        }
        summary.total_entries += 1;
        match entry_type {
            0 => summary.lapic += 1,
            1 => summary.ioapic += 1,
            2 => summary.interrupt_override += 1,
            4 => summary.nmi += 1,
            5 => summary.lapic_address_override += 1,
            _ => summary.other += 1,
        }
        offset += entry_len;
    }
    Ok(summary)
}

/// MCFG: 44-byte header + 16-byte allocation records.
pub fn parse_mcfg_summary(mcfg: &[u8]) -> Result<McfgSummary, HalError> {
    let (header, mcfg) = validated_sdt(mcfg)?;
    if &header.signature != b"MCFG" {
        return Err(HalError::Invalid {
            reason: "MCFG signature mismatch",
        });
    }
    // MCFG header is 36-byte SDT header + 8 reserved bytes.
    if mcfg.len() < 44 {
        return Err(HalError::Truncated {
            need: 44,
            have: mcfg.len(),
        });
    }
    let body = (header.length as usize)
        .checked_sub(44)
        .ok_or(HalError::Invalid {
            reason: "MCFG length below header size",
        })?;
    if body % 16 != 0 {
        return Err(HalError::Invalid {
            reason: "MCFG body not a multiple of 16",
        });
    }
    Ok(McfgSummary {
        segment_groups: body / 16,
    })
}

/// FACP: revision plus the DSDT/X_DSDT and SMI command fields.
pub fn parse_facp_summary(facp: &[u8]) -> Result<FacpSummary, HalError> {
    let (header, facp) = validated_sdt(facp)?;
    if &header.signature != b"FACP" {
        return Err(HalError::Invalid {
            reason: "FACP signature mismatch",
        });
    }
    // Offsets per ACPI spec: DSDT@40, SMI_CMD@48, ACPI_ENABLE@52, X_DSDT@140.
    if facp.len() < 53 {
        return Err(HalError::Truncated {
            need: 53,
            have: facp.len(),
        });
    }
    let dsdt = read_u32_le(facp, 40)?;
    let smi_cmd = read_u32_le(facp, 48)?;
    let acpi_enable = facp[52];
    let x_dsdt = if facp.len() >= 148 {
        read_u64_le(facp, 140)?
    } else {
        0
    };
    Ok(FacpSummary {
        dsdt,
        x_dsdt,
        smi_cmd,
        acpi_enable,
    })
}

#[allow(dead_code)]
pub fn signature_of(bytes: &[u8]) -> Option<[u8; 4]> {
    if bytes.len() < 4 {
        return None;
    }
    let mut sig = [0u8; 4];
    sig.copy_from_slice(&bytes[0..4]);
    Some(sig)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn checksum_fix_sdt(buf: &mut [u8]) {
        // ACPI SDT checksum byte lives at offset 9; adjusting it preserves
        // entry addresses, unlike patching the last byte.
        let sum: u8 = buf.iter().fold(0u8, |a, &b| a.wrapping_add(b));
        buf[9] = buf[9].wrapping_sub(sum);
    }

    fn minimal_sdt(sig: &[u8; 4], revision: u8) -> Vec<u8> {
        let mut v = vec![0u8; 44];
        v[0..4].copy_from_slice(sig);
        v[4..8].copy_from_slice(&44u32.to_le_bytes());
        v[8] = revision;
        v[10..16].copy_from_slice(b"BOCHS ");
        v[16..24].copy_from_slice(b"BXPC    ");
        checksum_fix_sdt(&mut v[0..44]);
        v
    }

    #[test]
    fn rsdp_v2_roundtrip() {
        let mut rsdp = vec![0u8; 36];
        rsdp[0..8].copy_from_slice(b"RSD PTR ");
        rsdp[15] = 2;
        rsdp[16..20].copy_from_slice(&0x12345678u32.to_le_bytes());
        rsdp[20..24].copy_from_slice(&36u32.to_le_bytes());
        rsdp[24..32].copy_from_slice(&0x9abcdef0u64.to_le_bytes());
        let sum20: u8 = rsdp[0..20].iter().fold(0u8, |a, &b| a.wrapping_add(b));
        rsdp[8] = rsdp[8].wrapping_sub(sum20);
        let sum36: u8 = rsdp.iter().fold(0u8, |a, &b| a.wrapping_add(b));
        rsdp[32] = rsdp[32].wrapping_sub(sum36);
        let info = parse_rsdp(&rsdp).unwrap();
        assert_eq!(info.revision, 2);
        assert_eq!(info.xsdt_address, 0x9abcdef0);
    }

    #[test]
    fn sdt_header_accepts_real_shape() {
        let table = minimal_sdt(b"FACP", 6);
        let header = parse_sdt_header(&table).unwrap();
        assert_eq!(&header.signature, b"FACP");
        assert_eq!(header.revision, 6);
        assert!(header.checksum_ok);
    }

    #[test]
    fn sdt_header_rejects_bad_checksum_only_as_flag() {
        // A wrong checksum is reported via checksum_ok=false, not Err, so the
        // harness can record REJECT-worthy tables without losing the summary.
        let mut table = minimal_sdt(b"APIC", 3);
        table[30] ^= 0x01;
        let header = parse_sdt_header(&table).unwrap();
        assert!(!header.checksum_ok);
    }

    #[test]
    fn xsdt_entries_decode() {
        let mut xsdt = vec![0u8; 36 + 16];
        xsdt[0..4].copy_from_slice(b"XSDT");
        xsdt[4..8].copy_from_slice(&52u32.to_le_bytes());
        xsdt[36..44].copy_from_slice(&0x1111111122222222u64.to_le_bytes());
        xsdt[44..52].copy_from_slice(&0x3333333344444444u64.to_le_bytes());
        checksum_fix_sdt(&mut xsdt);
        let addrs = parse_xsdt_addresses(&xsdt).unwrap();
        assert_eq!(addrs, vec![0x1111111122222222, 0x3333333344444444]);
    }

    #[test]
    fn rejects_truncated_inputs() {
        assert!(parse_rsdp(&[0u8; 10]).is_err());
        assert!(parse_sdt_header(&[0u8; 10]).is_err());
        assert!(parse_madt_summary(&minimal_sdt(b"APIC", 3)[..36]).is_err());
    }

    #[test]
    fn read_u16_helper_covers_pci_paths() {
        assert_eq!(read_u16_le(&[0x34, 0x12], 0).unwrap(), 0x1234);
        assert!(read_u16_le(&[0x00], 0).is_err());
    }
}
