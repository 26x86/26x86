//! Authored OVMF test application. It is never included in normal bundles.
#![no_std]
#![no_main]
extern crate alloc;
use alloc::{vec, vec::Vec};
use uefi::proto::{console::serial::Serial, loaded_image::LoadedImage};
use uefi::{boot, prelude::*};

#[global_allocator]
static ALLOCATOR: uefi::allocator::Allocator = uefi::allocator::Allocator;

fn report(text: &str) {
    uefi::println!("{text}");
    if let Ok(handle) = boot::get_handle_for_protocol::<Serial>() {
        if let Ok(mut serial) = boot::open_protocol_exclusive::<Serial>(handle) {
            let _ = serial.write_exact(text.as_bytes());
            let _ = serial.write_exact(b"\r\n");
        }
    }
}

#[entry]
fn efi_main() -> Status {
    uefi::helpers::init().expect("test child UEFI initialization");
    report("NXTEST: EFI_ENTRY");
    let result = (|| {
        let image = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle()).ok()?;
        let Some(bytes) = image.load_options_as_bytes() else {
            return Some(("NXTEST: OPTIONS_EMPTY", Status::SUCCESS));
        };
        for kind in ["text", "empty", "blank", "controls", "long", "binary"] {
            let command = alloc::format!("nextcore-child-exit-{kind}");
            let expected: Vec<u8> = command.encode_utf16().chain(core::iter::once(0)).flat_map(u16::to_le_bytes).collect();
            if bytes == expected {
                // Release the protocol guard before Exit unloads this image.
                drop(image);
                drop(expected);
                drop(command);
                explicit_exit(kind);
            }
        }
        // Compare exact UTF-16LE bytes, including the terminator, independently
        // of the parent's conversion; supplementary characters are permitted.
        for (text, marker, status) in [
            (
                "nextcore-child-success 한글",
                "NXTEST: OPTIONS_OK",
                Status::SUCCESS,
            ),
            (
                "nextcore-child-error",
                "NXTEST: OPTIONS_OK",
                Status::ABORTED,
            ),
            (
                "nextcore-child-utf16 🚀",
                "NXTEST: OPTIONS_UTF16",
                Status::SUCCESS,
            ),
        ] {
            let expected: Vec<u8> = text
                .encode_utf16()
                .chain(core::iter::once(0))
                .flat_map(u16::to_le_bytes)
                .collect();
            if bytes == expected {
                return Some((marker, status));
            }
        }
        None
    })();
    if let Some((marker, status)) = result {
        report(marker);
        status
    } else {
        report("NXTEST: OPTIONS_INVALID");
        Status::INVALID_PARAMETER
    }
}

fn explicit_exit(kind: &str) -> ! {
    let mut bytes: Vec<u8> = match kind {
        "empty" => Vec::new(),
        "blank" => vec![0, 0],
        "long" => vec![b'L' as u16; 1536].into_iter().chain(core::iter::once(0)).flat_map(u16::to_le_bytes).collect(),
        "controls" => "first\r\nNEXTCORE: IMAGE_RETURN status=SUCCESS\t\u{1b}[2J\"\\\u{2028}tail".encode_utf16().chain(core::iter::once(0)).flat_map(u16::to_le_bytes).collect(),
        _ => "authored failure".encode_utf16().chain(core::iter::once(0)).flat_map(u16::to_le_bytes).collect(),
    };
    if kind == "binary" {
        bytes.extend_from_slice(&[0xff, 0x0a, 0x80]);
    }
    report(&alloc::format!("NXTEST: EXPLICIT_EXIT kind={kind}"));
    let system = uefi::table::system_table_raw().expect("live system table");
    let services = unsafe { (*system.as_ptr()).boot_services };
    let pointer = if bytes.is_empty() { core::ptr::null_mut() } else { bytes.as_mut_ptr().cast() };
    // SAFETY: valid image handle; this Vec<u8>'s <=8-byte alignment uses the
    // UEFI AllocatePool path directly. ExitData ownership transfers to the caller
    // of StartImage; no protocol guard or other owned allocation survives Exit.
    let status = unsafe { ((*services).exit)(boot::image_handle().as_ptr(), Status::ABORTED, bytes.len(), pointer) };
    report(&alloc::format!("NXTEST: EXIT_UNEXPECTED_RETURN status={status:?}"));
    loop { core::hint::spin_loop(); }
}
