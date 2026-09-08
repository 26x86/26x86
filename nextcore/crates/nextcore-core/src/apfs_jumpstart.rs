//! Bounded, read-only APFS EFI Jumpstart extraction; no PE validation or execution.
//!
//! Format: Apple's File System Reference (2020-06-22), pp. 8–39. Exact layout,
//! checksum convention and implementation limits are recorded in
//! `artifacts/apfs-jumpstart-20260908/contract.md`. All offsets are bytes relative
//! to the supplied APFS partition, not device LBAs or filesystem volume offsets.

use alloc::vec::Vec;

const NX_MAGIC: u32 = 0x4253_584e;
const JSDR_MAGIC: u32 = 0x5244_534a;
const MIN_BLOCK_SIZE: u32 = 4096;
const MAX_BLOCK_SIZE: u32 = 65536;
const MIN_CONTAINER_BYTES: u64 = 1024 * 1024;
const NX_JUMPSTART: usize = 1272;
const NX_FUSION_UUID: usize = 1280;
const JSDR_EXTENTS: usize = 176;
const EXTENT_SIZE: usize = 16;

/// A stable, partition-relative read-only byte source.
///
/// Return `Err` on short reads, media replacement or device failure. `Ok(())`
/// promises every requested byte was read. A caller must prevent concurrent
/// writes for the extraction's duration; metadata checksums do not authenticate
/// a source or prove that driver contents stayed unchanged.
pub trait ReadAt {
    type Error;

    fn read_exact_at(&mut self, offset: u64, out: &mut [u8]) -> Result<(), Self::Error>;
}

/// Resource policy, separate from APFS format limits.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct JumpstartLimits {
    pub max_driver_bytes: usize,
    pub max_extents: usize,
}

