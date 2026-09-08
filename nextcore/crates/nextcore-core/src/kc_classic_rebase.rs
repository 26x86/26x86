//! Kernel-proper classic relocations in an owned host arena, never XNU entry.
//! Public contract: `artifacts/kc-classic-relocation-contract-20260908.md`.
use crate::{
    kc_fixup_audit::{
        audit_kernel_collection, AuditError, ClassicTable, MemberOverlap, RecordDetail,
    },
    kc_staging::{KcStagingError, KcStagingPlan, StagingVerification},
    kernel_collection::ImageMetadata,
};
use alloc::vec::Vec;
use core::fmt;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ClassicRebaseError {
    Staging(KcStagingError),
    Audit(AuditError),
    AuditIssues,
    ExecutableMemberCount,
    EmptyClassicTable,
    UnsupportedClassicProfile,
    OutsideKernelFileMapping,
    HeaderWrite,
    AddressOverflow,
    /// Outside this conservative subset, not necessarily malformed Mach-O.
    ValueOverflow,
    AllocationFailed,
    DestinationSize,
    ReadbackMismatch,
}
impl fmt::Display for ClassicRebaseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "KC_CLASSIC_REBASE_{self:?}")
    }
}
impl core::error::Error for ClassicRebaseError {}
impl From<KcStagingError> for ClassicRebaseError {
    fn from(e: KcStagingError) -> Self {
        Self::Staging(e)
    }
}
impl From<AuditError> for ClassicRebaseError {
    fn from(e: AuditError) -> Self {
        Self::Audit(e)
    }
}
type Result<T> = core::result::Result<T, ClassicRebaseError>;
use ClassicRebaseError as E;

#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct ClassicRebaseVerification {
    pub slide: u32,
    pub arena_bytes: usize,
    pub classic_words: usize,
    pub width4_words: usize,
    pub width8_words: usize,
    pub write_bytes_verified: usize,
    pub non_target_bytes_verified: usize,
    pub changed_bytes: usize,
    pub chain_words_preserved: usize,
    pub header_ranges_preserved: usize,
}

struct Word {
    offset: usize,
    width: usize,
    after: [u8; 8],
}

/// Private fields bind all decisions to the immutable source. Runtime slide
/// selection and virtual/physical placement are deliberately not inferred.
pub struct KcClassicRebasePlan<'a> {
    source: &'a [u8],
    staging: KcStagingPlan<'a>,
    words: Vec<Word>,
    verification: ClassicRebaseVerification,
}
impl fmt::Debug for KcClassicRebasePlan<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("KcClassicRebasePlan")
            .field("verification", &self.verification)
            .finish()
    }
}

