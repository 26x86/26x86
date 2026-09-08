//! Read-only classic/format-11 write-target audit. Never applies a fixup.
//! Public provenance: `artifacts/kc-fixup-audit-contract-20260908.md`.
use crate::kernel_collection::{
    inspect_kernel_collection, FileRange, ImageMetadata, KcMetadataError, KcMetadataInspection,
    SegmentMetadata,
};
use alloc::vec::Vec;
use core::fmt;

pub const MAX_AUDIT_RECORDS: usize = 1_000_000;
pub const MAX_AUDIT_ISSUES: usize = 1_000_000;
pub const MAX_AUDIT_PAGE_STARTS: usize = 1_000_000;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AuditLimits {
    pub records: usize,
    pub issues: usize,
    pub page_starts: usize,
}
impl Default for AuditLimits {
    fn default() -> Self {
        Self {
            records: MAX_AUDIT_RECORDS,
            issues: MAX_AUDIT_ISSUES,
            page_starts: MAX_AUDIT_PAGE_STARTS,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum AuditError {
    Metadata(KcMetadataError),
    InvalidLimits,
    LimitExceeded,
    AllocationFailed,
    InvalidMetadata,
    Overflow,
}
impl fmt::Display for AuditError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "KC_FIXUP_AUDIT_{self:?}")
    }
}
impl core::error::Error for AuditError {}
impl From<KcMetadataError> for AuditError {
    fn from(e: KcMetadataError) -> Self {
        Self::Metadata(e)
    }
}
type Result<T> = core::result::Result<T, AuditError>;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub enum IssueCode {
    UnsupportedClassicType,
    UnsupportedClassicWidth,
    UnsupportedPcRelative,
    UnsupportedExternal,
    MissingClassicBase,
    NegativeSectionDisplacement,
    WriteOutsideSection,
    WriteOutsideFileMapping,
    WriteAddressOverflow,
    UnsupportedPointerFormat,
    UnsupportedImports,
    UnsupportedCompressedSymbols,
    UnsupportedMultiStartConsumer,
    ChainOutsidePage,
    ChainOutsideFileMapping,
    DuplicateChainVisit,
    MissingCacheBase,
    UnsupportedAuthentication,
    PointerTargetOverflow,
    PointerTargetOutsideMappings,
    SameMechanismWriteOverlap,
    CrossMechanismWriteOverlap,
}
#[derive(Clone, Debug)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct AuditIssue {
    pub code: IssueCode,
    pub image_index: usize,
    pub record_index: Option<usize>,
    pub related_record_index: Option<usize>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub enum ClassicTable {
    LocalDynamic,
    ExternalDynamic,
    Section,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub enum MemberOverlap {
    ExecutableMember,
    KextMember,
    Both,
    OuterOnly,
}
#[derive(Clone, Debug)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub enum RecordDetail {
    Classic {
        table: ClassicTable,
        displacement: i32,
        symbol_ordinal: u32,
        relocation_type: u8,
        length_exponent: u8,
        pc_relative: bool,
        external: bool,
        /// Raw word evidence only; no final classic pointer interpretation.
        stored_value: Option<u64>,
    },
    Chain11 {
        segment_index: usize,
        page_index: usize,
        target_offset: u32,
        cache_level: u8,
        diversity: u16,
        address_diversity: bool,
        key: u8,
        next: u16,
        authenticated: bool,
        resolved_target: Option<u64>,
        /// Point containment only, not the size/semantics of a pointee object.
        target_in_primary_mapping: bool,
    },
}
#[derive(Clone, Debug)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct AuditRecord {
    /// Zero is outer; n+1 is the nth fileset member. This is source provenance.
    pub image_index: usize,
    pub source_record_offset: u64,
    pub write_address: Option<u64>,
    pub write_file_offset: Option<u64>,
    pub width: u8,
    /// Which member mappings intersect this write; not execution ownership.
    pub member_overlap: MemberOverlap,
    pub detail: RecordDetail,
}
#[derive(Clone, Debug, Default)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct AuditSummary {
    pub classic_records: usize,
    pub classic_negative_displacements: usize,
    pub classic_types: [usize; 16],
    pub classic_width_exponents: [usize; 4],
    pub classic_pc_relative: usize,
    pub classic_external: usize,
    pub chain_records: usize,
    pub chain_starts: usize,
    pub chains_terminated: usize,
    pub chain_page_straddling_words: usize,
    pub page_starts_visited: usize,
    pub multi_start_pages: usize,
    pub chain_cache_levels: [usize; 4],
    pub authenticated_words: usize,
    pub primary_pointer_targets_covered: usize,
    pub file_backed_write_records: usize,
    pub executable_member_write_records: usize,
    pub kext_member_write_records: usize,
    pub both_member_write_records: usize,
    pub outer_only_write_records: usize,
    pub issue_counts: Vec<IssueCount>,
}
#[derive(Clone, Debug)]
#[cfg_attr(feature = "std", derive(serde::Serialize))]
pub struct IssueCount {
    pub code: IssueCode,
    pub count: usize,
}

