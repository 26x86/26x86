use thiserror::Error;

#[derive(Debug, Error)]
pub enum PipelineError {
    #[error("invalid vertex buffer stride: {0}")]
    InvalidStride(u32),
    #[error("invalid attachment index: {0}")]
    InvalidAttachment(u32),
    #[error("pipeline not bound")]
    NotBound,
    #[error("rasterization error: {0}")]
    RasterizationError(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Topology {
    TriangleList,
    TriangleStrip,
    LineList,
    LineStrip,
    PointList,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FillMode {
    Fill,
    Line,
    Point,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CullMode {
    None,
    Front,
    Back,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FrontFace {
    CounterClockwise,
    Clockwise,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BlendFactor {
    Zero,
    One,
    SrcAlpha,
    OneMinusSrcAlpha,
    DstAlpha,
    OneMinusDstAlpha,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BlendOp {
    Add,
    Subtract,
    ReverseSubtract,
    Min,
    Max,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CompareOp {
    Never,
    Less,
    Equal,
    LessEqual,
    Greater,
    NotEqual,
    GreaterEqual,
    Always,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StencilOp {
    Keep,
    Zero,
    Replace,
    IncrementAndClamp,
    DecrementAndClamp,
    Invert,
    IncrementAndWrap,
    DecrementAndWrap,
}

#[derive(Debug, Clone)]
pub struct DepthState {
    pub test_enabled: bool,
    pub write_enabled: bool,
    pub compare_op: CompareOp,
}

impl Default for DepthState {
    fn default() -> Self {
        Self {
            test_enabled: true,
            write_enabled: true,
            compare_op: CompareOp::Less,
        }
    }
}

#[derive(Debug, Clone)]
pub struct StencilState {
    pub test_enabled: bool,
    pub front_op: StencilOp,
    pub back_op: StencilOp,
    pub front_compare: CompareOp,
    pub back_compare: CompareOp,
    pub reference: u32,
    pub read_mask: u32,
    pub write_mask: u32,
}

impl Default for StencilState {
    fn default() -> Self {
        Self {
            test_enabled: false,
            front_op: StencilOp::Keep,
            back_op: StencilOp::Keep,
            front_compare: CompareOp::Always,
            back_compare: CompareOp::Always,
            reference: 0,
            read_mask: 0xFF,
            write_mask: 0xFF,
        }
    }
}

#[derive(Debug, Clone)]
pub struct BlendState {
    pub enabled: bool,
    pub src_color: BlendFactor,
    pub dst_color: BlendFactor,
    pub color_op: BlendOp,
    pub src_alpha: BlendFactor,
    pub dst_alpha: BlendFactor,
    pub alpha_op: BlendOp,
    pub write_mask: u8,
}

impl Default for BlendState {
    fn default() -> Self {
        Self {
            enabled: false,
            src_color: BlendFactor::One,
            dst_color: BlendFactor::Zero,
            color_op: BlendOp::Add,
            src_alpha: BlendFactor::One,
            dst_alpha: BlendFactor::Zero,
            alpha_op: BlendOp::Add,
            write_mask: 0xF,
        }
    }
}

#[derive(Debug, Clone)]
pub struct RasterizerState {
    pub fill_mode: FillMode,
    pub cull_mode: CullMode,
    pub front_face: FrontFace,
    pub depth_bias_enable: bool,
    pub depth_bias_constant: f32,
    pub depth_bias_slope: f32,
    pub depth_bias_clamp: f32,
    pub scissor_enable: bool,
    pub line_width: f32,
}

impl Default for RasterizerState {
    fn default() -> Self {
        Self {
            fill_mode: FillMode::Fill,
            cull_mode: CullMode::Back,
            front_face: FrontFace::CounterClockwise,
            depth_bias_enable: false,
            depth_bias_constant: 0.0,
            depth_bias_slope: 0.0,
            depth_bias_clamp: 0.0,
            scissor_enable: false,
            line_width: 1.0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct VertexAttribute {
    pub location: u32,
    pub binding: u32,
    pub format: VertexFormat,
    pub offset: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VertexFormat {
    Float32x1,
    Float32x2,
    Float32x3,
    Float32x4,
    Uint32x1,
    Uint32x2,
    Uint32x3,
    Uint32x4,
    Sint32x1,
    Sint32x2,
    Sint32x3,
    Sint32x4,
    Uint8x4Norm,
}

impl VertexFormat {
    pub fn byte_size(&self) -> u32 {
        match self {
            VertexFormat::Float32x1 | VertexFormat::Uint32x1 | VertexFormat::Sint32x1 => 4,
            VertexFormat::Float32x2 | VertexFormat::Uint32x2 | VertexFormat::Sint32x2 => 8,
            VertexFormat::Float32x3 | VertexFormat::Uint32x3 | VertexFormat::Sint32x3 => 12,
            VertexFormat::Float32x4 | VertexFormat::Uint32x4 | VertexFormat::Sint32x4 => 16,
            VertexFormat::Uint8x4Norm => 4,
        }
    }
}

#[derive(Debug, Clone)]
pub struct VertexBinding {
    pub binding: u32,
    pub stride: u32,
    pub input_rate: VertexInputRate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VertexInputRate {
    Vertex,
    Instance,
}

#[derive(Debug, Clone)]
pub struct VertexInputState {
    pub bindings: Vec<VertexBinding>,
    pub attributes: Vec<VertexAttribute>,
}

#[derive(Debug, Clone)]
pub struct ShaderModule {
    pub id: u32,
    pub stage: ShaderStage,
    pub entry_point: String,
    pub bytecode: Vec<u8>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShaderStage {
    Vertex,
    Fragment,
    Compute,
}

#[derive(Debug, Clone)]
pub struct ColorAttachment {
    pub format: ColorFormat,
    pub blend: BlendState,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ColorFormat {
    Rgba8Unorm,
    Rgba8Srgb,
    Bgra8Unorm,
    Rgba16Float,
}

#[derive(Debug, Clone)]
pub struct RenderPassDescriptor {
    pub color_attachments: Vec<ColorAttachment>,
    pub depth_attachment: Option<DepthAttachment>,
}

#[derive(Debug, Clone)]
pub struct DepthAttachment {
    pub format: DepthFormat,
    pub load_op: LoadOp,
    pub store_op: StoreOp,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DepthFormat {
    Depth32Float,
    Depth24Stencil8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LoadOp {
    Load,
    Clear,
    DontCare,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StoreOp {
    Store,
    DontCare,
}

#[derive(Debug, Clone)]
pub struct RenderPipelineDescriptor {
    pub vertex_input: VertexInputState,
    pub vertex_shader: ShaderModule,
    pub fragment_shader: ShaderModule,
    pub topology: Topology,
    pub rasterizer: RasterizerState,
    pub depth: DepthState,
    pub stencil: StencilState,
    pub render_pass: RenderPassDescriptor,
}

#[derive(Debug, Clone)]
pub struct RenderPipeline {
    pub id: u32,
    pub descriptor: RenderPipelineDescriptor,
}

impl RenderPipeline {
    pub fn new(id: u32, descriptor: RenderPipelineDescriptor) -> Self {
        Self { id, descriptor }
    }
}

#[derive(Debug, Clone)]
pub struct ScissorRect {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
}

#[derive(Debug, Clone)]
pub struct Viewport {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
    pub min_depth: f32,
    pub max_depth: f32,
}

#[derive(Debug, Clone)]
pub struct ViewportState {
    pub viewports: Vec<Viewport>,
    pub scissors: Vec<ScissorRect>,
}
