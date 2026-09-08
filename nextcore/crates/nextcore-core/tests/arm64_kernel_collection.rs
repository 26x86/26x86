//! Independently authored format fixtures. No firmware or OS bytes.
use nextcore_core::{
    kc_staging::{KcStagingError, KcStagingPlan},
    kernel_collection::{
        inspect_arm64_kernel_collection as inspect, inspect_kernel_collection, EntryMetadata,
        KcMetadataError as E, PreparationRequirement,
    },
};

const PAGE: usize = 16384;
const VA: u64 = 0x1000_0000;
const LINK: usize = 3 * PAGE;
const FIX: usize = LINK + 64;
const ARM64E_KERNEL: u32 = 0xc000_0002;

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
fn segment(name: &str, offset: usize, file: usize, memory: usize, prot: u32) -> Vec<u8> {
    let mut b = command(0x19, 72);
    b[8..8 + name.len()].copy_from_slice(name.as_bytes());
    put64(&mut b, 24, VA + offset as u64);
    put64(&mut b, 32, memory as u64);
    put64(&mut b, 40, offset as u64);
    put64(&mut b, 48, file as u64);
    put32(&mut b, 56, prot);
    put32(&mut b, 60, prot);
    b
}
fn thread(pc: u64) -> Vec<u8> {
    let mut b = command(5, 288);
    put32(&mut b, 8, 6);
    put32(&mut b, 12, 68);
    put64(&mut b, 264, 0x2222_0000);
    put64(&mut b, 272, pc);
    put32(&mut b, 280, 0x3c5);
    put32(&mut b, 284, 1);
    b
}
fn member(id: &str, offset: usize) -> Vec<u8> {
    let mut b = command(0x8000_0035, (32 + id.len() + 1).div_ceil(8) * 8);
    put64(&mut b, 8, VA + offset as u64);
    put64(&mut b, 16, offset as u64);
    put32(&mut b, 24, 32);
    b[32..32 + id.len()].copy_from_slice(id.as_bytes());
    b
}
fn write_image(b: &mut [u8], base: usize, kind: u32, commands: Vec<Vec<u8>>) {
    put32(b, base, 0xfeed_facf);
    put32(b, base + 4, 0x0100_000c);
    put32(b, base + 8, ARM64E_KERNEL);
    put32(b, base + 12, kind);
    put32(b, base + 16, commands.len() as u32);
    put32(
        b,
        base + 20,
        commands.iter().map(Vec::len).sum::<usize>() as u32,
    );
    let mut at = base + 32;
    for command in commands {
        b[at..at + command.len()].copy_from_slice(&command);
        at += command.len();
    }
}
fn fixture() -> Vec<u8> {
    let mut b = vec![0; LINK + 512];
    let mut fix = command(0x8000_0034, 16);
    put32(&mut fix, 8, FIX as u32);
    put32(&mut fix, 12, 80);
    write_image(
        &mut b,
        0,
        12,
        vec![
            segment("__TEXT", 0, PAGE, PAGE, 1),
            segment("__CODE", PAGE, PAGE - 8, PAGE, 5),
            segment("__DATA", 2 * PAGE, PAGE / 2, PAGE, 3),
            segment("__LINKEDIT", LINK, 512, 512, 1),
            thread(VA + PAGE as u64 + 1024),
            member("fixture.kernel", PAGE),
            member("fixture.driver", 2 * PAGE),
            fix,
        ],
    );
    write_image(
        &mut b,
        PAGE,
        2,
        vec![
            segment("__TEXT", PAGE, PAGE - 8, PAGE, 5),
            segment("__DATA", 2 * PAGE, PAGE / 2, PAGE, 3),
            segment("__LINKEDIT", LINK, 512, 512, 1),
            thread(0x5555_0000),
        ],
    );
    write_image(
        &mut b,
        2 * PAGE,
        11,
        vec![
            segment("__TEXT", 2 * PAGE, PAGE / 2, PAGE, 3),
            segment("__LINKEDIT", LINK, 512, 512, 1),
        ],
    );
    put32(&mut b, FIX + 4, 28);
    put32(&mut b, FIX + 8, 80);
    put32(&mut b, FIX + 12, 80);
    put32(&mut b, FIX + 20, 1);
    put32(&mut b, FIX + 28, 4);
    put32(&mut b, FIX + 40, 20);
    put32(&mut b, FIX + 48, 24);
    put16(&mut b, FIX + 52, PAGE as u16);
    put16(&mut b, FIX + 54, 8);
    put64(&mut b, FIX + 56, (2 * PAGE) as u64);
    put16(&mut b, FIX + 68, 1);
    put16(&mut b, FIX + 70, 1024);
    // Opaque word deliberately preserved; no pointer interpretation requested.
    put64(&mut b, 2 * PAGE + 1024, 0xd1e2_f3a4_b5c6_7788);
    b
}
fn locate(b: &[u8], base: usize, kind: u32, nth: usize) -> usize {
    let mut at = base + 32;
    let mut found = 0;
    for _ in 0..get32(b, base + 16) {
        if get32(b, at) == kind {
            if found == nth {
                return at;
            }
            found += 1;
        }
        at += get32(b, at + 4) as usize;
    }
    panic!("missing authored command");
}

