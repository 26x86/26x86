/// Nextcore runtime mode selection. On x86 hardware the boot layer is native
/// EFI + ISE + GPU abstraction; on Apple Silicon it switches to the
/// APLS-Sandbox mode which routes through Apple's Virtualization framework.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AplsMode {
    NativeEfiX86,
    AppleSiliconSandbox,
}

impl AplsMode {
    pub fn as_str(&self) -> &'static str {
        match self {
            AplsMode::NativeEfiX86 => "native-efi-x86",
            AplsMode::AppleSiliconSandbox => "apls-sandbox",
        }
    }
}

#[derive(Debug, Clone)]
pub struct BootEnv {
    pub mode: AplsMode,
    pub arch: &'static str,
    pub virtualization_backend_available: bool,
}

/// Detect the mode from the build target. Real identification of Apple
/// Silicon hardware with an available Virtualization framework happens at
/// runtime via `probe`.
pub fn detect() -> AplsMode {
    if cfg!(all(target_arch = "aarch64", target_vendor = "apple")) {
        AplsMode::AppleSiliconSandbox
    } else {
        AplsMode::NativeEfiX86
    }
}

/// Probe the runtime environment: target architecture and whether the
/// virtualization backend reports itself available on this host.
pub fn probe() -> BootEnv {
    let mode = detect();
    let backend_available = match mode {
        AplsMode::NativeEfiX86 => false,
        AplsMode::AppleSiliconSandbox => crate::guest::current_backend().available(),
    };
    BootEnv {
        mode,
        arch: std::env::consts::ARCH,
        virtualization_backend_available: backend_available,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detect_is_environment_consistent() {
        if cfg!(all(target_arch = "aarch64", target_vendor = "apple")) {
            assert_eq!(detect(), AplsMode::AppleSiliconSandbox);
        } else {
            assert_eq!(detect(), AplsMode::NativeEfiX86);
        }
    }

    #[test]
    fn probe_reports_arch_and_mode() {
        let env = probe();
        assert_eq!(env.arch, std::env::consts::ARCH);
        if cfg!(all(target_arch = "aarch64", target_vendor = "apple")) {
            assert_eq!(env.mode, AplsMode::AppleSiliconSandbox);
        } else {
            assert_eq!(env.mode, AplsMode::NativeEfiX86);
            assert!(!env.virtualization_backend_available);
        }
    }
}