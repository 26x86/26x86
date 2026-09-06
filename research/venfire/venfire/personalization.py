"""Request a real Apple TSS ticket for the live VM; preserve the iBSS payload.

libtatsu only encodes the request. HTTPS certificate/hostname checks stay enabled
in Python; no HTTP fallback, cached foreign ticket, signing key or trust override.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import plistlib
import re
import ssl
import time
import urllib.request

from .artifacts import (ArtifactIntegrityError, create_manifest, read_regular,
                        require_intact, verify_manifest, write_manifest, load_manifest)
from .policy import authorize_host
from .process import run_bounded
from .recovery import RecoveryTransport, RecoveryProtocolError

TSS_URL = "https://gs.apple.com/TSS/controller?action=2"
APPLE_ROOT_SHA256 = "b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024"
# Standard empty restore LocalPolicy IM4P used by the public restore client;
# it has no authority until Apple signs it for the next-stage ticket and VM.
# idevicerestore 540c352c4c44896f7415abef87a166e8bbaea9b0, lpol_file[22].
RESTORE_POLICY = bytes.fromhex("30141604494d345016046c706f6c1603312e30040100")
MAX_BUILD_MANIFEST = 32 * 1024 * 1024
RESTORE_ROLES = frozenset(("RestoreKernelCache", "RestoreDeviceTree", "RestoreRamDisk",
                           "RestoreTrustCache", "RestoreLogo"))


def read_build_manifest(path):
    with read_regular(path) as stream:
        size = os.fstat(stream.fileno()).st_size
        if size > MAX_BUILD_MANIFEST:
            raise ValueError("BuildManifest exceeds 32 MiB bound")
        encoded = stream.read(size + 1)
    if len(encoded) != size:
        raise ValueError("BuildManifest size changed")
    manifest = plistlib.loads(encoded)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("BuildIdentities"), list):
        raise ValueError("Invalid BuildManifest identities")
    return manifest


def _select_identity(manifest, live):
    candidates = [identity for identity in manifest["BuildIdentities"]
                  if _manifest_integer(identity.get("ApChipID", "0")) == live["CPID"]
                  and _manifest_integer(identity.get("ApBoardID", "0")) == live["BDID"]
                  and _manifest_integer(identity.get("ApSecurityDomain", "0")) == live["SDOM"]
                  and identity["Info"].get("Variant") == "Customer Erase Install (IPSW)"]
    if len(candidates) != 1:
        raise ValueError("Exactly one matching genuine restore identity is required")
    return candidates[0]


def _parameters(live, *, in_rom=False):
    return {"ApECID": live["ECID"], "ApNonce": live["NONC"], "ApSepNonce": live["SNON"],
            "ApProductionMode": True, "ApSecurityMode": True, "ApSupportsImg4": True,
            "ApInRomDFU": in_rom}


def _finish_report(sources, report, directory, outputs):
    operation_failed = "error_type" in report
    integrity = verify_manifest(sources)
    report["input_integrity"] = integrity.to_dict()
    if not integrity.valid:
        report.update(stage="input-integrity", ticket_received=False,
                      error_type="ArtifactIntegrityError", error="Input changed during personalization")
        if "payload_preserved" in report:
            report["payload_preserved"] = False
        if "ticket_reused" in report:
            report["ticket_reused"] = False
        if "restore_policy" in report:
            report["restore_policy"]["ticket_received"] = False
        for path in outputs:
            path.unlink(missing_ok=True)
    (directory / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    if not integrity.valid and not operation_failed:
        raise ArtifactIntegrityError(integrity)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise RuntimeError("TSS redirects are not permitted")


def _tss_opener():
    # The actual gs.apple.com TLS chain uses Apple's private PKI root, which
    # is absent from Ubuntu's Mozilla trust store. This public certificate was
    # fetched through independently verified HTTPS from Apple's PKI site.
    # Scope the extra anchor to this one client; never alter the OS trust store.
    with read_regular(Path(__file__).parent / "certs" / "AppleIncRootCertificate.cer") as stream:
        root = stream.read(16385)
    if hashlib.sha256(root).hexdigest() != APPLE_ROOT_SHA256:
        raise ValueError("Bundled Apple PKI root certificate does not match its pin")
    context = ssl.create_default_context()
    context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(root))
    return urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=context))


def _manifest_integer(value):
    if type(value) not in (str, int):
        raise ValueError("Manifest hardware identifiers must be integers or integer strings")
    return int(value, 0) if isinstance(value, str) else int(value)


def _time_left(deadline, maximum=60):
    if deadline is None:
        return maximum
    if isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
        raise ValueError("Personalization deadline must be a finite monotonic time")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Personalization stage deadline expired")
    return min(maximum, remaining)


def _usb_string(transport, index, *, deadline=None):
    data = transport.descriptor(3, index=index, language=0x409, length=255, deadline=deadline)
    if len(data) < 2 or data[0] != len(data) or data[1] != 3 or len(data) % 2:
        raise RecoveryProtocolError("Invalid USB string descriptor")
    return data[2:].decode("utf-16-le", errors="strict")


def _identity(transport, *, require_dfu_idle=True, deadline=None):
    _time_left(deadline)
    descriptor = transport.descriptor(1, length=18, deadline=deadline)
    if len(descriptor) != 18 or descriptor[:2] != bytes([18, 1]) or descriptor[8:10] != bytes.fromhex("ac05"):
        raise RecoveryProtocolError("An actual Apple restore device descriptor is required")
    product = int.from_bytes(descriptor[10:12], "little")
    if product == 0x1227:
        state = transport.dfu_state(deadline=deadline)
        status = transport.dfu_status(deadline=deadline)
        if state != 2 or status["status"] != 0 or status["state"] != 2:
            raise RecoveryProtocolError("Live ROM must be in error-free DFU idle before personalization")
    elif require_dfu_idle or product not in (0x1280, 0x1281, 0x1282, 0x1283):
        raise RecoveryProtocolError("Unexpected restore mode for the requested boot stage")
    serial = _usb_string(transport, descriptor[16], deadline=deadline)
    nonces = _usb_string(transport, 1, deadline=deadline)
    tags = {}
    for name in ("SDOM", "CPID", "CPFM", "SCEP", "BDID", "ECID"):
        matches = re.findall(r"(?:^| )" + name + r":([0-9A-Fa-f]+)(?= |$)", serial)
        if len(matches) != 1:
            raise RecoveryProtocolError("Missing or duplicate live identity field " + name)
        tags[name] = int(matches[0], 16)
    if tags["CPFM"] != 3 or tags["SCEP"] != 1:
        raise RecoveryProtocolError("This path requires production and secure IMG4 mode")
    for name, required_size in (("NONC", 32), ("SNON", 20)):
        matches = re.findall(r"(?:^| )" + name + r":([0-9A-Fa-f]+)(?= |$)", nonces)
        if len(matches) != 1 or len(matches[0]) != required_size * 2:
            raise RecoveryProtocolError("Missing or unexpected nonce representation " + name)
        tags[name] = bytes.fromhex(matches[0])
    return tags


def _der(tag, content):
    size = len(content)
    encoded = (bytes([size]) if size < 128 else
               bytes([0x80 + (size.bit_length() + 7) // 8]) + size.to_bytes((size.bit_length() + 7) // 8, "big"))
    return bytes([tag]) + encoded + content


def _der_content(data, expected_magic):
    if len(data) < 3 or data[0] != 0x30:
        raise ValueError("Expected a DER sequence")
    count = data[1] & 0x7f if data[1] & 0x80 else 0
    if count > 4 or data[1] == 0x80 or len(data) < 2 + count:
        raise ValueError("Invalid DER length")
    size = int.from_bytes(data[2:2 + count], "big") if count else data[1]
    start = 2 + count
    if start + size != len(data) or not data[start:].startswith(_der(0x16, expected_magic)):
        raise ValueError("DER type/length does not match the expected IMG4 component")
    return data[start:]


def wrap_firmware(payload, ticket, component):
    if component not in ("iBSS", "iBEC"):
        raise ValueError("Only original iBSS/iBEC components are supported")
    tag = {"iBSS": b"ibss", "iBEC": b"ibec"}[component]
    contents = _der_content(payload, b"IM4P")
    if not contents.startswith(_der(0x16, b"IM4P") + _der(0x16, tag)):
        raise ValueError("Original IM4P does not match the selected firmware component")
    _der_content(ticket, b"IM4M")
    # Standard IMG4 sequence: IA5String IMG4, original IM4P, explicit[0] IM4M.
    # Embedding a server-issued ticket is personalization, not a code patch.
    return _der(0x30, _der(0x16, b"IMG4") + payload + _der(0xa0, ticket))


def wrap_ibss(payload, ticket):
    return wrap_firmware(payload, ticket, "iBSS")


def _issue_ticket(helper, identity_file, parameters, directory, report, *, local_policy=False, deadline=None):
    parameters_file = directory / "live-parameters.private.plist"
    parameters_file.write_bytes(plistlib.dumps(parameters))
    command = [helper, str(identity_file), str(parameters_file)]
    if local_policy:
        command.append("local-policy")
    report["stage"] = "encode-request"
    encoded = run_bounded(command, timeout=_time_left(deadline, 30))
    encoded.check_returncode()
    plistlib.loads(encoded.stdout)
    (directory / "request.private.plist").write_bytes(encoded.stdout)
    request = urllib.request.Request(TSS_URL, data=encoded.stdout, method="POST",
        headers={"Content-Type": "text/xml", "User-Agent": "26x86/0.2.0"})
    report["stage"] = "request-ticket"
    with _tss_opener().open(request, timeout=_time_left(deadline)) as response:
        if response.url != TSS_URL or response.status != 200:
            raise RuntimeError("Unexpected TSS endpoint or HTTP result")
        raw = response.read(4 * 1024 * 1024 + 1)
    _time_left(deadline)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("TSS response exceeds bound")
    (directory / "response.private.txt").write_bytes(raw)
    prefix, separator, xml = raw.partition(b"&REQUEST_STRING=")
    metadata = dict(item.split(b"=", 1) for item in prefix.split(b"&") if b"=" in item)
    report["tss_status"] = metadata.get(b"STATUS", b"missing").decode("ascii", "replace")
    if metadata.get(b"STATUS") != b"0" or not separator:
        raise RuntimeError("Apple TSS did not issue a ticket; status=" + report["tss_status"])
    result = plistlib.loads(xml)
    ticket = result.get("ApImg4Ticket")
    if not isinstance(ticket, bytes) or not ticket:
        raise ValueError("Apple TSS response does not contain an IMG4 ticket")
    _der_content(ticket, b"IM4M")
    return ticket


def personalize_ibss(*, socket_path, build_manifest, ibss, helper, output,
                     developer_host_bypass=False):
    return personalize_firmware(socket_path=socket_path, build_manifest=build_manifest,
        firmware=ibss, component="iBSS", helper=helper, output=output,
        developer_host_bypass=developer_host_bypass)


def personalize_firmware(*, socket_path, build_manifest, firmware, component, helper, output,
                         developer_host_bypass=False, include_restore_policy=False, deadline=None):
    authorization = authorize_host(developer_host_bypass=developer_host_bypass)
    _time_left(deadline)
    if component not in ("iBSS", "iBEC"):
        raise ValueError("Only original iBSS/iBEC components are supported")
    if include_restore_policy and component != "iBEC":
        raise ValueError("Restore policy can only bind the next-stage iBEC ticket")
    sources = create_manifest([build_manifest, firmware, helper])
    manifest = read_build_manifest(build_manifest)
    with read_regular(firmware) as stream:
        payload = stream.read(8 * 1024 * 1024 + 1)
    if len(payload) > 8 * 1024 * 1024:
        raise ValueError("Firmware exceeds supported bound")
    _der_content(payload, b"IM4P")
    directory = Path(output).absolute()
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o700)
    write_manifest(sources, directory / "inputs.json")
    report = {"schema": 1, "component": component, "host_authorization": authorization.to_dict(), "tss_url": TSS_URL,
              "ticket_received": False, "payload_preserved": False, "macos_boot_verified": False,
              "stage": "read-live-identity"}
    try:
        with RecoveryTransport(socket_path, _time_left(deadline, 10)) as transport:
            live = _identity(transport, require_dfu_idle=component == "iBSS", deadline=deadline)
            identity = _select_identity(manifest, live)
            report["stage"] = "validate-component"
            digest = identity["Manifest"][component]["Digest"]
            algorithm = {20: "sha1", 32: "sha256", 48: "sha384"}.get(len(digest))
            if not algorithm or hashlib.new(algorithm, payload).digest() != digest:
                raise ValueError("Original firmware does not match the official restore manifest")
            parameters = _parameters(live, in_rom=component == "iBSS")
            identity_file = directory / "identity.plist"
            identity_file.write_bytes(plistlib.dumps(identity))
            require_intact(sources)
            ticket = _issue_ticket(helper, identity_file, parameters, directory, report, deadline=deadline)
            report["stage"] = "verify-live-nonce"
            # Ensure the running ROM has not changed nonce/identity while HTTPS ran.
            if _identity(transport, require_dfu_idle=component == "iBSS", deadline=deadline) != live:
                raise RuntimeError("Live guest identity or nonce changed during personalization")
            if include_restore_policy:
                policy_directory = directory / "restore-policy"
                policy_directory.mkdir(mode=0o700)
                policy_parameters = {**parameters, "Ap,LocalBoot": False,
                    "Ap,LocalPolicy": {"Digest": hashlib.sha384(RESTORE_POLICY).digest(), "Trusted": True},
                    "Ap,NextStageIM4MHash": hashlib.sha384(ticket).digest()}
                policy_report = {"ticket_received": False, "guest_acceptance_verified": False}
                report["restore_policy"] = policy_report
                policy_ticket = _issue_ticket(helper, identity_file, policy_parameters,
                    policy_directory, policy_report, local_policy=True, deadline=deadline)
                if _identity(transport, require_dfu_idle=False, deadline=deadline) != live:
                    raise RuntimeError("Live guest nonce changed during restore policy signing")
                policy_image = _der(0x30, _der(0x16, b"IMG4") + RESTORE_POLICY + _der(0xa0, policy_ticket))
                (policy_directory / "apple-ticket.private.im4m").write_bytes(policy_ticket)
                (policy_directory / "RestoreLocalPolicy.personalized.img4").write_bytes(policy_image)
                policy_report.update(ticket_received=True, bytes=len(policy_image),
                    sha256=hashlib.sha256(policy_image).hexdigest(),
                    next_stage_ticket_sha384=hashlib.sha384(ticket).hexdigest())
            wrapped = wrap_firmware(payload, ticket, component)
            _time_left(deadline)
            (directory / "apple-ticket.private.im4m").write_bytes(ticket)
            (directory / (component + ".personalized.img4")).write_bytes(wrapped)
            report.update(stage="complete", ticket_received=True, payload_preserved=True,
                          component_sha256=hashlib.sha256(payload).hexdigest(),
                          personalized_sha256=hashlib.sha256(wrapped).hexdigest(),
                          bytes=len(wrapped), output=str(directory / (component + ".personalized.img4")))
    except BaseException as exc:
        report.update(error_type=type(exc).__name__, error=str(exc)[:1024])
        raise
    finally:
        _finish_report(sources, report, directory, [directory / "apple-ticket.private.im4m",
            directory / (component + ".personalized.img4"),
            directory / "restore-policy/apple-ticket.private.im4m",
            directory / "restore-policy/RestoreLocalPolicy.personalized.img4"])
    return report


def request_restore_ticket(*, socket_path, build_manifest, components, helper, output,
                           developer_host_bypass=False, original_inputs=()):
    """Sign manifest-matched restore containers for the current recovery guest.

    Prepared role containers may have the standard restore IM4P type tag. Their
    complete bytes must match Apple's unchanged restore identity. Preparation,
    source/payload identity proofs and final wrapping belong to restore.py.
    """
    authorization = authorize_host(developer_host_bypass=developer_host_bypass)
    if not isinstance(components, dict) or not components or not set(components) <= RESTORE_ROLES:
        raise ValueError("Only named standard restore components are supported")
    # The same original may also be an unchanged prepared input; hash once.
    paths = list(dict.fromkeys(os.path.abspath(os.fspath(path)) for path in
                 [build_manifest, helper, *components.values(), *original_inputs]))
    sources = create_manifest(paths)
    directory = Path(output).absolute()
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o700)
    write_manifest(sources, directory / "inputs.json")
    report = {"schema": 1, "component": "restore-batch", "components": {},
              "host_authorization": authorization.to_dict(), "tss_url": TSS_URL,
              "ticket_received": False, "macos_boot_verified": False, "stage": "read-manifest"}
    try:
        manifest = read_build_manifest(build_manifest)
        report["stage"] = "read-live-identity"
        with RecoveryTransport(socket_path, 10) as transport:
            live = _identity(transport, require_dfu_idle=False)
            identity = _select_identity(manifest, live)
            report["stage"] = "validate-components"
            _validate_restore_components(identity, components, report)
            identity_file = directory / "identity.plist"
            identity_file.write_bytes(plistlib.dumps(identity))
            require_intact(sources)
            ticket = _issue_ticket(helper, identity_file, _parameters(live), directory, report)
            report["stage"] = "verify-live-nonce"
            if _identity(transport, require_dfu_idle=False) != live:
                raise RuntimeError("Live guest identity or nonce changed during restore personalization")
            require_intact(sources)
            ticket_path = directory / "apple-ticket.private.im4m"
            ticket_path.write_bytes(ticket)
            report.update(stage="complete", ticket_received=True, ticket_path=str(ticket_path),
                          ticket_sha256=hashlib.sha256(ticket).hexdigest())
    except BaseException as exc:
        report.update(error_type=type(exc).__name__, error=str(exc)[:1024])
        raise
    finally:
        _finish_report(sources, report, directory, [directory / "apple-ticket.private.im4m"])
    return report


def _validate_restore_components(identity, components, report):
    for role, path in components.items():
        digest = identity["Manifest"][role]["Digest"]
        if not isinstance(digest, bytes):
            raise ValueError("Manifest component digest must be bytes")
        algorithm = {20: "sha1", 32: "sha256", 48: "sha384"}.get(len(digest))
        if not algorithm:
            raise ValueError("Unsupported manifest digest length")
        calculated, sha256, size = hashlib.new(algorithm), hashlib.sha256(), 0
        with read_regular(path) as stream:
            while chunk := stream.read(1024 * 1024):
                calculated.update(chunk)
                sha256.update(chunk)
                size += len(chunk)
        if calculated.digest() != digest:
            raise ValueError(role + " does not match the official restore manifest")
        report["components"][role] = {"bytes": size, "sha256": sha256.hexdigest(),
            "manifest_algorithm": algorithm, "manifest_digest_verified": True}


def _read_private_document(path, *, plist=False, maximum=4 * 1024 * 1024):
    with read_regular(path) as stream:
        size = os.fstat(stream.fileno()).st_size
        if size > maximum:
            raise ValueError("Private chain document exceeds bound")
        data = stream.read(size + 1)
    if len(data) != size:
        raise ValueError("Private chain document changed size")
    return plistlib.loads(data) if plist else json.loads(data)


def reuse_restore_ticket(*, socket_path, build_manifest, components, chain_personalization,
                         output, developer_host_bypass=False, original_inputs=(), deadline=None):
    """Reuse the same live iBEC chain's ticket; never request a replacement.

    LocalPolicy binds the entire next-stage IM4M hash. A later server-issued
    ticket can differ even when nonces are unchanged, so a restore must retain
    the original chain ticket. The guest still performs all trust checks.
    """
    authorization = authorize_host(developer_host_bypass=developer_host_bypass)
    _time_left(deadline)
    if not isinstance(components, dict) or not components or not set(components) <= RESTORE_ROLES:
        raise ValueError("Only named standard restore components are supported")
    chain = Path(chain_personalization).absolute()
    chain_inputs = load_manifest(chain / "inputs.json")
    require_intact(chain_inputs)
    names = ["inputs.json", "result.json", "identity.plist", "live-parameters.private.plist",
             "apple-ticket.private.im4m", "restore-policy/live-parameters.private.plist"]
    paths = [build_manifest, *components.values(), *original_inputs,
             *(chain / name for name in names), *(record.path for record in chain_inputs.artifacts)]
    sources = create_manifest(list(dict.fromkeys(os.path.abspath(os.fspath(path)) for path in paths)))
    directory = Path(output).absolute()
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o700)
    write_manifest(sources, directory / "inputs.json")
    report = {"schema": 1, "component": "restore-chain", "components": {},
              "host_authorization": authorization.to_dict(), "ticket_received": False,
              "ticket_reused": False, "network_request_sent": False,
              "macos_boot_verified": False, "stage": "validate-chain"}
    try:
        manifest = read_build_manifest(build_manifest)
        previous = _read_private_document(chain / "result.json")
        parameters = _read_private_document(chain / "live-parameters.private.plist", plist=True)
        policy = _read_private_document(chain / "restore-policy/live-parameters.private.plist", plist=True)
        old_identity = _read_private_document(chain / "identity.plist", plist=True, maximum=MAX_BUILD_MANIFEST)
        if (previous.get("component") != "iBEC" or previous.get("ticket_received") is not True
                or previous.get("payload_preserved") is not True
                or previous.get("input_integrity", {}).get("valid") is not True
                or previous.get("restore_policy", {}).get("ticket_received") is not True):
            raise ValueError("A successful preserved iBEC and LocalPolicy chain is required")
        with read_regular(chain / "apple-ticket.private.im4m") as stream:
            size = os.fstat(stream.fileno()).st_size
            if size > 4 * 1024 * 1024:
                raise ValueError("Chain ticket exceeds bound")
            ticket = stream.read(size + 1)
        _der_content(ticket, b"IM4M")
        ticket_hash = hashlib.sha384(ticket).digest()
        if (policy.get("Ap,NextStageIM4MHash") != ticket_hash
                or previous["restore_policy"].get("next_stage_ticket_sha384") != ticket_hash.hex()
                or policy.get("Ap,LocalBoot") is not False
                or policy.get("Ap,LocalPolicy") != {"Digest": hashlib.sha384(RESTORE_POLICY).digest(), "Trusted": True}):
            raise ValueError("LocalPolicy does not bind this exact iBEC chain ticket")
        report["stage"] = "read-live-identity"
        with RecoveryTransport(socket_path, _time_left(deadline, 10)) as transport:
            live = _identity(transport, require_dfu_idle=False, deadline=deadline)
            identity = _select_identity(manifest, live)
            if identity != old_identity:
                raise ValueError("Live restore identity differs from the original iBEC chain")
            required = _parameters(live)
            for name, value in required.items():
                if type(parameters.get(name)) is not type(value) or parameters[name] != value:
                    raise ValueError("Live guest identity or nonce differs from the original iBEC chain")
                if type(policy.get(name)) is not type(value) or policy[name] != value:
                    raise ValueError("Live guest identity or nonce differs from the original LocalPolicy")
            report["stage"] = "validate-components"
            _validate_restore_components(identity, components, report)
            require_intact(sources)
            if _identity(transport, require_dfu_idle=False, deadline=deadline) != live:
                raise RuntimeError("Live guest identity or nonce changed during chain validation")
            ticket_path = directory / "apple-ticket.private.im4m"
            ticket_path.write_bytes(ticket)
            report.update(stage="complete", ticket_received=True, ticket_reused=True,
                          ticket_path=str(ticket_path), ticket_sha256=hashlib.sha256(ticket).hexdigest(),
                          next_stage_ticket_sha384=ticket_hash.hex())
    except BaseException as exc:
        report.update(error_type=type(exc).__name__, error=str(exc)[:1024])
        raise
    finally:
        _finish_report(sources, report, directory, [directory / "apple-ticket.private.im4m"])
    return report