#[test]
fn raw_cpu_and_thread_provenance_survive_inspection() {
    let source = fixture();
    let result = inspect(&source).unwrap();
    assert_eq!(result.collection.cpu_type, 0x0100_000c);
    assert_eq!(result.collection.cpu_subtype, ARM64E_KERNEL);
    assert!(result
        .members
        .iter()
        .all(|m| m.image.cpu_subtype == ARM64E_KERNEL));
    assert_eq!(
        result.collection.entry,
        Some(EntryMetadata::ArmThread64 {
            instruction_pointer: VA + PAGE as u64 + 1024,
            stack_pointer: 0x2222_0000,
            cpsr: 0x3c5,
            flags: 1,
        })
    );
    assert!(matches!(
        result.members[0].image.entry,
        Some(EntryMetadata::ArmThread64 {
            instruction_pointer: 0x5555_0000,
            ..
        })
    ));
    assert!(result
        .requirements
        .contains(&PreparationRequirement::ChainedRebasing));
    assert!(result
        .requirements
        .contains(&PreparationRequirement::UnsupportedPointerFormat(8)));
    assert!(!result.preparation_ready());
}

#[test]
fn default_intel_inspection_and_staging_still_reject_arm() {
    let source = fixture();
    assert_eq!(
        inspect_kernel_collection(&source).unwrap_err(),
        E::UnsupportedCpu
    );
    assert_eq!(
        KcStagingPlan::new(&source).unwrap_err(),
        KcStagingError::Metadata(E::UnsupportedCpu)
    );
}

#[test]
fn wrong_cpu_and_mixed_member_subtypes_are_rejected() {
    for (at, value) in [(4, 0x0100_0007), (8, 7), (PAGE + 8, 2), (2 * PAGE + 4, 12)] {
        let mut source = fixture();
        put32(&mut source, at, value);
        assert_eq!(inspect(&source).unwrap_err(), E::UnsupportedCpu);
    }
}

#[test]
fn explicit_plain_arm64_profiles_are_not_inferred_from_arm64e() {
    for subtype in [
        0,
        1,
        2,
        0x8000_0002,
        0x8100_0002,
        0xc000_0002,
        0xc100_0002,
        0xc200_0002,
    ] {
        let mut source = fixture();
        for base in [0, PAGE, 2 * PAGE] {
            put32(&mut source, base + 8, subtype);
        }
        assert_eq!(inspect(&source).unwrap().collection.cpu_subtype, subtype);
    }
    for subtype in [
        0x8000_0000,
        0x8200_0002,
        0xc300_0002,
        0xff00_0002,
        0x4000_0002,
    ] {
        let mut source = fixture();
        put32(&mut source, 8, subtype);
        assert_eq!(inspect(&source).unwrap_err(), E::UnsupportedCpu);
    }
}

#[test]
fn thread_flavor_count_and_single_state_subset_are_checked() {
    for (delta, value) in [(8, 4), (12, 42), (4, 280), (4, 296)] {
        let mut source = fixture();
        let at = locate(&source, 0, 5, 0);
        put32(&mut source, at + delta, value);
        assert_eq!(inspect(&source).unwrap_err(), E::UnsupportedThreadState);
    }
}

#[test]
fn pc_requires_alignment_and_all_four_file_backed_bytes() {
    for pc in [VA + PAGE as u64 + 1025, VA, VA + (2 * PAGE - 8) as u64] {
        let mut source = fixture();
        let at = locate(&source, 0, 5, 0);
        put64(&mut source, at + 272, pc);
        assert_eq!(inspect(&source).unwrap_err(), E::InvalidEntry);
    }
    let mut source = fixture();
    let entry = locate(&source, 0, 5, 0);
    let code = locate(&source, 0, 0x19, 1);
    // A mapped aligned PC with only two file-backed bytes is still invalid.
    put64(&mut source, entry + 272, VA + PAGE as u64 + 1024);
    put64(&mut source, code + 48, 1026);
    assert_eq!(inspect(&source).unwrap_err(), E::InvalidEntry);
}

