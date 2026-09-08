//! Authored test DriverBinding/SFS forwarder. This is not an APFS filesystem.
#![no_std]
#![no_main]
extern crate alloc;
#[allow(dead_code)]
mod apfs_filesystems;
#[allow(dead_code)]
mod apfs_observation;
use alloc::{boxed::Box, format, vec::Vec};
use core::{ffi::c_void, ptr};
use uefi::proto::{
    console::serial::Serial,
    media::{fs::SimpleFileSystem, partition::PartitionInfo},
};
use uefi::{boot, guid, prelude::*, table, Guid};
use uefi_raw::{
    protocol::{
        device_path::DevicePathProtocol,
        driver::DriverBindingProtocol,
        file_system::{FileProtocolV1, SimpleFileSystemProtocol},
    },
    Handle as RawHandle,
};

#[global_allocator]
static ALLOCATOR: uefi::allocator::Allocator = uefi::allocator::Allocator;
#[used]
static mut CONFIG: [u8; 27] = *b"NEXTCORE_FIXTURE_CHILDREN=1";
const PATH_GUID: Guid = guid!("09576e91-6d3f-11d2-8e39-00a0c969723b");

fn report(text: &str) {
    uefi::println!("{text}");
    if let Ok(handle) = boot::get_handle_for_protocol::<Serial>() {
        if let Ok(mut serial) = boot::open_protocol_exclusive::<Serial>(handle) {
            let _ = serial.write_exact(text.as_bytes());
            let _ = serial.write_exact(b"\r\n");
        }
    }
}
fn services() -> *mut uefi_raw::table::boot::BootServices {
    unsafe { (*table::system_table_raw().unwrap().as_ptr()).boot_services }
}

#[repr(C)]
struct Forward {
    interface: SimpleFileSystemProtocol,
    source: RawHandle,
}
unsafe extern "efiapi" fn open_volume(
    this: *mut SimpleFileSystemProtocol,
    root: *mut *mut FileProtocolV1,
) -> Status {
    if this.is_null() || root.is_null() {
        return Status::INVALID_PARAMETER;
    }
    unsafe {
        *root = ptr::null_mut();
    }
    let source = unsafe { (*this.cast::<Forward>()).source };
    let bt = services();
    let mut interface = ptr::null_mut();
    let agent = boot::image_handle().as_ptr();
    let status = unsafe {
        ((*bt).open_protocol)(
            source,
            &SimpleFileSystemProtocol::GUID,
            &mut interface,
            agent,
            ptr::null_mut(),
            2,
        )
    };
    if status != Status::SUCCESS {
        return status;
    }
    let status = if interface.is_null() {
        Status::UNSUPPORTED
    } else {
        let fs = interface.cast::<SimpleFileSystemProtocol>();
        // Forward to a fresh protocol lookup, never a retained borrowed pointer.
        unsafe { ((*fs).open_volume)(fs, root) }
    };
    let close = unsafe {
        ((*bt).close_protocol)(
            source,
            &SimpleFileSystemProtocol::GUID,
            agent,
            ptr::null_mut(),
        )
    };
    if status == Status::SUCCESS && close != Status::SUCCESS {
        let file = unsafe { *root };
        if !file.is_null() {
            let _ = unsafe { ((*file).close)(file) };
        }
        unsafe {
            *root = ptr::null_mut();
        }
        return close;
    }
    status
}

