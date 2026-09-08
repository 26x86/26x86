//! Firmware adapter for the public APFS Jumpstart format (BP24).
use alloc::{format, string::String};
use core::ptr;
use nextcore_core::apfs_jumpstart::{
    extract_jumpstart, JumpstartDriver, JumpstartError, JumpstartLimits, ReadAt,
};
use uefi::boot::{OpenProtocolAttributes, OpenProtocolParams, ScopedProtocol};
use uefi::mem::memory_map::MemoryType;
use uefi::proto::{
    device_path::DevicePath,
    loaded_image::LoadedImage,
    media::{block::BlockIO, disk::DiskIo, partition::PartitionInfo},
    ProtocolPointer,
};
use uefi::{boot, guid, table, Handle, Status};

const MAX_PARTITION_HANDLES: usize = 256;

// GET_PROTOCOL avoids disconnecting existing disk/filesystem drivers. The
// returned shared references are used only synchronously: no dispatch, protocol
// installation/removal, connect/disconnect or image start while they are borrowed.
// In particular every guard is dropped before transferring control to a driver.
fn read_protocol<P: ProtocolPointer + ?Sized>(handle: Handle) -> Result<ScopedProtocol<P>, Status> {
    let protocol = unsafe {
        boot::open_protocol::<P>(
            OpenProtocolParams {
                handle,
                agent: boot::image_handle(),
                controller: None,
            },
            OpenProtocolAttributes::GetProtocol,
        )
    }
    .map_err(|e| e.status())?;
    if protocol.get().is_none() {
        return Err(Status::UNSUPPORTED);
    }
    Ok(protocol)
}

struct PartitionReader<'a> {
    disk: &'a DiskIo,
    media_id: u32,
    length: u64,
}
impl ReadAt for PartitionReader<'_> {
    type Error = Status;
    fn read_exact_at(&mut self, offset: u64, out: &mut [u8]) -> Result<(), Status> {
        let end = offset
            .checked_add(out.len() as u64)
            .ok_or(Status::BAD_BUFFER_SIZE)?;
        if end > self.length {
            return Err(Status::END_OF_FILE);
        }
        self.disk
            .read_disk(self.media_id, offset, out)
            .map_err(|e| e.status())
    }
}

fn extract_status(error: JumpstartError<Status>) -> Status {
    match error {
        JumpstartError::Io(status) => status,
        _ => Status::VOLUME_CORRUPTED,
    }
}

