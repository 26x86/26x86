//! Independently authored Mach-O fixture: no OS bytes or instructions.
use nextcore_core::{
    kc_classic_rebase::{ClassicRebaseError as E, KcClassicRebasePlan},
    kc_staging::KcStagingPlan,
};
const VA: u64 = 0x8000_0000;
const RELOCS: usize = 0x3100;
const FIX: usize = 0x3200;
const INFO: usize = FIX + 52;
const CHAIN: usize = 0x2600;
const DYSYM: usize = 32 + 72 * 4 + 184 + 48 * 2 + 24;
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
fn seg(name: &str, va: u64, file: u64, prot: u32) -> Vec<u8> {
    let mut b = cmd(0x19, 72);
    b[8..8 + name.len()].copy_from_slice(name.as_bytes());
    p64(&mut b, 24, va);
    p64(&mut b, 32, 4096);
    p64(&mut b, 40, file);
    p64(&mut b, 48, 4096);
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
    let mut b = cmd(0x8000_0035, 48);
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
    let mut pos = at + 32;
    for c in commands {
        b[pos..pos + c.len()].copy_from_slice(&c);
        pos += c.len();
    }
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
            seg("__TEXT", VA + 0x2000, 0, 1),
            seg("__CODE", VA, 0x1000, 5),
            seg("__DATA", VA + 0x4000, 0x2000, 3),
            seg("__LINKEDIT", VA + 0x6000, 0x3000, 1),
            thread(VA + 0x800),
            member("kernel", 0x1000, VA),
            member("driver", 0x2000, VA + 0x4000),
            cmd(2, 24),
            dysym,
            fix,
        ],
    );
    image(
        &mut b,
        0x1000,
        2,
        vec![seg("__TEXT", VA, 0x1000, 5), thread(VA + 0x888)],
    );
    image(
        &mut b,
        0x2000,
        11,
        vec![seg("__TEXT", VA + 0x4000, 0x2000, 3)],
    );
    // Both negative displacements resolve into the executable member. The
    // second unaligned four-byte destination tests width-specific reads/writes.
    p32(&mut b, RELOCS, (-0x37f0i32) as u32);
    p32(&mut b, RELOCS + 4, 3 << 25);
    p32(&mut b, RELOCS + 8, (-0x37d3i32) as u32);
    p32(&mut b, RELOCS + 12, 2 << 25);
    p64(&mut b, 0x1810, VA + 0x4400);
    p32(&mut b, 0x182d, 0x1200_1234);
    p32(&mut b, FIX + 4, 28);
    p32(&mut b, FIX + 8, 76);
    p32(&mut b, FIX + 12, 76);
    p32(&mut b, FIX + 20, 1);
    p32(&mut b, FIX + 28, 4);
    p32(&mut b, FIX + 40, 24);
    p32(&mut b, INFO, 24);
    p16(&mut b, INFO + 4, 4096);
    p16(&mut b, INFO + 6, 11);
    p64(&mut b, INFO + 8, 0x2000);
    p16(&mut b, INFO + 20, 1);
    p16(&mut b, INFO + 22, 0x600);
    p64(&mut b, CHAIN, 0x820 | (9u64 << 51));
    p64(&mut b, CHAIN + 9, 0x4400);
    // Source has bytes beyond this shortened file mapping; staging must zero
    // its owned tail and the subsequent page-rounded arena independently.
    p64(&mut b, 32 + 72 * 3 + 48, 0x800);
    b[0x3900] = 0x5a;
    b
}
fn rejects(b: &[u8], slide: u32, expected: E) {
    let original = b.to_vec();
    assert_eq!(KcClassicRebasePlan::new(b, slide).unwrap_err(), expected);
    assert_eq!(b, original);
}
#[test]
fn applies_both_widths_and_preserves_every_other_byte() {
    let b = fixture();
    let original = b.clone();
    let baseline = KcStagingPlan::new(&b).unwrap().stage().unwrap();
    let mut expected = baseline.bytes().to_vec();
    p64(&mut expected, 0x810, VA + 0x4400 + 0x200000);
    p32(&mut expected, 0x82d, 0x1220_1234);
    let result = KcClassicRebasePlan::new(&b, 0x200000)
        .unwrap()
        .apply()
        .unwrap();
    assert_eq!(result.bytes(), expected);
    assert_eq!(b, original);
    let s = result.verification();
    assert_eq!((s.classic_words, s.width4_words, s.width8_words), (2, 1, 1));
    assert_eq!(s.write_bytes_verified, 12);
    assert_eq!(s.non_target_bytes_verified + 12, s.arena_bytes);
    assert_eq!((s.chain_words_preserved, s.header_ranges_preserved), (2, 3));
    assert!(s.changed_bytes > 0);
    assert!(result.classic_relocations_applied());
    assert!(!result.preparation_ready());
    assert!(result.original_staging().hole_bytes > 0);
    assert_eq!(result.original_staging().zero_tail_bytes, 0x800);
    assert_eq!(result.plan().verify(result.bytes()).unwrap(), *s);
}
#[test]
fn zero_slide_preserves_image_and_still_reads_back() {
    let b = fixture();
    let result = KcClassicRebasePlan::new(&b, 0).unwrap().apply().unwrap();
    assert_eq!(result.verification().changed_bytes, 0);
    assert_eq!(
        result.bytes(),
        KcStagingPlan::new(&b).unwrap().stage().unwrap().bytes()
    );
}
#[test]
fn width4_overflow_rejected_without_wrapping() {
    let mut b = fixture();
    p32(&mut b, 0x182d, u32::MAX);
    rejects(&b, 1, E::ValueOverflow);
}
#[test]
fn width8_overflow_rejected_without_wrapping() {
    let mut b = fixture();
    p64(&mut b, 0x1810, u64::MAX);
    rejects(&b, 1, E::ValueOverflow);
}
#[test]
fn width4_exact_max_is_supported() {
    let mut b = fixture();
    p32(&mut b, 0x182d, u32::MAX - 1);
    let r = KcClassicRebasePlan::new(&b, 1).unwrap().apply().unwrap();
    assert_eq!(&r.bytes()[0x82d..0x831], &u32::MAX.to_le_bytes());
}
#[test]
fn symbol_nonzero_is_outside_profile() {
    let mut b = fixture();
    p32(&mut b, RELOCS + 4, (3 << 25) | 1);
    rejects(&b, 1, E::UnsupportedClassicProfile);
}
#[test]
fn unsupported_type_pc_external_width_are_rejected() {
    for flags in [
        (3 << 25) | (1 << 28),
        (3 << 25) | (1 << 24),
        (3 << 25) | (1 << 27),
        1 << 25,
    ] {
        let mut b = fixture();
        p32(&mut b, RELOCS + 4, flags);
        rejects(&b, 1, E::AuditIssues);
    }
}
#[test]
fn target_in_kext_is_not_kernel_proper() {
    let mut b = fixture();
    p32(&mut b, RELOCS + 8, 0x410);
    rejects(&b, 1, E::UnsupportedClassicProfile);
}
#[test]
fn word_crossing_kernel_file_end_is_rejected() {
    let mut b = fixture();
    p32(&mut b, RELOCS, (-0x3004i32) as u32);
    rejects(&b, 1, E::AuditIssues);
}
#[test]
fn header_and_load_commands_are_preserved_by_rejection() {
    for offset in [0i32, 32, 104] {
        let mut b = fixture();
        p32(&mut b, RELOCS, (-0x4000i32 + offset) as u32);
        rejects(&b, 1, E::HeaderWrite);
    }
}
#[test]
fn duplicate_classic_write_rejected() {
    let mut b = fixture();
    p32(&mut b, RELOCS + 8, (-0x37f0i32) as u32);
    rejects(&b, 1, E::AuditIssues);
}
#[test]
fn classic_chain_overlap_rejected_before_profile_application() {
    let mut b = fixture();
    p32(&mut b, RELOCS, 0x600);
    rejects(&b, 1, E::AuditIssues);
}
#[test]
fn no_executable_is_rejected() {
    let mut b = fixture();
    p32(&mut b, 0x1000 + 12, 11);
    rejects(&b, 1, E::ExecutableMemberCount);
}
#[test]
fn two_executables_are_rejected() {
    let mut b = fixture();
    p32(&mut b, 0x2000 + 12, 2);
    rejects(&b, 1, E::ExecutableMemberCount);
}
#[test]
fn empty_classic_table_is_not_success() {
    let mut b = fixture();
    p32(&mut b, DYSYM + 72, 0);
    p32(&mut b, DYSYM + 76, 0);
    rejects(&b, 1, E::EmptyClassicTable);
}
#[test]
fn non_outer_classic_table_is_rejected() {
    let mut b = fixture();
    // Move the same table into the kernel header, preserving its source range.
    let mut dysym = cmd(0xb, 80);
    p32(&mut dysym, 72, RELOCS as u32);
    p32(&mut dysym, 76, 2);
    image(
        &mut b,
        0x1000,
        2,
        vec![
            seg("__TEXT", VA, 0x1000, 5),
            thread(VA + 0x888),
            seg("__LINKEDIT", VA + 0x6000, 0x3000, 1),
            cmd(2, 24),
            dysym,
        ],
    );
    // Keep member linkedit consistent with outer shortened file mapping.
    p64(&mut b, 0x1000 + 32 + 72 + 184 + 48, 0x800);
    p32(&mut b, DYSYM + 72, 0);
    p32(&mut b, DYSYM + 76, 0);
    // Give the member its own valid writable base and relative offsets so the
    // audit succeeds; the new profile must still reject a non-outer table.
    p32(&mut b, 0x1000 + 32 + 56, 7);
    p32(&mut b, 0x1000 + 32 + 60, 7);
    p32(&mut b, RELOCS, 0x810);
    p32(&mut b, RELOCS + 8, 0x82d);
    rejects(&b, 1, E::UnsupportedClassicProfile);
}

