//! CLI mapping to the shared APLS host runner. No VM lifecycle or verdict logic
//! is duplicated here: the runner owns both and preserves its full receipt.

use std::path::PathBuf;
use std::process::ExitCode;

use anyhow::{ensure, Context, Result};
use clap::{Args, ValueEnum};
use nextcore_apls::runner::{FirmwareKind, RunOutcome, RunnerBackend, RunnerHost, RunnerRequest};

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
enum Backend {
    LocalNative,
    Tcg,
    TcgRecovery,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
enum Host {
    Local,
    Wsl,
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum Firmware {
    Avpbooter,
    IbootStage2,
}

#[derive(Debug, Args)]
#[command(
    after_help = "Exit status: 0 = macOS boot verified; 2 = unverified observation or invalid CLI arguments; 1 = runner/setup error.\nFor WSL, all paths except --host-receipt-dir use paths inside the selected distribution.\nTCG recovery uses --duration only after restore processing. Its --total-timeout covers worker and cleanup; pre/post integrity budgets add 40 seconds.\nThis command does not infer macOS boot from a successful worker exit or bootx acknowledgement."
)]
pub(super) struct RunArgs {
    #[arg(long, value_enum)]
    backend: Backend,
    #[arg(long, value_enum)]
    host: Host,
    /// Python executable in the selected host or WSL distribution
    #[arg(long)]
    python: PathBuf,
    #[arg(long, required_if_eq("host", "wsl"))]
    distribution: Option<String>,
    /// Repository containing the existing x86 VMApple worker
    #[arg(long)]
    repository: PathBuf,
    #[arg(long)]
    vm_json: PathBuf,
    /// New worker output directory, interpreted by the selected host
    #[arg(long)]
    output: PathBuf,
    /// New receipt directory on the current host; its parent must exist
    #[arg(long)]
    host_receipt_dir: PathBuf,
    #[arg(long, value_parser = clap::value_parser!(u16).range(26..=27))]
    target: u16,
    /// Native/raw-TCG UART observation timeout (default: 60); unavailable for recovery
    #[arg(long, value_parser = clap::value_parser!(u32).range(1..=86400))]
    observation_timeout: Option<u32>,
    /// Recovery: post-restore observation duration, not the overall timeout
    #[arg(long, default_value_t = 60, value_parser = clap::value_parser!(u32).range(1..=86400))]
    duration: u32,
    /// Required explicit research execution mode
    #[arg(long, required = true)]
    research_only: bool,
    /// Emit the runner's complete evidence receipt as JSON
    #[arg(long)]
    json: bool,
    #[arg(long, required_if_eq("backend", "local-native"))]
    macosvm: Option<PathBuf>,
    #[arg(long, required_if_eq_any = [("backend", "tcg"), ("backend", "tcg-recovery")], conflicts_with = "macosvm")]
    qemu: Option<PathBuf>,
    #[arg(long, required_if_eq_any = [("backend", "tcg"), ("backend", "tcg-recovery")], conflicts_with = "macosvm")]
    qemu_img: Option<PathBuf>,
    #[arg(long, required_if_eq_any = [("backend", "tcg"), ("backend", "tcg-recovery")], conflicts_with = "macosvm")]
    firmware: Option<PathBuf>,
    #[arg(
        long,
        value_enum,
        required_if_eq("backend", "tcg"),
        conflicts_with = "macosvm"
    )]
    firmware_kind: Option<Firmware>,
    /// TCG memory in MiB (default: 4096)
    #[arg(long, conflicts_with = "macosvm", value_parser = clap::value_parser!(u32).range(128..=1048576))]
    memory_mib: Option<u32>,
    /// TCG virtual CPU count (default: 2)
    #[arg(long, conflicts_with = "macosvm", value_parser = clap::value_parser!(u32).range(1..=255))]
    smp: Option<u32>,
    #[arg(
        long,
        required_if_eq("backend", "tcg-recovery"),
        conflicts_with = "macosvm"
    )]
    build_manifest: Option<PathBuf>,
    #[arg(
        long,
        required_if_eq("backend", "tcg-recovery"),
        conflicts_with = "macosvm"
    )]
    tss_helper: Option<PathBuf>,
    #[arg(
        long,
        required_if_eq("backend", "tcg-recovery"),
        conflicts_with = "macosvm"
    )]
    original_ibss: Option<PathBuf>,
    #[arg(
        long,
        required_if_eq("backend", "tcg-recovery"),
        conflicts_with = "macosvm"
    )]
    original_ibec: Option<PathBuf>,
    #[arg(
        long,
        required_if_eq("backend", "tcg-recovery"),
        conflicts_with = "macosvm"
    )]
    restore_role_dir: Option<PathBuf>,
    #[arg(long, required_if_eq("backend", "tcg-recovery"), value_parser = clap::value_parser!(u32).range(1..=300))]
    transition_timeout: Option<u32>,
    #[arg(long, required_if_eq("backend", "tcg-recovery"), value_parser = clap::value_parser!(u32).range(1..=300))]
    restore_timeout: Option<u32>,
    #[arg(long, required_if_eq("backend", "tcg-recovery"), value_parser = clap::value_parser!(u32).range(30..=86400))]
    total_timeout: Option<u32>,
    /// Explicit optional RPC experiment for normal recovery; default off
    #[arg(long)]
    optional_rpc_unavailable: bool,
}

