//! Explicit APFS Jumpstart inspection/driver-start application; no default boot change.
#![no_std]
#![no_main]
extern crate alloc;

mod apfs_driver;
mod apfs_filesystems;
mod apfs_observation;
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

fn requested_mode() -> Result<apfs_driver::Mode, Status> {
    let image = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle())
        .map_err(|e| e.status())?;
    let Some(options) = image.load_options_as_bytes() else {
        return Ok(apfs_driver::Mode::Extract);
    };
    if options.is_empty() || options == [0, 0] {
        return Ok(apfs_driver::Mode::Extract);
    }
    for (text, mode) in [
        ("--start-driver", apfs_driver::Mode::Start),
        ("--inspect-filesystems", apfs_driver::Mode::Filesystems),
    ] {
        let expected: Vec<u8> = text
            .encode_utf16()
            .chain(core::iter::once(0))
            .flat_map(u16::to_le_bytes)
            .collect();
        if options == expected {
            return Ok(mode);
        }
    }
    Err(Status::INVALID_PARAMETER)
}

#[entry]
fn efi_main() -> Status {
    uefi::helpers::init().expect("NextCore APFS UEFI initialization");
    report("NXAPFS: EFI_ENTRY");
    let result = requested_mode().and_then(|mode| apfs_driver::inspect(mode, report));
    let status = result.err().unwrap_or(Status::SUCCESS);
    report(&format!("NXAPFS: RESULT status={status:?}"));
    status
}
