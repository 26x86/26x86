"""Bounded VMApple recovery transport; USB status always comes from the guest.

The LE32 socket framing belongs to our host interface. Payload layout follows
the independently observed VMApple USB DMA interface; no reply is fabricated.
"""

import hashlib
from pathlib import Path
import socket
import struct
import time
import zlib

from .artifacts import create_manifest, read_regular, verify_manifest

# iBSS recovery receives a 1 MiB payload and a six-byte BDIF header.
MAX_FRAME = 1024 * 1024 + 6
MAX_DFU_IMAGE = 64 * 1024 * 1024
MAX_RECOVERY_IMAGE = 512 * 1024 * 1024
DFU_BLOCK_SIZE = 2048
DFU_SUFFIX = bytes.fromhex("ffffffffac05000155464410")


class RecoveryProtocolError(RuntimeError):
    pass


class RecoveryStallError(RecoveryProtocolError):
    """The original guest explicitly returned a type-2 endpoint STALL."""

    def __init__(self, response):
        self.response_hex = response.hex()
        super().__init__("Guest USB endpoint stalled: " + self.response_hex)


class RecoveryUploadError(RecoveryProtocolError):
    """A failed upload with the original replies and partial progress retained."""

    def __init__(self, message, report):
        super().__init__(message)
        self.report = report


