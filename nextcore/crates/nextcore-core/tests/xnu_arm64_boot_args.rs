use nextcore_core::flat_dt::{self, FlatNode, FlatProperty};
use nextcore_core::xnu_arm64_boot_args::{
    encode_arm64_boot_args, Arm64BootArgsError as Error, Arm64BootArgsInput, Arm64BootVideo,
    ARM64_BOOT_ARGS_SIZE, VMAPPLE_PAGE_SIZE,
};

const RAM: u64 = 0x4000_0000;
const MEMORY: u64 = 0x4000_0000;
const KERNEL: u64 = RAM + 0x0200_0000;
const PAGE: u64 = VMAPPLE_PAGE_SIZE;

fn chosen(base: Vec<u8>, size: Vec<u8>) -> FlatNode {
    FlatNode {
        name: "chosen".into(),
        properties: vec![
            FlatProperty {
                name: "dram-base".into(),
                value: base,
            },
            FlatProperty {
                name: "dram-size".into(),
                value: size,
            },
        ],
        children: vec![],
    }
}

fn tree(child: FlatNode) -> Vec<u8> {
    flat_dt::encode(&FlatNode {
        name: "device-tree".into(),
        properties: vec![],
        children: vec![child],
    })
    .unwrap()
}

fn dt() -> Vec<u8> {
    tree(chosen(
        RAM.to_le_bytes().to_vec(),
        MEMORY.to_le_bytes().to_vec(),
    ))
}

fn input(bytes: &[u8]) -> Arm64BootArgsInput<'_> {
    Arm64BootArgsInput {
        physical_base: RAM,
        virtual_base: 0xffff_ff80_0000_0000,
        memory_size: MEMORY,
        actual_memory_size: MEMORY,
        top_of_kernel_data: KERNEL + 4 * PAGE,
        kernel_phys: KERNEL,
        kernel_size: 2 * PAGE,
        boot_args_phys: KERNEL + 2 * PAGE,
        device_tree_phys: KERNEL + 2 * PAGE + 4096,
        device_tree: bytes,
        command_line: "-v serial=3",
        machine_type: 42,
        boot_flags: 1,
        video: Arm64BootVideo::default(),
    }
}

fn u64_at(bytes: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(bytes[offset..offset + 8].try_into().unwrap())
}

#[test]
fn public_layout_and_pa_kva_roles_are_distinct() {
    let dt = dt();
    let mut input = input(&dt);
    input.video = Arm64BootVideo {
        base_address: 0x1234_0000,
        display: 2,
        row_bytes: 4096,
        width: 1024,
        height: 768,
        depth: 32,
    };
    let encoded = encode_arm64_boot_args(&input).unwrap();
    let bytes = encoded.as_bytes();
    assert_eq!(bytes.len(), ARM64_BOOT_ARGS_SIZE);
    assert_eq!(&bytes[..4], &[2, 0, 2, 0]);
    // Offsets independently checked by the C LP64/Darwin ARM64 layout fixture.
    assert_eq!(u64_at(bytes, 8), input.virtual_base);
    assert_eq!(u64_at(bytes, 16), RAM);
    assert_eq!(u64_at(bytes, 24), MEMORY);
    assert_eq!(u64_at(bytes, 32), input.top_of_kernel_data);
    assert_eq!(u64_at(bytes, 40), 0x1234_0000);
    assert_eq!(u64_at(bytes, 48), 2);
    assert_eq!(u64_at(bytes, 56), 4096);
    assert_eq!(u64_at(bytes, 64), 1024);
    assert_eq!(u64_at(bytes, 72), 768);
    assert_eq!(u64_at(bytes, 80), 32);
    assert_eq!(&bytes[88..92], &42u32.to_le_bytes());
    let dt_virtual = input.virtual_base + (input.device_tree_phys - RAM);
    assert_eq!(u64_at(bytes, 96), dt_virtual);
    assert_eq!(encoded.device_tree_virtual_address(), dt_virtual);
    assert_eq!(encoded.physical_address(), input.boot_args_phys);
    assert_ne!(encoded.physical_address(), dt_virtual);
    assert_eq!(&bytes[104..108], &(dt.len() as u32).to_le_bytes());
    assert_eq!(&bytes[108..120], b"-v serial=3\0");
    assert!(bytes[120..1136].iter().all(|&b| b == 0));
    assert_eq!(u64_at(bytes, 1136), 1);
    assert_eq!(u64_at(bytes, 1144), MEMORY);
    for range in [4..8, 92..96] {
        assert!(bytes[range].iter().all(|&b| b == 0));
    }
    assert!(!encoded.execution_ready());
}

