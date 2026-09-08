//! Bounded host-memory staging of one inspected x86_64 kernel collection.
//!
//! Public format provenance and scope: `artifacts/native-kc-next-step-20260908.md`.
//! Outer segments own copies and zero-fill; members are shared views. Relative
//! arena offsets are not physical addresses or runtime mappings. No relocation,
//! executable mapping, firmware allocation, boot-argument encoding or entry is
//! performed. Successful staging never establishes preparation readiness.

use alloc::vec::Vec;
use core::fmt;

use crate::kernel_collection::{
    inspect_kernel_collection, EntryMetadata, KcMetadataError, KcMetadataInspection,
};

pub const STAGING_PAGE_SIZE: u64 = 4096;
/// Independent bound on the page-rounded memory span, including holes.
pub const MAX_STAGING_SIZE: usize = 128 * 1024 * 1024;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum KcStagingError {
    Metadata(KcMetadataError),
    EmptyImage,
    AddressOverflow,
    ArenaTooLarge,
    AllocationFailed,
    DestinationSize,
    InvalidMapping,
    ReadbackMismatch,
}

impl fmt::Display for KcStagingError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "KC_STAGING_{self:?}")
    }
}
impl core::error::Error for KcStagingError {}
impl From<KcMetadataError> for KcStagingError {
    fn from(value: KcMetadataError) -> Self {
        Self::Metadata(value)
    }
}
type Result<T> = core::result::Result<T, KcStagingError>;
use KcStagingError as E;

/// Read-only description of one outer mapping. The original command index is
/// retained even though staging copies are ordered by linked virtual address.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StagingSegment {
    pub collection_segment_index: usize,
    pub virtual_address: u64,
    pub destination_offset: usize,
    pub memory_size: usize,
    pub file_offset: usize,
    pub file_size: usize,
    /// Metadata only: host staging does not install these page protections.
    pub initial_protection: u32,
    pub maximum_protection: u32,
}

#[derive(Clone, Debug)]
struct MemberView {
    destination_offset: usize,
    memory_size: usize,
    file_offset: usize,
    file_size: usize,
    is_header: bool,
}

/// Counts describe the completed full-arena readback. Member view comparisons
/// may overlap, so `member_file_bytes_compared` is not a unique-byte count.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StagingVerification {
    pub arena_bytes: usize,
    pub copied_bytes: usize,
    pub zero_tail_bytes: usize,
    pub hole_bytes: usize,
    pub member_headers_checked: usize,
    pub member_segment_views_checked: usize,
    pub member_file_bytes_compared: usize,
}

/// An inspected plan bound to a live immutable source. Private fields prevent
/// forged plans, and borrowing prevents safe callers from replacing or mutating
/// the source while this plan or its staged result exists.
pub struct KcStagingPlan<'a> {
    source: &'a [u8],
    inspection: KcMetadataInspection,
    segments: Vec<StagingSegment>,
    member_views: Vec<MemberView>,
    minimum_virtual_address: u64,
    arena_size: usize,
    collection_header_offset: usize,
    outer_entry_offset: usize,
}

impl fmt::Debug for KcStagingPlan<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // Never expand an externally supplied image into logs via Debug.
        f.debug_struct("KcStagingPlan")
            .field("source_bytes", &self.source.len())
            .field("minimum_virtual_address", &self.minimum_virtual_address)
            .field("arena_size", &self.arena_size)
            .field("collection_header_offset", &self.collection_header_offset)
            .field("outer_entry_offset", &self.outer_entry_offset)
            .field("outer_segments", &self.segments.len())
            .field("member_views", &self.member_views.len())
            .finish()
    }
}

