#!/usr/bin/env python3
"""Send one preserved Apple DFU image to the VMApple TCG Stage0 socket.

The QEMU VMApple BDIF USB bridge uses a length-prefixed Unix socket.  Each
payload contains the bridge's six-byte transfer header followed by either an
8-byte USB setup packet or a DFU data packet.  This is the host-side transport
only: it does not create an IMG4 manifest, personalize an image, or turn an
ACK into proof that iBSS accepted the signature.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import socket
import struct
import sys
import time
import zlib


MAX_IMAGE_BYTES = 64 * 1024 * 1024
DEFAULT_BLOCK_BYTES = 2048
DFU_SUFFIX = bytes.fromhex("ffffffffac05000155464410")


class DfuTransportError(RuntimeError):
    """The VMApple DFU transport returned an invalid or stalled response."""


class DfuSocket:
    def __init__(self, path: str, timeout: float) -> None:
        if not 0 < timeout <= 60:
            raise ValueError("timeout must be between 0 and 60 seconds")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect(path)

    def close(self) -> None:
        self.sock.close()

    def __enter__(self) -> "DfuSocket":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _read_exact(self, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            chunk = self.sock.recv(size - len(result))
            if not chunk:
                raise DfuTransportError("VMApple DFU socket closed mid-frame")
            result.extend(chunk)
        return bytes(result)

    def receive(self) -> tuple[int, int, bytes]:
        frame_size = struct.unpack("<I", self._read_exact(4))[0]
        if not 2 <= frame_size <= MAX_IMAGE_BYTES + 64:
            raise DfuTransportError(f"invalid VMApple frame size {frame_size}")
        frame = self._read_exact(frame_size)
        if len(frame) < 2:
            raise DfuTransportError("VMApple response is missing its transfer header")
        # The guest-to-host response is already framed by the outer uint32:
        # its first two bytes are transfer type and endpoint.  The six-byte
        # ``<iBB`` header exists only on host-to-guest packets accepted by
        # vmapple-bdif.
        return frame[0], frame[1], frame[2:]

    def send_frame(self, transfer_type: int, payload: bytes, endpoint: int = 0) -> None:
        if not 0 <= transfer_type <= 255 or not 0 <= endpoint <= 255:
            raise ValueError("VMApple transfer header is out of range")
        frame = struct.pack("<iBB", len(payload), endpoint, transfer_type) + payload
        self.sock.sendall(struct.pack("<I", len(frame)) + frame)

    def setup(self, request_type: int, request: int, *, value: int = 0,
              index: int = 0, length: int = 0) -> bytes:
        """Return the eight-byte USB setup packet without a BDIF header.

        Current mBoot (20457.x) consumes a type-1 host frame whose payload is
        ``SETUP || OUT_DATA``.  Older experiments sent a setup frame followed
        by type 3; that type is a queue-cancel operation in this firmware and
        must not be used for DFU data.
        """
        return struct.pack(
            "<BBHHH", request_type, request, value, index, length,
        )

    def _control(self, request_type: int, request: int, *, value: int = 0,
                 index: int = 0, length: int = 0, data: bytes = b"") -> bytes:
        incoming = bool(request_type & 0x80)
        if incoming and data:
            raise ValueError("USB IN control requests cannot carry OUT data")
        if not incoming and len(data) != length:
            raise ValueError("USB OUT control length does not match its data")
        self.send_frame(1, self.setup(
            request_type, request, value=value, index=index, length=length
        ) + data)
        transfer_type, endpoint, payload = self.receive()
        if (transfer_type, endpoint) == (2, 0):
            raise DfuTransportError("VMApple DFU control request stalled")
        if (transfer_type, endpoint) != (1, 0):
            raise DfuTransportError(
                f"unexpected control response type={transfer_type} endpoint={endpoint}"
            )
        if incoming and len(payload) > length:
            raise DfuTransportError("VMApple DFU control response exceeds requested length")
        if not incoming and payload:
            raise DfuTransportError("VMApple DFU OUT completion carried unexpected data")
        return payload

    def control_in(self, request_type: int, request: int, *, value: int = 0,
                   index: int = 0, length: int = 0) -> bytes:
        return self._control(
            request_type, request, value=value, index=index, length=length
        )

    def control_out_data(self, request: int, block: int, data: bytes) -> dict[str, object]:
        payload = self._control(
            0x21, request, value=block, length=len(data), data=data
        )
        return {
            "response_type": 1,
            "endpoint": 0,
            "payload_hex": payload.hex(),
            "accepted": not payload,
        }

    def control_out_empty(self, request: int, block: int) -> dict[str, object]:
        payload = self._control(
            0x21, request, value=block, length=0
        )
        return {
            "response_type": 1,
            "endpoint": 0,
            "payload_hex": payload.hex(),
            "accepted": not payload,
        }

    def usb_reset(self) -> dict[str, object]:
        """Forward the AVP host-side USB reset event after DFU manifestation.

        Current mBoot represents the bus reset as a type-2 event and returns a
        type-4 acknowledgement.  Type 0 is not the reset event here.
        """
        self.send_frame(2, b"")
        transfer_type, endpoint, payload = self.receive()
        if (transfer_type, endpoint) != (4, 0):
            raise DfuTransportError(
                f"unexpected USB reset response type={transfer_type} endpoint={endpoint}"
            )
        if payload:
            raise DfuTransportError("USB reset acknowledgement carried unexpected data")
        return {
            "transfer_type": transfer_type,
            "endpoint": endpoint,
            "payload_hex": "",
            "sent": True,
            "acknowledged": True,
            "guest_signature_acceptance_verified": False,
        }

    def dfu_state(self) -> int:
        state = self._control(0xA1, 5, length=1)
        if len(state) != 1 or state[0] > 10:
            raise DfuTransportError("DFU GETSTATE did not return a valid one-byte state")
        return state[0]

    def dfu_status(self) -> dict[str, object]:
        status = self._control(0xA1, 3, length=6)
        if len(status) != 6 or status[0] > 15 or status[4] > 10:
            raise DfuTransportError("DFU GETSTATUS did not return six valid bytes")
        return {
            "raw": status.hex(),
            "status": status[0],
            "poll_timeout_ms": int.from_bytes(status[1:4], "little"),
            "state": status[4],
            "string_index": status[5],
        }

    def wait_dfu_state(self, target: int, transient: set[int], *, limit: int = 64) -> list[dict[str, object]]:
        """Poll real DFU status until ``target``; never treat empty data as success."""
        replies: list[dict[str, object]] = []
        for _ in range(limit):
            status = self.dfu_status()
            replies.append(status)
            if status["status"]:
                raise DfuTransportError(
                    f"DFU error {status['status']} in state {status['state']}"
                )
            if status["state"] == target:
                return replies
            if status["state"] not in transient:
                raise DfuTransportError(
                    f"unexpected DFU state {status['state']}; expected {target}"
                )
            delay = max(int(status["poll_timeout_ms"]) / 1000, 0.001)
            time.sleep(min(delay, 0.25))
        raise DfuTransportError(f"DFU state did not reach {target} within {limit} polls")


def upload(path: Path, socket_path: str, *, block_bytes: int, timeout: float,
           report_path: Path | None = None) -> dict[str, object]:
    image = path.read_bytes()
    if not 0 < len(image) <= MAX_IMAGE_BYTES - len(DFU_SUFFIX) - 4:
        raise ValueError("DFU image must be between 1 byte and 64 MiB")
    if not 1 <= block_bytes <= 64 * 1024:
        raise ValueError("DFU block size must be between 1 and 65536 bytes")

    report: dict[str, object] = {
        "schema": "26x86.vmapple-tcg-dfu/1",
        "socket": socket_path,
        "image": {
            "path": str(path),
            "bytes": len(image),
            "sha256": hashlib.sha256(image).hexdigest(),
        },
        "dfu_suffix_hex": None,
        "wire_image": None,
        "block_bytes": block_bytes,
        "enumeration": None,
        "blocks": [],
        "block_statuses": [],
        "manifest": None,
        "statuses": [],
        "usb_reset": None,
        "transport_complete": False,
        "guest_signature_acceptance_verified": False,
        "error": None,
    }

    try:
        with DfuSocket(socket_path, timeout) as transport:
            device = transport.control_in(0x80, 6, value=0x0100, length=18)
            header = transport.control_in(0x80, 6, value=0x0200, length=9)
            if len(header) != 9:
                raise DfuTransportError("USB configuration header is incomplete")
            total = int.from_bytes(header[2:4], "little")
            configuration = transport.control_in(0x80, 6, value=0x0200, length=total)
            address = transport._control(0x00, 5, value=1)
            config_set = transport._control(0x00, 9, value=1)
            state = transport.dfu_state()
            report["enumeration"] = {
                "device_descriptor_hex": device.hex(),
                "configuration_hex": configuration.hex(),
                "address_reply_hex": address.hex(),
                "configuration_reply_hex": config_set.hex(),
                "initial_dfu_state": state,
            }

            suffix = DFU_SUFFIX + struct.pack(
                "<I", zlib.crc32(image + DFU_SUFFIX) ^ 0xFFFFFFFF
            )
            wire_image = image + suffix
            report["dfu_suffix_hex"] = suffix.hex()
            report["wire_image"] = {
                "bytes": len(wire_image),
                "sha256": hashlib.sha256(wire_image).hexdigest(),
            }

            blocks = report["blocks"]
            assert isinstance(blocks, list)
            initial_state = state
            if initial_state != 2:
                raise DfuTransportError(
                    f"DFU upload requires idle state 2; got {initial_state}"
                )
            for number, offset in enumerate(range(0, len(wire_image), block_bytes)):
                result = transport.control_out_data(
                    1, number, wire_image[offset:offset + block_bytes]
                )
                result.update({"number": number, "bytes": min(block_bytes, len(wire_image) - offset)})
                blocks.append(result)
                report["block_statuses"].append({
                    "number": number,
                    "statuses": transport.wait_dfu_state(5, {3, 4}),
                })
            manifest = transport.control_out_empty(
                1, (len(wire_image) + block_bytes - 1) // block_bytes
            )
            report["manifest"] = manifest
            report["statuses"] = transport.wait_dfu_state(8, {6, 7})
            report["transport_complete"] = transport.dfu_state() == 8
            if not report["transport_complete"]:
                raise DfuTransportError("DFU manifestation did not reach state 8")
            report["usb_reset"] = transport.usb_reset()
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        # The report is intentionally transport-only.  A successful data
        # phase cannot establish cryptographic acceptance or Stage1 execution.
        report["guest_signature_acceptance_verified"] = False
        if report_path is not None:
            report_path.write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("socket")
    parser.add_argument("image", type=Path)
    parser.add_argument("--block-bytes", type=int, default=DEFAULT_BLOCK_BYTES)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = upload(
        args.image.resolve(), args.socket,
        block_bytes=args.block_bytes, timeout=args.timeout,
        report_path=args.report.resolve() if args.report else None,
    )
    encoded = json.dumps(report, indent=2)
    print(encoded)
    if args.report:
        args.report.write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, DfuTransportError) as exc:
        print(f"vmapple_tcg_dfu: {exc}", file=sys.stderr)
        raise SystemExit(1)
