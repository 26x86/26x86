use nextcore_core::xnu_boot_args::{
    encode_boot_args, encode_fileset_boot_args, BootArgsError, XnuBootArgsInput,
    XnuFilesetBootArgsInput, BOOT_ARGS_SIZE,
};

fn input() -> XnuBootArgsInput<'static> {
    XnuBootArgsInput {
        memory_map_phys: 0x0030_0000,
        memory_map_size: 96,
        memory_map_descriptor_size: 48,
        memory_map_descriptor_version: 1,
        device_tree_phys: 0x0031_0000,
        device_tree_size: 48,
        kernel_phys: 0x0010_0000,
        kernel_size: 0x0022_0000,
        physical_memory_size: 0x0000_0002_0000_0000,
        efi_system_table_phys: 0x07f0_0000,
        command_line: "-v keepsyms=1",
    }
}

#[test]
fn pinned_public_offsets_are_little_endian_and_reserved_bytes_stay_zero() {
    let bytes = encode_boot_args(&input()).unwrap();
    assert_eq!(bytes.len(), BOOT_ARGS_SIZE);
    let mut golden = [0u8; 4096];
    golden[2] = 2;
    golden[4] = 64;
    golden[8..21].copy_from_slice(b"-v keepsyms=1");
    golden[0x408..0x418].copy_from_slice(&[
        0x00, 0x00, 0x30, 0x00, // map physical
        0x60, 0x00, 0x00, 0x00, // map bytes
        0x30, 0x00, 0x00, 0x00, // descriptor stride
        0x01, 0x00, 0x00, 0x00, // descriptor version
    ]);
    golden[0x430..0x440].copy_from_slice(&[
        0x00, 0x00, 0x31, 0x00, // DT physical
        0x30, 0x00, 0x00, 0x00, // DT bytes
        0x00, 0x00, 0x10, 0x00, // kernel physical
        0x00, 0x00, 0x22, 0x00, // protected covered bytes
    ]);
    golden[0x450..0x454].copy_from_slice(&[0, 0, 0xf0, 7]);
    golden[0x478..0x480].copy_from_slice(&[0, 0, 0, 0, 2, 0, 0, 0]);
    assert_eq!(bytes, golden);
}

#[test]
fn maximum_command_leaves_one_nul_before_memory_map() {
    let command = "x".repeat(1023);
    let mut value = input();
    value.command_line = &command;
    let bytes = encode_boot_args(&value).unwrap();
    assert!(bytes[8..0x407].iter().all(|&b| b == b'x'));
    assert_eq!(bytes[0x407], 0);
    assert_eq!(&bytes[0x408..0x40c], &[0, 0, 0x30, 0]);
}

#[test]
fn rejects_command_truncation_nul_and_non_ascii() {
    for command in ["x".repeat(1024), "a\0b".into(), "커널".into(), "😀".into()] {
        let mut value = input();
        value.command_line = &command;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidCommandLine)
        );
    }
}

#[test]
fn requires_actual_efi_descriptor_shape_without_silently_repacking() {
    for stride in [0, 8, 32, 39, 41, 44] {
        let mut value = input();
        value.memory_map_descriptor_size = stride;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidMemoryMap)
        );
    }
    for version in [0, 2, u32::MAX] {
        let mut value = input();
        value.memory_map_descriptor_version = version;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidMemoryMap)
        );
    }
    for size in [0, 47, 49, u64::MAX] {
        let mut value = input();
        value.memory_map_size = size;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidMemoryMap)
        );
    }
    let mut value = input();
    value.memory_map_descriptor_size = 40;
    value.memory_map_size = 80;
    assert!(encode_boot_args(&value).is_ok());
}

#[test]
fn refuses_null_unaligned_high_and_wrapping_references() {
    for address in [0, 0x0030_0001, 0x1_0030_0000, 0xffff_fff8, u64::MAX - 7] {
        let mut value = input();
        value.memory_map_phys = address;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidMemoryMap)
        );
    }
    for address in [0, 0x0031_0001, 0x1_0031_0000, 0xffff_fffc, u64::MAX - 3] {
        let mut value = input();
        value.device_tree_phys = address;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidDeviceTree)
        );
    }
    for size in [0, 4, 47, 0x1_0000_0000, u64::MAX - 3] {
        let mut value = input();
        value.device_tree_size = size;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidDeviceTree)
        );
    }
}

#[test]
fn prevents_early_allocator_reusing_map_or_tree_and_rejects_overlap() {
    let mut value = input();
    value.kernel_size = 0x0021_0000;
    assert_eq!(
        encode_boot_args(&value),
        Err(BootArgsError::HandoffOutsideKernel)
    );
    value = input();
    value.device_tree_phys = 0x000f_0000;
    assert_eq!(
        encode_boot_args(&value),
        Err(BootArgsError::HandoffOutsideKernel)
    );
    value = input();
    value.memory_map_phys = 0x000f_0000;
    assert_eq!(
        encode_boot_args(&value),
        Err(BootArgsError::HandoffOutsideKernel)
    );
    value = input();
    value.device_tree_phys = value.memory_map_phys + 4;
    assert_eq!(
        encode_boot_args(&value),
        Err(BootArgsError::OverlappingHandoff)
    );
    value.device_tree_phys = value.memory_map_phys + value.memory_map_size;
    assert!(
        encode_boot_args(&value).is_ok(),
        "adjacent half-open ranges are valid"
    );
}

