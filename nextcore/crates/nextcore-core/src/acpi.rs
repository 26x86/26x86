use crate::error::{CoreError, Result};

const RSDP_SIGNATURE: &[u8; 8] = b"RSD PTR ";
const XSDT_SIGNATURE: &[u8; 4] = b"XSDT";
const RSDT_SIGNATURE: &[u8; 4] = b"RSDT";

const RSDP_LENGTH: usize = 36;
const XSDT_HEADER_SIZE: usize = 36;

#[derive(Debug, Clone)]
pub struct AcpiSignature(pub [u8; 4]);

#[derive(Debug, Clone)]
pub struct AcpiTableHeader {
    pub length: u32,
    pub revision: u8,
    pub checksum: u8,
    pub oem_id: [u8; 6],
    pub oem_table_id: [u8; 8],
}

#[derive(Debug, Clone)]
pub struct Rsdp {
    pub signature: [u8; 8],
    pub checksum: u8,
    pub rsdt_address: u32,
    pub length: u32,
    pub xsdt_address: u64,
    pub extended_checksum: u8,
}

#[derive(Debug, Clone)]
pub struct Xsdt {
    pub header: AcpiTableHeader,
    pub table_addresses: Vec<u64>,
}

#[derive(Debug)]
pub struct AcpiTables<'a> {
    data: &'a [u8],
    xsdt: Xsdt,
}

impl<'a> AcpiTables<'a> {
    pub fn parse(data: &'a [u8]) -> Result<Self> {
        let rsdp = Self::find_rsdp(data)?;
        let use_xsdt = rsdp.xsdt_address != 0;

        if use_xsdt {
            let xsdt_offset = rsdp.xsdt_address as usize;
            if xsdt_offset + XSDT_HEADER_SIZE > data.len() {
                return Err(CoreError::AcpiInvalid("XSDT extends beyond data"));
            }
            let xsdt = Self::parse_xsdt_table(data, xsdt_offset)?;
            Ok(Self { data, xsdt })
        } else {
            let rsdt_offset = rsdp.rsdt_address as usize;
            if rsdt_offset + XSDT_HEADER_SIZE > data.len() {
                return Err(CoreError::AcpiInvalid("RSDT extends beyond data"));
            }
            let xsdt = Self::parse_rsdt_table(data, rsdt_offset)?;
            Ok(Self { data, xsdt })
        }
    }

