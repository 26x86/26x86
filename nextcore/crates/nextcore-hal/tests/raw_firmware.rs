use nextcore_hal::{acpi_raw::*, pci_raw::decode_config_space};

fn checksum_fix(bytes: &mut [u8]) {
    let sum = bytes.iter().fold(0u8, |a, b| a.wrapping_add(*b));
    bytes[9] = bytes[9].wrapping_sub(sum);
}

fn sdt(signature: &[u8; 4], length: usize) -> Vec<u8> {
    let mut bytes = vec![0; length];
    bytes[..4].copy_from_slice(signature);
    bytes[4..8].copy_from_slice(&(length as u32).to_le_bytes());
    checksum_fix(&mut bytes);
    bytes
}

#[test]
fn fixed_fields_cannot_come_from_after_declared_table() {
    let mut madt = sdt(b"APIC", 36);
    madt.extend_from_slice(&[0; 8]);
    assert!(parse_madt_summary(&madt).is_err());

    let mut facp = sdt(b"FACP", 52);
    facp.resize(148, 0xaa);
    assert!(parse_facp_summary(&facp).is_err());

    let mut mcfg = sdt(b"MCFG", 36);
    mcfg.resize(60, 0);
    assert!(parse_mcfg_summary(&mcfg).is_err());
}

#[test]
fn facp_optional_x_dsdt_uses_declared_length() {
    let mut facp = sdt(b"FACP", 116);
    facp[40..44].copy_from_slice(&0x1234_5678u32.to_le_bytes());
    checksum_fix(&mut facp);
    facp.resize(148, 0xaa);
    let info = parse_facp_summary(&facp).unwrap();
    assert_eq!(info.dsdt, 0x1234_5678);
    assert_eq!(info.x_dsdt, 0);

    facp[4..8].copy_from_slice(&148u32.to_le_bytes());
    facp[140..148].copy_from_slice(&0x1234_5678_9abc_def0u64.to_le_bytes());
    checksum_fix(&mut facp);
    assert_eq!(
        parse_facp_summary(&facp).unwrap().x_dsdt,
        0x1234_5678_9abc_def0
    );
}

#[test]
fn madt_rejects_dangling_header_and_overlong_body() {
    assert!(parse_madt_summary(&sdt(b"APIC", 45)).is_err());
    let mut bytes = sdt(b"APIC", 48);
    bytes[44..46].copy_from_slice(&[0xfe, 5]);
    checksum_fix(&mut bytes);
    assert!(parse_madt_summary(&bytes).is_err());
}

#[test]
fn madt_known_records_require_complete_layouts() {
    for (kind, length) in [(0, 8), (1, 12), (2, 10), (3, 8), (4, 6), (5, 12)] {
        let mut bytes = sdt(b"APIC", 44 + length - 1);
        bytes[44] = kind;
        bytes[45] = (length - 1) as u8;
        checksum_fix(&mut bytes);
        assert!(parse_madt_summary(&bytes).is_err(), "short type {kind}");

        let mut bytes = sdt(b"APIC", 44 + length);
        bytes[44] = kind;
        bytes[45] = length as u8;
        checksum_fix(&mut bytes);
        assert_eq!(parse_madt_summary(&bytes).unwrap().total_entries, 1);
    }
}

#[test]
fn madt_preserves_unknown_records_without_decoding_them() {
    let mut bytes = sdt(b"APIC", 54);
    bytes[44..46].copy_from_slice(&[0, 8]);
    bytes[52..54].copy_from_slice(&[0xfe, 2]);
    checksum_fix(&mut bytes);
    let info = parse_madt_summary(&bytes).unwrap();
    assert_eq!((info.total_entries, info.lapic, info.other), (2, 1, 1));
}

#[test]
fn every_typed_sdt_parser_rejects_bad_checksum() {
    for signature in [b"XSDT", b"RSDT", b"APIC", b"MCFG", b"FACP"] {
        let length = if signature == b"FACP" { 116 } else { 44 };
        let mut bytes = sdt(signature, length);
        bytes[9] ^= 1;
        assert!(!parse_sdt_header(&bytes).unwrap().checksum_ok);
        let accepted = match signature {
            b"XSDT" => parse_xsdt_addresses(&bytes).is_ok(),
            b"RSDT" => parse_rsdt_addresses(&bytes).is_ok(),
            b"APIC" => parse_madt_summary(&bytes).is_ok(),
            b"MCFG" => parse_mcfg_summary(&bytes).is_ok(),
            _ => parse_facp_summary(&bytes).is_ok(),
        };
        assert!(!accepted, "bad checksum accepted for {signature:?}");
    }
}

#[test]
fn root_entry_width_and_mcfg_allocation_width_are_enforced() {
    assert!(parse_xsdt_addresses(&sdt(b"XSDT", 43)).is_err());
    assert!(parse_rsdt_addresses(&sdt(b"RSDT", 39)).is_err());
    assert!(parse_mcfg_summary(&sdt(b"MCFG", 59)).is_err());
    assert_eq!(
        parse_mcfg_summary(&sdt(b"MCFG", 60))
            .unwrap()
            .segment_groups,
        1
    );
    let mut rsdt = sdt(b"RSDT", 40);
    rsdt[36..40].copy_from_slice(&0xfabc_def0u32.to_le_bytes());
    checksum_fix(&mut rsdt);
    assert_eq!(parse_rsdt_addresses(&rsdt).unwrap(), vec![0xfabc_def0]);
}

#[test]
fn pci_layout_mask_accepts_multifunction_type0_and_rejects_other_layouts() {
    let mut bytes = [0u8; 64];
    bytes[..4].copy_from_slice(&[0x34, 0x12, 0x78, 0x56]);
    bytes[44..48].copy_from_slice(&[0xbc, 0x9a, 0xf0, 0xde]);
    for layout in [0, 0x80] {
        bytes[0x0e] = layout;
        let device = decode_config_space(&bytes).unwrap();
        assert_eq!(
            (device.subsystem_vendor_id, device.subsystem_device_id),
            (0x9abc, 0xdef0)
        );
    }
    for layout in [1, 2, 0x7f, 0x81, 0x82, 0xff] {
        bytes[0x0e] = layout;
        assert!(decode_config_space(&bytes).is_err(), "layout {layout:#x}");
    }
}