#[test]
fn kernel_cursor_must_not_overflow_when_rounded_to_page() {
    for (base, size) in [
        (0, 0x0032_0000),
        (0x0010_0001, 0x0022_0000),
        (0x0010_0000, 0),
        (0xffff_f000, 4096),
        (0xffff_f000, 1),
        (0x0010_0000, u64::MAX),
        (0x1_0010_0000, 0x0022_0000),
    ] {
        let mut value = input();
        value.kernel_phys = base;
        value.kernel_size = size;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidKernelRange)
        );
    }
    let mut value = input();
    value.kernel_size -= 1;
    assert!(
        encode_boot_args(&value).is_ok(),
        "covered size may end inside a page"
    );
}

#[test]
fn physical_ram_can_exceed_four_gib_but_cannot_overflow_early_physmap_addition() {
    assert!(encode_boot_args(&input()).is_ok());
    for size in [0, u64::MAX, u64::MAX - 0xffff_ffff] {
        let mut value = input();
        value.physical_memory_size = size;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidPhysicalMemory)
        );
    }
}

#[test]
fn efi_pointer_is_not_forced_into_kernel_arena_but_must_fit_its_wire_field() {
    for address in [0, 0x07f0_0001, 0x1_0000_0000, u64::MAX] {
        let mut value = input();
        value.efi_system_table_phys = address;
        assert_eq!(
            encode_boot_args(&value),
            Err(BootArgsError::InvalidEfiSystemTable)
        );
    }
    assert!(encode_boot_args(&input()).is_ok());
}

#[test]
fn errors_are_fixed_log_tokens() {
    assert_eq!(
        BootArgsError::InvalidCommandLine.to_string(),
        "INVALID_COMMAND_LINE"
    );
    assert_eq!(
        BootArgsError::HandoffOutsideKernel.to_string(),
        "HANDOFF_OUTSIDE_KERNEL"
    );
}

fn fileset() -> XnuFilesetBootArgsInput<'static> {
    XnuFilesetBootArgsInput {
        common: input(),
        collection_header_phys: 0x0020_0000,
        collection_header_size: 512,
        kernel_slide: 0x0360_0000,
    }
}

#[test]
fn fileset_extension_matches_independently_compiled_public_c_layout() {
    // C offsetof receipt: artifacts/kc-bootargs-contract-20260908.md.
    let value = fileset();
    let mut expected = encode_boot_args(&value.common).unwrap();
    let actual = encode_fileset_boot_args(&value).unwrap();
    expected[0..2].copy_from_slice(&[1, 0]);
    expected[1108..1112].copy_from_slice(&[0, 0, 0x60, 3]);
    expected[1256..1264].copy_from_slice(&[0, 0, 0x20, 0, 0, 0, 0, 0]);
    assert_eq!(actual, expected);
    let standalone = encode_boot_args(&value.common).unwrap();
    assert_eq!(&standalone[0..2], &[0, 0]);
    assert_eq!(&standalone[1108..1112], &[0; 4]);
    assert_eq!(&standalone[1256..1264], &[0; 8]);
}

#[test]
fn fileset_rejects_virtual_null_unaligned_overflow_and_unowned_header_ranges() {
    for (address, size) in [
        (0, 512),
        (0x0020_0001, 512),
        (0xffff_ff80_0020_0000, 512),
        (0xffff_fff8, 32),
        (u64::MAX - 7, 32),
        (0x0020_0000, 0),
        (0x0020_0000, 31),
        (0x0020_0000, u64::MAX),
        (0x000f_fff8, 32),
        (0x0032_0000 - 24, 32),
    ] {
        let mut value = fileset();
        value.collection_header_phys = address;
        value.collection_header_size = size;
        assert_eq!(
            encode_fileset_boot_args(&value),
            Err(BootArgsError::InvalidCollectionHeader)
        );
    }
}

#[test]
fn fileset_checks_full_header_extent_against_map_and_tree() {
    for (address, size) in [
        (0x0030_0000, 32),
        (0x0030_0000 - 24, 32),
        (0x0030_0000 + 88, 32),
        (0x0031_0000, 32),
        (0x002f_0000, 0x20000),
    ] {
        let mut value = fileset();
        value.collection_header_phys = address;
        value.collection_header_size = size;
        assert_eq!(
            encode_fileset_boot_args(&value),
            Err(BootArgsError::OverlappingHandoff)
        );
    }
    for address in [0x0030_0000 - 32, 0x0030_0000 + 96, 0x0032_0000 - 32] {
        let mut value = fileset();
        value.collection_header_phys = address;
        value.collection_header_size = 32;
        assert!(encode_fileset_boot_args(&value).is_ok());
    }
}

#[test]
fn fileset_keeps_common_validation_and_never_truncates_slide() {
    let mut value = fileset();
    value.common.memory_map_descriptor_version = 2;
    assert_eq!(
        encode_fileset_boot_args(&value),
        Err(BootArgsError::InvalidMemoryMap)
    );
    for slide in [0, 0x200000, u32::MAX] {
        let mut value = fileset();
        value.kernel_slide = slide;
        let bytes = encode_fileset_boot_args(&value).unwrap();
        assert_eq!(&bytes[1108..1112], &slide.to_le_bytes());
    }
}
