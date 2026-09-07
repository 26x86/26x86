//! Bounded, allocation-only plans for a small static x86_64 Mach-O subset.
//!
//! This is independent of the host `mach_o` inspector. Linked virtual addresses
//! are not physical addresses. A caller must copy each file range, zero the
//! remaining segment memory, establish the requested mappings/protections, and
//! separately implement the target's entry ABI. No relocation, authentication,
//! register restoration, or kernel execution is performed here.
//!
//! Format references, pinned to public XNU xnu-12377.121.6:
//! - <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/EXTERNAL_HEADERS/mach-o/loader.h>
//! - <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/mach/i386/thread_status.h>
//! - <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/mach/i386/_structs.h>

use alloc::vec::Vec;
use core::fmt;

pub const MAX_FILE_SIZE: usize = 64 * 1024 * 1024;
pub const MAX_IMAGE_SIZE: u64 = 256 * 1024 * 1024;
pub const MAX_COMMANDS: usize = 1024;
pub const MAX_SEGMENTS: usize = 64;
pub const MAX_SECTIONS: usize = 1024;
pub const PAGE_SIZE: u64 = 4096;
pub const VM_PROT_READ: u32 = 1;
pub const VM_PROT_WRITE: u32 = 2;
pub const VM_PROT_EXECUTE: u32 = 4;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MachOImagePlan {
    /// Lowest loaded linked VA, rounded down to a 4 KiB page boundary.
    pub preferred_base: u64,
    /// Page-rounded allocation span, including any holes between segments.
    /// Holes are not mapped segments and must not be treated as executable.
    pub image_size: u64,
    /// Linked VA of the Mach header in the segment containing file offset zero
    /// and the complete load-command table. Not necessarily `preferred_base`.
    pub header_vaddr: u64,
    pub entry_vaddr: u64,
    /// Command provenance only; this does not prescribe a CPU execution mode.
    pub entry_kind: EntryKind,
    /// Relative to `preferred_base`, never relative to the file or physical RAM.
    pub entry_offset: u64,
    /// Sorted by linked VA. A valid, unmapped __PAGEZERO guard is excluded.
    pub segments: Vec<SegmentPlan>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SegmentPlan {
    /// Raw fixed-width format name; do not log it as an unsanitized marker.
    pub name: [u8; 16],
    pub vmaddr: u64,
    pub memory_offset: u64,
    pub memory_size: u64,
    pub file_offset: usize,
    /// Copy this many bytes at `memory_offset`, then zero through `memory_size`.
    pub file_size: usize,
    pub init_prot: u32,
    pub max_prot: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EntryKind {
    Main,
    UnixThread64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MachOImageError {
    InputTooLarge,
    Truncated,
    UnsupportedFormat,
    UnsupportedCpu,
    UnsupportedFileType,
    UnsupportedFlags,
    UnsupportedCommand,
    UnsupportedThreadState,
    UnsupportedStack,
    UnsupportedRelocations,
    UnsupportedSection,
    LimitExceeded,
    InvalidHeader,
    InvalidCommand,
    InvalidSegment,
    InvalidSection,
    InvalidMetadata,
    Overflow,
    SegmentOverlap,
    SectionOverlap,
    MissingSegments,
    MissingEntry,
    DuplicateEntry,
    EntryOutsideExecutable,
}

impl fmt::Display for MachOImageError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let token = match self {
            Self::InputTooLarge => "MACHO_INPUT_TOO_LARGE",
            Self::Truncated => "MACHO_TRUNCATED",
            Self::UnsupportedFormat => "MACHO_UNSUPPORTED_FORMAT",
            Self::UnsupportedCpu => "MACHO_UNSUPPORTED_CPU",
            Self::UnsupportedFileType => "MACHO_UNSUPPORTED_FILETYPE",
            Self::UnsupportedFlags => "MACHO_UNSUPPORTED_FLAGS",
            Self::UnsupportedCommand => "MACHO_UNSUPPORTED_COMMAND",
            Self::UnsupportedThreadState => "MACHO_UNSUPPORTED_THREAD_STATE",
            Self::UnsupportedStack => "MACHO_UNSUPPORTED_STACK",
            Self::UnsupportedRelocations => "MACHO_UNSUPPORTED_RELOCATIONS",
            Self::UnsupportedSection => "MACHO_UNSUPPORTED_SECTION",
            Self::LimitExceeded => "MACHO_LIMIT_EXCEEDED",
            Self::InvalidHeader => "MACHO_INVALID_HEADER",
            Self::InvalidCommand => "MACHO_INVALID_COMMAND",
            Self::InvalidSegment => "MACHO_INVALID_SEGMENT",
            Self::InvalidSection => "MACHO_INVALID_SECTION",
            Self::InvalidMetadata => "MACHO_INVALID_METADATA",
            Self::Overflow => "MACHO_OVERFLOW",
            Self::SegmentOverlap => "MACHO_SEGMENT_OVERLAP",
            Self::SectionOverlap => "MACHO_SECTION_OVERLAP",
            Self::MissingSegments => "MACHO_MISSING_SEGMENTS",
            Self::MissingEntry => "MACHO_MISSING_ENTRY",
            Self::DuplicateEntry => "MACHO_DUPLICATE_ENTRY",
            Self::EntryOutsideExecutable => "MACHO_ENTRY_OUTSIDE_EXECUTABLE",
        };
        f.write_str(token)
    }
}

impl core::error::Error for MachOImageError {}

type Result<T> = core::result::Result<T, MachOImageError>;

enum Entry {
    FileOffset(u64),
    VirtualAddress(u64),
}

/// Parse thin little-endian generic x86_64 MH_EXECUTE without dyld or fixups.
///
/// Exactly one LC_MAIN (with no requested stack) or LC_UNIXTHREAD (one
/// x86_THREAD_STATE64 state) is accepted. Only RIP is extracted from thread
/// state; this plan is not a promise that the remaining entry ABI is satisfied.
/// Benign metadata ranges are bounded, not interpreted or authenticated.
pub fn parse_macho_image(bytes: &[u8]) -> Result<MachOImagePlan> {
    use MachOImageError as E;
    if bytes.len() > MAX_FILE_SIZE {
        return Err(E::InputTooLarge);
    }
    if read32(bytes, 0)? != 0xfeed_facf {
        return Err(E::UnsupportedFormat);
    }
    slice(bytes, 0, 32)?;
    if read32(bytes, 4)? != 0x0100_0007 || read32(bytes, 8)? != 3 {
        return Err(E::UnsupportedCpu);
    }
    if read32(bytes, 12)? != 2 {
        return Err(E::UnsupportedFileType);
    }
    // Only informational static-image flags are currently supported:
    // MH_NOUNDEFS and MH_SUBSECTIONS_VIA_SYMBOLS. In particular, no PIE/dyld.
    if read32(bytes, 24)? & !(0x1 | 0x2000) != 0 {
        return Err(E::UnsupportedFlags);
    }
    if read32(bytes, 28)? != 0 {
        return Err(E::InvalidHeader);
    }
    let count = read32(bytes, 16)? as usize;
    let command_size = read32(bytes, 20)? as usize;
    if count > MAX_COMMANDS {
        return Err(E::LimitExceeded);
    }
    if command_size % 8 != 0 || count > command_size / 8 {
        return Err(E::InvalidHeader);
    }
    let commands = slice(bytes, 32, command_size)?;
    let mut offset = 0;
    let mut segments = Vec::new();
    let mut guard = None;
    let mut segment_count = 0;
    let mut section_count = 0;
    let mut entry = None;
    for _ in 0..count {
        let kind = read32(commands, offset)?;
        let size = read32(commands, offset + 4)? as usize;
        if size < 8 || size % 8 != 0 {
            return Err(E::InvalidCommand);
        }
        let command = slice(commands, offset, size)?;
        match kind {
            0x19 => {
                segment_count += 1;
                if segment_count > MAX_SEGMENTS {
                    return Err(E::LimitExceeded);
                }
                let segment = parse_segment(bytes, command, &mut section_count)?;
                if &command[8..24] == b"__PAGEZERO\0\0\0\0\0\0" {
                    if guard.is_some()
                        || segment.vmaddr != 0
                        || segment.file_offset != 0
                        || segment.file_size != 0
                        || segment.init_prot != 0
                        || segment.max_prot != 0
                        || read32(command, 64)? != 0
                    {
                        return Err(E::InvalidSegment);
                    }
                    guard = Some(segment.memory_size);
                } else {
                    segments.push(segment);
                }
            }
            0x8000_0028 => {
                exact_size(command, 24)?;
                if read64(command, 16)? != 0 {
                    return Err(E::UnsupportedStack);
                }
                set_entry(&mut entry, Entry::FileOffset(read64(command, 8)?))?;
            }
            0x5 => {
                // 8-byte command, 8-byte flavor/count, 21 64-bit registers.
                if read32(command, 8)? != 4 || read32(command, 12)? != 42 {
                    return Err(E::UnsupportedThreadState);
                }
                exact_size(command, 184)?;
                set_entry(&mut entry, Entry::VirtualAddress(read64(command, 144)?))?;
            }
            _ => validate_metadata(bytes, command, kind)?,
        }
        offset = offset.checked_add(size).ok_or(E::Overflow)?;
    }
    if offset != commands.len() {
        return Err(E::InvalidCommand);
    }
    if segments.is_empty() {
        return Err(E::MissingSegments);
    }
    segments.sort_unstable_by_key(|segment| segment.vmaddr);
    let mut previous_end = guard.unwrap_or(0);
    for segment in &segments {
        if segment.vmaddr < previous_end {
            return Err(E::SegmentOverlap);
        }
        previous_end = checked_end(segment.vmaddr, segment.memory_size)?;
    }
    // A byte must not have two distinct mappings in this minimal plan.
    for (index, segment) in segments.iter().enumerate() {
        for other in &segments[..index] {
            if overlap(
                segment.file_offset as u64,
                segment.file_size as u64,
                other.file_offset as u64,
                other.file_size as u64,
            ) {
                return Err(E::SegmentOverlap);
            }
        }
    }
    let header_vaddr = segments
        .iter()
        .find(|segment| segment.file_offset == 0 && segment.file_size >= 32 + command_size)
        .map(|segment| segment.vmaddr)
        .ok_or(E::InvalidHeader)?;
    let preferred_base = segments[0].vmaddr & !(PAGE_SIZE - 1);
    let image_end = checked_end(previous_end, PAGE_SIZE - 1)? & !(PAGE_SIZE - 1);
    let image_size = image_end.checked_sub(preferred_base).ok_or(E::Overflow)?;
    if image_size > MAX_IMAGE_SIZE {
        return Err(E::LimitExceeded);
    }
    let entry = entry.ok_or(E::MissingEntry)?;
    let entry_kind = match entry {
        Entry::FileOffset(_) => EntryKind::Main,
        Entry::VirtualAddress(_) => EntryKind::UnixThread64,
    };
    let mut entry_vaddr = None;
    for segment in &mut segments {
        segment.memory_offset = segment.vmaddr - preferred_base;
        if segment.init_prot & VM_PROT_EXECUTE == 0 {
            continue;
        }
        let relative = match entry {
            Entry::FileOffset(value) => value.checked_sub(segment.file_offset as u64),
            Entry::VirtualAddress(value) => value.checked_sub(segment.vmaddr),
        };
        if let Some(relative) = relative.filter(|&value| value < segment.file_size as u64) {
            entry_vaddr = Some(checked_end(segment.vmaddr, relative)?);
        }
    }
    let entry_vaddr = entry_vaddr.ok_or(E::EntryOutsideExecutable)?;
    Ok(MachOImagePlan {
        preferred_base,
        image_size,
        header_vaddr,
        entry_vaddr,
        entry_kind,
        entry_offset: entry_vaddr - preferred_base,
        segments,
    })
}

fn parse_segment(bytes: &[u8], command: &[u8], total_sections: &mut usize) -> Result<SegmentPlan> {
    use MachOImageError as E;
    slice(command, 0, 72)?;
    let count = read32(command, 64)? as usize;
    *total_sections = total_sections.checked_add(count).ok_or(E::Overflow)?;
    if *total_sections > MAX_SECTIONS {
        return Err(E::LimitExceeded);
    }
    exact_size(command, 72 + count * 80)?;
    let vmaddr = read64(command, 24)?;
    let memory_size = read64(command, 32)?;
    let file_offset = read64(command, 40)?;
    let file_size = read64(command, 48)?;
    let max_prot = read32(command, 56)?;
    let init_prot = read32(command, 60)?;
    if memory_size == 0
        || file_size > memory_size
        || max_prot & !7 != 0
        || init_prot & !max_prot != 0
    {
        return Err(E::InvalidSegment);
    }
    // SG_NORELOC is informational; SG_HIGHVM changes the copy layout and
    // SG_PROTECTED/SG_READ_ONLY require mechanisms not implemented here.
    if read32(command, 68)? & !4 != 0 {
        return Err(E::UnsupportedFlags);
    }
    let memory_end = checked_end(vmaddr, memory_size)?;
    file_range(bytes, file_offset, file_size)?;
    let file_memory_end = checked_end(vmaddr, file_size)?;
    let mut ranges = Vec::with_capacity(count);
    for section in command[72..].chunks_exact(80) {
        if section[16..32] != command[8..24] {
            return Err(E::InvalidSection);
        }
        let addr = read64(section, 32)?;
        let size = read64(section, 40)?;
        let end = checked_end(addr, size)?;
        let align = read32(section, 52)?;
        let flags = read32(section, 64)?;
        if addr < vmaddr || end > memory_end || align >= 64 || addr & ((1u64 << align) - 1) != 0 {
            return Err(E::InvalidSection);
        }
        if read32(section, 60)? != 0 || flags & 0x300 != 0 {
            return Err(E::UnsupportedRelocations);
        }
        // Only static data/instructions and zero-fill sections. In particular,
        // no dyld pointers, initializers, TLS, or indirect symbol stubs.
        match flags & 0xff {
            1 | 0xc => {
                if addr < file_memory_end {
                    return Err(E::InvalidSection);
                }
            }
            0 | 2 | 3 | 4 | 0xe => {
                let section_offset = read32(section, 48)? as u64;
                if end > file_memory_end
                    || section_offset != checked_end(file_offset, addr - vmaddr)?
                {
                    return Err(E::InvalidSection);
                }
                file_range(bytes, section_offset, size)?;
            }
            _ => return Err(E::UnsupportedSection),
        }
        if size != 0 {
            ranges.push((addr, end));
        }
    }
    ranges.sort_unstable_by_key(|range| range.0);
    for pair in ranges.windows(2) {
        if pair[1].0 < pair[0].1 {
            return Err(E::SectionOverlap);
        }
    }
    Ok(SegmentPlan {
        name: command[8..24].try_into().unwrap(),
        vmaddr,
        memory_offset: 0,
        memory_size,
        file_offset: file_offset as usize,
        file_size: file_size as usize,
        init_prot,
        max_prot,
    })
}

fn validate_metadata(bytes: &[u8], command: &[u8], kind: u32) -> Result<()> {
    use MachOImageError as E;
    match kind {
        0x2 => {
            exact_size(command, 24)?;
            file_range(
                bytes,
                read32(command, 8)? as u64,
                read32(command, 12)? as u64 * 16,
            )?;
            file_range(
                bytes,
                read32(command, 16)? as u64,
                read32(command, 20)? as u64,
            )?;
        }
        0x1b => exact_size(command, 24)?,        // UUID
        0x24 | 0x2a => exact_size(command, 16)?, // min macOS / source version
        0x32 => {
            slice(command, 0, 24)?;
            let count = read32(command, 20)? as u64;
            if 24 + count * 8 != command.len() as u64 {
                return Err(E::InvalidCommand);
            }
        }
        0x1d | 0x26 | 0x29 => {
            exact_size(command, 16)?;
            let size = read32(command, 12)? as u64;
            if kind == 0x29 && size % 8 != 0 {
                return Err(E::InvalidMetadata);
            }
            file_range(bytes, read32(command, 8)? as u64, size)?;
        }
        _ => return Err(E::UnsupportedCommand),
    }
    Ok(())
}

fn set_entry(entry: &mut Option<Entry>, value: Entry) -> Result<()> {
    if entry.replace(value).is_some() {
        return Err(MachOImageError::DuplicateEntry);
    }
    Ok(())
}

fn checked_end(start: u64, size: u64) -> Result<u64> {
    start.checked_add(size).ok_or(MachOImageError::Overflow)
}

fn file_range(bytes: &[u8], start: u64, size: u64) -> Result<()> {
    if checked_end(start, size)? > bytes.len() as u64 {
        return Err(MachOImageError::Truncated);
    }
    Ok(())
}

fn overlap(start: u64, size: u64, other_start: u64, other_size: u64) -> bool {
    // Callers have already checked both range ends for overflow.
    size != 0 && other_size != 0 && start < other_start + other_size && other_start < start + size
}

fn exact_size(command: &[u8], expected: usize) -> Result<()> {
    if command.len() != expected {
        return Err(MachOImageError::InvalidCommand);
    }
    Ok(())
}

fn slice(bytes: &[u8], offset: usize, size: usize) -> Result<&[u8]> {
    let end = offset.checked_add(size).ok_or(MachOImageError::Overflow)?;
    bytes.get(offset..end).ok_or(MachOImageError::Truncated)
}

fn read32(bytes: &[u8], offset: usize) -> Result<u32> {
    let value: [u8; 4] = slice(bytes, offset, 4)?.try_into().unwrap();
    Ok(u32::from_le_bytes(value))
}

fn read64(bytes: &[u8], offset: usize) -> Result<u64> {
    let value: [u8; 8] = slice(bytes, offset, 8)?.try_into().unwrap();
    Ok(u64::from_le_bytes(value))
}
