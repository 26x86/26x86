//! Authored firmware layout, glyphs and navigation; no UEFI or OS dependency.
use alloc::{format, vec::Vec};
pub const MAX_PIXELS: usize = 4096 * 2160;
pub trait Pixel: Copy {
    fn rgb(red: u8, green: u8, blue: u8) -> Self;
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ViewError {
    Dimensions,
    Selection,
    Allocation,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Previous,
    Next,
    First,
    Last,
    Boot,
    Cancel,
    None,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Update {
    Redraw,
    Boot(usize),
    Cancel,
    Unchanged,
}
pub fn navigate(selected: &mut usize, count: usize, action: Action) -> Update {
    if count == 0 || *selected >= count {
        return Update::Cancel;
    }
    let old = *selected;
    match action {
        Action::Previous => *selected = if old == 0 { count - 1 } else { old - 1 },
        Action::Next => *selected = (old + 1) % count,
        Action::First => *selected = 0,
        Action::Last => *selected = count - 1,
        Action::Boot => return Update::Boot(old),
        Action::Cancel => return Update::Cancel,
        Action::None => {}
    }
    if *selected == old {
        Update::Unchanged
    } else {
        Update::Redraw
    }
}

const BG: u32 = 0x08090b;
const TILE: u32 = 0x16191e;
const LINE: u32 = 0x313741;
const WHITE: u32 = 0xf3f5f7;
const MUTED: u32 = 0x969fae;
const ACCENT: u32 = 0xb9edce;
struct Canvas<P> {
    pixels: Vec<P>,
    width: usize,
    height: usize,
}
impl<P: Pixel> Canvas<P> {
    fn color(value: u32) -> P {
        P::rgb((value >> 16) as u8, (value >> 8) as u8, value as u8)
    }
    fn rect(&mut self, x: usize, y: usize, w: usize, h: usize, color: u32) {
        let right = x.saturating_add(w).min(self.width);
        let bottom = y.saturating_add(h).min(self.height);
        if x >= right || y >= bottom {
            return;
        }
        for row in y..bottom {
            self.pixels[row * self.width + x..row * self.width + right].fill(Self::color(color));
        }
    }
    fn rounded(&mut self, x: usize, y: usize, w: usize, h: usize, r: usize, color: u32) {
        for dy in 0..h {
            let edge = if dy < r {
                r - dy - 1
            } else if dy >= h - r {
                dy - (h - r)
            } else {
                0
            };
            let mut inset = 0;
            while inset < r && (r - inset) * (r - inset) + edge * edge > r * r {
                inset += 1;
            }
            self.rect(x + inset, y + dy, w.saturating_sub(2 * inset), 1, color);
        }
    }
    fn text(&mut self, x: usize, y: usize, text: &str, scale: usize, color: u32, max_chars: usize) {
        let truncated = text.chars().count() > max_chars;
        for (index, ch) in text.chars().take(max_chars).enumerate() {
            let ch = if truncated && index >= max_chars.saturating_sub(3) {
                '.'
            } else {
                ch
            };
            let rows = glyph(ch);
            for (row, bits) in rows.into_iter().enumerate() {
                for col in 0..5 {
                    if bits & (1 << (4 - col)) != 0 {
                        self.rect(
                            x + index * 6 * scale + col * scale,
                            y + row * scale,
                            scale,
                            scale,
                            color,
                        );
                    }
                }
            }
        }
    }
    fn centered(
        &mut self,
        center: usize,
        y: usize,
        text: &str,
        scale: usize,
        color: u32,
        max_chars: usize,
    ) {
        let chars = text.chars().count().min(max_chars);
        let width = chars.saturating_mul(6 * scale).saturating_sub(scale);
        self.text(
            center.saturating_sub(width / 2),
            y,
            text,
            scale,
            color,
            max_chars,
        );
    }
}

pub fn render<P: Pixel>(
    width: usize,
    height: usize,
    names: &[&str],
    volume: &str,
    selected: usize,
    starting: bool,
) -> Result<Vec<P>, ViewError> {
    let size = width.checked_mul(height).ok_or(ViewError::Dimensions)?;
    if width < 640 || height < 480 || width > 4096 || height > 2160 || size > MAX_PIXELS {
        return Err(ViewError::Dimensions);
    }
    if names.is_empty() || names.len() > 64 || selected >= names.len() {
        return Err(ViewError::Selection);
    }
    let mut pixels = Vec::new();
    pixels
        .try_reserve_exact(size)
        .map_err(|_| ViewError::Allocation)?;
    pixels.resize(size, Canvas::<P>::color(BG));
    let mut c = Canvas {
        pixels,
        width,
        height,
    };
    let pad = if width >= 900 { 56 } else { 32 };
    c.rounded(pad, 32, 30, 30, 8, ACCENT);
    c.text(pad + 8, 40, "N", 2, BG, 1);
    c.text(pad + 44, 39, "NextCore", 3, WHITE, 8);
    c.text(pad + 45, 69, "BOOT MANAGER", 1, MUTED, 20);
    c.rect(pad, 100, width - pad * 2, 1, LINE);
    let title_y = if height >= 600 { 142 } else { 123 };
    c.centered(
        width / 2,
        title_y,
        if starting {
            "Starting selected system"
        } else {
            "Choose your system"
        },
        if width >= 900 { 3 } else { 2 },
        WHITE,
        35,
    );
    c.centered(
        width / 2,
        title_y + 34,
        "Your next session starts here",
        1,
        MUTED,
        40,
    );
    let visible = if width >= 1080 {
        3
    } else if width >= 740 {
        2
    } else {
        1
    };
    let visible = visible.min(names.len());
    let gap = 20;
    let tile_w = ((width - pad * 2 - gap * (visible - 1)) / visible).min(280);
    let tile_h = if height >= 600 { 236 } else { 164 };
    let tile_y = if height >= 600 {
        (height - tile_h) / 2 + 32
    } else {
        185
    };
    let all_w = visible * tile_w + (visible - 1) * gap;
    let start_x = (width - all_w) / 2;
    let first = selected
        .saturating_sub(visible / 2)
        .min(names.len() - visible);
    for slot in 0..visible {
        let index = first + slot;
        let x = start_x + slot * (tile_w + gap);
        let active = index == selected;
        c.rounded(
            x,
            tile_y,
            tile_w,
            tile_h,
            14,
            if active { ACCENT } else { LINE },
        );
        c.rounded(
            x + 2,
            tile_y + 2,
            tile_w - 4,
            tile_h - 4,
            12,
            if active { 0x1c2723 } else { TILE },
        );
        if active {
            c.text(
                x + 18,
                tile_y + 18,
                if starting { "STARTING" } else { "SELECTED" },
                1,
                ACCENT,
                12,
            );
        }
        let center = x + tile_w / 2;
        let icon_y = tile_y + if tile_h > 180 { 61 } else { 42 };
        // A neutral authored volume icon; no OS logo or unsupported badge.
        c.rounded(
            center - 30,
            icon_y,
            60,
            43,
            7,
            if active { 0x476458 } else { 0x353c46 },
        );
        c.rect(
            center - 20,
            icon_y + 11,
            40,
            2,
            if active { ACCENT } else { MUTED },
        );
        c.rect(
            center + 14,
            icon_y + 30,
            6,
            3,
            if active { ACCENT } else { MUTED },
        );
        let label_y = icon_y + if tile_h > 180 { 66 } else { 57 };
        c.centered(center, label_y, names[index], 2, WHITE, (tile_w - 28) / 12);
        c.centered(center, label_y + 27, volume, 1, MUTED, (tile_w - 28) / 6);
        c.centered(
            center,
            tile_y + tile_h - 22,
            &format!("{:02} / {:02}", index + 1, names.len()),
            1,
            if active { ACCENT } else { MUTED },
            12,
        );
    }
    let footer = height - 46;
    c.rect(pad, footer - 20, width - pad * 2, 1, LINE);
    c.text(pad, footer, "ARROWS / TAB  Choose", 1, MUTED, 24);
    c.centered(width / 2, footer, "ENTER  Boot", 1, ACCENT, 14);
    let esc = "ESC  Cancel";
    c.text(width - pad - esc.len() * 6, footer, esc, 1, MUTED, 14);
    Ok(c.pixels)
}

// Independently authored 5x7 bitmap alphabet. Unsupported Unicode is explicit
// '?' fallback; no control code can write outside the fixed glyph rectangle.
fn glyph(ch: char) -> [u8; 7] {
    match ch {
        'a' => [0, 0, 14, 1, 15, 17, 15],
        'b' => [16, 16, 22, 25, 17, 17, 30],
        'c' => [0, 0, 14, 17, 16, 17, 14],
        'd' => [1, 1, 13, 19, 17, 17, 15],
        'e' => [0, 0, 14, 17, 31, 16, 14],
        'f' => [6, 9, 8, 28, 8, 8, 8],
        'g' => [0, 0, 15, 17, 15, 1, 14],
        'h' => [16, 16, 22, 25, 17, 17, 17],
        'i' => [4, 0, 12, 4, 4, 4, 14],
        'j' => [2, 0, 6, 2, 2, 18, 12],
        'k' => [16, 16, 18, 20, 24, 20, 18],
        'l' => [12, 4, 4, 4, 4, 4, 14],
        'm' => [0, 0, 26, 21, 21, 17, 17],
        'n' => [0, 0, 22, 25, 17, 17, 17],
        'o' => [0, 0, 14, 17, 17, 17, 14],
        'p' => [0, 0, 30, 17, 30, 16, 16],
        'q' => [0, 0, 15, 17, 15, 1, 1],
        'r' => [0, 0, 22, 25, 16, 16, 16],
        's' => [0, 0, 15, 16, 14, 1, 30],
        't' => [8, 8, 28, 8, 8, 9, 6],
        'u' => [0, 0, 17, 17, 17, 19, 13],
        'v' => [0, 0, 17, 17, 17, 10, 4],
        'w' => [0, 0, 17, 17, 21, 21, 10],
        'x' => [0, 0, 17, 10, 4, 10, 17],
        'y' => [0, 0, 17, 17, 15, 1, 14],
        'z' => [0, 0, 31, 2, 4, 8, 31],
        'A' => [14, 17, 17, 31, 17, 17, 17],
        'B' => [30, 17, 17, 30, 17, 17, 30],
        'C' => [14, 17, 16, 16, 16, 17, 14],
        'D' => [30, 17, 17, 17, 17, 17, 30],
        'E' => [31, 16, 16, 30, 16, 16, 31],
        'F' => [31, 16, 16, 30, 16, 16, 16],
        'G' => [14, 17, 16, 23, 17, 17, 15],
        'H' => [17, 17, 17, 31, 17, 17, 17],
        'I' => [14, 4, 4, 4, 4, 4, 14],
        'J' => [7, 2, 2, 2, 2, 18, 12],
        'K' => [17, 18, 20, 24, 20, 18, 17],
        'L' => [16, 16, 16, 16, 16, 16, 31],
        'M' => [17, 27, 21, 21, 17, 17, 17],
        'N' => [17, 25, 25, 21, 19, 19, 17],
        'O' => [14, 17, 17, 17, 17, 17, 14],
        'P' => [30, 17, 17, 30, 16, 16, 16],
        'Q' => [14, 17, 17, 17, 21, 18, 13],
        'R' => [30, 17, 17, 30, 20, 18, 17],
        'S' => [15, 16, 16, 14, 1, 1, 30],
        'T' => [31, 4, 4, 4, 4, 4, 4],
        'U' => [17, 17, 17, 17, 17, 17, 14],
        'V' => [17, 17, 17, 17, 17, 10, 4],
        'W' => [17, 17, 17, 21, 21, 21, 10],
        'X' => [17, 17, 10, 4, 10, 17, 17],
        'Y' => [17, 17, 10, 4, 4, 4, 4],
        'Z' => [31, 1, 2, 4, 8, 16, 31],
        '0' => [14, 17, 19, 21, 25, 17, 14],
        '1' => [4, 12, 4, 4, 4, 4, 14],
        '2' => [14, 17, 1, 2, 4, 8, 31],
        '3' => [30, 1, 1, 14, 1, 1, 30],
        '4' => [2, 6, 10, 18, 31, 2, 2],
        '5' => [31, 16, 16, 30, 1, 1, 30],
        '6' => [14, 16, 16, 30, 17, 17, 14],
        '7' => [31, 1, 2, 4, 8, 8, 8],
        '8' => [14, 17, 17, 14, 17, 17, 14],
        '9' => [14, 17, 17, 15, 1, 1, 14],
        ' ' => [0; 7],
        '.' => [0, 0, 0, 0, 0, 6, 6],
        '-' => [0, 0, 0, 31, 0, 0, 0],
        '_' => [0, 0, 0, 0, 0, 0, 31],
        '/' => [1, 2, 2, 4, 8, 8, 16],
        '(' => [2, 4, 8, 8, 8, 4, 2],
        ')' => [8, 4, 2, 2, 2, 4, 8],
        ':' => [0, 6, 6, 0, 6, 6, 0],
        _ => [14, 17, 1, 2, 4, 0, 4],
    }
}