impl RunArgs {
    fn into_request(self) -> Result<RunnerRequest> {
        if self.backend != Backend::TcgRecovery {
            ensure!(
                self.build_manifest.is_none()
                    && self.tss_helper.is_none()
                    && self.original_ibss.is_none()
                    && self.original_ibec.is_none()
                    && self.restore_role_dir.is_none()
                    && self.transition_timeout.is_none()
                    && self.restore_timeout.is_none()
                    && self.total_timeout.is_none()
                    && !self.optional_rpc_unavailable,
                "recovery options require --backend tcg-recovery"
            );
        } else {
            ensure!(
                self.firmware_kind.is_none() && self.observation_timeout.is_none(),
                "tcg-recovery uses AVPBooter and phase/total timeouts; omit --firmware-kind and --observation-timeout"
            );
        }
        let host = match self.host {
            Host::Local => {
                ensure!(
                    self.distribution.is_none(),
                    "--distribution requires --host wsl"
                );
                RunnerHost::Local {
                    python: self.python,
                }
            }
            Host::Wsl => RunnerHost::Wsl {
                distribution: self
                    .distribution
                    .context("--host wsl requires --distribution")?,
                python: self.python,
            },
        };
        let backend = match self.backend {
            Backend::LocalNative => {
                ensure!(
                    matches!(host, RunnerHost::Local { .. }),
                    "--backend local-native requires --host local"
                );
                RunnerBackend::Native {
                    macosvm: self
                        .macosvm
                        .context("--backend local-native requires --macosvm")?,
                }
            }
            Backend::Tcg => {
                ensure!(
                    (128..=262144).contains(&self.memory_mib.unwrap_or(4096)),
                    "raw TCG memory must be 128..262144 MiB"
                );
                RunnerBackend::Tcg {
                    qemu: self.qemu.context("--backend tcg requires --qemu")?,
                    qemu_img: self.qemu_img.context("--backend tcg requires --qemu-img")?,
                    firmware: self.firmware.context("--backend tcg requires --firmware")?,
                    firmware_kind: match self
                        .firmware_kind
                        .context("--backend tcg requires --firmware-kind")?
                    {
                        Firmware::Avpbooter => FirmwareKind::Avpbooter,
                        Firmware::IbootStage2 => FirmwareKind::IbootStage2,
                    },
                    memory_mib: self.memory_mib.unwrap_or(4096),
                    smp: self.smp.unwrap_or(2),
                }
            }
            Backend::TcgRecovery => RunnerBackend::TcgRecovery {
                qemu: self.qemu.context("tcg-recovery requires --qemu")?,
                qemu_img: self.qemu_img.context("tcg-recovery requires --qemu-img")?,
                firmware: self.firmware.context("tcg-recovery requires --firmware")?,
                memory_mib: self.memory_mib.unwrap_or(4096),
                smp: self.smp.unwrap_or(2),
                build_manifest: self
                    .build_manifest
                    .context("tcg-recovery requires --build-manifest")?,
                tss_helper: self
                    .tss_helper
                    .context("tcg-recovery requires --tss-helper")?,
                original_ibss: self
                    .original_ibss
                    .context("tcg-recovery requires --original-ibss")?,
                original_ibec: self
                    .original_ibec
                    .context("tcg-recovery requires --original-ibec")?,
                restore_role_dir: self
                    .restore_role_dir
                    .context("tcg-recovery requires --restore-role-dir")?,
                transition_timeout_secs: self
                    .transition_timeout
                    .context("tcg-recovery requires --transition-timeout")?,
                restore_timeout_secs: self
                    .restore_timeout
                    .context("tcg-recovery requires --restore-timeout")?,
                total_timeout_secs: self
                    .total_timeout
                    .context("tcg-recovery requires --total-timeout")?,
                optional_rpc_unavailable: self.optional_rpc_unavailable,
            },
        };
        Ok(RunnerRequest {
            host,
            backend,
            repository: self.repository,
            vm_json: self.vm_json,
            output: self.output,
            host_receipt_dir: self.host_receipt_dir,
            target_major: self.target,
            observation_timeout_secs: self.observation_timeout.unwrap_or(60),
            duration_secs: self.duration,
            research_only: self.research_only,
        })
    }

