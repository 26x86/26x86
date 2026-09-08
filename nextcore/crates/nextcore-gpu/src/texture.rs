use std::collections::HashMap;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum TextureError {
    #[error("texture not found: {0}")]
    NotFound(u32),
    #[error("invalid dimensions: {width}x{height}")]
    InvalidDimensions { width: u32, height: u32 },
    #[error("data size mismatch: expected {expected}, got {actual}")]
    DataSizeMismatch { expected: usize, actual: usize },
    #[error("unsupported pixel format")]
    UnsupportedFormat,
    #[error("sampler error: {0}")]
    SamplerError(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TextureFormat {
    Rgba8Unorm,
    Bgra8Unorm,
    Rgba8Srgb,
    Rgba16Float,
    Rgba32Float,
    Depth32Float,
    Depth24Stencil8,
}

impl TextureFormat {
    pub fn bytes_per_pixel(&self) -> usize {
        match self {
            TextureFormat::Rgba8Unorm
            | TextureFormat::Bgra8Unorm
            | TextureFormat::Rgba8Srgb
            | TextureFormat::Depth24Stencil8 => 4,
            TextureFormat::Rgba16Float => 8,
            TextureFormat::Rgba32Float => 16,
            TextureFormat::Depth32Float => 4,
        }
    }

    pub fn is_depth(&self) -> bool {
        matches!(self, TextureFormat::Depth32Float | TextureFormat::Depth24Stencil8)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TextureUsage {
    ShaderRead,
    ShaderWrite,
    RenderTarget,
    DepthAttachment,
    CopySrc,
    CopyDst,
}

#[derive(Debug, Clone)]
pub struct TextureDescriptor {
    pub width: u32,
    pub height: u32,
    pub depth: u32,
    pub mip_levels: u32,
    pub array_layers: u32,
    pub format: TextureFormat,
    pub usage: Vec<TextureUsage>,
}

impl TextureDescriptor {
    pub fn new_2d(width: u32, height: u32, format: TextureFormat) -> Self {
        Self {
            width,
            height,
            depth: 1,
            mip_levels: 1,
            array_layers: 1,
            format,
            usage: vec![TextureUsage::ShaderRead],
        }
    }

    pub fn total_pixels(&self) -> u64 {
        self.width as u64 * self.height as u64 * self.depth as u64 * self.array_layers as u64
    }

    pub fn data_size(&self) -> usize {
        self.total_pixels() as usize * self.format.bytes_per_pixel()
    }
}

#[derive(Debug, Clone)]
pub struct Texture {
    pub id: u32,
    pub descriptor: TextureDescriptor,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FilterMode {
    Nearest,
    Linear,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AddressMode {
    Repeat,
    ClampToEdge,
    ClampToBorder,
    MirrorRepeat,
}

#[derive(Debug, Clone)]
pub struct SamplerDescriptor {
    pub min_filter: FilterMode,
    pub mag_filter: FilterMode,
    pub mip_filter: FilterMode,
    pub address_u: AddressMode,
    pub address_v: AddressMode,
    pub address_w: AddressMode,
    pub max_anisotropy: f32,
    pub min_lod: f32,
    pub max_lod: f32,
}

impl Default for SamplerDescriptor {
    fn default() -> Self {
        Self {
            min_filter: FilterMode::Linear,
            mag_filter: FilterMode::Linear,
            mip_filter: FilterMode::Linear,
            address_u: AddressMode::ClampToEdge,
            address_v: AddressMode::ClampToEdge,
            address_w: AddressMode::ClampToEdge,
            max_anisotropy: 1.0,
            min_lod: 0.0,
            max_lod: 1000.0,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CompareFunc {
    Never,
    Less,
    Equal,
    LessEqual,
    Greater,
    NotEqual,
    GreaterEqual,
    Always,
}

pub struct TextureManager {
    next_id: u32,
    textures: HashMap<u32, Texture>,
    samplers: HashMap<u32, SamplerDescriptor>,
    next_sampler_id: u32,
}

impl Default for TextureManager {
    fn default() -> Self {
        Self::new()
    }
}

impl TextureManager {
    pub fn new() -> Self {
        Self {
            next_id: 1,
            textures: HashMap::new(),
            samplers: HashMap::new(),
            next_sampler_id: 1,
        }
    }

    pub fn create_texture(&mut self, desc: TextureDescriptor) -> Result<u32, TextureError> {
        if desc.width == 0 || desc.height == 0 {
            return Err(TextureError::InvalidDimensions {
                width: desc.width,
                height: desc.height,
            });
        }
        let id = self.next_id;
        self.next_id += 1;
        let data = vec![0u8; desc.data_size()];
        self.textures.insert(id, Texture { id, descriptor: desc, data });
        Ok(id)
    }

    pub fn upload_texture(&mut self, id: u32, data: &[u8]) -> Result<(), TextureError> {
        let tex = self.textures.get_mut(&id).ok_or(TextureError::NotFound(id))?;
        if data.len() != tex.descriptor.data_size() {
            return Err(TextureError::DataSizeMismatch {
                expected: tex.descriptor.data_size(),
                actual: data.len(),
            });
        }
        tex.data.copy_from_slice(data);
        Ok(())
    }

    pub fn download_texture(&self, id: u32) -> Result<Vec<u8>, TextureError> {
        let tex = self.textures.get(&id).ok_or(TextureError::NotFound(id))?;
        Ok(tex.data.clone())
    }

    pub fn get_texture(&self, id: u32) -> Result<&Texture, TextureError> {
        self.textures.get(&id).ok_or(TextureError::NotFound(id))
    }

    pub fn get_texture_mut(&mut self, id: u32) -> Result<&mut Texture, TextureError> {
        self.textures.get_mut(&id).ok_or(TextureError::NotFound(id))
    }

    pub fn delete_texture(&mut self, id: u32) -> Result<(), TextureError> {
        self.textures.remove(&id).ok_or(TextureError::NotFound(id))?;
        Ok(())
    }

    pub fn texture_count(&self) -> usize {
        self.textures.len()
    }

    pub fn create_sampler(&mut self, desc: SamplerDescriptor) -> u32 {
        let id = self.next_sampler_id;
        self.next_sampler_id += 1;
        self.samplers.insert(id, desc);
        id
    }

    pub fn get_sampler(&self, id: u32) -> Option<&SamplerDescriptor> {
        self.samplers.get(&id)
    }

    pub fn delete_sampler(&mut self, id: u32) -> bool {
        self.samplers.remove(&id).is_some()
    }

    pub fn sample_2d(
        &self,
        texture_id: u32,
        sampler_id: u32,
        u: f32,
        v: f32,
    ) -> Result<[f32; 4], TextureError> {
        let tex = self.textures.get(&texture_id).ok_or(TextureError::NotFound(texture_id))?;
        let sampler = self.samplers.get(&sampler_id).ok_or_else(|| {
            TextureError::SamplerError(format!("sampler {} not found", sampler_id))
        })?;

        let w = tex.descriptor.width as f32;
        let h = tex.descriptor.height as f32;

        let (tex_u, tex_v) = match sampler.address_u {
            AddressMode::ClampToEdge => (u.clamp(0.0, 1.0 - f32::EPSILON), v.clamp(0.0, 1.0 - f32::EPSILON)),
            AddressMode::Repeat => (u - u.floor(), v - v.floor()),
            AddressMode::MirrorRepeat => {
                let fu = u.floor() as i32;
                let tu = u - u.floor();
                let mu = if fu % 2 == 0 { tu } else { 1.0 - tu };
                let fv = v.floor() as i32;
                let tv = v - v.floor();
                let mv = if fv % 2 == 0 { tv } else { 1.0 - tv };
                (mu, mv)
            }
            AddressMode::ClampToBorder => (u.clamp(0.0, 1.0), v.clamp(0.0, 1.0)),
        };

        let px = ((tex_u * w) as u32).min(w as u32 - 1);
        let py = ((tex_v * h) as u32).min(h as u32 - 1);
        let bpp = tex.descriptor.format.bytes_per_pixel();
        let offset = ((py * tex.descriptor.width + px) * bpp as u32) as usize;

        if offset + 4 > tex.data.len() {
            return Err(TextureError::SamplerError("sample out of bounds".into()));
        }

        match tex.descriptor.format {
            TextureFormat::Rgba8Unorm | TextureFormat::Rgba8Srgb => Ok([
                tex.data[offset] as f32 / 255.0,
                tex.data[offset + 1] as f32 / 255.0,
                tex.data[offset + 2] as f32 / 255.0,
                tex.data[offset + 3] as f32 / 255.0,
            ]),
            TextureFormat::Bgra8Unorm => Ok([
                tex.data[offset + 2] as f32 / 255.0,
                tex.data[offset + 1] as f32 / 255.0,
                tex.data[offset] as f32 / 255.0,
                tex.data[offset + 3] as f32 / 255.0,
            ]),
            _ => Err(TextureError::UnsupportedFormat),
        }
    }
}
