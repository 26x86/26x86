"""Restore role normalization must never change an executable/data OCTET."""
import hashlib
import tempfile
import unittest
import plistlib
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from venfire.restore import _header, prepare_role_container, wrap_role_container, run_stage
from venfire.recovery import RecoveryUploadError, RecoveryStallError, RecoveryProtocolError
from tools.restore_stage import execute


def element(tag, data):
    return _header(tag, len(data)) + data


def fixture(kind=b"krnl", payload=b"original code includes krnl and rkrn strings"):
    body = (element(0x16, b"IM4P") + element(0x16, kind)
            + element(0x16, b"own-byte-test") + element(4, payload))
    return element(0x30, body)


class RestoreRoleTests(unittest.TestCase):
    def test_boot_without_existing_chain_stops_before_any_tss_request(self):
        args = SimpleNamespace(developer_host_bypass=False, boot=True, chain_personalization=None)
        with patch("tools.restore_stage.authorize_host"), patch("venfire.personalization.request_restore_ticket") as request:
            with self.assertRaisesRegex(ValueError, "chain-personalization"):
                execute(args)
            request.assert_not_called()

    def test_existing_chain_routes_to_reuse_without_new_tss_or_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "original.im4p"
            source.write_bytes(fixture())
            manifest = directory / "manifest.plist"
            manifest.write_bytes(plistlib.dumps({"BuildIdentities": [{
                "Info": {"DeviceClass": "vma2macosap", "Variant": "Customer Erase Install (IPSW)"},
                "Manifest": {"RestoreKernelCache": {"Digest": hashlib.sha384(fixture(b"rkrn")).digest()}}}]}))
            ticket = directory / "original-ticket"
            ticket.write_bytes(element(0x30, element(0x16, b"IM4M")))
            args = SimpleNamespace(developer_host_bypass=False, boot=False, helper=None,
                component=["RestoreKernelCache=" + str(source)], manifest=manifest,
                output=directory / "result", chain_personalization=directory / "existing-chain",
                socket="unused", total_timeout=30)
            auth = SimpleNamespace(to_dict=lambda: {"fixture": True})
            with patch("tools.restore_stage.authorize_host", return_value=auth), \
                 patch("venfire.personalization.request_restore_ticket") as request, \
                 patch("venfire.personalization.reuse_restore_ticket",
                       return_value={"ticket_received": True, "ticket_path": str(ticket)}) as reuse:
                result = execute(args)
            request.assert_not_called()
            self.assertEqual(reuse.call_count, 1)
            self.assertEqual(reuse.call_args.kwargs["chain_personalization"], args.chain_personalization)
            self.assertEqual(result["ticket_mode"], "existing-ibec-localpolicy-chain")
            self.assertIsNone(result["error"])
            self.assertTrue(result["input_integrity"]["valid"])
            self.assertFalse(result["xnu_boot_verified"])

    def test_only_optional_notification_stall_allows_standard_boot_command(self):
        for notification_error in (RecoveryStallError(b"\x02\x00"),
                                   RecoveryProtocolError("malformed endpoint")):
            with self.subTest(error=type(notification_error).__name__), tempfile.TemporaryDirectory() as temp:
                commands = []
                class Guest:
                    def __init__(self, *args): pass
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                    def configure_recovery(self, **kwargs): return {"fixture": True}
                    def send_recovery_file(self, *args, **kwargs): return {"transfer_complete": True}
                    def send_command(self, text, **kwargs): commands.append(text)
                    def control(self, *args, **kwargs): raise notification_error
                images = {}
                for role in ("RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache"):
                    path = Path(temp) / role
                    path.write_bytes(b"own immutable fixture")
                    images[role] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                with patch("venfire.restore.RecoveryTransport", Guest), patch("venfire.restore.time.sleep"):
                    result = run_stage("unused", images)
                if isinstance(notification_error, RecoveryStallError):
                    self.assertFalse(result["preboot_notification"]["acknowledged"])
                    self.assertEqual(result["preboot_notification"]["guest_stall_hex"], "0200")
                    self.assertEqual(commands[-1], "bootx")
                    self.assertTrue(result["sequence_sent"])
                    self.assertFalse(result["xnu_boot_verified"])
                else:
                    self.assertNotIn("bootx", commands)
                    self.assertFalse(result["sequence_sent"])

    def test_failed_transfer_stops_before_boot_and_keeps_partial_report(self):
        class Guest:
            def __init__(self, *args):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def configure_recovery(self, **kwargs):
                return {"fixture": True}
            def send_recovery_file(self, *args, **kwargs):
                raise RecoveryUploadError("original transfer error", {"bytes_sent": 32})
            def send_command(self, *args, **kwargs):
                raise AssertionError("Must not execute after a failed upload")
        with tempfile.TemporaryDirectory() as temp:
            images = {}
            for role in ("RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache"):
                source = Path(temp) / role
                source.write_bytes(b"own immutable test")
                images[role] = {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
            with patch("venfire.restore.RecoveryTransport", Guest):
                result = run_stage("unused", images)
            self.assertEqual(result["partial_upload"]["bytes_sent"], 32)
            self.assertFalse(result["sequence_sent"])
            self.assertFalse(result["xnu_boot_verified"])
            self.assertTrue(result["input_integrity"]["valid"])

    def test_only_typed_metadata_changes_and_original_payload_is_preserved(self):
        original = fixture()
        expected = fixture(b"rkrn")
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / "source", Path(temp) / "prepared"
            source.write_bytes(original)
            proof = prepare_role_container(source, "RestoreKernelCache", hashlib.sha384(expected).digest(), target)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(target.read_bytes(), expected)
            self.assertEqual(proof["original_octet_sha256"], proof["prepared_octet_sha256"])
            self.assertTrue(proof["outside_type_bytes_unchanged"])

    def test_manifest_mismatch_does_not_create_a_prepared_image(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / "source", Path(temp) / "prepared"
            source.write_bytes(fixture())
            with self.assertRaises(ValueError):
                prepare_role_container(source, "RestoreKernelCache", bytes(48), target)
            self.assertFalse(target.exists())

    def test_wrong_type_and_malformed_der_are_rejected(self):
        for original in (fixture(b"ibss"), fixture()[:-1], fixture() + b"trailing", b"\x30\x80"):
            with self.subTest(original=original), tempfile.TemporaryDirectory() as temp:
                source, target = Path(temp) / "source", Path(temp) / "prepared"
                source.write_bytes(original)
                with self.assertRaises(ValueError):
                    prepare_role_container(source, "RestoreKernelCache", bytes(48), target)
                self.assertFalse(target.exists())

    def test_already_correct_ramdisk_is_byte_identical(self):
        original = fixture(b"rdsk", bytes(range(256)) * 1024)
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / "source", Path(temp) / "prepared"
            source.write_bytes(original)
            proof = prepare_role_container(source, "RestoreRamDisk", hashlib.sha384(original).digest(), target)
            self.assertFalse(proof["metadata_changed"])
            self.assertEqual(source.read_bytes(), target.read_bytes())

    def test_wrapper_preserves_container_and_ticket_bytes(self):
        # Structural unit fixture only; it is never sent to a guest or TSS.
        prepared = fixture(b"rkrn")
        ticket = element(0x30, element(0x16, b"IM4M") + element(4, b"own ticket fixture"))
        with tempfile.TemporaryDirectory() as temp:
            source, signature, target = (Path(temp) / name for name in ("prepared", "ticket", "wrapped"))
            source.write_bytes(prepared)
            signature.write_bytes(ticket)
            proof = wrap_role_container(source, signature, target)
            self.assertIn(prepared, target.read_bytes())
            self.assertTrue(target.read_bytes().endswith(ticket))
            self.assertEqual(source.read_bytes(), prepared)
            self.assertEqual(signature.read_bytes(), ticket)
            self.assertFalse(proof["guest_acceptance_verified"])


if __name__ == "__main__":
    unittest.main()
