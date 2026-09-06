"""Original-preserving VMApple GUI runner and DFU transition probe.

This module is a 26x86 research control plane, not a macOS image patcher.
Apple firmware and storage inputs are supplied by the caller, verified before
use, and never modified.  The current VMApple backend is expected to run in a
POSIX/WSL environment because its recovery socket is a Unix socket.

The runner deliberately stops when iBSS does not advertise the next recovery
endpoint.  It never fabricates a descriptor, changes an IMG4 signature, or
forces an iBSS-to-iBEC transition.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import zlib

from .iboot_personality import (
    DEFAULT_RECOVERY_IMAGE,
    IBOOT_MACHINE_TYPE,
    MACOS_GUEST_OS,
    default_scope,
    validate_iboot_scope,
)
from .boot_picker import (
    BOOT_DELAY_SECONDS,
    DEFAULT_ALT_KEY,
    MACOS_ENTRY_ID,
    RECOVERY_ENTRY_ID,
    validate_boot_picker_config,
)


MAX_FIRMWARE_BYTES = 1 * 1024 * 1024
MAX_DFU_BYTES = 64 * 1024 * 1024
MAX_RECOVERY_BYTES = 512 * 1024 * 1024
MAX_FRAME_BYTES = MAX_RECOVERY_BYTES + 6
DFU_BLOCK_BYTES = 2048
DFU_SUFFIX = bytes.fromhex("ffffffffac05000155464410")
MAX_TRANSITION_ATTEMPTS = 240
MAX_LOG_BYTES = 16 * 1024 * 1024


class VMappleError(RuntimeError):
    """A bounded launch or recovery-protocol failure."""


class RecoveryProtocolError(VMappleError):
    """The guest returned a malformed or unsupported recovery response."""


@dataclass(frozen=True)
class Executable:
    """An executable and the way the current host invokes it."""

    program: str
    wrapper: str | None = None

    @property
    def is_wsl(self) -> bool:
        return self.wrapper is not None

    def command(self, *arguments: str) -> list[str]:
        if self.wrapper is None:
            return [self.program, *arguments]
        return [self.wrapper, "--", self.program, *arguments]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular(value: str | Path, label: str, *, limit: int | None = None) -> Path:
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    size = path.stat().st_size
    if limit is not None and size > limit:
        raise ValueError(f"{label} exceeds the {limit} byte limit")
    return path


def _to_wsl_path(path: Path) -> str:
    """Convert a Windows path to a path visible from WSL."""
    text = str(path)
    if os.name != "nt":
        return text
    if len(text) >= 2 and text[1] == ":":
        tail = text[2:].replace("\\", "/")
        return f"/mnt/{text[0].lower()}{tail}"
    return text.replace("\\", "/")


def _resolve_executable(value: str | Path | None, default: str, label: str) -> Executable:
    raw = str(value or os.environ.get(default) or "").strip()
    if not raw:
        raw = shutil.which(label) or ""
    if not raw:
        raise ValueError(f"{label} was not found; set {default}")

    # VMApple's private backend is a Linux binary.  A Windows GUI may pass its
    # WSL path to the bridge, which launches the full runner inside WSL.
    if os.name == "nt" and raw.startswith("/"):
        wrapper = shutil.which("wsl.exe")
        if wrapper is None:
            raise ValueError("A WSL VMApple executable was supplied but wsl.exe is unavailable")
        probe = subprocess.run([wrapper, "--", raw, "--version"], capture_output=True,
                               text=True, timeout=10, check=False)
        if probe.returncode != 0:
            raise ValueError(f"{label} cannot be executed through WSL: {probe.stderr.strip()}")
        return Executable(raw, wrapper)

    candidate = Path(raw).expanduser()
    if candidate.parent == Path("."):
        located = shutil.which(raw)
        if located is None:
            raise ValueError(f"{label} was not found on PATH: {raw}")
        candidate = Path(located)
    candidate = candidate.resolve(strict=True)
    if not candidate.is_file():
        raise ValueError(f"{label} must be a regular file: {candidate}")
    return Executable(str(candidate))


def _guest_path(path: Path, executable: Executable) -> str:
    return _to_wsl_path(path) if executable.is_wsl else str(path)


def probe_backend(executable: Executable) -> dict[str, object]:
    """Require the VMApple research machine without treating help as boot evidence."""
    version = subprocess.run(executable.command("--version"), capture_output=True,
                             text=True, timeout=15, check=False)
    machines = subprocess.run(executable.command("-machine", "help"), capture_output=True,
                              text=True, timeout=15, check=False)
    accelerators = subprocess.run(executable.command("-accel", "help"), capture_output=True,
                                  text=True, timeout=15, check=False)
    if version.returncode or machines.returncode or accelerators.returncode:
        raise ValueError("QEMU capability probe failed")
    machine_names = {line.split()[0] for line in machines.stdout.splitlines() if line.strip()}
    if "vmapple" not in machine_names or "tcg" not in accelerators.stdout.split():
        raise ValueError("QEMU must expose vmapple and TCG")
    research = subprocess.run(executable.command("-machine", "vmapple,help"),
                              capture_output=True, text=True, timeout=15, check=False)
    if research.returncode or "research-headless" not in research.stdout:
        raise ValueError("QEMU VMApple backend does not advertise research-headless")
    first_line = (version.stdout or version.stderr).splitlines()
    return {
        "executable": executable.program,
        "version": first_line[0] if first_line else "",
        "vmapple": True,
        "tcg": True,
        "research_headless": True,
        "macos_boot_verified": False,
    }


def _qcow_size(path: Path) -> int:
    with path.open("rb") as source:
        header = source.read(104)
    if len(header) != 104 or header[:4] != b"QFI\xfb":
        raise ValueError(f"Invalid qcow2 overlay header: {path}")
    version, backing_offset, backing_size = struct.unpack_from(">IQI", header, 4)
    virtual_size, crypt = struct.unpack_from(">QI", header, 24)
    incompatible = struct.unpack_from(">Q", header, 72)[0]
    if (version != 3 or backing_offset or backing_size or crypt or incompatible & ~1
            or virtual_size <= 0 or virtual_size % 512):
        raise ValueError("Overlay must be qcow2 v3, unencrypted, and have no external backing path")
    return virtual_size


@dataclass(frozen=True)
class StorageSession:
    directory: Path
    aux_base: Path
    root_base: Path
    aux_overlay: Path
    root_overlay: Path
    aux_offset: int

    def arguments(self, executable: Executable) -> list[str]:
        """Build an explicit raw-read-only base + qcow2-writable graph."""
        aux_size = self.aux_base.stat().st_size - self.aux_offset
        root_size = self.root_base.stat().st_size
        if aux_size <= 0 or root_size <= 0 or aux_size % 512 or root_size % 512:
            raise ValueError("AUX view and root base must be nonempty 512-byte multiples")
        if _qcow_size(self.aux_overlay) != aux_size or _qcow_size(self.root_overlay) != root_size:
            raise ValueError("COW overlay size does not match its immutable base view")

        result: list[str] = ["-global", "vmapple-bdif.allow-block-writes=on"]
        for index, (role, base, overlay, size) in enumerate((
            ("aux", self.aux_base, self.aux_overlay, aux_size),
            ("root", self.root_base, self.root_overlay, root_size),
        )):
            # Block node names follow QEMU's identifier grammar (alphanumeric,
            # dot, and hyphen; underscores are rejected before graph parsing).
            # QEMU additionally requires the first character to be alphabetic.
            node_name = "x86" + role
            backing = {
                "driver": "raw",
                "read-only": True,
                "offset": self.aux_offset if role == "aux" else 0,
                "file": {"driver": "file", "filename": _guest_path(base, executable),
                         "read-only": True},
            }
            node = {
                "driver": "qcow2",
                "node-name": node_name,
                "read-only": False,
                "file": {"driver": "file", "filename": _guest_path(overlay, executable)},
                "backing": backing,
            }
            result.extend(["-blockdev", json.dumps(node, separators=(",", ":"))])
            view = "json:" + json.dumps({"driver": "raw", "file": node_name},
                                         separators=(",", ":"))
            # QemuOpts uses doubled commas inside a value.
            result.extend([
                "-drive", f"if=pflash,index={index},readonly=off,file={view.replace(',', ',,')}",
                "-drive", f"if=none,id={role}disk,werror=report,rerror=report,"
                           f"cache=writeback,file={view.replace(',', ',,')}",
                "-device", f"vmapple-virtio-blk-pci,variant={role},drive={role}disk,share-rw=on",
            ])
        return result


def _new_directory(value: str | Path | None) -> Path:
    if value:
        destination = Path(value).expanduser().absolute()
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Output directory must be new: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir()
        return destination
    parent = Path(os.environ.get("X86_VMAPLE_OUTPUT_ROOT", tempfile.gettempdir())).expanduser()
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="26x86-vmapple-", dir=parent))


def create_storage(*, aux: Path, root: Path, directory: Path,
                   qemu_img: Executable, aux_offset: int) -> StorageSession:
    if type(aux_offset) is not int or aux_offset < 0 or aux_offset % 512:
        raise ValueError("AUX offset must be a nonnegative multiple of 512")
    aux_size = aux.stat().st_size - aux_offset
    root_size = root.stat().st_size
    if aux_size <= 0 or root_size <= 0 or aux_size % 512 or root_size % 512:
        raise ValueError("AUX/root inputs must expose nonempty 512-byte views")
    storage = directory / "storage"
    storage.mkdir()
    overlays = (storage / "aux.qcow2", storage / "root.qcow2")
    for overlay, size in zip(overlays, (aux_size, root_size)):
        completed = subprocess.run(
            qemu_img.command("create", "-f", "qcow2", "-o", "compat=1.1,lazy_refcounts=off",
                             _guest_path(overlay, qemu_img), str(size)),
            capture_output=True, text=True, timeout=30, check=False,
        )
        if completed.returncode:
            raise ValueError(f"qemu-img failed to create {overlay.name}: {completed.stderr.strip()}")
        if _qcow_size(overlay) != size:
            raise ValueError(f"qemu-img created an unexpected {overlay.name} size")
    metadata = {
        "schema": 1,
        "base_images_read_only": True,
        "writes": "separate qcow2 overlays",
        "aux_offset": aux_offset,
        "bases": {
            "aux": {"path": str(aux), "bytes": aux.stat().st_size, "sha256": _sha256(aux)},
            "root": {"path": str(root), "bytes": root.stat().st_size, "sha256": _sha256(root)},
        },
        "macos_boot_verified": False,
    }
    (storage / "session.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return StorageSession(directory, aux, root, overlays[0], overlays[1], aux_offset)


class RecoveryTransport:
    """Small host transport for the observed VMApple USB chardev framing."""

    def __init__(self, socket_path: str, timeout: float = 5.0):
        if not hasattr(socket, "AF_UNIX"):
            raise ValueError("VMApple recovery requires Unix sockets; run it inside WSL/Linux")
        if not 0 < timeout <= 60:
            raise ValueError("Recovery socket timeout must be between 0 and 60 seconds")
        self.path = socket_path
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout
        try:
            self.socket.connect(socket_path)
        except BaseException:
            self.socket.close()
            raise

    def __enter__(self) -> "RecoveryTransport":
        return self

    def __exit__(self, *_: object) -> None:
        self.socket.close()

    def _read_exact(self, count: int) -> bytes:
        data = bytearray()
        while len(data) < count:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Recovery socket deadline exceeded")
            self.socket.settimeout(remaining)
            chunk = self.socket.recv(count - len(data))
            if not chunk:
                raise RecoveryProtocolError("Recovery socket closed mid-frame")
            data.extend(chunk)
        return bytes(data)

    def _receive(self, expected_type: int, endpoint: int = 0) -> bytes:
        size = struct.unpack("<I", self._read_exact(4))[0]
        if not 2 <= size <= MAX_FRAME_BYTES:
            raise RecoveryProtocolError("Invalid recovery frame length")
        response = self._read_exact(size)
        if response == bytes((2, endpoint)):
            raise RecoveryProtocolError(f"Guest USB endpoint stalled: {response.hex()}")
        if len(response) < 2 or response[0] != expected_type or response[1] != endpoint:
            raise RecoveryProtocolError("Guest reported an unexpected transfer type or endpoint")
        return response[2:]

    def _send(self, transfer_type: int, data: bytes, endpoint: int = 0) -> None:
        packet = struct.pack("<iBB", len(data), endpoint, transfer_type) + data
        if len(packet) > MAX_FRAME_BYTES:
            raise ValueError("Recovery packet exceeds the transport bound")
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Recovery socket deadline exceeded")
        self.socket.settimeout(remaining)
        self.socket.sendall(struct.pack("<I", len(packet)) + packet)

    def control(self, request_type: int, request: int, value: int = 0, index: int = 0,
                *, length: int = 0, data: bytes = b"") -> bytes:
        fields = (request_type, request, value, index, length)
        if not all(type(item) is int for item in fields):
            raise ValueError("USB setup fields must be integers")
        if not (0 <= request_type <= 255 and 0 <= request <= 255
                and 0 <= value <= 65535 and 0 <= index <= 65535
                and 0 <= length <= 65535):
            raise ValueError("USB setup field out of range")
        incoming = bool(request_type & 0x80)
        if (incoming and data) or (not incoming and length != len(data)):
            raise ValueError("USB direction and data phase disagree")
        setup = struct.pack("<BBHHH", request_type, request, value, index, length)
        self.deadline = time.monotonic() + self.timeout
        self._send(1, setup + data)
        payload = self._receive(1)
        if incoming and len(payload) > length:
            raise RecoveryProtocolError("Guest returned more USB data than requested")
        if not incoming and payload:
            raise RecoveryProtocolError("Unexpected payload on USB OUT completion")
        return payload

    def descriptor(self, kind: int, index: int = 0, length: int = 255) -> bytes:
        return self.control(0x80, 6, kind << 8 | index, 0x409 if kind == 3 else 0,
                            length=length)

    def dfu_state(self) -> int:
        data = self.control(0xA1, 5, length=1)
        if len(data) != 1 or data[0] > 10:
            raise RecoveryProtocolError("DFU GETSTATE did not return one valid byte")
        return data[0]

    def dfu_status(self) -> dict[str, int | str]:
        data = self.control(0xA1, 3, length=6)
        if len(data) != 6 or data[0] > 15 or data[4] > 10:
            raise RecoveryProtocolError("DFU GETSTATUS did not return six valid bytes")
        return {"raw": data.hex(), "status": data[0],
                "poll_timeout_ms": int.from_bytes(data[1:4], "little"),
                "state": data[4], "string_index": data[5]}

    def _wait_state(self, target: int, transient: set[int], deadline: float,
                    records: list[dict[str, int | str]]) -> None:
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("DFU state deadline exceeded")
            status = self.dfu_status()
            records.append(status)
            if status["status"]:
                raise RecoveryProtocolError(f"Guest DFU error {status['status']}")
            if status["state"] == target:
                return
            if status["state"] not in transient:
                raise RecoveryProtocolError(f"Unexpected DFU state {status['state']}; expected {target}")
            time.sleep(min(max(float(status["poll_timeout_ms"]) / 1000, 0.001), 0.25))

    def usb_reset(self) -> None:
        self.deadline = time.monotonic() + self.timeout
        self._send(2, b"")
        if self._receive(4):
            raise RecoveryProtocolError("USB reset acknowledgement contained a payload")

    def bulk_out(self, data: bytes, endpoint: int = 4) -> None:
        self.deadline = time.monotonic() + self.timeout
        self._send(1, data, endpoint)
        if self._receive(1, endpoint):
            raise RecoveryProtocolError("Bulk OUT acknowledgement contained a payload")

    def send_dfu_file(self, path: Path, *, expected_sha256: str | None = None,
                      total_timeout: float = 300, reset: bool = True) -> dict[str, object]:
        image = path.read_bytes()
        if not 0 < len(image) <= MAX_DFU_BYTES:
            raise ValueError("iBSS input must be between 1 byte and 64 MiB")
        digest = hashlib.sha256(image).hexdigest()
        if expected_sha256 and digest != expected_sha256.lower():
            raise ValueError("iBSS SHA-256 does not match the requested artifact")
        suffix = DFU_SUFFIX + struct.pack("<I", zlib.crc32(image + DFU_SUFFIX) ^ 0xFFFFFFFF)
        wire = image + suffix
        deadline = time.monotonic() + total_timeout
        report: dict[str, object] = {
            "schema": 1, "image_path": str(path), "image_size": len(image),
            "image_sha256": digest, "dfu_suffix_hex": suffix.hex(), "bytes_sent": 0,
            "image_bytes_sent": 0, "blocks": [], "manifest_statuses": [],
            "transfer_complete": False, "usb_reset_acknowledged": False,
            "guest_responses_preserved": True, "signature_acceptance_verified": False,
            "macos_boot_verified": False, "input_integrity": False, "error": None,
        }
        try:
            initial = self.dfu_state()
            report["initial_state"] = initial
            if initial != 2:
                raise RecoveryProtocolError(f"DFU upload requires IDLE state 2; got {initial}")
            for number, offset in enumerate(range(0, len(wire), DFU_BLOCK_BYTES)):
                block = wire[offset:offset + DFU_BLOCK_BYTES]
                self.control(0x21, 1, value=number, length=len(block), data=block)
                report["bytes_sent"] = int(report["bytes_sent"]) + len(block)
                report["image_bytes_sent"] = min(int(report["bytes_sent"]), len(image))
                entry: dict[str, object] = {"number": number, "size": len(block), "statuses": []}
                cast_blocks = report["blocks"]
                assert isinstance(cast_blocks, list)
                cast_blocks.append(entry)
                self._wait_state(5, {3, 4}, deadline, entry["statuses"])  # type: ignore[arg-type]
            self.control(0x21, 1, value=len(report["blocks"]))  # type: ignore[arg-type]
            self._wait_state(8, {6, 7}, deadline, report["manifest_statuses"])  # type: ignore[arg-type]
            report["final_state"] = self.dfu_state()
            if report["final_state"] != 8:
                raise RecoveryProtocolError("DFU state changed before USB reset")
            report["transfer_complete"] = True
            if reset:
                self.usb_reset()
                report["usb_reset_acknowledged"] = True
        except BaseException as error:
            report["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            report["input_integrity"] = _sha256(path) == digest
            if not report["input_integrity"]:
                report["error"] = "iBSS source changed during upload"
        return report

    def probe(self) -> dict[str, object]:
        device = self.descriptor(1, length=18)
        if len(device) != 18 or device[:2] != b"\x12\x01":
            raise RecoveryProtocolError("Missing complete USB device descriptor")
        vendor, product = struct.unpack_from("<HH", device, 8)
        header = self.descriptor(2, length=9)
        if len(header) != 9 or header[:2] != b"\x09\x02":
            raise RecoveryProtocolError("Missing USB configuration header")
        length = int.from_bytes(header[2:4], "little")
        if not 9 <= length <= 4096:
            raise RecoveryProtocolError("USB configuration length is out of bounds")
        configuration = self.descriptor(2, length=length)
        if len(configuration) != length or configuration[:9] != header:
            raise RecoveryProtocolError("USB configuration descriptor is inconsistent")
        endpoint: int | None = None
        offset = 0
        while offset < length:
            size = configuration[offset]
            if size < 2 or offset + size > length:
                raise RecoveryProtocolError("Invalid USB descriptor structure")
            item = configuration[offset:offset + size]
            if item[1] == 5 and size >= 7 and item[2] == 4 and item[3] & 3 == 2:
                endpoint = item[2]
            offset += size
        dfu_state_value: int | None = None
        dfu_status_value: dict[str, int | str] | None = None
        dfu_control_error: str | None = None
        try:
            dfu_state_value = self.dfu_state()
            dfu_status_value = self.dfu_status()
        except (RecoveryProtocolError, OSError, TimeoutError) as error:
            # iBEC is a recovery interface, not necessarily a DFU class
            # interface. Keep the descriptor evidence and make this optional
            # control failure explicit instead of hiding a bulk endpoint.
            dfu_control_error = f"{type(error).__name__}: {error}"
        result = {
            "usb_vendor": f"{vendor:04x}", "usb_product": f"{product:04x}",
            "device_descriptor_hex": device.hex(),
            "configuration_hex": configuration.hex(),
            "configuration_value": configuration[5],
            "bulk_out_endpoint": endpoint,
            "dfu_state": dfu_state_value,
            "dfu_status": dfu_status_value,
        }
        if dfu_control_error:
            result["dfu_control_error"] = dfu_control_error
        return result

    def send_recovery_file(self, path: Path, *, total_timeout: float = 300) -> dict[str, object]:
        image = path.read_bytes()
        if not 0 < len(image) <= MAX_RECOVERY_BYTES:
            raise ValueError("iBEC input must be between 1 byte and 512 MiB")
        digest = hashlib.sha256(image).hexdigest()
        deadline = time.monotonic() + total_timeout
        report: dict[str, object] = {
            "schema": 1, "image_path": str(path), "image_size": len(image),
            "image_sha256": digest, "bytes_sent": 0, "blocks": [],
            "transfer_complete": False, "signature_acceptance_verified": False,
            "macos_boot_verified": False, "input_integrity": False, "error": None,
        }
        try:
            self.control(0x41, 0)
            for offset in range(0, len(image), 0x8000):
                if time.monotonic() >= deadline:
                    raise TimeoutError("iBEC upload deadline exceeded")
                block = image[offset:offset + 0x8000]
                self.bulk_out(block)
                report["bytes_sent"] = int(report["bytes_sent"]) + len(block)
                report["blocks"].append({"offset": offset, "size": len(block), "acknowledged": True})
            if len(image) % 512 == 0:
                self.bulk_out(b"")
                report["zero_length_packet"] = True
            report["transfer_complete"] = True
        except BaseException as error:
            report["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            report["input_integrity"] = _sha256(path) == digest
            if not report["input_integrity"]:
                report["error"] = "iBEC source changed during upload"
        return report


def _wait_for_socket(socket_path: str, process: subprocess.Popen[bytes], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise VMappleError(f"QEMU exited before the recovery socket appeared: {process.returncode}")
        if Path(socket_path).exists():
            return
        time.sleep(0.05)
    raise TimeoutError(f"Recovery socket did not appear: {socket_path}")


def _inputs_intact(inputs: object) -> bool:
    """Re-hash caller inputs without ever opening them for writing."""
    if not isinstance(inputs, dict) or not inputs:
        return False
    for item in inputs.values():
        if not isinstance(item, dict):
            return False
        path_value = item.get("path")
        expected = item.get("sha256")
        if not isinstance(path_value, str) or not isinstance(expected, str):
            return False
        try:
            path = Path(path_value)
            if not path.is_file() or _sha256(path) != expected.lower():
                return False
        except (OSError, ValueError):
            return False
    return True


def _write_report(output: Path, report: dict[str, object]) -> None:
    """Persist a UTF-8 report atomically enough for GUI readers."""
    temporary = output / "launch.json.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output / "launch.json")


def _probe_transition(socket_path: str, timeout: float) -> dict[str, object]:
    """Poll real descriptors after reset; never synthesize a next-stage device."""
    deadline = time.monotonic() + timeout
    attempts: list[dict[str, object]] = []
    last: dict[str, object] | None = None
    while time.monotonic() < deadline and len(attempts) < MAX_TRANSITION_ATTEMPTS:
        try:
            with RecoveryTransport(socket_path, timeout=min(2.0, max(deadline - time.monotonic(), 0.1))) as transport:
                last = transport.probe()
                if last.get("bulk_out_endpoint") == 4:
                    value = last.get("configuration_value")
                    if not isinstance(value, int) or not 0 <= value <= 255:
                        raise RecoveryProtocolError("Recovery configuration value is missing")
                    # iBEC exposes a bulk recovery interface rather than a
                    # DFU class interface; select its real configuration
                    # before any endpoint transfer.
                    transport.control(0x00, 9, value=value)
                    last["configuration_selected"] = True
            attempts.append(last)
            if last.get("bulk_out_endpoint") == 4:
                return {"state": "ibec-ready", "attempts": attempts, "last": last,
                        "forced_transition": False}
        except (OSError, TimeoutError, RecoveryProtocolError) as error:
            attempts.append({"error": f"{type(error).__name__}: {error}"})
        time.sleep(0.1)
    return {
        "state": "transition-blocked",
        "attempts": attempts[-MAX_TRANSITION_ATTEMPTS:],
        "last": last,
        "forced_transition": False,
        "reason": "iBSS remained in DFU or the recovery endpoint was not advertised",
    }


def _command_for(config: "VMappleConfig", executable: Executable, storage: StorageSession,
                 socket_path: str, output: Path) -> list[str]:
    guest_firmware = _guest_path(config.firmware, executable)
    guest_serial = _guest_path(output / "serial.log", executable)
    guest_trace = _guest_path(output / "transport.log", executable)
    args: list[str] = [
        "-M", f"vmapple,research-headless=on,uuid={config.uuid}",
        "-accel", "tcg,thread=single",
        "-cpu", "max,pauth=on,pauth-qarma5=on,cntfrq=24000000",
        "-m", f"{config.memory_mib}M", "-smp", str(config.smp),
        "-bios", guest_firmware,
        *storage.arguments(executable),
        "-display", config.display, "-monitor", "none",
        "-serial", f"file:{guest_serial}", "-nic", "none", "-no-reboot",
        "-global", "vmapple-cfg.optional-rpc-unavailable=on",
        "-chardev", f"socket,id=vusb,path={socket_path},server=on,wait=off",
        "-global", "vmapple-bdif.usbdev=vusb",
        "-trace", f"enable=bdif_*,file={guest_trace}",
        "-trace", f"enable=vmapple_optional_rpc_*,file={guest_trace}",
        "-d", "guest_errors,unimp",
    ]
    return executable.command(*args)


@dataclass(frozen=True)
class VMappleConfig:
    target_major: int
    qemu: str | None
    firmware: str
    ibss: str
    aux: str
    root: str
    output: str | None = None
    ibec: str | None = None
    qemu_img: str | None = None
    display: str = "gtk"
    uuid: int = 0
    aux_offset: int = 0
    memory_mib: int = 4096
    smp: int = 2
    transition_timeout: float = 10.0
    duration: float | None = None
    research_only: bool = False
    machine_type: str = IBOOT_MACHINE_TYPE
    guest_os: str = MACOS_GUEST_OS
    recovery_protocol: str = "DFU/IPSW"
    recovery_image_name: str = DEFAULT_RECOVERY_IMAGE
    boot_picker_enabled: bool = True
    boot_delay_seconds: float = BOOT_DELAY_SECONDS
    boot_selection: str = RECOVERY_ENTRY_ID
    boot_picker_trigger: str = "runner-default-recovery"

    def validate(self) -> tuple[Executable, Executable, dict[str, Path]]:
        # Scope is checked before resolving executables or opening any caller
        # supplied firmware/storage input.  An iOS/iPadOS request therefore
        # cannot reach the DFU uploader even when all paths are valid.
        validate_iboot_scope(
            self.machine_type,
            self.guest_os,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
            recovery_enabled=True,
            target_major=self.target_major,
        )
        picker = validate_boot_picker_config(
            enabled=self.boot_picker_enabled,
            delay_seconds=self.boot_delay_seconds,
            alt_key=DEFAULT_ALT_KEY,
            show_picker_on_alt=True,
            target_major=self.target_major,
            recovery_enabled=True,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
        )
        if type(self.boot_picker_enabled) is not bool:
            raise ValueError("VMApple boot_picker_enabled must be a boolean")
        if self.boot_selection not in (MACOS_ENTRY_ID, RECOVERY_ENTRY_ID):
            raise ValueError("VMApple boot selection must be macos or recovery")
        if not isinstance(self.boot_picker_trigger, str) or not self.boot_picker_trigger.strip():
            raise ValueError("VMApple boot picker trigger must be a nonempty string")
        if self.boot_picker_enabled and self.boot_selection == RECOVERY_ENTRY_ID and not picker.get("recovery_entry_enabled"):
            raise ValueError("VMApple Recovery entry is disabled")
        if self.target_major not in (26, 27):
            raise ValueError("VMApple target must be macOS 26 or 27")
        if not self.research_only:
            raise ValueError("VMApple launch requires the explicit --research-only flag")
        if self.display not in ("gtk", "sdl"):
            raise ValueError("VMApple display must be gtk or sdl")
        if type(self.uuid) is not int or not 0 <= self.uuid < 2**64:
            raise ValueError("VMApple uuid must fit an unsigned 64-bit integer")
        if type(self.aux_offset) is not int or self.aux_offset < 0 or self.aux_offset % 512:
            raise ValueError("AUX offset must be a nonnegative 512-byte multiple")
        if type(self.memory_mib) is not int or not 512 <= self.memory_mib <= 1024 * 1024:
            raise ValueError("VMApple memory must be between 512 MiB and 1 TiB")
        if type(self.smp) is not int or not 1 <= self.smp <= 32:
            raise ValueError("VMApple SMP must be between 1 and 32 CPUs")
        if not 0 < self.transition_timeout <= 300:
            raise ValueError("Transition timeout must be between 0 and 300 seconds")
        if self.duration is not None and not 0 < self.duration <= 86400:
            raise ValueError("Duration must be between 0 and 86400 seconds")
        qemu = _resolve_executable(self.qemu, "X86_VMAPLE_QEMU", "qemu-system-aarch64")
        qemu_img = _resolve_executable(self.qemu_img, "X86_VMAPLE_QEMU_IMG", "qemu-img")
        paths = {
            "firmware": _regular(self.firmware, "AVPBooter firmware", limit=MAX_FIRMWARE_BYTES),
            "ibss": _regular(self.ibss, "personalized iBSS", limit=MAX_DFU_BYTES),
            "aux": _regular(self.aux, "AUX base image"),
            "root": _regular(self.root, "root base image"),
        }
        if self.ibec:
            paths["ibec"] = _regular(self.ibec, "personalized iBEC", limit=MAX_RECOVERY_BYTES)
        if qemu.is_wsl and os.name == "nt":
            raise ValueError("Run the VMApple worker inside WSL; the GUI bridge performs this re-exec")
        return qemu, qemu_img, paths

    def personality_report(self) -> dict[str, object]:
        """Return the validated iBoot/macOS policy metadata for reports."""
        personality = validate_iboot_scope(
            self.machine_type,
            self.guest_os,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
            recovery_enabled=True,
            target_major=self.target_major,
        )
        personality["boot_picker"] = validate_boot_picker_config(
            enabled=self.boot_picker_enabled,
            delay_seconds=self.boot_delay_seconds,
            alt_key=DEFAULT_ALT_KEY,
            show_picker_on_alt=True,
            target_major=self.target_major,
            recovery_enabled=True,
            recovery_protocol=self.recovery_protocol,
            recovery_image_name=self.recovery_image_name,
        )
        personality["boot_picker"]["selection"] = self.boot_selection
        trigger = self.boot_picker_trigger.strip() if isinstance(self.boot_picker_trigger, str) else ""
        personality["boot_picker"]["selection_source"] = trigger
        personality["boot_picker"]["hotkey_event_observed"] = trigger.startswith("alt-")
        personality["boot_picker"]["delay_enforced"] = self.boot_picker_enabled
        return personality


def run(config: VMappleConfig) -> dict[str, object]:
    """Start a visible VMApple instance, upload iBSS, and record the real boundary."""
    personality = config.personality_report()
    qemu, qemu_img, paths = config.validate()
    backend = probe_backend(qemu)
    output = _new_directory(config.output)
    storage: StorageSession | None = None
    process: subprocess.Popen[bytes] | None = None
    report: dict[str, object] | None = None
    started = time.monotonic()
    socket_path = f"/tmp/26x86-vmapple-{output.name}.sock"
    try:
        try:
            Path(socket_path).unlink()
        except FileNotFoundError:
            pass
        storage = create_storage(aux=paths["aux"], root=paths["root"], directory=output,
                                 qemu_img=qemu_img, aux_offset=config.aux_offset)
        command = _command_for(config, qemu, storage, socket_path, output)
        inputs = {name: {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)}
                  for name, path in paths.items()}
        report = {
            "schema": "26x86.vmapple-gui/1", "target_major": config.target_major,
            "target_name": "Tahoe" if config.target_major == 26 else "Golden Gate",
            "machine_type": personality["machine_type"],
            "personality": personality["personality"],
            "guest_os": personality["guest_os"],
            "guest_os_supported": personality["guest_os_supported"],
            "guest_os_policy": personality["guest_os_policy"],
            "supported_guest_os": personality["supported_guest_os"],
            "unsupported_guest_os": personality["unsupported_guest_os"],
            "policy_matrix": personality["policy_matrix"],
            "recovery_scope": personality["recovery"],
            "boot_picker": personality["boot_picker"],
            "validation_level": "RECOVERY-PROTOCOL", "display_backend": config.display,
            "research_only": True, "developer_host_bypass": True,
            "distribution_status": "NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT",
            "host": {"system": platform.system(), "architecture": platform.machine(),
                     "physical_mac_verified": False},
            "backend": backend, "command": command, "inputs": inputs,
            "cow_storage": True, "storage_session": str(storage.directory / "storage"),
            "forced_transition": False, "signature_acceptance_verified": False,
            "ibec_executed": False, "xnu_executed": False, "macos_boot_verified": False,
            "physical_mac_verified": False, "termination": None, "returncode": None,
            "duration_seconds": None, "input_integrity": False, "error": None,
        }
        _write_report(output, report)
        stdout = (output / "qemu.stdout.log").open("xb")
        stderr = (output / "qemu.stderr.log").open("xb")
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
        finally:
            stdout.close()
            stderr.close()
        report["pid"] = process.pid
        _write_report(output, report)
        _wait_for_socket(socket_path, process, 30)
        # The gate starts when QEMU has exposed its recovery socket, which is
        # the first point at which the guest is powered and input can be
        # observed by this runner.  The GUI picker records the real Alt event
        # separately; this bounded sleep enforces the same two-second policy
        # before any DFU transfer is attempted.
        if config.boot_picker_enabled:
            report["boot_picker"]["gate_started_monotonic"] = round(time.monotonic() - started, 3)  # type: ignore[index]
            time.sleep(config.boot_delay_seconds)
            report["boot_picker"]["gate_released_monotonic"] = round(time.monotonic() - started, 3)  # type: ignore[index]
        report["boot_picker"]["gate_released"] = True  # type: ignore[index]
        _write_report(output, report)
        if config.boot_selection == MACOS_ENTRY_ID:
            raise VMappleError(
                "The macOS BootPicker entry was selected, but direct macOS boot is not implemented; "
                "choose macOS Recovery for the verified DFU/IPSW path."
            )
        with RecoveryTransport(socket_path, timeout=10) as transport:
            initial = transport.probe()
            report["initial_device"] = initial
            dfu = transport.send_dfu_file(paths["ibss"], reset=True)
        report["dfu_upload"] = dfu
        transition = _probe_transition(socket_path, config.transition_timeout)
        report["transition"] = transition
        if transition.get("state") == "ibec-ready" and "ibec" in paths:
            report["ibec_upload_attempted"] = True
            with RecoveryTransport(socket_path, timeout=10) as transport:
                report["ibec_upload"] = transport.send_recovery_file(paths["ibec"])
            # Upload acknowledgement is not proof that iBEC was accepted or executed.
            report["ibec_executed"] = False
        elif transition.get("state") != "ibec-ready":
            report["ibec_upload_attempted"] = False
            report["transition_blocker"] = "iBSS did not advertise bulk OUT endpoint 4"
        else:
            report["ibec_upload_attempted"] = False
            report["transition_blocker"] = "No personalized iBEC input was supplied"
        _write_report(output, report)

        deadline = time.monotonic() + config.duration if config.duration is not None else None
        while process.poll() is None:
            if deadline is not None and time.monotonic() >= deadline:
                report["termination"] = "time_budget"
                process.terminate()
                break
            if (output / "stop").exists():
                report["termination"] = "stop_file"
                process.terminate()
                break
            time.sleep(0.1)
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        report["returncode"] = process.returncode
        if report.get("termination") is None:
            report["termination"] = "guest_exit"
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["input_integrity"] = _inputs_intact(report.get("inputs"))
        if not report["input_integrity"]:
            report["error"] = "One or more caller-supplied inputs changed during the run"
        _write_report(output, report)
        return report
    except BaseException as error:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if report is None:
            report = {
                "schema": "26x86.vmapple-gui/1", "target_major": config.target_major,
                "target_name": "Tahoe" if config.target_major == 26 else "Golden Gate",
                "machine_type": personality["machine_type"],
                "personality": personality["personality"],
                "guest_os": personality["guest_os"],
                "guest_os_supported": personality["guest_os_supported"],
                "guest_os_policy": personality["guest_os_policy"],
                "policy_matrix": personality["policy_matrix"],
                "recovery_scope": personality["recovery"],
                "boot_picker": personality["boot_picker"],
                "validation_level": "RECOVERY-PROTOCOL", "display_backend": config.display,
                "forced_transition": False, "signature_acceptance_verified": False,
                "macos_boot_verified": False, "physical_mac_verified": False,
            }
        report["error"] = f"{type(error).__name__}: {error}"
        report["termination"] = report.get("termination") or "error"
        report["returncode"] = process.returncode if process is not None else None
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["input_integrity"] = _inputs_intact(report.get("inputs"))
        _write_report(output, report)
        raise
    finally:
        try:
            Path(socket_path).unlink()
        except FileNotFoundError:
            pass


def configured_from_environment() -> dict[str, object]:
    """Return GUI-safe availability information without launching a guest."""
    values = {
        "qemu": os.environ.get("X86_VMAPLE_QEMU", ""),
        "firmware": os.environ.get("X86_VMAPLE_AVPBOOTER", ""),
        "ibss": os.environ.get("X86_VMAPLE_IBSS", ""),
        "ibec": os.environ.get("X86_VMAPLE_IBEC", ""),
        "aux": os.environ.get("X86_VMAPLE_AUX", ""),
        "root": os.environ.get("X86_VMAPLE_ROOT", ""),
        "qemu_img": os.environ.get("X86_VMAPLE_QEMU_IMG", ""),
        "output": os.environ.get("X86_VMAPLE_OUTPUT", ""),
    }
    required = ("qemu", "firmware", "ibss", "aux", "root", "qemu_img")
    present = {name: bool(value) for name, value in values.items()}
    boot_picker = validate_boot_picker_config(target_major=27)
    boot_picker["selection"] = RECOVERY_ENTRY_ID
    boot_picker["selection_source"] = "runner-default-recovery"
    boot_picker["hotkey_event_observed"] = False
    boot_picker["delay_enforced"] = True
    return {
        "ok": True, "research_only_required": True, "display_backend": "gtk",
        "machine_type": IBOOT_MACHINE_TYPE, "personality": "iBoot",
        "guest_os": MACOS_GUEST_OS, "guest_os_supported": True,
        "guest_os_policy": "macOS-only", "supported_guest_os": [MACOS_GUEST_OS],
        "unsupported_guest_os": ["iOS", "iPadOS", "tvOS", "watchOS", "visionOS"],
        "policy_matrix": default_scope(recovery_enabled=True)["policy_matrix"],
        "recovery_scope": default_scope(recovery_enabled=True)["recovery"],
        "boot_picker": boot_picker,
        "configured": all(present[name] for name in required), "fields": present,
        "values": values, "macos_boot_verified": False,
        "note": "Paths are caller-supplied. The GUI never bundles Apple firmware or writes an existing ESP.",
    }
