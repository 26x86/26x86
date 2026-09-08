//! NXHAL: live-firmware ACPI/PCI dumper for HAL integration.
//!
//! Additive, feature-gated test instrument (`hal-tables` feature, `NXHAL`
//! binary). It never touches the production BOOTX64 path: it locates the ACPI
//! RSDP via the EFI configuration table on a live OVMF boot, walks
//! RSDP->XSDT/RSDT->FACP/APIC(MADT)/HPET/MCFG (plus any other entries up to a
//! cap), dumps the exact raw table bytes as hex over serial, scans PCI bus 0
//! via CF8/CFC, and exits via isa-debug-exit. The host harness feeds those
//! exact bytes to the `nextcore-hal` parsers. QEMU/OVMF tables only.
#![no_std]
#![no_main]

extern crate alloc;

use alloc::{format, string::String, vec::Vec};
use core::arch::asm;
use uefi::{
    boot, entry,
    mem::memory_map::{MemoryMap, MemoryType},
    proto::console::serial::Serial,
    table::cfg::ConfigTableEntry,
    Status,
};

#[global_allocator]
static ALLOCATOR: uefi::allocator::Allocator = uefi::allocator::Allocator;

// A corrupt length field must not consume firmware memory or flood serial.
const MAX_TABLES: usize = 32;
const MAX_TABLE_BYTES: usize = 16 * 1024;
const MAX_XSDT_BYTES: usize = 4096;
const HEX_CHUNK: usize = 64;

fn report(message: &str) {
    uefi::println!("{message}");
    if let Ok(handle) = boot::get_handle_for_protocol::<Serial>() {
        if let Ok(mut serial) = boot::open_protocol_exclusive::<Serial>(handle) {
            let _ = serial.write_exact(message.as_bytes());
            let _ = serial.write_exact(b"\r\n");
        }
    }
}

fn hex_encode(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(DIGITS[(b >> 4) as usize] as char);
        out.push(DIGITS[(b & 0x0f) as usize] as char);
    }
    out
}

/// Copy an ACPI range from trusted q35/OVMF firmware while Boot Services are
/// active. The complete range must belong to one ACPI memory descriptor.
/// This instrument is not a general physical-memory reader or an OS provider.
unsafe fn phys_copy(phys: u64, len: usize) -> Result<Vec<u8>, Status> {
    if phys == 0 {
        return Err(Status::NOT_FOUND);
    }
    if len == 0 || len > MAX_TABLE_BYTES.max(MAX_XSDT_BYTES) {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let end = phys
        .checked_add(len as u64)
        .ok_or(Status::INVALID_PARAMETER)?;
    // This test instrument deliberately supports only q35's low-memory tables.
    if end > 0x1_0000_0000 {
        return Err(Status::INVALID_PARAMETER);
    }
    let map = boot::memory_map(MemoryType::LOADER_DATA).map_err(|error| error.status())?;
    let covered = map.entries().any(|descriptor| {
        if !matches!(
            descriptor.ty,
            MemoryType::ACPI_RECLAIM | MemoryType::ACPI_NON_VOLATILE
        ) {
            return false;
        }
        descriptor
            .page_count
            .checked_mul(4096)
            .and_then(|size| descriptor.phys_start.checked_add(size))
            .is_some_and(|limit| phys >= descriptor.phys_start && end <= limit)
    });
    if !covered {
        return Err(Status::ACCESS_DENIED);
    }
    let mut buf = alloc::vec![0; len];
    unsafe {
        core::ptr::copy_nonoverlapping(phys as *const u8, buf.as_mut_ptr(), len);
    }
    Ok(buf)
}

fn checksum_zero(bytes: &[u8]) -> bool {
    bytes.iter().fold(0u8, |a, &b| a.wrapping_add(b)) == 0
}

fn sig_str(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|&b| {
            if (0x20..0x7f).contains(&b) {
                b as char
            } else {
                '.'
            }
        })
        .collect()
}

fn debug_exit(value: u32) -> ! {
    unsafe {
        asm!("out dx, eax", in("dx") 0xf4u16, in("eax") value, options(nomem, nostack, preserves_flags));
    }
    loop {
        unsafe {
            asm!("hlt", options(nomem, nostack));
        }
    }
}

#[entry]
fn efi_main() -> Status {
    uefi::helpers::init().expect("NXHAL UEFI init failed");
    report("NXHAL: EFI_ENTRY");
    match run() {
        Ok((tables, pci)) => {
            report(&format!("NXHAL: DONE tables={tables} pci={pci}"));
            debug_exit(0x21);
        }
        Err(status) => {
            report(&format!("NXHAL: ERROR status={status:?}"));
            debug_exit(0x23);
        }
    }
}

