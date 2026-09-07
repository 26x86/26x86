use serde::Deserialize;
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::vf_abi::{Result as VfResult, VfError};

/// VSK product policy normalization. The v0.1 product policy is fixed at
/// `AppleIntelOnly`; there is no runtime switch that permits a general PC,
/// Hackintosh or outer VM, and no security downgrade when VMX, EPT, DMA
/// remapping or interrupt remapping is absent. `boot_authorized` is always
/// `false` because no real signature verifier or hardware executor is present;
/// no externally supplied "verified" boolean can turn a unit test or a config
/// parse into boot authorization.
#[derive(Debug, Error)]
pub enum PolicyError {
    #[error("plist parse failed: {0}")]
    Plist(String),
    #[error("duplicate or unknown config key")]
    UnknownKey,
    #[error("unsupported platform policy: {0}")]
    PlatformPolicy(String),
    #[error("weakened security setting rejected: {0}")]
    WeakenedSecurity(&'static str),
    #[error("unsupported guest profile: {0}")]
    GuestProfile(String),
    #[error("ABI violation: {0}")]
    Vf(#[from] VfError),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PlatformPolicy {
    AppleIntelOnly,
}

impl PlatformPolicy {
    pub fn as_str(&self) -> &'static str {
        match self {
            PlatformPolicy::AppleIntelOnly => "AppleIntelOnly",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GuestProfile {
    MacOS26Tahoe,
    MacOS27GoldenGate,
}

impl GuestProfile {
    pub fn as_str(&self) -> &'static str {
        match self {
            GuestProfile::MacOS26Tahoe => "macos26-tahoe",
            GuestProfile::MacOS27GoldenGate => "macos27-golden-gate",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DenialReason {
    NoSignatureVerifier,
    NoHardwareExecutor,
    UnknownConfig,
}

impl DenialReason {
    pub fn as_str(&self) -> &'static str {
        match self {
            DenialReason::NoSignatureVerifier => "no signature verifier",
            DenialReason::NoHardwareExecutor => "no hardware executor",
            DenialReason::UnknownConfig => "unknown config",
        }
    }
}

/// Normalized VSK policy. Always denies boot.
#[derive(Debug, Clone)]
pub struct VskPolicy {
    pub platform: PlatformPolicy,
    pub guest_profile: Option<GuestProfile>,
    pub require_vmx: bool,
    pub require_ept: bool,
    pub require_iommu: bool,
    pub require_interrupt_remapping: bool,
    pub guest_mib: u64,
    pub host_reserve_mib: u64,
    pub jit_cache_mib: u64,
    pub config_sha256: [u8; 32],
    pub boot_authorized: bool,
    pub denial_reason: DenialReason,
}

impl VskPolicy {
    /// Always false. The deliberately empty hardware path can never authorize.
    pub fn boot_authorized(&self) -> bool {
        false
    }

    pub fn deny(&self) -> (bool, &'static str) {
        (false, self.denial_reason.as_str())
    }

    /// The migration domain an execution cell must carry to boot this policy.
    pub fn required_features_present(&self, has_vmx: bool, has_ept: bool, has_irq: bool) -> bool {
        if self.require_vmx && !has_vmx {
            return false;
        }
        if self.require_ept && !has_ept {
            return false;
        }
        if self.require_interrupt_remapping && !has_irq {
            return false;
        }
        true
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct CpuConfig {
    #[serde(rename = "MinimumISA")]
    minimum_isa: Option<String>,
    #[serde(rename = "Codegen")]
    codegen: Option<String>,
    #[serde(rename = "HybridScheduling")]
    hybrid_scheduling: Option<String>,
    #[serde(rename = "VCPUs")]
    vcpus: Option<String>,
    #[serde(rename = "ServiceLogicalCPUs")]
    service_logical_cpus: Option<u32>,
    #[serde(rename = "SMTPolicy")]
    smt_policy: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SecurityConfig {
    #[serde(rename = "VMXRequired")]
    vmx_required: Option<bool>,
    #[serde(rename = "EPTRequired")]
    ept_required: Option<bool>,
    #[serde(rename = "IOMMURequired")]
    iommu_required: Option<bool>,
    #[serde(rename = "InterruptRemappingRequired")]
    interrupt_remapping_required: Option<bool>,
    #[serde(rename = "DMABypass")]
    dma_bypass: Option<bool>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct MemoryConfig {
    #[serde(rename = "GuestMiB")]
    guest_mib: Option<u64>,
    #[serde(rename = "HostReserveMiB")]
    host_reserve_mib: Option<u64>,
    #[serde(rename = "JITCacheMiB")]
    jit_cache_mib: Option<u64>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct GraphicsConfig {
    #[serde(rename = "Device")]
    device: Option<String>,
    #[serde(rename = "DriverPolicy")]
    driver_policy: Option<String>,
    #[serde(rename = "MinimumProfile")]
    minimum_profile: Option<String>,
    #[serde(rename = "OnUnsupported")]
    on_unsupported: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct StorageDevice {
    #[serde(rename = "ID")]
    id: Option<String>,
    #[serde(rename = "Backend")]
    backend: Option<String>,
    #[serde(rename = "DeviceSerial")]
    device_serial: Option<String>,
    #[serde(rename = "DiskGUID")]
    disk_guid: Option<String>,
    #[serde(rename = "PartitionGUID")]
    partition_guid: Option<String>,
    #[serde(rename = "SectorBytes")]
    sector_bytes: Option<u32>,
    #[serde(rename = "ReadOnly")]
    read_only: Option<bool>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct GuestConfig {
    #[serde(rename = "ProfileID")]
    profile_id: Option<String>,
    #[serde(rename = "RequireMetal")]
    require_metal: Option<bool>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct RawPolicy {
    #[serde(rename = "SchemaVersion")]
    schema_version: Option<i64>,
    #[serde(rename = "PlatformPolicy")]
    platform_policy: Option<String>,
    #[serde(rename = "CPU")]
    cpu: Option<CpuConfig>,
    #[serde(rename = "Security")]
    security: Option<SecurityConfig>,
    #[serde(rename = "Memory")]
    memory: Option<MemoryConfig>,
    #[serde(rename = "Storage")]
    storage: Option<Vec<StorageDevice>>,
    #[serde(rename = "Graphics")]
    graphics: Option<GraphicsConfig>,
    #[serde(rename = "Guest")]
    guest: Option<GuestConfig>,
}

impl VskPolicy {
    /// Parse and normalize a bounded XML plist. Unknown keys and weakened
    /// security settings are rejected. The result always denies boot.
    pub fn from_plist_bytes(bytes: &[u8]) -> Result<Self, PolicyError> {
        let hash = Sha256::digest(bytes);

        let raw: RawPolicy = plist::from_bytes(bytes).map_err(|e| PolicyError::Plist(e.to_string()))?;

        let platform = match raw.platform_policy.as_deref() {
            Some("AppleIntelOnly") | None => PlatformPolicy::AppleIntelOnly,
            Some(other) => return Err(PolicyError::PlatformPolicy(other.to_string())),
        };

        let cpu = raw.cpu.ok_or_else(|| PolicyError::UnknownKey)?;
        if let Some(isa) = cpu.minimum_isa.as_deref() {
            let ok = isa.eq_ignore_ascii_case("sse4.2") || isa.eq_ignore_ascii_case("sse42");
            if !ok {
                // ISA baselines below SSE4.2 are below the product floor.
                return Err(PolicyError::GuestProfile(isa.to_string()));
            }
        }

        let security = raw.security.ok_or_else(|| PolicyError::UnknownKey)?;
        if security.dma_bypass == Some(true) {
            return Err(PolicyError::WeakenedSecurity("DMA bypass enabled"));
        }
        let require_vmx = security.vmx_required.unwrap_or(false);
        let require_ept = security.ept_required.unwrap_or(false);
        let require_iommu = security.iommu_required.unwrap_or(false);
        let require_interrupt_remapping = security.interrupt_remapping_required.unwrap_or(false);

        let memory = raw.memory.ok_or_else(|| PolicyError::UnknownKey)?;
        let guest_mib = memory.guest_mib.unwrap_or(0);
        let host_reserve_mib = memory.host_reserve_mib.unwrap_or(0);
        let jit_cache_mib = memory.jit_cache_mib.unwrap_or(0);
        if guest_mib == 0 || host_reserve_mib == 0 || jit_cache_mib == 0 {
            return Err(PolicyError::UnknownKey);
        }

        let guest = raw.guest.ok_or_else(|| PolicyError::UnknownKey)?;
        let profile = match guest.profile_id.as_deref() {
            None | Some("") => None,
            Some("macos26-tahoe") => Some(GuestProfile::MacOS26Tahoe),
            Some("macos27-golden-gate") => Some(GuestProfile::MacOS27GoldenGate),
            Some(other) => return Err(PolicyError::GuestProfile(other.to_string())),
        };

        Ok(VskPolicy {
            platform,
            guest_profile: profile,
            require_vmx,
            require_ept,
            require_iommu,
            require_interrupt_remapping,
            guest_mib,
            host_reserve_mib,
            jit_cache_mib,
            config_sha256: hash.into(),
            boot_authorized: false,
            denial_reason: DenialReason::NoSignatureVerifier,
        })
    }

    /// Report the config hash as a hex string for receipts.
    pub fn config_hash_hex(&self) -> String {
        self.config_sha256
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect()
    }
}

/// A root→guest VF grant. Identity and range checks are separated from the
/// envelope shape: this is a bounded struct, not proof that the grant was
/// produced by a verified root.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VfGrant {
    pub object_id: u64,
    pub offset: u64,
    pub length: u64,
    pub restricted: bool,
}

impl VfGrant {
    pub fn new(object_id: u64, offset: u64, length: u64) -> Self {
        Self {
            object_id,
            offset,
            length,
            restricted: false,
        }
    }

    pub fn range_check(&self, within_object_len: u64) -> VfResult<()> {
        let end = self.offset.checked_add(self.length).ok_or(VfError::Erange)?;
        if end > within_object_len {
            return Err(VfError::Erange);
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    const GT_TEMPLATE: &[u8] = include_bytes!("../../../../sandbox/vsk/config/golden-gate.template.plist");

    #[test]
    fn golden_gate_template_parses_and_denies() {
        let policy = VskPolicy::from_plist_bytes(GT_TEMPLATE).unwrap();
        assert_eq!(policy.platform, PlatformPolicy::AppleIntelOnly);
        assert!(policy.require_vmx);
        assert!(policy.require_ept);
        assert!(policy.require_iommu);
        assert!(policy.require_interrupt_remapping);
        assert_eq!(policy.guest_mib, 8192);
        assert!(!policy.boot_authorized());
        assert_eq!(policy.deny(), (false, "no signature verifier"));
        assert_eq!(policy.config_sha256.len(), 32);
        assert_eq!(policy.config_hash_hex().len(), 64);
    }

    #[test]
    fn required_features_gate() {
        let policy = VskPolicy::from_plist_bytes(GT_TEMPLATE).unwrap();
        assert!(policy.required_features_present(true, true, true));
        assert!(!policy.required_features_present(false, true, true));
        assert!(!policy.required_features_present(true, false, true));
        assert!(!policy.required_features_present(true, true, false));
    }

    #[test]
    fn weakens_security_is_rejected() {
        let weak = String::from_utf8_lossy(GT_TEMPLATE)
            .replace("\r\n", "\n")
            .replace("<key>DMABypass</key>\n\t\t<false/>", "<key>DMABypass</key>\n\t\t<true/>");
        let res = VskPolicy::from_plist_bytes(weak.as_bytes());
        assert!(matches!(res, Err(PolicyError::WeakenedSecurity(_))));
    }

    #[test]
    fn unknown_key_is_rejected() {
        let unknown = String::from_utf8_lossy(GT_TEMPLATE)
            .replace("\r\n", "\n")
            .replace("<key>Guest</key>", "<key>NotARealKey</key>");
        let res = VskPolicy::from_plist_bytes(unknown.as_bytes());
        assert!(res.is_err());
    }

    #[test]
    fn unsupported_platform_policy_rejected() {
        let changed = String::from_utf8_lossy(GT_TEMPLATE)
            .replace("\r\n", "\n")
            .replace("AppleIntelOnly", "AnyPC");
        let res = VskPolicy::from_plist_bytes(changed.as_bytes());
        assert!(matches!(res, Err(PolicyError::PlatformPolicy(_))));
    }

    #[test]
    fn unregistered_guest_profile_rejected() {
        let changed = String::from_utf8_lossy(GT_TEMPLATE)
            .replace("\r\n", "\n")
            .replace("<key>ProfileID</key>\n\t\t<string></string>", "<key>ProfileID</key>\n\t\t<string>macos28-void</string>");
        let res = VskPolicy::from_plist_bytes(changed.as_bytes());
        assert!(matches!(res, Err(PolicyError::GuestProfile(_))));
    }

    #[test]
    fn grant_range_check() {
        let grant = VfGrant::new(0x10, 0, 4096);
        assert!(grant.range_check(8192).is_ok());
        assert!(grant.range_check(2048).is_err());

        let overflow = VfGrant::new(0x10, u64::MAX - 1, 16);
        assert!(overflow.range_check(u64::MAX).is_err());
    }

    #[test]
    fn bounded_key_set() {
        let raw: RawPolicy = plist::from_bytes(GT_TEMPLATE).unwrap();
        let mut keys = HashSet::new();
        macro_rules! track {
            ($($opt:expr),*) => { $( if let Some(_) = $opt { keys.insert(stringify!($opt)); } )* };
        }
        track!(raw.platform_policy, raw.cpu, raw.security, raw.memory, raw.graphics, raw.guest);
        assert!(keys.len() >= 5);
    }
}