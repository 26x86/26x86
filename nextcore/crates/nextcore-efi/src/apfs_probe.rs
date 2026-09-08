//! Explicit APFS Jumpstart inspection/driver-start application; no default boot change.
#![no_std]
#![no_main]
extern crate alloc;

mod apfs_driver;
mod exit_data;

use alloc::{format, vec::Vec};
use uefi::proto::{console::serial::Serial, loaded_image::LoadedImage};
use uefi::{boot, prelude::*};

#[global_allocator]
static ALLOCATOR: uefi::allocator::Allocator = uefi::allocator::Allocator;

fn report(message: &str) {
    uefi::println!("{message}");
    if let Ok(handle) = boot::get_handle_for_protocol::<Serial>() {
        if let Ok(mut serial) = boot::open_protocol_exclusive::<Serial>(handle) {
            let _ = serial.write_exact(message.as_bytes());
            let _ = serial.write_exact(b"\r\n");
        }
    }
}

fn start_requested() -> Result<bool, Status> {
    let image = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle())
        .map_err(|e| e.status())?;
    let Some(options) = image.load_options_as_bytes() else {
        return Ok(false);
    };
    if options.is_empty() || options == [0, 0] {
        return Ok(false);
    }
    let expected: Vec<u8> = "--start-driver"
        .encode_utf16()
        .chain(core::iter::once(0))
        .flat_map(u16::to_le_bytes)
        .collect();
    if options == expected {
        Ok(true)
    } else {
        Err(Status::INVALID_PARAMETER)
    }
}

#[entry]
fn efi_main() -> Status {
    uefi::helpers::init().expect("NextCore APFS UEFI initialization");
    report("NXAPFS: EFI_ENTRY");
    let result = start_requested().and_then(|start| apfs_driver::inspect(start, report));
    let status = result.err().unwrap_or(Status::SUCCESS);
    report(&format!("NXAPFS: RESULT status={status:?}"));
    status
}
