use thiserror::Error;

/// APLS-Sandbox guest virtualization bridge. On Apple Silicon this routes
/// through Apple's Virtualization framework (`Virtualization.framework`);
/// everywhere else the backend is deliberately absent and every launch
/// fails closed. Nothing in this module reports macOS boot success.
#[derive(Debug, Error, PartialEq, Eq)]
pub enum GuestError {
    #[error("unsupported host: {0}")]
    UnsupportedHost(&'static str),
    #[error("invalid spec: {0}")]
    InvalidSpec(&'static str),
    #[error("backend unavailable")]
    BackendUnavailable,
    #[error("framework symbol missing: {0}")]
    FrameworkSymbol(&'static str),
    #[error("Apple Virtualization launch ABI pending: {0}")]
    AbiPending(&'static str),
}

pub type Result<T> = core::result::Result<T, GuestError>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct GuestSpec {
    pub cpu_count: u32,
    pub memory_bytes: u64,
}

impl GuestSpec {
    pub fn validate(&self) -> Result<()> {
        if self.cpu_count == 0 || self.cpu_count > 255 {
            return Err(GuestError::InvalidSpec("cpu_count out of range"));
        }
        if self.memory_bytes < 128 * 1024 * 1024 {
            return Err(GuestError::InvalidSpec("memory below 128 MiB"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GuestState {
    Stopped,
    Running,
    Paused,
    Faulted(String),
}

/// XSTATE migration domain. The execution cell must carry exactly the enabled
/// register state that a guest ABI expects; this is the SSE4.2 floor plus any
/// enabled vector state, computed from an `xcr0` value.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct XstateDomain {
    pub xcr0: u64,
}

impl XstateDomain {
    pub const XCR0_X87: u64 = 1 << 0;
    pub const XCR0_SSE: u64 = 1 << 1;
    pub const XCR0_AVX: u64 = 1 << 2;
    pub const XCR0_SSE4_2_FLOOR: u64 = Self::XCR0_X87 | Self::XCR0_SSE;

    pub fn from_xcr0(xcr0: u64) -> Self {
        Self { xcr0 }
    }

    pub fn has_floored_state(&self) -> bool {
        (self.xcr0 & Self::XCR0_SSE4_2_FLOOR) == Self::XCR0_SSE4_2_FLOOR
    }

    pub fn has_avx_state(&self) -> bool {
        (self.xcr0 & Self::XCR0_AVX) != 0
    }

    /// Fixed compacted frame requirements for the 8 general-purpose + YMM
    /// registers that ISE emulation has to preserve across a trap.
    pub fn ise_gpr_saved_count(&self) -> u32 {
        16
    }
}

/// Serialized guest launch plan. The plan is host-independent and fully
/// validated; applying it to a real VM is the backend's job.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuestLaunchPlan {
    pub spec: GuestSpec,
    pub boot_disk: String,
    pub smbios_override: Vec<(String, String)>,
    pub device_map: Vec<(u32, u32, u64)>,
}

impl GuestLaunchPlan {
    pub fn new(spec: GuestSpec, boot_disk: String) -> Result<Self> {
        spec.validate()?;
        if boot_disk.is_empty() {
            return Err(GuestError::InvalidSpec("empty boot disk"));
        }
        Ok(Self {
            spec,
            boot_disk,
            smbios_override: Vec::new(),
            device_map: Vec::new(),
        })
    }

    pub fn smbios(&mut self, key: String, value: String) -> &mut Self {
        self.smbios_override.push((key, value));
        self
    }

    pub fn map_device(&mut self, vendor_id: u32, device_id: u32, mmio_len: u64) -> &mut Self {
        self.device_map.push((vendor_id, device_id, mmio_len));
        self
    }

    pub fn encode(&self) -> Vec<u8> {
        let mut out = Vec::new();
        out.extend_from_slice(&self.spec.cpu_count.to_le_bytes());
        out.extend_from_slice(&self.spec.memory_bytes.to_le_bytes());
        out.extend_from_slice(&(self.boot_disk.len() as u32).to_le_bytes());
        out.extend_from_slice(self.boot_disk.as_bytes());
        out.extend_from_slice(&(self.smbios_override.len() as u32).to_le_bytes());
        for (k, v) in &self.smbios_override {
            out.extend_from_slice(&(k.len() as u32).to_le_bytes());
            out.extend_from_slice(k.as_bytes());
            out.extend_from_slice(&(v.len() as u32).to_le_bytes());
            out.extend_from_slice(v.as_bytes());
        }
        out.extend_from_slice(&(self.device_map.len() as u32).to_le_bytes());
        for (vid, did, len) in &self.device_map {
            out.extend_from_slice(&vid.to_le_bytes());
            out.extend_from_slice(&did.to_le_bytes());
            out.extend_from_slice(&len.to_le_bytes());
        }
        out
    }

    pub fn decode(buf: &[u8]) -> Result<Self> {
        let mut p = 0usize;
        fn take<'a>(buf: &'a [u8], p: &mut usize, n: usize) -> Result<&'a [u8]> {
            if *p + n > buf.len() {
                return Err(GuestError::InvalidSpec("truncated plan"));
            }
            let s = &buf[*p..*p + n];
            *p += n;
            Ok(s)
        }
        fn take_u32(buf: &[u8], p: &mut usize) -> Result<u32> {
            Ok(u32::from_le_bytes(take(buf, p, 4)?.try_into().unwrap()))
        }
        fn take_u64(buf: &[u8], p: &mut usize) -> Result<u64> {
            Ok(u64::from_le_bytes(take(buf, p, 8)?.try_into().unwrap()))
        }
        let cpu_count = take_u32(buf, &mut p)?;
        let memory_bytes = take_u64(buf, &mut p)?;
        let spec = GuestSpec { cpu_count, memory_bytes };
        spec.validate()?;
        let name_len = take_u32(buf, &mut p)? as usize;
        let boot_disk = String::from_utf8(take(buf, &mut p, name_len)?.to_vec())
            .map_err(|_| GuestError::InvalidSpec("boot disk not utf-8"))?;
        let mut plan = Self::new(spec, boot_disk)?;
        let smbios_count = take_u32(buf, &mut p)?;
        for _ in 0..smbios_count {
            let klen = take_u32(buf, &mut p)? as usize;
            let k = String::from_utf8(take(buf, &mut p, klen)?.to_vec())
                .map_err(|_| GuestError::InvalidSpec("smbios key not utf-8"))?;
            let vlen = take_u32(buf, &mut p)? as usize;
            let v = String::from_utf8(take(buf, &mut p, vlen)?.to_vec())
                .map_err(|_| GuestError::InvalidSpec("smbios value not utf-8"))?;
            plan.smbios_override.push((k, v));
        }
        let n_dev = take_u32(buf, &mut p)?;
        for _ in 0..n_dev {
            let vid = take_u32(buf, &mut p)?;
            let did = take_u32(buf, &mut p)?;
            let len = take_u64(buf, &mut p)?;
            plan.device_map.push((vid, did, len));
        }
        if p != buf.len() {
            return Err(GuestError::InvalidSpec("trailing bytes"));
        }
        Ok(plan)
    }
}

/// Backend contract for launching the APLS-Sandbox guest.
pub trait VirtualizationBackend {
    fn name(&self) -> &'static str;
    fn available(&self) -> bool;
    fn launch(&self, plan: &GuestLaunchPlan) -> Result<GuestState>;
    fn pause(&self) -> Result<GuestState>;
    fn resume(&self) -> Result<GuestState>;
}

/// Fail-closed backend used on every host that is not a supported Apple
/// Silicon target (or where the framework probe fails).
#[derive(Debug)]
pub struct UnsupportedBackend;

impl VirtualizationBackend for UnsupportedBackend {
    fn name(&self) -> &'static str {
        "unsupported"
    }
    fn available(&self) -> bool {
        false
    }
    fn launch(&self, _plan: &GuestLaunchPlan) -> Result<GuestState> {
        Err(GuestError::UnsupportedHost("no virtualization backend on this host"))
    }
    fn pause(&self) -> Result<GuestState> {
        Err(GuestError::BackendUnavailable)
    }
    fn resume(&self) -> Result<GuestState> {
        Err(GuestError::BackendUnavailable)
    }
}

/// Apple Silicon backend over Apple's Virtualization framework. The framework
/// discovery probe is genuine (dlopen + dlsym). Constructing an Objective-C
/// message flow (`VZVirtualMachineConfiguration` + asynchronous
/// `VZVirtualMachine.start`) without an Apple host to verify selector/block
/// ABI is an explicit pending boundary: it reports a precise
/// `GuestError::AbiPending` instead of fabricating success.
#[cfg(all(target_os = "macos", target_arch = "aarch64"))]
#[derive(Debug)]
pub struct AppleVirtualizationBackend {
    handle: *mut core::ffi::c_void,
    config_class: core::ptr::NonNull<()>,
}

#[cfg(all(target_os = "macos", target_arch = "aarch64"))]
impl Drop for AppleVirtualizationBackend {
    fn drop(&mut self) {
        extern "C" {
            fn dlclose(handle: *mut core::ffi::c_void) -> i32;
        }
        unsafe {
            dlclose(self.handle);
        }
    }
}

#[cfg(all(target_os = "macos", target_arch = "aarch64"))]
impl AppleVirtualizationBackend {
    pub fn probe() -> Result<Self> {
        extern "C" {
            fn dlopen(path: *const core::ffi::c_char, mode: i32) -> *mut core::ffi::c_void;
            fn dlsym(
                handle: *mut core::ffi::c_void,
                symbol: *const core::ffi::c_char,
            ) -> *mut core::ffi::c_void;
        }
        const RTLD_NOW: i32 = 2;
        let path = c"/System/Library/Frameworks/Virtualization.framework/Virtualization";
        let handle = unsafe { dlopen(path.as_ptr(), RTLD_NOW) };
        if handle.is_null() {
            return Err(GuestError::BackendUnavailable);
        }
        let sym = c"VZVirtualMachineConfiguration";
        let cfg = unsafe { dlsym(handle, sym.as_ptr()) };
        if cfg.is_null() {
            unsafe { dlclose(handle) };
            return Err(GuestError::FrameworkSymbol("VZVirtualMachineConfiguration"));
        }
        Ok(Self {
            handle,
            config_class: core::ptr::NonNull::new(cfg).unwrap(),
        })
    }
}

#[cfg(all(target_os = "macos", target_arch = "aarch64"))]
impl VirtualizationBackend for AppleVirtualizationBackend {
    fn name(&self) -> &'static str {
        "apple-virtualization"
    }
    fn available(&self) -> bool {
        true
    }
    fn launch(&self, plan: &GuestLaunchPlan) -> Result<GuestState> {
        plan.spec.validate()?;
        let _ = self.config_class;
        // The VZ async start requires objc_msgSend with a completion block;
        // selector and block ABI must be verified against a real Apple host
        // before this path reports a state transition.
        Err(GuestError::AbiPending(
            "VZ launch requires verified Objective-C ABI on an Apple Silicon host",
        ))
    }
    fn pause(&self) -> Result<GuestState> {
        Err(GuestError::AbiPending("VZ pause selector unverified"))
    }
    fn resume(&self) -> Result<GuestState> {
        Err(GuestError::AbiPending("VZ resume selector unverified"))
    }
}

/// Select the backend for the current host.
pub fn current_backend() -> Box<dyn VirtualizationBackend> {
    #[cfg(all(target_os = "macos", target_arch = "aarch64"))]
    {
        match AppleVirtualizationBackend::probe() {
            Ok(b) => Box::new(b),
            Err(_) => Box::new(UnsupportedBackend),
        }
    }
    #[cfg(not(all(target_os = "macos", target_arch = "aarch64")))]
    {
        Box::new(UnsupportedBackend)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spec_validation() {
        assert!(GuestSpec { cpu_count: 0, memory_bytes: 1 << 30 }.validate().is_err());
        assert!(GuestSpec { cpu_count: 2, memory_bytes: 64 << 20 }.validate().is_err());
        assert!(GuestSpec { cpu_count: 2, memory_bytes: 1 << 30 }.validate().is_ok());
        assert!(GuestSpec { cpu_count: 300, memory_bytes: 1 << 30 }.validate().is_err());
    }

    #[test]
    fn launch_plan_roundtrip() {
        let spec = GuestSpec { cpu_count: 8, memory_bytes: 8192 << 20 };
        let mut plan = GuestLaunchPlan::new(spec, "synthetic-boot.dmg".into()).unwrap();
        plan.smbios("product_name".into(), "Mac16,1".into());
        plan.map_device(0x106B, 0x1E00, 0x10000);
        let encoded = plan.encode();
        let back = GuestLaunchPlan::decode(&encoded).unwrap();
        assert_eq!(plan, back);
    }

    #[test]
    fn iso_boot_disk_rejected() {
        let spec = GuestSpec { cpu_count: 4, memory_bytes: 1 << 30 };
        assert!(GuestLaunchPlan::new(spec, String::new()).is_err());
    }

    #[test]
    fn launch_plan_decode_rejects_truncation() {
        let spec = GuestSpec { cpu_count: 4, memory_bytes: 1 << 30 };
        let plan = GuestLaunchPlan::new(spec, "synthetic-boot.dmg".into()).unwrap();
        let encoded = plan.encode();
        assert!(GuestLaunchPlan::decode(&encoded[..encoded.len() - 1]).is_err());
    }

    #[test]
    fn xstate_domain_floor() {
        let floor = XstateDomain::from_xcr0(XstateDomain::XCR0_SSE4_2_FLOOR);
        assert!(floor.has_floored_state());
        assert!(!floor.has_avx_state());
        let avx = XstateDomain::from_xcr0(XstateDomain::XCR0_SSE4_2_FLOOR | XstateDomain::XCR0_AVX);
        assert!(avx.has_avx_state());
        let below = XstateDomain::from_xcr0(XstateDomain::XCR0_X87);
        assert!(!below.has_floored_state());
        assert_eq!(avx.ise_gpr_saved_count(), 16);
    }

    #[test]
    fn unsupported_backend_fails_closed() {
        let backend = UnsupportedBackend;
        assert!(!backend.available());
        let spec = GuestSpec { cpu_count: 4, memory_bytes: 1 << 30 };
        let plan = GuestLaunchPlan::new(spec, "synthetic-boot.dmg".into()).unwrap();
        assert!(matches!(
            backend.launch(&plan),
            Err(GuestError::UnsupportedHost(_))
        ));
    }
}