#[test]
fn last_complete_instruction_extent_is_accepted() {
    let mut source = fixture();
    let entry = locate(&source, 0, 5, 0);
    put64(&mut source, entry + 272, VA + (2 * PAGE - 12) as u64);
    inspect(&source).unwrap();
}

#[test]
fn format8_start_requires_full_opaque_word() {
    let mut source = fixture();
    put16(&mut source, FIX + 70, (PAGE / 2 - 4) as u16);
    assert_eq!(inspect(&source).unwrap_err(), E::InvalidFixups);
}

#[test]
fn staging_rounds_16k_and_preserves_every_source_view() {
    let source = fixture();
    let original = source.clone();
    let staged = KcStagingPlan::new_arm64(&source).unwrap().stage().unwrap();
    assert_eq!(staged.plan().page_size(), PAGE as u64);
    assert_eq!(staged.plan().minimum_virtual_address(), VA);
    assert_eq!(staged.plan().outer_entry_offset(), PAGE + 1024);
    let verified = staged.verification();
    assert_eq!(verified.arena_bytes, 4 * PAGE);
    assert_eq!(verified.zero_tail_bytes, PAGE / 2 + 8);
    assert_eq!(verified.hole_bytes, PAGE - 512);
    assert_eq!(verified.member_headers_checked, 2);
    assert_eq!(verified.member_segment_views_checked, 5);
    assert_eq!(
        verified.copied_bytes + verified.zero_tail_bytes + verified.hole_bytes,
        4 * PAGE
    );
    assert_eq!(&staged.bytes()[FIX..FIX + 80], &source[FIX..FIX + 80]);
    assert_eq!(
        &staged.bytes()[2 * PAGE + 1024..2 * PAGE + 1032],
        &source[2 * PAGE + 1024..2 * PAGE + 1032]
    );
    assert_eq!(source, original);
    assert!(!staged.preparation_ready());
}

#[test]
fn member_shared_views_do_not_require_outer_page_alignment() {
    let mut source = fixture();
    let data = locate(&source, PAGE, 0x19, 1);
    put64(&mut source, data + 24, VA + (2 * PAGE + 4) as u64);
    put64(&mut source, data + 32, (PAGE - 4) as u64);
    put64(&mut source, data + 40, (2 * PAGE + 4) as u64);
    put64(&mut source, data + 48, (PAGE / 2 - 4) as u64);
    let staged = KcStagingPlan::new_arm64(&source).unwrap().stage().unwrap();
    assert_eq!(staged.verification().member_segment_views_checked, 5);
    assert_eq!(staged.verification().member_headers_checked, 2);
}

#[test]
fn staging_detects_corrupt_header_payload_tail_and_hole() {
    let source = fixture();
    let plan = KcStagingPlan::new_arm64(&source).unwrap();
    for offset in [
        0,
        PAGE,
        2 * PAGE + 1024,
        2 * PAGE - 1,
        3 * PAGE - 1,
        4 * PAGE - 1,
    ] {
        let mut arena = vec![0x99; plan.arena_size()];
        plan.stage_into(&mut arena).unwrap();
        arena[offset] ^= 0xff;
        assert_eq!(
            plan.verify(&arena).unwrap_err(),
            KcStagingError::ReadbackMismatch
        );
    }
    let mut short = vec![0x99; plan.arena_size() - 1];
    assert_eq!(
        plan.stage_into(&mut short).unwrap_err(),
        KcStagingError::DestinationSize
    );
    assert!(short.iter().all(|&byte| byte == 0x99));
}

#[test]
fn malformed_outer_and_member_ranges_stay_bounded() {
    let mut source = fixture();
    let member = locate(&source, 0, 0x8000_0035, 0);
    put64(&mut source, member + 16, u64::MAX - 15);
    assert_eq!(inspect(&source).unwrap_err(), E::Overflow);
    let mut source = fixture();
    let code = locate(&source, 0, 0x19, 1);
    put64(&mut source, code + 24, u64::MAX - 3);
    assert_eq!(inspect(&source).unwrap_err(), E::Overflow);
    let mut source = fixture();
    let data = locate(&source, 0, 0x19, 2);
    put64(&mut source, data + 24, VA + PAGE as u64);
    assert_eq!(inspect(&source).unwrap_err(), E::OverlappingRange);
}
