//! Explicit host-user-space adapter to the existing VMApple execution workers.
//! A worker PID is not a VM boot verdict. See `IMPLEMENTATION.md` for the contract.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Instant;
use thiserror::Error;

const MAX_REPORT_BYTES: u64 = 4 * 1024 * 1024;
// The supervisor caps JSON at 8 MiB and print() appends one newline.
const MAX_RECOVERY_REPORT_BYTES: u64 = 8 * 1024 * 1024 + 1;
const RECOVERY_CLEANUP_GRACE_SECS: u32 = 5;

#[derive(Debug, Error)]
pub enum RunnerError {
    #[error("invalid runner request: {0}")]
    InvalidRequest(&'static str),
    #[error("native worker requires local Apple-Silicon macOS")]
    UnsupportedHost,
    #[error("runner I/O: {0}")]
    Io(#[from] std::io::Error),
    #[error("runner receipt: {0}")]
    Json(#[from] serde_json::Error),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "transport", rename_all = "kebab-case")]
pub enum RunnerHost {
    Local {
        python: PathBuf,
    },
    /// All request paths except `host_receipt_dir` are Linux paths in this distro.
    Wsl {
        distribution: String,
        python: PathBuf,
    },
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum FirmwareKind {
    Avpbooter,
    IbootStage2,
}

impl FirmwareKind {
    fn argument(self) -> &'static str {
        match self {
            Self::Avpbooter => "avpbooter",
            Self::IbootStage2 => "iboot-stage2",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "backend", rename_all = "kebab-case")]
pub enum RunnerBackend {
    Native {
        macosvm: PathBuf,
    },
    Tcg {
        qemu: PathBuf,
        qemu_img: PathBuf,
        firmware: PathBuf,
        firmware_kind: FirmwareKind,
        memory_mib: u32,
        smp: u32,
    },
    /// Normal AVPBooter -> DFU -> iBEC -> restore execution, supervised in Linux.
    /// This is distinct from the raw Stage2/AVP `run-tcg` experiment.
    TcgRecovery {
        qemu: PathBuf,
        qemu_img: PathBuf,
        firmware: PathBuf,
        memory_mib: u32,
        smp: u32,
        build_manifest: PathBuf,
        tss_helper: PathBuf,
        original_ibss: PathBuf,
        original_ibec: PathBuf,
        restore_role_dir: PathBuf,
        transition_timeout_secs: u32,
        restore_timeout_secs: u32,
        total_timeout_secs: u32,
        optional_rpc_unavailable: bool,
    },
}

impl RunnerBackend {
    fn schema(&self) -> &'static str {
        match self {
            Self::Native { .. } => "26x86.macosvm-native/1",
            Self::Tcg { .. } => "26x86.vmapple-tcg/1",
            Self::TcgRecovery { .. } => "nextcore.recovery-supervisor/1",
        }
    }

    fn engine(&self) -> &'static str {
        match self {
            Self::Native { .. } => "macosvm",
            Self::Tcg { .. } => "qemu-vmapple-tcg",
            Self::TcgRecovery { .. } => "qemu-vmapple-recovery",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerRequest {
    pub host: RunnerHost,
    pub backend: RunnerBackend,
    pub repository: PathBuf,
    pub vm_json: PathBuf,
    pub output: PathBuf,
    /// New directory on the current host; never an input or existing VM folder.
    pub host_receipt_dir: PathBuf,
    pub target_major: u16,
    /// UART observation timeout for native/raw-TCG; unused by TCG recovery.
    pub observation_timeout_secs: u32,
    /// TCG recovery uses this only for the post-restore observation period.
    pub duration_secs: u32,
    pub research_only: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Invocation {
    pub executable: PathBuf,
    pub arguments: Vec<String>,
    pub current_dir: Option<PathBuf>,
}

/// Protocol progress is evidence of individual stages, never a boot verdict.
#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct RecoveryProgress {
    pub dfu_upload_completed: bool,
    pub ibec_endpoint_advertised: bool,
    pub stage2_banner_observed: bool,
    pub stage2_prompt_observed: bool,
    pub restore_sequence_sent: bool,
    pub restore_role_step_count: u32,
    pub bootx_acknowledged: bool,
    pub firmware_panic_observed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunOutcome {
    pub schema: String,
    pub runner_pid: u32,
    pub runner_exit_code: Option<i32>,
    pub runner_completed: bool,
    pub elapsed_seconds: f64,
    pub engine: String,
    pub guest_runtime_started: bool,
    pub guest_process_terminated: bool,
    pub xnu_executed: bool,
    pub macos_userspace_reached: bool,
    pub guest_target_match: bool,
    pub input_integrity: bool,
    pub macos_boot_verified: bool,
    pub installation_verified: bool,
    pub graphics_acceleration_verified: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recovery_progress: Option<RecoveryProgress>,
    pub stdout_sha256: String,
    pub report: Option<Value>,
    pub failure: Option<String>,
}

impl RunOutcome {
    /// The worker has been reaped by this point: never return `Running` here.
    pub fn guest_state(&self) -> crate::guest::GuestState {
        if let Some(reason) = &self.failure {
            crate::guest::GuestState::Faulted(reason.clone())
        } else {
            crate::guest::GuestState::Stopped
        }
    }
}

fn text_path(path: &Path) -> Result<String, RunnerError> {
    match path.to_str() {
        Some(s) if !s.is_empty() && !s.contains('\0') => Ok(s.to_owned()),
        _ => Err(RunnerError::InvalidRequest(
            "paths must be nonempty UTF-8 without NUL",
        )),
    }
}

impl RunnerRequest {
    pub fn invocation(&self) -> Result<Invocation, RunnerError> {
        if !self.research_only {
            return Err(RunnerError::InvalidRequest(
                "explicit research_only acknowledgement required",
            ));
        }
        if !matches!(self.target_major, 26 | 27) {
            return Err(RunnerError::InvalidRequest("target must be 26 or 27"));
        }
        let recovery = matches!(self.backend, RunnerBackend::TcgRecovery { .. });
        if (!recovery && !(1..=86400).contains(&self.observation_timeout_secs))
            || !(1..=86400).contains(&self.duration_secs)
        {
            return Err(RunnerError::InvalidRequest(
                "timeouts must be 1..86400 seconds",
            ));
        }
        if matches!(self.backend, RunnerBackend::Native { .. })
            && (!cfg!(all(target_os = "macos", target_arch = "aarch64"))
                || !matches!(self.host, RunnerHost::Local { .. }))
        {
            return Err(RunnerError::UnsupportedHost);
        }
        text_path(&self.host_receipt_dir)?;
        let repository = text_path(&self.repository)?;
        let mut arguments = vec!["-m".into(), "x86".into(), "vmapple".into()];
        match &self.backend {
            RunnerBackend::Native { macosvm } => {
                arguments.extend(["run-native".into(), "--macosvm".into(), text_path(macosvm)?]);
            }
            RunnerBackend::Tcg {
                qemu,
                qemu_img,
                firmware,
                firmware_kind,
                memory_mib,
                smp,
            } => {
                if !(128..=262144).contains(memory_mib) || !(1..=255).contains(smp) {
                    return Err(RunnerError::InvalidRequest(
                        "TCG memory/CPU count out of range",
                    ));
                }
                arguments.extend([
                    "run-tcg".into(),
                    "--qemu".into(),
                    text_path(qemu)?,
                    "--qemu-img".into(),
                    text_path(qemu_img)?,
                    "--firmware".into(),
                    text_path(firmware)?,
                    "--firmware-kind".into(),
                    firmware_kind.argument().into(),
                    "--memory-mib".into(),
                    memory_mib.to_string(),
                    "--smp".into(),
                    smp.to_string(),
                    "--display".into(),
                    "none".into(),
                ]);
            }
            RunnerBackend::TcgRecovery {
                qemu,
                qemu_img,
                firmware,
                memory_mib,
                smp,
                build_manifest,
                tss_helper,
                original_ibss,
                original_ibec,
                restore_role_dir,
                transition_timeout_secs,
                restore_timeout_secs,
                total_timeout_secs,
                optional_rpc_unavailable,
            } => {
                if !(512..=1048576).contains(memory_mib) || !(1..=32).contains(smp) {
                    return Err(RunnerError::InvalidRequest(
                        "recovery memory must be 512..1048576 MiB and CPU count 1..32",
                    ));
                }
                if !(1..=300).contains(transition_timeout_secs)
                    || !(1..=300).contains(restore_timeout_secs)
                    || !(30..=86400).contains(total_timeout_secs)
                    || *total_timeout_secs <= self.duration_secs + RECOVERY_CLEANUP_GRACE_SECS
                {
                    return Err(RunnerError::InvalidRequest(
                        "recovery phase timeouts must be 1..300 seconds; total 30..86400 and greater than post duration plus 5 seconds cleanup",
                    ));
                }
                arguments = vec!["-m".into(), "x86.recovery_supervisor".into()];
                for (flag, path) in [
                    ("--qemu", qemu),
                    ("--qemu-img", qemu_img),
                    ("--firmware", firmware),
                    ("--build-manifest", build_manifest),
                    ("--tss-helper", tss_helper),
                    ("--original-ibss", original_ibss),
                    ("--original-ibec", original_ibec),
                    ("--restore-role-dir", restore_role_dir),
                ] {
                    arguments.extend([flag.into(), text_path(path)?]);
                }
                for (flag, value) in [
                    ("--memory-mib", *memory_mib),
                    ("--smp", *smp),
                    ("--transition-timeout", *transition_timeout_secs),
                    ("--restore-timeout", *restore_timeout_secs),
                    ("--total-timeout", *total_timeout_secs),
                    ("--cleanup-grace", RECOVERY_CLEANUP_GRACE_SECS),
                ] {
                    arguments.extend([flag.into(), value.to_string()]);
                }
                if *optional_rpc_unavailable {
                    arguments.push("--optional-rpc-unavailable".into());
                }
            }
        }
        arguments.extend([
            "--target".into(),
            self.target_major.to_string(),
            "--vm-json".into(),
            text_path(&self.vm_json)?,
            "--output".into(),
            text_path(&self.output)?,
            "--duration".into(),
            self.duration_secs.to_string(),
        ]);
        if !recovery {
            arguments.extend([
                "--observation-timeout".into(),
                self.observation_timeout_secs.to_string(),
                "--research-only".into(),
                "--json".into(),
            ]);
        }
        match &self.host {
            RunnerHost::Local { python } => {
                text_path(python)?;
                Ok(Invocation {
                    executable: python.clone(),
                    arguments,
                    current_dir: Some(self.repository.clone()),
                })
            }
            RunnerHost::Wsl {
                distribution,
                python,
            } => {
                if !cfg!(target_os = "windows") {
                    return Err(RunnerError::InvalidRequest(
                        "WSL transport requires Windows host",
                    ));
                }
                if distribution.is_empty() || distribution.contains('\0') {
                    return Err(RunnerError::InvalidRequest(
                        "WSL distribution must be explicit",
                    ));
                }
                let mut prefix = vec![
                    "--distribution".into(),
                    distribution.clone(),
                    "--cd".into(),
                    repository,
                    "--exec".into(),
                    text_path(python)?,
                ];
                prefix.extend(arguments);
                Ok(Invocation {
                    executable: "wsl.exe".into(),
                    arguments: prefix,
                    current_dir: None,
                })
            }
        }
    }

    /// Run to completion. TCG recovery's Linux supervisor owns its overall
    /// deadline, process group and source hashing. Legacy native/raw-TCG workers
    /// retain their own lifecycle contracts. This adapter never detaches them.
    pub fn run(&self) -> Result<RunOutcome, RunnerError> {
        let invocation = self.invocation()?;
        fs::create_dir(&self.host_receipt_dir)?;
        write_new_json(&self.host_receipt_dir.join("request.json"), self)?;
        write_new_json(&self.host_receipt_dir.join("invocation.json"), &invocation)?;
        let stdout_path = self.host_receipt_dir.join("worker.stdout.json");
        let stdout = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&stdout_path)?;
        let stderr = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(self.host_receipt_dir.join("worker.stderr.log"))?;
        let mut command = Command::new(&invocation.executable);
        command
            .args(&invocation.arguments)
            .stdin(Stdio::null())
            .stdout(stdout)
            .stderr(stderr);
        if let Some(directory) = &invocation.current_dir {
            command.current_dir(directory);
        }
        // Avoid visible console windows on Windows. VM display is independently
        // set to headless above; the native worker does not receive --gui.
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000); // CREATE_NO_WINDOW
        }
        let started = Instant::now();
        let mut child = match command.spawn() {
            Ok(child) => child,
            Err(error) => {
                write_new_json(
                    &self.host_receipt_dir.join("spawn-error.json"),
                    &serde_json::json!({"runner_started": false, "macos_boot_verified": false, "error": error.to_string()}),
                )?;
                return Err(error.into());
            }
        };
        let pid = child.id();
        // Never abandon the live worker if persisting its PID fails.
        let pid_record = fs::write(self.host_receipt_dir.join("runner.pid"), format!("{pid}\n"));
        let status = child.wait()?;
        pid_record?;
        let report_limit = if matches!(self.backend, RunnerBackend::TcgRecovery { .. }) {
            MAX_RECOVERY_REPORT_BYTES
        } else {
            MAX_REPORT_BYTES
        };
        let (bytes, hash) = read_report(&stdout_path, report_limit)?;
        let parse_result = if bytes.len() as u64 > report_limit {
            Err(format!(
                "worker report exceeds {} MiB",
                report_limit / (1024 * 1024)
            ))
        } else {
            serde_json::from_slice::<Value>(&bytes)
                .map_err(|e| format!("worker did not return valid JSON: {e}"))
        };
        let mut outcome = evaluate_report(self, status.code(), parse_result);
        outcome.runner_pid = pid;
        outcome.elapsed_seconds = started.elapsed().as_secs_f64();
        outcome.stdout_sha256 = hash;
        write_new_json(&self.host_receipt_dir.join("adapter.json"), &outcome)?;
        Ok(outcome)
    }
}

fn read_report(path: &Path, limit: u64) -> Result<(Vec<u8>, String), std::io::Error> {
    let mut input = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut bytes = Vec::new();
    let mut buffer = [0u8; 65536];
    loop {
        let count = input.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
        let remaining = (limit as usize + 1).saturating_sub(bytes.len());
        bytes.extend_from_slice(&buffer[..count.min(remaining)]);
    }
    let hash = hasher
        .finalize()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    Ok((bytes, hash))
}

fn write_new_json(path: &Path, value: &impl Serialize) -> Result<(), RunnerError> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    serde_json::to_writer_pretty(&mut file, value)?;
    file.write_all(b"\n")?;
    Ok(())
}

fn evaluate_report(
    request: &RunnerRequest,
    exit: Option<i32>,
    parsed: Result<Value, String>,
) -> RunOutcome {
    if matches!(request.backend, RunnerBackend::TcgRecovery { .. }) {
        return evaluate_recovery_report(request, exit, parsed);
    }
    let (report, parse_error) = match parsed {
        Ok(value) => (Some(value), None),
        Err(error) => (None, Some(error)),
    };
    let empty = Value::Null;
    let r = report.as_ref().unwrap_or(&empty);
    let yes = |key: &str| r.get(key).and_then(Value::as_bool) == Some(true);
    let identity = r["schema"].as_str() == Some(request.backend.schema())
        && r["engine"].as_str() == Some(request.backend.engine())
        && r["target_major"].as_u64() == Some(u64::from(request.target_major));
    let runtime = identity
        && match request.backend {
            RunnerBackend::Native { .. } => yes("native_runtime_started"),
            // The Python TCG report historically sets native_runtime_started too.
            // Do not let that historical name reclassify TCG as native VF.
            RunnerBackend::Tcg { .. } => yes("tcg_runtime_started"),
            RunnerBackend::TcgRecovery { .. } => unreachable!("handled by recovery evaluator"),
        };
    let terminated = runtime
        && r["returncode"].as_i64().is_some()
        && r["termination"].as_str().is_some_and(|s| !s.is_empty());
    let markers = &r["observed_markers"];
    let xnu_offset = markers["xnu"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|m| {
            let recognized = matches!(
                m["marker"].as_str(),
                Some("Darwin Kernel Version" | "Darwin Kernel")
            );
            recognized.then(|| m["byte_offset"].as_u64()).flatten()
        })
        .min();
    let userspace_offset = markers["userspace"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|m| {
            matches!(
                m["marker"].as_str(),
                Some("launchd:" | "launchd " | "loginwindow" | "WindowServer")
            )
            .then(|| m["byte_offset"].as_u64())
            .flatten()
        })
        .filter(|offset| xnu_offset.is_some_and(|xnu| *offset > xnu))
        .min();
    let xnu = runtime && yes("xnu_executed") && xnu_offset.is_some();
    let userspace = runtime && yes("macos_userspace_reached") && userspace_offset.is_some();
    let target = identity
        && yes("guest_target_match")
        && r["guest_kernel_major"].as_u64() == Some(u64::from(request.target_major))
        && markers["xnu"].as_array().is_some_and(|items| {
            items.iter().any(|m| {
                matches!(
                    m["marker"].as_str(),
                    Some("Darwin Kernel Version" | "Darwin Kernel")
                ) && m["kernel_major"].as_u64() == Some(u64::from(request.target_major))
                    && m["byte_offset"].as_u64().is_some()
            })
        });
    let intact = identity && yes("input_integrity") && !yes("guest_inputs_modified");
    let verified = exit == Some(0)
        && terminated
        && xnu
        && userspace
        && target
        && intact
        && yes("macos_boot_verified")
        && r["error"].is_null();
    let failure = if verified {
        None
    } else {
        Some(parse_error.unwrap_or_else(|| {
            r["error"]
                .as_str()
                .or(r["blocker"].as_str())
                .map(str::to_owned)
                .unwrap_or_else(|| {
                    if !identity {
                        "worker report has no matching backend/target receipt"
                    } else if !runtime {
                        "guest runtime was not started"
                    } else if !terminated {
                        "guest process termination is unconfirmed"
                    } else if !intact {
                        "original input integrity is unconfirmed"
                    } else {
                        "target-matching XNU/userspace boot evidence is incomplete"
                    }
                    .to_owned()
                })
        }))
    };
    RunOutcome {
        schema: "nextcore.apls-host-run/1".into(),
        runner_pid: 0,
        runner_exit_code: exit,
        runner_completed: true,
        elapsed_seconds: 0.0,
        engine: request.backend.engine().into(),
        guest_runtime_started: runtime,
        guest_process_terminated: terminated,
        xnu_executed: xnu,
        macos_userspace_reached: userspace,
        guest_target_match: target,
        input_integrity: intact,
        macos_boot_verified: verified,
        installation_verified: false,
        graphics_acceleration_verified: false,
        recovery_progress: None,
        stdout_sha256: String::new(),
        report,
        failure,
    }
}

fn is_true(value: &Value) -> bool {
    value.as_bool() == Some(true)
}

/// A supervisor receipt and its original launch report are different schemas.
/// Never rewrite recovery progress into a raw-TCG report to reuse its verdict.
fn evaluate_recovery_report(
    request: &RunnerRequest,
    exit: Option<i32>,
    parsed: Result<Value, String>,
) -> RunOutcome {
    let (report, parse_error) = match parsed {
        Ok(value) => (Some(value), None),
        Err(error) => (None, Some(error)),
    };
    let empty = Value::Null;
    let envelope = report.as_ref().unwrap_or(&empty);
    let raw = &envelope["launch_report"]["raw"];
    let target = u64::from(request.target_major);
    let canonical_output = envelope["output"]
        .as_str()
        .filter(|path| path.starts_with('/') && !path.contains('\0'));
    let identity = envelope["schema"].as_str() == Some("nextcore.recovery-supervisor/1")
        && envelope["target_major"].as_u64() == Some(target)
        && envelope["requested_output"].as_str() == request.output.to_str()
        && canonical_output.is_some();
    let launch_identity = identity
        && envelope["launch_report"]["raw_schema"].as_str() == Some("26x86.vmapple-gui/1")
        && is_true(&envelope["launch_report"]["identity_valid"])
        && raw["schema"].as_str() == Some("26x86.vmapple-gui/1")
        && raw["target_major"].as_u64() == Some(target)
        && raw["output"].as_str() == canonical_output
        && raw["machine_type"].as_str() == Some("iBoot(AArch64)")
        && raw["personality"].as_str() == Some("iBoot")
        && raw["guest_os"].as_str() == Some("macOS")
        && raw["boot_mode"].as_str() == Some("recovery");
    let worker_pid = envelope["worker"]["pid"]
        .as_u64()
        .filter(|pid| *pid > 0 && *pid <= u64::from(u32::MAX));
    let qemu_pid = raw["pid"]
        .as_u64()
        .filter(|pid| *pid > 0 && *pid <= u64::from(u32::MAX));
    let runtime_pid_observed = worker_pid.is_some()
        && qemu_pid.is_some()
        && worker_pid != qemu_pid
        && is_true(&envelope["worker"]["process_inventory_complete"])
        && is_true(&envelope["launch_report"]["runtime_pid_observed"])
        && envelope["worker"]["observed_processes"]
            .as_array()
            .is_some_and(|processes| {
                let mut matches = processes
                    .iter()
                    .filter(|process| process["pid"].as_u64() == qemu_pid);
                // More than one recorded starttime for the PID is ambiguous reuse.
                matches.next().is_some_and(|process| {
                    process["session"].as_u64() == worker_pid
                        && process["starttime"].as_u64().is_some_and(|time| time > 0)
                }) && matches.next().is_none()
            });
    let runtime = launch_identity && is_true(&raw["runtime_started"]) && runtime_pid_observed;
    let cleanup = identity
        && is_true(&envelope["cleanup"]["complete"])
        && is_true(&envelope["cleanup"]["leader_reaped"])
        && envelope["cleanup"]["remaining_pids"]
            .as_array()
            .is_some_and(Vec::is_empty);
    let terminated = runtime && cleanup;
    let intact = identity && is_true(&envelope["input_integrity"]["unchanged"]);
    let uploaded_roles = [
        "RestoreTrustCache",
        "RestoreRamDisk",
        "RestoreDeviceTree",
        "RestoreKernelCache",
        "RestoreLogo",
    ]
    .map(|role| {
        raw["restore_chain"]["steps"]
            .as_array()
            .is_some_and(|steps| {
                steps.iter().any(|step| {
                    step["role"].as_str() == Some(role)
                        && is_true(&step["upload"]["transfer_complete"])
                })
            })
    });
    let progress = if runtime {
        RecoveryProgress {
            dfu_upload_completed: is_true(&raw["dfu_upload"]["transfer_complete"]),
            ibec_endpoint_advertised: raw["transition"]["state"].as_str() == Some("ibec-ready"),
            stage2_banner_observed: is_true(&raw["stage2"]["stage2_serial_started"])
                && raw["stage2"]["stage2_serial_start_byte_offset"]
                    .as_u64()
                    .is_some(),
            stage2_prompt_observed: is_true(&raw["stage2"]["observed"])
                && raw["stage2"]["byte_offset"].as_u64().is_some(),
            restore_sequence_sent: is_true(&raw["restore_chain"]["sequence_sent"])
                && is_true(&raw["restore_chain"]["input_integrity"])
                && uploaded_roles[..4].iter().all(|complete| *complete),
            restore_role_step_count: uploaded_roles.iter().filter(|complete| **complete).count()
                as u32,
            bootx_acknowledged: is_true(&raw["restore_chain"]["bootx_acknowledged"]),
            firmware_panic_observed: is_true(&raw["guest_panic"]["observed"])
                || is_true(&raw["stage2"]["panic_observed"])
                || is_true(&raw["restore_chain"]["post_bootx_panic"]),
        }
    } else {
        RecoveryProgress::default()
    };
    // Recovery's future observer may be nested, but all marker/major claims
    // must come from that single observation in this original launch receipt.
    let observation = raw
        .get("observation")
        .filter(|v| v.is_object())
        .unwrap_or(raw);
    let markers = &observation["observed_markers"];
    let xnu_offset = markers["xnu"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|marker| {
            (matches!(
                marker["marker"].as_str(),
                Some("Darwin Kernel Version" | "Darwin Kernel")
            ) && marker["kernel_major"].as_u64() == Some(target))
            .then(|| marker["byte_offset"].as_u64())
            .flatten()
        })
        .min();
    let userspace_offset = markers["userspace"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|marker| {
            matches!(
                marker["marker"].as_str(),
                Some("launchd:" | "launchd " | "loginwindow" | "WindowServer")
            )
            .then(|| marker["byte_offset"].as_u64())
            .flatten()
        })
        .filter(|offset| xnu_offset.is_some_and(|xnu| *offset > xnu))
        .min();
    let handoff = &raw["iboot_xnu_handoff"];
    let handoff_identity = handoff["schema"].as_str() == Some("26x86.iboot-xnu-handoff/1")
        && is_true(&handoff["valid"])
        && handoff["mode"].as_str() == Some("recovery")
        && handoff["target_major"].as_u64() == Some(target);
    let xnu = runtime
        && xnu_offset.is_some()
        && is_true(&raw["xnu_executed"])
        && is_true(&observation["xnu_executed"])
        && is_true(&envelope["boot"]["xnu_executed"]);
    let userspace = xnu
        && userspace_offset.is_some()
        && is_true(&observation["macos_userspace_reached"])
        && is_true(&envelope["boot"]["userspace"]);
    let target_match = xnu
        && raw["guest_kernel_major"].as_u64() == Some(target)
        && observation["guest_kernel_major"].as_u64() == Some(target)
        && envelope["boot"]["guest_kernel_major"].as_u64() == Some(target)
        && is_true(&raw["guest_target_match"])
        && is_true(&observation["guest_target_match"])
        && is_true(&envelope["boot"]["target_match"]);
    let complete = is_true(&envelope["launch_report"]["complete"])
        && is_true(&envelope["worker"]["completed"])
        && envelope["worker"]["returncode"].as_i64() == Some(0);
    let uninterrupted = envelope["deadline"]["exceeded"].as_bool() == Some(false)
        && envelope["cancel"]["requested"].as_bool() == Some(false);
    let verified = exit == Some(0)
        && complete
        && uninterrupted
        && terminated
        && intact
        && xnu
        && userspace
        && target_match
        && is_true(&raw["input_integrity"])
        && raw["error"].is_null()
        && envelope["error"].is_null()
        && is_true(&raw["macos_boot_verified"])
        && is_true(&envelope["boot"]["macos_boot_verified"])
        && handoff_identity
        && is_true(&handoff["claims"]["xnu_executed"])
        && is_true(&handoff["claims"]["macos_userspace_reached"])
        && is_true(&handoff["claims"]["macos_boot_verified"])
        && progress.dfu_upload_completed
        && progress.ibec_endpoint_advertised
        && progress.stage2_prompt_observed
        && progress.restore_sequence_sent
        && progress.bootx_acknowledged
        && !progress.firmware_panic_observed
        && raw["stage2"]["byte_offset"]
            .as_u64()
            .zip(xnu_offset)
            .is_some_and(|(stage2, xnu)| stage2 < xnu);
    let failure = if verified {
        None
    } else {
        Some(parse_error.unwrap_or_else(|| {
            if !identity || !launch_identity {
                "recovery receipt has no matching supervisor/launch identity".into()
            } else if !runtime {
                "recovery QEMU process identity was not observed in this run".into()
            } else if !cleanup {
                "Linux guest process cleanup is unconfirmed".into()
            } else if !intact {
                "original recovery input integrity is unconfirmed".into()
            } else if !uninterrupted {
                "recovery was cancelled or exceeded its deadline".into()
            } else {
                envelope["error"].as_str().or(raw["error"].as_str())
                    .or(raw["transition_blocker"].as_str())
                    .or(raw["golden_gate_installation"]["blocker"].as_str())
                    .unwrap_or("recovery completed-unverified: target-matching XNU/userspace evidence is incomplete")
                    .to_owned()
            }
        }))
    };
    RunOutcome {
        schema: "nextcore.apls-host-run/1".into(),
        runner_pid: 0,
        runner_exit_code: exit,
        runner_completed: true,
        elapsed_seconds: 0.0,
        engine: request.backend.engine().into(),
        guest_runtime_started: runtime,
        guest_process_terminated: terminated,
        xnu_executed: xnu,
        macos_userspace_reached: userspace,
        guest_target_match: target_match,
        input_integrity: intact,
        macos_boot_verified: verified,
        installation_verified: false,
        graphics_acceleration_verified: false,
        recovery_progress: Some(progress),
        stdout_sha256: String::new(),
        report,
        failure,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request() -> RunnerRequest {
        RunnerRequest {
            host: RunnerHost::Local {
                python: "python3".into(),
            },
            backend: RunnerBackend::Tcg {
                qemu: "/opt/qemu custom".into(),
                qemu_img: "/usr/bin/qemu-img".into(),
                firmware: "/input/original firmware.bin".into(),
                firmware_kind: FirmwareKind::Avpbooter,
                memory_mib: 4096,
                smp: 2,
            },
            repository: "/source".into(),
            vm_json: "/input/my bundle/macosvm.json".into(),
            output: "/output/new-run".into(),
            host_receipt_dir: "/receipts/new-run".into(),
            target_major: 27,
            observation_timeout_secs: 5,
            duration_secs: 5,
            research_only: true,
        }
    }

    #[test]
    fn command_keeps_paths_as_single_arguments_and_requires_acknowledgement() {
        let mut r = request();
        let command = r.invocation().unwrap();
        assert!(command
            .arguments
            .contains(&"/input/my bundle/macosvm.json".into()));
        assert!(command.arguments.contains(&"/opt/qemu custom".into()));
        assert!(!command.arguments.contains(&"--gui".into()));
        r.research_only = false;
        assert!(r.invocation().is_err());
    }

    #[test]
    fn booleans_and_successful_process_do_not_prove_boot() {
        let out = evaluate_report(
            &request(),
            Some(0),
            Ok(serde_json::json!({
                "schema": "26x86.vmapple-tcg/1", "engine": "qemu-vmapple-tcg", "target_major": 27,
                "tcg_runtime_started": true, "native_runtime_started": true,
                "macos_boot_verified": true, "xnu_executed": true, "macos_userspace_reached": true,
                "guest_target_match": true, "guest_kernel_major": 27, "input_integrity": true,
                "returncode": 0, "termination": "guest_exit"
            })),
        );
        assert!(out.guest_runtime_started);
        assert!(out.guest_process_terminated);
        assert!(!out.macos_boot_verified);
        assert!(!out.xnu_executed);
        assert!(matches!(
            out.guest_state(),
            crate::guest::GuestState::Faulted(_)
        ));
    }

    #[test]
    fn preflight_failure_and_missing_report_remain_failures() {
        let out = evaluate_report(
            &request(),
            Some(2),
            Ok(serde_json::json!({"error":"qemu unavailable","macos_boot_verified":false})),
        );
        assert!(!out.guest_runtime_started);
        assert_eq!(out.failure.as_deref(), Some("qemu unavailable"));
        let out = evaluate_report(&request(), Some(0), Err("truncated output".into()));
        assert!(!out.macos_boot_verified);
        assert_eq!(out.failure.as_deref(), Some("truncated output"));
    }

    #[test]
    fn wrong_target_and_input_mutation_deny_even_populated_evidence() {
        let base = serde_json::json!({
            "schema":"26x86.vmapple-tcg/1", "engine":"qemu-vmapple-tcg", "target_major":27,
            "tcg_runtime_started":true, "returncode":0, "termination":"guest_exit",
            "xnu_executed":true, "macos_userspace_reached":true, "guest_target_match":true,
            "guest_kernel_major":26, "input_integrity":true, "macos_boot_verified":true,
            "observed_markers":{"xnu":[{"marker":"Darwin Kernel Version","byte_offset":0,"kernel_major":27}],"userspace":[{"marker":"launchd:","byte_offset":100}]}
        });
        assert!(!evaluate_report(&request(), Some(0), Ok(base.clone())).macos_boot_verified);
        let mut mutated = base;
        mutated["guest_kernel_major"] = 27.into();
        mutated["input_integrity"] = false.into();
        assert!(!evaluate_report(&request(), Some(0), Ok(mutated)).macos_boot_verified);
    }

    #[test]
    fn evidence_verdict_requires_order_exit_and_backend_specific_runtime() {
        // Synthetic report validation only: this test never starts a guest.
        let base = serde_json::json!({
            "schema":"26x86.vmapple-tcg/1", "engine":"qemu-vmapple-tcg", "target_major":27,
            "tcg_runtime_started":true, "returncode":0, "termination":"guest_exit",
            "xnu_executed":true, "macos_userspace_reached":true, "guest_target_match":true,
            "guest_kernel_major":27, "input_integrity":true, "macos_boot_verified":true,
            "observed_markers":{"xnu":[{"marker":"Darwin Kernel Version","byte_offset":100,"kernel_major":27}],"userspace":[{"marker":"launchd:","byte_offset":200}]}
        });
        assert!(evaluate_report(&request(), Some(0), Ok(base.clone())).macos_boot_verified);
        assert!(!evaluate_report(&request(), Some(2), Ok(base.clone())).macos_boot_verified);
        let mut reversed = base.clone();
        reversed["observed_markers"]["userspace"][0]["byte_offset"] = 0.into();
        assert!(!evaluate_report(&request(), Some(0), Ok(reversed)).macos_boot_verified);
        let mut wrong_runtime = base;
        wrong_runtime["tcg_runtime_started"] = false.into();
        wrong_runtime["native_runtime_started"] = true.into();
        let out = evaluate_report(&request(), Some(0), Ok(wrong_runtime));
        assert!(!out.guest_runtime_started);
        assert!(!out.macos_boot_verified);
    }

    #[test]
    #[cfg(windows)]
    fn wsl_is_explicit_exec_transport_without_a_shell() {
        let mut r = request();
        r.host = RunnerHost::Wsl {
            distribution: "Ubuntu-24.04".into(),
            python: "/usr/bin/python3".into(),
        };
        let invocation = r.invocation().unwrap();
        assert_eq!(invocation.executable, PathBuf::from("wsl.exe"));
        assert_eq!(
            &invocation.arguments[..7],
            [
                "--distribution",
                "Ubuntu-24.04",
                "--cd",
                "/source",
                "--exec",
                "/usr/bin/python3",
                "-m"
            ]
        );
        assert!(invocation.current_dir.is_none());
        r.backend = RunnerBackend::Native {
            macosvm: "/usr/bin/macosvm".into(),
        };
        assert!(matches!(r.invocation(), Err(RunnerError::UnsupportedHost)));
    }

    #[test]
    fn invalid_request_creates_no_receipts() {
        let mut r = request();
        r.duration_secs = 0;
        assert!(r.run().is_err());
    }

    fn recovery_request() -> RunnerRequest {
        let mut request = request();
        request.duration_secs = 10;
        request.backend = RunnerBackend::TcgRecovery {
            qemu: "/qemu tools/qemu-system-aarch64".into(),
            qemu_img: "/qemu tools/qemu-img".into(),
            firmware: "/inputs/AVPBooter.bin".into(),
            memory_mib: 4096,
            smp: 2,
            build_manifest: "/inputs/BuildManifest.plist".into(),
            tss_helper: "/helper tools/request-encoder".into(),
            original_ibss: "/inputs/original iBSS.im4p".into(),
            original_ibec: "/inputs/original iBEC.im4p".into(),
            restore_role_dir: "/inputs/restore roles".into(),
            transition_timeout_secs: 20,
            restore_timeout_secs: 30,
            total_timeout_secs: 75,
            optional_rpc_unavailable: false,
        };
        request
    }

    // Authored JSON only. This fixture is not a guest-execution receipt.
    fn recovery_receipt() -> Value {
        let steps: Vec<Value> = [
            "RestoreTrustCache",
            "RestoreRamDisk",
            "RestoreDeviceTree",
            "RestoreKernelCache",
        ]
        .into_iter()
        .map(|role| {
            serde_json::json!({
                "role": role, "upload": {"transfer_complete": true}
            })
        })
        .collect();
        let worker = serde_json::json!({
            "pid":12,"returncode":0,"completed":true,"process_inventory_complete":true,
            "observed_processes":[{"pid":12,"starttime":100,"session":12},{"pid":13,"starttime":110,"session":12}]
        });
        serde_json::json!({
            "schema":"nextcore.recovery-supervisor/1", "target_major":27,
            "requested_output":"/output/new-run", "output":"/output/new-run", "supervisor_pid":11,
            "worker":worker,
            "cleanup":{"leader_reaped":true,"remaining_pids":[],"complete":true},
            "input_integrity":{"unchanged":true,"records":[]},
            "deadline":{"total_timeout_seconds":75,"cleanup_grace_seconds":5,"exceeded":false},
            "cancel":{"requested":false,"reason":null,"signal":null},
            "launch_report":{
                "path":"/output/new-run/launch.json", "complete":true,
                "raw_schema":"26x86.vmapple-gui/1", "identity_valid":true,"runtime_pid_observed":true,
                "raw":{
                    "schema":"26x86.vmapple-gui/1", "target_major":27,
                    "output":"/output/new-run", "machine_type":"iBoot(AArch64)",
                    "personality":"iBoot", "guest_os":"macOS", "boot_mode":"recovery",
                    "runtime_started":true,"pid":13,"returncode":0,"termination":"time_budget",
                    "dfu_upload":{"transfer_complete":true},
                    "transition":{"state":"ibec-ready"},
                    "stage2":{"stage2_serial_started":true,"stage2_serial_start_byte_offset":5,
                        "observed":true,"byte_offset":20},
                    "restore_chain":{"sequence_sent":true,"input_integrity":true,"bootx_acknowledged":true,
                        "steps":steps},
                    "guest_panic":{"observed":false},"input_integrity":true,
                    "xnu_executed":false,"guest_kernel_major":null,"guest_target_match":false,
                    "macos_boot_verified":false,"error":null
                }
            },
            "boot":{"xnu_executed":false,"guest_kernel_major":null,"target_match":false,
                "userspace":false,"macos_boot_verified":false}
        })
    }

    fn strict_recovery_receipt() -> Value {
        let mut report = recovery_receipt();
        let raw = &mut report["launch_report"]["raw"];
        raw["xnu_executed"] = true.into();
        raw["macos_userspace_reached"] = true.into();
        raw["guest_kernel_major"] = 27.into();
        raw["guest_target_match"] = true.into();
        raw["macos_boot_verified"] = true.into();
        raw["observed_markers"] = serde_json::json!({
            "xnu":[{"marker":"Darwin Kernel Version","kernel_major":27,"byte_offset":100}],
            "userspace":[{"marker":"launchd:","byte_offset":200}]
        });
        raw["iboot_xnu_handoff"] = serde_json::json!({
            "schema":"26x86.iboot-xnu-handoff/1","valid":true,"target_major":27,"mode":"recovery",
            "claims":{"xnu_executed":true,"macos_userspace_reached":true,"macos_boot_verified":true}
        });
        report["boot"] = serde_json::json!({
            "xnu_executed":true,"guest_kernel_major":27,"target_match":true,
            "userspace":true,"macos_boot_verified":true
        });
        report
    }

    #[test]
    fn recovery_invocation_uses_only_supervisor_flags_and_preserves_path_arguments() {
        let mut request = recovery_request();
        // An unused legacy observation timeout must not affect this variant.
        request.observation_timeout_secs = 0;
        let invocation = request.invocation().unwrap();
        assert_eq!(invocation.executable, PathBuf::from("python3"));
        assert_eq!(invocation.current_dir, Some(PathBuf::from("/source")));
        assert_eq!(
            invocation.arguments,
            [
                "-m",
                "x86.recovery_supervisor",
                "--qemu",
                "/qemu tools/qemu-system-aarch64",
                "--qemu-img",
                "/qemu tools/qemu-img",
                "--firmware",
                "/inputs/AVPBooter.bin",
                "--build-manifest",
                "/inputs/BuildManifest.plist",
                "--tss-helper",
                "/helper tools/request-encoder",
                "--original-ibss",
                "/inputs/original iBSS.im4p",
                "--original-ibec",
                "/inputs/original iBEC.im4p",
                "--restore-role-dir",
                "/inputs/restore roles",
                "--memory-mib",
                "4096",
                "--smp",
                "2",
                "--transition-timeout",
                "20",
                "--restore-timeout",
                "30",
                "--total-timeout",
                "75",
                "--cleanup-grace",
                "5",
                "--target",
                "27",
                "--vm-json",
                "/input/my bundle/macosvm.json",
                "--output",
                "/output/new-run",
                "--duration",
                "10",
            ]
        );
        if let RunnerBackend::TcgRecovery {
            optional_rpc_unavailable,
            ..
        } = &mut request.backend
        {
            *optional_rpc_unavailable = true;
        }
        let args = request.invocation().unwrap().arguments;
        assert_eq!(
            args.iter()
                .filter(|arg| *arg == "--optional-rpc-unavailable")
                .count(),
            1
        );
        for absent in [
            "run-tcg",
            "--firmware-kind",
            "--observation-timeout",
            "--json",
            "--research-only",
        ] {
            assert!(!args.iter().any(|arg| arg == absent));
        }
    }

    #[test]
    fn recovery_request_rejects_bad_paths_and_inconsistent_budgets_before_io() {
        let base = serde_json::to_value(recovery_request()).unwrap();
        for pointer in [
            "/repository",
            "/vm_json",
            "/output",
            "/host_receipt_dir",
            "/host/python",
            "/backend/qemu",
            "/backend/qemu_img",
            "/backend/firmware",
            "/backend/build_manifest",
            "/backend/tss_helper",
            "/backend/original_ibss",
            "/backend/original_ibec",
            "/backend/restore_role_dir",
        ] {
            for value in ["", "bad\0path"] {
                let mut input = base.clone();
                *input.pointer_mut(pointer).unwrap() = value.into();
                let request: RunnerRequest = serde_json::from_value(input).unwrap();
                assert!(request.invocation().is_err(), "accepted {pointer}");
            }
        }
        for (pointer, value) in [
            ("/backend/memory_mib", 511),
            ("/backend/memory_mib", 1048577),
            ("/backend/smp", 0),
            ("/backend/smp", 33),
            ("/backend/transition_timeout_secs", 0),
            ("/backend/transition_timeout_secs", 301),
            ("/backend/restore_timeout_secs", 0),
            ("/backend/restore_timeout_secs", 301),
            ("/backend/total_timeout_secs", 29),
            ("/backend/total_timeout_secs", 86401),
            ("/duration_secs", 70),
            ("/duration_secs", 0),
        ] {
            let mut input = base.clone();
            *input.pointer_mut(pointer).unwrap() = value.into();
            let request: RunnerRequest = serde_json::from_value(input).unwrap();
            assert!(request.invocation().is_err(), "accepted {pointer}={value}");
        }
        let mut request = recovery_request();
        request.duration_secs = 69;
        assert!(request.invocation().is_ok());
        request.research_only = false;
        assert!(request.invocation().is_err());
    }

    #[test]
    fn recovery_bootx_and_zero_worker_exit_preserve_progress_but_not_boot() {
        let report = recovery_receipt();
        let outcome = evaluate_report(&recovery_request(), Some(0), Ok(report.clone()));
        assert!(
            outcome.runner_completed
                && outcome.guest_runtime_started
                && outcome.guest_process_terminated
        );
        assert!(outcome.input_integrity);
        assert!(
            !outcome.xnu_executed
                && !outcome.macos_userspace_reached
                && !outcome.macos_boot_verified
        );
        let progress = outcome.recovery_progress.unwrap();
        assert!(progress.dfu_upload_completed && progress.ibec_endpoint_advertised);
        assert!(progress.stage2_banner_observed && progress.stage2_prompt_observed);
        assert!(progress.restore_sequence_sent && progress.bootx_acknowledged);
        assert_eq!(progress.restore_role_step_count, 4);
        assert_eq!(outcome.report, Some(report));
        assert_eq!(outcome.engine, "qemu-vmapple-recovery");
    }

    #[test]
    fn recovery_rejects_mismatched_envelope_and_raw_launch_identity() {
        let base = recovery_receipt();
        for (pointer, value) in [
            ("/schema", serde_json::json!("26x86.vmapple-tcg/1")),
            ("/target_major", serde_json::json!(26)),
            ("/requested_output", serde_json::json!("/different-request")),
            ("/output", serde_json::json!("/different-run")),
            (
                "/launch_report/raw_schema",
                serde_json::json!("26x86.vmapple-tcg/1"),
            ),
            ("/launch_report/identity_valid", serde_json::json!(false)),
            ("/launch_report/raw/schema", serde_json::json!("wrong")),
            ("/launch_report/raw/target_major", serde_json::json!(26)),
            (
                "/launch_report/raw/output",
                serde_json::json!("/different-run"),
            ),
            (
                "/launch_report/raw/machine_type",
                serde_json::json!("x86_64"),
            ),
            ("/launch_report/raw/personality", serde_json::json!("other")),
            ("/launch_report/raw/guest_os", serde_json::json!("iOS")),
            (
                "/launch_report/raw/boot_mode",
                serde_json::json!("direct-macos"),
            ),
            ("/launch_report/raw/runtime_started", serde_json::json!(1)),
            ("/launch_report/raw/pid", serde_json::Value::Null),
        ] {
            let mut report = base.clone();
            *report.pointer_mut(pointer).unwrap() = value;
            let outcome = evaluate_report(&recovery_request(), Some(0), Ok(report));
            assert!(!outcome.guest_runtime_started, "accepted {pointer}");
            assert!(!outcome.guest_process_terminated && !outcome.macos_boot_verified);
            assert_eq!(outcome.recovery_progress, Some(RecoveryProgress::default()));
        }
    }

    #[test]
    fn recovery_correlates_relative_request_with_canonical_linux_output() {
        let mut request = recovery_request();
        request.output = "runs/../result".into();
        let mut report = recovery_receipt();
        report["requested_output"] = "runs/../result".into();
        report["output"] = "/source/result".into();
        report["launch_report"]["raw"]["output"] = "/source/result".into();
        report["launch_report"]["path"] = "/source/result/launch.json".into();
        let outcome = evaluate_report(&request, Some(0), Ok(report.clone()));
        assert!(outcome.guest_runtime_started && outcome.guest_process_terminated);
        assert!(!outcome.macos_boot_verified);
        report["requested_output"] = Value::Null;
        assert!(!evaluate_report(&request, Some(0), Ok(report.clone())).guest_runtime_started);
        report["requested_output"] = "runs/../result".into();
        for output in [Value::Null, serde_json::json!("relative-only")] {
            report["output"] = output.clone();
            report["launch_report"]["raw"]["output"] = output;
            assert!(!evaluate_report(&request, Some(0), Ok(report.clone())).guest_runtime_started);
        }
    }

    #[test]
    fn recovery_requires_a_unique_observed_qemu_identity_in_the_worker_session() {
        let base = strict_recovery_receipt();
        for (pointer, value) in [
            (
                "/worker/process_inventory_complete",
                serde_json::json!(false),
            ),
            (
                "/launch_report/runtime_pid_observed",
                serde_json::json!(false),
            ),
            ("/worker/observed_processes", Value::Null),
            ("/worker/observed_processes", serde_json::json!([])),
            (
                "/worker/observed_processes/1/starttime",
                serde_json::json!(0),
            ),
            (
                "/worker/observed_processes/1/session",
                serde_json::json!(999),
            ),
            ("/worker/observed_processes/1/pid", serde_json::json!(999)),
            ("/worker/pid", Value::Null),
            ("/launch_report/raw/pid", serde_json::json!(12)),
            ("/launch_report/raw/pid", serde_json::json!(999)),
        ] {
            let mut report = base.clone();
            *report.pointer_mut(pointer).unwrap() = value;
            let outcome = evaluate_report(&recovery_request(), Some(0), Ok(report));
            assert!(!outcome.guest_runtime_started, "accepted {pointer}");
            assert!(
                !outcome.guest_process_terminated
                    && !outcome.xnu_executed
                    && !outcome.macos_boot_verified
            );
        }
        let mut reused = base;
        reused["worker"]["observed_processes"]
            .as_array_mut()
            .unwrap()
            .push(serde_json::json!({"pid":13,"starttime":120,"session":12}));
        assert!(!evaluate_report(&recovery_request(), Some(0), Ok(reused)).guest_runtime_started);
    }

    #[test]
    fn recovery_transport_loss_and_missing_cleanup_never_confirm_linux_exit() {
        for parsed in [
            Err("WSL transport closed".into()),
            Ok(Value::Null),
            Ok(serde_json::json!([])),
            Ok(serde_json::json!({"error":"supervisor unavailable"})),
        ] {
            let outcome = evaluate_report(&recovery_request(), Some(0), parsed);
            assert!(!outcome.guest_process_terminated && !outcome.macos_boot_verified);
        }
        for (pointer, value) in [
            ("/cleanup/complete", Value::Null),
            ("/cleanup/complete", serde_json::json!(false)),
            ("/cleanup/leader_reaped", serde_json::json!(false)),
            ("/cleanup/remaining_pids", Value::Null),
            ("/cleanup/remaining_pids", serde_json::json!([42])),
            ("/cleanup/remaining_pids", serde_json::json!({})),
        ] {
            let mut report = recovery_receipt();
            *report.pointer_mut(pointer).unwrap() = value;
            let outcome = evaluate_report(&recovery_request(), Some(0), Ok(report));
            assert!(outcome.guest_runtime_started);
            assert!(
                !outcome.guest_process_terminated && !outcome.macos_boot_verified,
                "accepted {pointer}"
            );
        }
    }

    #[test]
    fn recovery_counts_completed_distinct_roles_and_preserves_post_bootx_panic() {
        let mut report = recovery_receipt();
        let steps = report["launch_report"]["raw"]["restore_chain"]["steps"]
            .as_array_mut()
            .unwrap();
        steps[3]["upload"]["transfer_complete"] = false.into();
        steps.push(steps[0].clone());
        let outcome = evaluate_report(&recovery_request(), Some(0), Ok(report.clone()));
        let progress = outcome.recovery_progress.unwrap();
        assert_eq!(progress.restore_role_step_count, 3);
        assert!(!progress.restore_sequence_sent);
        report["launch_report"]["raw"]["restore_chain"]["post_bootx_panic"] = true.into();
        let outcome = evaluate_report(&recovery_request(), Some(0), Ok(report));
        assert!(outcome.recovery_progress.unwrap().firmware_panic_observed);
        assert!(!outcome.macos_boot_verified);
    }

    #[test]
    fn recovery_strict_future_evidence_requires_causality_integrity_and_clean_completion() {
        let base = strict_recovery_receipt();
        assert!(
            evaluate_report(&recovery_request(), Some(0), Ok(base.clone())).macos_boot_verified
        );
        for (pointer, value) in [
            ("/launch_report/raw/observed_markers", Value::Null),
            ("/boot/macos_boot_verified", serde_json::json!(false)),
            ("/boot/target_match", serde_json::json!(false)),
            ("/boot/guest_kernel_major", serde_json::json!(26)),
            ("/input_integrity/unchanged", Value::Null),
            ("/worker/completed", serde_json::json!(false)),
            ("/worker/returncode", serde_json::json!(2)),
            ("/launch_report/complete", serde_json::json!(false)),
            ("/deadline/exceeded", serde_json::json!(true)),
            ("/cancel/requested", serde_json::json!(true)),
            (
                "/launch_report/raw/guest_panic/observed",
                serde_json::json!(true),
            ),
            (
                "/launch_report/raw/input_integrity",
                serde_json::json!(false),
            ),
            (
                "/launch_report/raw/guest_kernel_major",
                serde_json::json!(26),
            ),
            (
                "/launch_report/raw/observed_markers/xnu/0/kernel_major",
                serde_json::json!(26),
            ),
            (
                "/launch_report/raw/observed_markers/userspace/0/byte_offset",
                serde_json::json!(50),
            ),
            (
                "/launch_report/raw/stage2/byte_offset",
                serde_json::json!(150),
            ),
            (
                "/launch_report/raw/iboot_xnu_handoff/claims/macos_boot_verified",
                serde_json::json!(false),
            ),
            (
                "/launch_report/raw/restore_chain/bootx_acknowledged",
                serde_json::json!(false),
            ),
        ] {
            let mut report = base.clone();
            *report.pointer_mut(pointer).unwrap() = value;
            assert!(
                !evaluate_report(&recovery_request(), Some(0), Ok(report)).macos_boot_verified,
                "accepted {pointer}"
            );
        }
        for exit in [None, Some(1), Some(2)] {
            assert!(
                !evaluate_report(&recovery_request(), exit, Ok(base.clone())).macos_boot_verified
            );
        }
    }

    #[test]
    #[cfg(windows)]
    fn recovery_wsl_uses_explicit_linux_supervisor_without_shell() {
        let mut request = recovery_request();
        request.host = RunnerHost::Wsl {
            distribution: "Ubuntu-24.04".into(),
            python: "/usr/bin/python3".into(),
        };
        let invocation = request.invocation().unwrap();
        assert_eq!(invocation.executable, PathBuf::from("wsl.exe"));
        assert!(invocation.current_dir.is_none());
        assert_eq!(
            &invocation.arguments[..8],
            [
                "--distribution",
                "Ubuntu-24.04",
                "--cd",
                "/source",
                "--exec",
                "/usr/bin/python3",
                "-m",
                "x86.recovery_supervisor"
            ]
        );
    }
}