impl<'a> KcStagingPlan<'a> {
    pub fn new(source: &'a [u8]) -> Result<Self> {
        let inspection = inspect_kernel_collection(source)?;
        let nonempty = inspection
            .collection
            .segments
            .iter()
            .filter(|s| s.memory_size != 0);
        let mut first = u64::MAX;
        let mut last = 0;
        for segment in nonempty {
            first = first.min(segment.address);
            last = last.max(
                segment
                    .address
                    .checked_add(segment.memory_size)
                    .ok_or(E::AddressOverflow)?,
            );
        }
        if first == u64::MAX || last <= first {
            return Err(E::EmptyImage);
        }
        let minimum_virtual_address = first & !(STAGING_PAGE_SIZE - 1);
        let rounded_end = last
            .checked_add(STAGING_PAGE_SIZE - 1)
            .ok_or(E::AddressOverflow)?
            & !(STAGING_PAGE_SIZE - 1);
        let span = rounded_end
            .checked_sub(minimum_virtual_address)
            .ok_or(E::AddressOverflow)?;
        if span == 0 || span > MAX_STAGING_SIZE as u64 || span > isize::MAX as u64 {
            return Err(E::ArenaTooLarge);
        }
        let arena_size = usize::try_from(span).map_err(|_| E::ArenaTooLarge)?;
        let mut segments = Vec::new();
        segments
            .try_reserve_exact(inspection.collection.segments.len())
            .map_err(|_| E::AllocationFailed)?;
        for (index, segment) in inspection.collection.segments.iter().enumerate() {
            if segment.memory_size == 0 {
                continue;
            }
            let destination_offset = relative_range(
                segment.address,
                segment.memory_size,
                minimum_virtual_address,
                arena_size,
            )?;
            let file_offset = source_range(source, segment.file.offset, segment.file.size)?;
            segments.push(StagingSegment {
                collection_segment_index: index,
                virtual_address: segment.address,
                destination_offset,
                memory_size: usize::try_from(segment.memory_size).map_err(|_| E::ArenaTooLarge)?,
                file_offset,
                file_size: usize::try_from(segment.file.size).map_err(|_| E::InvalidMapping)?,
                initial_protection: segment.initial_protection,
                maximum_protection: segment.maximum_protection,
            });
        }
        segments.sort_unstable_by_key(|s| s.destination_offset);
        for pair in segments.windows(2) {
            if pair[0].destination_offset + pair[0].memory_size > pair[1].destination_offset {
                return Err(E::InvalidMapping);
            }
        }
        let header_size = 32 + u64::from(inspection.collection.command_bytes);
        let collection_header_offset = relative_range(
            inspection.collection.header_address,
            header_size,
            minimum_virtual_address,
            arena_size,
        )?;
        let entry = match &inspection.collection.entry {
            Some(EntryMetadata::UnixThread64 {
                instruction_pointer,
            }) => *instruction_pointer,
            _ => return Err(E::InvalidMapping),
        };
        let outer_entry_offset = relative_range(entry, 1, minimum_virtual_address, arena_size)?;
        let mut member_views = Vec::new();
        let view_count = inspection
            .members
            .iter()
            .try_fold(0usize, |total, member| {
                total
                    .checked_add(1)
                    .and_then(|n| n.checked_add(member.image.segments.len()))
                    .ok_or(E::AddressOverflow)
            })?;
        member_views
            .try_reserve_exact(view_count)
            .map_err(|_| E::AllocationFailed)?;
        for member in &inspection.members {
            let image = &member.image;
            let header_size = 32 + u64::from(image.command_bytes);
            member_views.push(view(
                source,
                &segments,
                minimum_virtual_address,
                arena_size,
                image.header_address,
                header_size,
                image.header_file_offset,
                header_size,
                true,
            )?);
            for segment in &image.segments {
                if segment.memory_size == 0 {
                    continue;
                }
                member_views.push(view(
                    source,
                    &segments,
                    minimum_virtual_address,
                    arena_size,
                    segment.address,
                    segment.memory_size,
                    segment.file.offset,
                    segment.file.size,
                    false,
                )?);
            }
        }
        Ok(Self {
            source,
            inspection,
            segments,
            member_views,
            minimum_virtual_address,
            arena_size,
            collection_header_offset,
            outer_entry_offset,
        })
    }