impl<'a> KcClassicRebasePlan<'a> {
    pub fn new(source: &'a [u8], slide: u32) -> Result<Self> {
        let staging = KcStagingPlan::new(source)?;
        let inspection = staging.inspection();
        let mut executables = inspection.members.iter().filter(|m| m.image.file_type == 2);
        let kernel = &executables.next().ok_or(E::ExecutableMemberCount)?.image;
        if executables.next().is_some() {
            return Err(E::ExecutableMemberCount);
        }
        let audit = audit_kernel_collection(source)?;
        if !audit.ranges_valid() {
            return Err(E::AuditIssues);
        }
        if audit.summary().classic_records == 0 {
            return Err(E::EmptyClassicTable);
        }
        let mut words = Vec::new();
        words
            .try_reserve_exact(audit.summary().classic_records)
            .map_err(|_| E::AllocationFailed)?;
        let mut verification = ClassicRebaseVerification {
            slide,
            arena_bytes: staging.arena_size(),
            classic_words: 0,
            width4_words: 0,
            width8_words: 0,
            write_bytes_verified: 0,
            non_target_bytes_verified: 0,
            changed_bytes: 0,
            chain_words_preserved: audit.summary().chain_records,
            header_ranges_preserved: inspection.members.len() + 1,
        };
        for record in audit.records() {
            let RecordDetail::Classic {
                table,
                symbol_ordinal,
                relocation_type,
                length_exponent,
                pc_relative,
                external,
                stored_value,
                ..
            } = &record.detail
            else {
                continue;
            };
            if record.image_index != 0
                || *table != ClassicTable::LocalDynamic
                || *symbol_ordinal != 0
                || *relocation_type != 0
                || *pc_relative
                || *external
                || !matches!(length_exponent, 2 | 3)
                || record.width != (1u8 << length_exponent)
                || record.member_overlap != MemberOverlap::ExecutableMember
            {
                return Err(E::UnsupportedClassicProfile);
            }
            let address = record.write_address.ok_or(E::OutsideKernelFileMapping)?;
            let file = record
                .write_file_offset
                .ok_or(E::OutsideKernelFileMapping)?;
            let width = usize::from(record.width);
            if !file_mapping_matches(kernel, address, file, width as u64)? {
                return Err(E::OutsideKernelFileMapping);
            }
            for image in core::iter::once(&inspection.collection)
                .chain(inspection.members.iter().map(|m| &m.image))
            {
                let header_size = 32 + u64::from(image.command_bytes);
                if overlaps(file, width as u64, image.header_file_offset, header_size)?
                    || overlaps(address, width as u64, image.header_address, header_size)?
                {
                    return Err(E::HeaderWrite);
                }
            }
            let before = stored_value.ok_or(E::OutsideKernelFileMapping)?;
            let after = before
                .checked_add(u64::from(slide))
                .ok_or(E::ValueOverflow)?;
            if width == 4 && after > u64::from(u32::MAX) {
                return Err(E::ValueOverflow);
            }
            let offset = usize::try_from(
                address
                    .checked_sub(staging.minimum_virtual_address())
                    .ok_or(E::AddressOverflow)?,
            )
            .map_err(|_| E::AddressOverflow)?;
            let end = offset.checked_add(width).ok_or(E::AddressOverflow)?;
            if end > staging.arena_size() {
                return Err(E::OutsideKernelFileMapping);
            }
            let source_start = usize::try_from(file).map_err(|_| E::AddressOverflow)?;
            let source_end = source_start.checked_add(width).ok_or(E::AddressOverflow)?;
            let raw = source
                .get(source_start..source_end)
                .ok_or(E::OutsideKernelFileMapping)?;
            let before_bytes = before.to_le_bytes();
            if raw != &before_bytes[..width] {
                return Err(E::UnsupportedClassicProfile);
            }
            let after = after.to_le_bytes();
            verification.changed_bytes += raw
                .iter()
                .zip(&after[..width])
                .filter(|(a, b)| a != b)
                .count();
            verification.classic_words += 1;
            verification.write_bytes_verified += width;
            if width == 4 {
                verification.width4_words += 1
            } else {
                verification.width8_words += 1
            }
            words.push(Word {
                offset,
                width,
                after,
            });
        }
        words.sort_unstable_by_key(|w| w.offset);
        for pair in words.windows(2) {
            if pair[0].offset + pair[0].width > pair[1].offset {
                return Err(E::AuditIssues);
            }
        }
        verification.non_target_bytes_verified = verification
            .arena_bytes
            .checked_sub(verification.write_bytes_verified)
            .ok_or(E::AddressOverflow)?;
        Ok(Self {
            source,
            staging,
            words,
            verification,
        })
    }

    pub fn planned_summary(&self) -> &ClassicRebaseVerification {
        &self.verification
    }
    pub const fn preparation_ready(&self) -> bool {
        false
    }

    /// Allocate only after the complete plan has passed. Stage_into performs
    /// full source-equivalence readback before any of the classic writes.
    pub fn apply(self) -> Result<RebasedKc<'a>> {
        let mut bytes = Vec::new();
        bytes
            .try_reserve_exact(self.staging.arena_size())
            .map_err(|_| E::AllocationFailed)?;
        bytes.resize(self.staging.arena_size(), 0);
        let original_staging = self.staging.stage_into(&mut bytes)?;
        for word in &self.words {
            bytes[word.offset..word.offset + word.width].copy_from_slice(&word.after[..word.width]);
        }
        self.verify(&bytes)?;
        Ok(RebasedKc {
            plan: self,
            bytes,
            original_staging,
        })
    }

    /// Read-only comparison against this plan's exact post-rebase image. This
    /// accepts a slice for corruption detection, never for in-place application.
    pub fn verify(&self, bytes: &[u8]) -> Result<ClassicRebaseVerification> {
        if bytes.len() != self.staging.arena_size() {
            return Err(E::DestinationSize);
        }
        let segments = self.staging.segments();
        let (mut cursor, mut si, mut wi) = (0, 0, 0);
        while cursor < bytes.len() {
            if let Some(word) = self.words.get(wi) {
                if word.offset == cursor {
                    if !readback(
                        &bytes[cursor..cursor + word.width],
                        Some(&word.after[..word.width]),
                    ) {
                        return Err(E::ReadbackMismatch);
                    }
                    cursor += word.width;
                    wi += 1;
                    continue;
                }
            }
            while si < segments.len()
                && cursor >= segments[si].destination_offset + segments[si].memory_size
            {
                si += 1;
            }
            let next_word = self.words.get(wi).map_or(bytes.len(), |w| w.offset);
            let mut end = next_word;
            let mut source_start = None;
            if let Some(segment) = segments.get(si) {
                if cursor < segment.destination_offset {
                    end = end.min(segment.destination_offset);
                } else {
                    let copy_end = segment.destination_offset + segment.file_size;
                    if cursor < copy_end {
                        end = end.min(copy_end);
                        source_start =
                            Some(segment.file_offset + cursor - segment.destination_offset);
                    } else {
                        end = end.min(segment.destination_offset + segment.memory_size);
                    }
                }
            }
            if end <= cursor {
                return Err(E::ReadbackMismatch);
            }
            let expected = source_start.map(|at| &self.source[at..at + end - cursor]);
            if !readback(&bytes[cursor..end], expected) {
                return Err(E::ReadbackMismatch);
            }
            cursor = end;
        }
        if wi != self.words.len() {
            return Err(E::ReadbackMismatch);
        }
        Ok(self.verification.clone())
    }
}

