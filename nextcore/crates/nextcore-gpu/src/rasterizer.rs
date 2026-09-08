use crate::framebuffer::{FramebufferError, LinearFramebuffer, PixelFormat};

use thiserror::Error;

#[derive(Debug, Error)]
pub enum RasterError {
    #[error("framebuffer error: {0}")]
    Framebuffer(#[from] FramebufferError),
    #[error("degenerate triangle")]
    DegenerateTriangle,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Vec2 {
    pub x: f32,
    pub y: f32,
}

impl Vec2 {
    pub fn new(x: f32, y: f32) -> Self {
        Self { x, y }
    }

    pub fn cross(self, other: Self) -> f32 {
        self.x * other.y - self.y * other.x
    }

    pub fn delta(self, other: Self) -> Self {
        Self {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Vec3 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

impl Vec3 {
    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
    }

    pub fn delta(self, other: Self) -> Self {
        Self {
            x: self.x - other.x,
            y: self.y - other.y,
            z: self.z - other.z,
        }
    }

    pub fn cross(self, other: Self) -> Self {
        Self {
            x: self.y * other.z - self.z * other.y,
            y: self.z * other.x - self.x * other.z,
            z: self.x * other.y - self.y * other.x,
        }
    }

    pub fn dot(self, other: Self) -> f32 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Vec4 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub w: f32,
}

impl Vec4 {
    pub fn new(x: f32, y: f32, z: f32, w: f32) -> Self {
        Self { x, y, z, w }
    }

    pub fn perspective_divide(self) -> Vec3 {
        let inv_w = 1.0 / self.w;
        Vec3::new(self.x * inv_w, self.y * inv_w, self.z * inv_w)
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Color {
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub a: f32,
}

impl Color {
    pub fn new(r: f32, g: f32, b: f32, a: f32) -> Self {
        Self { r, g, b, a }
    }

    pub fn white() -> Self {
        Self::new(1.0, 1.0, 1.0, 1.0)
    }

    pub fn black() -> Self {
        Self::new(0.0, 0.0, 0.0, 1.0)
    }

    pub fn red() -> Self {
        Self::new(1.0, 0.0, 0.0, 1.0)
    }

    pub fn green() -> Self {
        Self::new(0.0, 1.0, 0.0, 1.0)
    }

    pub fn blue() -> Self {
        Self::new(0.0, 0.0, 1.0, 1.0)
    }

    pub fn to_bytes_rgba(self) -> [u8; 4] {
        [
            (self.r.clamp(0.0, 1.0) * 255.0) as u8,
            (self.g.clamp(0.0, 1.0) * 255.0) as u8,
            (self.b.clamp(0.0, 1.0) * 255.0) as u8,
            (self.a.clamp(0.0, 1.0) * 255.0) as u8,
        ]
    }

    pub fn to_bytes_bgra(self) -> [u8; 4] {
        [
            (self.b.clamp(0.0, 1.0) * 255.0) as u8,
            (self.g.clamp(0.0, 1.0) * 255.0) as u8,
            (self.r.clamp(0.0, 1.0) * 255.0) as u8,
            (self.a.clamp(0.0, 1.0) * 255.0) as u8,
        ]
    }

    pub fn lerp(self, other: Self, t: f32) -> Self {
        Self {
            r: self.r + (other.r - self.r) * t,
            g: self.g + (other.g - self.g) * t,
            b: self.b + (other.b - self.b) * t,
            a: self.a + (other.a - self.a) * t,
        }
    }

    pub fn alpha_blend(self, src: Self) -> Self {
        let inv_a = 1.0 - src.a;
        Self {
            r: src.r * src.a + self.r * inv_a,
            g: src.g * src.a + self.g * inv_a,
            b: src.b * src.a + self.b * inv_a,
            a: src.a * src.a + self.a * inv_a,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Vertex {
    pub position: Vec4,
    pub color: Color,
    pub tex_coord: Vec2,
    pub normal: Vec3,
}

impl Vertex {
    pub fn new(position: Vec4, color: Color) -> Self {
        Self {
            position,
            color,
            tex_coord: Vec2::new(0.0, 0.0),
            normal: Vec3::new(0.0, 0.0, 1.0),
        }
    }

    pub fn with_tex_coord(mut self, u: f32, v: f32) -> Self {
        self.tex_coord = Vec2::new(u, v);
        self
    }

    pub fn with_normal(mut self, nx: f32, ny: f32, nz: f32) -> Self {
        self.normal = Vec3::new(nx, ny, nz);
        self
    }
}

pub struct SoftwareRasterizer {
    depth_buffer: Vec<f32>,
    depth_width: u32,
    depth_height: u32,
}

impl SoftwareRasterizer {
    pub fn new() -> Self {
        Self {
            depth_buffer: Vec::new(),
            depth_width: 0,
            depth_height: 0,
        }
    }

    pub fn resize_depth_buffer(&mut self, width: u32, height: u32) {
        self.depth_width = width;
        self.depth_height = height;
        self.depth_buffer = vec![1.0; (width * height) as usize];
    }

    pub fn clear_depth_buffer(&mut self) {
        self.depth_buffer.iter_mut().for_each(|d| *d = 1.0);
    }

    fn get_depth(&self, x: u32, y: u32) -> f32 {
        if x < self.depth_width && y < self.depth_height {
            self.depth_buffer[(y * self.depth_width + x) as usize]
        } else {
            1.0
        }
    }

    fn set_depth(&mut self, x: u32, y: u32, depth: f32) {
        if x < self.depth_width && y < self.depth_height {
            let idx = (y * self.depth_width + x) as usize;
            self.depth_buffer[idx] = depth;
        }
    }

    fn edge_function(a: Vec2, b: Vec2, c: Vec2) -> f32 {
        (c.x - a.x) * (b.y - a.y) - (c.y - a.y) * (b.x - a.x)
    }

    fn barycentric_coordinates(p: Vec2, a: Vec2, b: Vec2, c: Vec2) -> Option<(f32, f32, f32)> {
        let area = Self::edge_function(a, b, c);
        if area.abs() < f32::EPSILON {
            return None;
        }
        let inv_area = 1.0 / area;
        let w_a = Self::edge_function(b, c, p) * inv_area;
        let w_b = Self::edge_function(c, a, p) * inv_area;
        let w_c = 1.0 - w_a - w_b;
        Some((w_a, w_b, w_c))
    }

    fn ndc_to_screen(v: &Vertex, width: f32, height: f32) -> (Vec2, Vec3, Color) {
        let ndc = v.position.perspective_divide();
        let sx = (ndc.x * 0.5 + 0.5) * width;
        let sy = (ndc.y * -0.5 + 0.5) * height;
        (
            Vec2::new(sx, sy),
            Vec3::new(sx, sy, ndc.z),
            v.color,
        )
    }

    pub fn rasterize_triangle(
        &mut self,
        fb: &mut LinearFramebuffer,
        v0: Vertex,
        v1: Vertex,
        v2: Vertex,
        depth_test: bool,
    ) -> Result<(), RasterError> {
        let width = fb.width() as f32;
        let height = fb.height() as f32;

        let (s0, _d0, _c0) = Self::ndc_to_screen(&v0, width, height);
        let (s1, _d1, _c1) = Self::ndc_to_screen(&v1, width, height);
        let (s2, _d2, _c2) = Self::ndc_to_screen(&v2, width, height);
        let (p0, p1, p2) = (s0, s1, s2);

        let min_x = p0.x.min(p1.x).min(p2.x).max(0.0) as u32;
        let max_x = (p0.x.max(p1.x).max(p2.x).min(width - 1.0) + 1.0) as u32;
        let min_y = p0.y.min(p1.y).min(p2.y).max(0.0) as u32;
        let max_y = (p0.y.max(p1.y).max(p2.y).min(height - 1.0) + 1.0) as u32;

        for y in min_y..max_y {
            for x in min_x..max_x {
                let p = Vec2::new(x as f32 + 0.5, y as f32 + 0.5);
                if let Some((w0, w1, w2)) = Self::barycentric_coordinates(p, p0, p1, p2) {
                    if w0 >= 0.0 && w1 >= 0.0 && w2 >= 0.0 {
                        let depth = w0 * v0.position.z + w1 * v1.position.z + w2 * v2.position.z;

                        if depth_test && depth >= 1.0 {
                            continue;
                        }
                        if depth_test {
                            let current = self.get_depth(x, y);
                            if depth >= current {
                                continue;
                            }
                            self.set_depth(x, y, depth);
                        }

                        let color = Color::new(
                            w0 * v0.color.r + w1 * v1.color.r + w2 * v2.color.r,
                            w0 * v0.color.g + w1 * v1.color.g + w2 * v2.color.g,
                            w0 * v0.color.b + w1 * v1.color.b + w2 * v2.color.b,
                            w0 * v0.color.a + w1 * v1.color.a + w2 * v2.color.a,
                        );

                        let bytes = match fb.format() {
                            PixelFormat::Rgba8 => color.to_bytes_rgba(),
                            _ => color.to_bytes_bgra(),
                        };
                        fb.set_pixel(x, y, bytes)?;
                    }
                }
            }
        }
        Ok(())
    }

    pub fn rasterize_triangle_list(
        &mut self,
        fb: &mut LinearFramebuffer,
        vertices: &[Vertex],
        depth_test: bool,
    ) -> Result<(), RasterError> {
        if !vertices.len().is_multiple_of(3) {
            return Err(RasterError::DegenerateTriangle);
        }
        for chunk in vertices.chunks(3) {
            self.rasterize_triangle(fb, chunk[0], chunk[1], chunk[2], depth_test)?;
        }
        Ok(())
    }

    pub fn rasterize_line(
        fb: &mut LinearFramebuffer,
        v0: Vertex,
        v1: Vertex,
        thickness: f32,
    ) -> Result<(), RasterError> {
        let width = fb.width() as f32;
        let height = fb.height() as f32;
        let (p0, _, _) = Self::ndc_to_screen(&v0, width, height);
        let (p1, _, _) = Self::ndc_to_screen(&v1, width, height);

        let x0 = p0.x as i32;
        let y0 = p0.y as i32;
        let x1 = p1.x as i32;
        let y1 = p1.y as i32;

        let dx = (x1 - x0).abs();
        let dy = -(y1 - y0).abs();
        let sx = if x0 < x1 { 1 } else { -1 };
        let sy = if y0 < y1 { 1 } else { -1 };
        let mut err = dx + dy;

        let mut cx = x0;
        let mut cy = y0;
        let _half = (thickness / 2.0) as i32;

        loop {
            if cx >= 0 && cy >= 0 && (cx as u32) < fb.width() && (cy as u32) < fb.height() {
                let t = if dx + dy != 0 {
                    ((cx - x0) as f32 / (x1 - x0).max(1) as f32)
                        .max((cy - y0) as f32 / (y1 - y0).max(1) as f32)
                } else {
                    0.0
                };
                let color = v0.color.lerp(v1.color, t.clamp(0.0, 1.0));
                let bytes = match fb.format() {
                    PixelFormat::Rgba8 => color.to_bytes_rgba(),
                    _ => color.to_bytes_bgra(),
                };
                let _ = fb.set_pixel(cx as u32, cy as u32, bytes);
            }

            if cx == x1 && cy == y1 {
                break;
            }

            let e2 = 2 * err;
            if e2 >= dy {
                err += dy;
                cx += sx;
            }
            if e2 <= dx {
                err += dx;
                cy += sy;
            }
        }
        Ok(())
    }
}

impl Default for SoftwareRasterizer {
    fn default() -> Self {
        Self::new()
    }
}

pub fn blend_normal(src: Color, dst: Color) -> Color {
    let inv_a = 1.0 - src.a;
    Color {
        r: src.r * src.a + dst.r * inv_a,
        g: src.g * src.a + dst.g * inv_a,
        b: src.b * src.a + dst.b * inv_a,
        a: 1.0,
    }
}

pub fn blend_add(src: Color, dst: Color) -> Color {
    Color {
        r: (src.r * src.a + dst.r).min(1.0),
        g: (src.g * src.a + dst.g).min(1.0),
        b: (src.b * src.a + dst.b).min(1.0),
        a: 1.0,
    }
}

pub fn blend_multiply(src: Color, dst: Color) -> Color {
    Color {
        r: src.r * dst.r,
        g: src.g * dst.g,
        b: src.b * dst.b,
        a: src.a * dst.a,
    }
}
