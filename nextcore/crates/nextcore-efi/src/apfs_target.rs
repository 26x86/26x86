//! Selected-entry APFS image resolution; the caller owns application lifetime.
use alloc::{
    format,
    string::{String, ToString},
};
use core::ptr;
use nextcore_core::boot_config::BootTarget;
use uefi::proto::{device_path::media, loaded_image::LoadedImage};
use uefi::{boot, table, Handle, Status};

pub fn load(target: &BootTarget, report: fn(&str)) -> Result<Handle, Status> {
    let label = target
        .apfs_volume
        .as_deref()
        .ok_or(Status::INVALID_PARAMETER)?;
    report("NEXTCORE: APFS_TARGET_BEGIN");
    let controller = crate::apfs_driver::connect_for_target(report)?;
    let volume = crate::apfs_filesystems::select_volume(controller, label, report)?;
    // Retain the existing self-reference policy only when this is actually the
    // current image's volume. Equal paths on a different volume are legitimate.
    let current = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle())
        .map_err(|e| e.status())?;
    let device = current
        .get()
        .ok_or(Status::UNSUPPORTED)?
        .device()
        .ok_or(Status::NOT_FOUND)?;
    if crate::apfs_filesystems::device_path(device)? == volume {
        let mut own = String::new();
        // The current LoadedImage file_path is the pre-existing trusted firmware
        // image ABI. New discovered filesystem paths use the bounded raw reader.
        for node in current.file_path().ok_or(Status::UNSUPPORTED)?.node_iter() {
            if let Ok(path) = <&media::FilePath>::try_from(node) {
                own.push_str(
                    &path
                        .path_name()
                        .to_cstring16()
                        .map_err(|_| Status::INVALID_PARAMETER)?
                        .to_string(),
                );
            }
        }
        if own.replace('/', "\\").eq_ignore_ascii_case(&target.path) {
            drop(current);
            report("NEXTCORE: TARGET_REJECTED reason=SELF_REFERENCE");
            return Err(Status::INVALID_PARAMETER);
        }
    }
    drop(current);
    let path = crate::apfs_observation::image_path(&volume, &target.path)
        .map_err(|_| Status::INVALID_PARAMETER)?;
    let system = table::system_table_raw().ok_or(Status::NOT_READY)?;
    let services = unsafe { (*system.as_ptr()).boot_services };
    if services.is_null() {
        return Err(Status::NOT_READY);
    }
    let mut raw = ptr::null_mut();
    report("NEXTCORE: IMAGE_LOAD_BEGIN");
    // SAFETY: all leases are released; the owned validated path lives across
    // synchronous LoadImage. Null source/zero size request firmware file loading.
    let status = unsafe {
        ((*services).load_image)(
            false.into(),
            boot::image_handle().as_ptr(),
            path.as_ptr().cast(),
            ptr::null(),
            0,
            &mut raw,
        )
    };
    let handle = unsafe { Handle::from_ptr(raw) };
    if status != Status::SUCCESS {
        if let Some(handle) = handle {
            let cleanup = boot::unload_image(handle)
                .err()
                .map(|e| e.status())
                .unwrap_or(Status::SUCCESS);
            report(&format!(
                "NEXTCORE: APFS_LOAD_REJECT_CLEANUP status={cleanup:?}"
            ));
        }
        return Err(status);
    }
    handle.ok_or(Status::LOAD_ERROR)
}