#[test]
fn command_line_limit_preserves_nul_and_rejects_lossy_inputs() {
    let dt = dt();
    let mut value = input(&dt);
    let maximum = "x".repeat(1023);
    value.command_line = &maximum;
    let encoded = encode_arm64_boot_args(&value).unwrap();
    assert_eq!(encoded.as_bytes()[1130], b'x');
    assert_eq!(encoded.as_bytes()[1131], 0);
    for invalid in ["x".repeat(1024), "a\0b".into(), "한글".into()] {
        let mut value = input(&dt);
        value.command_line = &invalid;
        assert_eq!(
            encode_arm64_boot_args(&value).unwrap_err(),
            Error::InvalidCommandLine
        );
    }
}

#[test]
fn flags_outside_public_subset_are_rejected() {
    let dt = dt();
    let mut value = input(&dt);
    value.boot_flags = 2;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::UnsupportedBootFlags
    );
}

#[test]
fn managed_ram_overflow_zero_and_alignment_are_rejected() {
    let dt = dt();
    for (base, size) in [
        (RAM, 0),
        (RAM + 1, MEMORY),
        (RAM, MEMORY + 1),
        (u64::MAX - PAGE + 1, 2 * PAGE),
    ] {
        let mut value = input(&dt);
        value.physical_base = base;
        value.memory_size = size;
        assert_eq!(
            encode_arm64_boot_args(&value).unwrap_err(),
            Error::InvalidMemoryRange
        );
    }
}

#[test]
fn virtual_window_overflow_and_alignment_are_rejected() {
    let dt = dt();
    for base in [u64::MAX - PAGE + 1, input(&dt).virtual_base + 8] {
        let mut value = input(&dt);
        value.virtual_base = base;
        assert_eq!(
            encode_arm64_boot_args(&value).unwrap_err(),
            Error::InvalidVirtualRange
        );
    }
}

#[test]
fn occupied_top_must_be_inside_managed_ram_and_page_aligned() {
    let dt = dt();
    for top in [RAM, RAM + MEMORY, KERNEL + 4 * PAGE + 8] {
        let mut value = input(&dt);
        value.top_of_kernel_data = top;
        assert_eq!(
            encode_arm64_boot_args(&value).unwrap_err(),
            Error::InvalidOccupiedTop
        );
    }
}

#[test]
fn kernel_range_is_checked_before_handoff_layout() {
    let dt = dt();
    for (base, size) in [
        (KERNEL + 8, PAGE),
        (RAM - PAGE, PAGE),
        (KERNEL, 0),
        (KERNEL, 5 * PAGE),
        (KERNEL, u64::MAX),
    ] {
        let mut value = input(&dt);
        value.kernel_phys = base;
        value.kernel_size = size;
        assert_eq!(
            encode_arm64_boot_args(&value).unwrap_err(),
            Error::InvalidKernelRange
        );
    }
}

#[test]
fn argument_alignment_overflow_and_extent_are_checked() {
    let dt = dt();
    for address in [KERNEL + 2 * PAGE + 1, u64::MAX - 7] {
        let mut value = input(&dt);
        value.boot_args_phys = address;
        assert_eq!(
            encode_arm64_boot_args(&value).unwrap_err(),
            Error::InvalidArgumentRange
        );
    }
    let mut value = input(&dt);
    value.boot_args_phys = value.top_of_kernel_data;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::HandoffOutsideOccupiedMemory
    );
}

