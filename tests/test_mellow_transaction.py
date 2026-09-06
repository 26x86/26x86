"""Actual temporary-directory copy/readback/rollback tests; no APFS, KC or kext load."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch

from x86.mellow.payload import load_payload
from x86.mellow.transaction import MellowTransaction, TransactionError, finalize_restore, restore_installed


PACKAGE = Path(__file__).resolve().parents[1] / "payloads/Mellow"


class MellowTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.data = self.base / "data"
        self.data.mkdir()
        self.journal = self.base / "journal"
        self.target = self.data / "Library/Extensions/Mellow.kext"
        self.payload = load_payload(PACKAGE)
        self.protected = self.data / "System/Library/Extensions/Unrelated.kext/protected"
        self.protected.parent.mkdir(parents=True)
        self.protected.write_bytes(b"outside the three Mellow targets")

    def tx(self, **kwargs):
        return MellowTransaction(self.payload, data_root=self.data, journal_root=kwargs.get("journal", self.journal))

    def receipt(self):
        return json.loads((self.journal / "active/receipt.json").read_text())["record"]

    def rewrite_receipt(self, edit, *, checksum=True):
        path = self.journal / "active/receipt.json"
        envelope = json.loads(path.read_text())
        edit(envelope["record"])
        if checksum:
            raw = json.dumps(envelope["record"], sort_keys=True, separators=(",", ":")).encode()
            envelope["sha256"] = hashlib.sha256(raw).hexdigest()
        path.write_text(json.dumps(envelope))

    def original(self):
        files = {"Contents/Info.plist": b"prior Mellow metadata", "Contents/MacOS/Mellow": b"prior kernel binary",
                 "Contents/Resources/original.bin": b"prior bundle resource"}
        for name, data in files.items():
            path = self.target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        os.chmod(self.target / "Contents/Resources/original.bin", 0o444)
        return self.snapshot(self.target)

    @staticmethod
    def snapshot(root):
        if not root.exists():
            return None
        return {p.relative_to(root).as_posix(): (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
                for p in root.rglob("*") if p.is_file()}

    def install(self):
        if self.target.exists():
            for p in self.target.rglob("*"):
                if p.is_file():
                    os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            shutil.rmtree(self.target)
        shutil.copytree(self.payload.components[0].source, self.target)

    def check_protected(self):
        self.assertEqual(self.protected.read_bytes(), b"outside the three Mellow targets")

    def test_prepare_only_creates_journal_and_preserves_existing_bytes_modes(self):
        original = self.original()
        tx = self.tx()
        result = tx.prepare()
        self.assertEqual(result["state"], "prepared")
        self.assertEqual(self.snapshot(self.target), original)
        self.assertEqual(self.snapshot(self.journal / "active/backups/kext"), original)
        self.assertEqual(self.receipt()["state"], "prepared")
        self.check_protected()

    def test_real_copy_readback_and_persistent_unpatch_restore_original(self):
        original = self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        result = tx.installed()
        self.assertEqual(result["state"], "files_verified")
        self.assertFalse(result["kernel_cache_verified"])
        self.assertFalse(result["snapshot_verified"])
        self.assertFalse(result["native_loaded"])
        self.assertTrue(restore_installed(self.data, self.journal))
        self.assertEqual(self.snapshot(self.target), original)
        self.assertFalse((self.journal / "active").exists())
        self.assertTrue((self.journal / "history" / tx.transaction_id / "receipt.json").is_file())
        self.assertFalse(restore_installed(self.data, self.journal))
        self.check_protected()

    def test_first_install_is_removed_by_verified_unpatch(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        tx.installed()
        self.assertTrue(tx.rollback())
        self.assertFalse(self.target.exists())
        self.check_protected()

    def test_prepare_then_rollback_without_copy_is_noop_for_target(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                original = self.original() if existing else None
                tx = self.tx()
                tx.prepare()
                self.assertTrue(tx.rollback())
                self.assertEqual(self.snapshot(self.target), original)

    def test_readback_rejects_missing_or_truncated_copy_then_restores_original(self):
        original = self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        binary = self.target / "Contents/MacOS/Mellow"
        binary.write_bytes(binary.read_bytes()[:257])
        with self.assertRaisesRegex(TransactionError, "payload bytes"):
            tx.installed()
        self.assertEqual(self.receipt()["state"], "prepared")
        self.assertTrue(tx.rollback())
        self.assertEqual(self.snapshot(self.target), original)

    def test_known_partial_first_install_is_removed(self):
        tx = self.tx()
        tx.prepare()
        binary = self.target / "Contents/MacOS/Mellow"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(self.payload.components[0].executable.read_bytes()[:100])
        with self.assertRaises(TransactionError):
            tx.installed()
        self.assertTrue(tx.rollback())
        self.assertFalse(self.target.exists())

    def test_unrecognized_bytes_are_not_deleted_even_at_mellow_destination(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        binary = self.target / "Contents/MacOS/Mellow"
        binary.write_bytes(b"unexpected third-party replacement")
        with self.assertRaisesRegex(TransactionError, "unrecognized"):
            tx.rollback()
        self.assertEqual(binary.read_bytes(), b"unexpected third-party replacement")
        self.assertTrue((self.journal / "active").exists())
        self.check_protected()

    def test_extra_files_in_new_target_block_destructive_rollback(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        extra = self.target / "do-not-delete"
        extra.write_bytes(b"external data")
        with self.assertRaises(TransactionError):
            tx.rollback()
        self.assertEqual(extra.read_bytes(), b"external data")

    def test_pending_and_files_verified_transactions_block_new_prepare(self):
        tx = self.tx()
        tx.prepare()
        for installed in (False, True):
            if installed:
                self.install()
                tx.installed()
            before = self.snapshot(self.target)
            with self.subTest(installed=installed), self.assertRaisesRegex(TransactionError, "new write"):
                self.tx().prepare()
            self.assertEqual(self.snapshot(self.target), before)

    def test_new_transaction_allowed_after_successful_restore(self):
        first = self.tx()
        first.prepare()
        self.install()
        first.installed()
        restore_installed(self.data, self.journal)
        second = self.tx()
        second.prepare()
        self.assertNotEqual(first.transaction_id, second.transaction_id)
        self.assertTrue((self.journal / "history" / first.transaction_id).is_dir())

    def test_new_instance_cannot_finalize_or_rollback_another_active_transaction(self):
        self.tx().prepare()
        for method in (self.tx().installed, self.tx().rollback):
            with self.assertRaises(TransactionError):
                method()

    def test_no_active_journal_returns_false_without_creating_it(self):
        self.assertFalse(restore_installed(self.data, self.journal))
        self.assertFalse(self.journal.exists())

    def test_default_journal_is_rooted_in_explicit_data_root(self):
        tx = MellowTransaction(self.payload, data_root=self.data)
        tx.prepare()
        self.assertTrue((self.data / "Library/Application Support/26x86/Mellow/transaction/active/receipt.json").is_file())
        self.assertFalse(self.target.exists())

    def test_journal_cannot_overlap_component_or_payload(self):
        for path in (self.target, self.target / "journal", self.target.parent, PACKAGE, PACKAGE / "journal", self.data):
            with self.subTest(path=path), self.assertRaises(TransactionError):
                self.tx(journal=path)

    def test_receipt_checksum_failure_preserves_targets(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        before = self.snapshot(self.target)
        self.rewrite_receipt(lambda r: r.update(state="files_verified"), checksum=False)
        with self.assertRaisesRegex(TransactionError, "integrity"):
            restore_installed(self.data, self.journal)
        self.assertEqual(self.snapshot(self.target), before)

    def test_recomputed_receipt_cannot_choose_arbitrary_destination(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        self.rewrite_receipt(lambda r: r["components"][0].update(destination="/System/Library/Extensions/Unrelated.kext"))
        with self.assertRaisesRegex(TransactionError, "allowed Mellow"):
            restore_installed(self.data, self.journal)
        self.check_protected()

    def test_recomputed_receipt_cannot_escape_with_backup_relative_path(self):
        tx = self.tx()
        tx.prepare()
        self.rewrite_receipt(lambda r: r["components"][0]["expected"].update({"../../escape": {
            "kind": "file", "mode": 0o644, "uid": 0, "gid": 0, "size": 0, "sha256": hashlib.sha256(b"").hexdigest()}}))
        with self.assertRaisesRegex(TransactionError, "traversal"):
            restore_installed(self.data, self.journal)
        self.check_protected()

    def test_duplicate_category_and_wrong_root_are_rejected(self):
        tx = self.tx()
        tx.prepare()
        self.rewrite_receipt(lambda r: r["components"].append(dict(r["components"][0])))
        with self.assertRaises(TransactionError):
            restore_installed(self.data, self.journal)
        other = self.base / "other-data"
        other.mkdir()
        with self.assertRaisesRegex(TransactionError, "data root"):
            restore_installed(other, self.journal)

    def test_corrupted_backup_is_detected_before_target_deletion(self):
        self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        before = self.snapshot(self.target)
        (self.journal / "active/backups/kext/Contents/MacOS/Mellow").write_bytes(b"broken backup")
        with self.assertRaisesRegex(TransactionError, "snapshot changed"):
            tx.rollback()
        self.assertEqual(self.snapshot(self.target), before)

    def test_corrupted_expected_snapshot_blocks_installed_receipt(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        (self.journal / "active/expected/kext/Contents/MacOS/Mellow").write_bytes(b"broken expected bytes")
        with self.assertRaises(TransactionError):
            tx.installed()
        self.assertEqual(self.receipt()["state"], "prepared")

    def symlink(self, source, target):
        try:
            source.symlink_to(target, target_is_directory=target.is_dir())
        except OSError:
            self.skipTest("Host does not permit unprivileged symlink creation")

    def test_symlinked_destination_parent_is_rejected_before_journal(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.symlink(self.data / "Library", outside)
        with self.assertRaisesRegex(TransactionError, "Symlink"):
            self.tx().prepare()
        self.assertFalse(self.journal.exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_inserted_after_install_blocks_rollback(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        self.symlink(self.target / "escape", self.protected)
        with self.assertRaisesRegex(TransactionError, "Symlink"):
            tx.rollback()
        self.check_protected()

    def test_preparation_copy_failure_leaves_blocked_journal_and_unchanged_original(self):
        original = self.original()
        with patch("x86.mellow.transaction.shutil.copytree", side_effect=OSError("injected backup failure")):
            with self.assertRaises(OSError):
                self.tx().prepare()
        self.assertEqual(self.snapshot(self.target), original)
        self.assertEqual(self.receipt()["state"], "preparing")
        with self.assertRaises(TransactionError):
            self.tx().prepare()
        with self.assertRaisesRegex(TransactionError, "Prepare did not complete"):
            restore_installed(self.data, self.journal)

    def test_restore_copy_failure_is_resumable_from_pending_receipt(self):
        original = self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        tx.installed()

        def partial_restore(source, destination):
            path = Path(destination) / "Contents/MacOS/Mellow"
            path.parent.mkdir(parents=True)
            path.write_bytes((Path(source) / "Contents/MacOS/Mellow").read_bytes()[:5])
            raise OSError("injected restore failure")

        with patch("x86.mellow.transaction.shutil.copytree", side_effect=partial_restore):
            with self.assertRaises(OSError):
                restore_installed(self.data, self.journal)
        self.assertEqual(self.receipt()["state"], "rollback_pending")
        with self.assertRaises(TransactionError):
            self.tx().prepare()
        self.assertTrue(restore_installed(self.data, self.journal))
        self.assertEqual(self.snapshot(self.target), original)

    def test_original_removed_by_engine_can_still_be_restored(self):
        original = self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        shutil.rmtree(self.target)
        self.assertTrue(tx.rollback())
        self.assertEqual(self.snapshot(self.target), original)

    def test_receipt_replacement_failure_does_not_claim_files_verified(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        with patch("x86.mellow.transaction.os.replace", side_effect=OSError("injected receipt replace failure")):
            with self.assertRaises(OSError):
                tx.installed()
        self.assertEqual(self.receipt()["state"], "prepared")
        self.assertTrue(tx.rollback())

    def test_deferred_finalize_preserves_receipt_for_cache_retry(self):
        original = self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        tx.installed()
        self.assertTrue(restore_installed(self.data, self.journal, defer_finalize=True))
        self.assertEqual(self.receipt()["state"], "restored")
        self.assertEqual(self.snapshot(self.target), original)
        with self.assertRaises(TransactionError):
            self.tx().prepare()
        with patch("x86.mellow.transaction.shutil.copytree", side_effect=AssertionError("cache retry must not recopy")):
            self.assertTrue(restore_installed(self.data, self.journal, defer_finalize=True))
        self.assertTrue(finalize_restore(self.data, self.journal))
        self.assertFalse(finalize_restore(self.data, self.journal))
        self.assertFalse((self.journal / "active").exists())

    def test_post_restore_external_change_blocks_retry_and_finalization(self):
        self.original()
        tx = self.tx()
        tx.prepare()
        self.install()
        tx.installed()
        restore_installed(self.data, self.journal, defer_finalize=True)
        target = self.target / "Contents/MacOS/Mellow"
        # Even a known original prefix is no longer authorized after restoration.
        target.write_bytes(target.read_bytes()[:3])
        for method in (lambda: restore_installed(self.data, self.journal, defer_finalize=True),
                       lambda: finalize_restore(self.data, self.journal)):
            with self.assertRaisesRegex(TransactionError, "Restored target changed"):
                method()
        self.assertEqual(target.read_bytes(), b"pri")
        self.assertEqual(self.receipt()["state"], "restored")

    def test_finalize_rejects_unrestored_transaction(self):
        self.tx().prepare()
        with self.assertRaisesRegex(TransactionError, "before original files"):
            finalize_restore(self.data, self.journal)

    def test_failed_archive_keeps_restored_receipt_for_retry(self):
        tx = self.tx()
        tx.prepare()
        self.install()
        tx.installed()
        restore_installed(self.data, self.journal, defer_finalize=True)
        with patch("x86.mellow.transaction.os.replace", side_effect=OSError("injected archive failure")):
            with self.assertRaises(OSError):
                finalize_restore(self.data, self.journal)
        self.assertEqual(self.receipt()["state"], "restored")
        self.assertFalse(self.target.exists())
        self.assertTrue(finalize_restore(self.data, self.journal))

    def test_prepare_fsync_failure_never_authorizes_target_overwrite(self):
        original = self.original()
        with patch("x86.mellow.transaction.os.fsync", side_effect=OSError("injected flush failure")):
            with self.assertRaises(OSError):
                self.tx().prepare()
        self.assertEqual(self.snapshot(self.target), original)
        with self.assertRaises(TransactionError):
            self.tx().prepare()

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() == 0,
                         "Ownership restoration needs a privileged POSIX temporary fixture")
    def test_posix_original_owner_is_restored(self):
        self.original()
        file = self.target / "Contents/MacOS/Mellow"
        os.chown(file, 65534, 65534)
        tx = self.tx()
        tx.prepare()
        self.install()
        self.assertEqual(file.stat().st_uid, 0)
        tx.installed()
        self.assertTrue(tx.rollback())
        self.assertEqual((file.stat().st_uid, file.stat().st_gid), (65534, 65534))


if __name__ == "__main__":
    unittest.main()
