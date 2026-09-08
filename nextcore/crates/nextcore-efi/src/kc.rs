//! Explicit OVMF KC staging instrument. It never executes collection code.
#![no_std]
#![no_main]
extern crate alloc;
mod firmware_io;
mod loaded_kernel_collection;
use alloc::{
    format,
    string::{String, ToString},
};
use core::arch::asm;
use firmware_io::{read_file, report};
use loaded_kernel_collection::LoadedKernelCollection;
use nextcore_core::kernel_collection::MAX_INPUT_SIZE;
use uefi::{boot, entry, proto::loaded_image::LoadedImage, CString16, Status};
#[global_allocator]
static ALLOCATOR: uefi::allocator::Allocator = uefi::allocator::Allocator;

#[entry]
fn efi_main() -> Status {
    if uefi::helpers::init().is_err() {
        return Status::NOT_READY;
    }
    report("NXKC: EFI_ENTRY");
    match run() {
        Ok(probe) => {
            report("NXKC: DONE preparation_ready=false relocations_applied=false xnu_executed=false native_hal_verified=false macos_boot_verified=false metal_verified=false");
            debug_exit(if probe { 0x2d } else { 0x2b });
        }
        Err(status) => {
            report(&format!("NXKC: ERROR status={status:?}"));
            debug_exit(0x2f);
        }
    }
}
fn options() -> Result<(bool, CString16), Status> {
    let image = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle())
        .map_err(|e| e.status())?;
    let raw = image
        .load_options_as_bytes()
        .ok_or(Status::INVALID_PARAMETER)?;
    if raw.len() > 2 * 1100 {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let text: String = image
        .load_options_as_cstr16()
        .map_err(|_| Status::INVALID_PARAMETER)?
        .to_string();
    let (mode, path) = text.split_once(' ').ok_or(Status::INVALID_PARAMETER)?;
    let probe = match mode {
        "stage" => false,
        "probe-readback-failure" => true,
        _ => return Err(Status::UNSUPPORTED),
    };
    if path.len() > 1024
        || !path.starts_with('\\')
        || path.len() < 2
        || !path
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'\\' | b'.' | b'_' | b'-'))
        || path[1..]
            .split('\\')
            .any(|c| c.is_empty() || c == "." || c == "..")
    {
        return Err(Status::INVALID_PARAMETER);
    }
    Ok((
        probe,
        CString16::try_from(path).map_err(|_| Status::INVALID_PARAMETER)?,
    ))
}
fn run() -> Result<bool, Status> {
    let (probe, path) = options()?;
    report(&format!(
        "NXKC: OPTIONS mode={}",
        if probe {
            "probe-readback-failure"
        } else {
            "stage"
        }
    ));
    let source = read_file(&path, MAX_INPUT_SIZE as u64)?;
    report(&format!("NXKC: SOURCE bytes={}", source.len()));
    let loaded = LoadedKernelCollection::load(&source, report)?;
    let v = loaded.verification();
    report(&format!("NXKC: VERIFIED base={:#x} arena={} copied={} zero_tail={} holes={} member_headers={} member_views={} member_compared={} descriptors={}",
        loaded.physical_base(), v.arena_bytes, v.copied_bytes, v.zero_tail_bytes, v.hole_bytes,
        v.member_headers_checked, v.member_segment_views_checked, v.member_file_bytes_compared, loaded.map_descriptors()));
    if probe {
        loaded.probe_readback_failure()?;
    } else {
        loaded.release()?;
    }
    drop(source);
    Ok(probe)
}
fn debug_exit(value: u32) -> ! {
    // Dedicated QEMU instrument, the explicit host command provides this port.
    unsafe {
        asm!("out dx, eax", in("dx") 0xf4u16, in("eax") value, options(nomem, nostack, preserves_flags));
    }
    loop {
        unsafe {
            asm!("hlt", options(nomem, nostack));
        }
    }
}
