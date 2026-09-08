//! Entirely authored Mach-O layout and sentinel bytes, independent of any OS.
use nextcore_core::{
    kc_staging::{KcStagingError as E, KcStagingPlan, MAX_STAGING_SIZE},
    kernel_collection::{EntryMetadata, KcMetadataError, PreparationRequirement},
};

const BASE: u64 = 0x2000_0000;
const HEADER: usize = 32;
const DATA: usize = HEADER + 72;
const LINK: usize = DATA + 72;
const CODE: usize = LINK + 72;
const EMPTY: usize = CODE + 72;
const THREAD: usize = EMPTY + 72;

fn put32(b: &mut [u8], at: usize, value: u32) {
    b[at..at + 4].copy_from_slice(&value.to_le_bytes());
}
fn put64(b: &mut [u8], at: usize, value: u64) {
    b[at..at + 8].copy_from_slice(&value.to_le_bytes());
}
fn command(kind: u32, size: usize) -> Vec<u8> {
    let mut b = vec![0; size];
    put32(&mut b, 0, kind);
    put32(&mut b, 4, size as u32);
    b
}
fn segment(name: &str, va: u64, size: u64, file: u64, file_size: u64, prot: u32) -> Vec<u8> {
    let mut b = command(0x19, 72);
    b[8..8 + name.len()].copy_from_slice(name.as_bytes());
    put64(&mut b, 24, va);
    put64(&mut b, 32, size);
    put64(&mut b, 40, file);
    put64(&mut b, 48, file_size);
    put32(&mut b, 56, prot);
    put32(&mut b, 60, prot);
    b
}
fn thread(entry: u64) -> Vec<u8> {
    let mut b = command(5, 184);
    put32(&mut b, 8, 4);
    put32(&mut b, 12, 42);
    put64(&mut b, 144, entry);
    b
}
fn member(id: &str, file: u64, va: u64) -> Vec<u8> {
    let mut b = command(0x8000_0035, (33 + id.len()).div_ceil(8) * 8);
    put64(&mut b, 8, va);
    put64(&mut b, 16, file);
    put32(&mut b, 24, 32);
    b[32..32 + id.len()].copy_from_slice(id.as_bytes());
    b
}
fn image(b: &mut [u8], at: usize, file_type: u32, commands: &[Vec<u8>]) {
    b[at..at + 32].fill(0);
    put32(b, at, 0xfeed_facf);
    put32(b, at + 4, 0x0100_0007);
    put32(b, at + 8, 3);
    put32(b, at + 12, file_type);
    put32(b, at + 16, commands.len() as u32);
    put32(
        b,
        at + 20,
        commands.iter().map(Vec::len).sum::<usize>() as u32,
    );
    let mut current = at + 32;
    for command in commands {
        b[current..current + command.len()].copy_from_slice(command);
        current += command.len();
    }
}
fn fixture() -> Vec<u8> {
    let mut b: Vec<u8> = (0..0x4000).map(|i| ((i * 13 + 71) % 251) as u8).collect();
    image(
        &mut b,
        0,
        12,
        &[
            segment("__TEXT", BASE + 0x2000, 0x1000, 0, 0x1000, 1),
            segment("__DATA", BASE + 0x4000, 0x1800, 0x1000, 0x1000, 3),
            segment("__LINKEDIT", BASE + 0x7000, 0x500, 0x2000, 0x200, 1),
            // Deliberately unaligned and before the collection's header VA.
            segment("__CODE", BASE + 0x23, 0x201, 0x3000, 0x101, 5),
            segment("__EMPTY", BASE + 0x6000, 0, 0, 0, 1),
            thread(BASE + 0x37),
            member("authored.kernel", 0x1000, BASE + 0x4000),
            member("authored.driver", 0x1600, BASE + 0x4600),
        ],
    );
    image(
        &mut b,
        0x1000,
        2,
        &[
            // This view's tail contains the other member's header and data.
            segment("__TEXT", BASE + 0x4000, 0x1000, 0x1000, 0x400, 3),
            segment("__LINKEDIT", BASE + 0x7000, 0x200, 0x2000, 0x100, 1),
            thread(BASE + 0x4001),
        ],
    );
    image(
        &mut b,
        0x1600,
        11,
        &[
            segment("__TEXT", BASE + 0x4600, 0x800, 0x1600, 0x200, 3),
            segment("__LINKEDIT", BASE + 0x7000, 0x200, 0x2000, 0x100, 1),
        ],
    );
    b
}