impl Default for JumpstartLimits {
    fn default() -> Self {
        Self {
            max_driver_bytes: 16 * 1024 * 1024,
            max_extents: 1024,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct JumpstartExtent {
    pub start_block: u64,
    pub block_count: u64,
}

/// Extracted opaque bytes. This is not a validated PE or trusted EFI image.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JumpstartDriver {
    pub bytes: Vec<u8>,
    pub block_size: u32,
    pub container_block_count: u64,
    pub jumpstart_block: u64,
    pub container_uuid: [u8; 16],
    pub extents: Vec<JumpstartExtent>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JumpstartError<E> {
    Io(E),
    OutOfBounds,
    ArithmeticOverflow,
    Allocation,
    InvalidLimits,
    InvalidBlockSize(u32),
    InvalidContainerSize,
    SourceChanged,
    BadMagic { jumpstart: bool },
    BadChecksum { jumpstart: bool },
    InvalidObject { jumpstart: bool },
    UnsupportedFusion,
    UnsupportedFeatures(u64),
    NoJumpstart,
    NegativeAddress,
    UnsupportedVersion(u32),
    InvalidFileLength,
    DriverTooLarge,
    InvalidExtentCount,
    TooManyExtents,
    ExtentTableOutOfBounds,
    EmptyExtent,
    InsufficientExtentCapacity,
}

/// Compute APFS Fletcher64 check words for one whole object block.
///
/// The first eight checksum bytes are excluded. `None` means that the supplied
/// object length is too short or is not an integral number of 32-bit words.
/// This function alone does not validate the object's format or authenticity.
pub fn fletcher64_checksum(object: &[u8]) -> Option<u64> {
    if object.len() < 8 || !object.len().is_multiple_of(4) {
        return None;
    }
    const MODULUS: u64 = u32::MAX as u64;
    let mut sum = 0_u64;
    let mut prefixes = 0_u64;
    for word in object[8..].chunks_exact(4) {
        let value = u32::from_le_bytes([word[0], word[1], word[2], word[3]]);
        sum = (sum + u64::from(value)) % MODULUS;
        prefixes = (prefixes + sum) % MODULUS;
    }
    let low = MODULUS - ((sum + prefixes) % MODULUS);
    let high = MODULUS - ((sum + low) % MODULUS);
    Some((high << 32) | low)
}

/// Extract exactly `nej_efi_file_len` bytes from a single-device APFS partition.
///
/// All metadata and extents are checked before reading driver data. Each read is
/// bounded by the caller's partition length and at most one container block.
/// Extents are concatenated in listed order, stopping at the declared file size;
/// surplus allocated blocks and final-block padding are not returned. Failures
/// return no partial image. This does not mount APFS or inspect/execute the file.
pub fn extract_jumpstart<R: ReadAt>(
    reader: &mut R,
    partition_len: u64,
    limits: JumpstartLimits,
) -> Result<JumpstartDriver, JumpstartError<R::Error>> {
    if limits.max_driver_bytes == 0 || limits.max_extents == 0 {
        return Err(JumpstartError::InvalidLimits);
    }

    // This untrusted prefix only selects a fixed-bounded metadata read. Its
    // geometry is not used to seek until the full block checksum has passed.
    let mut prefix = [0_u8; 40];
    read_bounded(reader, partition_len, 0, &mut prefix)?;
    let block_size = le32(&prefix, 36);
    if !(MIN_BLOCK_SIZE..=MAX_BLOCK_SIZE).contains(&block_size) || !block_size.is_power_of_two() {
        return Err(JumpstartError::InvalidBlockSize(block_size));
    }
    let mut block = zeroed_bytes(block_size as usize)?;
    read_bounded(reader, partition_len, 0, &mut block)?;
    if block[..prefix.len()] != prefix {
        return Err(JumpstartError::SourceChanged);
    }
    check_object(&block, NX_MAGIC, 1, false, None)?;
    let block_count = le64(&block, 40);
    let container_bytes = block_count
        .checked_mul(u64::from(block_size))
        .ok_or(JumpstartError::ArithmeticOverflow)?;
    if container_bytes < MIN_CONTAINER_BYTES {
        return Err(JumpstartError::InvalidContainerSize);
    }
    if container_bytes > partition_len {
        return Err(JumpstartError::OutOfBounds);
    }
    let incompatible = le64(&block, 64);
    if incompatible & 0x100 != 0
        || le64(&block, 48) & 2 != 0
        || block[NX_FUSION_UUID..NX_FUSION_UUID + 16]
            .iter()
            .any(|byte| *byte != 0)
        || block[1352..1384].iter().any(|byte| *byte != 0)
    {
        return Err(JumpstartError::UnsupportedFusion);
    }
    if incompatible != 2 {
        return Err(JumpstartError::UnsupportedFeatures(incompatible));
    }
    let mut container_uuid = [0_u8; 16];
    container_uuid.copy_from_slice(&block[72..88]);
    let jumpstart_block = positive_paddr(le64(&block, NX_JUMPSTART))?;
    if jumpstart_block == 0 {
        return Err(JumpstartError::NoJumpstart);
    }
    let jumpstart_offset = block_range(jumpstart_block, 1, block_count, block_size)?;
    read_bounded(reader, container_bytes, jumpstart_offset, &mut block)?;
    check_object(&block, JSDR_MAGIC, 0x14, true, Some(jumpstart_block))?;
    let version = le32(&block, 36);
    if version != 1 {
        return Err(JumpstartError::UnsupportedVersion(version));
    }
    let file_len =
        usize::try_from(le32(&block, 40)).map_err(|_| JumpstartError::ArithmeticOverflow)?;
    if file_len == 0 {
        return Err(JumpstartError::InvalidFileLength);
    }
    if file_len > limits.max_driver_bytes {
        return Err(JumpstartError::DriverTooLarge);
    }
    let count =
        usize::try_from(le32(&block, 44)).map_err(|_| JumpstartError::ArithmeticOverflow)?;
    if count == 0 {
        return Err(JumpstartError::InvalidExtentCount);
    }
    if count > limits.max_extents {
        return Err(JumpstartError::TooManyExtents);
    }
    let table_end = count
        .checked_mul(EXTENT_SIZE)
        .and_then(|bytes| JSDR_EXTENTS.checked_add(bytes))
        .ok_or(JumpstartError::ArithmeticOverflow)?;
    if table_end > block.len() {
        return Err(JumpstartError::ExtentTableOutOfBounds);
    }
    let mut extents = Vec::new();
    extents
        .try_reserve_exact(count)
        .map_err(|_| JumpstartError::Allocation)?;
    let mut capacity = 0_u64;
    for record in block[JSDR_EXTENTS..table_end].chunks_exact(EXTENT_SIZE) {
        let start_block = positive_paddr(le64(record, 0))?;
        let count = le64(record, 8);
        if count == 0 {
            return Err(JumpstartError::EmptyExtent);
        }
        block_range(start_block, count, block_count, block_size)?;
        let size = count
            .checked_mul(u64::from(block_size))
            .ok_or(JumpstartError::ArithmeticOverflow)?;
        capacity = capacity
            .checked_add(size)
            .ok_or(JumpstartError::ArithmeticOverflow)?;
        extents.push(JumpstartExtent {
            start_block,
            block_count: count,
        });
    }
    if capacity < file_len as u64 {
        return Err(JumpstartError::InsufficientExtentCapacity);
    }

    let mut bytes = zeroed_bytes(file_len)?;
    let mut written = 0;
    for extent in &extents {
        // Only iterate blocks needed for the bounded file, not untrusted excess
        // extent capacity. The complete extent table was already checked above.
        let remaining = file_len - written;
        if remaining == 0 {
            break;
        }
        let needed = (remaining as u64).div_ceil(u64::from(block_size));
        for index in 0..extent.block_count.min(needed) {
            let address = extent
                .start_block
                .checked_add(index)
                .ok_or(JumpstartError::ArithmeticOverflow)?;
            let offset = block_range(address, 1, block_count, block_size)?;
            read_bounded(reader, container_bytes, offset, &mut block)?;
            let count = (file_len - written).min(block.len());
            bytes[written..written + count].copy_from_slice(&block[..count]);
            written += count;
        }
    }
    debug_assert_eq!(written, file_len);
    Ok(JumpstartDriver {
        bytes,
        block_size,
        container_block_count: block_count,
        jumpstart_block,
        container_uuid,
        extents,
    })
}

fn check_object<E>(
    block: &[u8],
    magic: u32,
    object_type: u32,
    jumpstart: bool,
    physical_oid: Option<u64>,
) -> Result<(), JumpstartError<E>> {
    if fletcher64_checksum(block) != Some(le64(block, 0)) {
        return Err(JumpstartError::BadChecksum { jumpstart });
    }
    if le32(block, 32) != magic {
        return Err(JumpstartError::BadMagic { jumpstart });
    }
    let kind = le32(block, 24);
    let storage = kind & 0xc000_0000;
    if kind & 0xffff != object_type
        || kind & 0x3fff_0000 != 0
        || storage == 0xc000_0000
        || le32(block, 28) != 0
        || le64(block, 16) == 0
        || physical_oid.is_some_and(|oid| storage != 0x4000_0000 || le64(block, 8) != oid)
    {
        return Err(JumpstartError::InvalidObject { jumpstart });
    }
    Ok(())
}

fn positive_paddr<E>(raw: u64) -> Result<u64, JumpstartError<E>> {
    if raw > i64::MAX as u64 {
        Err(JumpstartError::NegativeAddress)
    } else {
        Ok(raw)
    }
}

fn block_range<E>(
    start: u64,
    count: u64,
    block_count: u64,
    block_size: u32,
) -> Result<u64, JumpstartError<E>> {
    let end = start
        .checked_add(count)
        .ok_or(JumpstartError::ArithmeticOverflow)?;
    if end > block_count {
        return Err(JumpstartError::OutOfBounds);
    }
    start
        .checked_mul(u64::from(block_size))
        .ok_or(JumpstartError::ArithmeticOverflow)
}

fn read_bounded<R: ReadAt>(
    reader: &mut R,
    limit: u64,
    offset: u64,
    out: &mut [u8],
) -> Result<(), JumpstartError<R::Error>> {
    let end = offset
        .checked_add(out.len() as u64)
        .ok_or(JumpstartError::ArithmeticOverflow)?;
    if end > limit {
        return Err(JumpstartError::OutOfBounds);
    }
    reader
        .read_exact_at(offset, out)
        .map_err(JumpstartError::Io)
}

fn zeroed_bytes<E>(size: usize) -> Result<Vec<u8>, JumpstartError<E>> {
    let mut bytes = Vec::new();
    bytes
        .try_reserve_exact(size)
        .map_err(|_| JumpstartError::Allocation)?;
    bytes.resize(size, 0);
    Ok(bytes)
}

// Callers pass only checked-size prefixes, blocks or complete extent records.
fn le32(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap())
}

fn le64(bytes: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(bytes[offset..offset + 8].try_into().unwrap())
}
