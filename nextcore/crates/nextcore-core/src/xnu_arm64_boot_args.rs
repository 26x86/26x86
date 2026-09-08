//! Independent ARM64 boot-argument byte codec; it does not enter a kernel.
//!
//! Public profile: xnu-12377.121.6, revision 2/version 2, LP64.
//! <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h>
//! The entry consumes x0 as a PA, but this codec encodes the DT's initial KVA.
//! The caller must copy and reserve both objects at their declared PAs. Encoding
//! does not validate a kernel's entry, bootstrap mappings, CPU, devices or trust.

use crate::flat_dt;
use core::fmt;

pub const ARM64_BOOT_ARGS_SIZE: usize = 1152;
pub const ARM64_COMMAND_LINE_MAX: usize = 1023;
pub const VMAPPLE_PAGE_SIZE: u64 = 16 * 1024;
pub const ARM64_DARK_BOOT: u64 = 1;

/// Public video words only. Supplying them does not validate their backing or
/// display operation; all zeroes likewise do not prove headless boot support.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Arm64BootVideo {
    pub base_address: u64,
    pub display: u64,
    pub row_bytes: u64,
    pub width: u64,
    pub height: u64,
    pub depth: u64,
}

#[derive(Clone, Copy, Debug)]
pub struct Arm64BootArgsInput<'a> {
    /// Kernel-managed physical RAM window, not just the kernel image.
    pub physical_base: u64,
    pub virtual_base: u64,
    pub memory_size: u64,
    /// Actual DRAM bytes; must match /chosen/dram-size in the supplied DT.
    pub actual_memory_size: u64,
    /// End of occupied boot storage. Later kernel allocations begin here.
    pub top_of_kernel_data: u64,
    /// Complete occupied kernel range, including its zero-fill and holes.
    /// These supplied coordinates are not evidence that an image was loaded.
    pub kernel_phys: u64,
    pub kernel_size: u64,
    pub boot_args_phys: u64,
    pub device_tree_phys: u64,
    /// Actual bytes to preserve at device_tree_phys, in XNU's flat DT format.
    pub device_tree: &'a [u8],
    pub command_line: &'a str,
    pub machine_type: u32,
    pub boot_flags: u64,
    pub video: Arm64BootVideo,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Arm64BootArgsError {
    InvalidCommandLine,
    UnsupportedBootFlags,
    InvalidMemoryRange,
    InvalidVirtualRange,
    InvalidKernelRange,
    InvalidOccupiedTop,
    InvalidArgumentRange,
    InvalidDeviceTree,
    MissingDramProperties,
    InvalidDramProperties,
    HandoffOutsideOccupiedMemory,
    OverlappingHandoff,
}

impl fmt::Display for Arm64BootArgsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidCommandLine => "ARM64_INVALID_COMMAND_LINE",
            Self::UnsupportedBootFlags => "ARM64_UNSUPPORTED_BOOT_FLAGS",
            Self::InvalidMemoryRange => "ARM64_INVALID_MEMORY_RANGE",
            Self::InvalidVirtualRange => "ARM64_INVALID_VIRTUAL_RANGE",
            Self::InvalidKernelRange => "ARM64_INVALID_KERNEL_RANGE",
            Self::InvalidOccupiedTop => "ARM64_INVALID_OCCUPIED_TOP",
            Self::InvalidArgumentRange => "ARM64_INVALID_ARGUMENT_RANGE",
            Self::InvalidDeviceTree => "ARM64_INVALID_DEVICE_TREE",
            Self::MissingDramProperties => "ARM64_MISSING_DRAM_PROPERTIES",
            Self::InvalidDramProperties => "ARM64_INVALID_DRAM_PROPERTIES",
            Self::HandoffOutsideOccupiedMemory => "ARM64_HANDOFF_OUTSIDE_OCCUPIED_MEMORY",
            Self::OverlappingHandoff => "ARM64_OVERLAPPING_HANDOFF",
        })
    }
}

/// Encoded bytes and declared addresses, without any allocation or entry right.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Arm64BootArgsEncoding {
    bytes: [u8; ARM64_BOOT_ARGS_SIZE],
    physical_address: u64,
    device_tree_virtual_address: u64,
}

impl Arm64BootArgsEncoding {
    pub fn as_bytes(&self) -> &[u8; ARM64_BOOT_ARGS_SIZE] {
        &self.bytes
    }

    /// The PA a future entry adapter would place in x0 after copying the bytes.
    pub const fn physical_address(&self) -> u64 {
        self.physical_address
    }

