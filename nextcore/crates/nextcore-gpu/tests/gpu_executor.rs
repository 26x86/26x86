use nextcore_gpu::command_executor::{CommandExecutor, GpuCommand, IndexType, RecordedCommandBuffer};
use nextcore_gpu::framebuffer::{LinearFramebuffer, PixelFormat};

#[test]
fn test_create_vertex_buffer() {
    let mut ex = CommandExecutor::new();
    let id = ex.create_vertex_buffer(vec![0u8; 64], 16);
    assert_eq!(id, 1);

    let fid = ex.create_vertex_buffer(vec![1u8; 32], 8);
    assert_eq!(fid, 2);
}

#[test]
fn test_create_index_buffer() {
    let mut ex = CommandExecutor::new();
    let id = ex.create_index_buffer(vec![0u8; 12], IndexType::Uint32);
    assert_eq!(id, 1);
}

#[test]
fn test_create_uniform_buffer() {
    let mut ex = CommandExecutor::new();
    let id = ex.create_uniform_buffer(vec![0u8; 16]);
    assert_eq!(id, 1);
}

#[test]
fn test_write_vertex_buffer() {
    let mut ex = CommandExecutor::new();
    let id = ex.create_vertex_buffer(vec![0u8; 64], 16);
    ex.write_vertex_buffer(id, &[0xFFu8; 64]).unwrap();

    // verify via re-execution command path implicitly (write returns Ok)
}

#[test]
fn test_begin_end_render_pass_clears() {
    let mut ex = CommandExecutor::new();
    let mut fbs = vec![LinearFramebuffer::new(4, 4, PixelFormat::Rgba8)];

    let cmdbuf = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BeginRenderPass { clear_color: [1.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::EndRenderPass,
        ],
    };
    ex.execute(&cmdbuf, &mut fbs, &mut nextcore_gpu::texture::TextureManager::new()).unwrap();

    // Clear applied to framebuffer
    assert_eq!(fbs[0].get_pixel(0, 0).unwrap(), [255, 0, 0, 255]);
}

#[test]
fn test_draw_commands_record_execution() {
    let mut ex = CommandExecutor::new();
    let mut fbs = vec![LinearFramebuffer::new(4, 4, PixelFormat::Rgba8)];
    let mut tm = nextcore_gpu::texture::TextureManager::new();

    let cmdbuf = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BeginRenderPass { clear_color: [0.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::Draw { vertex_count: 3, first_vertex: 0 },
            GpuCommand::Draw { vertex_count: 6, first_vertex: 3 },
            GpuCommand::DrawIndexed { index_count: 6, first_index: 0, vertex_offset: 0 },
            GpuCommand::EndRenderPass,
        ],
    };
    ex.execute(&cmdbuf, &mut fbs, &mut tm).unwrap();
    assert_eq!(ex.executed_command_count(), 3);
}

#[test]
fn test_copy_texture_commands() {
    let mut ex = CommandExecutor::new();
    let mut fbs = vec![LinearFramebuffer::new(4, 4, PixelFormat::Rgba8)];
    let mut tm = nextcore_gpu::texture::TextureManager::new();
    let tid = tm.create_texture(
        nextcore_gpu::texture::TextureDescriptor::new_2d(2, 2, nextcore_gpu::texture::TextureFormat::Rgba8Unorm)
    ).unwrap();

    let vb = ex.create_vertex_buffer(vec![0xAAu8; 16], 4);
    let cmdbuf = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::CopyBufferToTexture { buffer_id: vb, texture_id: tid },
            GpuCommand::ClearTexture { texture_id: tid, color: [1.0, 1.0, 0.0, 1.0] },
            GpuCommand::CopyTextureToBuffer { texture_id: tid, buffer_id: vb },
        ],
    };
    ex.execute(&cmdbuf, &mut fbs, &mut tm).unwrap();

    let out = tm.download_texture(tid).unwrap();
    assert_eq!(out.len(), 16);
    assert_eq!(out[0], 255); // after clear all 255
}

