//! Read-only UEFI filesystem observation, scoped by a bounded device path.
use crate::apfs_observation::{self as checked, Budget, Entry, VolumeInfo};
use alloc::{format, string::String, vec::Vec};
use core::{ffi::c_void, ptr};
use uefi::proto::media::fs::SimpleFileSystem;
use uefi::{boot, guid, table, Guid, Handle, Status};
use uefi_raw::protocol::file_system::{
    FileInfo, FileProtocolV1, FileSystemInfo, SimpleFileSystemProtocol,
};

const PATH_GUID: Guid = guid!("09576e91-6d3f-11d2-8e39-00a0c969723b");
const MAX_HANDLES: usize = 256;
const MAX_VOLUMES: usize = 32;
const _: () = assert!(core::mem::offset_of!(FileInfo, file_name) == 80);
const _: () = assert!(core::mem::offset_of!(FileSystemInfo, volume_label) == 36);

fn invalid(error: checked::Invalid) -> Status {
    if error == checked::Invalid::Limit {
        Status::BAD_BUFFER_SIZE
    } else {
        Status::VOLUME_CORRUPTED
    }
}

/// Raw GET_PROTOCOL avoids DevicePath's unbounded DST-size walk. No Rust
/// reference to a firmware interface survives a call into that interface.
struct Protocol {
    handle: Handle,
    guid: Guid,
    interface: *mut c_void,
    active: bool,
}
impl Protocol {
    fn open(handle: Handle, guid: Guid) -> Result<Self, Status> {
        let system = table::system_table_raw().ok_or(Status::NOT_READY)?;
        let services = unsafe { (*system.as_ptr()).boot_services };
        if services.is_null() {
            return Err(Status::NOT_READY);
        }
        let mut interface = ptr::null_mut();
        // SAFETY: live firmware table and initialized out parameter. GET_PROTOCOL
        // does not disconnect the driver; this module does not dispatch/mutate
        // protocol registration while the resulting pointer is in use.
        let status = unsafe {
            ((*services).open_protocol)(
                handle.as_ptr(),
                &guid,
                &mut interface,
                boot::image_handle().as_ptr(),
                ptr::null_mut(),
                2,
            )
        };
        if status != Status::SUCCESS {
            return Err(status);
        }
        let lease = Self {
            handle,
            guid,
            interface,
            active: true,
        };
        if interface.is_null() {
            return Err(Status::UNSUPPORTED);
        }
        Ok(lease)
    }
    fn close(&mut self) -> Status {
        if !self.active {
            return Status::SUCCESS;
        }
        self.active = false;
        let Some(system) = table::system_table_raw() else {
            return Status::NOT_READY;
        };
        let services = unsafe { (*system.as_ptr()).boot_services };
        if services.is_null() {
            return Status::NOT_READY;
        }
        // SAFETY: exactly the successful OpenProtocol tuple, once only.
        unsafe {
            ((*services).close_protocol)(
                self.handle.as_ptr(),
                &self.guid,
                boot::image_handle().as_ptr(),
                ptr::null_mut(),
            )
        }
    }
}
impl Drop for Protocol {
    fn drop(&mut self) {
        let _ = self.close();
    }
}

pub fn device_path(handle: Handle) -> Result<Vec<u8>, Status> {
    let mut lease = Protocol::open(handle, PATH_GUID)?;
    let result = (|| {
        let base = lease.interface.cast::<u8>();
        let mut bytes = Vec::new();
        bytes
            .try_reserve_exact(checked::MAX_PATH)
            .map_err(|_| Status::OUT_OF_RESOURCES)?;
        for _ in 0..checked::MAX_NODES {
            let offset = bytes.len();
            if offset + 4 > checked::MAX_PATH {
                return Err(Status::BAD_BUFFER_SIZE);
            }
            // SAFETY: a successful firmware DevicePath protocol supplies readable
            // node storage. Read only its fixed header first; never ask the uefi
            // DST constructor to walk an unbounded path. Firmware pointer validity
            // is the UEFI trust boundary, not established by the length cap.
            let header = unsafe { core::slice::from_raw_parts(base.add(offset), 4) };
            let length = u16::from_le_bytes([header[2], header[3]]) as usize;
            if length < 4 || length > checked::MAX_PATH - offset {
                return Err(Status::BAD_BUFFER_SIZE);
            }
            let end = header[0] == 0x7f;
            // SAFETY: length checked before reading this firmware-owned node.
            bytes.extend_from_slice(unsafe {
                core::slice::from_raw_parts(base.add(offset), length)
            });
            if end {
                checked::path_body(&bytes).map_err(invalid)?;
                return Ok(bytes);
            }
        }
        Err(Status::BAD_BUFFER_SIZE)
    })();
    let close = lease.close();
    if close != Status::SUCCESS {
        return Err(close);
    }
    result
}

