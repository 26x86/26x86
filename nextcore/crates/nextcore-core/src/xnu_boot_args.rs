//! Independent byte encoders for the public xnu-12377 boot-argument profiles.
//!
//! Public format reference, not an imported C layout:
//! <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/i386/boot.h>
//! The 32-bit bootstrap consumes the physical ranges before establishing its
//! full mappings. The caller must allocate them, preserve them across firmware
//! exit, and separately supply/validate the actual DT and memory-map contents.
//! This encoder does not establish runtime, entropy, security, video, or KC
//! providers. Zeroed unsupported fields do not establish their safe absence.

use core::fmt;

pub const BOOT_ARGS_SIZE: usize = 4096;
pub const MAX_COMMAND_LINE: usize = 1023;
const PAGE_SIZE: u64 = 4096;
const LOW_ADDRESS_LIMIT: u64 = 1 << 32;

#[derive(Clone, Copy, Debug)]
pub struct XnuBootArgsInput<'a> {
    pub memory_map_phys: u64,
    pub memory_map_size: u64,
    pub memory_map_descriptor_size: u32,
    pub memory_map_descriptor_version: u32,
    pub device_tree_phys: u64,
    pub device_tree_size: u64,
    /// Physical start of the loaded image and protected handoff arena.
    pub kernel_phys: u64,
    /// Covered bytes, including map, DT, boot_args and other handoff storage.
    /// The caller must also reserve backing for the kernel's early allocations
    /// after this range and ensure boot_args itself is inside it.
    pub kernel_size: u64,
    /// Actual physical RAM bytes; this field is not limited to 4 GiB.
    pub physical_memory_size: u64,
    /// The external firmware table is not required to be in the kernel arena.
    /// Only pointer representation/alignment is checked, not table contents.
    pub efi_system_table_phys: u64,
    pub command_line: &'a str,
}

/// Explicit revision-1 extension. This is supplied range metadata, not proof
/// of an allocated/relocated KC or of its entry-point VA-to-PA correspondence.
#[derive(Clone, Copy, Debug)]
pub struct XnuFilesetBootArgsInput<'a> {
    pub common: XnuBootArgsInput<'a>,
    /// Physical address consumed by early i386 initialization despite the
    /// public wire field's name. Do not pass an already translated kernel VA.
    pub collection_header_phys: u64,
    /// Actual validated outer header plus load-command extent. The encoder
    /// checks its range but does not read or authenticate those bytes.
    pub collection_header_size: u64,
    /// A caller-selected slide. Encoding does not choose or validate the
    /// platform's placement/relocation policy, alignment or entry mapping.
    pub kernel_slide: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BootArgsError {
    InvalidCommandLine,
    InvalidMemoryMap,
    InvalidDeviceTree,
    InvalidKernelRange,
    InvalidPhysicalMemory,
    InvalidEfiSystemTable,
    HandoffOutsideKernel,
    OverlappingHandoff,
    InvalidCollectionHeader,
}

impl fmt::Display for BootArgsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidCommandLine => "INVALID_COMMAND_LINE",
            Self::InvalidMemoryMap => "INVALID_MEMORY_MAP",
            Self::InvalidDeviceTree => "INVALID_DEVICE_TREE",
            Self::InvalidKernelRange => "INVALID_KERNEL_RANGE",
            Self::InvalidPhysicalMemory => "INVALID_PHYSICAL_MEMORY",
            Self::InvalidEfiSystemTable => "INVALID_EFI_SYSTEM_TABLE",
            Self::HandoffOutsideKernel => "HANDOFF_OUTSIDE_KERNEL",
            Self::OverlappingHandoff => "OVERLAPPING_HANDOFF",
            Self::InvalidCollectionHeader => "INVALID_COLLECTION_HEADER",
        })
    }
}

