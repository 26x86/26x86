use std::collections::HashMap;
use thiserror::Error;

use crate::framebuffer::{FramebufferError, LinearFramebuffer};
use crate::rasterizer::{Color, RasterError, SoftwareRasterizer, Vec2, Vec3, Vec4, Vertex};
use crate::texture::{TextureError, TextureManager};

/// 소프트웨어 폴백 정점 한 개의 인터리브 레이아웃 크기(바이트):
/// position Vec4(16) + color Color(16) + tex_coord Vec2(8) + normal Vec3(12).
pub const SOFTWARE_RENDER_VERTEX_STRIDE: u32 = 52;

fn f32_at(data: &[u8], offset: usize) -> Option<f32> {
    let bytes: [u8; 4] = data.get(offset..offset + 4)?.try_into().ok()?;
    Some(f32::from_le_bytes(bytes))
}

/// `SOFTWARE_RENDER_VERTEX_STRIDE` 레이아웃으로 인코딩된 정점을 offset에서 해석한다.
pub fn decode_software_vertex(data: &[u8], offset: usize) -> Option<Vertex> {
    let position = Vec4::new(
        f32_at(data, offset)?,
        f32_at(data, offset + 4)?,
        f32_at(data, offset + 8)?,
        f32_at(data, offset + 12)?,
    );
    let color = Color::new(
        f32_at(data, offset + 16)?,
        f32_at(data, offset + 20)?,
        f32_at(data, offset + 24)?,
        f32_at(data, offset + 28)?,
    );
    let tex_coord = Vec2::new(f32_at(data, offset + 32)?, f32_at(data, offset + 36)?);
    let normal = Vec3::new(
        f32_at(data, offset + 40)?,
        f32_at(data, offset + 44)?,
        f32_at(data, offset + 48)?,
    );
    Some(Vertex {
        position,
        color,
        tex_coord,
        normal,
    })
}

fn read_index(data: &[u8], offset: usize, index_type: IndexType) -> u32 {
    match index_type {
        IndexType::Uint16 => data
            .get(offset * 2..offset * 2 + 2)
            .map(|b| u16::from_le_bytes([b[0], b[1]]) as u32)
            .unwrap_or(0),
        IndexType::Uint32 => data
            .get(offset * 4..offset * 4 + 4)
            .map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]))
            .unwrap_or(0),
    }
}