#[test]
fn actual_copy_zero_holes_and_shared_views_match_independent_layout() {
    let source = fixture();
    let before = source.clone();
    let staged = KcStagingPlan::new(&source).unwrap().stage().unwrap();
    let bytes = staged.bytes();
    assert_eq!(bytes.len(), 0x8000);
    let mut expected = vec![0; 0x8000];
    expected[0x2000..0x3000].copy_from_slice(&source[..0x1000]);
    expected[0x4000..0x5000].copy_from_slice(&source[0x1000..0x2000]);
    expected[0x7000..0x7200].copy_from_slice(&source[0x2000..0x2200]);
    expected[0x23..0x124].copy_from_slice(&source[0x3000..0x3101]);
    assert_eq!(bytes, expected);
    // Member-one tail must not erase member-two header and sentinel payload.
    assert_eq!(&bytes[0x4600..0x4800], &source[0x1600..0x1800]);
    assert_eq!(&bytes[0x7100..0x7200], &source[0x2100..0x2200]);
    let verified = staged.verification();
    assert_eq!(verified.copied_bytes, 8961);
    assert_eq!(verified.zero_tail_bytes, 3072);
    assert_eq!(verified.hole_bytes, 20735);
    assert_eq!(
        verified.arena_bytes,
        verified.copied_bytes + verified.zero_tail_bytes + verified.hole_bytes
    );
    assert_eq!(verified.member_headers_checked, 2);
    assert_eq!(verified.member_segment_views_checked, 4);
    assert_eq!(source, before);
}

#[test]
fn header_minimum_entry_and_original_segment_indices_stay_distinct() {
    let source = fixture();
    let plan = KcStagingPlan::new(&source).unwrap();
    assert_eq!(plan.minimum_virtual_address(), BASE);
    assert_eq!(plan.inspection().collection.header_address, BASE + 0x2000);
    assert_eq!(plan.collection_header_offset(), 0x2000);
    assert_eq!(plan.outer_entry_offset(), 0x37);
    assert_eq!(
        plan.segments()
            .iter()
            .map(|s| s.collection_segment_index)
            .collect::<Vec<_>>(),
        vec![3, 0, 1, 2]
    );
    assert_eq!(
        plan.inspection().members[0].image.entry,
        Some(EntryMetadata::UnixThread64 {
            instruction_pointer: BASE + 0x4001
        })
    );
    assert!(!plan.preparation_ready());
    assert!(plan
        .inspection()
        .requirements
        .contains(&PreparationRequirement::CollectionPlacement));
    assert!(!plan.stage().unwrap().preparation_ready());
}

#[test]
fn supplied_buffer_size_rejection_leaves_every_byte_unchanged() {
    let source = fixture();
    let plan = KcStagingPlan::new(&source).unwrap();
    for size in [0, plan.arena_size() - 1, plan.arena_size() + 1] {
        let mut destination = vec![0xac; size];
        let original = destination.clone();
        assert_eq!(plan.stage_into(&mut destination), Err(E::DestinationSize));
        assert_eq!(destination, original);
        assert_eq!(plan.verify(&destination), Err(E::DestinationSize));
    }
}

