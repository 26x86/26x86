use nextcore_core::apfs_jumpstart::{
    extract_jumpstart, fletcher64_checksum, JumpstartDriver, JumpstartError, JumpstartLimits,
    ReadAt,
};
use std::collections::BTreeMap;

const BS: usize = 4096;
const PARTITION_BYTES: u64 = 1024 * 1024;

#[derive(Clone)]
struct Source {
    blocks: BTreeMap<u64, Vec<u8>>,
    len: u64,
    reads: Vec<(u64, usize)>,
    fail_on: Option<usize>,
    changed_prefix: bool,
}

impl ReadAt for Source {
    type Error = &'static str;

    fn read_exact_at(&mut self, offset: u64, out: &mut [u8]) -> Result<(), Self::Error> {
        // A callback outside this bound fails the test, not just the parser call.
        assert!(offset.checked_add(out.len() as u64).unwrap() <= self.len);
        assert!(out.len() <= 65536);
        self.reads.push((offset, out.len()));
        if self.fail_on == Some(self.reads.len()) {
            return Err("device failed or short read");
        }
        let (base, bytes) = self.blocks.range(..=offset).next_back().ok_or("EOF")?;
        let within = (offset - base) as usize;
        out.copy_from_slice(bytes.get(within..within + out.len()).ok_or("EOF")?);
        if self.changed_prefix && self.reads.len() == 2 {
            out[8] ^= 1;
        }
        Ok(())
    }
}

fn put32(bytes: &mut [u8], at: usize, value: u32) {
    bytes[at..at + 4].copy_from_slice(&value.to_le_bytes());
}
fn put64(bytes: &mut [u8], at: usize, value: u64) {
    bytes[at..at + 8].copy_from_slice(&value.to_le_bytes());
}

// Independent positional-weight formulation, also used by layout_fixture.c.
fn seal(block: &mut [u8]) {
    let modulus = u32::MAX as u128;
    let count = (block.len() - 8) / 4;
    let (mut a, mut b) = (0_u128, 0_u128);
    for (index, bytes) in block[8..].chunks_exact(4).enumerate() {
        let word = u32::from_le_bytes(bytes.try_into().unwrap()) as u128;
        a += word;
        b += (count - index) as u128 * word;
    }
    let low = modulus - ((a + b) % modulus);
    let high = modulus - ((a + low) % modulus);
    put64(block, 0, ((high as u64) << 32) | low as u64);
}

fn fixture(block_size: usize) -> Source {
    let mut nx = vec![0; block_size];
    put64(&mut nx, 8, 1); // An ephemeral object copied to physical block zero.
    put64(&mut nx, 16, 1);
    put32(&mut nx, 24, 0x8000_0001);
    put32(&mut nx, 32, 0x4253_584e);
    put32(&mut nx, 36, block_size as u32);
    put64(&mut nx, 40, PARTITION_BYTES / block_size as u64);
    put64(&mut nx, 64, 2);
    nx[72..88].copy_from_slice(b"Authored-UUID-01");
    put64(&mut nx, 1272, 2);
    seal(&mut nx);
    let mut jump = vec![0; block_size];
    put64(&mut jump, 8, 2);
    put64(&mut jump, 16, 1);
    put32(&mut jump, 24, 0x4000_0014);
    put32(&mut jump, 32, 0x5244_534a);
    put32(&mut jump, 36, 1);
    put32(&mut jump, 40, block_size as u32 + 19);
    put32(&mut jump, 44, 2);
    put64(&mut jump, 176, 5); // Order differs from physical address ordering.
    put64(&mut jump, 184, 1);
    put64(&mut jump, 192, 4);
    put64(&mut jump, 200, 1);
    seal(&mut jump);
    Source {
        blocks: BTreeMap::from([
            (0, nx),
            (2 * block_size as u64, jump),
            (5 * block_size as u64, vec![0x31; block_size]),
            (4 * block_size as u64, vec![0xa7; block_size]),
        ]),
        len: PARTITION_BYTES,
        reads: Vec::new(),
        fail_on: None,
        changed_prefix: false,
    }
}

fn edit(source: &mut Source, jump: bool, change: impl FnOnce(&mut [u8])) {
    let offset = if jump { (2 * BS) as u64 } else { 0 };
    let block = source.blocks.get_mut(&offset).unwrap();
    change(block);
    seal(block);
}

