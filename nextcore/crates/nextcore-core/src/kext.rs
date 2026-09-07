use std::path::Path;

use crate::error::{CoreError, Result};

#[derive(Debug, Clone)]
pub struct KextInfo {
    pub bundle_id: String,
    pub executable: Option<String>,
    pub version: String,
    pub plist_path: String,
}

pub fn scan_kexts(kext_dir: &Path) -> Result<Vec<KextInfo>> {
    let mut kexts = Vec::new();

    let entries = std::fs::read_dir(kext_dir)
        .map_err(|e| CoreError::KextScan(format!("failed to read kext directory: {e}")))?;

    for entry in entries {
        let entry =
            entry.map_err(|e| CoreError::KextScan(format!("failed to read dir entry: {e}")))?;
        let path = entry.path();

        if !path.is_dir() {
            continue;
        }

        let plist_path = path.join("Contents").join("Info.plist");
        if !plist_path.exists() {
            continue;
        }

        let data = std::fs::read(&plist_path).map_err(|e| {
            CoreError::KextScan(format!("failed to read {}: {e}", plist_path.display()))
        })?;

        match parse_info_plist(&data) {
            Ok(mut info) => {
                info.plist_path = plist_path.to_string_lossy().into_owned();
                kexts.push(info);
            }
            Err(e) => {
                log::warn!("skipping kext {}: {e}", path.display());
            }
        }
    }

    Ok(kexts)
}

pub fn parse_info_plist(data: &[u8]) -> Result<KextInfo> {
    let plist: plist::Value =
        plist::from_bytes(data).map_err(|e| CoreError::KextPlist(format!("plist parse failed: {e}")))?;

    let dict = match plist {
        plist::Value::Dictionary(d) => d,
        _ => {
            return Err(CoreError::KextPlist(
                "Info.plist root is not a dictionary".into(),
            ))
        }
    };

    let bundle_id = get_string_field(&dict, "CFBundleIdentifier")
        .ok_or_else(|| CoreError::KextPlist("CFBundleIdentifier missing".into()))?;

    let executable = get_string_field(&dict, "CFBundleExecutable");

    let version = get_string_field(&dict, "CFBundleVersion")
        .or_else(|| get_string_field(&dict, "CFBundleShortVersionString"))
        .unwrap_or_default();

    Ok(KextInfo {
        bundle_id,
        executable,
        version,
        plist_path: String::new(),
    })
}

fn get_string_field(dict: &plist::Dictionary, key: &str) -> Option<String> {
    dict.get(key)
        .and_then(|v| v.as_string())
        .map(|s| s.to_owned())
}
