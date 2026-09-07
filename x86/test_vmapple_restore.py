"""Offline checks for the Stage2 restore-role boundary."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class VMappleRestoreTests(unittest.TestCase):
    def _im4p(self, tag: bytes, payload: bytes = b"payload") -> bytes:
        from x86.vmapple_personalization import _der

        return _der(0x30, _der(0x16, b"IM4P") + _der(0x16, tag) +
                     _der(0x16, b"1.0") + _der(0x04, payload))

    def test_normalize_role_changes_only_the_type_string(self) -> None:
        from x86.vmapple_restore import normalize_role

        source = self._im4p(b"krnl", b"kernel")
        expected = self._im4p(b"rkrn", b"kernel")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "RestoreKernelCache.im4p"
            destination = root / "out.im4p"
            source_path.write_bytes(source)
            proof = normalize_role(source_path, "RestoreKernelCache",
                                   hashlib.sha384(expected).digest(), destination)
            self.assertTrue(proof["metadata_changed"])
            self.assertTrue(proof["payload_preserved"])
            self.assertEqual(destination.read_bytes(), expected)

    def test_normalize_role_rejects_manifest_mismatch(self) -> None:
        from x86.vmapple_restore import normalize_role

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "RestoreKernelCache.im4p"
            source_path.write_bytes(self._im4p(b"krnl"))
            with self.assertRaisesRegex(ValueError, "official BuildManifest"):
                normalize_role(source_path, "RestoreKernelCache", hashlib.sha384(b"wrong").digest(), root / "out.im4p")

    def test_wrap_role_preserves_im4p_and_ticket(self) -> None:
        from x86.vmapple_personalization import _der
        from x86.vmapple_restore import wrap_role

        payload = self._im4p(b"rkrn")
        ticket = _der(0x30, _der(0x16, b"IM4M") + b"ticket")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload_path = root / "role.im4p"
            ticket_path = root / "ticket.im4m"
            output = root / "role.img4"
            payload_path.write_bytes(payload)
            ticket_path.write_bytes(ticket)
            proof = wrap_role(payload_path, ticket_path, output)
            wrapped = output.read_bytes()
            self.assertTrue(proof["im4p_preserved"])
            self.assertTrue(proof["ticket_preserved"])
            self.assertIn(payload, wrapped)
            self.assertIn(ticket, wrapped)

    def test_restore_sequence_records_the_expected_preboot_stall(self) -> None:
        from x86.vmapple_personalization import _der
        from x86.vmapple import RecoveryProtocolError
        from x86.vmapple_restore import run_restore_sequence

        class FakeTransport:
            def __init__(self, *_args, **_kwargs):
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def configure_recovery(self, **_kwargs):
                return {"bulk_out_endpoint": 4}

            def send_recovery_file(self, path, **_kwargs):
                return {"image_path": str(path), "blocks": [{"acknowledged": True}]}

            def send_command(self, command, **_kwargs):
                self.commands.append(command)
                return b""

            def control(self, *_args, **_kwargs):
                raise RecoveryProtocolError("Guest USB endpoint stalled: 0200")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            role_names = (
                "RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache",
            )
            source_paths = {}
            manifest_roles = {}
            for role in role_names:
                tag = {
                    "RestoreTrustCache": b"rtsc", "RestoreRamDisk": b"rdsk",
                    "RestoreDeviceTree": b"rdtr", "RestoreKernelCache": b"rkrn",
                }[role]
                payload = self._im4p(tag, role.encode("ascii"))
                source = root / (role + ".im4p")
                source.write_bytes(payload)
                source_paths[role] = source
                manifest_roles[role] = {"Digest": hashlib.sha384(payload).digest()}
            manifest = {
                "BuildIdentities": [{
                    "Info": {
                        "DeviceClass": "vma2macosap",
                        "Variant": "Customer Erase Install (IPSW)",
                    },
                    "Manifest": manifest_roles,
                }],
            }
            manifest_path = root / "BuildManifest.plist"
            import plistlib
            manifest_path.write_bytes(plistlib.dumps(manifest))
            ticket = root / "ticket.im4m"
            ticket.write_bytes(_der(0x30, _der(0x16, b"IM4M") + b"ticket"))

            with patch("x86.vmapple_restore.RecoveryTransport", FakeTransport):
                held = []
                report = run_restore_sequence(
                    socket_path="unused",
                    build_manifest=manifest_path,
                    role_sources=source_paths,
                    ticket=ticket,
                    output=root / "restore",
                    total_timeout=5,
                    transport_holders=held,
                )
            self.assertTrue(report["sequence_sent"])
            self.assertTrue(report["bootx_acknowledged"])
            self.assertEqual(report["preboot_notification"]["guest_stall_hex"], "0200")
            self.assertFalse(report["preboot_notification"]["acknowledged"])
            self.assertEqual(len(held), 1)
            held[0].__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
