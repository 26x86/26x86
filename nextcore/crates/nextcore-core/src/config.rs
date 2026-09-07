use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::error::{CoreError, Result};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct Config {
    #[serde(default, rename = "ACPI")]
    pub acpi: AcpiConfig,
    #[serde(default)]
    pub boot_properties: BootProperties,
    #[serde(default)]
    pub device_properties: DevicePropertiesConfig,
    #[serde(default)]
    pub kernel: KernelConfig,
    #[serde(default)]
    pub misc: MiscConfig,
    #[serde(default)]
    pub nvram: NvramConfig,
    #[serde(default)]
    pub platform_info: PlatformInfo,
    #[serde(default)]
    pub uefi: UefiConfig,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct AcpiConfig {
    #[serde(default)]
    pub add: Vec<String>,
    #[serde(default)]
    pub delete: Vec<String>,
    #[serde(default)]
    pub patch: Vec<AcpiPatch>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct AcpiPatch {
    #[serde(default)]
    pub count: u32,
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub find: String,
    #[serde(default)]
    pub replace: String,
    #[serde(default)]
    pub table_signature: String,
    #[serde(default)]
    pub base: String,
    #[serde(default)]
    pub base_skip: u32,
    #[serde(default)]
    pub mask: String,
    #[serde(default)]
    pub replace_mask: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct BootProperties {
    #[serde(default)]
    pub arguments: String,
    #[serde(default)]
    pub console: String,
    #[serde(default)]
    pub cursor: bool,
    #[serde(default)]
    pub hibernate_mode: String,
    #[serde(default)]
    pub launcher_option: String,
    #[serde(default)]
    pub picker_attributes: u32,
    #[serde(default)]
    pub picker_mode: String,
    #[serde(default)]
    pub show_picker: bool,
    #[serde(default)]
    pub timeout: u32,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct DevicePropertiesConfig {
    #[serde(default)]
    pub add: HashMap<String, HashMap<String, DevicePropValue>>,
    #[serde(default)]
    pub delete: HashMap<String, Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(untagged)]
pub enum DevicePropValue {
    Data(Vec<u8>),
    Integer(i64),
    String(String),
    Bool(bool),
}

impl Default for DevicePropValue {
    fn default() -> Self {
        DevicePropValue::String(String::new())
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct KernelConfig {
    #[serde(default)]
    pub add: Vec<KernelExtension>,
    #[serde(default)]
    pub block: Vec<KernelExtension>,
    #[serde(default)]
    pub emulate: Vec<String>,
    #[serde(default)]
    pub force: Vec<KernelExtension>,
    #[serde(default)]
    pub patch: Vec<KernelPatch>,
    #[serde(default)]
    pub quirk: HashMap<String, bool>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct KernelExtension {
    #[serde(default)]
    pub bundle_path: String,
    #[serde(default)]
    pub comment: String,
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub executable_path: String,
    #[serde(default)]
    pub max_kernel: String,
    #[serde(default)]
    pub min_kernel: String,
    #[serde(default)]
    pub plist_path: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct KernelPatch {
    #[serde(default)]
    pub arch: String,
    #[serde(default)]
    pub base: String,
    #[serde(default)]
    pub count: u32,
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub find: String,
    #[serde(default)]
    pub identifier: String,
    #[serde(default)]
    pub limit: u32,
    #[serde(default)]
    pub mask: String,
    #[serde(default)]
    pub max_kernel: String,
    #[serde(default)]
    pub min_kernel: String,
    #[serde(default)]
    pub replace: String,
    #[serde(default)]
    pub replace_mask: String,
    #[serde(default)]
    pub skip: u32,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct MiscConfig {
    #[serde(default)]
    pub debug: DebugConfig,
    #[serde(default)]
    pub entries: Vec<MiscEntry>,
    #[serde(default)]
    pub security: SecurityConfig,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct DebugConfig {
    #[serde(default)]
    pub apple_debug: bool,
    #[serde(default)]
    pub apple_panic: bool,
    #[serde(default)]
    pub disable_watchdog: bool,
    #[serde(default)]
    pub target: u32,
    #[serde(default)]
    pub display_delay: u32,
    #[serde(default)]
    pub log_modules: String,
    #[serde(default)]
    pub save_logs_size: u32,
    #[serde(default)]
    pub syslog: bool,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct MiscEntry {
    #[serde(default)]
    pub arguments: String,
    #[serde(default)]
    pub comment: String,
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub path: String,
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub tool: bool,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct SecurityConfig {
    #[serde(default)]
    pub allow_set_default: bool,
    #[serde(default)]
    pub apple_secure_boot: String,
    #[serde(default)]
    pub scanned_policy: u32,
    #[serde(default)]
    pub expose_sensitive: u32,
    #[serde(default)]
    pub vault: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct NvramConfig {
    #[serde(default)]
    pub add: HashMap<String, HashMap<String, NvramValue>>,
    #[serde(default)]
    pub delete: HashMap<String, Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(untagged)]
pub enum NvramValue {
    String(String),
    Data(Vec<u8>),
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct PlatformInfo {
    #[serde(default)]
    pub generic: GenericPlatformInfo,
    #[serde(default)]
    pub update_smbios: bool,
    #[serde(default)]
    pub update_smbios_mode: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct GenericPlatformInfo {
    #[serde(default)]
    pub ambient_hardware_info: String,
    #[serde(default)]
    pub apex_memory: String,
    #[serde(default)]
    pub apex_processor: String,
    #[serde(default)]
    pub manufacturer: String,
    #[serde(default, rename = "MLB")]
    pub mlb: String,
    #[serde(default)]
    pub processor_type: String,
    #[serde(default)]
    pub rom: String,
    #[serde(default)]
    pub spoof_vendor: String,
    #[serde(default)]
    pub system_memory_status: String,
    #[serde(default)]
    pub system_name: String,
    #[serde(default)]
    pub system_product_name: String,
    #[serde(default)]
    pub system_serial_number: String,
    #[serde(default, rename = "SystemUUID")]
    pub system_uuid: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct UefiConfig {
    #[serde(default)]
    pub drivers: Vec<UefiDriver>,
    #[serde(default)]
    pub input: InputConfig,
    #[serde(default)]
    pub output: OutputConfig,
    #[serde(default)]
    pub quirks: HashMap<String, bool>,
    #[serde(default)]
    pub reserved_memory: Vec<ReservedMemory>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct UefiDriver {
    #[serde(default)]
    pub arguments: String,
    #[serde(default)]
    pub comment: String,
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub path: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct InputConfig {
    #[serde(default)]
    pub key_filtering: bool,
    #[serde(default)]
    pub key_forget_threshold: u32,
    #[serde(default, rename = "KeySupport")]
    pub key_supported: bool,
    #[serde(default)]
    pub key_swap: bool,
    #[serde(default)]
    pub key_success: bool,
    #[serde(default)]
    pub pointer_support: bool,
    #[serde(default)]
    pub pointer_support_profile: String,
    #[serde(default)]
    pub timer_resolution: u32,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct OutputConfig {
    #[serde(default)]
    pub clear_screen_on_mode_switch: bool,
    #[serde(default)]
    pub console_mode: String,
    #[serde(default)]
    pub direct_gop_rendering: bool,
    #[serde(default)]
    pub force_resolution: bool,
    #[serde(default)]
    pub gop_burst_length: u32,
    #[serde(default)]
    pub gop_pixel_limit: u32,
    #[serde(default)]
    pub ignore_text_in_graphics: bool,
    #[serde(default)]
    pub replace_tab_with_space: bool,
    #[serde(default)]
    pub resolution: String,
    #[serde(default)]
    pub screen_resolution: String,
    #[serde(default)]
    pub text_renderer: String,
    #[serde(default)]
    pub uga_resolution: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
pub struct ReservedMemory {
    #[serde(default)]
    pub address: u64,
    #[serde(default)]
    pub comment: String,
    #[serde(default)]
    pub data: String,
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub size: u64,
}

impl Config {
    pub fn from_bytes(data: &[u8]) -> Result<Self> {
        let config: Config = plist::from_bytes(data)?;
        Ok(config)
    }

    pub fn to_bytes(&self) -> Result<Vec<u8>> {
        let mut buf = Vec::new();
        plist::to_writer_binary(&mut buf, self)?;
        Ok(buf)
    }

    pub fn from_xml_bytes(data: &[u8]) -> Result<Self> {
        let mut cursor = std::io::Cursor::new(data);
        let config: Config = plist::from_reader(&mut cursor)?;
        Ok(config)
    }

    pub fn to_xml_bytes(&self) -> Result<Vec<u8>> {
        let mut buf = Vec::new();
        plist::to_writer_xml(&mut buf, self)?;
        Ok(buf)
    }

    pub fn validate(&self) -> Result<()> {
        if self.platform_info.generic.system_name.is_empty() {
            return Err(CoreError::ConfigValidation(
                "system_name is required".into(),
            ));
        }
        if self.platform_info.generic.mlb.is_empty() {
            return Err(CoreError::ConfigValidation("mlb is required".into()));
        }
        if self.platform_info.generic.system_serial_number.is_empty() {
            return Err(CoreError::ConfigValidation(
                "system_serial_number is required".into(),
            ));
        }
        Ok(())
    }
}