    pub const fn device_tree_virtual_address(&self) -> u64 {
        self.device_tree_virtual_address
    }

    /// A codec cannot establish a live CPU, loaded kernel or platform contract.
    pub const fn execution_ready(&self) -> bool {
        false
    }
}

#[derive(Clone, Copy)]
struct Range {
    start: u64,
    end: u64,
}

impl Range {
    fn new(start: u64, size: u64, error: Arm64BootArgsError) -> Result<Self, Arm64BootArgsError> {
        if size == 0 {
            return Err(error);
        }
        Ok(Self {
            start,
            end: start.checked_add(size).ok_or(error)?,
        })
    }

    fn contains(self, other: Self) -> bool {
        self.start <= other.start && other.end <= self.end
    }

    fn overlaps(self, other: Self) -> bool {
        self.start < other.end && other.start < self.end
    }
}

/// Validate the selected public range/DT profile and encode its argument bytes.
///
/// This does not round memory upward or validate the 32-MiB bootstrap block
/// coverage. The image header position, within-block VA/PA correspondence and
/// bootstrap-table capacity need a separate placement check before execution.
pub fn encode_arm64_boot_args(
    input: &Arm64BootArgsInput<'_>,
) -> Result<Arm64BootArgsEncoding, Arm64BootArgsError> {
    use Arm64BootArgsError as Error;
    if input.command_line.len() > ARM64_COMMAND_LINE_MAX
        || !input.command_line.is_ascii()
        || input.command_line.as_bytes().contains(&0)
    {
        return Err(Error::InvalidCommandLine);
    }
    if input.boot_flags & !ARM64_DARK_BOOT != 0 {
        return Err(Error::UnsupportedBootFlags);
    }
    let ram = Range::new(
        input.physical_base,
        input.memory_size,
        Error::InvalidMemoryRange,
    )?;
    if input.physical_base % VMAPPLE_PAGE_SIZE != 0 || input.memory_size % VMAPPLE_PAGE_SIZE != 0 {
        return Err(Error::InvalidMemoryRange);
    }
    Range::new(
        input.virtual_base,
        input.memory_size,
        Error::InvalidVirtualRange,
    )?;
    if input.virtual_base % VMAPPLE_PAGE_SIZE != 0 {
        return Err(Error::InvalidVirtualRange);
    }
    let top = input.top_of_kernel_data;
    if top <= ram.start || top >= ram.end || top % VMAPPLE_PAGE_SIZE != 0 {
        return Err(Error::InvalidOccupiedTop);
    }
    let occupied = Range {
        start: ram.start,
        end: top,
    };
    let kernel = Range::new(
        input.kernel_phys,
        input.kernel_size,
        Error::InvalidKernelRange,
    )?;
    if input.kernel_phys % VMAPPLE_PAGE_SIZE != 0 || !occupied.contains(kernel) {
        return Err(Error::InvalidKernelRange);
    }
    let args = Range::new(
        input.boot_args_phys,
        ARM64_BOOT_ARGS_SIZE as u64,
        Error::InvalidArgumentRange,
    )?;
    if input.boot_args_phys % 8 != 0 {
        return Err(Error::InvalidArgumentRange);
    }
    let dt_length = u32::try_from(input.device_tree.len()).map_err(|_| Error::InvalidDeviceTree)?;
    if input.device_tree_phys % 4 != 0 || dt_length % 4 != 0 {
        return Err(Error::InvalidDeviceTree);
    }
    let dt = Range::new(
        input.device_tree_phys,
        u64::from(dt_length),
        Error::InvalidDeviceTree,
    )?;
    flat_dt::validate(input.device_tree).map_err(|_| Error::InvalidDeviceTree)?;
    let dram = dram_range(input.device_tree)?;
    if dram.start % VMAPPLE_PAGE_SIZE != 0
        || (dram.end - dram.start) % VMAPPLE_PAGE_SIZE != 0
        || dram.end - dram.start != input.actual_memory_size
        || !dram.contains(ram)
    {
        return Err(Error::InvalidDramProperties);
    }
    if !occupied.contains(args) || !occupied.contains(dt) {
        return Err(Error::HandoffOutsideOccupiedMemory);
    }
    if args.overlaps(dt) || args.overlaps(kernel) || dt.overlaps(kernel) {
        return Err(Error::OverlappingHandoff);
    }
    // arm_vm_init's later DT/ramdisk/argument-region remap starts at end_kern.
    if args.start < kernel.end || dt.start < kernel.end {
        return Err(Error::HandoffOutsideOccupiedMemory);
    }
    let dt_virtual = input
        .virtual_base
        .checked_add(
            dt.start
                .checked_sub(ram.start)
                .ok_or(Error::InvalidDeviceTree)?,
        )
        .ok_or(Error::InvalidVirtualRange)?;
    let mut bytes = [0u8; ARM64_BOOT_ARGS_SIZE];
    bytes[0..2].copy_from_slice(&2u16.to_le_bytes());
    bytes[2..4].copy_from_slice(&2u16.to_le_bytes());
    for (offset, value) in [
        (8, input.virtual_base),
        (16, input.physical_base),
        (24, input.memory_size),
        (32, input.top_of_kernel_data),
        (40, input.video.base_address),
        (48, input.video.display),
        (56, input.video.row_bytes),
        (64, input.video.width),
        (72, input.video.height),
        (80, input.video.depth),
        (96, dt_virtual),
        (1136, input.boot_flags),
        (1144, input.actual_memory_size),
    ] {
        bytes[offset..offset + 8].copy_from_slice(&value.to_le_bytes());
    }
    bytes[88..92].copy_from_slice(&input.machine_type.to_le_bytes());
    bytes[104..108].copy_from_slice(&dt_length.to_le_bytes());
    bytes[108..108 + input.command_line.len()].copy_from_slice(input.command_line.as_bytes());
    Ok(Arm64BootArgsEncoding {
        bytes,
        physical_address: input.boot_args_phys,
        device_tree_virtual_address: dt_virtual,
    })
}

