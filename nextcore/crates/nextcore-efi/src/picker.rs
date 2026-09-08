//! NextCore's public UEFI GOP / Simple Text Input boot menu.
//! Returns a selection only; the caller owns LoadImage and StartImage.
use alloc::{format, string::String, vec::Vec};
use core::fmt::Write;
use nextcore_core::boot_config::BootMenuEntry;
use nextcore_core::boot_picker as view;
use uefi::proto::console::{
    gop::{BltOp, BltPixel, BltRegion, GraphicsOutput},
    serial::Serial,
    text::{Color, Key, ScanCode},
};
use uefi::proto::media::file::{File, FileSystemInfo};
use uefi::{boot, char16, system, Status};
use view::{Action, Update};

#[repr(transparent)]
#[derive(Clone, Copy)]
struct Pixel(BltPixel);
impl view::Pixel for Pixel {
    fn rgb(red: u8, green: u8, blue: u8) -> Self {
        Self(BltPixel::new(red, green, blue))
    }
}

struct Cursor(bool);
impl Drop for Cursor {
    fn drop(&mut self) {
        system::with_stdout(|out| {
            let _ = out.enable_cursor(self.0);
        });
    }
}

/// All buffers and protocol guards are released before returning a target.
pub fn choose(entries: &[BootMenuEntry], report: fn(&str)) -> Result<Option<usize>, Status> {
    if entries.is_empty() || entries.len() > 64 {
        return Err(Status::INVALID_PARAMETER);
    }
    report(&format!("NEXTCORE: PICKER_BEGIN entries={}", entries.len()));
    let _cursor = Cursor(system::with_stdout(|out| {
        let previous = out.cursor_visible();
        let _ = out.enable_cursor(false);
        previous
    }));
    // A bounded display copy keeps control characters and unbounded caller-owned
    // names out of both the text console and independently authored bitmap font.
    let names: Vec<String> = entries
        .iter()
        .map(|entry| display(&entry.name, 64))
        .collect();
    let names: Vec<&str> = names.iter().map(String::as_str).collect();
    let volume = volume_label();
    let mut graphics = boot::get_handle_for_protocol::<GraphicsOutput>()
        .ok()
        .and_then(|handle| boot::open_protocol_exclusive::<GraphicsOutput>(handle).ok());
    let mut selected = 0;
    let mut redraw = true;
    loop {
        if redraw {
            let rendered = graphics
                .as_mut()
                .is_some_and(|gop| draw(gop, &names, &volume, selected, false).is_ok());
            if !rendered {
                // Release GOP before using the firmware's text console.
                graphics = None;
                draw_text(&names, &volume, selected, false)?;
            }
            serial(&format!(
                "NEXTCORE: PICKER_READY renderer={} selected={selected}",
                if rendered { "GOP" } else { "TEXT" }
            ));
        }
        let action = read_action()?;
        redraw = false;
        match view::navigate(&mut selected, names.len(), action) {
            Update::Redraw => redraw = true,
            Update::Boot(index) => {
                if let Some(gop) = graphics.as_mut() {
                    let _ = draw(gop, &names, &volume, index, true);
                } else {
                    draw_text(&names, &volume, index, true)?;
                }
                serial(&format!("NEXTCORE: PICKER_BOOT index={index}"));
                return Ok(Some(index));
            }
            Update::Cancel => {
                serial("NEXTCORE: PICKER_CANCEL");
                drop(graphics);
                system::with_stdout(|out| {
                    let _ = out.clear();
                });
                return Ok(None);
            }
            Update::Unchanged => {}
        }
    }
}

fn display(value: &str, cap: usize) -> String {
    value
        .chars()
        .take(cap)
        .map(|ch| {
            if ch.is_ascii() && !ch.is_control() {
                ch
            } else {
                '?'
            }
        })
        .collect()
}