/// Detailed records contain input-derived addresses; save actual-image details
/// only in isolation. Debug intentionally prints no record/target list.
pub struct KcFixupAudit {
    summary: AuditSummary,
    records: Vec<AuditRecord>,
    issues: Vec<AuditIssue>,
    primary_base: u64,
}
impl fmt::Debug for KcFixupAudit {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("KcFixupAudit")
            .field("summary", &self.summary)
            .finish()
    }
}
impl KcFixupAudit {
    pub fn summary(&self) -> &AuditSummary {
        &self.summary
    }
    pub fn records(&self) -> &[AuditRecord] {
        &self.records
    }
    pub fn issues(&self) -> &[AuditIssue] {
        &self.issues
    }
    pub fn primary_base(&self) -> u64 {
        self.primary_base
    }
    pub fn ranges_valid(&self) -> bool {
        self.issues.is_empty()
    }
    pub const fn preparation_ready(&self) -> bool {
        false
    }
    pub const fn relocations_applied(&self) -> bool {
        false
    }
    pub const fn ownership_resolved(&self) -> bool {
        false
    }
}

#[derive(Clone)]
struct Mapping {
    start: u64,
    end: u64,
    file_end: u64,
    file_offset: u64,
}
fn mappings(segments: &[SegmentMetadata]) -> Result<Vec<Mapping>> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(segments.len())
        .map_err(|_| AuditError::AllocationFailed)?;
    for s in segments.iter().filter(|s| s.memory_size != 0) {
        result.push(Mapping {
            start: s.address,
            end: add(s.address, s.memory_size)?,
            file_end: add(s.address, s.file.size)?,
            file_offset: s.file.offset,
        });
    }
    result.sort_unstable_by_key(|m| m.start);
    Ok(result)
}
fn containing(maps: &[Mapping], address: u64, width: u64) -> Option<&Mapping> {
    let index = maps
        .partition_point(|m| m.start <= address)
        .checked_sub(1)?;
    let m = &maps[index];
    (address.checked_add(width)? <= m.end).then_some(m)
}
fn file_location(maps: &[Mapping], address: u64, width: u64) -> Option<u64> {
    let m = containing(maps, address, width)?;
    (address.checked_add(width)? <= m.file_end).then(|| m.file_offset + (address - m.start))
}
fn add(a: u64, b: u64) -> Result<u64> {
    a.checked_add(b).ok_or(AuditError::Overflow)
}
fn raw(source: &[u8], at: u64, size: usize) -> Result<&[u8]> {
    let end = add(at, size as u64)?;
    if end > source.len() as u64 {
        return Err(AuditError::InvalidMetadata);
    }
    Ok(&source[at as usize..end as usize])
}
fn u16_at(source: &[u8], at: u64) -> Result<u16> {
    Ok(u16::from_le_bytes(raw(source, at, 2)?.try_into().unwrap()))
}
fn u32_at(source: &[u8], at: u64) -> Result<u32> {
    Ok(u32::from_le_bytes(raw(source, at, 4)?.try_into().unwrap()))
}
fn word_at(source: &[u8], at: u64, width: u8) -> Result<u64> {
    let mut b = [0; 8];
    b[..width as usize].copy_from_slice(raw(source, at, width as usize)?);
    Ok(u64::from_le_bytes(b))
}
fn push_bounded<T>(items: &mut Vec<T>, value: T, limit: usize) -> Result<usize> {
    if items.len() >= limit {
        return Err(AuditError::LimitExceeded);
    }
    if items.len() == items.capacity() {
        items
            .try_reserve((limit - items.len()).min(1024))
            .map_err(|_| AuditError::AllocationFailed)?;
    }
    let index = items.len();
    items.push(value);
    Ok(index)
}

