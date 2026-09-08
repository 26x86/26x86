use std::collections::HashMap;
use thiserror::Error;

use crate::canonical_spec::{GpuCapabilities, GpuVendor};

#[derive(Debug, Error)]
pub enum GpuError {
    #[error("unsupported command")]
    UnsupportedCommand,
    #[error("buffer not found: {0}")]
    BufferNotFound(u64),
    #[error("out of memory")]
    OutOfMemory,
    #[error("invalid handle: {0}")]
    InvalidHandle(u64),
    #[error("driver error: {0}")]
    DriverError(String),
}

#[derive(Debug, Clone)]
pub struct GpuBuffer {
    pub handle: u64,
    pub size: u64,
    pub host_ptr: Vec<u8>,
}

#[derive(Debug, Clone)]
pub enum GpuCommand {
    CopyBuffer { src: u64, dst: u64, size: u64 },
    ComputeKernel { kernel_id: u32, grid: (u32, u32, u32), block: (u32, u32, u32) },
    RenderClear { color: [f32; 4] },
    PresentSwapchain { buffer: u64 },
}

#[derive(Debug, Clone)]
pub struct CommandBuffer {
    pub cmds: Vec<GpuCommand>,
}

#[derive(Debug, Clone)]
pub enum AccelerationMode {
    Software,
    HardwareWrapped,
    Full,
}

#[derive(Debug, Clone)]
pub struct GpuMemoryManager {
    next_handle: u64,
    buffers: HashMap<u64, Vec<u8>>,
}

impl Default for GpuMemoryManager {
    fn default() -> Self {
        Self::new()
    }
}

impl GpuMemoryManager {
    pub fn new() -> Self {
        Self {
            next_handle: 1,
            buffers: HashMap::new(),
        }
    }

    pub fn allocate(&mut self, size: u64) -> GpuBuffer {
        let handle = self.next_handle;
        self.next_handle += 1;
        let host_ptr = vec![0u8; size as usize];
        self.buffers.insert(handle, host_ptr.clone());
        GpuBuffer { handle, size, host_ptr }
    }

    pub fn read(&self, handle: u64, offset: u64, len: u64) -> Result<Vec<u8>, GpuError> {
        let buf = self.buffers.get(&handle).ok_or(GpuError::BufferNotFound(handle))?;
        let start = usize::try_from(offset).map_err(|_| GpuError::InvalidHandle(handle))?;
        let len = usize::try_from(len).map_err(|_| GpuError::InvalidHandle(handle))?;
        let end = start.checked_add(len).ok_or(GpuError::InvalidHandle(handle))?;
        if end > buf.len() {
            return Err(GpuError::InvalidHandle(handle));
        }
        Ok(buf[start..end].to_vec())
    }

    pub fn write(&mut self, handle: u64, offset: u64, data: &[u8]) -> Result<(), GpuError> {
        let buf = self.buffers.get_mut(&handle).ok_or(GpuError::BufferNotFound(handle))?;
        let start = usize::try_from(offset).map_err(|_| GpuError::InvalidHandle(handle))?;
        let end = start.checked_add(data.len()).ok_or(GpuError::InvalidHandle(handle))?;
        if end > buf.len() {
            return Err(GpuError::InvalidHandle(handle));
        }
        buf[start..end].copy_from_slice(data);
        Ok(())
    }

    pub fn free(&mut self, handle: u64) -> Result<(), GpuError> {
        self.buffers.remove(&handle).ok_or(GpuError::BufferNotFound(handle))?;
        Ok(())
    }

    fn get_buf(&self, handle: u64) -> Result<&Vec<u8>, GpuError> {
        self.buffers.get(&handle).ok_or(GpuError::BufferNotFound(handle))
    }
}

#[derive(Debug, Clone)]
pub struct VirtualMetalDevice {
    pub spec: GpuCapabilities,
    pub name: String,
    pub memory: GpuMemoryManager,
    pub acceleration_mode: AccelerationMode,
}

impl VirtualMetalDevice {
    pub fn new(spec: GpuCapabilities) -> Self {
        let vendor_str = match spec.vendor {
            GpuVendor::AMD => "AMD",
            GpuVendor::NVIDIA => "NVIDIA",
            GpuVendor::Intel => "Intel",
            GpuVendor::Unknown => "Generic",
        };
        let name = format!("Apple {} GPU", vendor_str);
        // This model owns host Vec buffers, not an executing device backend.
        // Capability metadata cannot promote it to hardware acceleration.
        let acceleration_mode = AccelerationMode::Software;
        Self {
            spec,
            name,
            memory: GpuMemoryManager::new(),
            acceleration_mode,
        }
    }

    pub fn supports_metal(&self) -> bool {
        // PCI capability metadata cannot establish an executing Metal backend.
        false
    }

    pub fn device_name(&self) -> &str {
        &self.name
    }

    pub fn vram_size(&self) -> u64 {
        self.spec.vram_size
    }

    pub fn is_software_accelerated(&self) -> bool {
        matches!(self.acceleration_mode, AccelerationMode::Software)
    }

    pub fn allocate_buffer(&mut self, size: u64) -> GpuBuffer {
        self.memory.allocate(size)
    }

    pub fn write_command_buffer(&mut self, cmdbuf: CommandBuffer) -> Result<(), GpuError> {
        // Validate the entire list before any software copy. This model has no
        // registered shader, render target, or presentation backend.
        for cmd in &cmdbuf.cmds {
            match *cmd {
                GpuCommand::CopyBuffer { src, dst, size } => {
                    if size > self.memory.get_buf(src)?.len() as u64
                        || size > self.memory.get_buf(dst)?.len() as u64
                    {
                        return Err(GpuError::InvalidHandle(dst));
                    }
                }
                _ => return Err(GpuError::UnsupportedCommand),
            }
        }
        for cmd in cmdbuf.cmds {
            match cmd {
                GpuCommand::CopyBuffer { src, dst, size } => {
                    let data = self.memory.read(src, 0, size)?;
                    self.memory.write(dst, 0, &data)?;
                }
                _ => unreachable!("all commands were validated before execution"),
            }
        }
        Ok(())
    }

    pub fn flush(&mut self) -> Result<(), GpuError> {
        log::debug!("flushing command queue");
        Ok(())
    }
}
