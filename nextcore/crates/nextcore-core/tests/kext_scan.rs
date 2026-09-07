use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

use nextcore_core::kext::{parse_info_plist, scan_kexts};

static COUNTER: AtomicU64 = AtomicU64::new(0);

fn temp_dir() -> PathBuf {
    let suffix = std::process::id() as u64 * 1_000_000 + COUNTER.fetch_add(1, Ordering::SeqCst);
    let dir = std::env::temp_dir().join(format!("nextcore_kext_test_{suffix}"));
    fs::create_dir_all(&dir).expect("create temp dir");
    dir
}

const INFO_PLIST: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.nextcore.TestKext</string>
    <key>CFBundleExecutable</key>
    <string>TestKext</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
</dict>
</plist>
"#;

#[test]
fn test_parse_info_plist() {
    let info = parse_info_plist(INFO_PLIST.as_bytes()).expect("plist should parse");
    assert_eq!(info.bundle_id, "com.nextcore.TestKext");
    assert_eq!(info.executable.as_deref(), Some("TestKext"));
    assert_eq!(info.version, "1.0.0");
}

#[test]
fn test_scan_kexts() {
    let root = temp_dir();
    let result = (|| -> Result<(), Box<dyn std::error::Error>> {
        let kext_dir = root.join("scan_kexts").join("kexts");
        fs::create_dir_all(&kext_dir)?;

        let kext_path = kext_dir.join("TestKext.kext").join("Contents");
        fs::create_dir_all(&kext_path)?;
        fs::write(kext_path.join("Info.plist"), INFO_PLIST)?;

        let scanned = scan_kexts(&kext_dir)?;
        assert_eq!(scanned.len(), 1, "exactly one kext should be found");
        assert_eq!(scanned[0].bundle_id, "com.nextcore.TestKext");
        assert_eq!(scanned[0].executable.as_deref(), Some("TestKext"));
        assert_eq!(scanned[0].version, "1.0.0");
        assert!(
            scanned[0].plist_path.ends_with("TestKext.kext\\Contents\\Info.plist")
                || scanned[0].plist_path.ends_with("TestKext.kext/Contents/Info.plist"),
            "plist_path was {}",
            scanned[0].plist_path
        );
        Ok(())
    })();

    let _ = fs::remove_dir_all(&root);
    result.expect("scan_kexts test failed");
}

#[test]
fn test_skip_invalid() {
    let root = temp_dir();
    let result = (|| -> Result<(), Box<dyn std::error::Error>> {
        let kext_dir = root.join("skip_invalid").join("kexts");
        fs::create_dir_all(&kext_dir)?;

        // No Info.plist -> should be skipped.
        fs::create_dir_all(kext_dir.join("Empty.kext").join("Contents"))?;

        // A regular file (not a directory) -> skipped.
        fs::write(kext_dir.join("notakext.txt"), b"hello")?;

        let scanned = scan_kexts(&kext_dir)?;
        assert!(
            scanned.is_empty(),
            "directories without Info.plist must be skipped, got {scanned:?}"
        );
        Ok(())
    })();

    let _ = fs::remove_dir_all(&root);
    result.expect("scan_kexts skip_invalid failed");
}
