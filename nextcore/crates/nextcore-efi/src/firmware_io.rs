use alloc::{vec, vec::Vec};
use uefi::proto::{
    console::serial::Serial,
    media::file::{File, FileAttribute, FileInfo, FileMode},
};
use uefi::{boot, CStr16, Status};

pub fn report(message: &str) {
    uefi::println!("{message}");
    if let Ok(handle) = boot::get_handle_for_protocol::<Serial>() {
        if let Ok(mut serial) = boot::open_protocol_exclusive::<Serial>(handle) {
            let _ = serial.write_exact(message.as_bytes());
            let _ = serial.write_exact(b"\r\n");
        }
    }
}

pub fn read_file(path: &CStr16, maximum: u64) -> Result<Vec<u8>, Status> {
    let mut fs = boot::get_image_file_system(boot::image_handle()).map_err(|e| e.status())?;
    let mut root = fs.open_volume().map_err(|e| e.status())?;
    let handle = root
        .open(path, FileMode::Read, FileAttribute::empty())
        .map_err(|e| e.status())?;
    let mut file = handle
        .into_regular_file()
        .ok_or(Status::INVALID_PARAMETER)?;
    let size = file
        .get_boxed_info::<FileInfo>()
        .map_err(|e| e.status())?
        .file_size();
    if size == 0 || size > maximum || size > usize::MAX as u64 {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let mut bytes = vec![0; size as usize];
    let mut position = 0;
    while position < bytes.len() {
        let count = file.read(&mut bytes[position..]).map_err(|e| e.status())?;
        if count == 0 {
            return Err(Status::END_OF_FILE);
        }
        position += count;
    }
    Ok(bytes)
}