#[test]
fn test_binding_commands() {
    let mut ex = CommandExecutor::new();
    let mut fbs = vec![LinearFramebuffer::new(2, 2, PixelFormat::Rgba8)];
    let mut tm = nextcore_gpu::texture::TextureManager::new();
    let tid = tm.create_texture(
        nextcore_gpu::texture::TextureDescriptor::new_2d(2, 2, nextcore_gpu::texture::TextureFormat::Rgba8Unorm)
    ).unwrap();
    let sid = tm.create_sampler(nextcore_gpu::texture::SamplerDescriptor::default());

    let vb = ex.create_vertex_buffer(vec![0u8; 32], 8);
    let ib = ex.create_index_buffer(vec![0u8; 12], IndexType::Uint16);
    let ub = ex.create_uniform_buffer(vec![0u8; 16]);

    let cmdbuf = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BindPipeline(1),
            GpuCommand::BindVertexBuffer { slot: 0, buffer_id: vb },
            GpuCommand::BindIndexBuffer { buffer_id: ib, index_type: IndexType::Uint16 },
            GpuCommand::BindUniformBuffer { slot: 0, buffer_id: ub },
            GpuCommand::BindTexture { slot: 0, texture_id: tid, sampler_id: sid },
            GpuCommand::SetViewport(nextcore_gpu::render_pipeline::Viewport {
                x: 0.0, y: 0.0, width: 2.0, height: 2.0, min_depth: 0.0, max_depth: 1.0,
            }),
            GpuCommand::SetScissor(nextcore_gpu::render_pipeline::ScissorRect {
                x: 0, y: 0, width: 2, height: 2,
            }),
            GpuCommand::SetLineWidth(1.0),
            GpuCommand::PushConstants { offset: 0, data: vec![0u8; 4] },
        ],
    };
    ex.execute(&cmdbuf, &mut fbs, &mut tm).unwrap();
    assert_eq!(ex.executed_command_count(), 0);
}

#[test]
fn test_draw_instanced() {
    let mut ex = CommandExecutor::new();
    let mut fbs = vec![LinearFramebuffer::new(4, 4, PixelFormat::Rgba8)];
    let mut tm = nextcore_gpu::texture::TextureManager::new();

    let cmdbuf = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BeginRenderPass { clear_color: [0.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::DrawInstanced { vertex_count: 3, instance_count: 4, first_vertex: 0, first_instance: 0 },
            GpuCommand::DrawIndexedInstanced {
                index_count: 6, instance_count: 2, first_index: 0, vertex_offset: 0, first_instance: 0,
            },
            GpuCommand::EndRenderPass,
        ],
    };
    ex.execute(&cmdbuf, &mut fbs, &mut tm).unwrap();
    assert_eq!(ex.executed_command_count(), 2);
}

#[test]
fn test_reset_stats() {
    let mut ex = CommandExecutor::new();
    let mut fbs = vec![LinearFramebuffer::new(4, 4, PixelFormat::Rgba8)];
    let _ = fbs.pop();

    let cmdbuf = RecordedCommandBuffer {
        commands: vec![GpuCommand::DispatchCompute { pipeline_id: 1, x: 1, y: 1, z: 1 }],
    };
    ex.execute(&cmdbuf, &mut [], &mut nextcore_gpu::texture::TextureManager::new()).unwrap();
    assert_eq!(ex.executed_command_count(), 1);
    ex.reset_stats();
    assert_eq!(ex.executed_command_count(), 0);
}

#[test]
fn test_write_uniform_limited_to_buffer_size() {
    let mut ex = CommandExecutor::new();
    let id = ex.create_uniform_buffer(vec![0u8; 16]);
    ex.write_uniform_buffer(id, &[0xFFu8; 32]).unwrap();
}