struct Root(*mut FileProtocolV1);
impl Root {
    fn close(&mut self) -> Status {
        if self.0.is_null() {
            return Status::SUCCESS;
        }
        let handle = core::mem::replace(&mut self.0, ptr::null_mut());
        // SAFETY: unique root returned by a successful OpenVolume, closed once.
        unsafe { ((*handle).close)(handle) }
    }
    fn response<'a>(
        &mut self,
        info: Option<Guid>,
        buffer: &'a mut Buffer,
        budget: &mut Budget,
    ) -> Result<&'a [u8], Status> {
        buffer.0.fill(0);
        let capacity = budget.capacity().map_err(invalid)?;
        let mut size = capacity;
        // SAFETY: live open root and aligned initialized buffer with the exact
        // advertised capacity. The driver must respect UEFI's BufferSize ABI.
        let status = unsafe {
            match info {
                Some(guid) => {
                    ((*self.0).get_info)(self.0, &guid, &mut size, buffer.0.as_mut_ptr().cast())
                }
                None => ((*self.0).read)(self.0, &mut size, buffer.0.as_mut_ptr().cast()),
            }
        };
        if status != Status::SUCCESS {
            return Err(status);
        }
        budget.response(size, capacity).map_err(invalid)?;
        Ok(&buffer.0[..size])
    }
}
impl Drop for Root {
    fn drop(&mut self) {
        let _ = self.close();
    }
}
#[repr(align(8))]
struct Buffer([u8; checked::MAX_RECORD]);

struct Volume {
    path: Vec<u8>,
    opened: bool,
    info: Option<VolumeInfo>,
    root_verified: bool,
    entries: Vec<Entry>,
    records: usize,
    read_calls: usize,
    eof: bool,
    close_status: Option<Status>,
    protocol_close_status: Option<Status>,
    status: Status,
}
impl Volume {
    fn new(path: Vec<u8>) -> Self {
        Self {
            path,
            opened: false,
            info: None,
            root_verified: false,
            entries: Vec::new(),
            records: 0,
            read_calls: 0,
            eof: false,
            close_status: None,
            protocol_close_status: None,
            status: Status::NOT_READY,
        }
    }
}

fn observe_volume(
    handle: Handle,
    volume: &mut Volume,
    budget: &mut Budget,
    enumerate: bool,
) -> Result<(), Status> {
    let mut lease = Protocol::open(handle, SimpleFileSystemProtocol::GUID)?;
    let result = (|| {
        let interface = lease.interface.cast::<SimpleFileSystemProtocol>();
        let mut raw_root = ptr::null_mut();
        // SAFETY: fixed-size protocol from successful OpenProtocol. No borrowed
        // typed reference crosses the call or escapes the enclosing lease.
        let status = unsafe { ((*interface).open_volume)(interface, &mut raw_root) };
        if status != Status::SUCCESS {
            return Err(status);
        }
        if raw_root.is_null() {
            return Err(Status::UNSUPPORTED);
        }
        let mut root = Root(raw_root);
        volume.opened = true;
        let result = (|| {
            let mut buffer = Buffer([0; checked::MAX_RECORD]);
            let bytes = root.response(Some(FileSystemInfo::ID), &mut buffer, budget)?;
            volume.info = Some(checked::volume_info(bytes).map_err(invalid)?);
            if !enumerate {
                return Ok(());
            }
            let bytes = root.response(Some(FileInfo::ID), &mut buffer, budget)?;
            checked::entry(bytes, true).map_err(invalid)?;
            volume.root_verified = true;
            loop {
                volume.read_calls += 1;
                let bytes = root.response(None, &mut buffer, budget)?;
                if bytes.is_empty() {
                    volume.eof = true;
                    return Ok(());
                }
                budget.record(volume.records).map_err(invalid)?;
                volume.records += 1;
                let entry = checked::entry(bytes, false).map_err(invalid)?;
                if !entry.dot {
                    if volume.entries.iter().any(|old| old.name == entry.name) {
                        return Err(Status::VOLUME_CORRUPTED);
                    }
                    volume
                        .entries
                        .try_reserve(1)
                        .map_err(|_| Status::OUT_OF_RESOURCES)?;
                    volume.entries.push(entry);
                }
            }
        })();
        let close = root.close();
        volume.close_status = Some(close);
        if close != Status::SUCCESS {
            return Err(close);
        }
        result
    })();
    let close = lease.close();
    volume.protocol_close_status = Some(close);
    if close != Status::SUCCESS {
        return Err(close);
    }
    result
}

fn collect(
    controller: Handle,
    volumes: &mut Vec<Volume>,
    budget: &mut Budget,
    examined: &mut usize,
) -> Result<(), Status> {
    let candidates = candidates(controller, examined)?;
    volumes
        .try_reserve_exact(candidates.len())
        .map_err(|_| Status::OUT_OF_RESOURCES)?;
    for (handle, path) in candidates {
        let mut volume = Volume::new(path);
        let result = observe_volume(handle, &mut volume, budget, true);
        volume.status = result.as_ref().err().copied().unwrap_or(Status::SUCCESS);
        volumes.push(volume);
        result?;
    }
    Ok(())
}

