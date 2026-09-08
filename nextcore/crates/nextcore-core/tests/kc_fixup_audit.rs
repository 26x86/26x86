//! Authored public-format records/words only; no OS payload or instructions.
use nextcore_core::kc_fixup_audit::{
    audit_kernel_collection, audit_kernel_collection_with_limits, AuditError, AuditLimits,
    IssueCode, MemberOverlap, RecordDetail,
};
const VA: u64 = 0x8000_0000;
const CODE: usize = 32 + 72;
const DATA: usize = CODE + 72;
const EMPTY: usize = DATA + 144;
const RELOCS: usize = 0x3100;
const FIX: usize = 0x3200;
const INFO: usize = FIX + 52;
const CHAIN: usize = 0x2600;
fn p16(b: &mut [u8], at: usize, n: u16) {
    b[at..at + 2].copy_from_slice(&n.to_le_bytes())
}
fn p32(b: &mut [u8], at: usize, n: u32) {
    b[at..at + 4].copy_from_slice(&n.to_le_bytes())
}
fn p64(b: &mut [u8], at: usize, n: u64) {
    b[at..at + 8].copy_from_slice(&n.to_le_bytes())
}
fn cmd(kind: u32, size: usize) -> Vec<u8> {
    let mut b = vec![0; size];
    p32(&mut b, 0, kind);
    p32(&mut b, 4, size as u32);
    b
}
fn seg(name: &str, va: u64, file: u64, size: u64, prot: u32) -> Vec<u8> {
    let mut b = cmd(0x19, 72);
    b[8..8 + name.len()].copy_from_slice(name.as_bytes());
    p64(&mut b, 24, va);
    p64(&mut b, 32, size);
    p64(&mut b, 40, file);
    p64(&mut b, 48, size);
    p32(&mut b, 56, prot);
    p32(&mut b, 60, prot);
    b
}
fn thread(va: u64) -> Vec<u8> {
    let mut b = cmd(5, 184);
    p32(&mut b, 8, 4);
    p32(&mut b, 12, 42);
    p64(&mut b, 144, va);
    b
}
fn member(name: &str, file: u64, va: u64) -> Vec<u8> {
    let mut b = cmd(0x8000_0035, (33 + name.len()).div_ceil(8) * 8);
    p64(&mut b, 8, va);
    p64(&mut b, 16, file);
    p32(&mut b, 24, 32);
    b[32..32 + name.len()].copy_from_slice(name.as_bytes());
    b
}
fn image(b: &mut [u8], at: usize, kind: u32, commands: Vec<Vec<u8>>) {
    p32(b, at, 0xfeed_facf);
    p32(b, at + 4, 0x0100_0007);
    p32(b, at + 8, 3);
    p32(b, at + 12, kind);
    p32(b, at + 16, commands.len() as u32);
    p32(
        b,
        at + 20,
        commands.iter().map(Vec::len).sum::<usize>() as u32,
    );
    let mut cur = at + 32;
    for c in commands {
        b[cur..cur + c.len()].copy_from_slice(&c);
        cur += c.len();
    }
}
fn word(target: u32, next: u16, cache: u8, auth: bool) -> u64 {
    u64::from(target) | (u64::from(cache) << 30) | (u64::from(next) << 51) | (u64::from(auth) << 63)
}
fn fixture() -> Vec<u8> {
    let mut b = vec![0; 0x4000];
    let mut dysym = cmd(0xb, 80);
    p32(&mut dysym, 72, RELOCS as u32);
    p32(&mut dysym, 76, 2);
    let mut fix = cmd(0x8000_0034, 16);
    p32(&mut fix, 8, FIX as u32);
    p32(&mut fix, 12, 76);
    image(
        &mut b,
        0,
        12,
        vec![
            seg("__TEXT", VA + 0x2000, 0, 4096, 1),
            seg("__CODE", VA, 0x1000, 4096, 5),
            seg("__DATA", VA + 0x4000, 0x2000, 4096, 3),
            seg("__LINKEDIT", VA + 0x6000, 0x3000, 4096, 1),
            seg("__EMPTY", VA + 0x8000, 0, 0, 1),
            thread(VA + 0x800),
            member("authored.kernel", 0x1000, VA),
            member("authored.driver", 0x2000, VA + 0x4000),
            cmd(2, 24),
            dysym,
            fix,
        ],
    );
    image(
        &mut b,
        0x1000,
        2,
        vec![seg("__TEXT", VA, 0x1000, 4096, 5), thread(VA + 0x888)],
    );
    image(
        &mut b,
        0x2000,
        11,
        vec![seg("__TEXT", VA + 0x4000, 0x2000, 4096, 3)],
    );
    p32(&mut b, RELOCS, (-0x37f0i32) as u32);
    p32(&mut b, RELOCS + 4, 3 << 25);
    p32(&mut b, RELOCS + 8, 0x410);
    p32(&mut b, RELOCS + 12, 2 << 25);
    p64(&mut b, 0x1810, VA + 0x4400);
    p32(&mut b, 0x2410, 0x12345678);
    p32(&mut b, FIX + 4, 28);
    p32(&mut b, FIX + 8, 76);
    p32(&mut b, FIX + 12, 76);
    p32(&mut b, FIX + 20, 1);
    p32(&mut b, FIX + 28, 5);
    p32(&mut b, FIX + 40, 24);
    p32(&mut b, INFO, 24);
    p16(&mut b, INFO + 4, 4096);
    p16(&mut b, INFO + 6, 11);
    p64(&mut b, INFO + 8, 0x2000);
    p16(&mut b, INFO + 20, 1);
    p16(&mut b, INFO + 22, 0x600);
    p64(&mut b, CHAIN, word(0x820, 9, 0, false));
    p64(&mut b, CHAIN + 9, word(0x4400, 0, 0, false));
    b
}
fn has(b: &[u8], issue: IssueCode) {
    let a = audit_kernel_collection(b).unwrap();
    assert!(!a.ranges_valid());
    assert!(
        a.issues().iter().any(|i| i.code == issue),
        "expected {issue:?}, got {:?}",
        a.summary()
    );
    assert!(!a.preparation_ready());
}
fn multi_fixture() -> Vec<u8> {
    let mut b = fixture();
    let fixcmd = command_at(&b, 0x8000_0034);
    p32(&mut b, fixcmd + 12, 80);
    p32(&mut b, FIX + 8, 80);
    p32(&mut b, FIX + 12, 80);
    p32(&mut b, INFO, 28);
    p16(&mut b, INFO + 22, 0x8001);
    p16(&mut b, INFO + 24, 0x600);
    p16(&mut b, INFO + 26, 0x8600);
    b
}
fn two_page_data_fixture() -> Vec<u8> {
    let mut b = fixture();
    b.resize(0x5000, 0);
    b.copy_within(0x3000..0x4000, 0x4000);
    b[0x3000..0x4000].fill(0);
    p64(&mut b, DATA + 32, 0x2000);
    p64(&mut b, DATA + 48, 0x2000);
    p64(&mut b, DATA + 72 + 40, 0x4000);
    let dysym = command_at(&b, 0xb);
    p32(&mut b, dysym + 72, (RELOCS + 0x1000) as u32);
    let fixcmd = command_at(&b, 0x8000_0034);
    p32(&mut b, fixcmd + 8, (FIX + 0x1000) as u32);
    p32(&mut b, fixcmd + 12, 78);
    p32(&mut b, FIX + 0x1000 + 8, 78);
    p32(&mut b, FIX + 0x1000 + 12, 78);
    p32(&mut b, INFO + 0x1000, 26);
    p16(&mut b, INFO + 0x1000 + 20, 2);
    p16(&mut b, INFO + 0x1000 + 22, 0x600);
    p16(&mut b, INFO + 0x1000 + 24, 0xffff);
    p64(&mut b, CHAIN, word(0x820, 0x9fc, 0, false));
    p64(&mut b, 0x2ffc, word(0x820, 0, 0, false));
    b
}
fn section_fixture(displacement: i32) -> Vec<u8> {
    let mut b = fixture();
    let mut s = seg("__TEXT", VA + 0x4000, 0x2000, 4096, 3);
    s.resize(152, 0);
    p32(&mut s, 4, 152);
    p32(&mut s, 64, 1);
    s[72..78].copy_from_slice(b"record");
    s[88..94].copy_from_slice(b"__TEXT");
    p64(&mut s, 104, VA + 0x4700);
    p64(&mut s, 112, 0x20);
    p32(&mut s, 120, 0x2700);
    p32(&mut s, 124, 3);
    p32(&mut s, 128, (RELOCS + 16) as u32);
    p32(&mut s, 132, 1);
    image(
        &mut b,
        0x2000,
        11,
        vec![s, seg("__LINKEDIT", VA + 0x6000, 0x3000, 4096, 1)],
    );
    p32(&mut b, RELOCS + 16, displacement as u32);
    p32(&mut b, RELOCS + 20, 3 << 25);
    b
}
fn command_at(b: &[u8], kind: u32) -> usize {
    let mut at = 32;
    loop {
        let cmd = u32::from_le_bytes(b[at..at + 4].try_into().unwrap());
        if cmd == kind {
            return at;
        }
        at += u32::from_le_bytes(b[at + 4..at + 8].try_into().unwrap()) as usize;
    }
}

