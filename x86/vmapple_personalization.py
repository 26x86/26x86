"""Live Apple TSS personalization for the VMApple research runner.

This module operates at the VMApple USB/iBoot control-plane layer.  It accepts
only caller-supplied, manifest-matched Apple components and writes all derived
IMG4 files into a new private output directory.  It never edits an IPSW,
installer, EFI partition, or source IM4P.  A server-issued IM4M ticket is
recorded separately from guest acceptance and macOS boot evidence.

The ``developer_host_bypass`` argument is an explicit lab acknowledgement. It
does not disable CPU checks, payload/manifest checks, TLS verification, nonce
binding, or guest trust.  Its outputs are marked non-redistributable.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import plistlib
import re
import ssl
import subprocess
import time
import urllib.request
from typing import Any

from .vmapple import RecoveryProtocolError, RecoveryTransport, _regular, _sha256


TSS_URL = "https://gs.apple.com/TSS/controller?action=2"
APPLE_ROOT_SHA256 = "b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024"
MAX_BUILD_MANIFEST = 32 * 1024 * 1024
MAX_COMPONENT_BYTES = 8 * 1024 * 1024
MAX_TSS_BYTES = 4 * 1024 * 1024
RESTORE_POLICY = bytes.fromhex("30141604494d345016046c706f6c1603312e30040100")


class PersonalizationError(RuntimeError):
    """A live identity, manifest, TSS, or IMG4 personalization failure."""


def _read_bytes(path: str | Path, label: str, limit: int) -> tuple[Path, bytes]:
    checked = _regular(path, label, limit=limit)
    with checked.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"{label} exceeds its {limit} byte bound")
    return checked, data


def _exclusive_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as destination:
        destination.write(data)


def _manifest_integer(value: Any) -> int:
    if type(value) not in (str, int):
        raise ValueError("BuildManifest hardware identifiers must be integers")
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("BuildManifest hardware identifier is invalid") from exc


def read_build_manifest(path: str | Path) -> dict[str, Any]:
    _, encoded = _read_bytes(path, "BuildManifest", MAX_BUILD_MANIFEST)
    try:
        manifest = plistlib.loads(encoded)
    except (ValueError, TypeError, OverflowError, plistlib.InvalidFileException) as exc:
        raise ValueError("BuildManifest is not a valid plist") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("BuildIdentities"), list):
        raise ValueError("BuildManifest must contain BuildIdentities")
    return manifest


def _select_identity(manifest: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for identity in manifest["BuildIdentities"]:
        if not isinstance(identity, dict) or not isinstance(identity.get("Info"), dict):
            continue
        try:
            match = (
                _manifest_integer(identity.get("ApChipID", "0")) == live["CPID"]
                and _manifest_integer(identity.get("ApBoardID", "0")) == live["BDID"]
                and _manifest_integer(identity.get("ApSecurityDomain", "0")) == live["SDOM"]
                and identity["Info"].get("Variant") == "Customer Erase Install (IPSW)"
            )
        except (KeyError, ValueError):
            match = False
        if match:
            candidates.append(identity)
    if len(candidates) != 1:
        raise ValueError("Exactly one matching Customer Erase Install (IPSW) identity is required")
    return candidates[0]


def _parameters(live: dict[str, Any], *, in_rom: bool) -> dict[str, Any]:
    return {
        "ApECID": live["ECID"],
        "ApNonce": live["NONC"],
        "ApSepNonce": live["SNON"],
        "ApProductionMode": True,
        "ApSecurityMode": True,
        "ApSupportsImg4": True,
        "ApInRomDFU": in_rom,
    }


def _der(tag: int, content: bytes) -> bytes:
    size = len(content)
    if size < 128:
        encoded = bytes([size])
    else:
        count = (size.bit_length() + 7) // 8
        encoded = bytes([0x80 | count]) + size.to_bytes(count, "big")
    return bytes([tag]) + encoded + content


def _der_content(data: bytes, expected_magic: bytes) -> bytes:
    if len(data) < 3 or data[0] != 0x30:
        raise ValueError("Expected a DER sequence")
    count = data[1] & 0x7F if data[1] & 0x80 else 0
    if count > 4 or data[1] == 0x80 or len(data) < 2 + count:
        raise ValueError("Invalid DER length")
    size = int.from_bytes(data[2:2 + count], "big") if count else data[1]
    start = 2 + count
    if start + size != len(data) or not data[start:].startswith(_der(0x16, expected_magic)):
        raise ValueError("DER type/length does not match the expected IMG4 component")
    return data[start:]


def wrap_firmware(payload: bytes, ticket: bytes, component: str) -> bytes:
    """Return a standard IMG4 container around unchanged IM4P and IM4M bytes."""
    if component not in ("iBSS", "iBEC"):
        raise ValueError("Only original iBSS and iBEC components are supported")
    tag = {"iBSS": b"ibss", "iBEC": b"ibec"}[component]
    contents = _der_content(payload, b"IM4P")
    if not contents.startswith(_der(0x16, b"IM4P") + _der(0x16, tag)):
        raise ValueError("Original IM4P does not match the selected component")
    _der_content(ticket, b"IM4M")
    return _der(0x30, _der(0x16, b"IMG4") + payload + _der(0xA0, ticket))


def _time_left(deadline: float | None, maximum: float = 60.0) -> float:
    if deadline is None:
        return maximum
    if isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
        raise ValueError("Personalization deadline must be a finite monotonic timestamp")
    remaining = float(deadline) - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Personalization deadline expired")
    return min(maximum, remaining)


def _usb_string(transport: RecoveryTransport, index: int, *, deadline: float | None) -> str:
    data = transport.descriptor(3, index=index, language=0x409, length=255, deadline=deadline)
    if len(data) < 2 or data[0] != len(data) or data[1] != 3 or len(data) % 2:
        raise RecoveryProtocolError("Invalid USB string descriptor")
    try:
        return data[2:].decode("utf-16-le", errors="strict")
    except UnicodeDecodeError as exc:
        raise RecoveryProtocolError("USB identity string is not UTF-16LE") from exc


def read_live_identity(transport: RecoveryTransport, *, require_dfu_idle: bool,
                       deadline: float | None = None) -> dict[str, Any]:
    """Read the actual USB identity and nonce; no identity is synthesized."""
    descriptor = transport.descriptor(1, length=18, deadline=deadline)
    if (len(descriptor) != 18 or descriptor[:2] != b"\x12\x01"
            or descriptor[8:10] != b"\xAC\x05"):
        raise RecoveryProtocolError("An actual Apple recovery device descriptor is required")
    product = int.from_bytes(descriptor[10:12], "little")
    if product == 0x1227:
        state = transport.dfu_state(deadline=deadline)
        status = transport.dfu_status(deadline=deadline)
        if state != 2 or status["status"] != 0 or status["state"] != 2:
            raise RecoveryProtocolError("Live ROM must be in error-free DFU idle")
    elif require_dfu_idle or product not in (0x1280, 0x1281, 0x1282, 0x1283):
        raise RecoveryProtocolError("Unexpected Apple recovery mode for this stage")

    serial = _usb_string(transport, descriptor[16], deadline=deadline)
    nonce_string = _usb_string(transport, 1, deadline=deadline)
    result: dict[str, Any] = {}
    for name in ("SDOM", "CPID", "CPFM", "SCEP", "BDID", "ECID"):
        matches = re.findall(r"(?:^| )" + name + r":([0-9A-Fa-f]+)(?= |$)", serial)
        if len(matches) != 1:
            raise RecoveryProtocolError("Missing or duplicate live identity field " + name)
        result[name] = int(matches[0], 16)
    if result["CPFM"] != 3 or result["SCEP"] != 1:
        raise RecoveryProtocolError("Live device is not in production secure IMG4 mode")
    for name, size in (("NONC", 32), ("SNON", 20)):
        matches = re.findall(r"(?:^| )" + name + r":([0-9A-Fa-f]+)(?= |$)", nonce_string)
        if len(matches) != 1 or len(matches[0]) != size * 2:
            raise RecoveryProtocolError("Missing or unexpected live nonce representation " + name)
        result[name] = bytes.fromhex(matches[0])
    result["USBProduct"] = product
    result["nonce_sha256"] = {
        "NONC": hashlib.sha256(result["NONC"]).hexdigest(),
        "SNON": hashlib.sha256(result["SNON"]).hexdigest(),
    }
    return result


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise PersonalizationError("TSS redirects are not permitted")


def _tss_opener() -> urllib.request.OpenerDirector:
    certificate = Path(__file__).parent / "certs" / "AppleIncRootCertificate.cer"
    checked = _regular(certificate, "Apple root certificate", limit=64 * 1024)
    root = checked.read_bytes()
    if hashlib.sha256(root).hexdigest() != APPLE_ROOT_SHA256:
        raise PersonalizationError("Pinned Apple root certificate hash does not match")
    context = ssl.create_default_context()
    context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(root))
    return urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=context))


def _run_tss_helper(helper: Path, identity_file: Path, parameters_file: Path,
                    *, local_policy: bool, timeout: float) -> bytes:
    command = [str(helper), str(identity_file), str(parameters_file)]
    if local_policy:
        command.append("local-policy")
    try:
        completed = subprocess.run(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=timeout, check=False, shell=False)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("TSS request helper timed out") from exc
    if completed.returncode:
        detail = completed.stderr[:1024].decode("utf-8", "replace").strip()
        raise PersonalizationError("TSS request helper failed" + (": " + detail if detail else ""))
    if len(completed.stdout) > MAX_TSS_BYTES:
        raise PersonalizationError("TSS request helper output exceeds its bound")
    try:
        plistlib.loads(completed.stdout)
    except (ValueError, TypeError, OverflowError, plistlib.InvalidFileException) as exc:
        raise PersonalizationError("TSS request helper did not return a plist") from exc
    return completed.stdout


def _issue_ticket(helper: Path, identity_file: Path, parameters: dict[str, Any],
                  directory: Path, report: dict[str, Any], *, local_policy: bool,
                  deadline: float | None) -> bytes:
    suffix = "-local-policy" if local_policy else ""
    parameters_file = directory / ("live-parameters" + suffix + ".private.plist")
    request_file = directory / ("request" + suffix + ".private.plist")
    _exclusive_write(parameters_file, plistlib.dumps(parameters))
    report["stage"] = "encode-local-policy-request" if local_policy else "encode-request"
    encoded = _run_tss_helper(helper, identity_file, parameters_file,
                              local_policy=local_policy, timeout=_time_left(deadline, 30))
    _exclusive_write(request_file, encoded)
    request = urllib.request.Request(
        TSS_URL, data=encoded, method="POST",
        headers={"Content-Type": "text/xml", "User-Agent": "26x86/2.0"},
    )
    report["stage"] = "request-local-policy-ticket" if local_policy else "request-ticket"
    with _tss_opener().open(request, timeout=_time_left(deadline)) as response:
        if response.url != TSS_URL or response.status != 200:
            raise PersonalizationError("Unexpected TSS endpoint or HTTP status")
        raw = response.read(MAX_TSS_BYTES + 1)
    if len(raw) > MAX_TSS_BYTES:
        raise PersonalizationError("TSS response exceeds its bound")
    response_file = directory / ("response" + suffix + ".private.txt")
    _exclusive_write(response_file, raw)
    prefix, separator, xml = raw.partition(b"&REQUEST_STRING=")
    metadata: dict[bytes, bytes] = {}
    for item in prefix.split(b"&"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            metadata[key] = value
    report["tss_status"] = metadata.get(b"STATUS", b"missing").decode("ascii", "replace")
    if metadata.get(b"STATUS") != b"0" or not separator:
        raise PersonalizationError("Apple TSS did not issue a ticket; status=" + report["tss_status"])
    try:
        result = plistlib.loads(xml)
    except (ValueError, TypeError, OverflowError, plistlib.InvalidFileException) as exc:
        raise PersonalizationError("TSS response XML is not a plist") from exc
    ticket = result.get("ApImg4Ticket") if isinstance(result, dict) else None
    if not isinstance(ticket, bytes) or not ticket:
        raise PersonalizationError("Apple TSS response does not contain an IMG4 ticket")
    _der_content(ticket, b"IM4M")
    return ticket


def _authorization(developer_host_bypass: bool) -> dict[str, Any]:
    if type(developer_host_bypass) is not bool:
        raise ValueError("developer_host_bypass must be an explicit boolean")
    if not developer_host_bypass:
        raise PersonalizationError(
            "Live VMApple personalization is a non-redistributable developer-host operation; "
            "pass the explicit research-only acknowledgement"
        )
    return {
        "authorized": True,
        "developer_host_bypass": True,
        "distribution_status": "NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT",
        "artifact_or_guest_trust_waived": False,
        "installer_modified": False,
    }


def _source_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        records.append({"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    return records


def _sources_intact(records: list[dict[str, Any]]) -> bool:
    for record in records:
        path = Path(record["path"])
        try:
            if not path.is_file() or path.stat().st_size != record["bytes"] or _sha256(path) != record["sha256"]:
                return False
        except OSError:
            return False
    return True


def _redacted_identity(live: dict[str, Any]) -> dict[str, Any]:
    return {
        name: (value.hex() if isinstance(value, bytes) else value)
        for name, value in live.items() if name not in ("NONC", "SNON")
    }


def personalize_firmware(*, socket_path: str, build_manifest: str | Path,
                         firmware: str | Path, component: str, helper: str | Path,
                         output: str | Path, developer_host_bypass: bool = False,
                         include_restore_policy: bool = False,
                         deadline: float | None = None) -> dict[str, Any]:
    """Request a fresh ticket for a live device and wrap unchanged component bytes."""
    authorization = _authorization(developer_host_bypass)
    if component not in ("iBSS", "iBEC"):
        raise ValueError("Only iBSS and iBEC personalization is supported")
    if include_restore_policy and component != "iBEC":
        raise ValueError("LocalPolicy can only bind an iBEC ticket")
    manifest_path = _regular(build_manifest, "BuildManifest", limit=MAX_BUILD_MANIFEST)
    firmware_path = _regular(firmware, "original " + component, limit=MAX_COMPONENT_BYTES)
    helper_path = _regular(helper, "TSS request helper", limit=16 * 1024 * 1024)
    manifest = read_build_manifest(manifest_path)
    payload = firmware_path.read_bytes()
    _der_content(payload, b"IM4P")
    directory = Path(output).expanduser().absolute()
    if directory.exists() or directory.is_symlink():
        raise ValueError("Personalization output directory must be new")
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(mode=0o700)
    sources = _source_records([manifest_path, firmware_path, helper_path])
    report: dict[str, Any] = {
        "schema": "26x86.vmapple-personalization/1",
        "component": component,
        "host_authorization": authorization,
        "tss_url": TSS_URL,
        "ticket_received": False,
        "ticket_nonce_match": False,
        "payload_preserved": False,
        "installer_modified": False,
        "guest_acceptance_verified": False,
        "xnu_boot_verified": False,
        "macos_boot_verified": False,
        "stage": "read-live-identity",
        "input_integrity": False,
        "inputs": sources,
    }
    outputs: list[Path] = []
    integrity_error: PersonalizationError | None = None
    try:
        _time_left(deadline)
        with RecoveryTransport(socket_path, timeout=min(10.0, _time_left(deadline, 10))) as transport:
            live = read_live_identity(transport, require_dfu_idle=component == "iBSS", deadline=deadline)
            report["live_identity"] = _redacted_identity(live)
            report["live_identity"]["NONC_sha256"] = live["nonce_sha256"]["NONC"]
            report["live_identity"]["SNON_sha256"] = live["nonce_sha256"]["SNON"]
            identity = _select_identity(manifest, live)
            report["stage"] = "validate-component"
            digest = identity.get("Manifest", {}).get(component, {}).get("Digest")
            if not isinstance(digest, bytes):
                raise ValueError("BuildManifest is missing the component digest")
            algorithm = {20: "sha1", 32: "sha256", 48: "sha384"}.get(len(digest))
            if algorithm is None or hashlib.new(algorithm, payload).digest() != digest:
                raise ValueError("Original component does not match the official BuildManifest")
            identity_file = directory / "identity.plist"
            _exclusive_write(identity_file, plistlib.dumps(identity))
            parameters = _parameters(live, in_rom=component == "iBSS")
            ticket = _issue_ticket(helper_path, identity_file, parameters, directory, report,
                                   local_policy=False, deadline=deadline)
            report["ticket_received"] = True
            report["ticket_sha256"] = hashlib.sha256(ticket).hexdigest()
            report["stage"] = "verify-live-nonce"
            if read_live_identity(transport, require_dfu_idle=component == "iBSS", deadline=deadline) != live:
                raise PersonalizationError("Live USB identity or nonce changed during TSS request")
            report["ticket_nonce_match"] = True
            ticket_path = directory / "apple-ticket.private.im4m"
            _exclusive_write(ticket_path, ticket)
            outputs.append(ticket_path)
            wrapped = wrap_firmware(payload, ticket, component)
            output_path = directory / (component + ".personalized.img4")
            _exclusive_write(output_path, wrapped)
            outputs.append(output_path)
            report.update(
                stage="complete",
                payload_preserved=payload in wrapped,
                original_payload_sha256=hashlib.sha256(payload).hexdigest(),
                personalized_sha256=hashlib.sha256(wrapped).hexdigest(),
                bytes=len(wrapped), output=str(output_path),
            )
            if include_restore_policy:
                policy_directory = directory / "restore-policy"
                policy_directory.mkdir(mode=0o700)
                policy_parameters = {
                    **parameters,
                    "Ap,LocalBoot": False,
                    "Ap,LocalPolicy": {"Digest": hashlib.sha384(RESTORE_POLICY).digest(), "Trusted": True},
                    "Ap,NextStageIM4MHash": hashlib.sha384(ticket).digest(),
                }
                policy_report: dict[str, Any] = {
                    "ticket_received": False, "guest_acceptance_verified": False,
                    "network_request_sent": True,
                }
                report["restore_policy"] = policy_report
                policy_ticket = _issue_ticket(helper_path, identity_file, policy_parameters,
                                              policy_directory, policy_report, local_policy=True,
                                              deadline=deadline)
                if read_live_identity(transport, require_dfu_idle=False, deadline=deadline) != live:
                    raise PersonalizationError("Live USB nonce changed during LocalPolicy request")
                policy_ticket_path = policy_directory / "apple-ticket.private.im4m"
                policy_image_path = policy_directory / "RestoreLocalPolicy.personalized.img4"
                policy_image = _der(0x30, _der(0x16, b"IMG4") + RESTORE_POLICY + _der(0xA0, policy_ticket))
                _exclusive_write(policy_ticket_path, policy_ticket)
                outputs.append(policy_ticket_path)
                _exclusive_write(policy_image_path, policy_image)
                outputs.append(policy_image_path)
                policy_report.update(
                    ticket_received=True, bytes=len(policy_image),
                    sha256=hashlib.sha256(policy_image).hexdigest(),
                    next_stage_ticket_sha384=hashlib.sha384(ticket).hexdigest(),
                    ticket_nonce_match=True,
                )
    except BaseException as exc:
        report.update(error_type=type(exc).__name__, error=str(exc)[:1024])
        for path in outputs:
            path.unlink(missing_ok=True)
        raise
    finally:
        report["input_integrity"] = _sources_intact(sources)
        if not report["input_integrity"]:
            report["payload_preserved"] = False
            report["ticket_nonce_match"] = False
            report["error_type"] = "PersonalizationError"
            report["error"] = "One or more caller-supplied personalization inputs changed during the run"
            for path in outputs:
                path.unlink(missing_ok=True)
            integrity_error = PersonalizationError(report["error"])
        (directory / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if integrity_error is not None:
        raise integrity_error
    return report


def personalize_ibss(**kwargs: Any) -> dict[str, Any]:
    kwargs["component"] = "iBSS"
    kwargs.pop("include_restore_policy", None)
    return personalize_firmware(**kwargs)


def personalize_ibec(**kwargs: Any) -> dict[str, Any]:
    kwargs["component"] = "iBEC"
    kwargs["include_restore_policy"] = True
    return personalize_firmware(**kwargs)


__all__ = [
    "APPLE_ROOT_SHA256", "PersonalizationError", "RESTORE_POLICY", "TSS_URL",
    "_der", "_der_content", "_select_identity", "personalize_firmware", "personalize_ibec",
    "personalize_ibss", "read_build_manifest", "read_live_identity", "wrap_firmware",
]