#[test]
fn external_dynamic_table_is_rejected_even_with_local_flags() {
    let mut b = fixture();
    p32(&mut b, DYSYM + 64, RELOCS as u32);
    p32(&mut b, DYSYM + 68, 2);
    p32(&mut b, DYSYM + 72, 0);
    p32(&mut b, DYSYM + 76, 0);
    // The existing complete audit classifies an external dynamic table as an
    // external relocation even when its record's external flag is cleared.
    rejects(&b, 1, E::AuditIssues);
}
#[test]
fn readback_detects_target_chain_header_hole_and_tail_damage() {
    let b = fixture();
    let result = KcClassicRebasePlan::new(&b, 0x200000)
        .unwrap()
        .apply()
        .unwrap();
    for offset in [0x810, 0x82d, 0, 32, 0x1000, 0x4600, 0x4609, 0x6800, 0x6fff] {
        let mut copy = result.bytes().to_vec();
        copy[offset] ^= 1;
        assert_eq!(
            result.plan().verify(&copy).unwrap_err(),
            E::ReadbackMismatch,
            "offset {offset:x}"
        );
    }
    assert_eq!(
        result
            .plan()
            .verify(&result.bytes()[..result.bytes().len() - 1])
            .unwrap_err(),
        E::DestinationSize
    );
}
