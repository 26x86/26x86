//! Read-only x86_64 fileset metadata inspection, never an executable load plan.
//!
//! Public format/consumer provenance and scope:
//! `nextcore/artifacts/kc-metadata-contract-20260908.md`.
//! No pointer chains, relocation targets, symbols or instructions are decoded.

use alloc::{vec, vec::Vec};
use core::fmt;

pub const MAX_INPUT_SIZE: usize = 128 * 1024 * 1024;
const MAX_COMMANDS: usize = 16_384;
const MAX_COMMAND_BYTES: usize = 1024 * 1024;
const MAX_SEGMENTS: usize = 4096;
const MAX_SECTIONS: usize = 32_768;
const MAX_MEMBERS: usize = 512;
const MAX_IDENTIFIER: usize = 1024;
const MAX_FIXUP_BYTES: u64 = 16 * 1024 * 1024;
const MAX_PAGE_START_VISITS: usize = 1_000_000;

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct FileRange {
    pub offset: u64,
    pub size: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct SectionMetadata {
    pub address: u64,
    pub size: u64,
    pub file_offset: u64,
    pub flags: u32,
    pub relocations: FileRange,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct SegmentMetadata {
    pub name: [u8; 16],
    pub address: u64,
    pub memory_size: u64,
    pub file: FileRange,
    pub maximum_protection: u32,
    pub initial_protection: u32,
    pub flags: u32,
    pub sections: Vec<SectionMetadata>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub enum EntryMetadata {
    /// Command provenance, not evidence of the CPU mode or calling convention.
    UnixThread64 {
        instruction_pointer: u64,
    },
    Main {
        text_offset: u64,
        stack_size: u64,
    },
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct RelocationMetadata {
    pub local: FileRange,
    pub external: FileRange,
    pub local_count: u32,
    pub external_count: u32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct FixupSegmentMetadata {
    pub segment_index: usize,
    pub pointer_format: u16,
    pub page_size: u16,
    pub page_count: u16,
    pub pages_with_fixups: u32,
    pub multiple_start_pages: u32,
    /// Unsigned on-disk displacement; this is not a physical address.
    pub segment_offset: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct ChainedFixupMetadata {
    pub file: FileRange,
    pub imports_count: u32,
    pub imports_format: u32,
    pub symbols_format: u32,
    pub segments: Vec<FixupSegmentMetadata>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct ImageMetadata {
    pub header_file_offset: u64,
    pub header_address: u64,
    pub file_type: u32,
    pub flags: u32,
    pub command_count: u32,
    pub command_bytes: u32,
    pub segments: Vec<SegmentMetadata>,
    /// Belongs to this header only. Member entries are never selected for boot.
    pub entry: Option<EntryMetadata>,
    pub relocations: Option<RelocationMetadata>,
    pub chained_fixups: Option<ChainedFixupMetadata>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct FilesetMember {
    /// Opaque bounded bytes, excluding the terminating NUL.
    pub identifier: Vec<u8>,
    pub image: ImageMetadata,
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub enum PreparationRequirement {
    CollectionPlacement,
    KernelEntryAbi,
    PlatformHandoffProviders,
    ClassicRelocations,
    ChainedRebasing,
    ChainedImports,
    CompressedFixupSymbols,
    UnsupportedPointerFormat(u16),
}

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct KcMetadataInspection {
    pub collection: ImageMetadata,
    pub members: Vec<FilesetMember>,
    pub requirements: Vec<PreparationRequirement>,
}

impl KcMetadataInspection {
    /// Metadata alone never authorizes allocation, rebasing, or entry.
    pub const fn preparation_ready(&self) -> bool {
        false
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum KcMetadataError {
    InputTooLarge,
    Truncated,
    Overflow,
    LimitExceeded,
    UnsupportedFormat,
    UnsupportedCpu,
    UnsupportedFileType,
    UnsupportedCommand,
    UnsupportedSegmentFlags,
    UnsupportedThreadState,
    UnsupportedCollectionEntry,
    UnsupportedFixupVersion,
    InvalidHeader,
    InvalidCommand,
    InvalidSegment,
    InvalidSection,
    InvalidIdentifier,
    DuplicateMember,
    OverlappingRange,
    InvalidMemberMapping,
    InvalidLinkedit,
    InvalidFixups,
    MissingEntry,
    DuplicateEntry,
    InvalidEntry,
}

impl fmt::Display for KcMetadataError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "KC_METADATA_{self:?}")
    }
}

impl core::error::Error for KcMetadataError {}
type Result<T> = core::result::Result<T, KcMetadataError>;
use KcMetadataError as E;

#[derive(Default)]
struct Budget {
    commands: usize,
    segments: usize,
    sections: usize,
}

struct MemberReference {
    identifier: Vec<u8>,
    offset: u64,
    address: u64,
}

struct ParsedImage {
    image: ImageMetadata,
    members: Vec<MemberReference>,
}

/// Inspect metadata of a thin generic x86_64 MH_FILESET and one member level.
/// The supplied bytes are never changed. No member payload is extracted.
pub fn inspect_kernel_collection(bytes: &[u8]) -> Result<KcMetadataInspection> {
    if bytes.len() > MAX_INPUT_SIZE {
        return Err(E::InputTooLarge);
    }
    let mut budget = Budget::default();
    let outer = parse_image(bytes, 0, true, &mut budget)?;
    validate_collection_entry(&outer.image)?;
    if outer.members.is_empty() {
        return Err(E::InvalidHeader);
    }
    let mut members = Vec::with_capacity(outer.members.len());
    for reference in &outer.members {
        let child = parse_image(bytes, reference.offset, false, &mut budget)?.image;
        if child.header_address != reference.address {
            return Err(E::InvalidMemberMapping);
        }
        let header = FileRange {
            offset: reference.offset,
            size: 32 + u64::from(child.command_bytes),
        };
        if !is_collection_view(&outer.image.segments, &header, reference.address) {
            return Err(E::InvalidMemberMapping);
        }
        for segment in &child.segments {
            if segment.memory_size != 0
                && !outer.image.segments.iter().any(|s| {
                    contains(
                        &FileRange {
                            offset: s.address,
                            size: s.memory_size,
                        },
                        &FileRange {
                            offset: segment.address,
                            size: segment.memory_size,
                        },
                    )
                })
            {
                return Err(E::InvalidMemberMapping);
            }
            if segment.file.size != 0
                && !is_collection_view(&outer.image.segments, &segment.file, segment.address)
            {
                return Err(E::InvalidMemberMapping);
            }
        }
        members.push(FilesetMember {
            identifier: reference.identifier.clone(),
            image: child,
        });
    }
    let mut requirements = vec![
        PreparationRequirement::CollectionPlacement,
        PreparationRequirement::KernelEntryAbi,
        PreparationRequirement::PlatformHandoffProviders,
    ];
    for image in core::iter::once(&outer.image).chain(members.iter().map(|m| &m.image)) {
        if image
            .relocations
            .as_ref()
            .is_some_and(|r| r.local_count != 0 || r.external_count != 0)
            || image
                .segments
                .iter()
                .any(|s| s.sections.iter().any(|s| s.relocations.size != 0))
        {
            require(
                &mut requirements,
                PreparationRequirement::ClassicRelocations,
            );
        }
        if let Some(fixups) = &image.chained_fixups {
            require(&mut requirements, PreparationRequirement::ChainedRebasing);
            if fixups.imports_count != 0 {
                require(&mut requirements, PreparationRequirement::ChainedImports);
            }
            if fixups.symbols_format != 0 {
                require(
                    &mut requirements,
                    PreparationRequirement::CompressedFixupSymbols,
                );
            }
            for segment in &fixups.segments {
                if segment.pointer_format != 11 {
                    require(
                        &mut requirements,
                        PreparationRequirement::UnsupportedPointerFormat(segment.pointer_format),
                    );
                }
            }
        }
    }
    Ok(KcMetadataInspection {
        collection: outer.image,
        members,
        requirements,
    })
}

fn require(requirements: &mut Vec<PreparationRequirement>, value: PreparationRequirement) {
    if !requirements.contains(&value) {
        requirements.push(value);
    }
}

fn parse_image(bytes: &[u8], base: u64, outer: bool, budget: &mut Budget) -> Result<ParsedImage> {
    let h = range(bytes, base, 32)?;
    if u32_at(h, 0)? != 0xfeed_facf {
        return Err(E::UnsupportedFormat);
    }
    if u32_at(h, 4)? != 0x0100_0007 || u32_at(h, 8)? != 3 {
        return Err(E::UnsupportedCpu);
    }
    let file_type = u32_at(h, 12)?;
    if (outer && file_type != 12) || (!outer && file_type != 2 && file_type != 11) {
        return Err(E::UnsupportedFileType);
    }
    let count = u32_at(h, 16)?;
    let command_bytes = u32_at(h, 20)?;
    if u32_at(h, 28)? != 0 || command_bytes % 8 != 0 || count > command_bytes / 8 {
        return Err(E::InvalidHeader);
    }
    add_budget(&mut budget.commands, count as usize, MAX_COMMANDS)?;
    if command_bytes as usize > MAX_COMMAND_BYTES {
        return Err(E::LimitExceeded);
    }
    let commands = range(bytes, end(base, 32)?, u64::from(command_bytes))?;
    let mut segments = Vec::new();
    let mut members: Vec<MemberReference> = Vec::new();
    let mut entry = None;
    let mut symtab = None;
    let mut dysymtab = None;
    let mut fixup_range = None;
    let mut linkedit_ranges = Vec::new();
    let mut offset = 0;
    for _ in 0..count {
        let kind = u32_at(commands, offset)?;
        let size = u32_at(commands, offset + 4)? as usize;
        if size < 8 || !size.is_multiple_of(8) {
            return Err(E::InvalidCommand);
        }
        let cmd = slice(commands, offset, size)?;
        match kind {
            0x19 => {
                add_budget(&mut budget.segments, 1, MAX_SEGMENTS)?;
                segments.push(parse_segment(bytes, cmd, budget)?);
            }
            0x8000_0035 if outer => {
                if size < 32 {
                    return Err(E::InvalidCommand);
                }
                if members.len() == MAX_MEMBERS {
                    return Err(E::LimitExceeded);
                }
                let string_offset = u32_at(cmd, 24)? as usize;
                if string_offset < 32 || string_offset >= size || u32_at(cmd, 28)? != 0 {
                    return Err(E::InvalidIdentifier);
                }
                let tail = &cmd[string_offset..];
                let length = tail
                    .iter()
                    .position(|&b| b == 0)
                    .ok_or(E::InvalidIdentifier)?;
                if length == 0 || length > MAX_IDENTIFIER {
                    return Err(E::InvalidIdentifier);
                }
                let identifier = tail[..length].to_vec();
                let member_offset = u64_at(cmd, 16)?;
                let address = u64_at(cmd, 8)?;
                range(bytes, member_offset, 32)?;
                if member_offset == 0
                    || members.iter().any(|m| {
                        m.offset == member_offset
                            || m.address == address
                            || m.identifier == identifier
                    })
                {
                    return Err(E::DuplicateMember);
                }
                members.push(MemberReference {
                    identifier,
                    offset: member_offset,
                    address,
                });
            }
            5 => {
                exact(cmd, 184)?;
                if u32_at(cmd, 8)? != 4 || u32_at(cmd, 12)? != 42 {
                    return Err(E::UnsupportedThreadState);
                }
                set_entry(
                    &mut entry,
                    EntryMetadata::UnixThread64 {
                        instruction_pointer: u64_at(cmd, 144)?,
                    },
                )?;
            }
            0x8000_0028 => {
                exact(cmd, 24)?;
                set_entry(
                    &mut entry,
                    EntryMetadata::Main {
                        text_offset: u64_at(cmd, 8)?,
                        stack_size: u64_at(cmd, 16)?,
                    },
                )?;
            }
            2 => {
                exact(cmd, 24)?;
                if symtab.is_some() {
                    return Err(E::InvalidCommand);
                }
                let symbols = file_range(
                    bytes,
                    u64::from(u32_at(cmd, 8)?),
                    u64::from(u32_at(cmd, 12)?),
                    16,
                )?;
                let strings = file_range(
                    bytes,
                    u64::from(u32_at(cmd, 16)?),
                    u64::from(u32_at(cmd, 20)?),
                    1,
                )?;
                linkedit_ranges.extend([symbols, strings]);
                symtab = Some(u32_at(cmd, 12)?);
            }
            0xb => {
                exact(cmd, 80)?;
                if dysymtab.is_some() {
                    return Err(E::InvalidCommand);
                }
                dysymtab = Some(cmd);
                for (at, width) in [(32, 8), (40, 56), (48, 4), (56, 4), (64, 8), (72, 8)] {
                    linkedit_ranges.push(file_range(
                        bytes,
                        u64::from(u32_at(cmd, at)?),
                        u64::from(u32_at(cmd, at + 4)?),
                        width,
                    )?);
                }
            }
            0x8000_0034 => {
                exact(cmd, 16)?;
                if fixup_range.is_some() {
                    return Err(E::InvalidCommand);
                }
                let r = file_range(
                    bytes,
                    u64::from(u32_at(cmd, 8)?),
                    u64::from(u32_at(cmd, 12)?),
                    1,
                )?;
                linkedit_ranges.push(r.clone());
                fixup_range = Some(r);
            }
            0x1b => exact(cmd, 24)?,
            0x24 | 0x2a => exact(cmd, 16)?,
            0x32 => {
                slice(cmd, 0, 24)?;
                if 24 + u64::from(u32_at(cmd, 20)?) * 8 != size as u64 {
                    return Err(E::InvalidCommand);
                }
            }
            0x1d | 0x26 | 0x29 => {
                exact(cmd, 16)?;
                let n = u32_at(cmd, 12)?;
                if kind == 0x29 && n % 8 != 0 {
                    return Err(E::InvalidCommand);
                }
                linkedit_ranges.push(file_range(
                    bytes,
                    u64::from(u32_at(cmd, 8)?),
                    u64::from(n),
                    1,
                )?);
            }
            _ => return Err(E::UnsupportedCommand),
        }
        offset = offset.checked_add(size).ok_or(E::Overflow)?;
    }
    if offset != commands.len() || segments.is_empty() {
        return Err(E::InvalidHeader);
    }
    validate_nonoverlap(&segments)?;
    let header_size = 32 + u64::from(command_bytes);
    let header_address = segments
        .iter()
        .find_map(|s| {
            if contains(
                &s.file,
                &FileRange {
                    offset: base,
                    size: header_size,
                },
            ) {
                s.address.checked_add(base - s.file.offset)
            } else {
                None
            }
        })
        .ok_or(E::InvalidHeader)?;
    for r in &linkedit_ranges {
        if r.size != 0
            && !segments
                .iter()
                .any(|s| s.name == *b"__LINKEDIT\0\0\0\0\0\0" && contains(&s.file, r))
        {
            return Err(E::InvalidLinkedit);
        }
    }
    for section in segments.iter().flat_map(|s| &s.sections) {
        if section.relocations.size != 0
            && !segments.iter().any(|s| {
                s.name == *b"__LINKEDIT\0\0\0\0\0\0" && contains(&s.file, &section.relocations)
            })
        {
            return Err(E::InvalidLinkedit);
        }
    }
    let relocations = if let Some(cmd) = dysymtab {
        let symbols = symtab.ok_or(E::InvalidLinkedit)?;
        for at in [8, 16, 24] {
            if end(u64::from(u32_at(cmd, at)?), u64::from(u32_at(cmd, at + 4)?))?
                > u64::from(symbols)
            {
                return Err(E::InvalidLinkedit);
            }
        }
        Some(RelocationMetadata {
            local: file_range(
                bytes,
                u64::from(u32_at(cmd, 72)?),
                u64::from(u32_at(cmd, 76)?),
                8,
            )?,
            external: file_range(
                bytes,
                u64::from(u32_at(cmd, 64)?),
                u64::from(u32_at(cmd, 68)?),
                8,
            )?,
            local_count: u32_at(cmd, 76)?,
            external_count: u32_at(cmd, 68)?,
        })
    } else {
        None
    };
    let chained_fixups = fixup_range
        .map(|r| parse_fixups(bytes, r, &segments, header_address))
        .transpose()?;
    Ok(ParsedImage {
        image: ImageMetadata {
            header_file_offset: base,
            header_address,
            file_type,
            flags: u32_at(h, 24)?,
            command_count: count,
            command_bytes,
            segments,
            entry,
            relocations,
            chained_fixups,
        },
        members,
    })
}

fn parse_segment(bytes: &[u8], cmd: &[u8], budget: &mut Budget) -> Result<SegmentMetadata> {
    slice(cmd, 0, 72)?;
    let count = u32_at(cmd, 64)? as usize;
    add_budget(&mut budget.sections, count, MAX_SECTIONS)?;
    if 72 + count as u64 * 80 != cmd.len() as u64 {
        return Err(E::InvalidCommand);
    }
    let address = u64_at(cmd, 24)?;
    let memory_size = u64_at(cmd, 32)?;
    let file = file_range(bytes, u64_at(cmd, 40)?, u64_at(cmd, 48)?, 1)?;
    let maximum_protection = u32_at(cmd, 56)?;
    let initial_protection = u32_at(cmd, 60)?;
    let flags = u32_at(cmd, 68)?;
    end(address, memory_size)?;
    if file.size > memory_size
        || maximum_protection & !7 != 0
        || initial_protection & !maximum_protection != 0
    {
        return Err(E::InvalidSegment);
    }
    // Only SG_NORELOC is layout-neutral in this initial inspection profile.
    if flags & !4 != 0 {
        return Err(E::UnsupportedSegmentFlags);
    }
    let mut sections = Vec::with_capacity(count);
    for s in cmd[72..].chunks_exact(80) {
        let sa = u64_at(s, 32)?;
        let size = u64_at(s, 40)?;
        let section_offset = u64::from(u32_at(s, 48)?);
        let align = u32_at(s, 52)?;
        let section_flags = u32_at(s, 64)?;
        if s[16..32] != cmd[8..24]
            || sa < address
            || end(sa, size)? > end(address, memory_size)?
            || align >= 64
            || sa & ((1u64 << align) - 1) != 0
        {
            return Err(E::InvalidSection);
        }
        if !matches!(section_flags & 0xff, 1 | 0xc | 0x12) && size != 0 {
            let section_file = FileRange {
                offset: section_offset,
                size,
            };
            if !contains(&file, &section_file) || section_offset - file.offset != sa - address {
                return Err(E::InvalidSection);
            }
        }
        let relocations = file_range(
            bytes,
            u64::from(u32_at(s, 56)?),
            u64::from(u32_at(s, 60)?),
            8,
        )?;
        sections.push(SectionMetadata {
            address: sa,
            size,
            file_offset: section_offset,
            flags: section_flags,
            relocations,
        });
    }
    let mut ordered: Vec<_> = sections.iter().filter(|s| s.size != 0).collect();
    ordered.sort_unstable_by_key(|s| s.address);
    for pair in ordered.windows(2) {
        if end(pair[0].address, pair[0].size)? > pair[1].address {
            return Err(E::OverlappingRange);
        }
    }
    Ok(SegmentMetadata {
        name: cmd[8..24].try_into().unwrap(),
        address,
        memory_size,
        file,
        maximum_protection,
        initial_protection,
        flags,
        sections,
    })
}

fn parse_fixups(
    bytes: &[u8],
    file: FileRange,
    segments: &[SegmentMetadata],
    header_address: u64,
) -> Result<ChainedFixupMetadata> {
    if file.size > MAX_FIXUP_BYTES {
        return Err(E::LimitExceeded);
    }
    let data = range(bytes, file.offset, file.size)?;
    slice(data, 0, 28)?;
    if u32_at(data, 0)? != 0 {
        return Err(E::UnsupportedFixupVersion);
    }
    let starts = u32_at(data, 4)? as usize;
    let imports = u32_at(data, 8)? as usize;
    let symbols = u32_at(data, 12)? as usize;
    let imports_count = u32_at(data, 16)?;
    let imports_format = u32_at(data, 20)?;
    let symbols_format = u32_at(data, 24)?;
    if starts < 28 || imports < 28 || symbols < 28 || symbols > data.len() || symbols_format > 1 {
        return Err(E::InvalidFixups);
    }
    let import_width = match imports_format {
        1 => 4u64,
        2 => 8,
        3 => 16,
        _ => return Err(E::InvalidFixups),
    };
    let import_range = file_range(data, imports as u64, u64::from(imports_count), import_width)?;
    let symbol_range = FileRange {
        offset: symbols as u64,
        size: (data.len() - symbols) as u64,
    };
    if overlaps(&import_range, &symbol_range) {
        return Err(E::InvalidFixups);
    }
    let count = u32_at(data, starts)? as usize;
    if count != segments.len() {
        return Err(E::InvalidFixups);
    }
    let table_size = 4 + count * 4;
    slice(data, starts, table_size)?;
    let table_range = FileRange {
        offset: starts as u64,
        size: table_size as u64,
    };
    if overlaps(&table_range, &import_range) || overlaps(&table_range, &symbol_range) {
        return Err(E::InvalidFixups);
    }
    let mut info_ranges = Vec::new();
    let mut result = Vec::new();
    let mut start_visits = 0;
    for (index, segment) in segments.iter().enumerate() {
        let relative = u32_at(data, starts + 4 + index * 4)? as usize;
        if relative == 0 {
            continue;
        }
        if relative < table_size {
            return Err(E::InvalidFixups);
        }
        let at = starts.checked_add(relative).ok_or(E::Overflow)?;
        let size = u32_at(data, at)? as usize;
        if size < 22 || !(size - 22).is_multiple_of(2) {
            return Err(E::InvalidFixups);
        }
        let info = slice(data, at, size)?;
        let ir = FileRange {
            offset: at as u64,
            size: size as u64,
        };
        if info_ranges.iter().any(|r| overlaps(r, &ir))
            || overlaps(&ir, &import_range)
            || overlaps(&ir, &symbol_range)
        {
            return Err(E::InvalidFixups);
        }
        info_ranges.push(ir);
        let page_size = u16_at(info, 4)?;
        let pointer_format = u16_at(info, 6)?;
        let segment_offset = u64_at(info, 8)?;
        let page_count = u16_at(info, 20)?;
        // This compares an on-disk modulo displacement. It does not calculate
        // a physical address or make an overflowed placement usable.
        if segment_offset != segment.address.wrapping_sub(header_address)
            || !matches!(page_size, 4096 | 16384)
            || u32_at(info, 16)? != 0
            || u64::from(page_count) > segment.memory_size.div_ceil(u64::from(page_size))
        {
            return Err(E::InvalidFixups);
        }
        let available = (size - 22) / 2;
        if usize::from(page_count) > available {
            return Err(E::InvalidFixups);
        }
        let mut pages_with_fixups = 0;
        let mut multiple_start_pages = 0;
        for page in 0..usize::from(page_count) {
            add_budget(&mut start_visits, 1, MAX_PAGE_START_VISITS)?;
            let first = u16_at(info, 22 + page * 2)?;
            if first == 0xffff {
                continue;
            }
            pages_with_fixups += 1;
            let page_offset = page as u64 * u64::from(page_size);
            let backed_bytes = segment
                .file
                .size
                .saturating_sub(page_offset)
                .min(segment.memory_size.saturating_sub(page_offset));
            if first & 0x8000 == 0 {
                validate_page_start(first, page_size, backed_bytes, pointer_format)?;
            } else {
                multiple_start_pages += 1;
                let mut cursor = usize::from(first & 0x7fff);
                if cursor < usize::from(page_count) {
                    return Err(E::InvalidFixups);
                }
                loop {
                    add_budget(&mut start_visits, 1, MAX_PAGE_START_VISITS)?;
                    if cursor >= available {
                        return Err(E::InvalidFixups);
                    }
                    let value = u16_at(info, 22 + cursor * 2)?;
                    validate_page_start(value & 0x7fff, page_size, backed_bytes, pointer_format)?;
                    if value & 0x8000 != 0 {
                        break;
                    }
                    cursor += 1;
                }
            }
        }
        result.push(FixupSegmentMetadata {
            segment_index: index,
            pointer_format,
            page_size,
            page_count,
            pages_with_fixups,
            multiple_start_pages,
            segment_offset,
        });
    }
    Ok(ChainedFixupMetadata {
        file,
        imports_count,
        imports_format,
        symbols_format,
        segments: result,
    })
}

fn validate_page_start(offset: u16, page_size: u16, backed_bytes: u64, format: u16) -> Result<()> {
    let width = if format == 11 { 8 } else { 1 };
    // KC chains group starts by page; an unaligned terminal word can straddle
    // it. Its full word still must fit the segment's file-backed memory.
    if offset >= page_size || u64::from(offset) + width > backed_bytes {
        return Err(E::InvalidFixups);
    }
    Ok(())
}

fn validate_collection_entry(image: &ImageMetadata) -> Result<()> {
    let entry = image.entry.as_ref().ok_or(E::MissingEntry)?;
    // LC_MAIN describes an offset relative to __TEXT. This initial fileset
    // profile does not generalize that into a collection-wide entry address.
    // Member LC_MAIN commands remain recorded with their own provenance only.
    if matches!(entry, EntryMetadata::Main { .. }) {
        return Err(E::UnsupportedCollectionEntry);
    }
    if !image.segments.iter().any(|s| {
        if s.initial_protection & 4 == 0 {
            return false;
        }
        match entry {
            EntryMetadata::UnixThread64 {
                instruction_pointer,
            } => instruction_pointer
                .checked_sub(s.address)
                .is_some_and(|n| n < s.file.size),
            EntryMetadata::Main { .. } => false,
        }
    }) {
        return Err(E::InvalidEntry);
    }
    Ok(())
}

fn is_collection_view(segments: &[SegmentMetadata], file: &FileRange, address: u64) -> bool {
    segments.iter().any(|s| {
        contains(&s.file, file)
            && address.checked_sub(s.address) == file.offset.checked_sub(s.file.offset)
    })
}

fn validate_nonoverlap(segments: &[SegmentMetadata]) -> Result<()> {
    let mut by_address: Vec<_> = segments.iter().filter(|s| s.memory_size != 0).collect();
    by_address.sort_unstable_by_key(|s| s.address);
    for p in by_address.windows(2) {
        if end(p[0].address, p[0].memory_size)? > p[1].address {
            return Err(E::OverlappingRange);
        }
    }
    let mut by_file: Vec<_> = segments.iter().filter(|s| s.file.size != 0).collect();
    by_file.sort_unstable_by_key(|s| s.file.offset);
    for p in by_file.windows(2) {
        if overlaps(&p[0].file, &p[1].file) {
            return Err(E::OverlappingRange);
        }
    }
    Ok(())
}

fn set_entry(entry: &mut Option<EntryMetadata>, value: EntryMetadata) -> Result<()> {
    if entry.replace(value).is_some() {
        return Err(E::DuplicateEntry);
    }
    Ok(())
}
fn add_budget(value: &mut usize, amount: usize, limit: usize) -> Result<()> {
    *value = value.checked_add(amount).ok_or(E::Overflow)?;
    if *value > limit {
        return Err(E::LimitExceeded);
    }
    Ok(())
}
fn end(start: u64, size: u64) -> Result<u64> {
    start.checked_add(size).ok_or(E::Overflow)
}
fn contains(outer: &FileRange, inner: &FileRange) -> bool {
    inner.offset >= outer.offset
        && inner
            .offset
            .checked_add(inner.size)
            .zip(outer.offset.checked_add(outer.size))
            .is_some_and(|(a, b)| a <= b)
}
fn overlaps(a: &FileRange, b: &FileRange) -> bool {
    a.size != 0 && b.size != 0 && a.offset < b.offset + b.size && b.offset < a.offset + a.size
}
fn file_range(bytes: &[u8], offset: u64, count: u64, width: u64) -> Result<FileRange> {
    let size = count.checked_mul(width).ok_or(E::Overflow)?;
    range(bytes, offset, size)?;
    Ok(FileRange { offset, size })
}
fn range(bytes: &[u8], offset: u64, size: u64) -> Result<&[u8]> {
    if end(offset, size)? > bytes.len() as u64 {
        return Err(E::Truncated);
    }
    slice(bytes, offset as usize, size as usize)
}
fn slice(bytes: &[u8], offset: usize, size: usize) -> Result<&[u8]> {
    bytes
        .get(offset..offset.checked_add(size).ok_or(E::Overflow)?)
        .ok_or(E::Truncated)
}
fn exact(bytes: &[u8], expected: usize) -> Result<()> {
    if bytes.len() != expected {
        return Err(E::InvalidCommand);
    }
    Ok(())
}
fn u16_at(bytes: &[u8], offset: usize) -> Result<u16> {
    Ok(u16::from_le_bytes(
        slice(bytes, offset, 2)?.try_into().unwrap(),
    ))
}
fn u32_at(bytes: &[u8], offset: usize) -> Result<u32> {
    Ok(u32::from_le_bytes(
        slice(bytes, offset, 4)?.try_into().unwrap(),
    ))
}
fn u64_at(bytes: &[u8], offset: usize) -> Result<u64> {
    Ok(u64::from_le_bytes(
        slice(bytes, offset, 8)?.try_into().unwrap(),
    ))
}