/// Encode revision 0, version 2, EFI64, zero slide using explicit LE offsets.
/// EFI64 describes firmware pointer width, not the CPU entry instruction mode.
/// This is range validation only; call `flat_dt::validate` on the actual DT.
pub fn encode_boot_args(
    input: &XnuBootArgsInput<'_>,
) -> Result<[u8; BOOT_ARGS_SIZE], BootArgsError> {
    if input.command_line.len() > MAX_COMMAND_LINE
        || !input.command_line.is_ascii()
        || input.command_line.as_bytes().contains(&0)
    {
        return Err(BootArgsError::InvalidCommandLine);
    }
    let stride = input.memory_map_descriptor_size;
    if stride < 40
        || stride % 8 != 0
        || input.memory_map_descriptor_version != 1
        || input.memory_map_phys % 8 != 0
        || input.memory_map_size % u64::from(stride) != 0
    {
        return Err(BootArgsError::InvalidMemoryMap);
    }
    let (map_phys, map_size, map_end) = low_range(
        input.memory_map_phys,
        input.memory_map_size,
        BootArgsError::InvalidMemoryMap,
    )?;
    if input.device_tree_phys % 4 != 0
        || input.device_tree_size < 8
        || input.device_tree_size % 4 != 0
    {
        return Err(BootArgsError::InvalidDeviceTree);
    }
    let (dt_phys, dt_size, dt_end) = low_range(
        input.device_tree_phys,
        input.device_tree_size,
        BootArgsError::InvalidDeviceTree,
    )?;
    let (kernel_phys, kernel_size, kernel_end) = low_range(
        input.kernel_phys,
        input.kernel_size,
        BootArgsError::InvalidKernelRange,
    )?;
    // vstart uses a u32 allocation cursor, then rounds it up to a page.
    if input.kernel_phys % PAGE_SIZE != 0
        || kernel_end
            .checked_add(PAGE_SIZE - 1)
            .map(|end| end & !(PAGE_SIZE - 1))
            .is_none_or(|end| end >= LOW_ADDRESS_LIMIT)
    {
        return Err(BootArgsError::InvalidKernelRange);
    }
    if input.memory_map_phys < input.kernel_phys
        || map_end > kernel_end
        || input.device_tree_phys < input.kernel_phys
        || dt_end > kernel_end
    {
        return Err(BootArgsError::HandoffOutsideKernel);
    }
    if input.memory_map_phys < dt_end && input.device_tree_phys < map_end {
        return Err(BootArgsError::OverlappingHandoff);
    }
    // The early physmap calculation adds 4 GiB for physical address holes.
    if input.physical_memory_size == 0
        || input
            .physical_memory_size
            .checked_add(LOW_ADDRESS_LIMIT)
            .is_none()
    {
        return Err(BootArgsError::InvalidPhysicalMemory);
    }
    if input.efi_system_table_phys == 0 || input.efi_system_table_phys % 8 != 0 {
        return Err(BootArgsError::InvalidEfiSystemTable);
    }
    let system_table = u32::try_from(input.efi_system_table_phys)
        .map_err(|_| BootArgsError::InvalidEfiSystemTable)?;

    let mut bytes = [0u8; BOOT_ARGS_SIZE];
    bytes[2..4].copy_from_slice(&2u16.to_le_bytes());
    bytes[4] = 64;
    bytes[8..8 + input.command_line.len()].copy_from_slice(input.command_line.as_bytes());
    write_u32(&mut bytes, 0x408, map_phys);
    write_u32(&mut bytes, 0x40c, map_size);
    write_u32(&mut bytes, 0x410, stride);
    write_u32(&mut bytes, 0x414, input.memory_map_descriptor_version);
    write_u32(&mut bytes, 0x430, dt_phys);
    write_u32(&mut bytes, 0x434, dt_size);
    write_u32(&mut bytes, 0x438, kernel_phys);
    write_u32(&mut bytes, 0x43c, kernel_size);
    write_u32(&mut bytes, 0x450, system_table);
    bytes[0x478..0x480].copy_from_slice(&input.physical_memory_size.to_le_bytes());
    Ok(bytes)
}

/// Encode version 2, revision 1 with an explicit physical fileset header.
///
/// The header must fit the caller's protected low kernel range without
/// overlapping the map or DT. The caller must additionally keep boot_args,
/// loaded segments and every other live handoff allocation disjoint, apply
/// only firmware-owned fixups and establish all required platform providers.
/// No existing EFI entry path is enabled by this codec.
///
/// Offsets were independently compiled from pinned public boot.h (C11,
/// x86_64): slide=1108, KC header=1256, total size=4096.
pub fn encode_fileset_boot_args(
    input: &XnuFilesetBootArgsInput<'_>,
) -> Result<[u8; BOOT_ARGS_SIZE], BootArgsError> {
    let mut bytes = encode_boot_args(&input.common)?;
    if input.collection_header_phys % 8 != 0 || input.collection_header_size < 32 {
        return Err(BootArgsError::InvalidCollectionHeader);
    }
    let (_, _, header_end) = low_range(
        input.collection_header_phys,
        input.collection_header_size,
        BootArgsError::InvalidCollectionHeader,
    )?;
    let common = &input.common;
    // These sums were checked by the common encoder before producing bytes.
    let kernel_end = common.kernel_phys + common.kernel_size;
    let map_end = common.memory_map_phys + common.memory_map_size;
    let dt_end = common.device_tree_phys + common.device_tree_size;
    if input.collection_header_phys < common.kernel_phys || header_end > kernel_end {
        return Err(BootArgsError::InvalidCollectionHeader);
    }
    if (input.collection_header_phys < map_end && common.memory_map_phys < header_end)
        || (input.collection_header_phys < dt_end && common.device_tree_phys < header_end)
    {
        return Err(BootArgsError::OverlappingHandoff);
    }
    bytes[..2].copy_from_slice(&1u16.to_le_bytes());
    write_u32(&mut bytes, 1108, input.kernel_slide);
    bytes[1256..1264].copy_from_slice(&input.collection_header_phys.to_le_bytes());
    Ok(bytes)
}

fn low_range(phys: u64, size: u64, error: BootArgsError) -> Result<(u32, u32, u64), BootArgsError> {
    let end = phys.checked_add(size).ok_or(error)?;
    if phys == 0 || size == 0 || end > LOW_ADDRESS_LIMIT {
        return Err(error);
    }
    Ok((
        u32::try_from(phys).map_err(|_| error)?,
        u32::try_from(size).map_err(|_| error)?,
        end,
    ))
}

fn write_u32(bytes: &mut [u8; BOOT_ARGS_SIZE], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