    pub fn inspection(&self) -> &KcMetadataInspection {
        &self.inspection
    }
    pub fn segments(&self) -> &[StagingSegment] {
        &self.segments
    }
    pub fn minimum_virtual_address(&self) -> u64 {
        self.minimum_virtual_address
    }
    pub fn arena_size(&self) -> usize {
        self.arena_size
    }
    pub fn collection_header_offset(&self) -> usize {
        self.collection_header_offset
    }
    pub fn outer_entry_offset(&self) -> usize {
        self.outer_entry_offset
    }
    pub fn preparation_ready(&self) -> bool {
        false
    }

    /// Materialize into a caller-owned slice of exactly `arena_size()` bytes.
    /// A size rejection leaves it unchanged. After copying, every arena byte
    /// and member file view is read back. On a readback error the caller must
    /// discard the contents; no successful result is returned.
    pub fn stage_into(&self, destination: &mut [u8]) -> Result<StagingVerification> {
        if destination.len() != self.arena_size {
            return Err(E::DestinationSize);
        }
        destination.fill(0);
        for segment in &self.segments {
            destination[segment.destination_offset..segment.destination_offset + segment.file_size]
                .copy_from_slice(
                    &self.source[segment.file_offset..segment.file_offset + segment.file_size],
                );
        }
        self.verify(destination)
    }

    /// Re-read a staged arena without modifying it. This also permits callers
    /// to detect corruption after a prior successful staging operation.
    pub fn verify(&self, destination: &[u8]) -> Result<StagingVerification> {
        if destination.len() != self.arena_size {
            return Err(E::DestinationSize);
        }
        let mut result = StagingVerification {
            arena_bytes: self.arena_size,
            copied_bytes: 0,
            zero_tail_bytes: 0,
            hole_bytes: 0,
            member_headers_checked: 0,
            member_segment_views_checked: 0,
            member_file_bytes_compared: 0,
        };
        let mut previous_end = 0;
        for segment in &self.segments {
            let start = segment.destination_offset;
            let copied_end = start + segment.file_size;
            let memory_end = start + segment.memory_size;
            if !readback(&destination[previous_end..start], None)
                || !readback(
                    &destination[start..copied_end],
                    Some(
                        &self.source[segment.file_offset..segment.file_offset + segment.file_size],
                    ),
                )
                || !readback(&destination[copied_end..memory_end], None)
            {
                return Err(E::ReadbackMismatch);
            }
            result.copied_bytes += segment.file_size;
            result.zero_tail_bytes += segment.memory_size - segment.file_size;
            result.hole_bytes += start - previous_end;
            previous_end = memory_end;
        }
        if !readback(&destination[previous_end..], None) {
            return Err(E::ReadbackMismatch);
        }
        result.hole_bytes += destination.len() - previous_end;
        for view in &self.member_views {
            // Member memory tails are intentionally not zeroed or compared to
            // zero: only the owning outer mapping determines those contents.
            if view.destination_offset + view.memory_size > destination.len()
                || !readback(
                    &destination[view.destination_offset..view.destination_offset + view.file_size],
                    Some(&self.source[view.file_offset..view.file_offset + view.file_size]),
                )
            {
                return Err(E::ReadbackMismatch);
            }
            if view.is_header {
                result.member_headers_checked += 1;
            } else {
                result.member_segment_views_checked += 1;
            }
            result.member_file_bytes_compared = result
                .member_file_bytes_compared
                .checked_add(view.file_size)
                .ok_or(E::AddressOverflow)?;
        }
        Ok(result)
    }

    /// Allocate an ordinary owned arena. This does not request executable
    /// memory. All allocations are released normally on errors or on drop.
    pub fn stage(self) -> Result<StagedKc<'a>> {
        let mut bytes = Vec::new();
        bytes
            .try_reserve_exact(self.arena_size)
            .map_err(|_| E::AllocationFailed)?;
        bytes.resize(self.arena_size, 0);
        let verification = self.stage_into(&mut bytes)?;
        Ok(StagedKc {
            plan: self,
            bytes,
            verification,
        })
    }
}

