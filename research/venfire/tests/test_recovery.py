"""A short or fabricated recovery status must never become a successful reply."""

import socket
import struct
import tempfile
import threading
import time
import unittest
from pathlib import Path

from venfire.recovery import (RecoveryTransport, RecoveryProtocolError, RecoveryUploadError,
                              RecoveryStallError, MAX_FRAME)


class RecoveryProtocolTests(unittest.TestCase):
    def transport(self, reply, *, fragmented=False):
        client, server = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        transport = RecoveryTransport.__new__(RecoveryTransport)
        transport.socket = client
        transport.timeout = 1
        transport.deadline = None

        def respond():
            try:
                server.recv(4096)
                if fragmented:
                    for value in reply:
                        server.sendall(bytes([value]))
                else:
                    server.sendall(reply)
                server.shutdown(socket.SHUT_WR)
            except OSError:
                pass

        worker = threading.Thread(target=respond, daemon=True)
        worker.start()
        self.addCleanup(worker.join, 2)
        return transport

    @staticmethod
    def frame(payload, kind=1, status=0):
        data = bytes([kind, status]) + payload
        return struct.pack("<I", len(data)) + data

    def test_fragmented_valid_status_is_preserved_exactly(self):
        raw = bytes.fromhex("000300000500")
        result = self.transport(self.frame(raw), fragmented=True).dfu_status()
        self.assertEqual(result["raw"], raw.hex())
        self.assertEqual(result["poll_timeout_ms"], 3)
        self.assertEqual(result["state"], 5)

    def test_empty_or_short_status_is_not_translated_to_success(self):
        for payload in (b"", b"\x00", b"\x00" * 5):
            with self.subTest(payload=payload):
                with self.assertRaises(RecoveryProtocolError):
                    self.transport(self.frame(payload)).dfu_status()

    def test_guest_error_is_not_relabelled_success(self):
        result = self.transport(self.frame(bytes.fromhex("090000000a00"))).dfu_status()
        self.assertEqual(result["status"], 9)
        self.assertEqual(result["state"], 10)

    def test_exact_guest_stall_remains_a_distinct_failure(self):
        with self.assertRaises(RecoveryStallError) as captured:
            self.transport(self.frame(b"", kind=2), fragmented=True).control(0x21, 1)
        self.assertEqual(captured.exception.response_hex, "0200")
        for reply in (self.frame(b"payload", kind=2), self.frame(b"", kind=2, status=1)):
            with self.subTest(reply=reply), self.assertRaises(RecoveryProtocolError) as error:
                self.transport(reply).control(0x21, 1)
            self.assertNotIsInstance(error.exception, RecoveryStallError)

    def test_bad_framing_type_and_transfer_failure_are_rejected(self):
        for reply in (struct.pack("<I", MAX_FRAME + 1), struct.pack("<I", 0),
                      self.frame(b"\x02", kind=5), self.frame(b"\x02", status=1),
                      struct.pack("<I", 9) + b"truncated"):
            with self.subTest(reply=reply):
                with self.assertRaises(RecoveryProtocolError):
                    self.transport(reply).dfu_state()

    def test_direction_mismatch_rejected_before_transmission(self):
        transport = RecoveryTransport.__new__(RecoveryTransport)
        with self.assertRaises(ValueError):
            transport.control(0x80, 6, length=1, data=b"X")
        with self.assertRaises(ValueError):
            transport.control(0x21, 1, length=2, data=b"X")

    def test_bulk_ack_checks_endpoint_and_actual_packet_has_no_setup(self):
        client, server = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        transport = RecoveryTransport.__new__(RecoveryTransport)
        transport.socket, transport.timeout = client, 1
        seen = []

        def respond():
            header = server.recv(4)
            size = struct.unpack("<I", header)[0]
            data = b""
            while len(data) < size:
                data += server.recv(size - len(data))
            seen.append(data)
            for byte in self.frame(b"", status=4):
                server.sendall(bytes([byte]))

        worker = threading.Thread(target=respond, daemon=True)
        worker.start()
        transport.bulk_out(b"original bytes")
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(seen, [struct.pack("<iBB", 14, 4, 1) + b"original bytes"])
        with self.assertRaises(RecoveryProtocolError):
            self.transport(self.frame(b"", status=0)).bulk_out(b"x")

    def test_recovery_file_uses_original_chunks_zlp_and_command_nul(self):
        transport = RecoveryTransport.__new__(RecoveryTransport)
        controls, chunks = [], []
        transport.control = lambda *args, **kwargs: controls.append((args, kwargs)) or b""
        transport.bulk_out = lambda data, **kwargs: chunks.append(data)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "original.bin"
            image = bytes(range(256)) * 130
            path.write_bytes(image)
            result = transport.send_recovery_file(path)
            self.assertEqual(path.read_bytes(), image)
        self.assertTrue(result["input_integrity"])
        self.assertTrue(result["transfer_complete"])
        self.assertEqual(chunks, [image[:32768], image[32768:], b""])
        self.assertEqual(controls[0][0], (0x41, 0))
        transport.send_command("go", request=1)
        self.assertEqual(controls[-1][0], (0x40, 1))
        self.assertEqual(controls[-1][1]["data"], b"go\0")
        self.assertFalse(result["signature_acceptance_verified"])

    def test_bulk_in_preserves_original_console_bytes_and_endpoint(self):
        raw = b"original iBoot console\r\n"
        self.assertEqual(self.transport(self.frame(raw, status=0x81)).bulk_in(), raw)
        with self.assertRaises(RecoveryProtocolError):
            self.transport(self.frame(raw, status=0x85)).bulk_in()

    def test_out_setup_and_data_are_one_frame_with_fragmented_ack(self):
        client, server = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        transport = RecoveryTransport.__new__(RecoveryTransport)
        transport.socket = client
        transport.timeout = 1
        received = []

        def exact(n):
            data = b""
            while len(data) < n:
                chunk = server.recv(n - len(data))
                if not chunk:
                    return data
                data += chunk
            return data

        def respond():
            try:
                size = struct.unpack("<I", exact(4))[0]
                received.append(exact(size))
                for byte in self.frame(b""):
                    server.sendall(bytes([byte]))
                size = struct.unpack("<I", exact(4))[0]
                received.append(exact(size))
                server.sendall(self.frame(bytes.fromhex("003200000500")))
            except OSError:
                pass

        worker = threading.Thread(target=respond, daemon=True)
        worker.start()
        data = b"\xa5" * 2048
        self.assertEqual(transport.control(0x21, 1, length=2048, data=data), b"")
        self.assertEqual(transport.dfu_status()["state"], 5)
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(received[0], bytes.fromhex("0808000000012101000000000008") + data)
        self.assertEqual(received[1], bytes.fromhex("080000000001a103000000000600"))

    def upload_fixture(self, statuses):
        transport = RecoveryTransport.__new__(RecoveryTransport)
        transport.timeout = 1
        states = iter([2, 8])
        transport.dfu_state = lambda **kwargs: next(states)
        replies = iter(statuses)
        transport.dfu_status = lambda **kwargs: next(replies)
        writes = []
        transport.control = lambda *args, **kwargs: writes.append((args, kwargs)) or b""
        transport.usb_reset = lambda **kwargs: writes.append(("reset", kwargs))
        return transport, writes

    @staticmethod
    def status(raw):
        data = bytes.fromhex(raw)
        return {"raw": raw, "status": data[0], "state": data[4],
                "poll_timeout_ms": int.from_bytes(data[1:4], "little"), "string_index": data[5]}

    def test_upload_preserves_image_adds_transport_crc_and_reports_no_boot_claim(self):
        statuses = [self.status("003200000500"), self.status("003200000500"),
                    self.status("003200000800")]
        transport, writes = self.upload_fixture(statuses)
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "unsigned-test.bin"
            original = b"\xa5" * 2048
            image.write_bytes(original)
            report = transport.send_dfu_file(image, reset=True)
            self.assertEqual(image.read_bytes(), original)
        self.assertEqual(writes[0][1]["data"], original)
        self.assertEqual(writes[1][1]["data"].hex(), "ffffffffac05000155464410dee5835b")
        self.assertTrue(all("deadline" in call[1] for call in writes))
        self.assertTrue(report["transfer_complete"])
        self.assertTrue(report["input_integrity"])
        self.assertTrue(report["usb_reset_acknowledged"])
        self.assertFalse(report["signature_acceptance_verified"])
        self.assertFalse(report["macos_boot_verified"])

    def test_upload_records_guest_error_and_sends_no_next_block_or_reset(self):
        transport, writes = self.upload_fixture([self.status("093200000a00")])
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "test.bin"
            image.write_bytes(b"\xa5" * 2048)
            with self.assertRaises(RecoveryUploadError) as raised:
                transport.send_dfu_file(image, reset=True)
        report = raised.exception.report
        self.assertEqual(len(writes), 1)
        self.assertEqual(report["blocks"][0]["statuses"][0]["raw"], "093200000a00")
        self.assertTrue(report["input_integrity"])
        self.assertFalse(report["transfer_complete"])
        self.assertFalse(report["usb_reset_acknowledged"])

    def test_guest_poll_delay_cannot_extend_absolute_upload_deadline(self):
        transport, _ = self.upload_fixture([self.status("00b80b000700")])
        replies = []
        with self.assertRaises(TimeoutError):
            transport._dfu_wait(8, {6, 7}, time.monotonic() + 0.05, replies)
        self.assertEqual(replies[0]["state"], 7)

    def test_interrupted_upload_still_checks_input_integrity(self):
        transport, _ = self.upload_fixture([])

        def interrupt(*args, **kwargs):
            raise KeyboardInterrupt()

        transport.control = interrupt
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "test.bin"
            image.write_bytes(b"unchanged original")
            with self.assertRaises(KeyboardInterrupt) as raised:
                transport.send_dfu_file(image)
        self.assertTrue(raised.exception.recovery_report["input_integrity"])
        self.assertFalse(raised.exception.recovery_report["transfer_complete"])

    def test_upload_rejects_symlink_input_before_usb_requests(self):
        transport, writes = self.upload_fixture([])
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "original.bin"
            link = Path(directory) / "link.bin"
            original.write_bytes(b"unchanged original")
            try:
                link.symlink_to(original)
            except OSError:
                self.skipTest("Host does not permit symlink creation")
            with self.assertRaises(ValueError):
                transport.send_dfu_file(link)
        self.assertEqual(writes, [])

    def test_read_deadline_does_not_reset_for_each_fragment(self):
        client, server = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        transport = RecoveryTransport.__new__(RecoveryTransport)
        transport.socket = client
        transport.deadline = time.monotonic() - 0.1
        with self.assertRaises(TimeoutError):
            transport._read(1)


if __name__ == "__main__":
    unittest.main()
