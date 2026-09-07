"""BP15 Linux host supervisor; it does not implement a guest boot protocol.

The worker plus cleanup share one monotonic total_timeout deadline. Preflight
hashing has a separate 20 second budget; post-run hashing AND evidence storage
share another 20 seconds. Thus the declared overall budget is total + 40, not
the sum of the worker's phase timers. Blocking kernel syscalls/process creation
and SIGKILL of this supervisor cannot be given a userspace cleanup guarantee.

Ownership is the new Linux session, including children in different process
groups. Daemons that deliberately leave that session are outside this contract.
PID/starttime/session are checked before pidfd signalling; unrelated children
are never waited for with waitpid(-1). PR_SET_CHILD_SUBREAPER allows adoption of
orphaned members after the worker leader exits. All three catchable outer stop
signals follow the same cleanup path as timeout and the output/stop file.

Public API references (independent implementation, no private helper imports):
https://docs.python.org/3/library/subprocess.html
https://docs.python.org/3/library/signal.html
https://www.man7.org/linux/man-pages/man5/proc_pid_stat.5.html
https://www.man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any

SCHEMA = "nextcore.recovery-supervisor/1"
RAW_SCHEMA = "26x86.vmapple-gui/1"
CAPTURE_LIMIT = 4 * 1024 * 1024
ENVELOPE_LIMIT = 8 * 1024 * 1024
INTEGRITY_BUDGET = 20.0
RESTORE_BOOT_ARGS = "rd=md0 nand-enable-reformat=1 -progress -restore"
REMOVED_ENVIRONMENT = (
    "VENFIRE_RESTORE_BOOT_ARGS", "VENFIRE_EXTRA_TRACE",
    "X86_VMAPLE_IPSW", "X86_VMAPLE_PROVISION_OUTPUT", "X86_VMAPLE_JSON",
    "X86_VMAPLE_OUTPUT", "X86_VMAPLE_OUTPUT_ROOT", "X86_VMAPLE_QEMU",
    "X86_VMAPLE_QEMU_IMG", "X86_VMAPLE_AVPBOOTER", "X86_VMAPLE_AUX_SEED",
    "X86_VMAPLE_ROOT_SEED", "X86_VMAPLE_AUX", "X86_VMAPLE_ROOT",
    "X86_VMAPLE_IBSS", "X86_VMAPLE_IBEC", "X86_VMAPLE_BUILD_MANIFEST",
    "X86_VMAPLE_TSS_HELPER", "X86_VMAPLE_ORIGINAL_IBSS",
    "X86_VMAPLE_ORIGINAL_IBEC", "X86_VMAPLE_RESTORE_ROLE_DIR",
)
REQUIRED_ROLES = (
    "RestoreTrustCache.im4p", "RestoreRamDisk.im4p",
    "RestoreDeviceTree.im4p", "RestoreKernelCache.im4p",
)
PATH_OPTIONS = (
    "qemu", "qemu_img", "firmware", "vm_json", "output", "build_manifest",
    "tss_helper", "original_ibss", "original_ibec", "restore_role_dir",
)
VALUE_OPTIONS = (
    "target", "qemu", "qemu_img", "firmware", "vm_json", "build_manifest",
    "tss_helper", "original_ibss", "original_ibec", "restore_role_dir",
    "memory_mib", "smp", "transition_timeout", "restore_timeout", "duration",
    "output",
)


def worker_environment(inherited: dict[str, str]) -> tuple[dict[str, str], dict]:
    env = {k: v for k, v in inherited.items() if k not in REMOVED_ENVIRONMENT}
    # No original values or whole-environment dump in the receipt.
    return env, {
        "removed_names": list(REMOVED_ENVIRONMENT),
        "effective": {
            "restore_boot_args": RESTORE_BOOT_ARGS, "extra_trace": "default",
            "legacy_optional_inputs": "unset", "explicit_inputs": "argv",
        },
    }


def worker_argv(request: argparse.Namespace) -> list[str]:
    argv = [sys.executable, "-m", "x86", "vmapple", "run"]
    for key in VALUE_OPTIONS:
        argv.extend(["--" + key.replace("_", "-"), str(getattr(request, key))])
    argv.extend([
        "--boot-selection", "recovery", "--no-boot-picker", "--display", "none",
        "--live-personalize", "--restore-chain", "--research-only", "--json",
    ])
    if request.optional_rpc_unavailable:
        argv.append("--optional-rpc-unavailable")
    return argv


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Argument values may contain private data: return a fixed category.
        raise ValueError("invalid CLI arguments")


def parse_request(argv: list[str]) -> argparse.Namespace:
    parser = JsonArgumentParser(add_help=False, allow_abbrev=False)
    for key in PATH_OPTIONS:
        parser.add_argument("--" + key.replace("_", "-"), required=True)
    parser.add_argument("--target", type=int, choices=(26, 27), required=True)
    for key in ("memory_mib", "smp"):
        parser.add_argument("--" + key.replace("_", "-"), type=int, required=True)
    for key in ("transition_timeout", "restore_timeout", "duration", "total_timeout"):
        parser.add_argument("--" + key.replace("_", "-"), type=float, required=True)
    parser.add_argument("--cleanup-grace", type=float, default=5.0)
    parser.add_argument("--optional-rpc-unavailable", action="store_true")
    args = parser.parse_args(argv)
    limits = {
        "memory_mib": (512, 1048576), "smp": (1, 32),
        "total_timeout": (30, 86400), "cleanup_grace": (1, 30),
    }
    for name, (low, high) in limits.items():
        value = getattr(args, name)
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError("numeric option outside supported range")
    for name, low, high in (("transition_timeout", 1, 300), ("restore_timeout", 1, 300), ("duration", 1, 86400)):
        value = getattr(args, name)
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError("recovery phase timeouts must be 1..300 seconds; post duration 1..86400")
    if args.total_timeout <= args.duration + args.cleanup_grace:
        raise ValueError("total timeout must exceed duration plus cleanup grace")
    for key in PATH_OPTIONS:
        value = getattr(args, key)
        if not value.strip() or "\0" in value:
            raise ValueError("empty or invalid path")
    return args


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    starttime: int
    session: int


def process_identity(pid: int) -> ProcessIdentity | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_bytes()
    except (FileNotFoundError, ProcessLookupError):
        return None
    # comm may itself contain spaces or closing parentheses.
    fields = raw[raw.rfind(b")") + 2:].split()
    return ProcessIdentity(pid, int(fields[19]), int(fields[3]))


def session_members(leader: ProcessIdentity) -> list[ProcessIdentity]:
    members = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            identity = process_identity(int(entry.name))
            if (identity is not None and identity.session == leader.session
                    and identity.starttime >= leader.starttime
                    and identity.pid != os.getpid()):
                members.append(identity)
    return members


def signal_member(identity: ProcessIdentity, signum: int) -> bool:
    if identity.pid == os.getpid() or process_identity(identity.pid) != identity:
        return False
    try:
        fd = os.pidfd_open(identity.pid)
    except ProcessLookupError:
        return False
    try:
        if process_identity(identity.pid) != identity:
            return False
        signal.pidfd_send_signal(fd, signum)
        return True
    except ProcessLookupError:
        return False
    finally:
        os.close(fd)


@dataclass
class Cancellation:
    requested: bool = False
    reason: str | None = None
    signal: int | None = None

    def handle(self, signum, _frame):
        self.requested = True
        self.reason = "signal"
        self.signal = signum


@dataclass
class Capture:
    data: bytearray = field(default_factory=bytearray)
    digest: Any = field(default_factory=hashlib.sha256)
    observed: int = 0
    eof: bool = False

    def add(self, data: bytes):
        self.digest.update(data)
        self.observed += len(data)
        self.data.extend(data[:max(0, CAPTURE_LIMIT - len(self.data))])

    def receipt(self) -> dict:
        return {
            "path": None, "sha256": self.digest.hexdigest(),
            "bytes_observed": self.observed, "bytes_saved": 0,
            "truncated": self.observed > len(self.data),
            "complete": False, "capture_complete": self.eof,
            "sha256_scope": "all_observed_bytes",
            "saved_sha256": None,
        }


def _touch_stop(output: Path | None) -> bool:
    if output is None:
        return False
    try:
        fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            stop_fd = os.open("stop", os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                              0o600, dir_fd=fd)
            os.close(stop_fd)
        finally:
            os.close(fd)
        return True
    except FileExistsError:
        return True
    except OSError:
        return False


def run_owned(argv: list[str], *, env: dict[str, str], output: Path | None,
              total_timeout: float, cleanup_grace: float,
              cancel: Cancellation) -> tuple[dict, Capture, Capture]:
    """Internal small-timeout seam also used by authored process tests.

    The public CLI separately enforces 30..86400 and duration+grace validation.
    This function never reads report contents or trusts worker cleanup claims.
    """
    started = time.monotonic()
    end = started + total_timeout
    work_end = end - cleanup_grace
    captures = (Capture(), Capture())
    result = {
        "pid": None, "returncode": None, "completed": False, "error": None,
        "deadline_exceeded": False, "elapsed_seconds": 0.0,
        "observed_processes": [], "process_inventory_complete": True,
        "cleanup": {"leader_reaped": False, "remaining_pids": [], "complete": False,
                    "scan_complete": False, "cooperative_stop": False},
    }
    if (sys.platform != "linux" or not hasattr(os, "pidfd_open")
            or not hasattr(signal, "pidfd_send_signal")):
        result["error"] = "linux-pidfd-required"
        return result, *captures
    libc = ctypes.CDLL(None, use_errno=True)
    old_subreaper = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(old_subreaper), 0, 0, 0) != 0:
        result["error"] = "subreaper-query-failed"
        return result, *captures
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        result["error"] = "subreaper-enable-failed"
        return result, *captures
    process = None
    leader = None
    selector = selectors.DefaultSelector()
    cleanup_start = None
    cleanup_end = None
    observed: dict[ProcessIdentity, None] = {}
    scan_ok = True
    members: list[ProcessIdentity] = []

    def refresh():
        nonlocal members, scan_ok
        if leader is None:
            scan_ok = False
            return
        try:
            members = session_members(leader)
            for member in members:
                if member not in observed:
                    if len(observed) < 4096:
                        observed[member] = None
                    else:
                        result["process_inventory_complete"] = False
            # Only reap known identities; never consume an unrelated child's status.
            for member in members:
                if member.pid != process.pid and process_identity(member.pid) == member:
                    try:
                        os.waitpid(member.pid, os.WNOHANG)
                    except ChildProcessError:
                        pass
            process.poll()
            members = session_members(leader)
        except (OSError, ValueError, IndexError):
            scan_ok = False

    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=env, start_new_session=True, close_fds=True)
        result["pid"] = process.pid
        leader = process_identity(process.pid)
        if leader is None or leader.session != process.pid:
            raise RuntimeError("worker-session-unconfirmed")
        for stream, capture in zip((process.stdout, process.stderr), captures):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, capture)
        while time.monotonic() < end:
            now = time.monotonic()
            refresh()
            if output is not None and (output / "stop").exists() and cleanup_start is None:
                cancel.requested, cancel.reason = True, "stop-file"
            if cleanup_start is None:
                if now >= work_end:
                    result["deadline_exceeded"] = True
                if process.returncode is not None or cancel.requested or now >= work_end:
                    cleanup_start = now
                    cleanup_end = min(end, now + cleanup_grace)
                    result["cleanup"]["cooperative_stop"] = _touch_stop(output)
            if cleanup_start is not None:
                span = cleanup_end - cleanup_start
                age = now - cleanup_start
                signum = (signal.SIGKILL if age >= span * 0.6 else
                          signal.SIGTERM if age >= span * 0.2 else None)
                if signum is not None:
                    for member in members:
                        try:
                            signal_member(member, signum)
                        except OSError:
                            scan_ok = False
                if not members and process.returncode is not None and not selector.get_map():
                    break
                if now >= cleanup_end:
                    break
            # Drain without unbounded communicate(), including TERM/KILL phases.
            pause = min(0.04, max(0.0, end - time.monotonic()))
            for key, _events in selector.select(pause):
                try:
                    data = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if data:
                    key.data.add(data)
                else:
                    key.data.eof = True
                    selector.unregister(key.fileobj)
    except Exception as error:
        result["error"] = type(error).__name__
    finally:
        # Even a scan/pipe exception cannot skip the owned cleanup path.
        if process is not None and leader is not None:
            refresh()
            if members:
                result["cleanup"]["cooperative_stop"] |= _touch_stop(output)
                if cleanup_start is None:
                    cleanup_start = time.monotonic()
                    cleanup_end = min(end, cleanup_start + cleanup_grace)
                while time.monotonic() < cleanup_end:
                    refresh()
                    if not members and process.returncode is not None:
                        break
                    age = time.monotonic() - cleanup_start
                    span = cleanup_end - cleanup_start
                    signum = (signal.SIGKILL if age >= span * 0.6 else
                              signal.SIGTERM if age >= span * 0.2 else None)
                    if signum is not None:
                        for member in members:
                            try:
                                signal_member(member, signum)
                            except OSError:
                                scan_ok = False
                    time.sleep(min(0.01, max(0.0, cleanup_end - time.monotonic())))
            refresh()
            result["returncode"] = process.returncode
            result["completed"] = process.returncode is not None
            result["cleanup"].update({
                "leader_reaped": process.returncode is not None,
                "remaining_pids": sorted(member.pid for member in members),
                "scan_complete": scan_ok,
                "complete": scan_ok and not members and process.returncode is not None,
            })
        # Read any final buffered bytes without waiting on escaped pipe holders.
        for key in list(selector.get_map().values()):
            while time.monotonic() < end:
                try:
                    data = os.read(key.fileobj.fileno(), 65536)
                except (BlockingIOError, OSError):
                    break
                if not data:
                    key.data.eof = True
                    break
                key.data.add(data)
        selector.close()
        if process is not None:
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        libc.prctl(36, old_subreaper.value, 0, 0, 0)
        result["elapsed_seconds"] = time.monotonic() - started
        result["observed_processes"] = [vars(identity) for identity in observed]
    return result, *captures


def resolve_inputs(request: argparse.Namespace) -> list[dict]:
    """Snapshot declared original inputs; VM identity blobs are inside VM JSON."""
    output = Path(request.output).expanduser().absolute()
    if os.path.lexists(output):
        raise ValueError("output must not exist")
    # Require its parent to exist, so no worker-visible output is pre-created.
    output = output.parent.resolve(strict=True) / output.name
    if not output.parent.is_dir():
        raise ValueError("output parent must be a directory")
    request.output = str(output)
    records = []
    for name in PATH_OPTIONS:
        if name in ("output", "restore_role_dir"):
            continue
        value = getattr(request, name)
        if name in ("qemu", "qemu_img", "tss_helper") and not Path(value).is_absolute():
            value = shutil.which(value) or value
        path = Path(value).expanduser().resolve(strict=True)
        if not path.is_file():
            raise ValueError("input must be a regular file")
        setattr(request, name, str(path))
        records.append({"role": name, "path": str(path)})
    bundle = Path(request.vm_json)
    with bundle.open("rb") as stream:
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("VM JSON exceeds limit")
    document = json.loads(data)
    storage = document.get("storage") if isinstance(document, dict) else None
    if not isinstance(storage, list) or len(storage) > 32:
        raise ValueError("VM JSON storage must be an array of at most 32 entries")
    counts = {"aux": 0, "disk": 0}
    for item in storage:
        if (not isinstance(item, dict) or not isinstance(item.get("type"), str)
                or not isinstance(item.get("file"), str) or not item["file"].strip()):
            raise ValueError("invalid VM storage entry")
        path = (bundle.parent / item["file"]).resolve(strict=True)
        if not path.is_file():
            raise ValueError("VM storage must be a regular file")
        if item["type"] in counts:
            counts[item["type"]] += 1
        # Only AUX/root are consumed; unrecognized entries are validated by the
        # worker but are not original guest inputs in this adapter contract.
        if item["type"] in counts:
            records.append({"role": "vm_storage_" + item["type"], "path": str(path)})
    if counts != {"aux": 1, "disk": 1}:
        raise ValueError("exactly one AUX and root disk required")
    roles = Path(request.restore_role_dir).expanduser().resolve(strict=True)
    if not roles.is_dir():
        raise ValueError("restore role directory required")
    request.restore_role_dir = str(roles)
    for parent in (bundle.parent, roles):
        if output == parent or parent in output.parents:
            raise ValueError("output must be outside original bundle and restore roles")
    for name in (*REQUIRED_ROLES, "RestoreLogo.im4p"):
        path = roles / name
        if name == "RestoreLogo.im4p" and not path.exists():
            continue
        path = path.resolve(strict=True)
        if not path.is_file():
            raise ValueError("restore role must be a regular file")
        records.append({"role": name, "path": str(path)})
    return records


def _file_fingerprint(path: str) -> dict:
    try:
        with open(path, "rb", buffering=0) as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                return {"status": "not-regular", "sha256": None}
            digest = hashlib.sha256()
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if identity(before) != identity(after):
            return {"status": "changed-during-read", "sha256": None}
        return {"status": "complete", "sha256": digest.hexdigest(),
                "bytes": after.st_size, "device": after.st_dev, "inode": after.st_ino,
                "mtime_ns": after.st_mtime_ns, "ctime_ns": after.st_ctime_ns}
    except OSError:
        return {"status": "io-error", "sha256": None}


def _hash_worker():
    records = json.loads(sys.argv[1])
    print(json.dumps([_file_fingerprint(record["path"]) for record in records]))


def hash_inputs(records: list[dict], deadline: float, env: dict[str, str],
                cancel: Cancellation, *, helper_receipt: dict | None = None) -> tuple[list[dict], bool]:
    if helper_receipt is not None:
        helper_receipt.update(pid=None, returncode=None,
                              cleanup={"complete": True, "remaining_pids": []})
    remaining = deadline - time.monotonic()
    if remaining <= 0.1:
        return [{"status": "timeout", "sha256": None} for _ in records], False
    argv = [sys.executable, "-c",
            "from x86.recovery_supervisor import _hash_worker; _hash_worker()",
            json.dumps(records)]
    # The file-reading helper can be killed when a filesystem read stalls.
    result, stdout, _stderr = run_owned(
        argv, env=env, output=None, total_timeout=remaining,
        cleanup_grace=min(1.0, remaining / 5), cancel=cancel)
    if helper_receipt is not None:
        helper_receipt.update({key: result[key] for key in ("pid", "returncode", "cleanup")})
    try:
        values = json.loads(stdout.data)
        if (result["returncode"] == 0 and result["cleanup"]["complete"]
                and stdout.eof and len(values) == len(records)
                and all(isinstance(value, dict) for value in values)):
            return values, True
    except (ValueError, TypeError):
        pass
    return [{"status": "unavailable", "sha256": None} for _ in records], False


def _save_capture(capture: Capture, output: Path, name: str, deadline: float) -> dict:
    receipt = capture.receipt()
    try:
        if time.monotonic() >= deadline:
            return receipt
        output.mkdir(mode=0o700, exist_ok=True)
        directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
        finally:
            os.close(directory)
        saved = hashlib.sha256()
        receipt["path"] = str(output / name)
        with os.fdopen(fd, "wb", buffering=0) as stream:
            offset = 0
            while offset < len(capture.data) and time.monotonic() < deadline:
                chunk = capture.data[offset:offset + 65536]
                written = stream.write(chunk)
                if not written:
                    break
                saved.update(chunk[:written])
                offset += written
                receipt["bytes_saved"] = offset
                receipt["saved_sha256"] = saved.hexdigest()
        receipt["saved_sha256"] = saved.hexdigest()
        receipt["complete"] = (capture.eof and not receipt["truncated"]
                               and offset == len(capture.data))
    except OSError:
        receipt["storage_error"] = True
    return receipt


def read_launch(output: Path, target: int, deadline: float) -> dict:
    path = output / "launch.json"
    receipt = {"path": str(path), "sha256": None, "complete": False,
               "raw_schema": None, "identity_valid": False, "raw": None}
    if time.monotonic() >= deadline:
        return receipt
    try:
        directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open("launch.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
        finally:
            os.close(directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                return receipt
            data = stream.read(CAPTURE_LIMIT + 1)
            after = os.fstat(stream.fileno())
        receipt["bytes"] = before.st_size
        receipt["hash_complete"] = len(data) == before.st_size <= CAPTURE_LIMIT
        digest = hashlib.sha256(data).hexdigest()
        if receipt["hash_complete"]:
            receipt["sha256"] = digest
        else:
            receipt["prefix_sha256"] = digest
        if (not receipt["hash_complete"] or before.st_mtime_ns != after.st_mtime_ns
                or before.st_size != after.st_size or time.monotonic() >= deadline):
            return receipt
        raw = json.loads(data, parse_constant=_reject_json_constant)
        if not isinstance(raw, dict):
            return receipt
        receipt.update(raw=raw, raw_schema=raw.get("schema"), complete=True)
        receipt["identity_valid"] = (
            raw.get("schema") == RAW_SCHEMA and raw.get("target_major") == target
            and raw.get("machine_type") == "iBoot(AArch64)"
            and raw.get("personality") == "iBoot" and raw.get("guest_os") == "macOS"
            and raw.get("boot_mode") == "recovery" and raw.get("output") == str(output))
    except (OSError, ValueError, RecursionError):
        pass
    return receipt


def _reject_json_constant(_value):
    raise ValueError("non-finite JSON number")


def serialize_envelope(envelope: dict) -> str:
    # ASCII JSON safely transports escaped lone surrogates from a malformed
    # worker string. UTF-8 strings can expand when escaped; cap the envelope
    # separately from the 4 MiB original launch-file cap.
    encoded = json.dumps(envelope, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    if len(encoded) > ENVELOPE_LIMIT:
        envelope["launch_report"]["raw"] = None
        envelope["launch_report"]["complete"] = False
        envelope["launch_report"]["identity_valid"] = False
        envelope["launch_report"]["runtime_pid_observed"] = False
        envelope["launch_report"]["omitted_reason"] = "envelope-size-limit"
        envelope["recovery_progress"] = recovery_progress({})
        encoded = json.dumps(envelope, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    if len(encoded) > ENVELOPE_LIMIT:
        # This cannot arise from the bounded supported input manifest, but the
        # JSON transport still fails closed if this internal API is misused.
        failure = empty_envelope()
        failure["error"] = "envelope-size-limit"
        encoded = json.dumps(failure, separators=(",", ":"))
    return encoded


def correlate_runtime(launch: dict, worker: dict) -> None:
    raw = launch.get("raw")
    pid = raw.get("pid") if isinstance(raw, dict) else None
    matches = [entry for entry in worker.get("observed_processes", [])
               if entry.get("pid") == pid and entry.get("session") == worker.get("pid")
               and isinstance(entry.get("starttime"), int) and entry["starttime"] > 0]
    launch["runtime_pid_observed"] = (
        launch.get("identity_valid") is True and type(pid) is int and pid > 0
        and pid != worker.get("pid") and len(matches) == 1
        and worker.get("process_inventory_complete") is True)


def recovery_progress(launch: dict) -> dict:
    raw = launch.get("raw") if (launch.get("identity_valid")
                               and launch.get("runtime_pid_observed")) else None
    raw = raw if isinstance(raw, dict) else {}
    if raw.get("runtime_started") is not True:
        raw = {}
    def part(key):
        value = raw.get(key)
        return value if isinstance(value, dict) else {}
    restore = part("restore_chain")
    steps = restore.get("steps")
    roles = {name.removesuffix(".im4p") for name in (*REQUIRED_ROLES, "RestoreLogo.im4p")}
    uploaded = set()
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict) or not isinstance(step.get("role"), str):
                continue
            upload = step.get("upload")
            if (step["role"] in roles and isinstance(upload, dict)
                    and upload.get("transfer_complete") is True):
                uploaded.add(step["role"])
    return {
        "runtime_started": raw.get("runtime_started") is True,
        "dfu_upload_completed": part("dfu_upload").get("transfer_complete") is True,
        "ibec_ready": part("transition").get("state") == "ibec-ready",
        "stage2_banner_observed": part("stage2").get("stage2_serial_started") is True,
        "stage2_prompt_observed": part("stage2").get("observed") is True,
        "restore_role_step_count": len(uploaded),
        "restore_sequence_sent": restore.get("sequence_sent") is True,
        "bootx_acknowledged": restore.get("bootx_acknowledged") is True,
        "firmware_panic_observed": part("guest_panic").get("observed") is True,
    }


def empty_envelope() -> dict:
    return {
        "schema": SCHEMA, "supervisor_pid": os.getpid(), "target_major": None,
        "output": None, "requested_output": None, "error": None, "elapsed_seconds": 0.0,
        "worker": {"pid": None, "returncode": None, "completed": False},
        "deadline": {}, "cancel": {"requested": False, "reason": None, "signal": None},
        "cleanup": {"leader_reaped": False, "remaining_pids": [], "complete": False},
        "input_integrity": {"unchanged": None, "records": []},
        "worker_stdout": Capture().receipt(), "worker_stderr": Capture().receipt(),
        "launch_report": {"path": None, "sha256": None, "complete": False,
                          "raw_schema": None, "raw": None, "identity_valid": False,
                          "runtime_pid_observed": False},
        "recovery_progress": recovery_progress({}),
        "boot": {"xnu_executed": False, "guest_kernel_major": None,
                 "target_match": False, "userspace": False, "macos_boot_verified": False},
        "limitations": ["supervisor-SIGKILL-cleanup-not-guaranteed",
                        "owned-session-only-no-daemon-escape-guarantee",
                        "blocking-kernel-syscall-latency-not-guaranteed"],
    }


def supervise(request: argparse.Namespace, *, cancel: Cancellation | None = None) -> dict:
    started = time.monotonic()
    cancel = cancel or Cancellation()
    envelope = empty_envelope()
    env, environment = worker_environment(dict(os.environ))
    envelope.update(target_major=request.target, environment=environment,
                    requested_output=request.output)
    envelope["deadline"] = {
        "total_timeout_seconds": request.total_timeout,
        "cleanup_grace_seconds": request.cleanup_grace,
        "pre_integrity_budget_seconds": INTEGRITY_BUDGET,
        "post_integrity_evidence_budget_seconds": INTEGRITY_BUDGET,
        "overall_bound_seconds": request.total_timeout + 2 * INTEGRITY_BUDGET,
        "exceeded": False,
    }
    try:
        pre_deadline = started + INTEGRITY_BUDGET
        records = resolve_inputs(request)
        envelope["output"] = request.output
        pre_helper: dict = {}
        post_helper: dict = {}
        before, before_complete = hash_inputs(records, pre_deadline, env, cancel,
                                              helper_receipt=pre_helper)
        envelope["input_integrity"] = {
            "unchanged": None,
            "records": [{**record, "before": pre, "after": None, "unchanged": None}
                        for record, pre in zip(records, before)],
            "pre_helper": pre_helper,
        }
        if cancel.requested:
            envelope["error"] = "cancelled-before-worker"
            return envelope
        if not pre_helper["cleanup"]["complete"]:
            envelope["error"] = "pre-integrity-helper-cleanup-incomplete"
            envelope["cleanup"]["remaining_pids"] = pre_helper["cleanup"]["remaining_pids"]
            return envelope
        if os.path.lexists(request.output):
            raise ValueError("output appeared before worker start")
        worker, stdout, stderr = run_owned(
            worker_argv(request), env=env, output=Path(request.output),
            total_timeout=request.total_timeout, cleanup_grace=request.cleanup_grace,
            cancel=cancel)
        envelope["worker"] = {key: worker[key] for key in ("pid", "returncode", "completed")}
        envelope["worker"]["elapsed_seconds"] = worker["elapsed_seconds"]
        envelope["worker"]["observed_processes"] = worker["observed_processes"]
        envelope["worker"]["process_inventory_complete"] = worker["process_inventory_complete"]
        envelope["cleanup"] = worker["cleanup"]
        envelope["error"] = worker["error"]
        envelope["deadline"]["exceeded"] = worker["deadline_exceeded"]
        post_deadline = min(time.monotonic() + INTEGRITY_BUDGET,
                            started + envelope["deadline"]["overall_bound_seconds"])
        output = Path(request.output)
        envelope["worker_stdout"] = _save_capture(stdout, output, "supervisor.worker.stdout.log", post_deadline)
        envelope["worker_stderr"] = _save_capture(stderr, output, "supervisor.worker.stderr.log", post_deadline)
        envelope["launch_report"] = read_launch(output, request.target, post_deadline)
        correlate_runtime(envelope["launch_report"], worker)
        # Outer cancellation must still permit bounded final integrity evidence.
        after, after_complete = hash_inputs(records, post_deadline, env, Cancellation(),
                                            helper_receipt=post_helper)
        unchanged: bool | None = True if before_complete and after_complete else None
        receipt = []
        for record, pre, post in zip(records, before, after):
            complete = pre.get("status") == post.get("status") == "complete"
            same = pre == post if complete else None
            if same is False or "changed-during-read" in (pre.get("status"), post.get("status")):
                unchanged = False
            elif same is None and unchanged is True:
                unchanged = None
            receipt.append({**record, "before": pre, "after": post, "unchanged": same})
        envelope["input_integrity"] = {"unchanged": unchanged, "records": receipt,
                                        "pre_helper_complete": before_complete,
                                        "post_helper_complete": after_complete,
                                        "pre_helper": pre_helper, "post_helper": post_helper}
        if not post_helper["cleanup"]["complete"]:
            envelope["cleanup"]["complete"] = False
            envelope["cleanup"]["remaining_pids"] = sorted(set(
                envelope["cleanup"]["remaining_pids"] + post_helper["cleanup"]["remaining_pids"]))
        envelope["recovery_progress"] = recovery_progress(envelope["launch_report"])
    except Exception as error:
        envelope["error"] = type(error).__name__
    finally:
        envelope["cancel"] = vars(cancel).copy()
        envelope["elapsed_seconds"] = time.monotonic() - started
    return envelope


def main(argv: list[str] | None = None) -> int:
    cancel = Cancellation()
    previous = {}
    envelope = empty_envelope()
    try:
        for name in ("SIGTERM", "SIGINT", "SIGHUP"):
            signum = getattr(signal, name, None)
            if signum is not None:
                previous[signum] = signal.signal(signum, cancel.handle)
        args = parse_request(list(sys.argv[1:] if argv is None else argv))
        envelope = supervise(args, cancel=cancel)
    except Exception as error:
        envelope["error"] = type(error).__name__
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(serialize_envelope(envelope))
    # Successful envelope transport, irrespective of worker or OS boot status.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