struct Audit<'a> {
    source: &'a [u8],
    limits: AuditLimits,
    out: KcFixupAudit,
    outer: Vec<Mapping>,
    executable: Vec<(u64, u64)>,
    kext: Vec<(u64, u64)>,
}
impl Audit<'_> {
    fn issue(
        &mut self,
        code: IssueCode,
        image: usize,
        record: Option<usize>,
        related: Option<usize>,
    ) -> Result<()> {
        push_bounded(
            &mut self.out.issues,
            AuditIssue {
                code,
                image_index: image,
                record_index: record,
                related_record_index: related,
            },
            self.limits.issues,
        )?;
        Ok(())
    }
    fn page_start(&mut self) -> Result<()> {
        if self.out.summary.page_starts_visited >= self.limits.page_starts {
            return Err(AuditError::LimitExceeded);
        }
        self.out.summary.page_starts_visited += 1;
        Ok(())
    }
    fn member_overlap(&self, address: Option<u64>, width: u8) -> MemberOverlap {
        let Some(start) = address else {
            return MemberOverlap::OuterOnly;
        };
        let Some(end) = start.checked_add(u64::from(width)) else {
            return MemberOverlap::OuterOnly;
        };
        let intersects = |ranges: &[(u64, u64)]| {
            let n = ranges.partition_point(|r| r.0 < end);
            n != 0 && ranges[n - 1].1 > start
        };
        match (intersects(&self.executable), intersects(&self.kext)) {
            (true, true) => MemberOverlap::Both,
            (true, false) => MemberOverlap::ExecutableMember,
            (false, true) => MemberOverlap::KextMember,
            _ => MemberOverlap::OuterOnly,
        }
    }
    fn record(&mut self, record: AuditRecord) -> Result<usize> {
        if record.write_file_offset.is_some() {
            self.out.summary.file_backed_write_records += 1;
        }
        match record.member_overlap {
            MemberOverlap::ExecutableMember => {
                self.out.summary.executable_member_write_records += 1
            }
            MemberOverlap::KextMember => self.out.summary.kext_member_write_records += 1,
            MemberOverlap::Both => self.out.summary.both_member_write_records += 1,
            MemberOverlap::OuterOnly => self.out.summary.outer_only_write_records += 1,
        }
        push_bounded(&mut self.out.records, record, self.limits.records)
    }
    fn classic(
        &mut self,
        image_index: usize,
        section_size: Option<u64>,
        maps: &[Mapping],
        table: ClassicTable,
        range: &FileRange,
        base: Option<u64>,
    ) -> Result<()> {
        for at in (0..range.size).step_by(8) {
            let offset = add(range.offset, at)?;
            let displacement = u32_at(self.source, offset)? as i32;
            let info = u32_at(self.source, offset + 4)?;
            let kind = (info >> 28) as u8;
            let length = ((info >> 25) & 3) as u8;
            let width = 1u8 << length;
            let pc = info & (1 << 24) != 0;
            let external = info & (1 << 27) != 0;
            let address = base.and_then(|b| b.checked_add_signed(i64::from(displacement)));
            let file = address
                .and_then(|a| file_location(maps, a, u64::from(width)))
                .filter(|off| {
                    address.and_then(|a| file_location(&self.outer, a, u64::from(width)))
                        == Some(*off)
                });
            let stored_value = file
                .map(|off| word_at(self.source, off, width))
                .transpose()?;
            let index = self.record(AuditRecord {
                image_index,
                source_record_offset: offset,
                write_address: address,
                write_file_offset: file,
                width,
                member_overlap: self.member_overlap(address, width),
                detail: RecordDetail::Classic {
                    table,
                    displacement,
                    symbol_ordinal: info & 0xff_ffff,
                    relocation_type: kind,
                    length_exponent: length,
                    pc_relative: pc,
                    external,
                    stored_value,
                },
            })?;
            let s = &mut self.out.summary;
            s.classic_records += 1;
            s.classic_types[kind as usize] += 1;
            s.classic_width_exponents[length as usize] += 1;
            s.classic_negative_displacements += usize::from(displacement < 0);
            s.classic_pc_relative += usize::from(pc);
            s.classic_external += usize::from(external);
            let mut codes = Vec::new();
            if kind != 0 {
                codes.push(IssueCode::UnsupportedClassicType)
            }
            if length < 2 {
                codes.push(IssueCode::UnsupportedClassicWidth)
            }
            if pc {
                codes.push(IssueCode::UnsupportedPcRelative)
            }
            if external || table == ClassicTable::ExternalDynamic {
                codes.push(IssueCode::UnsupportedExternal)
            }
            if base.is_none() {
                codes.push(IssueCode::MissingClassicBase)
            } else if address.is_none() {
                codes.push(IssueCode::WriteAddressOverflow)
            }
            if table == ClassicTable::Section && displacement < 0 {
                codes.push(IssueCode::NegativeSectionDisplacement)
            }
            if section_size.is_some_and(|size| {
                displacement < 0
                    || (displacement as u64)
                        .checked_add(u64::from(width))
                        .is_none_or(|end| end > size)
            }) {
                codes.push(IssueCode::WriteOutsideSection)
            }
            if file.is_none() {
                codes.push(IssueCode::WriteOutsideFileMapping)
            }
            for code in codes {
                self.issue(code, image_index, Some(index), None)?;
            }
        }
        Ok(())
    }
    fn chain(
        &mut self,
        image_index: usize,
        segment_index: usize,
        page_index: usize,
        segment: &SegmentMetadata,
        page_size: u16,
        start: u16,
    ) -> Result<()> {
        self.out.summary.chain_starts += 1;
        let page_offset = (page_index as u64)
            .checked_mul(u64::from(page_size))
            .ok_or(AuditError::Overflow)?;
        let mut in_page = u64::from(start);
        loop {
            // The public KC producer groups fixup starts by page. A terminal
            // unaligned word may straddle it; its full segment/file bounds
            // remain mandatory below. Next starts cannot leave this page.
            if in_page >= u64::from(page_size) {
                self.issue(IssueCode::ChainOutsidePage, image_index, None, None)?;
                break;
            }
            let segment_offset = add(page_offset, in_page)?;
            if segment_offset
                .checked_add(8)
                .is_none_or(|end| end > segment.file.size || end > segment.memory_size)
            {
                self.issue(IssueCode::ChainOutsideFileMapping, image_index, None, None)?;
                break;
            }
            let address = add(segment.address, segment_offset)?;
            let file = add(segment.file.offset, segment_offset)?;
            if file_location(&self.outer, address, 8) != Some(file) {
                self.issue(IssueCode::ChainOutsideFileMapping, image_index, None, None)?;
                break;
            }
            let word = word_at(self.source, file, 8)?;
            let target = (word & 0x3fff_ffff) as u32;
            let cache = ((word >> 30) & 3) as u8;
            let auth = word >> 63 != 0;
            let next = ((word >> 51) & 0xfff) as u16;
            let resolved = if cache == 0 && self.out.primary_base != 0 {
                self.out.primary_base.checked_add(u64::from(target))
            } else {
                None
            };
            let covered = resolved.is_some_and(|a| containing(&self.outer, a, 1).is_some());
            let index = self.record(AuditRecord {
                image_index,
                source_record_offset: file,
                write_address: Some(address),
                write_file_offset: Some(file),
                width: 8,
                member_overlap: self.member_overlap(Some(address), 8),
                detail: RecordDetail::Chain11 {
                    segment_index,
                    page_index,
                    target_offset: target,
                    cache_level: cache,
                    diversity: ((word >> 32) & 0xffff) as u16,
                    address_diversity: word & (1 << 48) != 0,
                    key: ((word >> 49) & 3) as u8,
                    next,
                    authenticated: auth,
                    resolved_target: resolved,
                    target_in_primary_mapping: covered,
                },
            })?;
            let s = &mut self.out.summary;
            s.chain_records += 1;
            s.chain_page_straddling_words += usize::from(in_page + 8 > u64::from(page_size));
            s.chain_cache_levels[cache as usize] += 1;
            s.authenticated_words += usize::from(auth);
            s.primary_pointer_targets_covered += usize::from(covered);
            if cache != 0 || self.out.primary_base == 0 {
                self.issue(IssueCode::MissingCacheBase, image_index, Some(index), None)?;
            } else if resolved.is_none() {
                self.issue(
                    IssueCode::PointerTargetOverflow,
                    image_index,
                    Some(index),
                    None,
                )?;
            } else if !covered {
                self.issue(
                    IssueCode::PointerTargetOutsideMappings,
                    image_index,
                    Some(index),
                    None,
                )?;
            }
            if auth {
                self.issue(
                    IssueCode::UnsupportedAuthentication,
                    image_index,
                    Some(index),
                    None,
                )?;
            }
            if next == 0 {
                self.out.summary.chains_terminated += 1;
                break;
            }
            // Byte stride is positive, never scaled by four/eight or wrapped.
            in_page = add(in_page, u64::from(next))?;
        }
        Ok(())
    }
    fn image(&mut self, index: usize, image: &ImageMetadata) -> Result<()> {
        let maps = mappings(&image.segments)?;
        let base = if image.file_type == 11 {
            image.segments.first().map(|s| s.address)
        } else {
            image
                .segments
                .iter()
                .find(|s| s.initial_protection & 2 != 0)
                .map(|s| s.address)
        };
        if let Some(reloc) = &image.relocations {
            self.classic(
                index,
                None,
                &maps,
                ClassicTable::LocalDynamic,
                &reloc.local,
                base,
            )?;
            self.classic(
                index,
                None,
                &maps,
                ClassicTable::ExternalDynamic,
                &reloc.external,
                base,
            )?;
        }
        for segment in &image.segments {
            for section in &segment.sections {
                self.classic(
                    index,
                    Some(section.size),
                    &maps,
                    ClassicTable::Section,
                    &section.relocations,
                    Some(section.address),
                )?;
            }
        }
        let Some(fixups) = &image.chained_fixups else {
            return Ok(());
        };
        if fixups.imports_count != 0 {
            self.issue(IssueCode::UnsupportedImports, index, None, None)?;
        }
        if fixups.symbols_format != 0 {
            self.issue(IssueCode::UnsupportedCompressedSymbols, index, None, None)?;
        }
        let starts = add(
            fixups.file.offset,
            u64::from(u32_at(self.source, fixups.file.offset + 4)?),
        )?;
        for seg_info in &fixups.segments {
            if seg_info.pointer_format != 11 {
                self.issue(IssueCode::UnsupportedPointerFormat, index, None, None)?;
                continue;
            }
            let segment = &image.segments[seg_info.segment_index];
            // The immutable inspector has checked modulo correspondence. Use
            // the validated absolute segment VA for every chain location.
            if seg_info.segment_offset != segment.address.wrapping_sub(image.header_address) {
                return Err(AuditError::InvalidMetadata);
            }
            let offset = u32_at(
                self.source,
                add(starts, 4 + seg_info.segment_index as u64 * 4)?,
            )?;
            let info = add(starts, u64::from(offset))?;
            let info_end = add(info, u64::from(u32_at(self.source, info)?))?;
            for page in 0..usize::from(seg_info.page_count) {
                self.page_start()?;
                let first = u16_at(self.source, add(info, 22 + page as u64 * 2)?)?;
                if first == 0xffff {
                    continue;
                }
                if first & 0x8000 == 0 {
                    self.chain(
                        index,
                        seg_info.segment_index,
                        page,
                        segment,
                        seg_info.page_size,
                        first,
                    )?;
                    continue;
                }
                self.out.summary.multi_start_pages += 1;
                self.issue(IssueCode::UnsupportedMultiStartConsumer, index, None, None)?;
                let mut at = add(info, 22 + u64::from(first & 0x7fff) * 2)?;
                loop {
                    self.page_start()?;
                    if add(at, 2)? > info_end {
                        return Err(AuditError::InvalidMetadata);
                    }
                    let start = u16_at(self.source, at)?;
                    self.chain(
                        index,
                        seg_info.segment_index,
                        page,
                        segment,
                        seg_info.page_size,
                        start & 0x7fff,
                    )?;
                    if start & 0x8000 != 0 {
                        break;
                    }
                    at = add(at, 2)?;
                }
            }
        }
        Ok(())
    }
    fn overlaps(&mut self) -> Result<()> {
        let mut ordered = Vec::new();
        ordered
            .try_reserve_exact(self.out.records.len())
            .map_err(|_| AuditError::AllocationFailed)?;
        for (index, r) in self.out.records.iter().enumerate() {
            if r.write_file_offset.is_some() {
                ordered.push(index);
            }
        }
        ordered.sort_unstable_by_key(|&i| (self.out.records[i].write_address.unwrap(), i));
        let mut furthest: [Option<(u64, usize)>; 2] = [None, None];
        let mut last_chain: Option<(u64, usize)> = None;
        for index in ordered {
            let r = &self.out.records[index];
            let address = r.write_address.unwrap();
            let end = add(address, u64::from(r.width))?;
            let image = r.image_index;
            let mechanism = usize::from(matches!(r.detail, RecordDetail::Chain11 { .. }));
            if mechanism == 1 {
                if let Some((prior, other)) = last_chain {
                    if prior == address {
                        self.issue(
                            IssueCode::DuplicateChainVisit,
                            image,
                            Some(index),
                            Some(other),
                        )?;
                    }
                }
                last_chain = Some((address, index));
            }
            for (kind, prior) in furthest.iter().enumerate() {
                if let Some((prior_end, other)) = *prior {
                    if prior_end > address {
                        self.issue(
                            if kind == mechanism {
                                IssueCode::SameMechanismWriteOverlap
                            } else {
                                IssueCode::CrossMechanismWriteOverlap
                            },
                            image,
                            Some(index),
                            Some(other),
                        )?;
                    }
                }
            }
            if furthest[mechanism].is_none_or(|(prior_end, _)| end > prior_end) {
                furthest[mechanism] = Some((end, index));
            }
        }
        // Counts are conflicting-record events with one earlier witness per
        // mechanism, not a potentially quadratic count of every overlap pair.
        for issue in &self.out.issues {
            if let Some(count) = self
                .out
                .summary
                .issue_counts
                .iter_mut()
                .find(|c| c.code == issue.code)
            {
                count.count += 1;
            } else {
                self.out.summary.issue_counts.push(IssueCount {
                    code: issue.code,
                    count: 1,
                });
            }
        }
        Ok(())
    }
}
fn member_ranges(inspection: &KcMetadataInspection, file_type: u32) -> Result<Vec<(u64, u64)>> {
    let mut ranges = Vec::new();
    for member in inspection
        .members
        .iter()
        .filter(|m| m.image.file_type == file_type)
    {
        for s in member.image.segments.iter().filter(|s| s.memory_size != 0) {
            push_bounded(
                &mut ranges,
                (s.address, add(s.address, s.memory_size)?),
                4096,
            )?;
        }
    }
    ranges.sort_unstable();
    let mut merged: Vec<(u64, u64)> = Vec::new();
    merged
        .try_reserve_exact(ranges.len())
        .map_err(|_| AuditError::AllocationFailed)?;
    for (start, end) in ranges {
        if let Some(last) = merged.last_mut() {
            if start <= last.1 {
                last.1 = last.1.max(end);
                continue;
            }
        }
        merged.push((start, end));
    }
    Ok(merged)
}

