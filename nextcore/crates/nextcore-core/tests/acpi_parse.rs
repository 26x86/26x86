use nextcore_core::acpi::AcpiTables;

const RSDP_LEN: usize = 36;
const XSDT_HEADER_LEN: usize = 36;
const SUBTABLE_LEN: usize = 16;

fn set_checksum(buf: &mut [u8], start: usize, end: usize, checksum_idx: usize) {
    let sum: u8 = buf[start..end]
        .iter()
        .enumerate()
        .filter(|(i, _)| *i != checksum_idx - start)
        .map(|(_, &b)| b)
        .fold(0u8, |a, b| a.wrapping_add(b));
    buf[checksum_idx] = 0u8.wrapping_sub(sum);
}

fn build_subtable(sig: &[u8; 4]) -> Vec<u8> {
    let mut t = vec![0u8; SUBTABLE_LEN];
    t[0..4].copy_from_slice(sig);
    t[4..8].copy_from_slice(&(SUBTABLE_LEN as u32).to_le_bytes());
    t[8] = 1; // revision
    t[10..16].copy_from_slice(b"ACME00");
    set_checksum(&mut t, 0, SUBTABLE_LEN, 9);
    t
}

fn build_acpi_blob() -> Vec<u8> {
    let xsdt_off = RSDP_LEN; // 36
    let facp_off = xsdt_off + XSDT_HEADER_LEN + 3 * 8; // 36 + 60 = 96
    let apic_off = facp_off + SUBTABLE_LEN;
    let hpet_off = apic_off + SUBTABLE_LEN;
    let total = hpet_off + SUBTABLE_LEN; // 144

    let facp = build_subtable(b"FACP");
    let apic = build_subtable(b"APIC");
    let hpet = build_subtable(b"HPET");

    let mut buf = vec![0u8; total];

    // ---- RSDP at 0 (36 bytes) ----
    buf[0..8].copy_from_slice(b"RSD PTR ");
    buf[15] = 2; // ACPI 2.0
    buf[16..20].copy_from_slice(&0u32.to_le_bytes()); // RSDT addr = 0
    buf[20..24].copy_from_slice(&(RSDP_LEN as u32).to_le_bytes()); // length = 36
    buf[24..32].copy_from_slice(&(xsdt_off as u64).to_le_bytes()); // XSDT addr
    set_checksum(&mut buf, 0, 20, 8); // first 20 bytes sum == 0
    set_checksum(&mut buf, 0, RSDP_LEN, 32); // full 36 bytes sum == 0

    // ---- XSDT at 36 (36 header + 3*8 addr = 60 bytes) ----
    buf[xsdt_off..xsdt_off + 4].copy_from_slice(b"XSDT");
    buf[xsdt_off + 4..xsdt_off + 8].copy_from_slice(&60u32.to_le_bytes()); // length
    buf[xsdt_off + 8] = 1; // revision
    buf[xsdt_off + 10..xsdt_off + 16].copy_from_slice(b"ACME00");
    buf[xsdt_off + 16..xsdt_off + 24].copy_from_slice(b"BOARD000");
    buf[xsdt_off + 24..xsdt_off + 28].copy_from_slice(&1u32.to_le_bytes()); // OEM rev
    buf[xsdt_off + 28..xsdt_off + 32].copy_from_slice(&1u32.to_le_bytes()); // creator id
    buf[xsdt_off + 32..xsdt_off + 36].copy_from_slice(&1u32.to_le_bytes()); // creator rev
    let addr_start = xsdt_off + XSDT_HEADER_LEN;
    buf[addr_start..addr_start + 8].copy_from_slice(&(facp_off as u64).to_le_bytes());
    buf[addr_start + 8..addr_start + 16].copy_from_slice(&(apic_off as u64).to_le_bytes());
    buf[addr_start + 16..addr_start + 24].copy_from_slice(&(hpet_off as u64).to_le_bytes());
    set_checksum(&mut buf, xsdt_off, xsdt_off + 60, xsdt_off + 9);

    // ---- sub-tables ----
    buf[facp_off..facp_off + SUBTABLE_LEN].copy_from_slice(&facp);
    buf[apic_off..apic_off + SUBTABLE_LEN].copy_from_slice(&apic);
    buf[hpet_off..hpet_off + SUBTABLE_LEN].copy_from_slice(&hpet);

    buf
}

#[test]
fn test_rsdp_detection() {
    let data = build_acpi_blob();
    let tables = AcpiTables::parse(&data)
        .expect("RSDP with XSDT address should be detected and parsed");

    // RSDP first 20 bytes must sum to zero by construction.
    assert_eq!(
        data[0..20].iter().fold(0u8, |a, b| a.wrapping_add(*b)),
        0,
        "RSDP first-20 checksum mismatch"
    );
    // Full 36-byte RSDP must sum to zero.
    assert_eq!(
        data[0..36].iter().fold(0u8, |a, b| a.wrapping_add(*b)),
        0,
        "RSDP extended checksum mismatch"
    );
    let sigs = tables.table_signatures();
    assert_eq!(sigs.len(), 3, "expected 3 tables from XSDT");
}

#[test]
fn test_xsdt_parse() {
    let data = build_acpi_blob();
    let tables = AcpiTables::parse(&data)
        .expect("XSDT should parse");
    let sigs = tables.table_signatures();
    assert_eq!(sigs, vec![*b"FACP", *b"APIC", *b"HPET"]);
}

#[test]
fn test_table_signatures() {
    let data = build_acpi_blob();
    let tables = AcpiTables::parse(&data).expect("parse should succeed");
    let mut sigs = tables.table_signatures();
    sigs.sort();
    assert_eq!(
        sigs,
        vec![*b"APIC", *b"FACP", *b"HPET"],
        "table_signatures should list all three sub-tables"
    );
}

#[test]
fn test_find_table() {
    let data = build_acpi_blob();
    let tables = AcpiTables::parse(&data).expect("parse should succeed");

    let apic = tables
        .find_table(b"APIC")
        .expect("APIC table should be found");
    assert_eq!(&apic[0..4], b"APIC");
    assert_eq!(apic.len(), SUBTABLE_LEN);

    let facp = tables
        .find_table(b"FACP")
        .expect("FACP table should be found");
    assert_eq!(&facp[0..4], b"FACP");

    let hpet = tables
        .find_table(b"HPET")
        .expect("HPET table should be found");
    assert_eq!(&hpet[0..4], b"HPET");

    assert!(
        tables.find_table(b"DSDT").is_none(),
        "unknown DSDT table should not be found"
    );
}
