use nextcore_gpu::render_pipeline::{
    BlendFactor, BlendOp, BlendState, CullMode, DepthState, FillMode, FrontFace,
    RasterizerState, RenderPipeline, RenderPipelineDescriptor, ShaderModule, ShaderStage,
    StencilState, VertexAttribute, VertexBinding, VertexFormat, VertexInputRate, VertexInputState,
};

#[test]
fn test_vertex_format_sizes() {
    assert_eq!(VertexFormat::Float32x1.byte_size(), 4);
    assert_eq!(VertexFormat::Float32x2.byte_size(), 8);
    assert_eq!(VertexFormat::Float32x3.byte_size(), 12);
    assert_eq!(VertexFormat::Float32x4.byte_size(), 16);
    assert_eq!(VertexFormat::Uint8x4Norm.byte_size(), 4);
}

#[test]
fn test_default_rasterizer_state() {
    let rs = RasterizerState::default();
    assert_eq!(rs.fill_mode, FillMode::Fill);
    assert_eq!(rs.cull_mode, CullMode::Back);
    assert_eq!(rs.front_face, FrontFace::CounterClockwise);
}

#[test]
fn test_default_depth_state() {
    let ds = DepthState::default();
    assert!(ds.test_enabled);
    assert!(ds.write_enabled);
}

#[test]
fn test_default_stencil_state() {
    let ss = StencilState::default();
    assert!(!ss.test_enabled);
    assert_eq!(ss.read_mask, 0xFF);
}

#[test]
fn test_default_blend_state() {
    let bs = BlendState::default();
    assert!(!bs.enabled);
    assert_eq!(bs.src_color, BlendFactor::One);
    assert_eq!(bs.dst_color, BlendFactor::Zero);
    assert_eq!(bs.color_op, BlendOp::Add);
}

#[test]
fn test_pipeline_construction() {
    let vertex_shader = ShaderModule {
        id: 1,
        stage: ShaderStage::Vertex,
        entry_point: "main".into(),
        bytecode: vec![0x01, 0x02, 0x03],
    };
    let fragment_shader = ShaderModule {
        id: 2,
        stage: ShaderStage::Fragment,
        entry_point: "main".into(),
        bytecode: vec![0x04, 0x05, 0x06],
    };

    let desc = RenderPipelineDescriptor {
        vertex_input: VertexInputState {
            bindings: vec![VertexBinding {
                binding: 0,
                stride: 32,
                input_rate: VertexInputRate::Vertex,
            }],
            attributes: vec![
                VertexAttribute { location: 0, binding: 0, format: VertexFormat::Float32x3, offset: 0 },
                VertexAttribute { location: 1, binding: 0, format: VertexFormat::Float32x2, offset: 12 },
            ],
        },
        vertex_shader,
        fragment_shader,
        topology: nextcore_gpu::render_pipeline::Topology::TriangleList,
        rasterizer: RasterizerState::default(),
        depth: DepthState::default(),
        stencil: StencilState::default(),
        render_pass: nextcore_gpu::render_pipeline::RenderPassDescriptor {
            color_attachments: Vec::new(),
            depth_attachment: None,
        },
    };

    let pipeline = RenderPipeline::new(1, desc);
    assert_eq!(pipeline.id, 1);
    assert_eq!(pipeline.descriptor.vertex_input.bindings.len(), 1);
    assert_eq!(pipeline.descriptor.vertex_input.attributes.len(), 2);
    assert_eq!(pipeline.descriptor.vertex_shader.id, 1);
    assert_eq!(pipeline.descriptor.fragment_shader.id, 2);
}

#[test]
fn test_attribute_offsets() {
    let attrs = [
        VertexAttribute { location: 0, binding: 0, format: VertexFormat::Float32x3, offset: 0 },
        VertexAttribute { location: 1, binding: 0, format: VertexFormat::Float32x3, offset: 12 },
        VertexAttribute { location: 2, binding: 0, format: VertexFormat::Float32x2, offset: 24 },
    ];
    assert_eq!(attrs[0].offset + attrs[0].format.byte_size(), 12);
    assert_eq!(attrs[1].offset + attrs[1].format.byte_size(), 24);
    assert_eq!(attrs[2].offset + attrs[2].format.byte_size(), 32);
}

#[test]
fn test_shader_module_stages() {
    let vs = ShaderModule { id: 1, stage: ShaderStage::Vertex, entry_point: "main".into(), bytecode: vec![] };
    let fs = ShaderModule { id: 2, stage: ShaderStage::Fragment, entry_point: "main".into(), bytecode: vec![] };
    let cs = ShaderModule { id: 3, stage: ShaderStage::Compute, entry_point: "main".into(), bytecode: vec![] };
    assert_eq!(vs.stage, ShaderStage::Vertex);
    assert_eq!(fs.stage, ShaderStage::Fragment);
    assert_eq!(cs.stage, ShaderStage::Compute);
}

#[test]
fn test_blend_factors_variants() {
    let _ = [
        BlendFactor::Zero, BlendFactor::One, BlendFactor::SrcAlpha,
        BlendFactor::OneMinusSrcAlpha, BlendFactor::DstAlpha, BlendFactor::OneMinusDstAlpha,
    ];
}

#[test]
fn test_input_rate_equality() {
    assert_eq!(VertexInputRate::Vertex, VertexInputRate::Vertex);
    assert_eq!(VertexInputRate::Instance, VertexInputRate::Instance);
    assert_ne!(VertexInputRate::Vertex, VertexInputRate::Instance);
}
