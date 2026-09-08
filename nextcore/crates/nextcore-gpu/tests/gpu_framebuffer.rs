use nextcore_gpu::framebuffer::{DoubleBuffer, LinearFramebuffer, PixelFormat};

#[test]
fn test_framebuffer_new_dimensions() {
    let fb = LinearFramebuffer::new(1920, 1080, PixelFormat::Bgra8);
    assert_eq!(fb.width(), 1920);
    assert_eq!(fb.height(), 1080);
    assert_eq!(fb.stride(), 1920 * 4);
    assert_eq!(fb.pixel_bytes(), 1920 * 1080 * 4);
    assert_eq!(fb.format(), PixelFormat::Bgra8);
}

#[test]
fn test_framebuffer_clear_rgba() {
    let mut fb = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);
    fb.clear([0x11, 0x22, 0x33, 0xFF]);
    let px = fb.get_pixel(2, 3).unwrap();
    assert_eq!(px, [0x11, 0x22, 0x33, 0xFF]);
}

#[test]
fn test_framebuffer_clear_bgra() {
    let mut fb = LinearFramebuffer::new(4, 4, PixelFormat::Bgra8);
    fb.clear([0x11, 0x22, 0x33, 0xFF]);
    let px = fb.get_pixel(2, 3).unwrap();
    assert_eq!(px, [0x11, 0x22, 0x33, 0xFF]);
}

#[test]
fn test_framebuffer_set_get_pixel_roundtrip() {
    let mut fb = LinearFramebuffer::new(16, 16, PixelFormat::Bgra8);
    fb.set_pixel(5, 7, [200, 100, 50, 255]).unwrap();
    assert_eq!(fb.get_pixel(5, 7).unwrap(), [200, 100, 50, 255]);
}

#[test]
fn test_framebuffer_out_of_bounds() {
    let mut fb = LinearFramebuffer::new(8, 8, PixelFormat::Bgra8);
    assert!(fb.set_pixel(9, 0, [0, 0, 0, 255]).is_err());
    assert!(fb.set_pixel(0, 9, [0, 0, 0, 255]).is_err());
    assert!(fb.get_pixel(8, 8).is_err());
}

#[test]
fn test_framebuffer_fill_rect() {
    let mut fb = LinearFramebuffer::new(10, 10, PixelFormat::Rgba8);
    fb.fill_rect(2, 2, 4, 4, [0xFF, 0x00, 0x00, 0xFF]).unwrap();
    assert_eq!(fb.get_pixel(3, 3).unwrap(), [0xFF, 0x00, 0x00, 0xFF]);
    assert_eq!(fb.get_pixel(1, 1).unwrap(), [0, 0, 0, 0]);
    assert_eq!(fb.get_pixel(5, 5).unwrap(), [0xFF, 0x00, 0x00, 0xFF]);
    assert_eq!(fb.get_pixel(7, 7).unwrap(), [0, 0, 0, 0]);
}

#[test]
fn test_framebuffer_blit() {
    let mut src = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);
    src.fill_rect(0, 0, 4, 4, [0xAB, 0xCD, 0xEF, 0x12]).unwrap();

    let mut dst = LinearFramebuffer::new(8, 8, PixelFormat::Rgba8);
    dst.blit((2, 2), &src, (0, 0), (4, 4)).unwrap();

    assert_eq!(dst.get_pixel(2, 2).unwrap(), [0xAB, 0xCD, 0xEF, 0x12]);
    assert_eq!(dst.get_pixel(5, 5).unwrap(), [0xAB, 0xCD, 0xEF, 0x12]);
    assert_eq!(dst.get_pixel(1, 1).unwrap(), [0, 0, 0, 0]);
    assert_eq!(dst.get_pixel(6, 6).unwrap(), [0, 0, 0, 0]);
}

#[test]
fn test_framebuffer_blit_out_of_bounds() {
    let src = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);
    let mut dst = LinearFramebuffer::new(8, 8, PixelFormat::Rgba8);
    assert!(dst.blit((6, 6), &src, (0, 0), (4, 4)).is_err());
}

#[test]
fn test_dirty_tracking() {
    let mut fb = LinearFramebuffer::new(4, 4, PixelFormat::Rgba8);
    assert!(!fb.is_dirty());
    fb.set_pixel(0, 0, [1, 2, 3, 4]).unwrap();
    assert!(fb.is_dirty());
    let _ = fb.present();
    assert!(!fb.is_dirty());
}

#[test]
fn test_double_buffer_swap() {
    let mut db = DoubleBuffer::new(8, 8, PixelFormat::Rgba8);
    assert_eq!(db.width(), 8);
    assert_eq!(db.height(), 8);

    db.back_mut().clear([0xDE, 0xAD, 0xBE, 0xEF]);
    db.swap();
    assert_eq!(db.front().get_pixel(4, 4).unwrap(), [0xDE, 0xAD, 0xBE, 0xEF]);
    assert!(!db.back().is_dirty());
}

#[test]
fn test_from_raw_framebuffer() {
    let data = vec![0u8; 32 * 4];
    let fb = LinearFramebuffer::from_raw(8, 4, 8, PixelFormat::Bgra8, data);
    assert_eq!(fb.width(), 8);
    assert_eq!(fb.height(), 4);
    assert_eq!(fb.stride(), 8);
}
