//! Authored format-only inputs; no operating-system bytes are included.
use nextcore_core::kernel_collection::{
    inspect_kernel_collection, EntryMetadata, KcMetadataError as E, PreparationRequirement as R,
};

const VA: u64 = 0x1000_0000;
const CHILD: usize = 4096;
const DRIVER: usize = 8192;
const LINK: usize = 12288;
const FIX: usize = LINK + 32;
const FIX_SIZE: usize = 80;

fn put32(b: &mut [u8], at: usize, n: u32) {
    b[at..at + 4].copy_from_slice(&n.to_le_bytes());
}
fn put64(b: &mut [u8], at: usize, n: u64) {
    b[at..at + 8].copy_from_slice(&n.to_le_bytes());
}
fn put16(b: &mut [u8], at: usize, n: u16) {
    b[at..at + 2].copy_from_slice(&n.to_le_bytes());
}
fn get32(b: &[u8], at: usize) -> u32 {
    u32::from_le_bytes(b[at..at + 4].try_into().unwrap())
}

fn command(kind: u32, size: usize) -> Vec<u8> {
    let mut b = vec![0; size];
    put32(&mut b, 0, kind);
    put32(&mut b, 4, size as u32);
    b
}
fn segment(name: &str, offset: usize, bytes: usize, protection: u32) -> Vec<u8> {
    let mut b = command(0x19, 72);
    b[8..8 + name.len()].copy_from_slice(name.as_bytes());
    put64(&mut b, 24, VA + offset as u64);
    put64(&mut b, 32, bytes as u64);
    put64(&mut b, 40, offset as u64);
    put64(&mut b, 48, bytes as u64);
    put32(&mut b, 56, protection);
    put32(&mut b, 60, protection);
    b
}
fn thread(rip: u64) -> Vec<u8> {
    let mut b = command(5, 184);
    put32(&mut b, 8, 4);
    put32(&mut b, 12, 42);
    put64(&mut b, 144, rip);
    b
}
fn member(id: &str, offset: usize) -> Vec<u8> {
    let size = (32 + id.len() + 1).div_ceil(8) * 8;
    let mut b = command(0x8000_0035, size);
    put64(&mut b, 8, VA + offset as u64);
    put64(&mut b, 16, offset as u64);
    put32(&mut b, 24, 32);
    b[32..32 + id.len()].copy_from_slice(id.as_bytes());
    b
}
fn write_image(b: &mut [u8], base: usize, filetype: u32, commands: Vec<Vec<u8>>) {
    put32(b, base, 0xfeed_facf);
    put32(b, base + 4, 0x0100_0007);
    put32(b, base + 8, 3);
    put32(b, base + 12, filetype);
    put32(b, base + 16, commands.len() as u32);
    put32(
        b,
        base + 20,
        commands.iter().map(Vec::len).sum::<usize>() as u32,
    );
    let mut at = base + 32;
    for cmd in commands {
        b[at..at + cmd.len()].copy_from_slice(&cmd);
        at += cmd.len();
    }
}
fn fixture() -> Vec<u8> {
    let mut b = vec![0; 16384];
    let mut dysym = command(0xb, 80);
    put32(&mut dysym, 72, LINK as u32);
    put32(&mut dysym, 76, 2);
    let mut fix = command(0x8000_0034, 16);
    put32(&mut fix, 8, FIX as u32);
    put32(&mut fix, 12, FIX_SIZE as u32);
    write_image(
        &mut b,
        0,
        12,
        vec![
            segment("__TEXT", 0, 4096, 1),
            segment("__CODE", CHILD, 4096, 5),
            segment("__DATA", DRIVER, 4096, 3),
            segment("__LINKEDIT", LINK, 4096, 1),
            segment("__EMPTY", 16384, 0, 1),
            thread(VA + CHILD as u64 + 2048),
            member("fixture.kernel", CHILD),
            member("fixture.driver", DRIVER),
            command(2, 24),
            dysym,
            fix,
        ],
    );
    write_image(
        &mut b,
        CHILD,
        2,
        vec![
            segment("__TEXT", CHILD, 4096, 5),
            segment("__DATA", DRIVER, 4096, 3),
            segment("__LINKEDIT", LINK, 4096, 1),
            thread(0x5555_0000),
        ],
    );
    write_image(
        &mut b,
        DRIVER,
        11,
        vec![
            segment("__TEXT", DRIVER, 4096, 3),
            segment("__LINKEDIT", LINK, 4096, 1),
        ],
    );
    // Two bounded classic relocation records, not applied by the inspector.
    put32(&mut b, LINK + 4, 3 << 25);
    put32(&mut b, LINK + 12, 3 << 25);
    // Header, five segment offsets, one page-start record, trailing padding.
    put32(&mut b, FIX + 4, 28);
    put32(&mut b, FIX + 8, FIX_SIZE as u32);
    put32(&mut b, FIX + 12, FIX_SIZE as u32);
    put32(&mut b, FIX + 20, 1);
    put32(&mut b, FIX + 28, 5);
    put32(&mut b, FIX + 40, 24);
    put32(&mut b, FIX + 52, 24);
    put16(&mut b, FIX + 56, 4096);
    put16(&mut b, FIX + 58, 11);
    put64(&mut b, FIX + 60, DRIVER as u64);
    put16(&mut b, FIX + 72, 1);
    put16(&mut b, FIX + 74, 16);
    b
}
fn fixture_with_sections(overlapping: bool) -> Vec<u8> {
    let mut b = fixture();
    let mut text = segment("__TEXT", CHILD, 4096, 5);
    let count = if overlapping { 2 } else { 1 };
    text.resize(72 + count * 80, 0);
    let size = text.len() as u32;
    put32(&mut text, 4, size);
    put32(&mut text, 64, count as u32);
    for index in 0..count {
        let at = 72 + index * 80;
        text[at..at + 7].copy_from_slice(b"fixture");
        text[at + 16..at + 22].copy_from_slice(b"__TEXT");
        // Both records intentionally share the same view in the overlap case.
        put64(&mut text, at + 32, VA + CHILD as u64 + 1024);
        put64(&mut text, at + 40, 64);
        put32(&mut text, at + 48, CHILD as u32 + 1024);
        put32(&mut text, at + 52, 4);
        put32(&mut text, at + 56, LINK as u32);
        put32(&mut text, at + 60, 1);
    }
    write_image(
        &mut b,
        CHILD,
        2,
        vec![
            text,
            segment("__DATA", DRIVER, 4096, 3),
            segment("__LINKEDIT", LINK, 4096, 1),
            thread(0x5555_0000),
        ],
    );
    b
}
fn locate(b: &[u8], base: usize, kind: u32, occurrence: usize) -> usize {
    let mut at = base + 32;
    let mut found = 0;
    for _ in 0..get32(b, base + 16) {
        if get32(b, at) == kind {
            if found == occurrence {
                return at;
            }
            found += 1;
        }
        at += get32(b, at + 4) as usize;
    }
    panic!("authored command missing");
}
fn reject(b: &[u8], expected: E) {
    assert_eq!(inspect_kernel_collection(b).unwrap_err(), expected);
}