fn extract(source: &mut Source) -> Result<JumpstartDriver, JumpstartError<&'static str>> {
    extract_jumpstart(source, source.len, JumpstartLimits::default())
}

#[test]
fn ordered_extents_return_exact_file_size_for_small_and_large_blocks() {
    for size in [4096, 65536] {
        let mut source = fixture(size);
        let driver = extract(&mut source).unwrap();
        assert_eq!(driver.block_size, size as u32);
        assert_eq!(driver.container_block_count, PARTITION_BYTES / size as u64);
        assert_eq!(driver.jumpstart_block, 2);
        assert_eq!(driver.container_uuid, *b"Authored-UUID-01");
        assert_eq!(driver.bytes.len(), size + 19);
        assert!(driver.bytes[..size].iter().all(|b| *b == 0x31));
        assert!(driver.bytes[size..].iter().all(|b| *b == 0xa7));
        assert_eq!(driver.extents[0].start_block, 5);
        assert_eq!(
            source.reads,
            [
                (0, 40),
                (0, size),
                (2 * size as u64, size),
                (5 * size as u64, size),
                (4 * size as u64, size)
            ]
        );
    }
}

#[test]
fn fletcher_matches_independent_c_vectors_and_checksum_field_is_excluded() {
    for (size, pattern, expected) in [
        (4096, 0, 0xffff_ffff_ffff_ffff),
        (4096, 1, 0xba20_c063_5340_cfba),
        (65536, 1, 0x111d_325c_075e_55c2),
        (4096, 2, 0xffff_ffff_ffff_ffff),
    ] {
        let mut block = vec![0; size];
        for (i, bytes) in block[8..].chunks_exact_mut(4).enumerate() {
            let word: u32 = match pattern {
                1 => (i as u32)
                    .wrapping_mul(0x9e37_79b1)
                    .wrapping_add(0xfedc_ba98),
                2 => u32::MAX,
                _ => 0,
            };
            bytes.copy_from_slice(&word.to_le_bytes());
        }
        assert_eq!(fletcher64_checksum(&block), Some(expected));
        block[..8].fill(0x73);
        assert_eq!(fletcher64_checksum(&block), Some(expected));
        seal(&mut block);
        let mut sum = 0_u128;
        let mut prefix = 0_u128;
        // Check words logically follow the payload, despite being stored first.
        for word in block[8..].chunks_exact(4).chain(block[..8].chunks_exact(4)) {
            sum += u32::from_le_bytes(word.try_into().unwrap()) as u128;
            prefix += sum;
        }
        assert_eq!(sum % u32::MAX as u128, 0);
        assert_eq!(prefix % u32::MAX as u128, 0);
    }
    assert_eq!(fletcher64_checksum(&[0; 7]), None);
    assert_eq!(fletcher64_checksum(&[0; 9]), None);
}

#[test]
fn bad_checksums_stop_before_dependent_reads() {
    for (jump, expected_reads) in [(false, 2), (true, 3)] {
        let mut source = fixture(BS);
        source
            .blocks
            .get_mut(&(if jump { (2 * BS) as u64 } else { 0 }))
            .unwrap()[100] ^= 1;
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::BadChecksum { jumpstart: jump })
        );
        assert_eq!(source.reads.len(), expected_reads);
    }
}

#[test]
fn bad_magic_and_object_headers_are_rejected_after_valid_checksum() {
    for jump in [false, true] {
        for (offset, value) in [
            (32, 0),
            (24, 0),
            (24, 0xc000_0014),
            (24, 0x5000_0014),
            (24, 0x6000_0014),
            (24, 0x4800_0014),
            (24, 0x4001_0014),
            (28, 1),
        ] {
            let mut source = fixture(BS);
            edit(&mut source, jump, |b| put32(b, offset, value));
            let error = if offset == 32 {
                JumpstartError::BadMagic { jumpstart: jump }
            } else {
                JumpstartError::InvalidObject { jumpstart: jump }
            };
            assert_eq!(extract(&mut source), Err(error));
        }
        let mut source = fixture(BS);
        edit(&mut source, jump, |b| put64(b, 16, 0));
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::InvalidObject { jumpstart: jump })
        );
    }
}

#[test]
fn physical_jumpstart_must_match_its_address_and_storage_type() {
    for (offset, value) in [(8, 3), (24, 0x8000_0014), (24, 0x14)] {
        let mut source = fixture(BS);
        edit(&mut source, true, |b| put64(b, offset, value));
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::InvalidObject { jumpstart: true })
        );
    }
}