#[test]
fn actual_dt_bytes_are_validated_not_just_their_length() {
    let dt = dt();
    let mut malformed = dt.clone();
    malformed[..4].copy_from_slice(&u32::MAX.to_le_bytes());
    let mut trailing = dt.clone();
    trailing.extend_from_slice(&[0; 4]);
    for bytes in [&[][..], &dt[..dt.len() - 4], &malformed, &trailing] {
        assert_eq!(
            encode_arm64_boot_args(&input(bytes)).unwrap_err(),
            Error::InvalidDeviceTree
        );
    }
    let mut value = input(&dt);
    value.device_tree_phys += 1;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::InvalidDeviceTree
    );
    value.device_tree_phys = u64::MAX - 3;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::InvalidDeviceTree
    );
}

#[test]
fn all_handoff_pairs_must_be_disjoint() {
    let dt = dt();
    let mut value = input(&dt);
    value.device_tree_phys = value.boot_args_phys;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::OverlappingHandoff
    );
    value = input(&dt);
    value.device_tree_phys = KERNEL;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::OverlappingHandoff
    );
    value = input(&dt);
    value.boot_args_phys = KERNEL;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::OverlappingHandoff
    );
}

#[test]
fn disjoint_handoff_before_kernel_is_still_rejected() {
    let dt = dt();
    let mut value = input(&dt);
    value.device_tree_phys = RAM;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::HandoffOutsideOccupiedMemory
    );
    value = input(&dt);
    value.boot_args_phys = RAM;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::HandoffOutsideOccupiedMemory
    );
}

#[test]
fn touching_ranges_and_exact_occupied_end_are_valid() {
    let dt = dt();
    let mut value = input(&dt);
    value.device_tree_phys = value.boot_args_phys + ARM64_BOOT_ARGS_SIZE as u64;
    encode_arm64_boot_args(&value).unwrap();
    value.device_tree_phys = value.top_of_kernel_data - dt.len() as u64;
    encode_arm64_boot_args(&value).unwrap();
    value = input(&dt);
    value.boot_args_phys = value.top_of_kernel_data - ARM64_BOOT_ARGS_SIZE as u64;
    encode_arm64_boot_args(&value).unwrap();
}

#[test]
fn dram_properties_must_exist_at_the_public_chosen_path() {
    let mut node = chosen(RAM.to_le_bytes().to_vec(), MEMORY.to_le_bytes().to_vec());
    node.properties.pop();
    assert_eq!(
        encode_arm64_boot_args(&input(&tree(node))).unwrap_err(),
        Error::MissingDramProperties
    );
    let bytes = tree(FlatNode {
        name: "wrapper".into(),
        properties: vec![],
        children: vec![chosen(
            RAM.to_le_bytes().to_vec(),
            MEMORY.to_le_bytes().to_vec(),
        )],
    });
    assert_eq!(
        encode_arm64_boot_args(&input(&bytes)).unwrap_err(),
        Error::MissingDramProperties
    );
}

#[test]
fn dram_values_must_match_contain_and_not_wrap() {
    for (base, size) in [
        (RAM, 0),
        (RAM + PAGE, MEMORY),
        (RAM, MEMORY - PAGE),
        (u64::MAX - PAGE + 1, 2 * PAGE),
    ] {
        let bytes = tree(chosen(
            base.to_le_bytes().to_vec(),
            size.to_le_bytes().to_vec(),
        ));
        assert_eq!(
            encode_arm64_boot_args(&input(&bytes)).unwrap_err(),
            Error::InvalidDramProperties
        );
    }
    let bytes = tree(chosen(RAM.to_le_bytes().to_vec(), vec![0; 4]));
    assert_eq!(
        encode_arm64_boot_args(&input(&bytes)).unwrap_err(),
        Error::InvalidDramProperties
    );
    let bytes = dt();
    let mut value = input(&bytes);
    value.actual_memory_size -= PAGE;
    assert_eq!(
        encode_arm64_boot_args(&value).unwrap_err(),
        Error::InvalidDramProperties
    );
}

#[test]
fn managed_window_may_be_a_subset_of_actual_dram() {
    let dt = dt();
    let mut value = input(&dt);
    value.physical_base += PAGE;
    value.virtual_base += PAGE;
    value.memory_size -= 2 * PAGE;
    let encoded = encode_arm64_boot_args(&value).unwrap();
    assert_eq!(u64_at(encoded.as_bytes(), 24), MEMORY - 2 * PAGE);
    assert_eq!(u64_at(encoded.as_bytes(), 1144), MEMORY);
}