#[test]
fn collection_and_member_entries_remain_distinct_and_never_ready() {
    let b = fixture();
    let before = b.clone();
    let result = inspect_kernel_collection(&b).unwrap();
    assert!(!result.preparation_ready());
    assert_eq!(b, before);
    assert_eq!(result.members.len(), 2);
    assert_eq!(result.collection.segments.len(), 5);
    assert_eq!(
        result.collection.entry,
        Some(EntryMetadata::UnixThread64 {
            instruction_pointer: VA + 6144
        })
    );
    assert_eq!(
        result.members[0].image.entry,
        Some(EntryMetadata::UnixThread64 {
            instruction_pointer: 0x5555_0000
        })
    );
    assert_eq!(
        result.collection.relocations.as_ref().unwrap().local_count,
        2
    );
    for requirement in [
        R::CollectionPlacement,
        R::KernelEntryAbi,
        R::PlatformHandoffProviders,
        R::ClassicRelocations,
        R::ChainedRebasing,
    ] {
        assert!(result.requirements.contains(&requirement));
    }
    assert_eq!(
        result.collection.chained_fixups.unwrap().segments[0].pages_with_fixups,
        1
    );
}

#[test]
fn zero_segments_and_member_shared_linkedit_are_valid_views() {
    let result = inspect_kernel_collection(&fixture()).unwrap();
    assert_eq!(result.collection.segments[4].memory_size, 0);
    let first = result.members[0].image.segments.last().unwrap();
    let second = result.members[1].image.segments.last().unwrap();
    assert_eq!(first.file, second.file);
}

