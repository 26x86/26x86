//! Authored format fixtures: these tests do not contain or execute XNU.
use nextcore_core::macho_image::{
    parse_macho_image, EntryKind, MachOImageError as E, MAX_COMMANDS, MAX_IMAGE_SIZE, MAX_SECTIONS,
    MAX_SEGMENTS,
};

const BASE: u64 = 0x1_0000_0000;

fn put32(bytes: &mut [u8], at: usize, value: u32) {
    bytes[at..at + 4].copy_from_slice(&value.to_le_bytes());
}

fn put64(bytes: &mut [u8], at: usize, value: u64) {
    bytes[at..at + 8].copy_from_slice(&value.to_le_bytes());
}

fn command(kind: u32, size: usize) -> Vec<u8> {
    let mut result = vec![0; size];
    put32(&mut result, 0, kind);
    put32(&mut result, 4, size as u32);
    result
}

fn segment(
    name: &[u8],
    vmaddr: u64,
    vmsize: u64,
    fileoff: u64,
    filesize: u64,
    prot: u32,
) -> Vec<u8> {
    let mut result = command(0x19, 72);
    result[8..8 + name.len()].copy_from_slice(name);
    put64(&mut result, 24, vmaddr);
    put64(&mut result, 32, vmsize);
    put64(&mut result, 40, fileoff);
    put64(&mut result, 48, filesize);
    put32(&mut result, 56, prot);
    put32(&mut result, 60, prot);
    result
}

fn main_entry() -> Vec<u8> {
    let mut result = command(0x8000_0028, 24);
    put64(&mut result, 8, 0x1100);
    result
}

fn thread_entry() -> Vec<u8> {
    let mut result = command(5, 184);
    put32(&mut result, 8, 4);
    put32(&mut result, 12, 42);
    put64(&mut result, 144, BASE + 0x4100);
    result
}

fn commands(entry: Vec<u8>) -> Vec<Vec<u8>> {
    vec![
        segment(b"__HEADER", BASE, 0x1000, 0, 0x1000, 1),
        segment(b"__TEXT", BASE + 0x4000, 0x1000, 0x1000, 0x1000, 5),
        segment(b"__DATA", BASE + 0x7000, 0x2000, 0x2000, 0x100, 3),
        entry,
    ]
}

fn image(commands: &[Vec<u8>]) -> Vec<u8> {
    let commands_size: usize = commands.iter().map(Vec::len).sum();
    let mut result = vec![0; 0x2100.max(32 + commands_size)];
    put32(&mut result, 0, 0xfeed_facf);
    put32(&mut result, 4, 0x0100_0007);
    put32(&mut result, 8, 3);
    put32(&mut result, 12, 2);
    put32(&mut result, 16, commands.len() as u32);
    put32(&mut result, 20, commands_size as u32);
    put32(&mut result, 24, 1);
    let mut at = 32;
    for command in commands {
        result[at..at + command.len()].copy_from_slice(command);
        at += command.len();
    }
    if at <= 0x1100 {
        result[0x1100..0x1108].copy_from_slice(b"TESTCODE");
    }
    if at <= 0x2000 {
        result[0x2000..0x2100].fill(0x5a);
    }
    result
}

#[test]
fn main_file_offset_is_mapped_through_its_executable_segment_and_zero_fill_is_exact() {
    let original = image(&commands(main_entry()));
    let before = original.clone();
    let plan = parse_macho_image(&original).unwrap();
    assert_eq!(plan.entry_kind, EntryKind::Main);
    assert_eq!(plan.preferred_base, BASE);
    assert_eq!(plan.image_size, 0x9000);
    assert_eq!(plan.header_vaddr, BASE);
    assert_eq!(&plan.segments[0].name, b"__HEADER\0\0\0\0\0\0\0\0");
    assert_eq!(plan.entry_vaddr, BASE + 0x4100);
    assert_eq!(plan.entry_offset, 0x4100);
    // Emulate a caller copying and zero-filling only the declared ranges.
    let mut memory = vec![0xcc; plan.image_size as usize];
    for segment in &plan.segments {
        let start = segment.memory_offset as usize;
        let copied = start + segment.file_size;
        memory[start..copied].copy_from_slice(
            &original[segment.file_offset..segment.file_offset + segment.file_size],
        );
        memory[copied..start + segment.memory_size as usize].fill(0);
    }
    assert_eq!(&memory[0x4100..0x4108], b"TESTCODE");
    assert!(memory[0x7000..0x7100].iter().all(|&byte| byte == 0x5a));
    assert!(memory[0x7100..0x9000].iter().all(|&byte| byte == 0));
    assert!(memory[0x1000..0x4000].iter().all(|&byte| byte == 0xcc));
    assert_eq!(original, before);
}