// The shared validator has already bounded the depth/counts, canonical names,
// lengths and duplicate children. This second read interprets only two public
// /chosen properties; no device bindings or arbitrary DT payloads are inferred.
fn dram_range(bytes: &[u8]) -> Result<Range, Arm64BootArgsError> {
    let mut cursor = Cursor { bytes, offset: 0 };
    let mut dram = None;
    read_dram_node(&mut cursor, 0, &mut dram)?;
    dram.ok_or(Arm64BootArgsError::MissingDramProperties)
}

struct Cursor<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> Cursor<'a> {
    fn take(&mut self, size: usize) -> Result<&'a [u8], Arm64BootArgsError> {
        let end = self
            .offset
            .checked_add(size)
            .ok_or(Arm64BootArgsError::InvalidDeviceTree)?;
        let result = self
            .bytes
            .get(self.offset..end)
            .ok_or(Arm64BootArgsError::InvalidDeviceTree)?;
        self.offset = end;
        Ok(result)
    }

    fn u32(&mut self) -> Result<u32, Arm64BootArgsError> {
        let raw = self.take(4)?;
        Ok(u32::from_le_bytes([raw[0], raw[1], raw[2], raw[3]]))
    }
}

fn read_dram_node(
    cursor: &mut Cursor<'_>,
    depth: usize,
    dram: &mut Option<Range>,
) -> Result<(), Arm64BootArgsError> {
    let properties = cursor.u32()?;
    let children = cursor.u32()?;
    let mut chosen = false;
    let mut base = None;
    let mut size = None;
    for _ in 0..properties {
        let raw_name = cursor.take(32)?;
        let name = &raw_name[..raw_name.iter().position(|&byte| byte == 0).unwrap_or(32)];
        let length =
            usize::try_from(cursor.u32()?).map_err(|_| Arm64BootArgsError::InvalidDeviceTree)?;
        let value = cursor.take(length)?;
        cursor.take((4 - length % 4) % 4)?;
        if name == b"name" {
            chosen = depth == 1 && value == b"chosen\0";
        } else if depth == 1 && name == b"dram-base" {
            base = Some(value);
        } else if depth == 1 && name == b"dram-size" {
            size = Some(value);
        }
    }
    if chosen {
        let base = base.ok_or(Arm64BootArgsError::MissingDramProperties)?;
        let size = size.ok_or(Arm64BootArgsError::MissingDramProperties)?;
        let base = u64::from_le_bytes(
            base.try_into()
                .map_err(|_| Arm64BootArgsError::InvalidDramProperties)?,
        );
        let size = u64::from_le_bytes(
            size.try_into()
                .map_err(|_| Arm64BootArgsError::InvalidDramProperties)?,
        );
        *dram = Some(Range::new(
            base,
            size,
            Arm64BootArgsError::InvalidDramProperties,
        )?);
    }
    for _ in 0..children {
        read_dram_node(cursor, depth + 1, dram)?;
    }
    Ok(())
}
