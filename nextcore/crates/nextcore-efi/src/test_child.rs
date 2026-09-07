//! Authored OVMF test application. It is never included in normal bundles.
#![no_std]
#![no_main]
extern crate alloc;
use alloc::vec::Vec;
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