#[test]
fn truncation_and_command_size_mutations_fail() {
    let good = fixture();
    for size in [0, 4, 31, 32, CHILD, FIX, good.len() - 1] {
        assert!(inspect_kernel_collection(&good[..size]).is_err());
    }
    for size in [0, 7, 9, u32::MAX - 7] {
        let mut b = good.clone();
        put32(&mut b, 36, size);
        assert!(inspect_kernel_collection(&b).is_err());
    }
    let mut b = good.clone();
    put32(&mut b, 16, 20_000);
    put32(&mut b, 20, 160_000);
    reject(&b, E::LimitExceeded);
    let mut b = good;
    put32(&mut b, 32, 0x7999);
    reject(&b, E::UnsupportedCommand);
}

#[test]
fn unsupported_headers_and_recursive_filesets_fail() {
    for (base, offset, value, error) in [
        (0, 0, 0xcffa_edfe, E::UnsupportedFormat),
        (0, 4, 0x0100_000c, E::UnsupportedCpu),
        (0, 12, 2, E::UnsupportedFileType),
        (0, 28, 1, E::InvalidHeader),
        (CHILD, 12, 12, E::UnsupportedFileType),
    ] {
        let mut b = fixture();
        put32(&mut b, base + offset, value);
        reject(&b, error);
    }
}

#[test]
fn member_identifiers_and_references_are_checked() {
    let good = fixture();
    let first = locate(&good, 0, 0x8000_0035, 0);
    let second = locate(&good, 0, 0x8000_0035, 1);
    for invalid in [0, 31, 48, u32::MAX] {
        let mut b = good.clone();
        put32(&mut b, first + 24, invalid);
        reject(&b, E::InvalidIdentifier);
    }
    let mut b = good.clone();
    b[first + 32..first + 48].fill(b'x');
    reject(&b, E::InvalidIdentifier);
    let mut b = good.clone();
    put64(&mut b, second + 16, CHILD as u64);
    reject(&b, E::DuplicateMember);
    let mut b = good.clone();
    put64(&mut b, first + 8, VA + CHILD as u64 + 1);
    reject(&b, E::InvalidMemberMapping);
    let mut b = good;
    put64(&mut b, first + 16, u64::MAX);
    reject(&b, E::Overflow);
}

#[test]
fn segment_overflow_overlap_protection_and_member_tail_fail() {
    let good = fixture();
    let seg = locate(&good, 0, 0x19, 1);
    let mut b = good.clone();
    put64(&mut b, seg + 24, u64::MAX - 2047);
    reject(&b, E::Overflow);
    let mut b = good.clone();
    put64(&mut b, seg + 24, VA + 2048);
    reject(&b, E::OverlappingRange);
    let mut b = good.clone();
    put32(&mut b, seg + 60, 7);
    reject(&b, E::InvalidSegment);
    let mut b = good.clone();
    put64(&mut b, seg + 48, 4097);
    reject(&b, E::InvalidSegment);
    let mut b = good.clone();
    put32(&mut b, seg + 68, 1);
    reject(&b, E::UnsupportedSegmentFlags);
    let member_segment = locate(&good, DRIVER, 0x19, 1);
    let mut b = good;
    put64(&mut b, member_segment + 32, 8192);
    reject(&b, E::InvalidMemberMapping);
}

#[test]
fn collection_entry_requires_file_backed_execute_mapping() {
    let good = fixture();
    let at = locate(&good, 0, 5, 0);
    let mut b = good.clone();
    put64(&mut b, at + 144, VA + DRIVER as u64);
    reject(&b, E::InvalidEntry);
    let mut b = good.clone();
    put32(&mut b, at + 8, 1);
    reject(&b, E::UnsupportedThreadState);
    let mut b = good.clone();
    put32(&mut b, at, 0x24);
    reject(&b, E::InvalidCommand);
    let mut b = good;
    let file_size = get32(&b, 20) as usize;
    b[32 + file_size..32 + file_size + 184].copy_from_slice(&thread(VA + 6144));
    let count = get32(&b, 16);
    put32(&mut b, 16, count + 1);
    put32(&mut b, 20, (file_size + 184) as u32);
    reject(&b, E::DuplicateEntry);
}

