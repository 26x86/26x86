//! Authored EFI callback/ownership probe; no operating-system input.
#![no_std]
#![no_main]
extern crate alloc;
mod console_control;
use console_control::{classify_lookup, Interface, Lease, GRAPHICS, GUID, TEXT};
use core::{arch::asm, ptr};
use uefi::proto::console::serial::Serial;
use uefi::{boot, entry, table, Status};
use uefi_raw::protocol::console::{
    GraphicsOutputModeInformation, GraphicsOutputProtocol, GraphicsOutputProtocolMode,
    GraphicsPixelFormat,
};
use uefi_raw::Boolean;

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

fn lookup() -> (Status, *mut Interface) {
    let services = unsafe { (*table::system_table_raw().unwrap().as_ptr()).boot_services };
    let mut interface = ptr::null_mut();
    let status = unsafe { ((*services).locate_protocol)(&GUID, ptr::null_mut(), &mut interface) };
    (status, interface.cast())
}

fn require(condition: bool, label: &str) -> Result<(), Status> {
    report(&alloc::format!(
        "NXCONSOLE: CHECK name={label} passed={condition}"
    ));
    if condition {
        Ok(())
    } else {
        Err(Status::ABORTED)
    }
}

fn run() -> Result<(), Status> {
    presence_fixtures()?;
    require(lookup().0 == Status::NOT_FOUND, "initial_absence")?;
    let owner = Lease::acquire(report)?;
    let interface = owner.interface();
    require(
        owner.is_owned() && lookup() == (Status::SUCCESS, interface),
        "creation_exact_instance",
    )?;
    let (mut mode, mut graphics, mut locked) = (u32::MAX, Boolean(0xaa), Boolean(0xaa));
    let get = unsafe { (*interface).get_mode };
    let status = unsafe { get(interface, &mut mode, &mut graphics, &mut locked) };
    require(
        status == Status::SUCCESS && mode == TEXT && graphics.0 <= 1 && locked.0 == 0,
        "actual_mode_outputs",
    )?;
    require(
        unsafe { get(interface, ptr::null_mut(), ptr::null_mut(), ptr::null_mut()) }
            == Status::SUCCESS,
        "optional_outputs",
    )?;
    require(
        unsafe { get(ptr::null_mut(), &mut mode, &mut graphics, &mut locked) }
            == Status::INVALID_PARAMETER,
        "null_instance",
    )?;
    let set = unsafe { (*interface).set_mode };
    require(
        unsafe { set(interface, TEXT) } == Status::SUCCESS,
        "firmware_text_transition",
    )?;
    require(
        unsafe { set(interface, GRAPHICS) } == Status::UNSUPPORTED,
        "graphics_rejected",
    )?;
    require(
        unsafe { set(interface, u32::MAX) } == Status::INVALID_PARAMETER,
        "invalid_mode_rejected",
    )?;
    let lock = unsafe { (*interface).lock_stdin };
    let password = [b'X' as u16, 0];
    require(
        unsafe { lock(interface, password.as_ptr()) } == Status::DEVICE_ERROR,
        "lock_rejected",
    )?;
    require(
        unsafe { lock(interface, ptr::null()) } == Status::SUCCESS,
        "already_unlocked",
    )?;
    let borrowed = Lease::acquire(report)?;
    require(
        !borrowed.is_owned() && borrowed.interface() == interface,
        "existing_instance_reused",
    )?;
    borrowed.release();
    require(
        lookup() == (Status::SUCCESS, interface),
        "borrow_release_preserves_instance",
    )?;
    owner.release();
    require(
        lookup().0 == Status::NOT_FOUND,
        "owned_release_removes_instance",
    )?;
    Ok(())
}

/// These are lookup-result regression fixtures, not installed GPU devices.
/// No GOP callback, framebuffer or mode pointer is consumed by a presence query.
fn presence_fixtures() -> Result<(), Status> {
    let services = unsafe { (*table::system_table_raw().unwrap().as_ptr()).boot_services };
    let mut found = ptr::null_mut();
    let status = unsafe {
        ((*services).locate_protocol)(&GraphicsOutputProtocol::GUID, ptr::null_mut(), &mut found)
    };
    if status != Status::SUCCESS || found.is_null() {
        return Err(Status::NOT_READY);
    }
    let original = unsafe { &*found.cast::<GraphicsOutputProtocol>() };
    let mut fixture = GraphicsOutputProtocol {
        query_mode: original.query_mode,
        set_mode: original.set_mode,
        blt: original.blt,
        mode: ptr::null_mut(),
    };
    let pointer = ptr::addr_of_mut!(fixture).cast();
    require(
        classify_lookup(Status::SUCCESS, pointer) == Ok(Some(pointer)),
        "fixture_gop_null_mode_present",
    )?;
    let mut info = GraphicsOutputModeInformation {
        horizontal_resolution: 1280,
        vertical_resolution: 800,
        pixel_format: GraphicsPixelFormat::PIXEL_BLT_ONLY,
        pixels_per_scan_line: 0,
        ..Default::default()
    };
    let mut mode = GraphicsOutputProtocolMode {
        max_mode: 1,
        mode: 0,
        info: &mut info,
        size_of_info: core::mem::size_of::<GraphicsOutputModeInformation>(),
        frame_buffer_base: 0,
        frame_buffer_size: 0,
    };
    fixture.mode = &mut mode;
    require(
        classify_lookup(Status::SUCCESS, pointer) == Ok(Some(pointer)) && fixture.mode == &mut mode,
        "fixture_blt_only_zero_stride_present",
    )?;
    require(
        classify_lookup(Status::NOT_FOUND, ptr::null_mut()) == Ok(None),
        "fixture_missing_protocol_absent",
    )?;
    require(
        classify_lookup(Status::SUCCESS, ptr::null_mut()) == Err(Status::DEVICE_ERROR),
        "fixture_null_success_rejected",
    )?;
    Ok(())
}

#[entry]
fn efi_main() -> Status {
    if uefi::helpers::init().is_err() {
        return Status::NOT_READY;
    }
    report("NXCONSOLE: EFI_ENTRY");
    let value = match run() {
        Ok(()) => {
            report("NXCONSOLE: DONE checks=17 passed=true");
            0x31u32
        }
        Err(status) => {
            report(&alloc::format!("NXCONSOLE: FAILED status={status:?}"));
            0x32u32
        }
    };
    // This explicit authored probe requires QEMU's matching debug-exit device.
    unsafe {
        asm!("out dx, eax", in("dx") 0xf4u16, in("eax") value, options(nomem, nostack, preserves_flags));
    }
    loop {
        unsafe {
            asm!("hlt", options(nomem, nostack));
        }
    }
}
