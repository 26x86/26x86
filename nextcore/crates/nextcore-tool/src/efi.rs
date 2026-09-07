//! Structural PE32+ validation for an x86_64 UEFI application, not a signature
//! verifier or proof that firmware will successfully execute the image.
//!
//! Public format references:
//! https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
//! https://uefi.org/specs/UEFI/2.10_A/02_Overview.html#uefi-images

use anyhow::{ensure, Context, Result};
use std::ops::Range;

fn bytes(data: &[u8], start: usize, size: usize) -> Result<&[u8]> {
    let end = start.checked_add(size).context("PE offset overflow")?;
    data.get(start..end).context("truncated PE image")
}

fn word(data: &[u8], offset: usize) -> Result<u16> {
    Ok(u16::from_le_bytes(bytes(data, offset, 2)?.try_into()?))
}

fn dword(data: &[u8], offset: usize) -> Result<u32> {
    Ok(u32::from_le_bytes(bytes(data, offset, 4)?.try_into()?))
}

fn overlaps(a: &Range<u64>, b: &Range<u64>) -> bool {
    a.start < b.end && b.start < a.end
}

/// Reject wrong architectures/subsystems and structurally incomplete PE images.
/// Relocation semantics, code behavior and Secure Boot trust remain firmware checks.
pub fn validate_x64_application(data: &[u8]) -> Result<()> {
    ensure!(bytes(data, 0, 2)? == b"MZ", "missing MZ signature");
    let pe = dword(data, 0x3c)? as usize;
    ensure!(pe >= 64, "PE header overlaps DOS header");
    let header = bytes(data, pe, 24)?;
    ensure!(&header[..4] == b"PE\0\0", "missing PE signature");
    ensure!(
        word(header, 4)? == 0x8664,
        "EFI image must target x86_64 (AMD64)"
    );
    let section_count = word(header, 6)? as usize;
    ensure!(section_count > 0, "PE image contains no sections");
    ensure!(
        word(header, 22)? & 0x0002 != 0,
        "PE image is not executable"
    );
    let optional_size = word(header, 20)? as usize;
    let optional = bytes(data, pe + 24, optional_size)?;
    ensure!(optional.len() >= 112, "truncated PE32+ optional header");
    ensure!(word(optional, 0)? == 0x20b, "EFI image must use PE32+");
    ensure!(
        word(optional, 68)? == 10,
        "PE subsystem must be EFI application (10)"
    );
    let directories = dword(optional, 108)? as usize;
    ensure!(
        directories <= (optional.len() - 112) / 8,
        "truncated PE data directories"
    );

    let entry = u64::from(dword(optional, 16)?);
    let section_align = u64::from(dword(optional, 32)?);
    let file_align = u64::from(dword(optional, 36)?);
    let image_size = u64::from(dword(optional, 56)?);
    let header_size = u64::from(dword(optional, 60)?);
    ensure!(
        section_align.is_power_of_two() && file_align.is_power_of_two(),
        "invalid PE alignment"
    );
    ensure!(
        section_align >= file_align,
        "section alignment is smaller than file alignment"
    );
    ensure!(
        if section_align < 4096 {
            file_align == section_align
        } else {
            (512..=65536).contains(&file_align)
        },
        "invalid PE file alignment"
    );
    ensure!(
        image_size > 0 && image_size % section_align == 0,
        "invalid PE SizeOfImage"
    );
    let section_start = pe + 24 + optional_size;
    let section_table = bytes(data, section_start, section_count * 40)?;
    ensure!(
        header_size >= (section_start + section_table.len()) as u64
            && header_size <= data.len() as u64
            && header_size <= image_size
            && header_size % file_align == 0,
        "invalid PE SizeOfHeaders"
    );
    ensure!(
        entry >= header_size && entry < image_size,
        "entry point is outside image sections"
    );

    let mut virtual_ranges = Vec::new();
    let mut raw_ranges = Vec::new();
    let mut file_backed_ranges = Vec::new();
    let mut entry_is_executable = false;
    for section in section_table.chunks_exact(40) {
        let virtual_size = u64::from(dword(section, 8)?);
        let virtual_start = u64::from(dword(section, 12)?);
        let raw_size = u64::from(dword(section, 16)?);
        let raw_start = u64::from(dword(section, 20)?);
        let flags = dword(section, 36)?;
        let virtual_end = virtual_start + virtual_size.max(raw_size);
        ensure!(
            virtual_start >= header_size
                && virtual_start % section_align == 0
                && virtual_end <= image_size,
            "section virtual range is outside the image or misaligned"
        );
        let virtual_range = virtual_start..virtual_end;
        ensure!(
            !virtual_ranges
                .iter()
                .any(|other| overlaps(&virtual_range, other)),
            "overlapping PE virtual sections"
        );
        virtual_ranges.push(virtual_range);
        if raw_size > 0 {
            let raw_end = raw_start + raw_size;
            ensure!(
                raw_start >= header_size
                    && raw_start % file_align == 0
                    && raw_size % file_align == 0,
                "invalid section raw alignment"
            );
            ensure!(raw_end <= data.len() as u64, "truncated PE section data");
            let raw_range = raw_start..raw_end;
            ensure!(
                !raw_ranges.iter().any(|other| overlaps(&raw_range, other)),
                "overlapping PE raw sections"
            );
            raw_ranges.push(raw_range);
            let backed = virtual_start..virtual_start + raw_size;
            if flags & 0x2000_0000 != 0
                && backed.contains(&entry)
                && (virtual_size == 0 || entry < virtual_start + virtual_size)
            {
                entry_is_executable = true;
            }
            file_backed_ranges.push(backed);
        }
    }
    ensure!(
        entry_is_executable,
        "entry point is not backed by executable section data"
    );

    for index in 0..directories {
        let start = u64::from(dword(optional, 112 + index * 8)?);
        let size = u64::from(dword(optional, 116 + index * 8)?);
        if size == 0 {
            continue;
        }
        ensure!(start != 0, "nonempty PE directory has a null address");
        let end = start + size;
        // The certificate table uniquely uses a file offset instead of an RVA.
        if index == 4 {
            ensure!(
                start % 8 == 0 && end <= data.len() as u64,
                "invalid PE certificate table range"
            );
        } else {
            ensure!(
                file_backed_ranges
                    .iter()
                    .any(|range| range.start <= start && end <= range.end),
                "PE directory is outside section data"
            );
        }
    }
    Ok(())
}
