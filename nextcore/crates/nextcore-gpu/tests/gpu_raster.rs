use nextcore_gpu::rasterizer::{
    blend_add, blend_multiply, blend_normal, Color, SoftwareRasterizer, Vec2, Vec3, Vec4, Vertex,
};
use nextcore_gpu::framebuffer::{LinearFramebuffer, PixelFormat};

#[test]
fn test_color_conversions() {
    let c = Color::new(0.5, 0.25, 0.125, 1.0);
    assert_eq!(c.to_bytes_rgba(), [127, 63, 31, 255]);
    assert_eq!(c.to_bytes_bgra(), [31, 63, 127, 255]);
}

#[test]
fn test_color_clamp() {
    let c = Color::new(2.0, -1.0, 0.5, 1.5);
    assert_eq!(c.to_bytes_rgba(), [255, 0, 127, 255]);
}

#[test]
fn test_color_lerp() {
    let a = Color::new(0.0, 0.0, 0.0, 1.0);
    let b = Color::new(1.0, 1.0, 1.0, 1.0);
    let mid = a.lerp(b, 0.5);
    assert!((mid.r - 0.5).abs() < 1e-6);
    assert!((mid.g - 0.5).abs() < 1e-6);
}

#[test]
fn test_alpha_blend() {
    let dst = Color::new(0.0, 0.0, 0.0, 1.0);
    let src = Color::new(1.0, 0.0, 0.0, 0.5);
    let blended = dst.alpha_blend(src);
    assert!((blended.r - 0.5).abs() < 1e-6);
}

#[test]
fn test_blend_functions() {
    let src = Color::new(1.0, 0.5, 0.25, 0.5);
    let dst = Color::new(0.5, 0.5, 0.5, 1.0);

    let normal = blend_normal(src, dst);
    assert!((normal.r - 0.75).abs() < 1e-6);

    let add = blend_add(src, dst);
    assert!(add.r >= dst.r);

    let mul = blend_multiply(src, dst);
    assert!((mul.r - 0.5).abs() < 1e-6);
}

#[test]
fn test_vec_operations() {
    let a = Vec2::new(1.0, 2.0);
    let b = Vec2::new(3.0, 4.0);
    assert!((a.cross(b) - (-2.0)).abs() < 1e-6);

    let v3a = Vec3::new(1.0, 0.0, 0.0);
    let v3b = Vec3::new(0.0, 1.0, 0.0);
    let cross = v3a.cross(v3b);
    assert!((cross.z - 1.0).abs() < 1e-6);
    assert!((v3a.dot(v3b)).abs() < 1e-6);
}

#[test]
fn test_perspective_divide() {
    let v = Vec4::new(2.0, 4.0, 6.0, 2.0);
    let v3 = v.perspective_divide();
    assert!((v3.x - 1.0).abs() < 1e-6);
    assert!((v3.y - 2.0).abs() < 1e-6);
}

#[test]
fn test_rasterize_fullscreen_triangle() {
    let mut rast = SoftwareRasterizer::new();
    let mut fb = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);

    rast.resize_depth_buffer(4, 4);
    rast.clear_depth_buffer();

    let v0 = Vertex::new(Vec4::new(-1.0, 1.0, 0.0, 1.0), Color::red());
    let v1 = Vertex::new(Vec4::new(1.0, 1.0, 0.0, 1.0), Color::green());
    let v2 = Vertex::new(Vec4::new(-1.0, -1.0, 0.0, 1.0), Color::blue());

    rast.rasterize_triangle(&mut fb, v0, v1, v2, false).unwrap();

    // Interior pixels should be covered
    let interior = fb.get_pixel(1, 1).unwrap();
    assert_ne!(interior, [0, 0, 0, 0]);
}

#[test]
fn test_rasterize_triangle_list() {
    let mut rast = SoftwareRasterizer::new();
    let mut fb = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);
    rast.resize_depth_buffer(4, 4);

    let vertices = vec![
        Vertex::new(Vec4::new(-1.0, 1.0, 0.0, 1.0), Color::white()),
        Vertex::new(Vec4::new(1.0, 1.0, 0.0, 1.0), Color::white()),
        Vertex::new(Vec4::new(-1.0, -1.0, 0.0, 1.0), Color::white()),
    ];
    rast.rasterize_triangle_list(&mut fb, &vertices, false).unwrap();
    assert_eq!(fb.get_pixel(1, 1).unwrap(), [255, 255, 255, 255]);
    assert_eq!(fb.get_pixel(2, 1).unwrap(), [255, 255, 255, 255]);
}

#[test]
fn test_rasterize_triangle_list_bad_length() {
    let mut rast = SoftwareRasterizer::new();
    let mut fb = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);
    let vertices = vec![
        Vertex::new(Vec4::new(0.0, 0.0, 0.0, 1.0), Color::white()),
        Vertex::new(Vec4::new(1.0, 0.0, 0.0, 1.0), Color::white()),
    ];
    assert!(rast.rasterize_triangle_list(&mut fb, &vertices, false).is_err());
}

#[test]
fn test_rasterize_line() {
    let mut fb = LinearFramebuffer::new(10, 10, PixelFormat::Rgba8);
    let v0 = Vertex::new(Vec4::new(-1.0, 1.0, 0.0, 1.0), Color::red());
    let v1 = Vertex::new(Vec4::new(1.0, -1.0, 0.0, 1.0), Color::red());
    SoftwareRasterizer::rasterize_line(&mut fb, v0, v1, 1.0).unwrap();
    assert_eq!(fb.get_pixel(0, 0).unwrap(), [255, 0, 0, 255]);
    assert_eq!(fb.get_pixel(9, 9).unwrap(), [255, 0, 0, 255]);
}

#[test]
fn test_vertex_with_attributes() {
    let v = Vertex::new(Vec4::new(0.0, 0.0, 0.0, 1.0), Color::white())
        .with_tex_coord(0.5, 0.5)
        .with_normal(0.0, 0.0, 1.0);
    assert!((v.tex_coord.x - 0.5).abs() < 1e-6);
    assert!((v.normal.z - 1.0).abs() < 1e-6);
}