fn run() -> Result<(usize, usize), Status> {
    // Exercise the rejection path before the first real table read. None of
    // these addresses may reach copy_nonoverlapping, even in the instrument.
    for (address, length, expected) in [
        (0, 36, Status::NOT_FOUND),
        (u64::MAX, 36, Status::INVALID_PARAMETER),
        (0xffff_ffff, 36, Status::INVALID_PARAMETER),
        (0xb8000, 36, Status::ACCESS_DENIED),
        (0xb8000, MAX_TABLE_BYTES + 1, Status::BAD_BUFFER_SIZE),
    ] {
        match unsafe { phys_copy(address, length) } {
            Err(status) if status == expected => {}
            _ => return Err(Status::COMPROMISED_DATA),
        }
    }
    report("NXHAL: READ_GUARDS_OK");
    let (rsdp_phys, rsdp_len, rsdp_rev, rsdt, xsdt) = find_rsdp()?;
    report(&format!(
        "NXHAL: RSDP addr={rsdp_phys:#x} len={rsdp_len} rev={rsdp_rev} rsdt={rsdt:#x} xsdt={xsdt:#x}"
    ));
    // Dump the RSDP bytes themselves first (36 or 20 bytes).
    let rsdp_bytes = unsafe { phys_copy(rsdp_phys, rsdp_len)? };
    dump_table("RSDP", rsdp_phys, &rsdp_bytes);

    let root_phys = if xsdt != 0 { xsdt } else { rsdt };
    if root_phys == 0 {
        return Err(Status::NOT_FOUND);
    }
    let root_hdr = unsafe { phys_copy(root_phys, 36)? };
    let root_len =
        u32::from_le_bytes([root_hdr[4], root_hdr[5], root_hdr[6], root_hdr[7]]) as usize;
    if root_len < 36 || root_len > MAX_XSDT_BYTES {
        report(&format!("NXHAL: ROOTLEN_INVALID len={root_len}"));
        return Err(Status::LOAD_ERROR);
    }
    let is_xsdt = &root_hdr[0..4] == b"XSDT";
    let is_rsdt = &root_hdr[0..4] == b"RSDT";
    if (xsdt != 0 && !is_xsdt) || (xsdt == 0 && !is_rsdt) {
        report("NXHAL: ROOTSIG_INVALID");
        return Err(Status::LOAD_ERROR);
    }
    let root_bytes = unsafe { phys_copy(root_phys, root_len)? };
    if !checksum_zero(&root_bytes) {
        report("NXHAL: ROOT_CHECKSUM nonzero");
        return Err(Status::CRC_ERROR);
    }
    let root_sig = if is_xsdt { "XSDT" } else { "RSDT" };
    dump_table(root_sig, root_phys, &root_bytes);

    let entry_size = if is_xsdt { 8 } else { 4 };
    if (root_len - 36) % entry_size != 0 {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let count = (root_len - 36) / entry_size;
    if count == 0 || count > MAX_TABLES {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    report(&format!("NXHAL: {root_sig} count={count}"));
    let mut dumped = 1usize; // root itself
    for i in 0..count {
        let off = 36 + i * entry_size;
        let addr = if is_xsdt {
            u64::from_le_bytes([
                root_bytes[off],
                root_bytes[off + 1],
                root_bytes[off + 2],
                root_bytes[off + 3],
                root_bytes[off + 4],
                root_bytes[off + 5],
                root_bytes[off + 6],
                root_bytes[off + 7],
            ])
        } else {
            u32::from_le_bytes([
                root_bytes[off],
                root_bytes[off + 1],
                root_bytes[off + 2],
                root_bytes[off + 3],
            ]) as u64
        };
        if addr == 0 {
            return Err(Status::COMPROMISED_DATA);
        }
        // Read the callee header first to learn its true length.
        let hdr = unsafe { phys_copy(addr, 36) };
        let hdr = match hdr {
            Ok(h) => h,
            Err(_) => {
                report(&format!("NXHAL: SKIP addr={addr:#x} reason=HDR_READ"));
                continue;
            }
        };
        let sig = sig_str(&hdr[0..4]);
        let len = u32::from_le_bytes([hdr[4], hdr[5], hdr[6], hdr[7]]) as usize;
        if len < 36 || len > MAX_TABLE_BYTES {
            report(&format!(
                "NXHAL: SKIP sig={sig} addr={addr:#x} len={len} reason=LEN_CAP"
            ));
            continue;
        }
        let bytes = unsafe { phys_copy(addr, len) };
        let bytes = match bytes {
            Ok(b) => b,
            Err(_) => {
                report(&format!(
                    "NXHAL: SKIP sig={sig} addr={addr:#x} reason=BODY_READ"
                ));
                continue;
            }
        };
        dump_table(&sig, addr, &bytes);
        dumped += 1;
    }
    let pci = dump_pci_bus0();
    Ok((dumped, pci))
}

/// Locate RSDP via the EFI configuration table. Returns
/// (rsdp_phys, rsdp_len, revision, rsdt_addr, xsdt_addr).
fn find_rsdp() -> Result<(u64, usize, u8, u64, u64), Status> {
    let st_ptr = uefi::table::system_table_raw().ok_or(Status::NOT_FOUND)?;
    let st = unsafe { &*st_ptr.as_ptr() };
    let n = st.number_of_configuration_table_entries;
    if n == 0 || n > 256 {
        return Err(Status::NOT_FOUND);
    }
    let entries = unsafe { core::slice::from_raw_parts(st.configuration_table, n) };
    let mut acpi2: u64 = 0;
    let mut acpi1: u64 = 0;
    for entry in entries {
        if entry.vendor_guid == ConfigTableEntry::ACPI2_GUID {
            acpi2 = entry.vendor_table as u64;
        } else if entry.vendor_guid == ConfigTableEntry::ACPI_GUID {
            acpi1 = entry.vendor_table as u64;
        }
    }
    let rsdp_phys = if acpi2 != 0 { acpi2 } else { acpi1 };
    if rsdp_phys == 0 {
        report("NXHAL: RSDP_NOT_FOUND");
        return Err(Status::NOT_FOUND);
    }
    let head = unsafe { phys_copy(rsdp_phys, 20)? };
    if &head[0..8] != b"RSD PTR " {
        report("NXHAL: RSDP_SIG_INVALID");
        return Err(Status::LOAD_ERROR);
    }
    if !checksum_zero(&head[0..20]) {
        report("NXHAL: RSDP_CHECKSUM nonzero");
        return Err(Status::LOAD_ERROR);
    }
    let rev = head[15];
    let rsdt = u32::from_le_bytes([head[16], head[17], head[18], head[19]]) as u64;
    if rev < 2 {
        return Ok((rsdp_phys, 20, rev, rsdt, 0));
    }
    let ext = unsafe { phys_copy(rsdp_phys, 36)? };
    let len = u32::from_le_bytes([ext[20], ext[21], ext[22], ext[23]]) as usize;
    if len < 36 || len > 64 {
        return Err(Status::LOAD_ERROR);
    }
    let full = unsafe { phys_copy(rsdp_phys, len)? };
    if !checksum_zero(&full) {
        report("NXHAL: RSDP_EXT_CHECKSUM nonzero");
        return Err(Status::LOAD_ERROR);
    }
    let xsdt = u64::from_le_bytes([
        full[24], full[25], full[26], full[27], full[28], full[29], full[30], full[31],
    ]);
    Ok((rsdp_phys, len, rev, rsdt, xsdt))
}

fn dump_table(sig: &str, addr: u64, bytes: &[u8]) {
    report(&format!(
        "NXHAL: TABLE sig={sig} addr={addr:#x} len={} csum={}",
        bytes.len(),
        checksum_zero(bytes)
    ));
    for chunk in bytes.chunks(HEX_CHUNK) {
        report(&format!("NXHAL: DATA {}", hex_encode(chunk)));
    }
}

fn pci_read(bus: u8, dev: u8, func: u8, offset: u8) -> u32 {
    let addr: u32 = 0x8000_0000
        | ((bus as u32) << 16)
        | ((dev as u32) << 11)
        | ((func as u32) << 8)
        | ((offset & 0xFC) as u32);
    let value: u32;
    unsafe {
        asm!("out dx, eax", in("dx") 0xCF8u16, in("eax") addr, options(nomem, nostack, preserves_flags));
        asm!("in eax, dx", in("dx") 0xCFCu16, out("eax") value, options(nomem, nostack, preserves_flags));
    }
    value
}

/// Scan PCI bus 0 via CF8/CFC and dump each present function's 64-byte header.
fn dump_pci_bus0() -> usize {
    let mut found = 0usize;
    for dev in 0..32u8 {
        for func in 0..8u8 {
            let d0 = pci_read(0, dev, func, 0x00);
            let vendor = (d0 & 0xFFFF) as u16;
            if vendor == 0xFFFF {
                continue;
            }
            let device = (d0 >> 16) as u16;
            let d2 = pci_read(0, dev, func, 0x08);
            let class = ((d2 >> 24) & 0xFF) as u8;
            let subclass = ((d2 >> 16) & 0xFF) as u8;
            let prog_if = ((d2 >> 8) & 0xFF) as u8;
            let revision = (d2 & 0xFF) as u8;
            // 64-byte header as 16 dwords.
            let mut header = Vec::with_capacity(64);
            for off in (0..64u8).step_by(4) {
                header.extend_from_slice(&pci_read(0, dev, func, off).to_le_bytes());
            }
            report(&format!(
                "NXHAL: PCI b=0 d={dev} f={func} vend={vendor:#06x} dev={device:#06x} class={class:#04x} sub={subclass:#04x} pif={prog_if:#04x} rev={revision:#04x}"
            ));
            for chunk in header.chunks(HEX_CHUNK) {
                report(&format!("NXHAL: PCIDATA {}", hex_encode(chunk)));
            }
            found += 1;
        }
    }
    found
}