struct Child {
    path: Box<[u8]>,
    fs: Forward,
    handle: RawHandle,
}
#[repr(C)]
struct State {
    binding: DriverBindingProtocol,
    controller: RawHandle,
    source: RawHandle,
    parent_path: Vec<u8>,
    count: usize,
    started: bool,
    failed: bool,
    // Registered protocol pointers must survive growth of the owner list.
    #[allow(clippy::vec_box)]
    children: Vec<Box<Child>>,
}
unsafe extern "efiapi" fn supported(
    this: *const DriverBindingProtocol,
    controller: RawHandle,
    _: *const DevicePathProtocol,
) -> Status {
    let state = this.cast::<State>();
    if controller != unsafe { (*state).controller } {
        return Status::UNSUPPORTED;
    }
    if unsafe { (*state).failed } {
        return Status::DEVICE_ERROR;
    }
    if unsafe { (*state).started } {
        Status::ALREADY_STARTED
    } else {
        Status::SUCCESS
    }
}
unsafe extern "efiapi" fn start(
    this: *const DriverBindingProtocol,
    controller: RawHandle,
    _: *const DevicePathProtocol,
) -> Status {
    let state = this.cast::<State>().cast_mut();
    let status = unsafe { supported(this, controller, ptr::null()) };
    if status != Status::SUCCESS {
        return status;
    }
    // Reentrant notification cannot publish the same child twice.
    unsafe {
        (*state).started = true;
    }
    let bt = services();
    let count = unsafe { (*state).count };
    report(&format!("NXFSFIX: BIND_START children={count}"));
    for index in 0..count {
        let mut path = unsafe { (*state).parent_path.clone() };
        path.truncate(path.len() - 4);
        path.extend_from_slice(&[4, 3, 21, 0]); // public MEDIA_VENDOR node + one test byte
        path.extend_from_slice(&[
            0x65, 0x34, 0x8a, 0x1e, 0x57, 0x4c, 0x91, 0x44, 0x9c, 0x1f, 0x3c, 0xf4, 0x30, 0xb0,
            0xdd, 0x25,
        ]);
        path.push(index as u8);
        path.extend_from_slice(&[0x7f, 0xff, 4, 0]);
        let mut child = Box::new(Child {
            path: path.into_boxed_slice(),
            handle: ptr::null_mut(),
            fs: Forward {
                interface: SimpleFileSystemProtocol {
                    revision: 0x10000,
                    open_volume,
                },
                source: unsafe { (*state).source },
            },
        });
        let status = unsafe {
            ((*bt).install_protocol_interface)(
                &mut child.handle,
                &PATH_GUID,
                uefi_raw::table::boot::InterfaceType::NATIVE_INTERFACE,
                child.path.as_ptr().cast(),
            )
        };
        if status != Status::SUCCESS {
            unsafe {
                (*state).failed = true;
            }
            report(&format!("NXFSFIX: PUBLISH_ERROR status={status:?}"));
            return status;
        }
        let status = unsafe {
            ((*bt).install_protocol_interface)(
                &mut child.handle,
                &SimpleFileSystemProtocol::GUID,
                uefi_raw::table::boot::InterfaceType::NATIVE_INTERFACE,
                (&child.fs.interface as *const SimpleFileSystemProtocol).cast(),
            )
        };
        // Retain every published pointer for the resident driver's lifetime even
        // on a fixture failure. StartBinding errors do not unload this image.
        unsafe {
            (*state).children.push(child);
        }
        if status != Status::SUCCESS {
            unsafe {
                (*state).failed = true;
            }
            report(&format!("NXFSFIX: PUBLISH_ERROR status={status:?}"));
            return status;
        }
        report(&format!("NXFSFIX: CHILD index={index} published=true"));
    }
    Status::SUCCESS
}
unsafe extern "efiapi" fn stop(
    _: *const DriverBindingProtocol,
    _: RawHandle,
    _: usize,
    _: *const RawHandle,
) -> Status {
    // Test driver remains resident until the harness resets the whole VM.
    Status::UNSUPPORTED
}

fn setup() -> Result<(), Status> {
    let count = unsafe { ptr::read_volatile(ptr::addr_of!(CONFIG).cast::<u8>().add(26)) };
    if !matches!(count, b'1' | b'2') {
        return Err(Status::INVALID_PARAMETER);
    }
    let fs = boot::find_handles::<SimpleFileSystem>().map_err(|e| e.status())?;
    if fs.len() != 1 {
        return Err(Status::NO_MAPPING);
    }
    let mut controller = None;
    for handle in boot::find_handles::<PartitionInfo>().map_err(|e| e.status())? {
        let info = unsafe {
            boot::open_protocol::<PartitionInfo>(
                boot::OpenProtocolParams {
                    handle,
                    agent: boot::image_handle(),
                    controller: None,
                },
                boot::OpenProtocolAttributes::GetProtocol,
            )
        }
        .map_err(|e| e.status())?;
        if info.get().is_some_and(|info| {
            info.gpt_partition_entry().is_some_and(|entry| {
                let kind = entry.partition_type_guid;
                kind.0 == guid!("7c3457ef-0000-11aa-aa11-00306543ecac")
            })
        }) && controller.replace(handle).is_some()
        {
            return Err(Status::NO_MAPPING);
        }
    }
    let controller = controller.ok_or(Status::NOT_FOUND)?;
    let parent_path = apfs_filesystems::device_path(controller)?;
    let image = boot::image_handle().as_ptr();
    let state = Box::new(State {
        binding: DriverBindingProtocol {
            supported,
            start,
            stop,
            version: 1,
            image_handle: image,
            driver_binding_handle: image,
        },
        controller: controller.as_ptr(),
        source: fs[0].as_ptr(),
        parent_path,
        count: (count - b'0') as usize,
        started: false,
        failed: false,
        children: Vec::new(),
    });
    let raw = Box::into_raw(state);
    let mut handle = image;
    let status = unsafe {
        ((*services()).install_protocol_interface)(
            &mut handle,
            &DriverBindingProtocol::GUID,
            uefi_raw::table::boot::InterfaceType::NATIVE_INTERFACE,
            raw.cast::<c_void>(),
        )
    };
    if status != Status::SUCCESS {
        unsafe {
            drop(Box::from_raw(raw));
        }
        return Err(status);
    }
    report(&format!("NXFSFIX: BINDING_READY children={}", count - b'0'));
    Ok(())
}
#[entry]
fn efi_main() -> Status {
    uefi::helpers::init().expect("authored SFS fixture init");
    report("NXFSFIX: EFI_ENTRY");
    setup().err().unwrap_or(Status::SUCCESS)
}
