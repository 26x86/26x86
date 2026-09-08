//! Explicit runtime input. Actual-image details belong only in isolation.
use nextcore_core::{
    kc_fixup_audit::{audit_kernel_collection, AuditIssue, AuditRecord},
    kernel_collection::MAX_INPUT_SIZE,
};
use std::{
    fs::{File, OpenOptions},
    io::{BufWriter, Read, Write},
    time::Instant,
};

#[derive(serde::Serialize)]
struct Details<'a> {
    kind: &'static str,
    primary_base: u64,
    records: &'a [AuditRecord],
    issues: &'a [AuditIssue],
    ownership_resolved: bool,
    relocations_applied: bool,
    preparation_ready: bool,
}

fn run() -> Result<bool, Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let path = args
        .next()
        .ok_or("usage: audit_kc <binary-file> [--details <fresh-file>]")?;
    let details = match args.next() {
        None => None,
        Some(flag) if flag == "--details" => Some(args.next().ok_or("missing details path")?),
        _ => return Err("usage: audit_kc <binary-file> [--details <fresh-file>]".into()),
    };
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
    let audit = audit_kernel_collection(&source)?;
    if let Some(path) = details {
        let mut output =
            BufWriter::new(OpenOptions::new().write(true).create_new(true).open(path)?);
        serde_json::to_writer(
            &mut output,
            &Details {
                kind: "kernel_collection_fixup_details",
                primary_base: audit.primary_base(),
                records: audit.records(),
                issues: audit.issues(),
                ownership_resolved: false,
                relocations_applied: false,
                preparation_ready: false,
            },
        )?;
        output.flush()?;
    }
    let valid = audit.ranges_valid();
    let output = serde_json::json!({
        "kind":"kernel_collection_fixup_audit","audit_completed":true,
        "fixup_ranges_valid":valid,"preparation_ready":audit.preparation_ready(),
        "relocations_applied":audit.relocations_applied(),"ownership_resolved":audit.ownership_resolved(),
        "physical_placement_verified":false,"firmware_executed":false,"xnu_executed":false,
        "native_hal_verified":false,"macos_boot_verified":false,"metal_verified":false,
        "source_bytes":source.len(),"summary":audit.summary(),"elapsed_seconds":started.elapsed().as_secs_f64(),
    });
    drop(audit);
    drop(source);
    println!("{}", serde_json::to_string(&output)?);
    Ok(valid)
}
fn main() {
    match run() {
        Ok(true) => {}
        Ok(false) => {
            eprintln!("KC_FIXUP_AUDIT_BLOCKED");
            std::process::exit(2)
        }
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(1)
        }
    }
}