/// Owned, verified bytes plus their source-bound plan. No mutable arena or
/// entry function pointer is exposed; this type carries no execution authority.
pub struct StagedKc<'a> {
    plan: KcStagingPlan<'a>,
    bytes: Vec<u8>,
    verification: StagingVerification,
}

impl fmt::Debug for StagedKc<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("StagedKc")
            .field("plan", &self.plan)
            .field("verification", &self.verification)
            .finish()
    }
}

impl<'a> StagedKc<'a> {
    pub fn plan(&self) -> &KcStagingPlan<'a> {
        &self.plan
    }
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    pub fn verification(&self) -> &StagingVerification {
        &self.verification
    }
    pub fn preparation_ready(&self) -> bool {
        false
    }
}

fn relative_range(address: u64, size: u64, base: u64, arena: usize) -> Result<usize> {
    let start = address.checked_sub(base).ok_or(E::InvalidMapping)?;
    if start.checked_add(size).ok_or(E::AddressOverflow)? > arena as u64 {
        return Err(E::InvalidMapping);
    }
    usize::try_from(start).map_err(|_| E::InvalidMapping)
}

fn source_range(source: &[u8], offset: u64, size: u64) -> Result<usize> {
    if offset.checked_add(size).ok_or(E::AddressOverflow)? > source.len() as u64 {
        return Err(E::InvalidMapping);
    }
    usize::try_from(offset).map_err(|_| E::InvalidMapping)
}

#[allow(clippy::too_many_arguments)]
fn view(
    source: &[u8],
    segments: &[StagingSegment],
    base: u64,
    arena: usize,
    address: u64,
    memory_size: u64,
    file_offset: u64,
    file_size: u64,
    is_header: bool,
) -> Result<MemberView> {
    let destination_offset = relative_range(address, memory_size, base, arena)?;
    let file_offset = source_range(source, file_offset, file_size)?;
    let memory_size = usize::try_from(memory_size).map_err(|_| E::InvalidMapping)?;
    let file_size = usize::try_from(file_size).map_err(|_| E::InvalidMapping)?;
    if file_size > memory_size
        || !segments.iter().any(|outer| {
            destination_offset >= outer.destination_offset
                && destination_offset + memory_size <= outer.destination_offset + outer.memory_size
                && (file_size == 0
                    || (file_offset >= outer.file_offset
                        && file_offset + file_size <= outer.file_offset + outer.file_size
                        && destination_offset - outer.destination_offset
                            == file_offset - outer.file_offset))
        })
    {
        return Err(E::InvalidMapping);
    }
    Ok(MemberView {
        destination_offset,
        memory_size,
        file_offset,
        file_size,
        is_header,
    })
}

/// Volatile reads prevent the compiler from satisfying verification by reusing
/// the preceding stores. Aligned word reads keep a bounded large image usable
/// in a debug host build; prefix/suffix bytes cover unaligned format ranges.
fn readback(actual: &[u8], expected: Option<&[u8]>) -> bool {
    if expected.is_some_and(|bytes| bytes.len() != actual.len()) {
        return false;
    }
    // SAFETY: every byte is initialized and u64 accepts every bit pattern.
    let (prefix, words, suffix) = unsafe { actual.align_to::<u64>() };
    let mut offset = 0;
    for byte in prefix {
        // SAFETY: the byte is live and initialized for the duration of the read.
        if unsafe { core::ptr::read_volatile(byte) } != expected.map_or(0, |bytes| bytes[offset]) {
            return false;
        }
        offset += 1;
    }
    for word in words {
        let expected_word = expected.map_or(0, |bytes| {
            u64::from_ne_bytes(bytes[offset..offset + 8].try_into().unwrap())
        });
        // SAFETY: align_to supplies aligned, live and initialized words.
        if unsafe { core::ptr::read_volatile(word) } != expected_word {
            return false;
        }
        offset += 8;
    }
    for byte in suffix {
        // SAFETY: same initialized-byte guarantee as the prefix.
        if unsafe { core::ptr::read_volatile(byte) } != expected.map_or(0, |bytes| bytes[offset]) {
            return false;
        }
        offset += 1;
    }
    true
}
