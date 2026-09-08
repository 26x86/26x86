use nextcore_gpu::command_executor::{
    CommandExecutor, GpuCommand, IndexType, RecordedCommandBuffer,
    SOFTWARE_RENDER_VERTEX_STRIDE,
};
use nextcore_gpu::framebuffer::{DoubleBuffer, LinearFramebuffer, PixelFormat};
use nextcore_gpu::rasterizer::SoftwareRasterizer;
use nextcore_gpu::texture::TextureManager;

fn encode_vertex(position: [f32; 4], color: [f32; 4]) -> Vec<u8> {
    let mut out = Vec::with_capacity(SOFTWARE_RENDER_VERTEX_STRIDE as usize);
    for v in position.iter().chain(color.iter()) {
        out.extend_from_slice(&v.to_le_bytes());
    }
    // tex_coord (u,v)
    out.extend_from_slice(&0.0f32.to_le_bytes());
    out.extend_from_slice(&0.0f32.to_le_bytes());
    // normal (nx,ny,nz)
    out.extend_from_slice(&0.0f32.to_le_bytes());
    out.extend_from_slice(&0.0f32.to_le_bytes());
    out.extend_from_slice(&1.0f32.to_le_bytes());
    out
}

fn red_triangle() -> Vec<u8> {
    let mut data = Vec::new();
    data.extend(encode_vertex([-1.0, -1.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]));
    data.extend(encode_vertex([1.0, -1.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]));
    data.extend(encode_vertex([0.0, 1.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]));
    data
}

fn render_single_draw() -> (CommandExecutor, LinearFramebuffer, TextureManager, SoftwareRasterizer) {
    let mut executor = CommandExecutor::new();
    let vb = executor.create_vertex_buffer(red_triangle(), SOFTWARE_RENDER_VERTEX_STRIDE);

    let commands = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BindPipeline(1),
            GpuCommand::BindVertexBuffer { slot: 0, buffer_id: vb },
            GpuCommand::BeginRenderPass { clear_color: [0.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::Draw { vertex_count: 3, first_vertex: 0 },
            GpuCommand::EndRenderPass,
        ],
    };

    let fb = LinearFramebuffer::new(16, 16, PixelFormat::Rgba8);
    let mut buffers = vec![fb];
    let mut textures = TextureManager::default();
    let mut rasterizer = SoftwareRasterizer::default();
    executor
        .execute_with_rasterizer(&commands, &mut buffers, &mut textures, &mut rasterizer)
        .unwrap();
    (executor, buffers.pop().unwrap(), textures, rasterizer)
}

#[test]
fn render_path_clears_and_rasterizes_triangle() {
    let (_exec, fb, _tex, _ras) = render_single_draw();

    assert_eq!(fb.get_pixel(8, 10).unwrap(), [255, 0, 0, 255]);
    assert_eq!(fb.get_pixel(8, 15).unwrap(), [255, 0, 0, 255]);
    assert_eq!(fb.get_pixel(1, 1).unwrap(), [0, 0, 0, 255]);
    assert_eq!(fb.get_pixel(4, 4).unwrap(), [0, 0, 0, 255]);
    assert!(fb.is_dirty());
}

#[test]
fn render_path_records_draw_call_count() {
    let (executor, _fb, _tex, _ras) = render_single_draw();
    assert_eq!(executor.executed_command_count(), 1);
}

#[test]
fn render_without_rasterizer_only_clears() {
    let mut executor = CommandExecutor::new();
    let vb = executor.create_vertex_buffer(red_triangle(), SOFTWARE_RENDER_VERTEX_STRIDE);

    let commands = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BindVertexBuffer { slot: 0, buffer_id: vb },
            GpuCommand::BeginRenderPass { clear_color: [0.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::Draw { vertex_count: 3, first_vertex: 0 },
            GpuCommand::EndRenderPass,
        ],
    };

    let mut fb = LinearFramebuffer::new(16, 16, PixelFormat::Rgba8);
    let mut textures = TextureManager::default();
    executor.execute(&commands, std::slice::from_mut(&mut fb), &mut textures).unwrap();

    assert_eq!(fb.get_pixel(8, 10).unwrap(), [0, 0, 0, 255]);
    assert_eq!(executor.executed_command_count(), 1);
}

