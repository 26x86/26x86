use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use nextcore_tool::efi::validate_x64_application;

const CONFIG: &[u8] = include_bytes!("../../nextcore-core/tests/sample.plist");
static SEQUENCE: AtomicU64 = AtomicU64::new(0);

struct Scratch(PathBuf);

impl Scratch {
    fn new() -> Self {
        let stamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "nextcore-tool-{}-{}-{}",
            std::process::id(),
            stamp,
            SEQUENCE.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }

    fn inputs(&self, image: &[u8]) -> (PathBuf, PathBuf) {
        let plist = self.0.join("input.plist");
        let efi = self.0.join("input.efi");
        fs::write(&plist, CONFIG).unwrap();
        fs::write(&efi, image).unwrap();
        (plist, efi)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        // Only the uniquely created direct child of the test temp directory is ours.
        assert_eq!(self.0.parent(), Some(std::env::temp_dir().as_path()));
        assert!(self
            .0
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("nextcore-tool-"));
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn cli(command: &str, plist: &Path, image: &Path, out: &Path) -> Output {
    Command::new(env!("CARGO_BIN_EXE_nextcore-tool"))
        .arg(command)
        .arg("--plist")
        .arg(plist)
        .arg("--efi")
        .arg(image)
        .arg("--out")
        .arg(out)
        .output()
        .unwrap()
}

fn put16(image: &mut [u8], offset: usize, value: u16) {
    image[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
}

fn put32(image: &mut [u8], offset: usize, value: u32) {
    image[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}

// A synthetic, structurally valid PE fixture for parser/copy regressions only.
// Firmware execution evidence must use compiled_efi_is_copied_without_changes
// followed by the independent OVMF runtime gate.
fn fixture() -> Vec<u8> {
    let mut image = vec![0u8; 1024];
    image[..2].copy_from_slice(b"MZ");
    put32(&mut image, 0x3c, 0x80);
    image[0x80..0x84].copy_from_slice(b"PE\0\0");
    put16(&mut image, 0x84, 0x8664);
    put16(&mut image, 0x86, 1);
    put16(&mut image, 0x94, 240);
    put16(&mut image, 0x96, 0x22);
    let optional = 0x98;
    put16(&mut image, optional, 0x20b);
    put32(&mut image, optional + 4, 512);
    put32(&mut image, optional + 16, 4096);
    put32(&mut image, optional + 20, 4096);
    put32(&mut image, optional + 32, 4096);
    put32(&mut image, optional + 36, 512);
    put32(&mut image, optional + 56, 8192);
    put32(&mut image, optional + 60, 512);
    put16(&mut image, optional + 68, 10);
    put32(&mut image, optional + 108, 16);
    let section = optional + 240;
    image[section..section + 5].copy_from_slice(b".text");
    put32(&mut image, section + 8, 3);
    put32(&mut image, section + 12, 4096);
    put32(&mut image, section + 16, 512);
    put32(&mut image, section + 20, 512);
    put32(&mut image, section + 36, 0x6000_0020);
    image[512..515].copy_from_slice(&[0x31, 0xc0, 0xc3]);
    image
}

fn assert_bundle(out: &Path, image: &[u8]) {
    assert_eq!(fs::read(out.join("EFI/BOOT/BOOTX64.EFI")).unwrap(), image);
    assert_eq!(fs::read(out.join("EFI/OC/config.plist")).unwrap(), CONFIG);
    for directory in ["ACPI", "Drivers", "Kexts"] {
        assert!(out.join("EFI/OC").join(directory).is_dir());
    }
}

#[test]
fn build_and_install_copy_validated_inputs_exactly() {
    let scratch = Scratch::new();
    let image = fixture();
    let (plist, efi) = scratch.inputs(&image);
    for command in ["build", "install-usb"] {
        let out = scratch.0.join(command);
        let result = cli(command, &plist, &efi, &out);
        assert!(
            result.status.success(),
            "{}",
            String::from_utf8_lossy(&result.stderr)
        );
        assert_bundle(&out, &image);
        if command == "install-usb" {
            assert!(String::from_utf8_lossy(&result.stdout).contains("continue on macOS"));
        }
    }
}

#[test]
fn every_truncated_prefix_is_rejected_without_panicking() {
    let image = fixture();
    assert!(validate_x64_application(&image).is_ok());
    for end in 0..image.len() {
        assert!(
            validate_x64_application(&image[..end]).is_err(),
            "accepted prefix {end}"
        );
    }
}

#[test]
fn malformed_pe_inputs_fail_before_output_creation() {
    let scratch = Scratch::new();
    let (plist, efi) = scratch.inputs(&fixture());
    let mut cases = vec![b"NXC00.1.0".to_vec(), fixture()[..700].to_vec()];
    // Wrong arch, PE32, wrong subsystem, no executable flag, short optional header.
    for (offset, value) in [
        (0x84, 0xaa64),
        (0x98, 0x10b),
        (0xdc, 3),
        (0x96, 0),
        (0x94, 111),
    ] {
        let mut image = fixture();
        put16(&mut image, offset, value);
        cases.push(image);
    }
    // Out-of-file header, missing entry, truncated directories, overflowing raw
    // range, raw section inside headers, and a directory pointing outside data.
    for (offset, value) in [
        (0x3c, u32::MAX),
        (0xa8, 0),
        (0x104, 17),
        (0x19c, u32::MAX),
        (0x19c, 0),
        (0x108, 0x3000),
    ] {
        let mut image = fixture();
        put32(&mut image, offset, value);
        if offset == 0x108 {
            put32(&mut image, 0x10c, 16);
        }
        cases.push(image);
    }
    for (index, image) in cases.into_iter().enumerate() {
        fs::write(&efi, image).unwrap();
        for command in ["build", "install-usb"] {
            let out = scratch.0.join(format!("{command}-{index}"));
            let result = cli(command, &plist, &efi, &out);
            assert!(!result.status.success(), "accepted malformed case {index}");
            assert!(!out.exists(), "created output for malformed case {index}");
        }
    }
}

#[test]
fn invalid_or_missing_inputs_do_not_create_output() {
    let scratch = Scratch::new();
    let (plist, efi) = scratch.inputs(&fixture());
    for config in [
        b"not a plist".as_slice(),
        b"<plist version=\"1.0\"><dict/></plist>".as_slice(),
    ] {
        fs::write(&plist, config).unwrap();
        let out = scratch.0.join("invalid-config");
        assert!(!cli("build", &plist, &efi, &out).status.success());
        assert!(!out.exists());
    }
    fs::write(&plist, CONFIG).unwrap();
    fs::remove_file(&efi).unwrap();
    let out = scratch.0.join("missing-image");
    assert!(!cli("install-usb", &plist, &efi, &out).status.success());
    assert!(!out.exists());
    fs::write(&efi, fixture()).unwrap();
    fs::remove_file(&plist).unwrap();
    assert!(!cli("build", &plist, &efi, &out).status.success());
    assert!(!out.exists());
}

#[test]
fn existing_outputs_and_self_copy_preserve_originals() {
    let scratch = Scratch::new();
    let image = fixture();
    let (plist, efi) = scratch.inputs(&image);
    let out = scratch.0.join("bundle");
    assert!(cli("build", &plist, &efi, &out).status.success());
    for (config, binary) in [
        (&plist, &efi),
        (&out.join("EFI/OC/config.plist"), &efi),
        (&plist, &out.join("EFI/BOOT/BOOTX64.EFI")),
    ] {
        let result = cli("build", config, binary, &out);
        assert!(!result.status.success());
        assert!(String::from_utf8_lossy(&result.stderr).contains("refusing to overwrite"));
        assert_bundle(&out, &image);
    }
}

#[test]
fn config_destination_preflight_prevents_partial_efi_write() {
    let scratch = Scratch::new();
    let (plist, efi) = scratch.inputs(&fixture());
    let out = scratch.0.join("bundle");
    fs::create_dir_all(out.join("EFI/OC")).unwrap();
    fs::write(out.join("EFI/OC/config.plist"), b"preserve this").unwrap();
    assert!(!cli("build", &plist, &efi, &out).status.success());
    assert!(!out.join("EFI/BOOT").exists());
    assert_eq!(
        fs::read(out.join("EFI/OC/config.plist")).unwrap(),
        b"preserve this"
    );
}

#[test]
fn hard_link_destination_cannot_truncate_input() {
    let scratch = Scratch::new();
    let image = fixture();
    let (plist, efi) = scratch.inputs(&image);
    let out = scratch.0.join("bundle");
    fs::create_dir_all(out.join("EFI/BOOT")).unwrap();
    fs::hard_link(&efi, out.join("EFI/BOOT/BOOTX64.EFI")).unwrap();
    assert!(!cli("build", &plist, &efi, &out).status.success());
    assert_eq!(fs::read(&efi).unwrap(), image);
    assert!(!out.join("EFI/OC").exists());
}

#[test]
fn explicit_efi_is_required_and_existing_read_only_commands_work() {
    let scratch = Scratch::new();
    let (plist, _) = scratch.inputs(&fixture());
    for command in ["build", "install-usb"] {
        let out = scratch.0.join(command);
        let result = Command::new(env!("CARGO_BIN_EXE_nextcore-tool"))
            .arg(command)
            .arg("--plist")
            .arg(&plist)
            .arg("--out")
            .arg(&out)
            .output()
            .unwrap();
        assert!(!result.status.success());
        assert!(String::from_utf8_lossy(&result.stderr).contains("--efi"));
        assert!(!out.exists());
    }
    let result = Command::new(env!("CARGO_BIN_EXE_nextcore-tool"))
        .arg("validate")
        .arg(&plist)
        .output()
        .unwrap();
    assert!(result.status.success());
    assert!(String::from_utf8_lossy(&result.stdout).contains("verify: ok"));
    let result = Command::new(env!("CARGO_BIN_EXE_nextcore-tool"))
        .args(["apls", "status"])
        .output()
        .unwrap();
    assert!(result.status.success());
    assert!(String::from_utf8_lossy(&result.stdout).contains("fail-closed: boot not authorized"));
}

#[test]
#[ignore = "requires NEXTCORE_TEST_EFI pointing to an independently compiled x86_64 UEFI image"]
fn compiled_efi_is_copied_without_changes() {
    let source = std::env::var_os("NEXTCORE_TEST_EFI")
        .expect("set NEXTCORE_TEST_EFI to a compiled EFI image");
    let image = fs::read(&source).expect("read independently compiled EFI image");
    let scratch = Scratch::new();
    let (plist, _) = scratch.inputs(&image);
    for command in ["build", "install-usb"] {
        let out = scratch.0.join(command);
        let result = cli(command, &plist, Path::new(&source), &out);
        assert!(
            result.status.success(),
            "{}",
            String::from_utf8_lossy(&result.stderr)
        );
        assert_bundle(&out, &image);
    }
    println!(
        "compiled EFI copied and read back unchanged: {} bytes from {}",
        image.len(),
        Path::new(&source).display()
    );
}
