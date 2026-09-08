//! Third-party Linux EFI-stub handoff notes (additive, no behavior change).
//!
//! A real Ubuntu `vmlinuz` with an EFI stub is a PE32+ application
//! (subsystem `IMAGE_SUBSYSTEM_EFI_APPLICATION = 10`) and boots through the
//! existing generic `LoadImage -> StartImage` path in `main.rs` with the
//! `Misc.Entries` `Arguments` string as the kernel command line. No new boot
//! path, no ExitBootServices change, and no extra serial markers are added
//! here, so the existing 12/12 chainload and 8/8 kernel-probe suites are
//! unaffected. Observed with Ubuntu `6.8.0-139-generic` in OVMF/q35/TCG:
//! `NEXTCORE: IMAGE_START` is followed by the foreign
//! `Linux version 6.8.0-139-generic ...` banner on the same serial log.

#![allow(dead_code)]

/// PE optional-header subsystem for EFI applications.
pub const LINUX_EFI_SUBSYSTEM: u16 = 10;

/// Mirrors the `Misc.Entries` arguments bound enforced by the parser; the
/// Linux command line must fit it (UTF-16 units, excluding the NUL the
/// caller appends).
pub const LINUX_CMDLINE_MAX_UTF16: usize = 4096;

/// Serial console fragment used to direct the foreign kernel's own banner to
/// the OVMF serial log captured by the harness.
pub const LINUX_SERIAL_CONSOLE_FRAGMENT: &str = "console=ttyS0,115200";

/// Contract identifier for receipts and log review.
pub const LINUX_HANDOFF_CONTRACT: &str = "nextcore.linux-efi-stub-handoff.v1";

/// Pure predicate describing the tested configuration. Not consulted by the
/// boot path; kept for documentation and host-side review.
pub fn is_linux_handoff_target(path: &str, arguments: &str) -> bool {
    path.len() <= 1024
        && path
            .rsplit_once('.')
            .is_some_and(|(_, extension)| extension.eq_ignore_ascii_case("efi"))
        && arguments.contains("console=ttyS0")
}
