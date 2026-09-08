//! Explicit runtime input and experimental slide; emits no image or addresses.
use nextcore_core::{kc_classic_rebase::KcClassicRebasePlan, kernel_collection::MAX_INPUT_SIZE};
use std::{fs::File, io::Read, time::Instant};

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let path = args
        .next()
        .ok_or("usage: rebase_kc <binary-file> --slide <u32-decimal-or-0x-hex>")?;
    if args.next().as_deref() != Some(std::ffi::OsStr::new("--slide")) {
        return Err("explicit --slide is required".into());
    }
    let slide = args.next().ok_or("missing slide")?;
    let slide = slide.to_str().ok_or("slide must be ASCII")?;
    let (number, radix) = slide.strip_prefix("0x").map_or((slide, 10), |s| (s, 16));
    if number.is_empty()
        || !number.bytes().all(|b| {
            if radix == 16 {
                b.is_ascii_hexdigit()
            } else {
                b.is_ascii_digit()
            }
        })
    {
        return Err("slide must be an unsigned decimal or 0x-hex u32".into());
    }
    let slide = u32::from_str_radix(number, radix)?;
    if args.next().is_some() {
        return Err("unexpected extra argument".into());
    }
    let started = Instant::now();
    let file = File::open(path)?;
    let metadata = file.metadata()?;
    if !metadata.is_file() || metadata.len() > MAX_INPUT_SIZE as u64 {
        return Err("KC input must be a bounded regular file".into());
    }
    let mut source = Vec::new();
    source.try_reserve_exact(metadata.len() as usize)?;
    file.take(MAX_INPUT_SIZE as u64 + 1)
        .read_to_end(&mut source)?;
    let rebased = KcClassicRebasePlan::new(&source, slide)?.apply()?;
    let result = serde_json::json!({
        "kind":"kernel_collection_classic_rebase", "source_bytes":source.len(),
        "classic_relocations_applied":rebased.classic_relocations_applied(),
        "host_readback_verified":true, "preparation_ready":rebased.preparation_ready(),
        "all_relocations_applied":false, "chained_relocations_applied":false,
        "headers_modified":false, "runtime_slide_selected":false,
        "physical_placement_verified":false, "firmware_executed":false,
        "xnu_executed":false, "native_hal_verified":false,
        "macos_boot_verified":false, "metal_verified":false,
        "summary":rebased.verification(), "elapsed_seconds":started.elapsed().as_secs_f64(),
    });
    drop(rebased);
    drop(source);
    println!("{}", serde_json::to_string(&result)?);
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