#[test]
fn main_entry_is_member_provenance_and_not_a_collection_entry() {
    let mut b = fixture();
    let at = locate(&b, 0, 5, 0);
    let old_size = get32(&b, 20) as usize;
    let count = get32(&b, 16);
    // Remove LC_UNIXTHREAD while retaining all subsequent commands.
    b.copy_within(at + 184..32 + old_size, at);
    put32(&mut b, 16, count - 1);
    put32(&mut b, 20, (old_size - 184) as u32);
    reject(&b, E::MissingEntry);
    let mut main = command(0x8000_0028, 24);
    put64(&mut main, 8, CHILD as u64 + 2048);
    let append_at = 32 + old_size - 184;
    b[append_at..append_at + 24].copy_from_slice(&main);
    put32(&mut b, 16, count);
    put32(&mut b, 20, (old_size - 184 + 24) as u32);
    reject(&b, E::UnsupportedCollectionEntry);
    let mut b = fixture();
    write_image(
        &mut b,
        CHILD,
        2,
        vec![
            segment("__TEXT", CHILD, 4096, 5),
            segment("__DATA", DRIVER, 4096, 3),
            segment("__LINKEDIT", LINK, 4096, 1),
            main,
        ],
    );
    let result = inspect_kernel_collection(&b).unwrap();
    assert_eq!(
        result.members[0].image.entry,
        Some(EntryMetadata::Main {
            text_offset: CHILD as u64 + 2048,
            stack_size: 0
        })
    );
    assert!(!result.preparation_ready());
}

#[test]
fn section_layout_relocations_and_aggregate_budget_are_checked() {
    let good = fixture_with_sections(false);
    let result = inspect_kernel_collection(&good).unwrap();
    let sections = &result.members[0].image.segments[0].sections;
    assert_eq!(sections.len(), 1);
    assert_eq!(sections[0].relocations.size, 8);
    let at = CHILD + 32 + 72;
    let mut b = good.clone();
    put64(&mut b, at + 32, u64::MAX - 15);
    reject(&b, E::Overflow);
    let mut b = good.clone();
    put32(&mut b, at + 48, CHILD as u32 + 1025);
    reject(&b, E::InvalidSection);
    let mut b = good.clone();
    put32(&mut b, at + 52, 64);
    reject(&b, E::InvalidSection);
    let mut b = good.clone();
    b[at + 16] = b'x';
    reject(&b, E::InvalidSection);
    let mut b = good.clone();
    put32(&mut b, at + 56, CHILD as u32);
    reject(&b, E::InvalidLinkedit);
    let mut b = good.clone();
    put32(&mut b, at + 60, u32::MAX);
    reject(&b, E::Truncated);
    let mut b = good;
    put32(&mut b, CHILD + 32 + 64, 40_000);
    reject(&b, E::LimitExceeded);
    reject(&fixture_with_sections(true), E::OverlappingRange);
}

#[test]
fn relocation_and_linkedit_ranges_are_bounded() {
    let good = fixture();
    let at = locate(&good, 0, 0xb, 0);
    let mut b = good.clone();
    put32(&mut b, at + 76, u32::MAX);
    reject(&b, E::Truncated);
    let mut b = good.clone();
    put32(&mut b, at + 72, CHILD as u32);
    reject(&b, E::InvalidLinkedit);
    let mut b = good;
    put32(&mut b, at + 12, 1);
    reject(&b, E::InvalidLinkedit);
}

#[test]
fn fixup_headers_segments_and_pages_are_strictly_bounded() {
    for (offset, value, error) in [
        (0, 1, E::UnsupportedFixupVersion),
        (4, 0, E::InvalidFixups),
        (8, u32::MAX, E::Truncated),
        (12, u32::MAX, E::InvalidFixups),
        (28, 6, E::InvalidFixups),
        (40, 4, E::InvalidFixups),
        (52, 22, E::InvalidFixups),
    ] {
        let mut b = fixture();
        put32(&mut b, FIX + offset, value);
        reject(&b, error);
    }
    let mut b = fixture();
    put16(&mut b, FIX + 56, 8192);
    reject(&b, E::InvalidFixups);
    let mut b = fixture();
    put64(&mut b, FIX + 60, 0);
    reject(&b, E::InvalidFixups);
    let mut b = fixture();
    put16(&mut b, FIX + 72, 2);
    reject(&b, E::InvalidFixups);
    let mut b = fixture();
    put16(&mut b, FIX + 74, 4090);
    reject(&b, E::InvalidFixups);
}

#[test]
fn multiple_page_starts_need_a_bounded_terminator() {
    let mut b = fixture();
    put32(&mut b, FIX + 52, 28);
    put16(&mut b, FIX + 74, 0x8001);
    put16(&mut b, FIX + 76, 16);
    put16(&mut b, FIX + 78, 0x8020);
    let result = inspect_kernel_collection(&b).unwrap();
    assert_eq!(
        result.collection.chained_fixups.unwrap().segments[0].multiple_start_pages,
        1
    );
    put16(&mut b, FIX + 78, 32);
    reject(&b, E::InvalidFixups);
    put16(&mut b, FIX + 74, 0x8000);
    reject(&b, E::InvalidFixups);
}