/// Owns ordinary initialized memory. No mutable bytes, raw entry, or native
/// handoff capability is exposed. The original immutable input stays borrowed.
pub struct RebasedKc<'a> {
    plan: KcClassicRebasePlan<'a>,
    bytes: Vec<u8>,
    original_staging: StagingVerification,
}
impl fmt::Debug for RebasedKc<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("RebasedKc")
            .field("verification", self.verification())
            .finish()
    }
}
impl<'a> RebasedKc<'a> {
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    pub fn plan(&self) -> &KcClassicRebasePlan<'a> {
        &self.plan
    }
    pub fn verification(&self) -> &ClassicRebaseVerification {
        &self.plan.verification
    }
    pub fn original_staging(&self) -> &StagingVerification {
        &self.original_staging
    }
    pub const fn classic_relocations_applied(&self) -> bool {
        true
    }
    pub const fn preparation_ready(&self) -> bool {
        false
    }
}

fn overlaps(a: u64, alen: u64, b: u64, blen: u64) -> Result<bool> {
    Ok(a < b.checked_add(blen).ok_or(E::AddressOverflow)?
        && b < a.checked_add(alen).ok_or(E::AddressOverflow)?)
}
fn file_mapping_matches(
    image: &ImageMetadata,
    address: u64,
    file: u64,
    width: u64,
) -> Result<bool> {
    let end = address.checked_add(width).ok_or(E::AddressOverflow)?;
    for segment in &image.segments {
        let file_end = segment
            .address
            .checked_add(segment.file.size)
            .ok_or(E::AddressOverflow)?;
        if address >= segment.address && end <= file_end {
            return Ok(segment
                .file
                .offset
                .checked_add(address - segment.address)
                .ok_or(E::AddressOverflow)?
                == file);
        }
    }
    Ok(false)
}

// All expected values are independent source/plan bytes; volatile reads cannot
// be replaced with the preceding stores. Align only initialized u64 bit patterns.
fn readback(actual: &[u8], expected: Option<&[u8]>) -> bool {
    if expected.is_some_and(|b| b.len() != actual.len()) {
        return false;
    }
    // SAFETY: initialized bytes, valid for every u64 bit pattern.
    let (prefix, words, suffix) = unsafe { actual.align_to::<u64>() };
    let mut offset = 0;
    for byte in prefix {
        // SAFETY: live initialized byte.
        if unsafe { core::ptr::read_volatile(byte) } != expected.map_or(0, |b| b[offset]) {
            return false;
        }
        offset += 1;
    }
    for word in words {
        let value = expected.map_or(0, |b| {
            u64::from_ne_bytes(b[offset..offset + 8].try_into().unwrap())
        });
        // SAFETY: align_to produced a live aligned initialized word.
        if unsafe { core::ptr::read_volatile(word) } != value {
            return false;
        }
        offset += 8;
    }
    for byte in suffix {
        // SAFETY: live initialized byte.
        if unsafe { core::ptr::read_volatile(byte) } != expected.map_or(0, |b| b[offset]) {
            return false;
        }
        offset += 1;
    }
    true
}