class RecoveryTransport:
    def __init__(self, path, timeout=5):
        if not hasattr(socket, "AF_UNIX"):
            raise ValueError("Recovery transport requires Unix sockets")
        if not 0 < timeout <= 60:
            raise ValueError("Recovery timeout must be between 0 and 60 seconds")
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.timeout = timeout
        self.deadline = None
        self.socket.settimeout(timeout)
        try:
            self.socket.connect(str(path))
        except BaseException:
            self.socket.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.socket.close()

    def _read(self, count):
        data = bytearray()
        while len(data) < count:
            self._bound_wait()
            chunk = self.socket.recv(count - len(data))
            if not chunk:
                raise RecoveryProtocolError("Recovery socket disconnected mid-frame")
            data.extend(chunk)
        return bytes(data)

    def _bound_wait(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Recovery control-transfer deadline exceeded")
        self.socket.settimeout(remaining)

    def _receive(self, expected_type, endpoint=0):
        size = struct.unpack("<I", self._read(4))[0]
        if not 2 <= size <= MAX_FRAME:
            raise RecoveryProtocolError("Invalid recovery frame length")
        response = self._read(size)
        if response == bytes((2, endpoint)):
            raise RecoveryStallError(response)
        if response[0] != expected_type or response[1] != endpoint:
            raise RecoveryProtocolError("Guest reported an unexpected transfer type or endpoint")
        return response[2:]

    def _send(self, transfer_type, data, endpoint=0):
        packet = struct.pack("<iBB", len(data), endpoint, transfer_type) + data
        if len(packet) > MAX_FRAME:
            raise ValueError("Recovery packet exceeds transport bound")
        self._bound_wait()
        self.socket.sendall(struct.pack("<I", len(packet)) + packet)

    def control(self, request_type, request, value=0, index=0, *, length=0, data=b"", deadline=None):
        if not all(type(n) is int for n in (request_type, request, value, index, length)):
            raise ValueError("USB setup fields must be integers")
        if not (0 <= request_type <= 255 and 0 <= request <= 255
                and 0 <= value <= 65535 and 0 <= index <= 65535 and 0 <= length <= 65535):
            raise ValueError("USB setup field out of range")
        incoming = bool(request_type & 0x80)
        if incoming and data or (not incoming and length != len(data)):
            raise ValueError("USB direction and data phase disagree")
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        # AVPBooter 7459.141.1, 0x10dbac..0x10dc34, splits a type-1
        # packet into the eight-byte SETUP and following OUT data. Type 3
        # cancels a queue; its type-5 acknowledgement is not a data ACK.
        setup = struct.pack("<BBHHH", request_type, request, value, index, length)
        self._send(1, setup + data)
        payload = self._receive(1)
        if incoming and len(payload) > length:
            raise RecoveryProtocolError("Guest returned more USB data than requested")
        if not incoming and payload:
            raise RecoveryProtocolError("Unexpected payload on a USB OUT completion")
        return payload

    def descriptor(self, kind, index=0, length=255, language=0, *, deadline=None):
        return self.control(0x80, 6, kind << 8 | index, language, length=length, deadline=deadline)

    def configure_recovery(self, *, deadline=None):
        """Select the actual recovery configuration and its bulk OUT endpoint."""
        descriptor = self.descriptor(1, length=18, deadline=deadline)
        if (len(descriptor) != 18 or descriptor[:2] != b"\x12\x01"
                or descriptor[8:10] != b"\xac\x05"
                or not 0x1280 <= int.from_bytes(descriptor[10:12], "little") <= 0x1283):
            raise RecoveryProtocolError("Expected an actual Apple recovery device")
        header = self.descriptor(2, length=9, deadline=deadline)
        if len(header) != 9 or header[:2] != b"\x09\x02":
            raise RecoveryProtocolError("Missing recovery configuration header")
        length = int.from_bytes(header[2:4], "little")
        configuration = self.descriptor(2, length=length, deadline=deadline)
        if len(configuration) != length or length < 9:
            raise RecoveryProtocolError("Truncated recovery configuration")
        offset, found = 0, False
        while offset < length:
            size = configuration[offset]
            if size < 2 or offset + size > length:
                raise RecoveryProtocolError("Invalid recovery USB descriptor structure")
            item = configuration[offset:offset + size]
            if item[1] == 5 and size >= 7 and item[2] == 4 and item[3] & 3 == 2:
                found = True
            offset += size
        if not found:
            raise RecoveryProtocolError("Recovery bulk OUT endpoint 4 was not advertised")
        self.control(0, 9, value=configuration[5], deadline=deadline)
        # libirecovery only claims interface 0 locally; it does not send
        # SET_INTERFACE for that interface's sole alternate setting.
        return {"device_descriptor_hex": descriptor.hex(),
                "configuration_hex": configuration.hex(), "bulk_out_endpoint": 4}

    def bulk_out(self, data, *, endpoint=4, deadline=None):
        """Send a type-1 endpoint packet; only a matching guest ACK completes it."""
        if type(endpoint) is not int or not 1 <= endpoint <= 15:
            raise ValueError("Expected a USB OUT endpoint number")
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        self._send(1, data, endpoint)
        if self._receive(1, endpoint):
            raise RecoveryProtocolError("Unexpected payload on bulk OUT acknowledgement")

    def bulk_in(self, *, endpoint=0x81, deadline=None):
        """Request queued endpoint data. An empty reply remains empty."""
        if type(endpoint) is not int or not 0x81 <= endpoint <= 0x8f:
            raise ValueError("Expected a USB IN endpoint address")
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        self._send(1, b"", endpoint)
        return self._receive(1, endpoint)

    def send_command(self, command, *, request=0, deadline=None):
        """Transmit an iBoot command; ACK alone does not prove command success."""
        data = command.encode("ascii")
        if not data or len(data) >= 256 or any(value < 32 or value > 126 for value in data):
            raise ValueError("Expected 1..255 printable ASCII command bytes")
        # libirecovery irecv_send_command_raw uses vendor OUT + trailing NUL.
        return self.control(0x40, request, length=len(data) + 1, data=data + b"\0", deadline=deadline)

    def send_recovery_file(self, image_path, *, total_timeout=300, expected_sha256=None):
        """Send original file bytes via recovery bulk; no DFU suffix or execution."""
        if not 0 < total_timeout <= 3600:
            raise ValueError("Recovery upload deadline must be between 0 and 3600 seconds")
        deadline = time.monotonic() + total_timeout
        path = Path(image_path)
        manifest = create_manifest([path])
        record = manifest.artifacts[0]
        if not 0 < record.size_bytes <= MAX_RECOVERY_IMAGE:
            raise ValueError("Recovery input exceeds the supported 512 MiB bound")
        digest = record.sha256
        if expected_sha256 is not None and digest != expected_sha256.lower():
            raise ValueError("Recovery input SHA-256 does not match required artifact")
        report = {"schema": 1, "image_size": record.size_bytes, "image_sha256": digest,
                  "bytes_sent": 0, "blocks": [], "zero_length_packet": False,
                  "transfer_complete": False, "input_integrity": False,
                  "signature_acceptance_verified": False, "macos_boot_verified": False,
                  "error": None}
        failure = None
        try:
            # Keep large restore ramdisks bounded in memory; compare the bytes
            # actually transmitted against the preflight manifest as well.
            sent_digest = hashlib.sha256()
            with read_regular(path) as source:
                self.control(0x41, 0, deadline=deadline)
                for offset in range(0, record.size_bytes, 0x8000):
                    size = min(0x8000, record.size_bytes - offset)
                    block = source.read(size)
                    if len(block) != size:
                        raise RecoveryProtocolError("Recovery source became shorter during upload")
                    self.bulk_out(block, deadline=deadline)
                    sent_digest.update(block)
                    report["bytes_sent"] += len(block)
                    report["blocks"].append({"offset": offset, "size": len(block), "acknowledged": True})
                if source.read(1) or sent_digest.hexdigest() != digest:
                    raise RecoveryProtocolError("Transmitted recovery bytes differ from preflight manifest")
            if record.size_bytes % 512 == 0:
                self.bulk_out(b"", deadline=deadline)
                report["zero_length_packet"] = True
            report["transfer_complete"] = True
        except BaseException as exc:
            failure = exc
            report["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            integrity = verify_manifest(manifest)
            report["input_integrity"] = integrity.valid
            report["input_integrity_report"] = integrity.to_dict()
            if not integrity.valid:
                failure = RecoveryProtocolError("Recovery source changed during upload")
                report["error"] = str(failure)
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            failure.recovery_report = report
            raise failure
        if failure is not None:
            raise RecoveryUploadError(report["error"], report) from failure
        return report

    def dfu_state(self, *, deadline=None):
        data = self.control(0xa1, 5, length=1, deadline=deadline)
        if len(data) != 1 or data[0] > 10:
            raise RecoveryProtocolError("DFU GETSTATE did not return a real valid one-byte state")
        return data[0]

    def dfu_status(self, *, deadline=None):
        data = self.control(0xa1, 3, length=6, deadline=deadline)
        if len(data) != 6 or data[0] > 15 or data[4] > 10:
            raise RecoveryProtocolError("DFU GETSTATUS must return six valid bytes; empty replies are failures")
        return {"raw": data.hex(), "status": data[0],
                "poll_timeout_ms": int.from_bytes(data[1:4], "little"),
                "state": data[4], "string_index": data[5]}

    def usb_reset(self, *, deadline=None):
        """Request the original controller's bus-reset event, not a VM reset."""
        self.deadline = time.monotonic() + self.timeout
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        # 0x1074dc sends ACK type 4; callback 0x10db64 maps type 2 to
        # the USB stack's bus-reset handler 0x108e10(event=2).
        self._send(2, b"")
        if self._receive(4):
            raise RecoveryProtocolError("Unexpected payload on USB reset acknowledgement")

    def send_dfu_file(self, image_path, *, total_timeout=300, reset=False,
                      expected_sha256=None):
        """Upload unchanged file bytes plus the standard DFU transport suffix.

        Completion means that the original DFU engine reached WAIT_RESET.
        It does not establish IMG4 acceptance, signature validity, or boot.
        RecoveryUploadError.report preserves progress on protocol failure.
        """
        if not 0 < total_timeout <= 3600:
            raise ValueError("DFU upload deadline must be between 0 and 3600 seconds")
        path = Path(image_path)
        with read_regular(path) as source:
            image = source.read(MAX_DFU_IMAGE + 1)
        if not 0 < len(image) <= MAX_DFU_IMAGE:
            raise ValueError("DFU input changed size or exceeds 64 MiB")
        digest = hashlib.sha256(image).hexdigest()
        if expected_sha256 is not None and digest != expected_sha256.lower():
            raise ValueError("DFU input SHA-256 does not match the required artifact")
        manifest = create_manifest([path])
        if manifest.artifacts[0].sha256 != digest:
            raise ValueError("DFU input changed before upload")
        # libirecovery's reflected CRC starts at FFFFFFFF and has no final
        # xor; Python's zlib.crc32 includes that final xor, undone below.
        suffix = DFU_SUFFIX + struct.pack("<I", zlib.crc32(image + DFU_SUFFIX) ^ 0xffffffff)
        wire_data = image + suffix
        deadline = time.monotonic() + total_timeout
        report = {"schema": 1, "image_path": str(path), "image_size": len(image),
                  "image_sha256": digest, "dfu_suffix_hex": suffix.hex(),
                  "bytes_sent": 0, "image_bytes_sent": 0, "blocks": [],
                  "manifest_statuses": [], "transfer_complete": False,
                  "usb_reset_acknowledged": False, "guest_responses_preserved": True,
                  "signature_acceptance_verified": False, "macos_boot_verified": False,
                  "input_integrity": False, "error": None}
        failure = None
        try:
            initial = self.dfu_state(deadline=deadline)
            report["initial_state"] = initial
            if initial != 2:
                raise RecoveryProtocolError(f"DFU upload requires actual IDLE state 2; got {initial}")
            for number, offset in enumerate(range(0, len(wire_data), DFU_BLOCK_SIZE)):
                block = wire_data[offset:offset + DFU_BLOCK_SIZE]
                self.control(0x21, 1, value=number, length=len(block), data=block, deadline=deadline)
                report["bytes_sent"] += len(block)
                report["image_bytes_sent"] = min(report["bytes_sent"], len(image))
                entry = {"number": number, "size": len(block), "statuses": []}
                report["blocks"].append(entry)
                self._dfu_wait(5, {3, 4}, deadline, entry["statuses"])
            self.control(0x21, 1, value=len(report["blocks"]), deadline=deadline)
            self._dfu_wait(8, {6, 7}, deadline, report["manifest_statuses"])
            report["final_state"] = self.dfu_state(deadline=deadline)
            if report["final_state"] != 8:
                raise RecoveryProtocolError("DFU state changed before bus reset")
            report["transfer_complete"] = True
            if reset:
                self.usb_reset(deadline=deadline)
                report["usb_reset_acknowledged"] = True
        except BaseException as exc:
            failure = exc
            report["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            integrity = verify_manifest(manifest)
            report["input_integrity"] = integrity.valid
            report["input_integrity_report"] = integrity.to_dict()
            if not integrity.valid:
                failure = RecoveryProtocolError("DFU source changed during upload")
                report["error"] = str(failure)
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            failure.recovery_report = report
            raise failure
        if failure is not None:
            raise RecoveryUploadError(report["error"], report) from failure
        return report

    def _dfu_wait(self, target, transient_states, deadline, replies):
        while True:
            status = self.dfu_status(deadline=deadline)
            replies.append(status)
            if status["status"]:
                raise RecoveryProtocolError(f"Guest DFU error {status['status']} in state {status['state']}")
            if status["state"] == target:
                return
            if status["state"] not in transient_states:
                raise RecoveryProtocolError(f"Unexpected DFU state {status['state']}; expected {target}")
            delay = max(status["poll_timeout_ms"] / 1000, 0.001)
            remaining = deadline - time.monotonic()
            if delay >= remaining:
                raise TimeoutError("Guest DFU poll delay exceeds the remaining upload deadline")
            until = time.monotonic() + delay
            while True:
                remaining_delay = until - time.monotonic()
                if remaining_delay <= 0:
                    break
                time.sleep(min(remaining_delay, 0.25))


def send_dfu_file(path, image_path, *, timeout=5, total_timeout=300,
                  reset=False, expected_sha256=None):
    """Connect and upload; caller provides host authorization and asset policy."""
    with RecoveryTransport(path, timeout) as transport:
        return transport.send_dfu_file(image_path, total_timeout=total_timeout,
                                       reset=reset, expected_sha256=expected_sha256)


def probe_recovery(path, timeout=5):
    with RecoveryTransport(path, timeout) as transport:
        device = transport.descriptor(1, length=18)
        if len(device) != 18 or device[:2] != b"\x12\x01":
            raise RecoveryProtocolError("Missing complete USB device descriptor")
        vendor, product = struct.unpack_from("<HH", device, 8)
        header = transport.descriptor(2, length=9)
        if len(header) != 9 or header[:2] != b"\x09\x02":
            raise RecoveryProtocolError("Missing USB configuration header")
        size = int.from_bytes(header[2:4], "little")
        if not 9 <= size <= 4096:
            raise RecoveryProtocolError("USB configuration length exceeds supported limit")
        configuration = transport.descriptor(2, length=size)
        if len(configuration) != size or configuration[:9] != header:
            raise RecoveryProtocolError("USB configuration descriptor is inconsistent")
        transport.control(0, 5, value=1)
        transport.control(0, 9, value=header[5])
        state = transport.dfu_state()
        status = transport.dfu_status()
        return {"schema": 1, "usb_vendor": vendor, "usb_product": product,
                "device_descriptor": device.hex(), "configuration_descriptor": configuration.hex(),
                "dfu_state": state, "dfu_status": status,
                "guest_responses_preserved": True, "macos_boot_verified": False,
                "meaning": "Observed recovery USB enumeration and DFU responses, not attestation or macOS boot."}