fn volume_label() -> String {
    let label = (|| {
        let mut fs = boot::get_image_file_system(boot::image_handle()).ok()?;
        let mut root = fs.open_volume().ok()?;
        // FileSystemInfo is 8-byte aligned. A fixed buffer avoids allocating
        // the length claimed by firmware or a malformed media label.
        let mut storage = [0u64; 512];
        let buffer = unsafe {
            core::slice::from_raw_parts_mut(
                storage.as_mut_ptr().cast::<u8>(),
                core::mem::size_of_val(&storage),
            )
        };
        let info = root.get_info::<FileSystemInfo>(buffer).ok()?;
        let label = display(&format!("{}", info.volume_label()), 32);
        if label.trim().is_empty() {
            None
        } else {
            Some(label)
        }
    })();
    label.unwrap_or_else(|| String::from("Current EFI volume"))
}

fn draw(
    gop: &mut GraphicsOutput,
    names: &[&str],
    volume: &str,
    selected: usize,
    starting: bool,
) -> Result<(), Status> {
    let (width, height) = gop.current_mode_info().resolution();
    let pixels = view::render::<Pixel>(width, height, names, volume, selected, starting)
        .map_err(|_| Status::UNSUPPORTED)?;
    gop.blt(BltOp::BufferToVideo {
        // SAFETY: Pixel is transparent over BltPixel, with identical alignment,
        // size and initialized value. This borrow cannot outlive the owned Vec.
        buffer: unsafe {
            core::slice::from_raw_parts(pixels.as_ptr().cast::<BltPixel>(), pixels.len())
        },
        src: BltRegion::Full,
        dest: (0, 0),
        dims: (width, height),
    })
    .map_err(|error| error.status())
}

fn draw_text(names: &[&str], volume: &str, selected: usize, starting: bool) -> Result<(), Status> {
    system::with_stdout(|out| {
        out.set_color(Color::LightGray, Color::Black)
            .map_err(|e| e.status())?;
        out.clear().map_err(|e| e.status())?;
        let (columns, rows) = out
            .current_mode()
            .ok()
            .flatten()
            .map(|m| (m.columns(), m.rows()))
            .unwrap_or((80, 25));
        writeln!(
            out,
            "NextCore boot menu\n\n{}\n",
            if starting {
                "Starting selected system"
            } else {
                "Choose your system"
            }
        )
        .map_err(|_| Status::DEVICE_ERROR)?;
        let visible = rows.saturating_sub(10).max(1).min(names.len());
        let first = selected
            .saturating_sub(visible / 2)
            .min(names.len() - visible);
        for (index, name) in names.iter().enumerate().skip(first).take(visible) {
            let shown = display(name, columns.saturating_sub(10));
            writeln!(
                out,
                "{} {:02}. {}",
                if index == selected { ">" } else { " " },
                index + 1,
                shown
            )
            .map_err(|_| Status::DEVICE_ERROR)?;
        }
        writeln!(
            out,
            "\n{}\n\nArrow keys / Tab to choose\nEnter to boot   Esc to cancel",
            display(volume, columns.saturating_sub(1))
        )
        .map_err(|_| Status::DEVICE_ERROR)?;
        Ok(())
    })
}

fn read_action() -> Result<Action, Status> {
    loop {
        let mut events =
            [system::with_stdin(|input| input.wait_for_key_event()).map_err(|e| e.status())?];
        boot::wait_for_event(&mut events).map_err(|e| e.status())?;
        let Some(key) = system::with_stdin(|input| input.read_key()).map_err(|e| e.status())?
        else {
            continue;
        };
        return Ok(match key {
            Key::Printable(ch) if ch == char16!('\r') => Action::Boot,
            Key::Printable(ch) if ch == char16!('\t') => Action::Next,
            Key::Special(ScanCode::LEFT | ScanCode::UP) => Action::Previous,
            Key::Special(ScanCode::RIGHT | ScanCode::DOWN) => Action::Next,
            Key::Special(ScanCode::HOME) => Action::First,
            Key::Special(ScanCode::END) => Action::Last,
            Key::Special(ScanCode::ESCAPE) => Action::Cancel,
            _ => Action::None,
        });
    }
}

// Readiness is emitted after Blt. Writing ConOut here would damage the GOP UI.
fn serial(text: &str) {
    if let Ok(handle) = boot::get_handle_for_protocol::<Serial>() {
        if let Ok(mut serial) = boot::open_protocol_exclusive::<Serial>(handle) {
            let _ = serial.write_exact(text.as_bytes());
            let _ = serial.write_exact(b"\r\n");
        }
    }
}
