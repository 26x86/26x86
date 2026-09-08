//! Runtime-path input only; no operating-system image is embedded or emitted.
use nextcore_core::{
    kc_staging::{KcStagingPlan, MAX_STAGING_SIZE},
    kernel_collection::MAX_INPUT_SIZE,
};
use std::{fs::File, io::Read, time::Instant};

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let usage = "usage: stage_kc [--arm64] <binary-file>";
    let first = args.next().ok_or(usage)?;
    let arm64 = first == "--arm64";
    let path = if arm64 {
        args.next().ok_or(usage)?
    } else {
        first
    };
    if args.next().is_some() {
        return Err(usage.into());
    }
    let started = Instant::now();
    let file = File::open(path)?;
    let metadata = file.metadata()?;
    if !metadata.is_file() || metadata.len() > MAX_INPUT_SIZE as u64 {
        return Err("KC input must be a regular file within the host inspection limit".into());
    }
    let mut source = Vec::new();
    source.try_reserve_exact(metadata.len() as usize)?;
    file.take(MAX_INPUT_SIZE as u64 + 1)
        .read_to_end(&mut source)?;
    let plan = if arm64 {
        KcStagingPlan::new_arm64(&source)?
    } else {
        KcStagingPlan::new(&source)?
    };
    let staged = plan.stage()?;
    let plan = staged.plan();
    let verified = staged.verification();
    let output = serde_json::json!({
        "kind": "kernel_collection_staging",
        "cpu_type": plan.inspection().collection.cpu_type,
        "cpu_subtype": plan.inspection().collection.cpu_subtype,
        "staging_page_size": plan.page_size(),
        "structural_metadata_valid": true,
        "host_staging_verified": true,
        "physical_placement_verified": false,
        "preparation_ready": staged.preparation_ready(),
        "relocations_applied": false,
        "firmware_executed": false,
        "xnu_executed": false,
        "native_hal_verified": false,
        "macos_boot_verified": false,
        "metal_verified": false,
        "source_bytes": source.len(),
        "staging_limit_bytes": MAX_STAGING_SIZE,
        "minimum_virtual_address": plan.minimum_virtual_address(),
        "collection_header_virtual_address": plan.inspection().collection.header_address,
        "collection_header_offset": plan.collection_header_offset(),
        "outer_entry": plan.inspection().collection.entry,
        "outer_entry_offset": plan.outer_entry_offset(),
        "outer_segment_count": plan.inspection().collection.segments.len(),
        "staged_outer_segment_count": plan.segments().len(),
        "member_count": plan.inspection().members.len(),
        "arena_bytes": verified.arena_bytes,
        "copied_bytes": verified.copied_bytes,
        "zero_tail_bytes": verified.zero_tail_bytes,
        "hole_bytes": verified.hole_bytes,
        "member_headers_checked": verified.member_headers_checked,
        "member_segment_views_checked": verified.member_segment_views_checked,
        "member_file_bytes_compared": verified.member_file_bytes_compared,
        "requirements": plan.inspection().requirements,
        "elapsed_seconds": started.elapsed().as_secs_f64(),
    });
    // Owned arena and metadata are released before reporting success. Output
    // contains measurements only, never staged image or instruction bytes.
    drop(staged);
    drop(source);
    println!("{}", serde_json::to_string(&output)?);
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
