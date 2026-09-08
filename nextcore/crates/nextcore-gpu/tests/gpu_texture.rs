use nextcore_gpu::texture::{
    AddressMode, CompareFunc, FilterMode, SamplerDescriptor, TextureDescriptor,
    TextureFormat, TextureManager, TextureUsage,
};

#[test]
fn test_texture_create_and_destroy() {
    let mut tm = TextureManager::new();
    let id = tm.create_texture(TextureDescriptor::new_2d(64, 64, TextureFormat::Rgba8Unorm)).unwrap();
    assert_eq!(id, 1);
    assert_eq!(tm.texture_count(), 1);
    tm.delete_texture(id).unwrap();
    assert_eq!(tm.texture_count(), 0);
}

#[test]
fn test_texture_invalid_dimensions() {
    let mut tm = TextureManager::new();
    assert!(tm.create_texture(TextureDescriptor::new_2d(0, 4, TextureFormat::Rgba8Unorm)).is_err());
    assert!(tm.create_texture(TextureDescriptor::new_2d(4, 0, TextureFormat::Rgba8Unorm)).is_err());
}

#[test]
fn test_texture_upload_download() {
    let mut tm = TextureManager::new();
    let desc = TextureDescriptor::new_2d(2, 2, TextureFormat::Rgba8Unorm);
    let id = tm.create_texture(desc).unwrap();

    let mut data = vec![0u8; 2 * 2 * 4];
    for (i, b) in data.iter_mut().enumerate() {
        *b = i as u8;
    }
    tm.upload_texture(id, &data).unwrap();
    let out = tm.download_texture(id).unwrap();
    assert_eq!(out, data);
}

#[test]
fn test_texture_upload_size_mismatch() {
    let mut tm = TextureManager::new();
    let id = tm.create_texture(TextureDescriptor::new_2d(4, 4, TextureFormat::Rgba8Unorm)).unwrap();
    assert!(tm.upload_texture(id, &[0u8; 10]).is_err());
}

#[test]
fn test_texture_not_found() {
    let mut tm = TextureManager::new();
    assert!(tm.get_texture(99).is_err());
    assert!(tm.delete_texture(99).is_err());
}

#[test]
fn test_sampler_create_get_delete() {
    let mut tm = TextureManager::new();
    let sid = tm.create_sampler(SamplerDescriptor::default());
    assert!(tm.get_sampler(sid).is_some());
    assert!(tm.delete_sampler(sid));
    assert!(tm.get_sampler(sid).is_none());
}

#[test]
fn test_sample_2d_nearest() {
    let mut tm = TextureManager::new();
    let desc = TextureDescriptor::new_2d(2, 2, TextureFormat::Rgba8Unorm);
    let id = tm.create_texture(desc).unwrap();

    let data = vec![
        255, 0, 0, 255, // (0,0) red
        0, 255, 0, 255, // (1,0) green
        0, 0, 255, 255, // (0,1) blue
        255, 255, 0, 255, // (1,1) yellow
    ];
    tm.upload_texture(id, &data).unwrap();

    let sid = tm.create_sampler(SamplerDescriptor::default());
    let sample = tm.sample_2d(id, sid, 0.0, 0.0).unwrap();
    assert_eq!(sample, [1.0, 0.0, 0.0, 1.0]);

    let sample = tm.sample_2d(id, sid, 0.99, 0.0).unwrap();
    assert_eq!(sample, [0.0, 1.0, 0.0, 1.0]);
}

#[test]
fn test_sample_clamp_to_border() {
    let mut tm = TextureManager::new();
    let id = tm.create_texture(TextureDescriptor::new_2d(1, 1, TextureFormat::Rgba8Unorm)).unwrap();
    tm.upload_texture(id, &[128, 64, 32, 255]).unwrap();

    let sid = tm.create_sampler(SamplerDescriptor {
        min_filter: FilterMode::Nearest,
        mag_filter: FilterMode::Nearest,
        mip_filter: FilterMode::Nearest,
        address_u: AddressMode::ClampToEdge,
        address_v: AddressMode::ClampToEdge,
        ..SamplerDescriptor::default()
    });

    let s = tm.sample_2d(id, sid, 5.0, 5.0).unwrap();
    assert_eq!(s, [128.0 / 255.0, 64.0 / 255.0, 32.0 / 255.0, 1.0]);
}

#[test]
fn test_texture_format_size() {
    assert_eq!(TextureFormat::Rgba8Unorm.bytes_per_pixel(), 4);
    assert_eq!(TextureFormat::Rgba16Float.bytes_per_pixel(), 8);
    assert_eq!(TextureFormat::Rgba32Float.bytes_per_pixel(), 16);
    assert_eq!(TextureFormat::Depth32Float.bytes_per_pixel(), 4);
    assert!(TextureFormat::Depth32Float.is_depth());
    assert!(!TextureFormat::Rgba8Unorm.is_depth());
}

#[test]
fn test_compare_func_variants() {
    let funcs = [CompareFunc::Never, CompareFunc::Less, CompareFunc::Equal,
        CompareFunc::LessEqual, CompareFunc::Greater, CompareFunc::NotEqual,
        CompareFunc::GreaterEqual, CompareFunc::Always];
    assert_eq!(funcs.len(), 8);
}

#[test]
fn test_usage_bit_dedup() {
    let mut usage = vec![TextureUsage::ShaderRead, TextureUsage::ShaderRead, TextureUsage::RenderTarget];
    let unique: Vec<_> = {
        let mut seen = Vec::new();
        for u in usage.drain(..) {
            if !seen.contains(&u) {
                seen.push(u);
            }
        }
        seen
    };
    assert_eq!(unique, vec![TextureUsage::ShaderRead, TextureUsage::RenderTarget]);
}