#[test]
fn jumpstart_reserved_and_optional_feature_bits_are_preserved_as_opaque() {
    let mut source = fixture(BS);
    edit(&mut source, false, |b| {
        put64(b, 48, 1 << 63);
        put64(b, 56, 1 << 62);
    });
    edit(&mut source, true, |b| b[48..176].fill(0x83));
    assert!(extract(&mut source).is_ok());
}

#[test]
fn all_fusion_indicators_fail_before_jumpstart_read() {
    for (offset, value) in [
        (48, 2),
        (64, 0x102),
        (1280, 1),
        (1288, 1),
        (1352, 1),
        (1360, 1),
        (1368, 1),
        (1376, 1),
    ] {
        let mut source = fixture(BS);
        edit(&mut source, false, |b| put64(b, offset, value));
        assert_eq!(extract(&mut source), Err(JumpstartError::UnsupportedFusion));
        assert_eq!(source.reads.len(), 2);
    }
}

#[test]
fn incompatible_features_fail_closed() {
    for value in [0, 1, 3, 4, 1 << 63] {
        let mut source = fixture(BS);
        edit(&mut source, false, |b| put64(b, 64, value));
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::UnsupportedFeatures(value))
        );
    }
}

#[test]
fn block_size_prefix_is_bounded_before_allocation_or_full_read() {
    for size in [0, 512, 4095, 4097, 6144, 65537, u32::MAX] {
        let mut source = fixture(BS);
        edit(&mut source, false, |b| put32(b, 36, size));
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::InvalidBlockSize(size))
        );
        assert_eq!(source.reads, [(0, 40)]);
    }
}

#[test]
fn changed_prefix_is_rejected() {
    let mut source = fixture(BS);
    source.changed_prefix = true;
    assert_eq!(extract(&mut source), Err(JumpstartError::SourceChanged));
}

#[test]
fn partition_bounds_stop_reads_before_callback() {
    for len in [0, 39, 40, 4095, PARTITION_BYTES - 1] {
        let mut source = fixture(BS);
        source.len = len;
        assert_eq!(extract(&mut source), Err(JumpstartError::OutOfBounds));
        assert!(source.reads.len() <= 2);
    }
}

#[test]
fn container_geometry_is_checked_without_wrapping() {
    for (count, error) in [
        (0, JumpstartError::InvalidContainerSize),
        (255, JumpstartError::InvalidContainerSize),
        (257, JumpstartError::OutOfBounds),
        (u64::MAX, JumpstartError::ArithmeticOverflow),
    ] {
        let mut source = fixture(BS);
        edit(&mut source, false, |b| put64(b, 40, count));
        assert_eq!(extract(&mut source), Err(error));
        assert_eq!(source.reads.len(), 2);
    }
}

#[test]
fn absent_negative_and_outside_jumpstart_addresses_do_not_seek() {
    for (address, error) in [
        (0, JumpstartError::NoJumpstart),
        (u64::MAX, JumpstartError::NegativeAddress),
        (1 << 63, JumpstartError::NegativeAddress),
        (256, JumpstartError::OutOfBounds),
        (i64::MAX as u64, JumpstartError::OutOfBounds),
    ] {
        let mut source = fixture(BS);
        edit(&mut source, false, |b| put64(b, 1272, address));
        assert_eq!(extract(&mut source), Err(error));
        assert_eq!(source.reads.len(), 2);
    }
}

#[test]
fn unsupported_jumpstart_version_and_zero_file_length_are_rejected() {
    for value in [0, 2, u32::MAX] {
        let mut source = fixture(BS);
        edit(&mut source, true, |b| put32(b, 36, value));
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::UnsupportedVersion(value))
        );
    }
    let mut source = fixture(BS);
    edit(&mut source, true, |b| put32(b, 40, 0));
    assert_eq!(extract(&mut source), Err(JumpstartError::InvalidFileLength));
}

#[test]
fn caller_limits_are_enforced() {
    for (limits, error) in [
        (
            JumpstartLimits {
                max_driver_bytes: 0,
                max_extents: 1,
            },
            JumpstartError::InvalidLimits,
        ),
        (
            JumpstartLimits {
                max_driver_bytes: 1,
                max_extents: 0,
            },
            JumpstartError::InvalidLimits,
        ),
        (
            JumpstartLimits {
                max_driver_bytes: BS,
                max_extents: 2,
            },
            JumpstartError::DriverTooLarge,
        ),
        (
            JumpstartLimits {
                max_driver_bytes: BS * 2,
                max_extents: 1,
            },
            JumpstartError::TooManyExtents,
        ),
    ] {
        let mut source = fixture(BS);
        assert_eq!(
            extract_jumpstart(&mut source, PARTITION_BYTES, limits),
            Err(error)
        );
        assert!(source.reads.len() <= 3);
    }
}