#[test]
fn unixthread_rip_is_absolute_and_not_a_file_offset() {
    let plan = parse_macho_image(&image(&commands(thread_entry()))).unwrap();
    assert_eq!(plan.entry_kind, EntryKind::UnixThread64);
    assert_eq!(plan.entry_vaddr, BASE + 0x4100);
    assert_eq!(plan.entry_offset, 0x4100);
}

#[test]
fn pagezero_is_an_unmapped_guard_and_non_page_aligned_segments_have_page_rounded_span() {
    let mut list = commands(main_entry());
    list.insert(0, segment(b"__PAGEZERO", 0, BASE, 0, 0, 0));
    put64(&mut list[1], 24, BASE + 0x80);
    let plan = parse_macho_image(&image(&list)).unwrap();
    assert_eq!(plan.segments.len(), 3);
    assert_eq!(plan.preferred_base, BASE);
    assert_eq!(plan.header_vaddr, BASE + 0x80);
    assert_eq!(plan.segments[0].memory_offset, 0x80);
    let mut bad = list.clone();
    put64(&mut bad[0], 32, BASE + 0x1000);
    assert_eq!(parse_macho_image(&image(&bad)), Err(E::SegmentOverlap));
    put32(&mut list[0], 60, 1);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::InvalidSegment));
}

#[test]
fn file_command_and_thread_truncations_fail_without_panics() {
    let bytes = image(&commands(thread_entry()));
    for end in 0..bytes.len() {
        assert!(
            parse_macho_image(&bytes[..end]).is_err(),
            "accepted prefix {end}"
        );
    }
    let mut list = commands(main_entry());
    put32(&mut list[0], 4, 71);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::InvalidCommand));
    let mut bytes = image(&commands(main_entry()));
    put32(&mut bytes, 16, 3);
    assert_eq!(parse_macho_image(&bytes), Err(E::InvalidCommand));
    let mut list = commands(thread_entry());
    put32(&mut list[3], 12, 40);
    assert_eq!(
        parse_macho_image(&image(&list)),
        Err(E::UnsupportedThreadState)
    );
    list[3].truncate(176);
    put32(&mut list[3], 4, 176);
    put32(&mut list[3], 12, 42);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::InvalidCommand));
}

#[test]
fn duplicate_missing_and_outside_executable_entries_are_rejected() {
    let mut list = commands(main_entry());
    list.push(thread_entry());
    assert_eq!(parse_macho_image(&image(&list)), Err(E::DuplicateEntry));
    list.truncate(3);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::MissingEntry));
    for bad in [0, 0x2000, 0x20ff, 0x2100, u64::MAX] {
        let mut list = commands(main_entry());
        put64(&mut list[3], 8, bad);
        assert_eq!(
            parse_macho_image(&image(&list)),
            Err(E::EntryOutsideExecutable)
        );
    }
    for bad in [BASE, BASE + 0x5000, BASE + 0x7000, BASE + 0x8000, u64::MAX] {
        let mut list = commands(thread_entry());
        put64(&mut list[3], 144, bad);
        assert_eq!(
            parse_macho_image(&image(&list)),
            Err(E::EntryOutsideExecutable)
        );
    }
    let mut list = commands(thread_entry());
    put32(&mut list[1], 60, 1); // max execute alone does not permit entry.
    assert_eq!(
        parse_macho_image(&image(&list)),
        Err(E::EntryOutsideExecutable)
    );
}

#[test]
fn segment_virtual_and_file_overlap_overflow_and_invalid_ranges_are_rejected() {
    let mut list = commands(main_entry());
    put64(&mut list[2], 24, BASE + 0x4fff);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::SegmentOverlap));
    let mut list = commands(main_entry());
    put64(&mut list[2], 40, 0x1fff);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::SegmentOverlap));
    for (offset, value, error) in [
        (24, u64::MAX - 1, E::Overflow),
        (40, u64::MAX, E::Overflow),
        (40, 0x2100, E::Truncated),
        (48, 0x2001, E::InvalidSegment),
        (32, 0, E::InvalidSegment),
    ] {
        let mut list = commands(main_entry());
        put64(&mut list[2], offset, value);
        assert_eq!(parse_macho_image(&image(&list)), Err(error));
    }
    let mut list = commands(main_entry());
    put32(&mut list[2], 60, 7);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::InvalidSegment));
}

fn section(name: &[u8], addr: u64, size: u64, fileoff: u32, kind: u32) -> Vec<u8> {
    let mut result = vec![0; 80];
    result[..name.len()].copy_from_slice(name);
    result[16..22].copy_from_slice(b"__DATA");
    put64(&mut result, 32, addr);
    put64(&mut result, 40, size);
    put32(&mut result, 48, fileoff);
    put32(&mut result, 64, kind);
    result
}

fn with_sections(sections: Vec<Vec<u8>>) -> Vec<Vec<u8>> {
    let mut list = commands(main_entry());
    put32(&mut list[2], 64, sections.len() as u32);
    for section in sections {
        list[2].extend(section);
    }
    let size = list[2].len() as u32;
    put32(&mut list[2], 4, size);
    list
}