fn candidate() -> Result<Handle, Status> {
    let handles = boot::find_handles::<PartitionInfo>().map_err(|e| e.status())?;
    if handles.len() > MAX_PARTITION_HANDLES {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let mut found = None;
    for handle in handles {
        let info = read_protocol::<PartitionInfo>(handle)?;
        if info.gpt_partition_entry().is_some_and(|entry| {
            let kind = entry.partition_type_guid;
            kind.0 == guid!("7c3457ef-0000-11aa-aa11-00306543ecac")
        }) && found.replace(handle).is_some()
        {
            return Err(Status::NO_MAPPING);
        }
    }
    found.ok_or(Status::NOT_FOUND)
}

fn media_geometry(block: &BlockIO) -> Result<(u32, u32, u64), Status> {
    let media = block.media();
    if !media.is_media_present() {
        return Err(Status::NO_MEDIA);
    }
    if !media.is_logical_partition() {
        return Err(Status::UNSUPPORTED);
    }
    let size = media.block_size();
    if !(512..=65536).contains(&size) || !size.is_power_of_two() {
        return Err(Status::UNSUPPORTED);
    }
    let length = media
        .last_block()
        .checked_add(1)
        .and_then(|blocks| blocks.checked_mul(u64::from(size)))
        .ok_or(Status::BAD_BUFFER_SIZE)?;
    Ok((media.media_id(), size, length))
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Extract,
    Start,
    Filesystems,
}

pub fn inspect(mode: Mode, report: fn(&str)) -> Result<(), Status> {
    let handle = candidate()?;
    let mut reason = None;
    let driver = read_driver(handle, &mut reason);
    // The helper has released all GET_PROTOCOL guards before calling arbitrary
    // reporting code, which may itself open or disconnect another protocol.
    if let Some(reason) = reason {
        report(&format!("NXAPFS: EXTRACT_ERROR reason={reason}"));
    }
    let driver = driver?;
    report(&format!(
        "NXAPFS: EXTRACT_OK bytes={} block_size={} extents={} readback=true",
        driver.bytes.len(),
        driver.block_size,
        driver.extents.len()
    ));
    if mode == Mode::Extract {
        report("NXAPFS: INSPECT_ONLY driver_started=false");
        return Ok(());
    }
    start_driver(handle, &driver.bytes, report)?;
    if mode == Mode::Filesystems {
        crate::apfs_filesystems::inspect(handle, report)?;
    }
    Ok(())
}

fn read_driver(handle: Handle, reason: &mut Option<String>) -> Result<JumpstartDriver, Status> {
    let info = read_protocol::<PartitionInfo>(handle)?;
    let entry = info.gpt_partition_entry().ok_or(Status::UNSUPPORTED)?;
    let blocks = entry.num_blocks().ok_or(Status::BAD_BUFFER_SIZE)?;
    let block = read_protocol::<BlockIO>(handle)?;
    let geometry = media_geometry(&block)?;
    if blocks.checked_mul(u64::from(geometry.1)) != Some(geometry.2) {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let disk = read_protocol::<DiskIo>(handle)?;
    let mut reader = PartitionReader {
        disk: &disk,
        media_id: geometry.0,
        length: geometry.2,
    };
    let driver = extract_jumpstart(&mut reader, geometry.2, JumpstartLimits::default()).map_err(
        |error| {
            *reason = Some(format!("{error:?}"));
            extract_status(error)
        },
    )?;
    // Full second extraction checks every metadata block and driver byte via
    // independent reads before execution. This is consistency, not signature
    // authentication; firmware LoadImage remains the image policy authority.
    let repeated = extract_jumpstart(&mut reader, geometry.2, JumpstartLimits::default())
        .map_err(extract_status)?;
    if driver.bytes != repeated.bytes
        || driver.container_uuid != repeated.container_uuid
        || driver.block_size != repeated.block_size
        || driver.container_block_count != repeated.container_block_count
        || driver.jumpstart_block != repeated.jumpstart_block
        || driver.extents != repeated.extents
        || media_geometry(&block)? != geometry
    {
        return Err(Status::MEDIA_CHANGED);
    }
    Ok(driver)
}

// uefi 0.40's safe LoadImage wrapper discards a returned handle on failure.
// UEFI 2.10 section 7.4.1 explicitly permits SECURITY_VIOLATION with a loaded
// image. Keep that handle so a rejected image is unloaded instead of leaked.
fn load_driver(bytes: &[u8], path: &DevicePath, report: fn(&str)) -> Result<Handle, Status> {
    let system = table::system_table_raw().ok_or(Status::NOT_READY)?;
    let services = unsafe { (*system.as_ptr()).boot_services };
    if services.is_null() {
        return Err(Status::NOT_READY);
    }
    let load = unsafe { (*services).load_image };
    let mut raw = ptr::null_mut();
    // SAFETY: boot services are live; source and device path are valid for this
    // synchronous call. Firmware owns validation and the copied loaded image.
    let status = unsafe {
        load(
            false.into(),
            boot::image_handle().as_ptr(),
            path.as_ffi_ptr().cast(),
            bytes.as_ptr().cast(),
            bytes.len(),
            &mut raw,
        )
    };
    let handle = unsafe { Handle::from_ptr(raw) };
    if status != Status::SUCCESS {
        if let Some(handle) = handle {
            let cleanup = boot::unload_image(handle);
            report(&format!(
                "NXAPFS: LOAD_REJECT_CLEANUP status={:?}",
                cleanup.err().map(|e| e.status()).unwrap_or(Status::SUCCESS)
            ));
        }
        return Err(status);
    }
    handle.ok_or(Status::LOAD_ERROR)
}

fn start_driver(controller: Handle, bytes: &[u8], report: fn(&str)) -> Result<(), Status> {
    let path = {
        let path = read_protocol::<DevicePath>(controller)?;
        path.to_boxed()
    };
    let child = load_driver(bytes, &path, report)?;
    drop(path);
    let accepted = (|| {
        let image = boot::open_protocol_exclusive::<LoadedImage>(child).map_err(|e| e.status())?;
        if image.code_type() != MemoryType::BOOT_SERVICES_CODE
            || image.data_type() != MemoryType::BOOT_SERVICES_DATA
        {
            return Err(Status::UNSUPPORTED);
        }
        Ok(())
    })();
    if let Err(status) = accepted {
        let cleanup = boot::unload_image(child);
        report(&format!(
            "NXAPFS: NOT_BOOT_DRIVER cleanup={:?}",
            cleanup.err().map(|e| e.status()).unwrap_or(Status::SUCCESS)
        ));
        return Err(status);
    }
    report("NXAPFS: DRIVER_START");
    let status = crate::exit_data::start_image(child, report);
    report(&format!("NXAPFS: DRIVER_RETURN status={status:?}"));
    if status != Status::SUCCESS {
        // A driver error normally unloads itself. A pre-entry error may leave an
        // image; UnloadImage handles both cases without borrowed parent pointers.
        let cleanup = boot::unload_image(child);
        report(&format!(
            "NXAPFS: START_REJECT_CLEANUP status={:?}",
            cleanup.err().map(|e| e.status()).unwrap_or(Status::SUCCESS)
        ));
        return Err(status);
    }
    report("NXAPFS: DRIVER_RESIDENT");
    let status = boot::connect_controller(controller, &[Some(child), None], None, true)
        .err()
        .map(|e| e.status())
        .unwrap_or(Status::SUCCESS);
    report(&format!("NXAPFS: CONNECT status={status:?}"));
    if status != Status::SUCCESS {
        return Err(status);
    }
    Ok(())
}
