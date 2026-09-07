use crate::error::{CoreError, Result};

const BOOT_ARGS_MAGIC: u32 = 0x4D656D41;

#[derive(Debug, Clone)]
pub struct BootArgs {
    pub magic: u32,
    pub version: u32,
    pub flags: u64,
    pub memory_map: MemoryMap,
    pub kernel_base: u64,
    pub kernel_size: u64,
    pub command_line: String,
    pub device_tree: Option<DeviceTreeBuf>,
}

#[derive(Debug, Clone)]
pub struct MemoryMap {
    pub entries: Vec<MemoryEntry>,
    pub total_size: u64,
}

#[derive(Debug, Clone)]
pub struct MemoryEntry {
    pub base: u64,
    pub size: u64,
    pub kind: MemoryKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u32)]
pub enum MemoryKind {
    EfiReserved = 0,
    EfiLoaderCode = 1,
    EfiLoaderData = 2,
    EfiBootServicesCode = 3,
    EfiBootServicesData = 4,
    EfiRuntimeServicesCode = 5,
    EfiRuntimeServicesData = 6,
    EfiConventional = 7,
    EfiUnusable = 8,
    EfiACPIReclaim = 9,
    EfiACPINVS = 10,
    EfiMemoryMap = 11,
    EfiPersistent = 12,
}