    pub fn find_table(&self, signature: &[u8; 4]) -> Option<&'a [u8]> {
        for &addr in &self.xsdt.table_addresses {
            let offset = addr as usize;
            if offset + 4 > self.data.len() {
                continue;
            }
            if &self.data[offset..offset + 4] == signature {
                let len = read_u32_le(self.data, offset + 4)?;
                let end = offset + len as usize;
                if end <= self.data.len() {
                    return Some(&self.data[offset..end]);
                }
            }
        }
        None
    }

    pub fn table_signatures(&self) -> Vec<[u8; 4]> {
        self.xsdt
            .table_addresses
            .iter()
            .filter_map(|&addr| {
                let offset = addr as usize;
                if offset + 4 <= self.data.len() {
                    let mut sig = [0u8; 4];
                    sig.copy_from_slice(&self.data[offset..offset + 4]);
                    Some(sig)
                } else {
                    None
                }
            })
            .collect()
    }

    fn find_rsdp(data: &[u8]) -> Result<Rsdp> {
        if data.len() < RSDP_LENGTH {
            return Err(CoreError::AcpiNotFound("data too short for RSDP"));
        }

        for i in 0..data.len().saturating_sub(RSDP_LENGTH) {
            if &data[i..i + 8] == RSDP_SIGNATURE {
                let rsdp_checksum = checksum(&data[i..i + 20]);
                if rsdp_checksum != 0 {
                    continue;
                }

                let xsdt_address = read_u64_le(data, i + 24).ok_or_else(|| {
                    CoreError::AcpiInvalid("failed to read XSDT address")
                })?;

                let mut sig = [0u8; 8];
                sig.copy_from_slice(&data[i..i + 8]);

                let length = if xsdt_address != 0 {
                    read_u32_le(data, i + 20).unwrap_or(36)
                } else {
                    36
                };

                let ext_checksum = if length >= 36 && i + length as usize <= data.len() {
                    checksum(&data[i..i + length as usize])
                } else {
                    0
                };

                return Ok(Rsdp {
                    signature: sig,
                    checksum: rsdp_checksum,
                    rsdt_address: read_u32_le(data, i + 16).unwrap_or(0),
                    length,
                    xsdt_address,
                    extended_checksum: ext_checksum,
                });
            }
        }

        Err(CoreError::AcpiNotFound("RSDP"))
    }

    fn parse_xsdt_table(data: &'a [u8], offset: usize) -> Result<Xsdt> {
        if offset + XSDT_HEADER_SIZE > data.len() {
            return Err(CoreError::AcpiInvalid("XSDT header truncated"));
        }

        let sig = &data[offset..offset + 4];
        if sig != XSDT_SIGNATURE {
            return Err(CoreError::AcpiInvalid("XSDT signature mismatch"));
        }

        let header = parse_table_header(data, offset)?;
        let count = (header.length as usize - XSDT_HEADER_SIZE) / 8;
        let mut table_addresses = Vec::with_capacity(count);

        for i in 0..count {
            let addr_offset = offset + XSDT_HEADER_SIZE + i * 8;
            if addr_offset + 8 > data.len() {
                break;
            }
            let addr = read_u64_le(data, addr_offset).ok_or_else(|| {
                CoreError::AcpiInvalid("failed to read XSDT entry address")
            })?;
            table_addresses.push(addr);
        }

        Ok(Xsdt {
            header,
            table_addresses,
        })
    }

    fn parse_rsdt_table(data: &'a [u8], offset: usize) -> Result<Xsdt> {
        if offset + XSDT_HEADER_SIZE > data.len() {
            return Err(CoreError::AcpiInvalid("RSDT header truncated"));
        }

        let sig = &data[offset..offset + 4];
        if sig != RSDT_SIGNATURE {
            return Err(CoreError::AcpiInvalid("RSDT signature mismatch"));
        }

        let header = parse_table_header(data, offset)?;
        let count = (header.length as usize - XSDT_HEADER_SIZE) / 4;
        let mut table_addresses = Vec::with_capacity(count);

        for i in 0..count {
            let addr_offset = offset + XSDT_HEADER_SIZE + i * 4;
            if addr_offset + 4 > data.len() {
                break;
            }
            let addr = read_u32_le(data, addr_offset)
                .map(|v| v as u64)
                .ok_or_else(|| {
                    CoreError::AcpiInvalid("failed to read RSDT entry address")
                })?;
            table_addresses.push(addr);
        }

        Ok(Xsdt {
            header,
            table_addresses,
        })
    }
}

fn parse_table_header(data: &[u8], offset: usize) -> Result<AcpiTableHeader> {
    let end = offset + 36;
    if end > data.len() {
        return Err(CoreError::AcpiInvalid("table header extends beyond data"));
    }

    let length = read_u32_le(data, offset + 4).unwrap_or(0);
    let revision = data[offset + 8];
    let checksum = data[offset + 9];

    let mut oem_id = [0u8; 6];
    oem_id.copy_from_slice(&data[offset + 10..offset + 16]);

    let mut oem_table_id = [0u8; 8];
    oem_table_id.copy_from_slice(&data[offset + 16..offset + 24]);

    Ok(AcpiTableHeader {
        length,
        revision,
        checksum,
        oem_id,
        oem_table_id,
    })
}

fn read_u32_le(data: &[u8], offset: usize) -> Option<u32> {
    if offset + 4 > data.len() {
        return None;
    }
    Some(u32::from_le_bytes([
        data[offset],
        data[offset + 1],
        data[offset + 2],
        data[offset + 3],
    ]))
}

fn read_u64_le(data: &[u8], offset: usize) -> Option<u64> {
    if offset + 8 > data.len() {
        return None;
    }
    Some(u64::from_le_bytes([
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

fn checksum(data: &[u8]) -> u8 {
    data.iter().fold(0u8, |acc, &b| acc.wrapping_add(b))
}
