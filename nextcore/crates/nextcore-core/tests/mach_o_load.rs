use nextcore_core::error::CoreError;
use nextcore_core::mach_o::{calculate_entry_address, MachOLoader};

const MH_MAGIC_64: u32 = 0xFEEDFACF;
const CPU_TYPE_X86_64: u32 = 0x01000007;
const MH_EXECUTE: u32 = 2;
const LC_SEGMENT_64: u32 = 0x19;
const LC_MAIN: u32 = 0x8000_0028;

fn build_minimal_header(ncmds: u32, sizeofcmds: u32) -> Vec<u8> {
    let mut h = Vec::with_capacity(32);
    h.extend_from_slice(&MH_MAGIC_64.to_le_bytes());
    h.extend_from_slice(&CPU_TYPE_X86_64.to_le_bytes());
    h.extend_from_slice(&0u32.to_le_bytes()); // cpusubtype
    h.extend_from_slice(&MH_EXECUTE.to_le_bytes());
    h.extend_from_slice(&ncmds.to_le_bytes());
    h.extend_from_slice(&sizeofcmds.to_le_bytes());
    h.extend_from_slice(&0u32.to_le_bytes()); // flags
    h.extend_from_slice(&0u32.to_le_bytes()); // reserved
    h
}

fn build_segment_cmd(
    segname: &[u8; 16],
    vmaddr: u64,
    vmsize: u64,
    fileoff: u64,
    filesize: u64,
) -> Vec<u8> {
    let mut c = Vec::with_capacity(72);
    c.extend_from_slice(&LC_SEGMENT_64.to_le_bytes());
    c.extend_from_slice(&72u32.to_le_bytes()); // cmdsize
    c.extend_from_slice(segname);
    c.extend_from_slice(&vmaddr.to_le_bytes());
    c.extend_from_slice(&vmsize.to_le_bytes());
    c.extend_from_slice(&fileoff.to_le_bytes());
    c.extend_from_slice(&filesize.to_le_bytes());
    c.extend_from_slice(&7u32.to_le_bytes()); // maxprot rwx
    c.extend_from_slice(&7u32.to_le_bytes()); // initprot
    c.extend_from_slice(&0u32.to_le_bytes()); // nsects
    c.extend_from_slice(&0u32.to_le_bytes()); // flags
    c
}

fn build_main_cmd(entryoff: u64) -> Vec<u8> {
    let mut c = Vec::with_capacity(24);
    c.extend_from_slice(&LC_MAIN.to_le_bytes());
    c.extend_from_slice(&24u32.to_le_bytes()); // cmdsize
    c.extend_from_slice(&entryoff.to_le_bytes());
    c.extend_from_slice(&0u64.to_le_bytes()); // stacksize
    c
}

fn minimal_segment_binary() -> Vec<u8> {
    // filesize must be within the actual buffer (goblin slices segment data
    // by fileoff..fileoff+filesize). 104 == 32 header + 72 segment command.
    let seg = build_segment_cmd(
        b"__TEXT\0\0\0\0\0\0\0\0\0\0",
        0x100000000,
        0x1000,
        0,
        104,
    );
    let mut bin = build_minimal_header(1, 72);
    bin.extend_from_slice(&seg);
    bin
}

#[test]
fn test_parse_header() {
    let bin = minimal_segment_binary();
    let h = MachOLoader::parse_header(&bin).expect("minimal 64-bit mach-o should parse");

    assert_eq!(h.magic, MH_MAGIC_64);
    assert_eq!(h.filetype, MH_EXECUTE);
    assert_eq!(h.cpu_type, CPU_TYPE_X86_64);
    assert_eq!(h.ncmds, 1);
    assert_eq!(h.sizeofcmds, 72);

    assert_eq!(h.segments.len(), 1, "one __TEXT segment expected");
    assert_eq!(h.segments[0].name, "__TEXT");
    assert_eq!(h.segments[0].vmaddr, 0x100000000);
    assert_eq!(h.segments[0].vmsize, 0x1000);
    assert_eq!(h.segments[0].fileoff, 0);
    assert_eq!(h.segments[0].filesize, 104);

    // No LC_MAIN present -> entry_offset defaults to 0.
    assert_eq!(h.entry_offset, 0, "no LC_MAIN means entry_offset=0");
}

#[test]
fn test_bad_magic() {
    let mut bin = minimal_segment_binary();
    bin[0] = 0x00; // corrupt the magic
    let err = MachOLoader::parse_header(&bin).expect_err("corrupt magic must fail");
    assert!(
        matches!(err, CoreError::MachO(_)),
        "expected MachO error, got {err:?}"
    );
}

#[test]
fn test_calculate_entry() {
    // Binary without LC_MAIN: entry = base + 0.
    let no_main = minimal_segment_binary();
    let h = MachOLoader::parse_header(&no_main).expect("parse no-main");
    assert_eq!(calculate_entry_address(&h).unwrap(), 0x100000000);

    // Binary with LC_MAIN (entryoff=0x1F00).
    const ENTRYOFF: u64 = 0x1F00;
    let text = build_segment_cmd(
        b"__TEXT\0\0\0\0\0\0\0\0\0\0",
        0x100000000,
        0x3000,
        0,
        128, // 32 header + 72 segment + 24 LC_MAIN
    );
    let main = build_main_cmd(ENTRYOFF);
    let mut bin = build_minimal_header(2, 72 + 24);
    bin.extend_from_slice(&text);
    bin.extend_from_slice(&main);

    let h = MachOLoader::parse_header(&bin).expect("parse with LC_MAIN");
    assert_eq!(h.segments.len(), 1);
    assert_eq!(h.entry_offset, ENTRYOFF);
    assert_eq!(
        calculate_entry_address(&h).unwrap(),
        0x100000000 + ENTRYOFF,
        "entry address must account for LC_MAIN entryoff"
    );
}
