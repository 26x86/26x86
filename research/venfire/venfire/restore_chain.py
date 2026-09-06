"""Original-preserving ROM -> iBSS -> iBEC/LocalPolicy -> restore orchestration.

UART stage prompts and USB transfer receipts are distinct observations. No
replacement ticket may break the accepted LocalPolicy-bound iBEC chain.
Completing this host operation does not establish a macOS boot.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import stat
import tempfile
import time

from .artifacts import (_absolute_path, _inspect_path, _open_fd, create_manifest, read_regular,
                        require_intact, verify_manifest, write_manifest)
from .personalization import personalize_firmware, read_build_manifest, reuse_restore_ticket
from .policy import authorize_host
from .recovery import RecoveryProtocolError, RecoveryTransport, send_dfu_file
from .restore import ROLE_TAGS, prepare_role_container, run_stage, wrap_role_container

PROMPTS = {1: b"Entering iBootStage1 recovery mode, starting command prompt",
           2: b"Entering iBootStage2 recovery mode, starting command prompt"}
REQUIRED_ROLES = frozenset(("RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache"))
MAX_SERIAL = 16 * 1024 * 1024
MAX_PROFILE = 64 * 1024


class RestoreChainError(RuntimeError):
    def __init__(self, message, report):
        self.chain_report = report
        super().__init__(message)


def duration(value, name, *, maximum=3600, allow_zero=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (not allow_zero and value == 0)
            or value > maximum):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}, at most {maximum}")
    return value


def load_profile(path):
    """Read one selected profile; resolve only its named regular asset files."""
    path = _absolute_path(path)
    with read_regular(path) as stream:
        data = stream.read(MAX_PROFILE + 1)
    if len(data) > MAX_PROFILE:
        raise ValueError("Restore profile exceeds 64 KiB")
    profile = json.loads(data)
    if (not isinstance(profile, dict) or type(profile.get("schema")) is not int
            or profile["schema"] != 1 or profile.get("mode") != "restore-chain"):
        raise ValueError("Expected schema 1 restore-chain profile")
    allowed = {"schema", "mode", "firmware", "aux", "disk", "aux_offset", "uuid", "build_manifest",
               "ibss", "ibec", "components", "seconds", "stage_timeout", "transfer_timeout", "observe_seconds", "graphics"}
    if profile.keys() - allowed:
        raise ValueError("Unknown restore profile fields: " + ", ".join(sorted(profile.keys() - allowed)))
    result = dict(profile)

    def asset(value):
        if not isinstance(value, str) or not value:
            raise ValueError("Restore asset paths must be nonempty strings")
        candidate = Path(value)
        absolute = _absolute_path(candidate if candidate.is_absolute() else path.parent / candidate)
        if not stat.S_ISREG(_inspect_path(absolute).st_mode):
            raise ValueError("Restore asset must be a regular file")
        return str(absolute)

    for name in ("firmware", "aux", "disk", "build_manifest", "ibss", "ibec"):
        result[name] = asset(profile.get(name))
    components = profile.get("components")
    if (not isinstance(components, dict) or not REQUIRED_ROLES <= components.keys()
            or components.keys() - ROLE_TAGS.keys()):
        raise ValueError("Restore profile needs the four standard restore roles; only RestoreLogo is optional")
    result["components"] = {role: asset(value) for role, value in components.items()}
    ecid = profile.get("uuid")
    if isinstance(ecid, str):
        try:
            ecid = int(ecid, 0)
        except ValueError as exc:
            raise ValueError("VM uuid must be an unsigned 64-bit integer") from exc
    if type(ecid) is not int or not 0 <= ecid < 2**64:
        raise ValueError("VM uuid must be an unsigned 64-bit integer")
    result["uuid"] = ecid
    offset = profile.get("aux_offset", 0)
    if type(offset) is not int or offset < 0 or offset % 512:
        raise ValueError("Aux offset must be a nonnegative 512-byte multiple")
    result["aux_offset"] = offset
    for name, default, maximum in (("seconds", 3600, 86400), ("stage_timeout", 300, 3600),
                                    ("transfer_timeout", 600, 3600), ("observe_seconds", 60, 3600)):
        result[name] = duration(profile.get(name, default), name, maximum=maximum,
                                allow_zero=name == "observe_seconds")
    if type(result["seconds"]) is not int:
        raise ValueError("Session seconds must be an integer")
    result["graphics"] = profile.get("graphics", "auto")
    if result["graphics"] not in ("auto", "on", "off"):
        raise ValueError("Graphics selection must be auto, on or off")
    return result


def _serial_bytes(path, start=0):
    """Read growing logs with path/device bounds, without requiring immutability."""
    path = _absolute_path(path)
    _inspect_path(path)
    descriptor = _open_fd(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        current = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino)
                or not 0 <= start <= info.st_size <= MAX_SERIAL):
            raise ValueError("UART log is not a bounded regular growing file")
        stream.seek(start)
        value = stream.read(MAX_SERIAL + 1)
        if len(value) > MAX_SERIAL:
            raise ValueError("UART log exceeds bound")
        return value


def wait_prompt(serial_log, stage, start, *, deadline, check_running=lambda: None):
    marker = PROMPTS[stage]
    while True:
        check_running()
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Actual iBootStage{stage} UART prompt was not observed")
        data = _serial_bytes(serial_log, start)
        if b"iBoot Panic:" in data or b"panic(cpu" in data:
            raise RuntimeError("Original guest panic before the next recovery stage")
        position = data.find(marker)
        if position >= 0:
            return {"stage": stage, "uart_prompt_observed": True,
                    "marker": marker.decode("ascii"), "byte_offset": start + position,
                    "searched_after_offset": start}
        time.sleep(min(0.1, max(0, deadline - time.monotonic())))


def _wait_dfu(socket_path, deadline, check_running):
    last = None
    while time.monotonic() < deadline:
        check_running()
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            with RecoveryTransport(socket_path, min(1, remaining)) as transport:
                device = transport.descriptor(1, length=18, deadline=deadline)
                if len(device) != 18 or device[:2] != b"\x12\x01" or device[8:12] != b"\xac\x05\x27\x12":
                    raise RecoveryProtocolError("Original ROM DFU descriptor not ready")
                if transport.dfu_state(deadline=deadline) != 2:
                    raise RecoveryProtocolError("Original ROM is not in DFU idle")
                return {"device_descriptor_hex": device.hex(), "dfu_idle_observed": True}
        except (OSError, RecoveryProtocolError) as exc:
            last = type(exc).__name__
        time.sleep(min(0.1, max(0, deadline - time.monotonic())))
    raise TimeoutError("Original ROM DFU not ready before deadline" + (": " + last if last else ""))


def run_chain(*, socket_path, serial_log, build_manifest, ibss, ibec, components, helper,
              output, developer_host_bypass=False, stage_timeout=300, transfer_timeout=600,
              observe_seconds=60, check_running=lambda: None, progress=None):
    authorization = authorize_host(developer_host_bypass=developer_host_bypass)
    duration(stage_timeout, "stage_timeout")
    duration(transfer_timeout, "transfer_timeout")
    duration(observe_seconds, "observe_seconds", allow_zero=True)
    if (not isinstance(components, dict) or not REQUIRED_ROLES <= components.keys()
            or components.keys() - ROLE_TAGS.keys()):
        raise ValueError("Required standard restore components are missing")
    inputs = create_manifest(list(dict.fromkeys(map(os.fspath, [build_manifest, ibss, ibec, helper, *components.values()]))))
    folder = _absolute_path(output)
    _inspect_path(folder, must_exist=False)
    folder.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_manifest(inputs, folder / "inputs.json")
    report = {"schema": 1, "host_authorization": authorization.to_dict(), "stage": "preflight",
              "steps": [], "chain_completed": False, "error": None,
              "macos_boot_verified": False, "xnu_boot_verified": False,
              "ticket_mode": "same-ibec-localpolicy-chain", "original_guest_code_modified": False}
    failure = None

    def save():
        (folder / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def stage(name, budget=stage_timeout):
        check_running()
        report["stage"] = name
        report["steps"].append({"stage": name, "monotonic_start": time.monotonic(), "budget_seconds": budget})
        save()
        if progress:
            progress(name)
        return time.monotonic() + budget

    def remaining(deadline):
        check_running()
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError("Recovery stage deadline expired: " + report["stage"])
        return value

    try:
        require_intact(inputs)
        manifest = read_build_manifest(build_manifest)
        identities = [identity for identity in manifest["BuildIdentities"]
                      if isinstance(identity, dict) and isinstance(identity.get("Info"), dict)
                      and identity["Info"].get("DeviceClass") == "vma2macosap"
                      and identity["Info"].get("Variant") == "Customer Erase Install (IPSW)"]
        if len(identities) != 1:
            raise ValueError("Expected one official VMApple erase restore identity")
        deadline = stage("prepare-original-restore-roles")
        prepared = {}
        report["prepared"] = {}
        (folder / "prepared").mkdir()
        for role, source in components.items():
            remaining(deadline)
            destination = folder / "prepared" / (role + ".im4p")
            digest = identities[0].get("Manifest", {}).get(role, {}).get("Digest")
            if not isinstance(digest, bytes):
                raise ValueError("Missing official restore digest for " + role)
            report["prepared"][role] = prepare_role_container(source, role, digest, destination)
            prepared[role] = str(destination)
        remaining(deadline)
        report["dfu"] = _wait_dfu(socket_path, stage("wait-rom-dfu"), check_running)
        deadline = stage("personalize-ibss")
        report["ibss"] = personalize_firmware(socket_path=socket_path, build_manifest=build_manifest,
            firmware=ibss, component="iBSS", helper=helper, output=folder / "ibss",
            developer_host_bypass=developer_host_bypass, deadline=deadline)
        remaining(deadline)
        if report["ibss"].get("ticket_received") is not True or report["ibss"].get("payload_preserved") is not True:
            raise RuntimeError("Original iBSS personalization did not complete")
        offset = len(_serial_bytes(serial_log))
        deadline = stage("upload-ibss-dfu", transfer_timeout)
        report["ibss_upload"] = send_dfu_file(socket_path, report["ibss"]["output"], timeout=min(10, remaining(deadline)),
            total_timeout=remaining(deadline), reset=True, expected_sha256=report["ibss"]["personalized_sha256"])
        remaining(deadline)
        if report["ibss_upload"].get("transfer_complete") is not True:
            raise RuntimeError("iBSS DFU transfer did not complete")
        report["stage1"] = wait_prompt(serial_log, 1, offset, deadline=stage("wait-stage1-uart"), check_running=check_running)
        deadline = stage("personalize-ibec-and-bound-policy")
        report["ibec"] = personalize_firmware(socket_path=socket_path, build_manifest=build_manifest,
            firmware=ibec, component="iBEC", helper=helper, output=folder / "ibec",
            developer_host_bypass=developer_host_bypass, include_restore_policy=True, deadline=deadline)
        remaining(deadline)
        policy = report["ibec"].get("restore_policy", {})
        if (report["ibec"].get("ticket_received") is not True or report["ibec"].get("payload_preserved") is not True
                or policy.get("ticket_received") is not True):
            raise RuntimeError("iBEC and its bound LocalPolicy did not personalize")
        offset = len(_serial_bytes(serial_log))
        deadline = stage("upload-bound-policy-then-ibec", transfer_timeout)
        with RecoveryTransport(socket_path, min(10, remaining(deadline))) as transport:
            report["ibec_configuration"] = transport.configure_recovery(deadline=deadline)
            report["policy_upload"] = transport.send_recovery_file(folder / "ibec/restore-policy/RestoreLocalPolicy.personalized.img4",
                total_timeout=remaining(deadline), expected_sha256=policy["sha256"])
            transport.send_command("lpolrestore", deadline=deadline)
            report["lpolrestore_acknowledged"] = True
            report["ibec_upload"] = transport.send_recovery_file(report["ibec"]["output"],
                total_timeout=remaining(deadline), expected_sha256=report["ibec"]["personalized_sha256"])
            transport.send_command("go", request=1, deadline=deadline)
            report["ibec_go_acknowledged"] = True
        remaining(deadline)
        report["stage2"] = wait_prompt(serial_log, 2, offset, deadline=stage("wait-stage2-uart"), check_running=check_running)
        deadline = stage("reuse-accepted-ibec-ticket")
        report["restore_ticket"] = reuse_restore_ticket(socket_path=socket_path, build_manifest=build_manifest,
            components=prepared, chain_personalization=folder / "ibec", output=folder / "restore-ticket",
            developer_host_bypass=developer_host_bypass, original_inputs=list(components.values()), deadline=deadline)
        remaining(deadline)
        ticket = report["restore_ticket"]
        if ticket.get("ticket_reused") is not True or ticket.get("network_request_sent") is not False:
            raise RuntimeError("Restore must reuse the accepted iBEC/LocalPolicy ticket without a new request")
        images = {}
        report["wrapped"] = {}
        for role, source in prepared.items():
            remaining(deadline)
            target = folder / (role + ".img4")
            proof = wrap_role_container(source, ticket["ticket_path"], target)
            report["wrapped"][role] = proof
            images[role] = {"path": str(target), "sha256": proof["sha256"]}
        require_intact(inputs)
        remaining(deadline)
        offset = len(_serial_bytes(serial_log))
        deadline = stage("send-standard-restore-sequence", transfer_timeout)
        report["restore"] = run_stage(socket_path, images, total_timeout=remaining(deadline))
        remaining(deadline)
        if (report["restore"].get("error") or report["restore"].get("sequence_sent") is not True
                or report["restore"].get("input_integrity", {}).get("valid") is not True):
            raise RuntimeError("Standard restore sequence did not complete intact")
        deadline = stage("observe-original-guest", observe_seconds)
        while time.monotonic() < deadline:
            check_running()
            data = _serial_bytes(serial_log, offset)
            if b"iBoot Panic:" in data or b"panic(cpu" in data:
                raise RuntimeError("Original guest panic after restore transfer")
            time.sleep(min(0.1, max(0, deadline - time.monotonic())))
        report.update(stage="chain-complete-boot-unverified", chain_completed=True)
    except BaseException as exc:
        failure = exc
        report["error"] = f"{type(exc).__name__}: {exc}"[:2048]
        for attribute, name in (("restore_report", "restore"), ("recovery_report", "partial_upload"), ("report", "partial_upload")):
            value = getattr(exc, attribute, None)
            if isinstance(value, dict):
                report[name] = value
    finally:
        integrity = verify_manifest(inputs)
        report["input_integrity"] = integrity.to_dict()
        if not integrity.valid:
            report["chain_completed"] = False
            report["integrity_error"] = "Original restore inputs changed"
        save()
    if failure is not None:
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            failure.chain_report = report
            raise failure
        raise RestoreChainError(report["error"], report) from failure
    if not report["input_integrity"]["valid"]:
        raise RestoreChainError(report["integrity_error"], report)
    return report


def boot_restore_chain(*, qemu, qemu_img, profile_path, helper, output, developer_host_bypass=False, progress=None):
    """Launch one COW VM and exclusively drive its complete recovery chain."""
    authorize_host(developer_host_bypass=developer_host_bypass)
    profile_inputs = create_manifest([profile_path])
    profile = load_profile(profile_path)
    folder = _absolute_path(output)
    _inspect_path(folder, must_exist=False)
    folder.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {"schema": 1, "chain_completed": False, "macos_boot_verified": False}
    try:
        require_intact(profile_inputs)
        from .storage import prepare_storage
        from .boot import boot_session
        storage = prepare_storage(aux=profile["aux"], disk=profile["disk"], directory=folder / "storage",
                                  qemu_img=qemu_img, aux_offset=profile["aux_offset"])
        with tempfile.TemporaryDirectory(prefix="venfire-chain-") as endpoint:
            socket_path = str(Path(endpoint) / "recovery.sock")
            def action(*, serial_log, check_running):
                return run_chain(socket_path=socket_path, serial_log=serial_log,
                    build_manifest=profile["build_manifest"], ibss=profile["ibss"], ibec=profile["ibec"],
                    components=profile["components"], helper=helper, output=folder / "chain",
                    developer_host_bypass=developer_host_bypass, stage_timeout=profile["stage_timeout"],
                    transfer_timeout=profile["transfer_timeout"], observe_seconds=profile["observe_seconds"],
                    check_running=check_running, progress=progress)
            report["session"] = boot_session(qemu=qemu, firmware=profile["firmware"], directory=str(storage.directory),
                uuid=profile["uuid"], output=str(folder / "backend"), seconds=profile["seconds"],
                developer_host_bypass=developer_host_bypass, recovery_socket=socket_path,
                runtime_action=action, graphics=profile["graphics"])
        report["chain_completed"] = (report["session"]["runtime_action_completed"]
                                     and report["session"]["runtime_action"]["chain_completed"])
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"[:2048]
        if hasattr(exc, "chain_report"):
            report["chain"] = exc.chain_report
        raise
    finally:
        report["profile_integrity"] = verify_manifest(profile_inputs).to_dict()
        if not report["profile_integrity"]["valid"]:
            report["chain_completed"] = False
        (folder / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
