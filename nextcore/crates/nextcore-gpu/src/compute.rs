use std::collections::{HashMap, HashSet};
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
    #[error("no compute execution backend configured")]
    BackendUnavailable,
    #[error("compute fence must exist and be unsignaled")]
    InvalidFence,
    #[error("unsupported or invalid compute input: {0}")]
    Unsupported(String),
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
    #[cfg(feature = "vulkan")]
    vulkan: Option<crate::vulkan_compute::VulkanComputeBackend>,
}

impl ComputePipelineManager {
    pub fn new() -> Self {
        Self {
            next_id: 1,
            pipelines: HashMap::new(),
            storage_buffers: HashMap::new(),
            next_buffer_handle: 1,
            #[cfg(feature = "vulkan")]
            vulkan: None,
        }
    }

    /// Explicit host Vulkan execution. This does not attach a Metal/guest device.
    #[cfg(feature = "vulkan")]
    pub fn with_vulkan(config: crate::vulkan_compute::VulkanComputeConfig) -> Result<Self, ComputeError> {
        let mut manager = Self::new();
        manager.vulkan = Some(crate::vulkan_compute::VulkanComputeBackend::new(config)?);
        Ok(manager)
    }

    #[cfg(feature = "vulkan")]
    pub fn vulkan_device_info(&self) -> Option<&crate::vulkan_compute::VulkanDeviceInfo> {
        self.vulkan.as_ref().map(|backend| backend.device_info())
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
        let end = offset.checked_add(data.len()).ok_or_else(|| ComputeError::Unsupported("buffer range overflow".into()))?;
        if end > buf.data.len() {
            return Err(ComputeError::StorageBufferTooSmall {
                needed: end,
                available: buf.data.len(),
            });
        }
        buf.data[offset..end].copy_from_slice(data);
        Ok(())
    }

    pub fn read_storage_buffer(&self, handle: u64, offset: usize, len: usize) -> Result<Vec<u8>, ComputeError> {
        let buf = self.storage_buffers.get(&handle).ok_or_else(|| {
            ComputeError::Generic(format!("buffer {} not found", handle))
        })?;
        let end = offset.checked_add(len).ok_or_else(|| ComputeError::Unsupported("buffer range overflow".into()))?;
        if end > buf.data.len() {
            return Err(ComputeError::StorageBufferTooSmall {
                needed: end,
                available: buf.data.len(),
            });
        }
        Ok(buf.data[offset..end].to_vec())
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

        if sync.get_fence(fence_id).is_none_or(|fence| fence.is_signaled()) {
            return Err(ComputeError::InvalidFence);
        }
        let dimensions = [workgroups.x, workgroups.y, workgroups.z];
        validate_dispatch(&pipeline.descriptor, dimensions)?;
        for binding in &pipeline.descriptor.buffer_bindings {
            let buf = self.storage_buffers.get(&binding.buffer_id).ok_or(ComputeError::BufferNotBound(binding.binding))?;
            let end = binding.offset.checked_add(binding.size).ok_or_else(|| ComputeError::Unsupported("binding range overflow".into()))?;
            if end > buf.data.len() as u64 {
                return Err(ComputeError::StorageBufferTooSmall { needed: usize::try_from(end).unwrap_or(usize::MAX), available: buf.data.len() });
            }
        }
        #[cfg(feature = "vulkan")]
        {
            let backend = self.vulkan.as_mut().ok_or(ComputeError::BackendUnavailable)?;
            let descriptor = &pipeline.descriptor;
            let views: Vec<_> = descriptor.buffer_bindings.iter().map(|binding| {
                let start = binding.offset as usize;
                let end = start + binding.size as usize;
                (binding.binding, self.storage_buffers[&binding.buffer_id].data[start..end].to_vec())
            }).collect();
            let updated = backend.dispatch(descriptor, dimensions, &views)?;
            if updated.len() != views.len() || updated.iter().zip(&views).any(|(data, (_, previous))| data.len() != previous.len()) {
                return Err(ComputeError::Generic("backend readback sizes disagree".into()));
            }
            // Commit only after every GPU buffer has completed and been read back.
            for (binding, data) in descriptor.buffer_bindings.iter().zip(updated) {
                let start = binding.offset as usize;
                self.storage_buffers.get_mut(&binding.buffer_id).unwrap().data[start..start + data.len()].copy_from_slice(&data);
            }
            sync.signal_fence(fence_id, 1);
            Ok(())
        }
        #[cfg(not(feature = "vulkan"))]
        Err(ComputeError::BackendUnavailable)
    }

    pub fn storage_buffer_count(&self) -> usize {
        self.storage_buffers.len()
    }
}

pub(crate) fn validate_dispatch(descriptor: &ComputePipelineDescriptor, groups: [u32; 3]) -> Result<(), ComputeError> {
    let product = groups.into_iter().chain(descriptor.workgroup_size).try_fold(1u64, |total, dimension| {
        if dimension == 0 { None } else { total.checked_mul(dimension as u64) }
    });
    if product.is_none_or(|total| total > 16 * 1024 * 1024) {
        return Err(ComputeError::InvalidDispatch(groups));
    }
    if descriptor.buffer_bindings.is_empty() || descriptor.buffer_bindings.len() > 8 {
        return Err(ComputeError::Unsupported("require 1..8 storage bindings".into()));
    }
    let (mut bindings, mut buffers, mut total_bytes) = (HashSet::new(), HashSet::new(), 0u64);
    for binding in &descriptor.buffer_bindings {
        if binding.binding >= 32 || !bindings.insert(binding.binding) || !buffers.insert(binding.buffer_id)
            || binding.size == 0 || binding.size > 16 * 1024 * 1024 || binding.offset % 4 != 0 || binding.size % 4 != 0 {
            return Err(ComputeError::Unsupported("invalid/duplicate/aliased storage binding".into()));
        }
        total_bytes += binding.size;
    }
    if total_bytes > 64 * 1024 * 1024 {
        return Err(ComputeError::Unsupported("storage byte cap exceeded".into()));
    }
    Ok(())
}