    pub(super) fn run(self) -> Result<ExitCode> {
        let json = self.json;
        let request = self.into_request()?;
        let outcome = request.run().context("APLS observation failed")?;
        if json {
            println!("{}", serde_json::to_string_pretty(&outcome)?);
        } else {
            println!(
                "runner: engine={} completed={} exit={}",
                outcome.engine,
                outcome.runner_completed,
                outcome
                    .runner_exit_code
                    .map_or_else(|| "unavailable".into(), |code| code.to_string())
            );
            println!(
                "guest: started={} terminated={}",
                outcome.guest_runtime_started, outcome.guest_process_terminated
            );
            if let Some(progress) = &outcome.recovery_progress {
                println!(
                    "recovery: dfu={} ibec-endpoint={} stage2-banner={} stage2-prompt={} restore-roles={} sequence={} bootx-ack={} firmware-panic={}",
                    progress.dfu_upload_completed,
                    progress.ibec_endpoint_advertised,
                    progress.stage2_banner_observed,
                    progress.stage2_prompt_observed,
                    progress.restore_role_step_count,
                    progress.restore_sequence_sent,
                    progress.bootx_acknowledged,
                    progress.firmware_panic_observed
                );
                println!(
                    "result: {}",
                    if outcome.macos_boot_verified {
                        "boot-verified"
                    } else if !outcome.guest_runtime_started {
                        "runtime-unconfirmed"
                    } else if !outcome.guest_process_terminated {
                        "cleanup-unconfirmed"
                    } else if !outcome.input_integrity {
                        "integrity-unconfirmed"
                    } else {
                        "completed-unverified"
                    }
                );
            }
            println!(
                "evidence: xnu={} userspace={} target-match={} input-integrity={}",
                outcome.xnu_executed,
                outcome.macos_userspace_reached,
                outcome.guest_target_match,
                outcome.input_integrity
            );
            println!("macos-boot-verified: {}", outcome.macos_boot_verified);
            println!(
                "installation-verified: {} graphics-acceleration-verified: {}",
                outcome.installation_verified, outcome.graphics_acceleration_verified
            );
            if let Some(failure) = &outcome.failure {
                println!("failure: {failure}");
            }
            println!(
                "receipt: {}",
                request.host_receipt_dir.join("adapter.json").display()
            );
        }
        Ok(outcome_exit(&outcome))
    }
}