#[test]
fn extent_count_and_complete_table_must_fit_the_checksum_block() {
    for (count, error) in [
        (0, JumpstartError::InvalidExtentCount),
        (246, JumpstartError::ExtentTableOutOfBounds),
        (u32::MAX, JumpstartError::TooManyExtents),
    ] {
        let mut source = fixture(BS);
        edit(&mut source, true, |b| put32(b, 44, count));
        assert_eq!(extract(&mut source), Err(error));
        assert_eq!(source.reads.len(), 3);
    }
}

#[test]
fn signed_and_overflowing_extent_ranges_fail_before_data_reads() {
    for (start, count, error) in [
        (u64::MAX, 1, JumpstartError::NegativeAddress),
        (1 << 63, 1, JumpstartError::NegativeAddress),
        (255, 2, JumpstartError::OutOfBounds),
        (5, 0, JumpstartError::EmptyExtent),
        (5, u64::MAX, JumpstartError::ArithmeticOverflow),
    ] {
        let mut source = fixture(BS);
        edit(&mut source, true, |b| {
            put64(b, 176, start);
            put64(b, 184, count);
        });
        assert_eq!(extract(&mut source), Err(error));
        assert_eq!(source.reads.len(), 3);
    }
}

#[test]
fn insufficient_capacity_does_not_return_partial_bytes() {
    let mut source = fixture(BS);
    edit(&mut source, true, |b| put32(b, 40, 2 * BS as u32 + 1));
    assert_eq!(
        extract(&mut source),
        Err(JumpstartError::InsufficientExtentCapacity)
    );
    assert_eq!(source.reads.len(), 3);
}

#[test]
fn extra_extents_are_validated_even_when_they_are_not_read() {
    let mut source = fixture(BS);
    edit(&mut source, true, |b| {
        put32(b, 40, 1);
        put64(b, 192, 256);
    });
    assert_eq!(extract(&mut source), Err(JumpstartError::OutOfBounds));
    assert_eq!(source.reads.len(), 3);
}

#[test]
fn excess_allocated_capacity_is_not_read_or_returned() {
    let mut source = fixture(BS);
    edit(&mut source, true, |b| {
        put32(b, 40, 1);
        put64(b, 184, 250);
    });
    assert_eq!(extract(&mut source).unwrap().bytes, [0x31]);
    assert_eq!(source.reads.len(), 4);
}

#[test]
fn aggregate_extent_capacity_overflow_is_rejected() {
    let mut source = fixture(BS);
    source.len = u64::MAX;
    let huge_blocks = u64::MAX / BS as u64;
    edit(&mut source, false, |b| put64(b, 40, huge_blocks));
    edit(&mut source, true, |b| {
        put64(b, 176, 0);
        put64(b, 184, huge_blocks);
        put64(b, 192, 0);
        put64(b, 200, huge_blocks);
    });
    assert_eq!(
        extract(&mut source),
        Err(JumpstartError::ArithmeticOverflow)
    );
    assert_eq!(source.reads.len(), 3);
}

#[test]
fn device_errors_and_short_reads_are_preserved_at_each_boundary() {
    for call in 1..=5 {
        let mut source = fixture(BS);
        source.fail_on = Some(call);
        assert_eq!(
            extract(&mut source),
            Err(JumpstartError::Io("device failed or short read"))
        );
        assert_eq!(source.reads.len(), call);
    }
    let mut source = fixture(BS);
    source
        .blocks
        .get_mut(&((2 * BS) as u64))
        .unwrap()
        .truncate(175);
    assert_eq!(extract(&mut source), Err(JumpstartError::Io("EOF")));
}

#[test]
fn driver_payload_is_opaque_and_not_mistaken_for_checksummed_or_valid_pe() {
    let mut source = fixture(BS);
    source.blocks.get_mut(&((5 * BS) as u64)).unwrap()[0] ^= 0xff;
    let bytes = extract(&mut source).unwrap().bytes;
    assert_eq!(bytes[0], 0xce);
    assert_ne!(&bytes[..2], b"MZ");
}
