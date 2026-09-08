use nextcore_gpu::compute::{ComputePipelineDescriptor, ComputePipelineManager, ComputeShader, DispatchWorkgroup, BufferBinding};
use nextcore_gpu::sync::GpuSyncManager;

#[test]
fn test_create_pipeline() {
    let mut mgr = ComputePipelineManager::new();
    let id = mgr.create_pipeline(ComputePipelineDescriptor {
        shader: ComputeShader { id: 1, entry_point: "main".into(), bytecode: vec![0x01] },
        workgroup_size: [8, 8, 1],
        buffer_bindings: vec![],
    });
    assert_eq!(id, 1);
    assert!(mgr.get_pipeline(id).is_some());
    assert!(mgr.get_pipeline(99).is_none());
}

#[test]
fn test_delete_pipeline() {
    let mut mgr = ComputePipelineManager::new();
    let id = mgr.create_pipeline(ComputePipelineDescriptor {
        shader: ComputeShader { id: 1, entry_point: "main".into(), bytecode: vec![] },
        workgroup_size: [1, 1, 1],
        buffer_bindings: vec![],
    });
    assert!(mgr.delete_pipeline(id));
    assert!(!mgr.delete_pipeline(id));
}

#[test]
fn test_storage_buffer_ops() {
    let mut mgr = ComputePipelineManager::new();
    let handle = mgr.create_storage_buffer(64);
    mgr.write_storage_buffer(handle, 0, &[0xABu8; 16]).unwrap();

    let out = mgr.read_storage_buffer(handle, 0, 16).unwrap();
    assert_eq!(out, vec![0xABu8; 16]);
    assert_eq!(mgr.storage_buffer_count(), 1);
}

#[test]
fn test_storage_buffer_oob_write() {
    let mut mgr = ComputePipelineManager::new();
    let handle = mgr.create_storage_buffer(4);
    assert!(mgr.write_storage_buffer(handle, 4, &[0u8; 4]).is_err());
}

#[test]
fn test_storage_buffer_oob_read() {
    let mut mgr = ComputePipelineManager::new();
    let handle = mgr.create_storage_buffer(4);
    assert!(mgr.read_storage_buffer(handle, 4, 4).is_err());
}

#[test]
fn test_dispatch_success() {
    let mut mgr = ComputePipelineManager::new();
    let mut sync = GpuSyncManager::new();
    let fence = sync.create_fence();

    let buf_handle = mgr.create_storage_buffer(1024);
    let pid = mgr.create_pipeline(ComputePipelineDescriptor {
        shader: ComputeShader { id: 1, entry_point: "main".into(), bytecode: vec![] },
        workgroup_size: [4, 4, 1],
        buffer_bindings: vec![BufferBinding {
            binding: 0,
            buffer_id: buf_handle,
            offset: 0,
            size: 1024,
        }],
    });

    let result = mgr.dispatch(pid, DispatchWorkgroup { x: 2, y: 2, z: 1 }, &sync, fence);
    assert!(result.is_ok());
    assert!(sync.get_fence(fence).unwrap().is_signaled());
}

#[test]
fn test_dispatch_invalid_dims() {
    let mut mgr = ComputePipelineManager::new();
    let mut sync = GpuSyncManager::new();
    let fence = sync.create_fence();

    let pid = mgr.create_pipeline(ComputePipelineDescriptor {
        shader: ComputeShader { id: 1, entry_point: "main".into(), bytecode: vec![] },
        workgroup_size: [4, 4, 1],
        buffer_bindings: vec![],
    });

    assert!(mgr.dispatch(pid, DispatchWorkgroup { x: 0, y: 1, z: 1 }, &sync, fence).is_err());
}

#[test]
fn test_dispatch_missing_pipeline() {
    let mut mgr = ComputePipelineManager::new();
    let mut sync = GpuSyncManager::new();
    let fence = sync.create_fence();
    assert!(mgr.dispatch(999, DispatchWorkgroup { x: 1, y: 1, z: 1 }, &sync, fence).is_err());
}

#[test]
fn test_dispatch_missing_buffer() {
    let mut mgr = ComputePipelineManager::new();
    let mut sync = GpuSyncManager::new();
    let fence = sync.create_fence();

    let pid = mgr.create_pipeline(ComputePipelineDescriptor {
        shader: ComputeShader { id: 1, entry_point: "main".into(), bytecode: vec![] },
        workgroup_size: [4, 4, 1],
        buffer_bindings: vec![BufferBinding {
            binding: 0,
            buffer_id: 999,
            offset: 0,
            size: 16,
        }],
    });

    assert!(mgr.dispatch(pid, DispatchWorkgroup { x: 1, y: 1, z: 1 }, &sync, fence).is_err());
}