#[test]
fn sections_follow_segment_copy_mapping_and_zero_fill_tail() {
    let data = section(b"__data", BASE + 0x7000, 0x100, 0x2000, 0);
    let zero = section(b"__bss", BASE + 0x7100, 0x1f00, 0, 1);
    assert!(parse_macho_image(&image(&with_sections(vec![data.clone(), zero.clone()]))).is_ok());
    let mut bad = zero.clone();
    put64(&mut bad, 32, BASE + 0x7080);
    assert_eq!(
        parse_macho_image(&image(&with_sections(vec![bad]))),
        Err(E::InvalidSection)
    );
    let mut bad = data.clone();
    put32(&mut bad, 48, 0x2001);
    assert_eq!(
        parse_macho_image(&image(&with_sections(vec![bad]))),
        Err(E::InvalidSection)
    );
    let mut bad = data.clone();
    put32(&mut bad, 60, 1);
    assert_eq!(
        parse_macho_image(&image(&with_sections(vec![bad]))),
        Err(E::UnsupportedRelocations)
    );
    let mut bad = data.clone();
    put64(&mut bad, 40, u64::MAX);
    assert_eq!(
        parse_macho_image(&image(&with_sections(vec![bad]))),
        Err(E::Overflow)
    );
    let mut bad = data.clone();
    put32(&mut bad, 52, 64);
    assert_eq!(
        parse_macho_image(&image(&with_sections(vec![bad]))),
        Err(E::InvalidSection)
    );
    assert_eq!(
        parse_macho_image(&image(&with_sections(vec![data.clone(), data]))),
        Err(E::SectionOverlap)
    );
}

#[test]
fn unsupported_format_cpu_filetypes_and_execution_mechanisms_are_explicit() {
    for (offset, value, error) in [
        (0, 0xcafe_babe, E::UnsupportedFormat),
        (0, 0xcefa_edfe, E::UnsupportedFormat),
        (4, 0x0100_000c, E::UnsupportedCpu),
        (8, 8, E::UnsupportedCpu),
        (12, 0xc, E::UnsupportedFileType),
        (12, 6, E::UnsupportedFileType),
        (24, 0x20_0000, E::UnsupportedFlags),
        (24, 4, E::UnsupportedFlags),
        (28, 1, E::InvalidHeader),
    ] {
        let mut bytes = image(&commands(main_entry()));
        put32(&mut bytes, offset, value);
        assert_eq!(parse_macho_image(&bytes), Err(error));
    }
    for kind in [0xb, 0xc, 0xe, 0x22, 0x8000_0034, 0x8000_0035, 0x1234_5678] {
        let mut list = commands(main_entry());
        list.push(command(kind, 8));
        assert_eq!(parse_macho_image(&image(&list)), Err(E::UnsupportedCommand));
    }
    let mut list = commands(main_entry());
    put64(&mut list[3], 16, 0x4000);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::UnsupportedStack));
    let mut list = commands(main_entry());
    put32(&mut list[1], 68, 1);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::UnsupportedFlags));
}

#[test]
fn command_segment_section_and_image_span_limits_are_enforced() {
    let mut bytes = image(&commands(main_entry()));
    put32(&mut bytes, 16, MAX_COMMANDS as u32 + 1);
    assert_eq!(parse_macho_image(&bytes), Err(E::LimitExceeded));
    let mut list = commands(main_entry());
    list.resize(MAX_SEGMENTS + 2, list[1].clone());
    assert_eq!(parse_macho_image(&image(&list)), Err(E::LimitExceeded));
    let mut list = commands(main_entry());
    put32(&mut list[1], 64, MAX_SECTIONS as u32 + 1);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::LimitExceeded));
    let mut list = commands(main_entry());
    put64(&mut list[2], 24, BASE + MAX_IMAGE_SIZE);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::LimitExceeded));
    let mut list = commands(main_entry());
    put64(&mut list[2], 24, u64::MAX - 0x2fff);
    put64(&mut list[2], 32, 0x2ffe);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::Overflow));
}

#[test]
fn metadata_ranges_and_header_mapping_are_bounded() {
    let mut list = commands(main_entry());
    let mut symbols = command(2, 24);
    put32(&mut symbols, 8, 0x2000);
    put32(&mut symbols, 12, 1);
    put32(&mut symbols, 16, 0x2010);
    put32(&mut symbols, 20, 16);
    list.push(symbols);
    list.push(command(0x1b, 24));
    list.push(command(0x32, 24));
    assert!(parse_macho_image(&image(&list)).is_ok());
    put32(&mut list[4], 12, u32::MAX);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::Truncated));
    let mut list = commands(main_entry());
    put64(&mut list[0], 48, 8);
    assert_eq!(parse_macho_image(&image(&list)), Err(E::InvalidHeader));
}
