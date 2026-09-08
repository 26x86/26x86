use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};

use nextcore_core::config::Config;
use nextcore_tool::build_efi_bundle;

mod apls;

#[derive(Parser)]
#[command(
    name = "nextcore-tool",
    version,
    about = "NextCore configuration and EFI build tool"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Validate a config.plist
    Validate {
        /// Path to the config.plist to validate
        plist: PathBuf,
    },
    /// Build a full EFI bundle directory
    Build {
        /// Path to the config.plist
        #[arg(long)]
        plist: PathBuf,
        /// Compiled x86_64 PE32+ EFI application to include
        #[arg(long)]
        efi: PathBuf,
        /// Output directory (existing bundle files are never overwritten)
        #[arg(long)]
        out: PathBuf,
    },
    /// Prepare an install USB (EFI only; macOS side runs createinstallmedia)
    InstallUsb {
        /// Path to the config.plist
        #[arg(long)]
        plist: PathBuf,
        /// Compiled x86_64 PE32+ EFI application to include
        #[arg(long)]
        efi: PathBuf,
        /// Output directory (existing bundle files are never overwritten)
        #[arg(long)]
        out: PathBuf,
    },
    /// APLS-Sandbox environment status
    Apls {
        #[command(subcommand)]
        action: AplsAction,
    },
}

#[derive(Subcommand)]
enum AplsAction {
    /// Run a bounded VM observation; exit 0 only for verified macOS boot
    Run(apls::RunArgs),
    /// Probe the boot mode, arch, and virtualization backend availability
    Status,
    /// Validate a VSK policy plist (fails closed)
    VerifyPolicy {
        /// Path to the VSK policy plist to validate
        #[arg(long)]
        plist: PathBuf,
    },
}

fn main() -> Result<ExitCode> {
    let cli = Cli::parse();

    match cli.command {
        Command::Validate { plist } => {
            let cfg = load_config(&plist)?;
            cfg.validate().context("config.plist validation failed")?;
            println!("verify: ok");
        }
        Command::Build { plist, efi, out } => {
            build_efi_bundle(&plist, &efi, &out)?;
            println!("built EFI bundle at {}", out.display());
        }
        Command::InstallUsb { plist, efi, out } => {
            build_efi_bundle(&plist, &efi, &out)?;
            println!("EFI 복사 완료 — macOS에서 계속하세요.");
            println!("EFI copy complete — continue on macOS.");
            println!("EFI layout assembled at {}", out.display());
            println!("Run createinstallmedia on macOS to create the install media.");
        }
        Command::Apls { action } => match action {
            AplsAction::Run(args) => return args.run(),
            AplsAction::Status => {
                let env = nextcore_apls::mode::probe();
                println!("mode: {}", env.mode.as_str());
                println!("arch: {}", env.arch);
                println!(
                    "virtualization-backend: {}",
                    if env.virtualization_backend_available {
                        "available"
                    } else {
                        "unavailable"
                    }
                );
                println!("fail-closed: boot not authorized");
            }
            AplsAction::VerifyPolicy { plist } => {
                let data = fs::read(&plist)
                    .with_context(|| format!("failed to read {}", plist.display()))?;
                let policy = nextcore_apls::vf_policy::VskPolicy::from_plist_bytes(&data)
                    .with_context(|| format!("VSK policy rejected {}", plist.display()))?;
                println!(
                    "policy ok: profile={} guest-miB={} sha256={}",
                    policy
                        .guest_profile
                        .as_ref()
                        .map(|p| p.as_str())
                        .unwrap_or("none"),
                    policy.guest_mib,
                    policy.config_hash_hex()
                );
                println!("boot authorized: {}", policy.boot_authorized());
            }
        },
    }

    Ok(ExitCode::SUCCESS)
}

fn load_config(path: &Path) -> Result<Config> {
    let data = fs::read(path).with_context(|| format!("failed to read {}", path.display()))?;
    Config::from_bytes(&data).with_context(|| format!("failed to parse {}", path.display()))
}