#[test]
fn signed_classic_and_unaligned_byte_stride_are_audited_without_writes() {
    let b = fixture();
    let before = b.clone();
    let a = audit_kernel_collection(&b).unwrap();
    assert!(a.ranges_valid(), "{a:?}");
    assert_eq!(b, before);
    assert_eq!(a.primary_base(), VA);
    assert_eq!(a.summary().classic_records, 2);
    assert_eq!(a.summary().classic_negative_displacements, 1);
    assert_eq!(a.summary().chain_records, 2);
    assert_eq!(a.summary().chains_terminated, 1);
    assert_eq!(a.summary().primary_pointer_targets_covered, 2);
    assert_eq!(a.records()[0].write_address, Some(VA + 0x810));
    assert_eq!(a.records()[0].write_file_offset, Some(0x1810));
    assert_eq!(a.records()[0].width, 8);
    assert_eq!(
        a.records()[0].member_overlap,
        MemberOverlap::ExecutableMember
    );
    assert_eq!(a.records()[1].width, 4);
    assert_eq!(a.records()[1].member_overlap, MemberOverlap::KextMember);
    assert_eq!(a.records()[2].write_address, Some(VA + 0x4600));
    assert_eq!(a.records()[3].write_address, Some(VA + 0x4609));
    assert!(matches!(
        a.records()[1].detail,
        RecordDetail::Classic {
            stored_value: Some(0x12345678),
            ..
        }
    ));
    assert!(!a.preparation_ready());
    assert!(!a.relocations_applied());
    assert!(!a.ownership_resolved());
}
#[test]
fn terminal_word_may_straddle_its_page_inside_one_file_backed_segment() {
    let b = two_page_data_fixture();
    let before = b.clone();
    let audit = audit_kernel_collection(&b).unwrap();
    assert!(audit.ranges_valid(), "{audit:?}");
    assert_eq!(audit.summary().chain_records, 2);
    assert_eq!(audit.summary().chains_terminated, 1);
    assert_eq!(audit.summary().chain_page_straddling_words, 1);
    assert_eq!(audit.records()[3].write_file_offset, Some(0x2ffc));
    assert_eq!(b, before);
    assert!(!audit.preparation_ready());
}
#[test]
fn first_and_only_chain_word_can_straddle_its_page() {
    let mut b = two_page_data_fixture();
    p16(&mut b, INFO + 0x1000 + 22, 0xffc);
    let audit = audit_kernel_collection(&b).unwrap();
    assert!(audit.ranges_valid(), "{audit:?}");
    assert_eq!(audit.summary().chain_records, 1);
    assert_eq!(audit.summary().chains_terminated, 1);
    assert_eq!(audit.summary().chain_page_straddling_words, 1);
}
#[test]
fn page_straddle_does_not_permit_crossing_a_segment_file_end() {
    let mut b = fixture();
    p64(&mut b, CHAIN, word(0x820, 0x9fc, 0, false));
    p64(&mut b, 0x2ffc, word(0x820, 0, 0, false));
    has(&b, IssueCode::ChainOutsideFileMapping);
}
#[test]
fn next_start_cannot_leave_the_page_even_in_a_larger_segment() {
    let mut b = two_page_data_fixture();
    p64(&mut b, 0x2ffc, word(0x820, 8, 0, false));
    p64(&mut b, 0x3004, word(0x820, 0, 0, false));
    has(&b, IssueCode::ChainOutsidePage);
}
#[test]
fn unsigned_classic_flags_and_widths_are_not_silently_supported() {
    for (bits, issue) in [
        (1 << 28, IssueCode::UnsupportedClassicType),
        (1 << 24, IssueCode::UnsupportedPcRelative),
        (1 << 27, IssueCode::UnsupportedExternal),
    ] {
        let mut b = fixture();
        p32(&mut b, RELOCS + 4, (3 << 25) | bits);
        has(&b, issue);
    }
    for length in [0, 1] {
        let mut b = fixture();
        p32(&mut b, RELOCS + 4, length << 25);
        has(&b, IssueCode::UnsupportedClassicWidth);
    }
}
#[test]
fn classic_write_must_fit_its_entire_file_backed_word() {
    let mut b = fixture();
    p32(&mut b, RELOCS, 0xffc);
    has(&b, IssueCode::WriteOutsideFileMapping);
    let mut b = fixture();
    p32(&mut b, RELOCS, (-0x1000i32) as u32);
    has(&b, IssueCode::WriteOutsideFileMapping);
}
#[test]
fn unsupported_external_table_is_reported_even_if_record_flag_is_clear() {
    let mut b = fixture();
    let at = command_at(&b, 0xb);
    p32(&mut b, at + 64, (RELOCS + 16) as u32);
    p32(&mut b, at + 68, 1);
    p32(&mut b, RELOCS + 16, 0x500);
    p32(&mut b, RELOCS + 20, 3 << 25);
    has(&b, IssueCode::UnsupportedExternal);
}
#[test]
fn missing_classic_base_does_not_guess_header_address() {
    let mut b = fixture();
    p32(&mut b, DATA + 60, 1);
    has(&b, IssueCode::MissingClassicBase);
}
#[test]
fn unknown_cache_and_authentication_remain_issues() {
    let mut b = fixture();
    p64(&mut b, CHAIN, word(0x820, 9, 2, false));
    has(&b, IssueCode::MissingCacheBase);
    let mut b = fixture();
    p64(&mut b, CHAIN, word(0x820, 9, 0, true));
    has(&b, IssueCode::UnsupportedAuthentication);
}
#[test]
fn pointer_into_hole_or_outside_collection_is_not_covered() {
    for target in [0x3000, 0x3fff_ffff] {
        let mut b = fixture();
        p64(&mut b, CHAIN, word(target, 9, 0, false));
        has(&b, IssueCode::PointerTargetOutsideMappings);
    }
}
#[test]
fn bad_next_stops_at_page_boundary() {
    let mut b = fixture();
    p64(&mut b, CHAIN, word(0x820, 4095, 0, false));
    has(&b, IssueCode::ChainOutsidePage);
}
#[test]
fn later_word_cannot_enter_segment_zero_fill() {
    let mut b = fixture();
    p64(&mut b, DATA + 48, 0xf80);
    p64(&mut b, 0x2000 + 32 + 48, 0xf80);
    p16(&mut b, INFO + 22, 0xf00);
    p64(&mut b, 0x2f00, word(0x820, 0xa0, 0, false));
    has(&b, IssueCode::ChainOutsideFileMapping);
}
#[test]
fn duplicate_multistart_visits_and_consumer_limit_are_reported() {
    let b = multi_fixture();
    let a = audit_kernel_collection(&b).unwrap();
    assert!(!a.ranges_valid());
    for issue in [
        IssueCode::UnsupportedMultiStartConsumer,
        IssueCode::DuplicateChainVisit,
        IssueCode::SameMechanismWriteOverlap,
    ] {
        assert!(a.issues().iter().any(|i| i.code == issue));
    }
}
#[test]
fn classic_chain_and_classic_classic_overlaps_have_distinct_witnesses() {
    let mut b = fixture();
    p32(&mut b, RELOCS + 8, 0x603);
    has(&b, IssueCode::CrossMechanismWriteOverlap);
    let mut b = fixture();
    p32(&mut b, RELOCS + 8, (-0x37eci32) as u32);
    has(&b, IssueCode::SameMechanismWriteOverlap);
}
#[test]
fn zero_size_segment_affects_declared_primary_base_without_fake_adjustment() {
    let mut b = fixture();
    p64(&mut b, EMPTY + 24, VA - 0x1000);
    let a = audit_kernel_collection(&b).unwrap();
    assert_eq!(a.primary_base(), VA - 0x1000);
    assert!(!a.ranges_valid());
}
#[test]
fn absent_primary_base_and_unsupported_format_are_explicit() {
    let mut b = fixture();
    p64(&mut b, EMPTY + 24, 0);
    has(&b, IssueCode::MissingCacheBase);
    let mut b = fixture();
    p16(&mut b, INFO + 6, 12);
    has(&b, IssueCode::UnsupportedPointerFormat);
}
#[test]
fn resource_limits_reject_partial_audits() {
    let b = fixture();
    let before = b.clone();
    for limits in [
        AuditLimits {
            records: 1,
            ..Default::default()
        },
        AuditLimits {
            page_starts: 1,
            records: 3,
            ..Default::default()
        },
    ] {
        assert!(matches!(
            audit_kernel_collection_with_limits(&b, limits),
            Err(AuditError::LimitExceeded)
        ));
    }
    assert_eq!(b, before);
    let mut b = fixture();
    p32(&mut b, RELOCS + 4, (1 << 28) | (1 << 24));
    assert!(matches!(
        audit_kernel_collection_with_limits(
            &b,
            AuditLimits {
                issues: 1,
                ..Default::default()
            }
        ),
        Err(AuditError::LimitExceeded)
    ));
    assert!(matches!(
        audit_kernel_collection_with_limits(
            &b,
            AuditLimits {
                records: 0,
                ..Default::default()
            }
        ),
        Err(AuditError::InvalidLimits)
    ));
}

#[test]
fn page_start_budget_is_independent_from_record_budget() {
    let b = multi_fixture();
    assert!(matches!(
        audit_kernel_collection_with_limits(
            &b,
            AuditLimits {
                page_starts: 1,
                ..Default::default()
            }
        ),
        Err(AuditError::LimitExceeded)
    ));
}

#[test]
fn section_relative_record_cannot_write_outside_its_section() {
    let b = section_fixture(0x10);
    let a = audit_kernel_collection(&b).unwrap();
    assert!(a.ranges_valid(), "{a:?}");
    assert_eq!(a.records().last().unwrap().write_address, Some(VA + 0x4710));
    has(&section_fixture(0x1c), IssueCode::WriteOutsideSection);
    has(&section_fixture(-4), IssueCode::NegativeSectionDisplacement);
}
#[test]
fn truncated_or_forged_metadata_never_returns_an_audit() {
    let b = fixture();
    for length in [0, 32, 0x3000, 0x3240] {
        assert!(matches!(
            audit_kernel_collection(&b[..length]),
            Err(AuditError::Metadata(_))
        ));
    }
}
