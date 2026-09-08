use std::collections::HashMap;
use thiserror::Error;

use crate::sync::{GpuSyncManager, FenceId};

#[derive(Debug, Error)]
pub enum ComputeError {
    #[error("pipeline not found: {0}")]
    PipelineNotFound(u32),
    #[error("buffer not bound at slot {0}")]
    BufferNotBound(u32),
    #[error("dispatch dimensions invalid: {0:?}")]
    InvalidDispatch([u32; 3]),
    #[error("storage buffer too small: need {needed}, got {available}")]
    StorageBufferTooSmall { needed: usize, available: usize },
    #[error("compute error: {0}")]
    Generic(String),
}

#[derive(Debug, Clone)]
pub struct ComputeShader {
    pub id: u32,
    pub entry_point: String,
    pub bytecode: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct BufferBinding {
    pub binding: u32,
    pub buffer_id: u64,
    pub offset: u64,
    pub size: u64,
}

#[derive(Debug, Clone)]
pub struct ComputePipelineDescriptor {
    pub shader: ComputeShader,
    pub workgroup_size: [u32; 3],
    pub buffer_bindings: Vec<BufferBinding>,
}

#[derive(Debug, Clone)]
pub struct ComputePipeline {
    pub id: u32,
    pub descriptor: ComputePipelineDescriptor,
}

#[derive(Debug, Clone)]
pub struct StorageBuffer {
    pub handle: u64,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct DispatchWorkgroup {
    pub x: u32,
    pub y: u32,
    pub z: u32,
}

impl Default for ComputePipelineManager {
    fn default() -> Self {
        Self::new()
    }
}

pub struct ComputePipelineManager {
    next_id: u32,
    pipelines: HashMap<u32, ComputePipeline>,
    storage_buffers: HashMap<u64, StorageBuffer>,
    next_buffer_handle: u64,
}

impl ComputePipelineManager {
    pub fn new() -> Self {
        Self {
            next_id: 1,
            pipelines: HashMap::new(),
            storage_buffers: HashMap::new(),
            next_buffer_handle: 1,
        }
    }

    pub fn create_pipeline(&mut self, desc: ComputePipelineDescriptor) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        self.pipelines.insert(id, ComputePipeline { id, descriptor: desc });
        id
    }

    pub fn get_pipeline(&self, id: u32) -> Option<&ComputePipeline> {
        self.pipelines.get(&id)
    }

    pub fn delete_pipeline(&mut self, id: u32) -> bool {
        self.pipelines.remove(&id).is_some()
    }

    pub fn create_storage_buffer(&mut self, size: usize) -> u64 {
        let handle = self.next_buffer_handle;
        self.next_buffer_handle += 1;
        self.storage_buffers
            .insert(handle, StorageBuffer { handle, data: vec![0u8; size] });
        handle
    }

    pub fn write_storage_buffer(&mut self, handle: u64, offset: usize, data: &[u8]) -> Result<(), ComputeError> {
        let buf = self.storage_buffers.get_mut(&handle).ok_or(ComputeError::BufferNotBound(0))?;
        if offset + data.len() > buf.data.len() {
            return Err(ComputeError::StorageBufferTooSmall {
                needed: offset + data.len(),
                available: buf.data.len(),
            });
        }
        buf.data[offset..offset + data.len()].copy_from_slice(data);
        Ok(())
    }

    pub fn read_storage_buffer(&self, handle: u64, offset: usize, len: usize) -> Result<Vec<u8>, ComputeError> {
        let buf = self.storage_buffers.get(&handle).ok_or_else(|| {
            ComputeError::Generic(format!("buffer {} not found", handle))
        })?;
        if offset + len > buf.data.len() {
            return Err(ComputeError::StorageBufferTooSmall {
                needed: offset + len,
                available: buf.data.len(),
            });
        }
        Ok(buf.data[offset..offset + len].to_vec())
    }

    pub fn dispatch(
        &mut self,
        pipeline_id: u32,
        workgroups: DispatchWorkgroup,
        sync: &GpuSyncManager,
        fence_id: FenceId,
    ) -> Result<(), ComputeError> {
        let pipeline = self.pipelines.get(&pipeline_id)
            .ok_or(ComputeError::PipelineNotFound(pipeline_id))?;

        if workgroups.x == 0 || workgroups.y == 0 || workgroups.z == 0 {
            return Err(ComputeError::InvalidDispatch([workgroups.x, workgroups.y, workgroups.z]));
        }

        let ws = &pipeline.descriptor.workgroup_size;
        let total_threads = workgroups.x as u64 * workgroups.y as u64 * workgroups.z as u64
            * ws[0] as u64 * ws[1] as u64 * ws[2] as u64;

        log::debug!(
            "compute dispatch pipeline {} workgroups({},{},{}) threads({},{},{}) total={}",
            pipeline_id,
            workgroups.x, workgroups.y, workgroups.z,
            ws[0], ws[1], ws[2],
            total_threads
        );

        for binding in &pipeline.descriptor.buffer_bindings {
            let buf = self.storage_buffers.get(&binding.buffer_id).ok_or(ComputeError::BufferNotBound(binding.binding))?;
            log::debug!("  binding {}: buffer {} ({} bytes)", binding.binding, binding.buffer_id, buf.data.len());
        }

        sync.signal_fence(fence_id, 1);
        Ok(())
    }

    pub fn storage_buffer_count(&self) -> usize {
        self.storage_buffers.len()
    }
}
