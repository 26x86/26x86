use nextcore_core::kernel_collection::{inspect_kernel_collection, MAX_INPUT_SIZE};
use std::{fs::File, io::Read};

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let path = args.next().ok_or("usage: inspect_kc <binary-file>")?;
    if args.next().is_some() {
        return Err("usage: inspect_kc <binary-file>".into());
    }
    let file = File::open(path)?;
    if file.metadata()?.len() > MAX_INPUT_SIZE as u64 {
        return Err("KC input exceeds host inspection limit".into());
    }
    let mut bytes = Vec::new();
    file.take(MAX_INPUT_SIZE as u64 + 1)
        .read_to_end(&mut bytes)?;
    let inspection = inspect_kernel_collection(&bytes)?;
    println!(
        "{}",
        serde_json::to_string(&serde_json::json!({
            "kind": "kernel_collection_metadata",
            "structural_metadata_valid": true,
            "preparation_ready": inspection.preparation_ready(),
            "inspection": inspection,
        }))?
    );
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
