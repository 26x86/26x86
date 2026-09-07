//! Host-side validation and assembly of an EFI bundle from explicit inputs.

pub mod efi;

use std::fs::{self, OpenOptions};
use std::io::{ErrorKind, Read, Seek, SeekFrom, Write};
use std::path::Path;

use anyhow::{bail, ensure, Context, Result};
use nextcore_core::config::Config;

/// Validate both inputs before creating any output, then copy the exact bytes.
/// Existing destination files are never replaced, including links to an input.
pub fn build_efi_bundle(plist: &Path, image: &Path, out: &Path) -> Result<()> {
    let config =
        fs::read(plist).with_context(|| format!("failed to read config {}", plist.display()))?;
    Config::from_bytes(&config)
        .with_context(|| format!("failed to parse {}", plist.display()))?
        .validate()
        .context("config.plist validation failed")?;
    let efi =
        fs::read(image).with_context(|| format!("failed to read EFI image {}", image.display()))?;
    efi::validate_x64_application(&efi)
        .with_context(|| format!("invalid EFI image {}", image.display()))?;

    let boot_dir = out.join("EFI/BOOT");
    let oc_dir = out.join("EFI/OC");
    let boot_path = boot_dir.join("BOOTX64.EFI");
    let config_path = oc_dir.join("config.plist");
    // symlink_metadata also catches dangling links. Check both destinations before
    // creating directories or opening either output, including the self-copy case.
    for path in [&boot_path, &config_path] {
        match fs::symlink_metadata(path) {
            Ok(_) => bail!(
                "destination already exists; refusing to overwrite {}",
                path.display()
            ),
            Err(err) if err.kind() == ErrorKind::NotFound => {}
            Err(err) => {
                return Err(err).with_context(|| format!("failed to inspect {}", path.display()))
            }
        }
    }
    for directory in [
        boot_dir,
        oc_dir.join("ACPI"),
        oc_dir.join("Drivers"),
        oc_dir.join("Kexts"),
    ] {
        fs::create_dir_all(&directory)
            .with_context(|| format!("failed to create {}", directory.display()))?;
    }
    write_new_verified(&boot_path, &efi)?;
    write_new_verified(&config_path, &config)?;
    Ok(())
}

fn write_new_verified(path: &Path, data: &[u8]) -> Result<()> {
    // create_new is atomic: a destination introduced after preflight cannot be
    // truncated. Reading through this handle verifies the bytes actually written.
    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .open(path)
        .with_context(|| format!("failed to create new output {}", path.display()))?;
    file.write_all(data)
        .with_context(|| format!("failed to write {}", path.display()))?;
    file.sync_all()
        .with_context(|| format!("failed to flush {}", path.display()))?;
    file.seek(SeekFrom::Start(0))?;
    let mut copied = Vec::new();
    file.read_to_end(&mut copied)?;
    ensure!(
        copied == data,
        "copy verification failed for {}",
        path.display()
    );
    Ok(())
}
