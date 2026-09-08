use std::sync::atomic::{AtomicBool, Ordering};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum FramebufferError {
    #[error("invalid pixel format")]
    InvalidPixelFormat,
    #[error("out of bounds: pixel ({x}, {y}) outside {width}x{height}")]
    OutOfBounds { x: u32, y: u32, width: u32, height: u32 },
    #[error("buffer too small: need {needed}, got {available}")]
    BufferTooSmall { needed: usize, available: usize },
    #[error("blit dimensions mismatch")]
    BlitDimensionsMismatch,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PixelFormat {
    Bgra8,
    Rgba8,
    Bgrx8,
}

impl PixelFormat {
    pub fn bytes_per_pixel(&self) -> usize {
        match self {
            PixelFormat::Bgra8 | PixelFormat::Rgba8 | PixelFormat::Bgrx8 => 4,
        }
    }

    pub fn channels(&self) -> usize {
        4
    }
}

#[derive(Debug)]
pub struct LinearFramebuffer {
    width: u32,
    height: u32,
    stride: u32,
    format: PixelFormat,
    pixels: Vec<u8>,
    dirty: AtomicBool,
}

impl LinearFramebuffer {
    pub fn new(width: u32, height: u32, format: PixelFormat) -> Self {
        let stride = width * format.bytes_per_pixel() as u32;
        let total = stride as usize * height as usize;
        Self {
            width,
            height,
            stride,
            format,
            pixels: vec![0u8; total],
            dirty: AtomicBool::new(false),
        }
    }

    pub fn from_raw(width: u32, height: u32, stride: u32, format: PixelFormat, data: Vec<u8>) -> Self {
        Self {
            width,
            height,
            stride,
            format,
            pixels: data,
            dirty: AtomicBool::new(false),
        }
    }

    pub fn width(&self) -> u32 {
        self.width
    }

    pub fn height(&self) -> u32 {
        self.height
    }

    pub fn stride(&self) -> u32 {
        self.stride
    }

    pub fn format(&self) -> PixelFormat {
        self.format
    }

    pub fn pixel_bytes(&self) -> usize {
        self.stride as usize * self.height as usize
    }

    pub fn pixels(&self) -> &[u8] {
        &self.pixels
    }

    pub fn pixels_mut(&mut self) -> &mut [u8] {
        self.dirty.store(true, Ordering::Relaxed);
        &mut self.pixels
    }

    pub fn is_dirty(&self) -> bool {
        self.dirty.load(Ordering::Relaxed)
    }

    pub fn clear_dirty(&self) {
        self.dirty.store(false, Ordering::Relaxed);
    }

    pub fn clear(&mut self, color: [u8; 4]) {
        let bpp = self.format.bytes_per_pixel();
        for y in 0..self.height {
            let row_start = (y * self.stride) as usize;
            for x in 0..self.width {
                let offset = row_start + x as usize * bpp;
                match self.format {
                    PixelFormat::Bgra8 | PixelFormat::Bgrx8 => {
                        self.pixels[offset] = color[2];
                        self.pixels[offset + 1] = color[1];
                        self.pixels[offset + 2] = color[0];
                        self.pixels[offset + 3] = color[3];
                    }
                    PixelFormat::Rgba8 => {
                        self.pixels[offset] = color[0];
                        self.pixels[offset + 1] = color[1];
                        self.pixels[offset + 2] = color[2];
                        self.pixels[offset + 3] = color[3];
                    }
                }
            }
        }
        self.dirty.store(true, Ordering::Relaxed);
    }

    pub fn set_pixel(&mut self, x: u32, y: u32, color: [u8; 4]) -> Result<(), FramebufferError> {
        if x >= self.width || y >= self.height {
            return Err(FramebufferError::OutOfBounds {
                x,
                y,
                width: self.width,
                height: self.height,
            });
        }
        let bpp = self.format.bytes_per_pixel();
        let offset = (y * self.stride + x * bpp as u32) as usize;
        match self.format {
            PixelFormat::Bgra8 | PixelFormat::Bgrx8 => {
                self.pixels[offset] = color[2];
                self.pixels[offset + 1] = color[1];
                self.pixels[offset + 2] = color[0];
                self.pixels[offset + 3] = color[3];
            }
            PixelFormat::Rgba8 => {
                self.pixels[offset] = color[0];
                self.pixels[offset + 1] = color[1];
                self.pixels[offset + 2] = color[2];
                self.pixels[offset + 3] = color[3];
            }
        }
        self.dirty.store(true, Ordering::Relaxed);
        Ok(())
    }

    pub fn get_pixel(&self, x: u32, y: u32) -> Result<[u8; 4], FramebufferError> {
        if x >= self.width || y >= self.height {
            return Err(FramebufferError::OutOfBounds {
                x,
                y,
                width: self.width,
                height: self.height,
            });
        }
        let bpp = self.format.bytes_per_pixel();
        let offset = (y * self.stride + x * bpp as u32) as usize;
        Ok(match self.format {
            PixelFormat::Bgra8 | PixelFormat::Bgrx8 => {
                [self.pixels[offset + 2], self.pixels[offset + 1], self.pixels[offset], self.pixels[offset + 3]]
            }
            PixelFormat::Rgba8 => {
                [self.pixels[offset], self.pixels[offset + 1], self.pixels[offset + 2], self.pixels[offset + 3]]
            }
        })
    }

    pub fn blit(
        &mut self,
        dst: (u32, u32),
        src: &LinearFramebuffer,
        src_origin: (u32, u32),
        region: (u32, u32),
    ) -> Result<(), FramebufferError> {
        let (dst_x, dst_y) = dst;
        let (src_x, src_y) = src_origin;
        let (blit_width, blit_height) = region;
        if src.format != self.format {
            return Err(FramebufferError::BlitDimensionsMismatch);
        }
        if dst_x + blit_width > self.width || dst_y + blit_height > self.height {
            return Err(FramebufferError::OutOfBounds {
                x: dst_x + blit_width,
                y: dst_y + blit_height,
                width: self.width,
                height: self.height,
            });
        }
        if src_x + blit_width > src.width || src_y + blit_height > src.height {
            return Err(FramebufferError::OutOfBounds {
                x: src_x + blit_width,
                y: src_y + blit_height,
                width: src.width,
                height: src.height,
            });
        }
        let bpp = self.format.bytes_per_pixel();
        for row in 0..blit_height {
            let src_offset = ((src_y + row) * src.stride + src_x * bpp as u32) as usize;
            let dst_offset = ((dst_y + row) * self.stride + dst_x * bpp as u32) as usize;
            let row_bytes = blit_width as usize * bpp;
            self.pixels[dst_offset..dst_offset + row_bytes]
                .copy_from_slice(&src.pixels[src_offset..src_offset + row_bytes]);
        }
        self.dirty.store(true, Ordering::Relaxed);
        Ok(())
    }

    pub fn fill_rect(
        &mut self,
        x: u32,
        y: u32,
        w: u32,
        h: u32,
        color: [u8; 4],
    ) -> Result<(), FramebufferError> {
        if x + w > self.width || y + h > self.height {
            return Err(FramebufferError::OutOfBounds {
                x: x + w,
                y: y + h,
                width: self.width,
                height: self.height,
            });
        }
        let bpp = self.format.bytes_per_pixel();
        for row in y..y + h {
            let row_start = (row * self.stride + x * bpp as u32) as usize;
            for col in 0..w {
                let offset = row_start + col as usize * bpp;
                match self.format {
                    PixelFormat::Bgra8 | PixelFormat::Bgrx8 => {
                        self.pixels[offset] = color[2];
                        self.pixels[offset + 1] = color[1];
                        self.pixels[offset + 2] = color[0];
                        self.pixels[offset + 3] = color[3];
                    }
                    PixelFormat::Rgba8 => {
                        self.pixels[offset] = color[0];
                        self.pixels[offset + 1] = color[1];
                        self.pixels[offset + 2] = color[2];
                        self.pixels[offset + 3] = color[3];
                    }
                }
            }
        }
        self.dirty.store(true, Ordering::Relaxed);
        Ok(())
    }

    pub fn present(&self) -> &[u8] {
        self.clear_dirty();
        &self.pixels
    }
}

impl Clone for LinearFramebuffer {
    fn clone(&self) -> Self {
        Self {
            width: self.width,
            height: self.height,
            stride: self.stride,
            format: self.format,
            pixels: self.pixels.clone(),
            dirty: AtomicBool::new(self.dirty.load(Ordering::Relaxed)),
        }
    }
}

#[derive(Debug, Clone)]
pub struct DoubleBuffer {
    front: LinearFramebuffer,
    back: LinearFramebuffer,
}

impl DoubleBuffer {
    pub fn new(width: u32, height: u32, format: PixelFormat) -> Self {
        Self {
            front: LinearFramebuffer::new(width, height, format),
            back: LinearFramebuffer::new(width, height, format),
        }
    }

    pub fn front(&self) -> &LinearFramebuffer {
        &self.front
    }

    pub fn back(&self) -> &LinearFramebuffer {
        &self.back
    }

    pub fn back_mut(&mut self) -> &mut LinearFramebuffer {
        &mut self.back
    }

    pub fn swap(&mut self) {
        std::mem::swap(&mut self.front, &mut self.back);
        self.back.clear_dirty();
    }

    pub fn width(&self) -> u32 {
        self.front.width()
    }

    pub fn height(&self) -> u32 {
        self.front.height()
    }

    pub fn format(&self) -> PixelFormat {
        self.front.format()
    }
}