fn candidates(controller: Handle, examined: &mut usize) -> Result<Vec<(Handle, Vec<u8>)>, Status> {
    let parent = device_path(controller)?;
    let handles = boot::find_handles::<SimpleFileSystem>().map_err(|e| e.status())?;
    if handles.len() > MAX_HANDLES {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let mut candidates = Vec::new();
    for handle in handles {
        *examined += 1;
        let path = match device_path(handle) {
            Ok(path) => path,
            Err(Status::UNSUPPORTED | Status::NOT_FOUND) => continue,
            Err(status) => return Err(status),
        };
        if !checked::descendant(&parent, &path).map_err(invalid)? {
            continue;
        }
        if candidates.len() == MAX_VOLUMES {
            return Err(Status::BAD_BUFFER_SIZE);
        }
        if candidates.iter().any(|(_, previous)| previous == &path) {
            return Err(Status::NO_MAPPING);
        }
        candidates
            .try_reserve(1)
            .map_err(|_| Status::OUT_OF_RESOURCES)?;
        candidates.push((handle, path));
    }
    if candidates.is_empty() {
        return Err(Status::NOT_FOUND);
    }
    Ok(candidates)
}

// Selected-entry BOOTX64 API; standalone NXAPFS retains its observation mode.
#[allow(dead_code)]
pub fn select_volume(controller: Handle, label: &str, report: fn(&str)) -> Result<Vec<u8>, Status> {
    let wanted: Vec<u16> = label.encode_utf16().collect();
    if wanted.is_empty() || wanted.len() > checked::MAX_NAME {
        return Err(Status::INVALID_PARAMETER);
    }
    let mut examined = 0;
    let mut observed = Vec::new();
    let mut budget = Budget::default();
    let result = (|| {
        let candidates = candidates(controller, &mut examined)?;
        observed
            .try_reserve_exact(candidates.len())
            .map_err(|_| Status::OUT_OF_RESOURCES)?;
        let mut selected = None;
        let mut matches = 0;
        for (handle, path) in candidates {
            let mut volume = Volume::new(path);
            let result = observe_volume(handle, &mut volume, &mut budget, false);
            volume.status = result.as_ref().err().copied().unwrap_or(Status::SUCCESS);
            let matched = volume
                .info
                .as_ref()
                .is_some_and(|info| info.label_utf16 == wanted);
            if result.is_ok() && matched {
                matches += 1;
                if selected.is_none() {
                    selected = Some(volume.path.clone());
                }
            }
            observed.push((volume, matched));
            result?;
        }
        match matches {
            0 => Err(Status::NOT_FOUND),
            1 => selected.ok_or(Status::NOT_FOUND),
            _ => Err(Status::NO_MAPPING),
        }
    })();
    // collect/observe_volume have released every lease before any callback.
    for (index, (volume, matched)) in observed.iter().enumerate() {
        report(&format!("NEXTCORE: APFS_LABEL index={index} matched={matched} open={} close={:?} protocol_close={:?} status={:?}",
            volume.opened, volume.close_status, volume.protocol_close_status, volume.status));
    }
    report(&format!("NEXTCORE: APFS_SELECT examined={examined} candidates={} matches={} metadata_bytes={} status={:?}",
        observed.len(), observed.iter().filter(|(_, matched)| *matched).count(), budget.bytes,
        result.as_ref().err().copied().unwrap_or(Status::SUCCESS)));
    result
}

pub fn inspect(controller: Handle, report: fn(&str)) -> Result<(), Status> {
    let mut volumes = Vec::new();
    let mut budget = Budget::default();
    let mut examined = 0;
    let result = collect(controller, &mut volumes, &mut budget, &mut examined);
    // All firmware protocol/file leases are gone before arbitrary callbacks.
    report(&format!(
        "NXAPFS: FS_SCAN examined={examined} observed={} depth=1",
        volumes.len()
    ));
    for (index, volume) in volumes.iter().enumerate() {
        let mut path = String::new();
        for byte in &volume.path {
            path.push_str(&format!("{byte:02x}"));
        }
        report(&format!(
            "NXAPFS: FS_PATH index={index} canonical_hex={path}"
        ));
        if let Some(info) = &volume.info {
            report(&format!("NXAPFS: FS_INFO index={index} label=\"{}\" read_only={} volume_size={} free_space={} block_size={}",
                info.label, info.read_only, info.size, info.free_space, info.block_size));
        }
        for entry in &volume.entries {
            report(&format!("NXAPFS: FS_ENTRY index={index} path=\"\\\\{}\" directory={} file_size={} physical_size={} attributes={:#x}",
                entry.name, entry.directory, entry.file_size, entry.physical_size, entry.attributes));
        }
        report(&format!("NXAPFS: FS_VOLUME index={index} open={} root_verified={} records={} entries={} read_calls={} eof={} close={:?} protocol_close={:?} status={:?}",
            volume.opened, volume.root_verified, volume.records, volume.entries.len(), volume.read_calls,
            volume.eof, volume.close_status, volume.protocol_close_status, volume.status));
    }
    report(&format!(
        "NXAPFS: FS_DONE volumes={} records={} metadata_bytes={} complete={} status={:?}",
        volumes.len(),
        budget.entries,
        budget.bytes,
        result.is_ok(),
        result.as_ref().err().copied().unwrap_or(Status::SUCCESS)
    ));
    result
}
