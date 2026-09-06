"""Self-authored data and protocol fixtures; no Apple guest or network runs."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

from venfire import restore_chain as chain
from venfire.personalization import _der, _time_left
from venfire.restore import ROLE_TAGS


def container(kind):
    return _der(0x30, _der(0x16, b"IM4P") + _der(0x16, kind) + _der(0x16, b"fixture") + _der(4, b"self-authored payload"))


class ChainTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.serial = self.root / "serial.log"
        self.serial.write_bytes(b"self-authored UART fixture\n")
        self.events = []
        self.components = {}
        identity = {"Info": {"DeviceClass": "vma2macosap", "Variant": "Customer Erase Install (IPSW)"}, "Manifest": {}}
        for role in sorted(chain.REQUIRED_ROLES):
            original, normalized = ROLE_TAGS[role]
            path = self.root / (role + ".im4p")
            path.write_bytes(container(original))
            self.components[role] = str(path)
            identity["Manifest"][role] = {"Digest": hashlib.sha384(container(normalized)).digest()}
        self.manifest = self.root / "BuildManifest.plist"
        self.manifest.write_bytes(plistlib.dumps({"BuildIdentities": [identity]}))
        self.ibss, self.ibec, self.helper = [self.root / name for name in ("ibss", "ibec", "helper")]
        for path in (self.ibss, self.ibec, self.helper):
            path.write_bytes(b"self-authored input")
        self.output = self.root / "chain"
        self.ticket = _der(0x30, _der(0x16, b"IM4M"))

    def append_uart(self, data):
        with self.serial.open("ab") as stream:
            stream.write(data + b"\n")

    def personalize(self, **kwargs):
        component = kwargs["component"]
        self.events.append("personalize:" + component)
        self.assertGreater(kwargs["deadline"], time.monotonic())
        directory = kwargs["output"]
        directory.mkdir()
        target = directory / (component + ".img4")
        target.write_bytes(b"self-authored personalized fixture:" + component.encode())
        result = {"ticket_received": True, "payload_preserved": True, "output": str(target),
                  "personalized_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        if component == "iBEC":
            self.assertTrue(kwargs["include_restore_policy"])
            policy_dir = directory / "restore-policy"
            policy_dir.mkdir()
            policy = policy_dir / "RestoreLocalPolicy.personalized.img4"
            policy.write_bytes(b"self-authored bound policy")
            result["restore_policy"] = {"ticket_received": True, "sha256": hashlib.sha256(policy.read_bytes()).hexdigest()}
        return result

    def dfu(self, socket, image, **kwargs):
        self.events.append("dfu:iBSS")
        self.assertTrue(kwargs["reset"])
        self.assertEqual(kwargs["expected_sha256"], hashlib.sha256(Path(image).read_bytes()).hexdigest())
        self.append_uart(chain.PROMPTS[1])
        return {"transfer_complete": True}

    def reuse(self, **kwargs):
        self.events.append("reuse:bound-ticket")
        self.assertEqual(kwargs["chain_personalization"], self.output / "ibec")
        target = self.root / "same-chain-ticket.im4m"
        target.write_bytes(self.ticket)
        return {"ticket_reused": True, "network_request_sent": False, "ticket_path": str(target)}

    def transport(self, *args, **kwargs):
        context = MagicMock()
        io = context.__enter__.return_value
        def configure(**_):
            self.events.append("configure:recovery")
            return {"actual_fixture": True}
        def upload(path, **options):
            self.assertEqual(options["expected_sha256"], hashlib.sha256(Path(path).read_bytes()).hexdigest())
            self.events.append("upload:policy" if "LocalPolicy" in Path(path).name else "upload:iBEC")
            return {"transfer_complete": True}
        def command(name, **options):
            self.events.append("command:" + name)
            if name == "go":
                self.assertEqual(options["request"], 1)
                self.append_uart(chain.PROMPTS[2])
        io.configure_recovery.side_effect = configure
        io.send_recovery_file.side_effect = upload
        io.send_command.side_effect = command
        return context

    def restore(self, socket, images, **kwargs):
        self.events.append("restore:run-stage")
        for image in images.values():
            self.assertEqual(image["sha256"], hashlib.sha256(Path(image["path"]).read_bytes()).hexdigest())
        return {"sequence_sent": True, "error": None, "input_integrity": {"valid": True}}

    def mocks(self):
        stack = ExitStack()
        stack.enter_context(patch.object(chain, "authorize_host", return_value=Mock(to_dict=lambda: {"fixture": True})))
        stack.enter_context(patch.object(chain, "_wait_dfu", return_value={"dfu_idle_observed": True}))
        stack.enter_context(patch.object(chain, "personalize_firmware", side_effect=self.personalize))
        stack.enter_context(patch.object(chain, "send_dfu_file", side_effect=self.dfu))
        stack.enter_context(patch.object(chain, "RecoveryTransport", side_effect=self.transport))
        stack.enter_context(patch.object(chain, "reuse_restore_ticket", side_effect=self.reuse))
        stack.enter_context(patch.object(chain, "run_stage", side_effect=self.restore))
        return stack

    def execute(self, **overrides):
        args = dict(socket_path="unused-fixture", serial_log=self.serial, build_manifest=self.manifest,
                    ibss=self.ibss, ibec=self.ibec, helper=self.helper, components=self.components,
                    output=self.output, observe_seconds=0)
        args.update(overrides)
        return chain.run_chain(**args)

    def test_exact_policy_ibec_order_and_real_new_uart_markers(self):
        before = self.manifest.read_bytes()
        with self.mocks():
            report = self.execute()
        self.assertEqual(self.events, ["personalize:iBSS", "dfu:iBSS", "personalize:iBEC", "configure:recovery",
                                      "upload:policy", "command:lpolrestore", "upload:iBEC", "command:go",
                                      "reuse:bound-ticket", "restore:run-stage"])
        self.assertTrue(report["chain_completed"])
        self.assertTrue(report["stage1"]["uart_prompt_observed"])
        self.assertTrue(report["stage2"]["uart_prompt_observed"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertFalse(report["xnu_boot_verified"])
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertTrue(all(p["outside_type_bytes_unchanged"] for p in report["prepared"].values()))

    def test_stale_stage2_prompt_does_not_satisfy_later_stage(self):
        self.append_uart(chain.PROMPTS[2])
        offset = self.serial.stat().st_size
        self.append_uart(chain.PROMPTS[1])
        with self.assertRaises(TimeoutError):
            chain.wait_prompt(self.serial, 2, offset, deadline=time.monotonic() + 0.02)

    def test_prompt_with_panic_is_rejected(self):
        self.append_uart(chain.PROMPTS[1] + b"\niBoot Panic: self-authored failure")
        with self.assertRaisesRegex(RuntimeError, "panic"):
            chain.wait_prompt(self.serial, 1, 0, deadline=time.monotonic() + 1)

    def test_transfers_without_stage1_do_not_personalize_ibec(self):
        with self.mocks(), patch.object(chain, "wait_prompt", side_effect=TimeoutError("no actual UART prompt")):
            with self.assertRaises(chain.RestoreChainError):
                self.execute()
        self.assertNotIn("personalize:iBEC", self.events)
        report = json.loads((self.output / "result.json").read_text())
        self.assertFalse(report["chain_completed"])
        self.assertTrue(report["input_integrity"]["valid"])

    def test_fresh_ticket_response_cannot_replace_bound_ticket(self):
        with self.mocks(), patch.object(chain, "reuse_restore_ticket", return_value={"ticket_reused": True, "network_request_sent": True}):
            with self.assertRaisesRegex(chain.RestoreChainError, "without a new request"):
                self.execute()
        self.assertNotIn("restore:run-stage", self.events)

    def test_cancellation_keeps_partial_restore_and_final_integrity(self):
        interruption = KeyboardInterrupt()
        interruption.restore_report = {"sequence_sent": False, "partial": "fixture"}
        with self.mocks(), patch.object(chain, "run_stage", side_effect=interruption):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.execute()
        self.assertIs(caught.exception, interruption)
        report = caught.exception.chain_report
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertEqual(report["restore"]["partial"], "fixture")
        self.assertFalse(report["chain_completed"])

    def test_original_mutation_after_transfer_revokes_completion(self):
        def changed(*args, **kwargs):
            self.ibss.write_bytes(b"changed original fixture")
            return {"sequence_sent": True, "error": None, "input_integrity": {"valid": True}}
        with self.mocks(), patch.object(chain, "run_stage", side_effect=changed):
            with self.assertRaises(chain.RestoreChainError) as caught:
                self.execute()
        self.assertFalse(caught.exception.chain_report["input_integrity"]["valid"])
        self.assertFalse(caught.exception.chain_report["chain_completed"])

    def test_host_guard_precedes_files_and_socket_access(self):
        with patch.object(chain, "authorize_host", side_effect=RuntimeError("denied")), patch.object(chain, "create_manifest") as manifest:
            with self.assertRaisesRegex(RuntimeError, "denied"):
                self.execute()
        manifest.assert_not_called()

    def test_deadline_validation_rejects_nonfinite_and_expired(self):
        for value in (True, float("nan"), float("inf"), -1, 0):
            with self.assertRaises(ValueError):
                chain.duration(value, "fixture")
        with self.assertRaises(TimeoutError):
            _time_left(time.monotonic() - 1)

    def profile(self):
        for name in ("rom", "aux", "disk"):
            (self.root / name).write_bytes(b"self-authored regular asset")
        value = {"schema": 1, "mode": "restore-chain", "firmware": "rom", "aux": "aux", "disk": "disk",
                 "build_manifest": self.manifest.name, "ibss": self.ibss.name, "ibec": self.ibec.name,
                 "uuid": "0x123", "components": {role: Path(path).name for role, path in self.components.items()}}
        path = self.root / "restore-profile.json"
        path.write_text(json.dumps(value))
        return path, value

    def test_profile_resolves_relative_assets_and_preserves_graphics_selection(self):
        path, value = self.profile()
        loaded = chain.load_profile(path)
        self.assertEqual(loaded["uuid"], 0x123)
        self.assertEqual(loaded["graphics"], "auto")
        self.assertTrue(Path(loaded["ibss"]).is_absolute())
        value["graphics"] = "off"
        path.write_text(json.dumps(value))
        self.assertEqual(chain.load_profile(path)["graphics"], "off")

    def test_profile_rejects_unsafe_paths_types_and_arbitrary_guest_roles(self):
        path, value = self.profile()
        for name, invalid in (("schema", True), ("uuid", True), ("aux_offset", 1), ("seconds", 1.5),
                              ("graphics", True), ("ibss", "../ibss"), ("ibec", str(self.root)),
                              ("components", {"arbitrary-kernel": "ibss"})):
            with self.subTest(name=name):
                path.write_text(json.dumps(dict(value, **{name: invalid})))
                with self.assertRaises(ValueError):
                    chain.load_profile(path)

    def test_usb_bundle_preserves_originals_and_uses_relative_asset_names(self):
        profile, _ = self.profile()
        spec = importlib.util.spec_from_file_location("chain_usb_bundle", Path(__file__).resolve().parents[1] / "tools/build_usb.py")
        usb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(usb)
        destination = self.root / "usb-data"
        receipt = usb.bundle_restore_profile(profile, destination, available_bytes=1024**3)
        self.assertTrue(receipt["originals_preserved"])
        self.assertFalse(receipt["tickets_included"])
        loaded = chain.load_profile(destination / "restore-profile.json")
        self.assertEqual(Path(loaded["ibss"]).read_bytes(), self.ibss.read_bytes())
        raw = json.loads((destination / "restore-profile.json").read_text())
        self.assertFalse(Path(raw["ibss"]).is_absolute())
        with self.assertRaisesRegex(ValueError, "working space"):
            usb.bundle_restore_profile(profile, self.root / "too-small", available_bytes=1024)
        self.assertFalse((self.root / "too-small").exists())


if __name__ == "__main__":
    unittest.main()