#[test]
fn render_indexed_draw_rasterizes_triangle() {
    let mut executor = CommandExecutor::new();
    let vb = executor.create_vertex_buffer(red_triangle(), SOFTWARE_RENDER_VERTEX_STRIDE);
    let ib = executor.create_index_buffer(vec![0u16, 1, 2].into_iter().flat_map(|i| i.to_le_bytes()).collect(), IndexType::Uint16);

    let commands = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BindPipeline(1),
            GpuCommand::BindVertexBuffer { slot: 0, buffer_id: vb },
            GpuCommand::BindIndexBuffer { buffer_id: ib, index_type: IndexType::Uint16 },
            GpuCommand::BeginRenderPass { clear_color: [0.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::DrawIndexed { index_count: 3, first_index: 0, vertex_offset: 0 },
            GpuCommand::EndRenderPass,
        ],
    };

    let mut fb = LinearFramebuffer::new(16, 16, PixelFormat::Rgba8);
    let mut textures = TextureManager::default();
    let mut rasterizer = SoftwareRasterizer::default();
    executor
        .execute_with_rasterizer(&commands, std::slice::from_mut(&mut fb), &mut textures, &mut rasterizer)
        .unwrap();

    assert_eq!(fb.get_pixel(8, 10).unwrap(), [255, 0, 0, 255]);
    assert_eq!(fb.get_pixel(1, 1).unwrap(), [0, 0, 0, 255]);
}

#[test]
fn render_path_double_buffer_presents() {
    let mut executor = CommandExecutor::new();
    let vb = executor.create_vertex_buffer(red_triangle(), SOFTWARE_RENDER_VERTEX_STRIDE);

    let commands = RecordedCommandBuffer {
        commands: vec![
            GpuCommand::BindVertexBuffer { slot: 0, buffer_id: vb },
            GpuCommand::BeginRenderPass { clear_color: [0.0, 0.0, 0.0, 1.0], clear_depth: 1.0 },
            GpuCommand::Draw { vertex_count: 3, first_vertex: 0 },
            GpuCommand::EndRenderPass,
        ],
    };

    let mut db = DoubleBuffer::new(16, 16, PixelFormat::Rgba8);
    let mut textures = TextureManager::default();
    let mut rasterizer = SoftwareRasterizer::default();

    {
        let back = std::slice::from_mut(db.back_mut());
        executor
            .execute_with_rasterizer(&commands, back, &mut textures, &mut rasterizer)
            .unwrap();
    }

    // swap 전에는 back에만 삼각형이 있고 front는 새 버퍼(투명)
    assert_eq!(db.front().get_pixel(8, 10).unwrap(), [0, 0, 0, 0]);
    assert_eq!(db.back().get_pixel(8, 10).unwrap(), [255, 0, 0, 255]);

    db.swap();

    // swap 후에는 front(표시면)에 삼각형
    assert_eq!(db.front().get_pixel(8, 10).unwrap(), [255, 0, 0, 255]);
    assert_eq!(db.front().get_pixel(1, 1).unwrap(), [0, 0, 0, 255]);
}

#[test]
fn software_vertex_roundtrip_via_decode() {
    let data = encode_vertex([0.5, -0.25, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]);
    assert_eq!(data.len(), SOFTWARE_RENDER_VERTEX_STRIDE as usize);

    let v = nextcore_gpu::command_executor::decode_software_vertex(&data, 0).unwrap();
    assert_eq!(v.position.x, 0.5);
    assert_eq!(v.position.y, -0.25);
    assert_eq!(v.color.to_bytes_rgba(), [255, 0, 0, 255]);

    assert!(nextcore_gpu::command_executor::decode_software_vertex(&data[..20], 0).is_none());
}