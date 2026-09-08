//! UEFI StartImage/Exit diagnostics, independent of the child implementation.
//!
//! UEFI 2.10A section 7.4: ExitData is a NUL-terminated CHAR16 description,
//! optionally followed by binary data; its caller owns the returned pool buffer.
//! Only a bounded prefix is copied. Binary suffixes are not interpreted as text.
use alloc::{format, string::String};
use core::{fmt::Write, ptr};
use uefi::{table, Handle, Status};

const MAX_EXIT_DATA_BYTES: usize = 2048;

/// Start an already loaded application with Boot Services active. Keep the exact
/// returned EFI_STATUS, including warning statuses; diagnostics never replace it.
pub fn start_image(child: Handle, report: fn(&str)) -> Status {
    let Some(system) = table::system_table_raw() else {
        return Status::NOT_READY;
    };
    // SAFETY: uefi's entry initializes the live system table. This path does not
    // call ExitBootServices, and an application returning here must leave it live.
    let services = unsafe { (*system.as_ptr()).boot_services };
    if services.is_null() {
        return Status::NOT_READY;
    }
    // Copy function pointers, rather than borrowing firmware data across child
    // execution. Layout and efiapi calling convention come from uefi-raw 0.16.
    let (start, free) = unsafe { ((*services).start_image, (*services).free_pool) };
    let mut size = 0usize;
    let mut data = ptr::null_mut();
    // SAFETY: child is owned by the loader, and both output pointers are valid.
    let status = unsafe { start(child.as_ptr(), &mut size, &mut data) };
    let mut copied = [0u8; MAX_EXIT_DATA_BYTES];
    let length = size.min(MAX_EXIT_DATA_BYTES);
    if data.is_null() {
        report(&format!("NEXTCORE: IMAGE_EXIT_DATA bytes={size} copied=0 pointer=null"));
    } else {
        // Firmware owns validation/allocation of the returned ExitData buffer.
        // Never construct a slice of its unbounded declared size or scan for NUL
        // outside the prefix. Byte copying imposes no CHAR16 alignment assumption.
        let range_valid = (data as usize).checked_add(length).is_some();
        if range_valid && length != 0 {
            // SAFETY: UEFI supplies size bytes; length <= size and local capacity.
            unsafe { ptr::copy_nonoverlapping(data.cast::<u8>(), copied.as_mut_ptr(), length) };
        }
        // SAFETY: StartImage transfers this pool allocation to its caller. Release
        // it exactly once before any diagnostic formatting/serial allocation.
        let freed = unsafe { free(data.cast::<u8>()) };
        if range_valid {
            let (text, units, terminated) = escaped_description(&copied[..length]);
            let trailing = if terminated { size.saturating_sub((units + 1) * 2) } else { 0 };
            report(&format!(
                "NEXTCORE: IMAGE_EXIT_DATA bytes={size} copied={length} units={units} terminated={terminated} truncated={} trailing_bytes={trailing}",
                size > length,
            ));
            // Only printable ASCII reaches the stream. CR/LF, ESC, Unicode line
            // separators, quotes and backslashes cannot create another marker.
            report(&format!("NEXTCORE: IMAGE_EXIT_TEXT text=\"{text}\""));
        } else {
            report(&format!("NEXTCORE: IMAGE_EXIT_DATA bytes={size} copied=0 invalid=ADDRESS_OVERFLOW"));
        }
        report(&format!("NEXTCORE: IMAGE_EXIT_DATA_FREE status={freed:?}"));
    }
    status
}

fn escaped_description(bytes: &[u8]) -> (String, usize, bool) {
    let mut text = String::new();
    let mut units = 0;
    let mut terminated = false;
    for pair in bytes.chunks_exact(2) {
        let unit = u16::from_le_bytes([pair[0], pair[1]]);
        if unit == 0 {
            terminated = true;
            break;
        }
        match unit {
            0x22 => text.push_str("\\\""),
            0x5c => text.push_str("\\\\"),
            0x20..=0x7e => text.push(unit as u8 as char),
            _ => { let _ = write!(text, "\\u{unit:04x}"); }
        }
        units += 1;
    }
    (text, units, terminated)
}