fn outcome_exit(outcome: &RunOutcome) -> ExitCode {
    if outcome.macos_boot_verified {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(2)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    fn arguments() -> Vec<String> {
        [
            "nextcore-tool",
            "apls",
            "run",
            "--backend",
            "tcg",
            "--host",
            "local",
            "--python",
            "python3",
            "--repository",
            "/workspace with spaces/repository",
            "--vm-json",
            "/input with spaces/vm.json",
            "--output",
            "/output/run",
            "--host-receipt-dir",
            "/host/receipts",
            "--target",
            "27",
            "--qemu",
            "/qemu custom/qemu-system-aarch64",
            "--qemu-img",
            "/qemu/qemu-img",
            "--firmware",
            "/input/firmware.bin",
            "--firmware-kind",
            "iboot-stage2",
            "--observation-timeout",
            "5",
            "--duration",
            "7",
            "--memory-mib",
            "8192",
            "--smp",
            "4",
            "--research-only",
        ]
        .into_iter()
        .map(String::from)
        .collect()
    }

    fn parsed(args: &[String]) -> Result<RunArgs> {
        let cli = crate::Cli::try_parse_from(args)?;
        let crate::Command::Apls {
            action: crate::AplsAction::Run(args),
        } = cli.command
        else {
            panic!("expected apls run");
        };
        Ok(args)
    }

    fn replace(args: &mut [String], flag: &str, value: &str) {
        let position = args.iter().position(|s| s == flag).unwrap();
        args[position + 1] = value.into();
    }

    fn remove(args: &mut Vec<String>, flag: &str, has_value: bool) {
        let position = args.iter().position(|s| s == flag).unwrap();
        args.drain(position..position + if has_value { 2 } else { 1 });
    }

    #[test]
    fn local_tcg_options_reach_shared_runner_without_path_splitting() {
        let request = parsed(&arguments()).unwrap().into_request().unwrap();
        assert_eq!(request.target_major, 27);
        assert_eq!(request.observation_timeout_secs, 5);
        assert_eq!(request.duration_secs, 7);
        assert_eq!(request.host_receipt_dir, PathBuf::from("/host/receipts"));
        assert!(request.research_only);
        let invocation = request.invocation().unwrap();
        assert_eq!(invocation.executable, PathBuf::from("python3"));
        assert_eq!(
            invocation.current_dir,
            Some(PathBuf::from("/workspace with spaces/repository"))
        );
        for expected in [
            "/input with spaces/vm.json",
            "/qemu custom/qemu-system-aarch64",
            "iboot-stage2",
            "8192",
            "4",
            "--research-only",
        ] {
            assert!(
                invocation.arguments.contains(&expected.to_owned()),
                "missing {expected}"
            );
        }
    }

    #[test]
    fn incomplete_or_invalid_requests_are_rejected_without_launching() {
        for flag in [
            "--python",
            "--qemu",
            "--qemu-img",
            "--firmware",
            "--firmware-kind",
            "--target",
            "--host-receipt-dir",
            "--research-only",
        ] {
            let mut args = arguments();
            remove(&mut args, flag, flag != "--research-only");
            assert!(parsed(&args).is_err(), "accepted missing {flag}");
        }
        for (flag, value) in [
            ("--target", "25"),
            ("--target", "28"),
            ("--duration", "0"),
            ("--observation-timeout", "86401"),
            ("--memory-mib", "127"),
            ("--smp", "0"),
        ] {
            let mut args = arguments();
            replace(&mut args, flag, value);
            assert!(parsed(&args).is_err(), "accepted {flag}={value}");
        }
        let mut args = arguments();
        args.extend(["--distribution".into(), "Ubuntu".into()]);
        assert!(parsed(&args).unwrap().into_request().is_err());
    }

    #[test]
    fn wsl_requires_distribution_and_preserves_linux_paths() {
        let mut args = arguments();
        replace(&mut args, "--host", "wsl");
        assert!(parsed(&args).is_err());
        args.extend(["--distribution".into(), "Ubuntu-24.04".into()]);
        let request = parsed(&args).unwrap().into_request().unwrap();
        assert!(
            matches!(&request.host, RunnerHost::Wsl { distribution, python } if distribution == "Ubuntu-24.04" && python == PathBuf::from("python3").as_path())
        );
        #[cfg(windows)]
        {
            let invocation = request.invocation().unwrap();
            assert_eq!(invocation.executable, PathBuf::from("wsl.exe"));
            assert!(invocation.current_dir.is_none());
            assert_eq!(
                &invocation.arguments[..6],
                [
                    "--distribution",
                    "Ubuntu-24.04",
                    "--cd",
                    "/workspace with spaces/repository",
                    "--exec",
                    "python3"
                ]
            );
        }
    }

    #[test]
    fn native_selection_is_explicit_and_cannot_use_tcg_or_wsl_options() {
        let mut args = arguments();
        replace(&mut args, "--backend", "local-native");
        assert!(parsed(&args).is_err());
        for flag in [
            "--qemu",
            "--qemu-img",
            "--firmware",
            "--firmware-kind",
            "--memory-mib",
            "--smp",
        ] {
            remove(&mut args, flag, true);
        }
        args.extend(["--macosvm".into(), "/bin/macosvm".into()]);
        let request = parsed(&args).unwrap().into_request().unwrap();
        assert!(matches!(request.backend, RunnerBackend::Native { .. }));
        replace(&mut args, "--host", "wsl");
        args.extend(["--distribution".into(), "Ubuntu".into()]);
        assert!(parsed(&args).unwrap().into_request().is_err());
    }

    #[test]
    fn successful_worker_exit_is_not_a_successful_boot_exit() {
        let mut outcome = RunOutcome {
            schema: "test-only".into(),
            runner_pid: 1,
            runner_exit_code: Some(0),
            runner_completed: true,
            elapsed_seconds: 0.1,
            engine: "qemu-vmapple-tcg".into(),
            guest_runtime_started: true,
            guest_process_terminated: true,
            xnu_executed: false,
            macos_userspace_reached: false,
            guest_target_match: false,
            input_integrity: true,
            macos_boot_verified: false,
            installation_verified: false,
            graphics_acceleration_verified: false,
            recovery_progress: None,
            stdout_sha256: String::new(),
            report: None,
            failure: Some("boot evidence is incomplete".into()),
        };
        assert_eq!(outcome_exit(&outcome), ExitCode::from(2));
        // The shared runner owns this verdict. This only tests CLI exit mapping.
        outcome.macos_boot_verified = true;
        assert_eq!(outcome_exit(&outcome), ExitCode::SUCCESS);
    }

    fn recovery_arguments() -> Vec<String> {
        let mut args = arguments();
        replace(&mut args, "--backend", "tcg-recovery");
        remove(&mut args, "--firmware-kind", true);
        remove(&mut args, "--observation-timeout", true);
        for (flag, value) in [
            ("--build-manifest", "/original inputs/BuildManifest.plist"),
            ("--tss-helper", "/local helpers/request encoder"),
            ("--original-ibss", "/original inputs/iBSS.im4p"),
            ("--original-ibec", "/original inputs/iBEC.im4p"),
            ("--restore-role-dir", "/original inputs/restore roles"),
            ("--transition-timeout", "20"),
            ("--restore-timeout", "30"),
            ("--total-timeout", "75"),
        ] {
            args.extend([flag.into(), value.into()]);
        }
        args
    }

    #[test]
    fn explicit_recovery_options_map_to_supervisor_and_default_rpc_off() {
        let mut args = recovery_arguments();
        let request = parsed(&args).unwrap().into_request().unwrap();
        assert_eq!(request.duration_secs, 7);
        assert!(matches!(
            &request.backend,
            RunnerBackend::TcgRecovery {
                transition_timeout_secs: 20,
                restore_timeout_secs: 30,
                total_timeout_secs: 75,
                optional_rpc_unavailable: false,
                memory_mib: 8192,
                smp: 4,
                ..
            }
        ));
        let invocation = request.invocation().unwrap();
        assert_eq!(
            &invocation.arguments[..2],
            ["-m", "x86.recovery_supervisor"]
        );
        for path in [
            "/original inputs/BuildManifest.plist",
            "/local helpers/request encoder",
            "/original inputs/iBSS.im4p",
            "/original inputs/iBEC.im4p",
            "/original inputs/restore roles",
        ] {
            assert!(invocation.arguments.contains(&path.to_owned()));
        }
        assert!(!invocation
            .arguments
            .contains(&"--observation-timeout".into()));
        assert!(!invocation.arguments.contains(&"--firmware-kind".into()));
        args.push("--optional-rpc-unavailable".into());
        let invocation = parsed(&args)
            .unwrap()
            .into_request()
            .unwrap()
            .invocation()
            .unwrap();
        assert!(invocation
            .arguments
            .contains(&"--optional-rpc-unavailable".into()));
    }

    #[test]
    fn recovery_requires_all_inputs_and_rejects_raw_backend_options() {
        for flag in [
            "--qemu",
            "--qemu-img",
            "--firmware",
            "--build-manifest",
            "--tss-helper",
            "--original-ibss",
            "--original-ibec",
            "--restore-role-dir",
            "--transition-timeout",
            "--restore-timeout",
            "--total-timeout",
        ] {
            let mut args = recovery_arguments();
            remove(&mut args, flag, true);
            assert!(parsed(&args).is_err(), "accepted missing {flag}");
        }
        for (flag, value) in [
            ("--firmware-kind", "avpbooter"),
            ("--observation-timeout", "10"),
        ] {
            let mut args = recovery_arguments();
            args.extend([flag.into(), value.into()]);
            assert!(parsed(&args).unwrap().into_request().is_err());
        }
        let mut raw = arguments();
        replace(&mut raw, "--firmware-kind", "avpbooter");
        assert!(matches!(
            parsed(&raw).unwrap().into_request().unwrap().backend,
            RunnerBackend::Tcg { .. }
        ));
        raw.push("--optional-rpc-unavailable".into());
        assert!(parsed(&raw).unwrap().into_request().is_err());
    }

    #[test]
    fn recovery_validation_keeps_post_and_total_budgets_distinct() {
        for (flag, value) in [
            ("--transition-timeout", "301"),
            ("--restore-timeout", "0"),
            ("--total-timeout", "29"),
            ("--memory-mib", "511"),
            ("--smp", "33"),
            ("--duration", "70"),
        ] {
            let mut args = recovery_arguments();
            replace(&mut args, flag, value);
            let accepted = parsed(&args)
                .and_then(RunArgs::into_request)
                .and_then(|request| request.invocation().map_err(Into::into));
            assert!(accepted.is_err(), "accepted {flag}={value}");
        }
        let mut args = recovery_arguments();
        replace(&mut args, "--duration", "69");
        assert!(parsed(&args)
            .unwrap()
            .into_request()
            .unwrap()
            .invocation()
            .is_ok());
    }

    #[test]
    fn recovery_wsl_keeps_linux_paths_and_host_receipts_separate() {
        let mut args = recovery_arguments();
        replace(&mut args, "--host", "wsl");
        assert!(parsed(&args).is_err());
        args.extend(["--distribution".into(), "Ubuntu-24.04".into()]);
        replace(&mut args, "--host-receipt-dir", "C:/receipts/new-run");
        let request = parsed(&args).unwrap().into_request().unwrap();
        assert_eq!(
            request.host_receipt_dir,
            PathBuf::from("C:/receipts/new-run")
        );
        #[cfg(windows)]
        {
            let invocation = request.invocation().unwrap();
            assert_eq!(
                &invocation.arguments[..8],
                [
                    "--distribution",
                    "Ubuntu-24.04",
                    "--cd",
                    "/workspace with spaces/repository",
                    "--exec",
                    "python3",
                    "-m",
                    "x86.recovery_supervisor"
                ]
            );
            assert!(!invocation.arguments.contains(&"C:/receipts/new-run".into()));
        }
    }
}