#[derive(Debug, Error)]
pub enum ExecutorError {
    #[error("framebuffer error: {0}")]
    Framebuffer(#[from] FramebufferError),
    #[error("texture error: {0}")]
    Texture(#[from] TextureError),
    #[error("raster error: {0}")]
    Raster(#[from] RasterError),
    #[error("command buffer not found: {0}")]
    CommandBufferNotFound(u64),
    #[error("pipeline not bound")]
    PipelineNotBound,
    #[error("render pass not active")]
    RenderPassNotActive,
    #[error("vertex buffer slot {0} not bound")]
    VertexBufferNotBound(u32),
    #[error("index buffer not bound")]
    IndexBufferNotBound,
    #[error("uniform buffer slot {0} not bound")]
    UniformBufferNotBound(u32),
    #[error("executor error: {0}")]
    Generic(String),
}

#[derive(Debug, Clone)]
pub struct VertexBuffer {
    pub data: Vec<u8>,
    pub stride: u32,
}

#[derive(Debug, Clone)]
pub struct IndexBuffer {
    pub data: Vec<u8>,
    pub index_type: IndexType,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IndexType {
    Uint16,
    Uint32,
}

#[derive(Debug, Clone)]
pub struct UniformBuffer {
    pub data: Vec<u8>,
}

#[derive(Debug, Clone)]
pub enum GpuCommand {
    BeginRenderPass {
        clear_color: [f32; 4],
        clear_depth: f32,
    },
    EndRenderPass,
    BindPipeline(u32),
    BindVertexBuffer { slot: u32, buffer_id: u64 },
    BindIndexBuffer { buffer_id: u64, index_type: IndexType },
    BindUniformBuffer { slot: u32, buffer_id: u64 },
    BindTexture { slot: u32, texture_id: u32, sampler_id: u32 },
    Draw { vertex_count: u32, first_vertex: u32 },
    DrawIndexed { index_count: u32, first_index: u32, vertex_offset: i32 },
    DrawInstanced { vertex_count: u32, instance_count: u32, first_vertex: u32, first_instance: u32 },
    DrawIndexedInstanced {
        index_count: u32,
        instance_count: u32,
        first_index: u32,
        vertex_offset: i32,
        first_instance: u32,
    },
    SetViewport(crate::render_pipeline::Viewport),
    SetScissor(crate::render_pipeline::ScissorRect),
    SetLineWidth(f32),
    PushConstants { offset: u32, data: Vec<u8> },
    CopyBufferToTexture { buffer_id: u64, texture_id: u32 },
    CopyTextureToBuffer { texture_id: u32, buffer_id: u64 },
    ClearTexture { texture_id: u32, color: [f32; 4] },
    GenerateMipmaps(u32),
    DispatchCompute { pipeline_id: u32, x: u32, y: u32, z: u32 },
}

#[derive(Debug, Clone)]
pub struct RecordedCommandBuffer {
    pub commands: Vec<GpuCommand>,
}

#[derive(Debug, Clone)]
struct BoundState {
    pipeline_id: Option<u32>,
    vertex_buffers: HashMap<u32, u64>,
    index_buffer: Option<(u64, IndexType)>,
    uniform_buffers: HashMap<u32, u64>,
    textures: HashMap<u32, (u32, u32)>,
    viewport: Option<crate::render_pipeline::Viewport>,
    scissor: Option<crate::render_pipeline::ScissorRect>,
}

struct RenderPassState {
    framebuffer: usize,
    clear_color: [f32; 4],
    clear_depth: f32,
    draw_calls: Vec<DrawCall>,
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
enum DrawCall {
    Draw { first_vertex: u32, vertex_count: u32 },
    DrawIndexed { first_index: u32, index_count: u32, vertex_offset: i32 },
    DrawInstanced { first_vertex: u32, vertex_count: u32, instance_count: u32, first_instance: u32 },
    DrawIndexedInstanced {
        first_index: u32,
        index_count: u32,
        instance_count: u32,
        vertex_offset: i32,
        first_instance: u32,
    },
}

impl DrawCall {
    fn descriptor(&self) -> &'static str {
        match self {
            DrawCall::Draw { .. } => "draw",
            DrawCall::DrawIndexed { .. } => "draw-indexed",
            DrawCall::DrawInstanced { .. } => "draw-instanced",
            DrawCall::DrawIndexedInstanced { .. } => "draw-indexed-instanced",
        }
    }
}

impl Default for CommandExecutor {
    fn default() -> Self {
        Self::new()
    }
}

pub struct CommandExecutor {
    vertex_buffers: HashMap<u64, VertexBuffer>,
    index_buffers: HashMap<u64, IndexBuffer>,
    uniform_buffers: HashMap<u64, UniformBuffer>,
    next_buffer_id: u64,
    bound: BoundState,
    active_pass: Option<RenderPassState>,
    executed_commands: u64,
}

impl CommandExecutor {
    pub fn new() -> Self {
        Self {
            vertex_buffers: HashMap::new(),
            index_buffers: HashMap::new(),
            uniform_buffers: HashMap::new(),
            next_buffer_id: 1,
            bound: BoundState {
                pipeline_id: None,
                vertex_buffers: HashMap::new(),
                index_buffer: None,
                uniform_buffers: HashMap::new(),
                textures: HashMap::new(),
                viewport: None,
                scissor: None,
            },
            active_pass: None,
            executed_commands: 0,
        }
    }

    pub fn create_vertex_buffer(&mut self, data: Vec<u8>, stride: u32) -> u64 {
        let id = self.next_buffer_id;
        self.next_buffer_id += 1;
        self.vertex_buffers.insert(id, VertexBuffer { data, stride });
        id
    }

    pub fn create_index_buffer(&mut self, data: Vec<u8>, index_type: IndexType) -> u64 {
        let id = self.next_buffer_id;
        self.next_buffer_id += 1;
        self.index_buffers.insert(id, IndexBuffer { data, index_type });
        id
    }

    pub fn create_uniform_buffer(&mut self, data: Vec<u8>) -> u64 {
        let id = self.next_buffer_id;
        self.next_buffer_id += 1;
        self.uniform_buffers.insert(id, UniformBuffer { data });
        id
    }

    pub fn write_vertex_buffer(&mut self, id: u64, data: &[u8]) -> Result<(), ExecutorError> {
        let buf = self.vertex_buffers.get_mut(&id)
            .ok_or_else(|| ExecutorError::Generic(format!("vertex buffer {} not found", id)))?;
        let copy_len = data.len().min(buf.data.len());
        buf.data[..copy_len].copy_from_slice(&data[..copy_len]);
        Ok(())
    }

    pub fn write_uniform_buffer(&mut self, id: u64, data: &[u8]) -> Result<(), ExecutorError> {
        let buf = self.uniform_buffers.get_mut(&id)
            .ok_or_else(|| ExecutorError::Generic(format!("uniform buffer {} not found", id)))?;
        let copy_len = data.len().min(buf.data.len());
        buf.data[..copy_len].copy_from_slice(&data[..copy_len]);
        Ok(())
    }

    pub fn execute(
        &mut self,
        commands: &RecordedCommandBuffer,
        framebuffers: &mut [LinearFramebuffer],
        textures: &mut TextureManager,
    ) -> Result<(), ExecutorError> {
        self.execute_inner(commands, framebuffers, textures, None)
    }

    /// `execute`와 같지만 BoundState의 vertex/index buffer에서 정점을 해석해
    /// SoftwareRasterizer로 실제 삼각형 래스터화까지 수행한다. depth buffer는
    /// render pass 시작 시 프레임버퍼 크기로 재할당·초기화된다.
    pub fn execute_with_rasterizer(
        &mut self,
        commands: &RecordedCommandBuffer,
        framebuffers: &mut [LinearFramebuffer],
        textures: &mut TextureManager,
        rasterizer: &mut SoftwareRasterizer,
    ) -> Result<(), ExecutorError> {
        self.execute_inner(commands, framebuffers, textures, Some(rasterizer))
    }

    fn execute_inner(
        &mut self,
        commands: &RecordedCommandBuffer,
        framebuffers: &mut [LinearFramebuffer],
        textures: &mut TextureManager,
        mut rasterizer: Option<&mut SoftwareRasterizer>,
    ) -> Result<(), ExecutorError> {
        for cmd in &commands.commands {
            match cmd {
                GpuCommand::BeginRenderPass { clear_color, clear_depth } => {
                    let fb_idx = 0;
                    if fb_idx < framebuffers.len() {
                        let c = [
                            (clear_color[0] * 255.0) as u8,
                            (clear_color[1] * 255.0) as u8,
                            (clear_color[2] * 255.0) as u8,
                            (clear_color[3] * 255.0) as u8,
                        ];
                        framebuffers[fb_idx].clear(c);
                        if let Some(ras) = rasterizer.as_deref_mut() {
                            ras.resize_depth_buffer(framebuffers[fb_idx].width(), framebuffers[fb_idx].height());
                            ras.clear_depth_buffer();
                        }
                    }
                    self.active_pass = Some(RenderPassState {
                        framebuffer: fb_idx,
                        clear_color: *clear_color,
                        clear_depth: *clear_depth,
                        draw_calls: Vec::new(),
                    });
                }
                GpuCommand::EndRenderPass => {
                    if let Some(pass) = &self.active_pass {
                        log::debug!(
                            "end render pass fb={} clear={:?} depth={} calls={}: {}",
                            pass.framebuffer,
                            pass.clear_color,
                            pass.clear_depth,
                            pass.draw_calls.len(),
                            pass.draw_calls.iter().map(|c| c.descriptor()).collect::<Vec<_>>().join(",")
                        );
                    }
                    self.active_pass = None;
                }
                GpuCommand::BindPipeline(id) => {
                    self.bound.pipeline_id = Some(*id);
                }
                GpuCommand::BindVertexBuffer { slot, buffer_id } => {
                    self.bound.vertex_buffers.insert(*slot, *buffer_id);
                }
                GpuCommand::BindIndexBuffer { buffer_id, index_type } => {
                    self.bound.index_buffer = Some((*buffer_id, *index_type));
                }
                GpuCommand::BindUniformBuffer { slot, buffer_id } => {
                    self.bound.uniform_buffers.insert(*slot, *buffer_id);
                }
                GpuCommand::BindTexture { slot, texture_id, sampler_id } => {
                    self.bound.textures.insert(*slot, (*texture_id, *sampler_id));
                }
                GpuCommand::Draw { vertex_count, first_vertex } => {
                    if let Some(ref mut pass) = self.active_pass {
                        pass.draw_calls.push(DrawCall::Draw {
                            first_vertex: *first_vertex,
                            vertex_count: *vertex_count,
                        });
                        if let Some(ras) = rasterizer.as_deref_mut() {
                            if let Some(buf_id) = self.bound.vertex_buffers.get(&0).copied() {
                                if let Some(buf) = self.vertex_buffers.get(&buf_id) {
                                    let mut vertices = Vec::with_capacity(*vertex_count as usize);
                                    for i in 0..*vertex_count {
                                        let base = (*first_vertex as usize + i as usize)
                                            * SOFTWARE_RENDER_VERTEX_STRIDE as usize;
                                        if let Some(v) = decode_software_vertex(&buf.data, base) {
                                            vertices.push(v);
                                        }
                                    }
                                    ras.rasterize_triangle_list(
                                        &mut framebuffers[pass.framebuffer],
                                        &vertices,
                                        true,
                                    )?;
                                }
                            }
                        }
                        self.executed_commands += 1;
                    }
                }
                GpuCommand::DrawIndexed { index_count, first_index, vertex_offset } => {
                    if let Some(ref mut pass) = self.active_pass {
                        pass.draw_calls.push(DrawCall::DrawIndexed {
                            first_index: *first_index,
                            index_count: *index_count,
                            vertex_offset: *vertex_offset,
                        });
                        if let Some(ras) = rasterizer.as_deref_mut() {
                            if let (Some((ibuf_id, index_type)), Some(vbuf_id)) =
                                (self.bound.index_buffer, self.bound.vertex_buffers.get(&0).copied())
                            {
                                if let (Some(ibuf), Some(vbuf)) = (
                                    self.index_buffers.get(&ibuf_id),
                                    self.vertex_buffers.get(&vbuf_id),
                                ) {
                                    let mut vertices = Vec::with_capacity(*index_count as usize);
                                    for i in 0..*index_count {
                                        let raw = read_index(&ibuf.data, (*first_index + i) as usize, index_type);
                                        let base = ((raw as i64 + *vertex_offset as i64).max(0) as usize)
                                            * SOFTWARE_RENDER_VERTEX_STRIDE as usize;
                                        if let Some(v) = decode_software_vertex(&vbuf.data, base) {
                                            vertices.push(v);
                                        }
                                    }
                                    ras.rasterize_triangle_list(
                                        &mut framebuffers[pass.framebuffer],
                                        &vertices,
                                        true,
                                    )?;
                                }
                            }
                        }
                        self.executed_commands += 1;
                    }
                }
                GpuCommand::DrawInstanced { vertex_count, instance_count, first_vertex, first_instance } => {
                    if let Some(ref mut pass) = self.active_pass {
                        pass.draw_calls.push(DrawCall::DrawInstanced {
                            first_vertex: *first_vertex,
                            vertex_count: *vertex_count,
                            instance_count: *instance_count,
                            first_instance: *first_instance,
                        });
                        self.executed_commands += 1;
                    }
                }
                GpuCommand::DrawIndexedInstanced {
                    index_count,
                    instance_count,
                    first_index,
                    vertex_offset,
                    first_instance,
                } => {
                    if let Some(ref mut pass) = self.active_pass {
                        pass.draw_calls.push(DrawCall::DrawIndexedInstanced {
                            first_index: *first_index,
                            index_count: *index_count,
                            instance_count: *instance_count,
                            vertex_offset: *vertex_offset,
                            first_instance: *first_instance,
                        });
                        self.executed_commands += 1;
                    }
                }
                GpuCommand::SetViewport(vp) => {
                    self.bound.viewport = Some(vp.clone());
                }
                GpuCommand::SetScissor(rect) => {
                    self.bound.scissor = Some(rect.clone());
                }
                GpuCommand::SetLineWidth(_w) => {}
                GpuCommand::PushConstants { .. } => {}
                GpuCommand::CopyBufferToTexture { buffer_id, texture_id } => {
                    if let Some(buf) = self.vertex_buffers.get(buffer_id) {
                        let _ = textures.upload_texture(*texture_id, &buf.data);
                    }
                }
                GpuCommand::CopyTextureToBuffer { texture_id, buffer_id } => {
                    if let Ok(data) = textures.download_texture(*texture_id) {
                        if let Some(buf) = self.vertex_buffers.get_mut(buffer_id) {
                            let copy_len = data.len().min(buf.data.len());
                            buf.data[..copy_len].copy_from_slice(&data[..copy_len]);
                        }
                    }
                }
                GpuCommand::ClearTexture { texture_id, color } => {
                    if let Ok(tex) = textures.get_texture_mut(*texture_id) {
                        let c = [
                            (color[0] * 255.0) as u8,
                            (color[1] * 255.0) as u8,
                            (color[2] * 255.0) as u8,
                            (color[3] * 255.0) as u8,
                        ];
                        tex.data.chunks_exact_mut(4).for_each(|pixel| {
                            pixel.copy_from_slice(&c);
                        });
                    }
                }
                GpuCommand::GenerateMipmaps(_) => {}
                GpuCommand::DispatchCompute { pipeline_id, x, y, z } => {
                    log::debug!("compute dispatch pipeline {} ({},{},{})", pipeline_id, x, y, z);
                    self.executed_commands += 1;
                }
            }
        }
        Ok(())
    }

    pub fn executed_command_count(&self) -> u64 {
        self.executed_commands
    }

    pub fn reset_stats(&mut self) {
        self.executed_commands = 0;
    }
}