/// Audit a single primary KC in its linked (unslid) address space. No source
/// write or arena allocation occurs. Missing external caches remain issues.
pub fn audit_kernel_collection(source: &[u8]) -> Result<KcFixupAudit> {
    audit_kernel_collection_with_limits(source, AuditLimits::default())
}
/// Limits may only tighten the public maxima. A resource error never returns a
/// partial-success audit, and all temporary/record allocations are dropped.
pub fn audit_kernel_collection_with_limits(
    source: &[u8],
    limits: AuditLimits,
) -> Result<KcFixupAudit> {
    if limits.records == 0
        || limits.records > MAX_AUDIT_RECORDS
        || limits.issues == 0
        || limits.issues > MAX_AUDIT_ISSUES
        || limits.page_starts == 0
        || limits.page_starts > MAX_AUDIT_PAGE_STARTS
    {
        return Err(AuditError::InvalidLimits);
    }
    let inspection = inspect_kernel_collection(source)?;
    let primary_base = inspection
        .collection
        .segments
        .iter()
        .map(|s| s.address)
        .min()
        .ok_or(AuditError::InvalidMetadata)?;
    let mut audit = Audit {
        source,
        limits,
        outer: mappings(&inspection.collection.segments)?,
        executable: member_ranges(&inspection, 2)?,
        kext: member_ranges(&inspection, 11)?,
        out: KcFixupAudit {
            summary: AuditSummary::default(),
            records: Vec::new(),
            issues: Vec::new(),
            primary_base,
        },
    };
    audit.image(0, &inspection.collection)?;
    for (index, member) in inspection.members.iter().enumerate() {
        audit.image(index + 1, &member.image)?;
    }
    audit.overlaps()?;
    Ok(audit.out)
}