impl MemoryKind {
    pub fn from_u32(v: u32) -> Option<Self> {
        match v {
            0 => Some(Self::EfiReserved),
            1 => Some(Self::EfiLoaderCode),
            2 => Some(Self::EfiLoaderData),
            3 => Some(Self::EfiBootServicesCode),
            4 => Some(Self::EfiBootServicesData),
            5 => Some(Self::EfiRuntimeServicesCode),
            6 => Some(Self::EfiRuntimeServicesData),
            7 => Some(Self::EfiConventional),
            8 => Some(Self::EfiUnusable),
            9 => Some(Self::EfiACPIReclaim),
            10 => Some(Self::EfiACPINVS),
            11 => Some(Self::EfiMemoryMap),
            12 => Some(Self::EfiPersistent),
            _ => None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct DeviceTreeBuf {
    pub data: Vec<u8>,
}

#[derive(Debug, Clone, Copy)]
#[repr(C, packed)]
struct BootArgsHeader {
    magic: u32,
    version: u32,
    flags: u64,
    memory_map_offset: u32,
    memory_map_size: u32,
    kernel_base: u64,
    kernel_size: u64,
    command_line_offset: u32,
    command_line_size: u32,
    device_tree_offset: u32,
    device_tree_size: u32,
}

const HEADER_SIZE: usize = std::mem::size_of::<BootArgsHeader>();

fn read_u32_le(data: &[u8], offset: usize) -> Result<u32> {
    if offset + 4 > data.len() {
        return Err(CoreError::Handoff("truncated read u32".into()));
    }
    Ok(u32::from_le_bytes([
        data[offset],
        data[offset + 1],
        data[offset + 2],
        data[offset + 3],
    ]))
}

fn read_u64_le(data: &[u8], offset: usize) -> Result<u64> {
    if offset + 8 > data.len() {
        return Err(CoreError::Handoff("truncated read u64".into()));
    }
    Ok(u64::from_le_bytes([
        data[offset],
        data[offset + 1],
        data[offset + 2],
        data[offset + 3],
        data[offset + 4],
        data[offset + 5],
        data[offset + 6],
        data[offset + 7],
    ]))
}

pub fn serialize_boot_args(args: &BootArgs) -> Result<Vec<u8>> {
    let memory_map_entries: Vec<u8> = args
        .memory_map
        .entries
        .iter()
        .flat_map(|e| {
            let mut buf = Vec::with_capacity(20);
            buf.extend_from_slice(&e.base.to_le_bytes());
            buf.extend_from_slice(&e.size.to_le_bytes());
            buf.extend_from_slice(&(e.kind as u32).to_le_bytes());
            buf
        })
        .collect();

    let cmd_bytes = args.command_line.as_bytes();
    let dt_bytes = args
        .device_tree
        .as_ref()
        .map(|dt| dt.data.as_slice())
        .unwrap_or(&[]);

    let memory_map_offset = HEADER_SIZE as u32;
    let memory_map_size = memory_map_entries.len() as u32;
    let command_line_offset = memory_map_offset + memory_map_size;
    let command_line_size = cmd_bytes.len() as u32;
    let device_tree_offset = command_line_offset + command_line_size;
    let device_tree_size = dt_bytes.len() as u32;

    let mut buf = Vec::with_capacity(HEADER_SIZE + memory_map_entries.len() + cmd_bytes.len() + dt_bytes.len());

    buf.extend_from_slice(&args.magic.to_le_bytes());
    buf.extend_from_slice(&args.version.to_le_bytes());
    buf.extend_from_slice(&args.flags.to_le_bytes());
    buf.extend_from_slice(&memory_map_offset.to_le_bytes());
    buf.extend_from_slice(&memory_map_size.to_le_bytes());
    buf.extend_from_slice(&args.kernel_base.to_le_bytes());
    buf.extend_from_slice(&args.kernel_size.to_le_bytes());
    buf.extend_from_slice(&command_line_offset.to_le_bytes());
    buf.extend_from_slice(&command_line_size.to_le_bytes());
    buf.extend_from_slice(&device_tree_offset.to_le_bytes());
    buf.extend_from_slice(&device_tree_size.to_le_bytes());

    buf.extend_from_slice(&memory_map_entries);
    buf.extend_from_slice(cmd_bytes);
    buf.extend_from_slice(dt_bytes);

    Ok(buf)
}

pub fn deserialize_boot_args(data: &[u8]) -> Result<BootArgs> {
    if data.len() < HEADER_SIZE {
        return Err(CoreError::Handoff(format!(
            "buffer too short: need {} bytes, have {}",
            HEADER_SIZE,
            data.len()
        )));
    }

    let magic = read_u32_le(data, 0)?;
    if magic != BOOT_ARGS_MAGIC {
        return Err(CoreError::InvalidMagic {
            expected: BOOT_ARGS_MAGIC,
            got: magic,
        });
    }

    let version = read_u32_le(data, 4)?;
    let flags = read_u64_le(data, 8)?;
    let memory_map_offset = read_u32_le(data, 16)? as usize;
    let memory_map_size = read_u32_le(data, 20)? as usize;
    let kernel_base = read_u64_le(data, 24)?;
    let kernel_size = read_u64_le(data, 32)?;
    let command_line_offset = read_u32_le(data, 40)? as usize;
    let command_line_size = read_u32_le(data, 44)? as usize;
    let device_tree_offset = read_u32_le(data, 48)? as usize;
    let device_tree_size = read_u32_le(data, 52)? as usize;

    let mut entries = Vec::new();
    let entry_size = 20;
    let entry_count = memory_map_size / entry_size;
    for i in 0..entry_count {
        let base_off = memory_map_offset + i * entry_size;
        if base_off + entry_size > data.len() {
            break;
        }
        let base = read_u64_le(data, base_off)?;
        let size = read_u64_le(data, base_off + 8)?;
        let kind_raw = read_u32_le(data, base_off + 16)?;
        let kind = MemoryKind::from_u32(kind_raw).ok_or_else(|| {
            CoreError::Handoff(format!("unknown memory kind: {kind_raw}"))
        })?;
        entries.push(MemoryEntry { base, size, kind });
    }

    let total_size: u64 = entries.iter().map(|e| e.size).sum();

    let command_line_end = command_line_offset + command_line_size;
    if command_line_end > data.len() {
        return Err(CoreError::Handoff("command line extends beyond data".into()));
    }
    let command_line = String::from_utf8_lossy(&data[command_line_offset..command_line_end]).into_owned();

    let device_tree = if device_tree_size > 0 {
        let dt_end = device_tree_offset + device_tree_size;
        if dt_end > data.len() {
            return Err(CoreError::Handoff("device tree extends beyond data".into()));
        }
        Some(DeviceTreeBuf {
            data: data[device_tree_offset..dt_end].to_vec(),
        })
    } else {
        None
    };

    Ok(BootArgs {
        magic,
        version,
        flags,
        memory_map: MemoryMap { entries, total_size },
        kernel_base,
        kernel_size,
        command_line,
        device_tree,
    })
}