#[test]
fn fixup_starts_cannot_reference_unbacked_bytes_or_other_tables() {
    let mut b = fixture();
    let data = locate(&b, 0, 0x19, 2);
    // The virtual page exists, but the pointer at byte 16 is not wholly backed.
    put64(&mut b, data + 48, 20);
    reject(&b, E::InvalidFixups);
    let mut b = fixture();
    put32(&mut b, FIX + 12, 52);
    reject(&b, E::InvalidFixups);
    let mut b = fixture();
    put32(&mut b, FIX + 8, 56);
    put32(&mut b, FIX + 16, 1);
    reject(&b, E::InvalidFixups);
}

#[test]
fn page_starts_allow_a_file_backed_straddling_word_but_not_a_start_on_next_page() {
    let mut b = fixture();
    b.resize(20480, 0);
    b.copy_within(LINK..LINK + 4096, LINK + 4096);
    b[LINK..LINK + 4096].fill(0);
    for (base, occurrence) in [(0, 3), (CHILD, 2), (DRIVER, 1)] {
        let link = locate(&b, base, 0x19, occurrence);
        put64(&mut b, link + 24, VA + 16384);
        put64(&mut b, link + 40, 16384);
    }
    let data = locate(&b, 0, 0x19, 2);
    put64(&mut b, data + 32, 8192);
    put64(&mut b, data + 48, 8192);
    let reloc = locate(&b, 0, 0xb, 0);
    put32(&mut b, reloc + 72, 16384);
    let fix = locate(&b, 0, 0x8000_0034, 0);
    put32(&mut b, fix + 8, (FIX + 4096) as u32);
    put16(&mut b, FIX + 4096 + 74, 4092);
    let before = b.clone();
    assert!(inspect_kernel_collection(&b).is_ok());
    assert_eq!(b, before);
    put16(&mut b, FIX + 4096 + 74, 4096);
    reject(&b, E::InvalidFixups);
    put16(&mut b, FIX + 4096 + 74, 4092);
    put64(&mut b, data + 48, 4099);
    reject(&b, E::InvalidFixups);
    put64(&mut b, data + 48, 8192);
    // The same start/full-word split applies to overflow-list entries.
    put32(&mut b, FIX + 4096 + 52, 26);
    put16(&mut b, FIX + 4096 + 74, 0x8001);
    put16(&mut b, FIX + 4096 + 76, 0x8ffc);
    assert!(inspect_kernel_collection(&b).is_ok());
    put16(&mut b, FIX + 4096 + 76, 0x9000);
    reject(&b, E::InvalidFixups);
    put16(&mut b, FIX + 4096 + 76, 0x8ffc);
    put64(&mut b, data + 48, 4099);
    reject(&b, E::InvalidFixups);
}

#[test]
fn imports_and_compressed_symbols_remain_explicit_requirements() {
    let mut b = fixture();
    let at = locate(&b, 0, 0x8000_0034, 0);
    put32(&mut b, at + 12, 88);
    put32(&mut b, FIX + 12, 84);
    put32(&mut b, FIX + 16, 1);
    put32(&mut b, FIX + 24, 1);
    let result = inspect_kernel_collection(&b).unwrap();
    assert!(result.requirements.contains(&R::ChainedImports));
    assert!(result.requirements.contains(&R::CompressedFixupSymbols));
    assert!(!result.preparation_ready());
}

#[test]
fn unknown_pointer_format_is_a_preparation_blocker() {
    let mut b = fixture();
    put16(&mut b, FIX + 58, 0x1234);
    let result = inspect_kernel_collection(&b).unwrap();
    assert!(!result.preparation_ready());
    assert!(result
        .requirements
        .contains(&R::UnsupportedPointerFormat(0x1234)));
}

#[test]
fn segment_before_header_uses_only_metadata_modulo_displacement() {
    let mut b = fixture();
    let data = locate(&b, 0, 0x19, 2);
    put64(&mut b, data + 24, VA - 4096);
    let child_data = locate(&b, CHILD, 0x19, 1);
    put64(&mut b, child_data + 24, VA - 4096);
    let driver_text = locate(&b, DRIVER, 0x19, 0);
    put64(&mut b, driver_text + 24, VA - 4096);
    let driver_ref = locate(&b, 0, 0x8000_0035, 1);
    put64(&mut b, driver_ref + 8, VA - 4096);
    put64(&mut b, FIX + 60, u64::MAX - 4095);
    assert!(!inspect_kernel_collection(&b).unwrap().preparation_ready());
}