#[test]
fn readback_detects_payload_zero_tail_hole_page_tail_and_member_corruption() {
    let source = fixture();
    let plan = KcStagingPlan::new(&source).unwrap();
    let mut destination = vec![0xde; plan.arena_size()];
    for offset in [
        0x23, 0x123, 0x124, 0x224, 0x4600, 0x5100, 0x7103, 0x7300, 0x7fff,
    ] {
        plan.stage_into(&mut destination).unwrap();
        destination[offset] ^= 0x80;
        assert_eq!(
            plan.verify(&destination),
            Err(E::ReadbackMismatch),
            "offset {offset:#x}"
        );
    }
}

#[test]
fn sparse_virtual_span_is_bounded_independently_of_file_size() {
    let mut source = fixture();
    let high = BASE + MAX_STAGING_SIZE as u64 + 0x10000;
    put64(&mut source, CODE + 24, high);
    put64(&mut source, THREAD + 144, high + 20);
    assert_eq!(KcStagingPlan::new(&source).unwrap_err(), E::ArenaTooLarge);
}

#[test]
fn exact_span_cap_is_accepted_without_allocating_arena_and_next_byte_rejected() {
    let mut source = fixture();
    put64(&mut source, LINK + 32, MAX_STAGING_SIZE as u64 - 0x7000);
    assert_eq!(
        KcStagingPlan::new(&source).unwrap().arena_size(),
        MAX_STAGING_SIZE
    );
    put64(&mut source, LINK + 32, MAX_STAGING_SIZE as u64 - 0x7000 + 1);
    assert_eq!(KcStagingPlan::new(&source).unwrap_err(), E::ArenaTooLarge);
}

#[test]
fn page_rounding_overflow_is_rejected_before_arena_allocation() {
    let mut source = fixture();
    let high = u64::MAX - 0x300;
    put64(&mut source, CODE + 24, high);
    put64(&mut source, THREAD + 144, high + 20);
    assert_eq!(KcStagingPlan::new(&source).unwrap_err(), E::AddressOverflow);
}

#[test]
fn zero_sized_extreme_segment_does_not_expand_the_arena() {
    let mut source = fixture();
    put64(&mut source, EMPTY + 24, u64::MAX);
    let plan = KcStagingPlan::new(&source).unwrap();
    assert_eq!(plan.arena_size(), 0x8000);
    assert_eq!(plan.segments().len(), 4);
}

#[test]
fn overlapping_outer_memory_and_file_ranges_remain_metadata_errors() {
    let mut source = fixture();
    put64(&mut source, CODE + 24, BASE + 0x2023);
    put64(&mut source, THREAD + 144, BASE + 0x2037);
    assert_eq!(
        KcStagingPlan::new(&source).unwrap_err(),
        E::Metadata(KcMetadataError::OverlappingRange)
    );
    let mut source = fixture();
    put64(&mut source, CODE + 40, 0x2020);
    assert_eq!(
        KcStagingPlan::new(&source).unwrap_err(),
        E::Metadata(KcMetadataError::OverlappingRange)
    );
}

#[test]
fn wrong_member_mapping_and_truncated_source_cannot_be_staged() {
    let mut source = fixture();
    put64(&mut source, 0x1600 + 32 + 24, BASE + 0x4601);
    assert!(matches!(KcStagingPlan::new(&source), Err(E::Metadata(_))));
    let source = fixture();
    assert!(matches!(
        KcStagingPlan::new(&source[..0x3080]),
        Err(E::Metadata(_))
    ));
}

#[test]
fn zero_file_backed_outer_segment_is_initialized_without_copying_source() {
    let mut source = fixture();
    // Replace the empty segment with a pure-zero mapping in an existing hole.
    put64(&mut source, EMPTY + 32, 0x200);
    let staged = KcStagingPlan::new(&source).unwrap().stage().unwrap();
    assert!(staged.bytes()[0x6000..0x6200].iter().all(|b| *b == 0));
    assert_eq!(staged.verification().zero_tail_bytes, 3072 + 0x200);
    assert_eq!(staged.verification().copied_bytes, 8961);
}
