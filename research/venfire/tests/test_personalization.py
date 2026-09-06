"""Self-authored IMG4-shaped fixtures; never real tickets or Apple firmware."""

from contextlib import contextmanager, ExitStack
import hashlib
import json
from pathlib import Path
import plistlib
import ssl
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error

from venfire.personalization import (
    _der, _der_content, _NoRedirect, _tss_opener, personalize_ibss, wrap_ibss,
    personalize_firmware, RESTORE_POLICY,
    request_restore_ticket, reuse_restore_ticket, MAX_BUILD_MANIFEST,
)
from venfire.artifacts import ArtifactIntegrityError, read_regular, verify_manifest
from venfire.process import BoundedProcessError


class PersonalizationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.payload = _der(0x30, _der(0x16, b"IM4P") + _der(0x16, b"ibss") +
                            _der(4, b"self-authored test bytes" * 20))
        self.ticket = _der(0x30, _der(0x16, b"IM4M") + _der(4, b"NOT A SIGNED TICKET"))
        self.live = dict(CPID=0xfe00, BDID=0x20, SDOM=1, CPFM=3, SCEP=1,
                         ECID=42, NONC=b"N" * 32, SNON=b"S" * 20)
        self.identity = dict(ApChipID="0xFE00", ApBoardID="0x20", ApSecurityDomain="0x01",
                             Info={"Variant": "Customer Erase Install (IPSW)"},
                             Manifest={"iBSS": {"Digest": hashlib.sha384(self.payload).digest()}})
        self.manifest = self.root / "manifest.plist"
        self.manifest.write_bytes(plistlib.dumps({"BuildIdentities": [self.identity]}))
        self.ibss = self.root / "ibss.fixture"
        self.ibss.write_bytes(self.payload)
        self.helper = self.root / "helper.fixture"
        self.helper.write_bytes(b"not executed")
        self.output = self.root / "output"

    def run_personalize(self):
        return personalize_ibss(socket_path="no-real-socket", build_manifest=self.manifest,
                                ibss=self.ibss, helper=str(self.helper), output=self.output)

    def patches(self, *, identities=None):
        host = Mock()
        host.to_dict.return_value = {"fixture": True}
        response = Mock()
        response.url = "https://gs.apple.com/TSS/controller?action=2"
        response.status = 200
        response.read.return_value = b"STATUS=0&MESSAGE=SUCCESS&REQUEST_STRING=" + plistlib.dumps({"ApImg4Ticket": self.ticket})
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        contexts = [
            patch("venfire.personalization.authorize_host", return_value=host),
            patch("venfire.personalization.RecoveryTransport"),
            patch("venfire.personalization._identity", side_effect=identities or [self.live, self.live]),
            patch("venfire.personalization._tss_opener", return_value=opener),
            patch("venfire.personalization.run_bounded", return_value=Mock(stdout=plistlib.dumps({"fixture": True}))),
        ]
        for context in contexts:
            context.start()
            self.addCleanup(context.stop)
        return opener, response

    def test_host_denial_precedes_input_read_or_network(self):
        with patch("venfire.personalization.authorize_host", side_effect=RuntimeError("host denied")), \
                patch("venfire.personalization.create_manifest") as read, \
                patch("venfire.personalization._tss_opener") as network:
            with self.assertRaisesRegex(RuntimeError, "host denied"):
                self.run_personalize()
        read.assert_not_called()
        network.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_wrapper_preserves_exact_original_component_and_ticket(self):
        result = wrap_ibss(self.payload, self.ticket)
        self.assertEqual(_der_content(result, b"IMG4"),
                         _der(0x16, b"IMG4") + self.payload + _der(0xa0, self.ticket))
        for invalid in (self.payload + b"trailing", self.payload.replace(b"ibss", b"ibec"),
                        b"\x30\x80" + self.payload):
            with self.assertRaises(ValueError):
                wrap_ibss(invalid, self.ticket)

    def test_mismatched_component_never_reaches_signing_service(self):
        opener, _ = self.patches()
        self.ibss.write_bytes(self.payload[:-1] + bytes([self.payload[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.run_personalize()
        opener.open.assert_not_called()
        self.assertFalse((self.output / "iBSS.personalized.img4").exists())

    def test_nonce_change_during_request_denies_output(self):
        self.patches(identities=[self.live, {**self.live, "NONC": b"X" * 32}])
        with self.assertRaisesRegex(RuntimeError, "nonce changed"):
            self.run_personalize()
        self.assertFalse((self.output / "iBSS.personalized.img4").exists())
        report = json.loads((self.output / "result.json").read_text())
        self.assertFalse(report["ticket_received"])
        self.assertTrue(report["input_integrity"]["valid"])

    def test_server_denial_is_not_a_ticket(self):
        _, response = self.patches()
        response.read.return_value = b"STATUS=94&MESSAGE=denied"
        with self.assertRaisesRegex(RuntimeError, "status=94"):
            self.run_personalize()
        self.assertFalse((self.output / "apple-ticket.private.im4m").exists())

    def test_successful_transport_still_never_claims_boot_or_valid_signature(self):
        self.patches()
        report = self.run_personalize()
        self.assertTrue(report["ticket_received"])
        self.assertTrue(report["payload_preserved"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertNotIn("signature_valid", report)
        self.assertEqual(self.ibss.read_bytes(), self.payload)

    def test_tls_verification_and_hostname_checks_remain_enabled(self):
        opener = _tss_opener()
        https = next(handler for handler in opener.handlers if hasattr(handler, "_context"))
        self.assertEqual(https._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(https._context.check_hostname)
        with self.assertRaisesRegex(RuntimeError, "redirects"):
            _NoRedirect().redirect_request(None, None, 302, "", {}, "http://example.invalid/")

    def test_restore_policy_is_signed_for_exact_next_stage_and_current_nonce(self):
        self.payload = self.payload.replace(b"ibss", b"ibec")
        self.ibss.write_bytes(self.payload)
        self.identity["Manifest"] = {"iBEC": {"Digest": hashlib.sha384(self.payload).digest()}}
        self.manifest.write_bytes(plistlib.dumps({"BuildIdentities": [self.identity]}))
        opener, _ = self.patches(identities=[self.live] * 3)
        result = personalize_firmware(socket_path="fixture", build_manifest=self.manifest,
            firmware=self.ibss, component="iBEC", helper=str(self.helper), output=self.output,
            include_restore_policy=True)
        self.assertEqual(opener.open.call_count, 2)
        parameters = plistlib.loads((self.output / "restore-policy/live-parameters.private.plist").read_bytes())
        self.assertEqual(parameters["Ap,NextStageIM4MHash"], hashlib.sha384(self.ticket).digest())
        self.assertEqual(parameters["Ap,LocalPolicy"]["Digest"], hashlib.sha384(RESTORE_POLICY).digest())
        self.assertEqual(parameters["ApNonce"], self.live["NONC"])
        self.assertEqual(parameters["ApECID"], self.live["ECID"])
        self.assertTrue(parameters["ApSecurityMode"])
        self.assertTrue(parameters["ApProductionMode"])
        self.assertFalse(parameters["Ap,LocalBoot"])
        self.assertTrue(result["restore_policy"]["ticket_received"])
        self.assertFalse(result["restore_policy"]["guest_acceptance_verified"])

    def test_changed_nonce_after_policy_request_prevents_firmware_outputs(self):
        self.payload = self.payload.replace(b"ibss", b"ibec")
        self.ibss.write_bytes(self.payload)
        self.identity["Manifest"] = {"iBEC": {"Digest": hashlib.sha384(self.payload).digest()}}
        self.manifest.write_bytes(plistlib.dumps({"BuildIdentities": [self.identity]}))
        self.patches(identities=[self.live, self.live, {**self.live, "NONC": b"C" * 32}])
        with self.assertRaisesRegex(RuntimeError, "nonce changed"):
            personalize_firmware(socket_path="fixture", build_manifest=self.manifest,
                firmware=self.ibss, component="iBEC", helper=str(self.helper), output=self.output,
                include_restore_policy=True)
        self.assertFalse((self.output / "iBEC.personalized.img4").exists())
        self.assertFalse((self.output / "restore-policy/RestoreLocalPolicy.personalized.img4").exists())


class RestoreBatchPersonalizationTests(unittest.TestCase):
    """Real files and hashes, isolated device/HTTP fixtures; no Apple requests."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.manifest, self.helper = self.root / "BuildManifest.plist", self.root / "encoder.fixture"
        self.output = self.root / "output"
        self.original = self.root / "original-container.fixture"
        self.original.write_bytes(b"self-authored original provenance input")
        self.helper.write_bytes(b"self-authored encoder identity; execution is isolated")
        self.components, self.digests, self.sha256 = {}, {}, {}
        self.live = dict(CPID=0xfe00, BDID=0x20, SDOM=1, CPFM=3, SCEP=1,
                         ECID=42, NONC=b"N" * 32, SNON=b"S" * 20)
        self.ticket = _der(0x30, _der(0x16, b"IM4M") + _der(4, b"SELF AUTHORED UNSIGNED TEST TICKET"))
        self.response_bytes = b"STATUS=0&MESSAGE=SUCCESS&REQUEST_STRING=" + plistlib.dumps({"ApImg4Ticket": self.ticket})
        self.add_component("RestoreKernelCache", b"rkrn", 1024)
        self.write_manifest()

    def add_component(self, role, tag, payload_size):
        # Write the fixture and its manifest digest incrementally, including
        # large ramdisks, without allocating the complete component in setup.
        def header(kind, length):
            if length < 128:
                return bytes((kind, length))
            encoded = length.to_bytes((length.bit_length() + 7) // 8, "big")
            return bytes((kind, 0x80 | len(encoded))) + encoded
        fields = _der(0x16, b"IM4P") + _der(0x16, tag) + _der(0x16, b"self-authored") + header(4, payload_size)
        prefix = header(0x30, len(fields) + payload_size) + fields
        path = self.root / (role + ".fixture.im4p")
        digest, sha256 = hashlib.sha384(), hashlib.sha256()
        with path.open("wb") as stream:
            stream.write(prefix)
            digest.update(prefix)
            sha256.update(prefix)
            remaining = payload_size
            while remaining:
                chunk = b"F" * min(1024 * 1024, remaining)
                stream.write(chunk)
                digest.update(chunk)
                sha256.update(chunk)
                remaining -= len(chunk)
        self.components[role] = path
        self.digests[role], self.sha256[role] = digest.digest(), sha256.hexdigest()

    def write_manifest(self):
        identity = {"ApChipID": "0xfe00", "ApBoardID": "0x20", "ApSecurityDomain": "0x1",
                    "Info": {"DeviceClass": "vma2macosap", "Variant": "Customer Erase Install (IPSW)"},
                    "Manifest": {role: {"Digest": digest} for role, digest in self.digests.items()}}
        self.manifest.write_bytes(plistlib.dumps({"BuildIdentities": [identity]}))

    @contextmanager
    def isolated_io(self, *, identities=None, helper_failure=None, network_failure=None, response_reader=None):
        host = Mock()
        host.to_dict.return_value = {"fixture": "isolated batch API test"}
        response = Mock(url="https://gs.apple.com/TSS/controller?action=2", status=200)
        if response_reader:
            response.read.side_effect = response_reader
        else:
            response.read.return_value = self.response_bytes
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        if network_failure:
            opener.open.side_effect = network_failure
        with ExitStack() as stack:
            stack.enter_context(patch("venfire.personalization.authorize_host", return_value=host))
            transport = stack.enter_context(patch("venfire.personalization.RecoveryTransport"))
            live = stack.enter_context(patch("venfire.personalization._identity", side_effect=identities or [self.live] * 2))
            stack.enter_context(patch("venfire.personalization._tss_opener", return_value=opener))
            encoder = stack.enter_context(patch("venfire.personalization.run_bounded",
                side_effect=helper_failure, return_value=subprocess.CompletedProcess(
                    ["fixture"], 0, stdout=plistlib.dumps({"self_authored_request": True}), stderr=b"")))
            yield {"opener": opener, "response": response, "encoder": encoder, "transport": transport, "live": live}

    def request(self, **overrides):
        kwargs = dict(socket_path="unused-test-socket", build_manifest=self.manifest,
            components=self.components, helper=self.helper, output=self.output,
            original_inputs=[self.original, self.components["RestoreKernelCache"]])
        kwargs.update(overrides)
        return request_restore_ticket(**kwargs)

    def result(self):
        return json.loads((self.output / "result.json").read_text())

    def assert_no_ticket(self):
        self.assertFalse((self.output / "apple-ticket.private.im4m").exists())
        self.assertFalse(self.result()["ticket_received"])

    def test_large_ramdisk_is_hashed_incrementally_and_ticket_binds_live_identity(self):
        self.add_component("RestoreRamDisk", b"rdsk", 9 * 1024 * 1024 + 113)
        self.write_manifest()
        reads = []
        ramdisk = self.components["RestoreRamDisk"]

        @contextmanager
        def guarded_read(path):
            with read_regular(path) as stream:
                if Path(path) != ramdisk:
                    yield stream
                    return
                class BoundedReader:
                    def read(self, size=-1):
                        self_outer.assertGreater(size, 0)
                        self_outer.assertLessEqual(size, 1024 * 1024)
                        reads.append(size)
                        return stream.read(size)
                self_outer = self
                yield BoundedReader()

        with self.isolated_io() as io, patch("venfire.personalization.read_regular", guarded_read):
            report = self.request()
        self.assertGreater(len(reads), 9)
        self.assertEqual(report["components"]["RestoreRamDisk"]["bytes"], ramdisk.stat().st_size)
        self.assertEqual(report["components"]["RestoreRamDisk"]["sha256"], self.sha256["RestoreRamDisk"])
        self.assertTrue(report["input_integrity"]["valid"])
        self.assertEqual(report["stage"], "complete")
        self.assertFalse(report["macos_boot_verified"])
        self.assertEqual(Path(report["ticket_path"]).read_bytes(), self.ticket)
        io["encoder"].assert_called_once()
        io["opener"].open.assert_called_once()
        for call in io["live"].call_args_list:
            self.assertFalse(call.kwargs["require_dfu_idle"])
        parameters = plistlib.loads((self.output / "live-parameters.private.plist").read_bytes())
        self.assertEqual(parameters["ApECID"], self.live["ECID"])
        self.assertEqual(parameters["ApNonce"], self.live["NONC"])
        self.assertEqual(parameters["ApSepNonce"], self.live["SNON"])
        self.assertTrue(parameters["ApSecurityMode"])
        self.assertTrue(parameters["ApProductionMode"])
        self.assertFalse(parameters["ApInRomDFU"])

    def test_digest_mismatch_denies_encoder_and_network(self):
        self.digests["RestoreKernelCache"] = bytes(48)
        self.write_manifest()
        with self.isolated_io() as io:
            with self.assertRaisesRegex(ValueError, "does not match"):
                self.request()
        io["encoder"].assert_not_called()
        io["opener"].open.assert_not_called()
        self.assert_no_ticket()
        self.assertEqual(self.result()["stage"], "validate-components")
        self.assertEqual(self.result()["error_type"], "ValueError")

    def test_network_failure_is_preserved_without_ticket(self):
        failure = urllib.error.URLError("isolated network denial")
        with self.isolated_io(network_failure=failure):
            with self.assertRaises(urllib.error.URLError) as raised:
                self.request()
        self.assertIs(raised.exception, failure)
        self.assert_no_ticket()
        self.assertEqual(self.result()["stage"], "request-ticket")
        self.assertIn("isolated network denial", self.result()["error"])

    def test_server_denial_preserves_status_and_produces_no_ticket(self):
        with self.isolated_io() as io:
            io["response"].read.return_value = b"STATUS=94&MESSAGE=SELF_AUTHORED_DENIAL"
            with self.assertRaisesRegex(RuntimeError, "status=94"):
                self.request()
        self.assert_no_ticket()
        self.assertEqual(self.result()["tss_status"], "94")

    def test_nonce_change_prevents_ticket_output(self):
        with self.isolated_io(identities=[self.live, {**self.live, "NONC": b"X" * 32}]):
            with self.assertRaisesRegex(RuntimeError, "nonce changed"):
                self.request()
        self.assert_no_ticket()
        self.assertEqual(self.result()["stage"], "verify-live-nonce")
        self.assertTrue(self.result()["input_integrity"]["valid"])

    def test_invalid_role_is_rejected_before_input_or_http(self):
        with self.isolated_io() as io, patch("venfire.personalization.create_manifest") as read:
            with self.assertRaisesRegex(ValueError, "standard restore"):
                self.request(components={"iBSS": self.original})
        read.assert_not_called()
        io["transport"].assert_not_called()
        io["opener"].open.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_original_change_during_http_is_reported_and_denies_ticket(self):
        def changed_input(_):
            self.original.write_bytes(b"different provenance bytes")
            return self.response_bytes
        with self.isolated_io(response_reader=changed_input):
            with self.assertRaises(ArtifactIntegrityError):
                self.request()
        self.assert_no_ticket()
        self.assertFalse(self.result()["input_integrity"]["valid"])
        self.assertEqual(self.result()["error_type"], "ArtifactIntegrityError")

    def test_final_integrity_failure_revokes_ticket_output_and_success(self):
        changed = False
        def final_verification(sources):
            nonlocal changed
            if (self.output / "apple-ticket.private.im4m").exists() and not changed:
                changed = True
                self.original.write_bytes(b"source changed at final integrity check")
            return verify_manifest(sources)
        with self.isolated_io(), patch("venfire.personalization.verify_manifest", final_verification):
            with self.assertRaises(ArtifactIntegrityError):
                self.request()
        self.assertTrue(changed)
        self.assert_no_ticket()
        self.assertFalse(self.result()["input_integrity"]["valid"])
        self.assertNotEqual(self.result()["stage"], "complete")
        self.assertEqual(self.result()["error_type"], "ArtifactIntegrityError")

    def test_bounded_encoder_failure_preserves_stage_and_never_uses_http(self):
        failure = BoundedProcessError("stdout-limit", [str(self.helper)], timeout=30,
            returncode=-9, stdout=b"bounded partial output", stderr=b"bounded diagnostic", elapsed=0.1)
        with self.isolated_io(helper_failure=failure) as io:
            with self.assertRaises(BoundedProcessError) as raised:
                self.request()
        self.assertIs(raised.exception, failure)
        self.assert_no_ticket()
        self.assertEqual(self.result()["stage"], "encode-request")
        self.assertEqual(self.result()["error_type"], "BoundedProcessError")
        self.assertIn("stdout-limit", self.result()["error"])
        io["opener"].open.assert_not_called()

    def test_final_integrity_error_is_not_suppressed_by_callers_handled_exception(self):
        def final_verification(sources):
            if (self.output / "apple-ticket.private.im4m").exists():
                self.original.write_bytes(b"changed at final integrity check")
            return verify_manifest(sources)
        with self.isolated_io(), patch("venfire.personalization.verify_manifest", final_verification):
            try:
                raise ValueError("already handled by the caller")
            except ValueError:
                with self.assertRaises(ArtifactIntegrityError):
                    self.request()
        self.assert_no_ticket()

    def test_original_helper_exception_survives_final_integrity_failure(self):
        failure = BoundedProcessError("stderr-limit", [str(self.helper)], timeout=30,
            returncode=-9, stdout=b"", stderr=b"bounded diagnostic", elapsed=0.1)
        def final_verification(sources):
            self.original.write_bytes(b"changed during failing helper call")
            return verify_manifest(sources)
        with self.isolated_io(helper_failure=failure), \
                patch("venfire.personalization.verify_manifest", final_verification):
            with self.assertRaises(BoundedProcessError) as raised:
                self.request()
        self.assertIs(raised.exception, failure)
        self.assert_no_ticket()
        self.assertFalse(self.result()["input_integrity"]["valid"])

    def test_oversized_manifest_is_rejected_before_device_or_http(self):
        with self.manifest.open("r+b") as stream:
            stream.truncate(MAX_BUILD_MANIFEST + 1)
        with self.isolated_io() as io:
            with self.assertRaisesRegex(ValueError, "32 MiB"):
                self.request()
        self.assert_no_ticket()
        self.assertEqual(self.result()["stage"], "read-manifest")
        io["transport"].assert_not_called()
        io["encoder"].assert_not_called()
        io["opener"].open.assert_not_called()


class RestoreChainReuseTests(unittest.TestCase):
    """Build a self-authored iBEC/LPOL fixture through the real preparation API."""

    add_component = RestoreBatchPersonalizationTests.add_component
    write_manifest = RestoreBatchPersonalizationTests.write_manifest
    isolated_io = RestoreBatchPersonalizationTests.isolated_io
    result = RestoreBatchPersonalizationTests.result
    assert_no_ticket = RestoreBatchPersonalizationTests.assert_no_ticket

    def setUp(self):
        RestoreBatchPersonalizationTests.setUp(self)
        self.ibec = self.root / "iBEC.self-authored.im4p"
        self.ibec.write_bytes(_der(0x30, _der(0x16, b"IM4P") + _der(0x16, b"ibec")
            + _der(0x16, b"self-authored") + _der(4, b"no Apple executable bytes")))
        manifest = plistlib.loads(self.manifest.read_bytes())
        manifest["BuildIdentities"][0]["Manifest"]["iBEC"] = {"Digest": hashlib.sha384(self.ibec.read_bytes()).digest()}
        self.manifest.write_bytes(plistlib.dumps(manifest))
        self.chain = self.root / "original-chain"
        self.policy_ticket = _der(0x30, _der(0x16, b"IM4M") + _der(4, b"DISTINCT UNSIGNED POLICY TEST TICKET"))
        with self.isolated_io(identities=[self.live] * 3) as io:
            io["response"].read.side_effect = [self.response_bytes,
                b"STATUS=0&MESSAGE=SUCCESS&REQUEST_STRING=" + plistlib.dumps({"ApImg4Ticket": self.policy_ticket})]
            personalize_firmware(socket_path="unused-fixture", build_manifest=self.manifest,
                firmware=self.ibec, component="iBEC", helper=self.helper, output=self.chain,
                include_restore_policy=True)
        self.assertNotEqual(self.ticket, self.policy_ticket)

    def request(self, **overrides):
        kwargs = dict(socket_path="unused-fixture", build_manifest=self.manifest,
            components=self.components, chain_personalization=self.chain,
            output=self.output, original_inputs=[self.original])
        kwargs.update(overrides)
        return reuse_restore_ticket(**kwargs)

    def test_exact_live_chain_ticket_is_reused_without_encoder_or_http(self):
        with self.isolated_io() as io:
            report = self.request()
        self.assertEqual(Path(report["ticket_path"]).read_bytes(), self.ticket)
        self.assertEqual(report["ticket_sha256"], hashlib.sha256(self.ticket).hexdigest())
        self.assertEqual(report["next_stage_ticket_sha384"], hashlib.sha384(self.ticket).hexdigest())
        self.assertTrue(report["ticket_reused"])
        self.assertTrue(report["ticket_received"])
        self.assertFalse(report["network_request_sent"])
        self.assertFalse(report["macos_boot_verified"])
        self.assertTrue(report["input_integrity"]["valid"])
        io["opener"].open.assert_not_called()
        io["encoder"].assert_not_called()
        self.assertEqual((self.chain / "apple-ticket.private.im4m").read_bytes(), self.ticket)

    def test_live_ecid_or_nonce_change_denies_reuse(self):
        for field, changed in (("ECID", 43), ("NONC", b"X" * 32)):
            with self.subTest(field=field):
                self.output = self.root / ("denied-" + field)
                live = {**self.live, field: changed}
                with self.isolated_io(identities=[live] * 2) as io:
                    with self.assertRaisesRegex(ValueError, "identity or nonce differs"):
                        self.request()
                self.assert_no_ticket()
                self.assertFalse(self.result()["ticket_reused"])
                io["opener"].open.assert_not_called()
                io["encoder"].assert_not_called()

    def test_new_manifest_identity_cannot_replace_original_chain_identity(self):
        candidate = self.root / "different-BuildManifest.plist"
        manifest = plistlib.loads(self.manifest.read_bytes())
        manifest["BuildIdentities"][0]["Info"]["BuildNumber"] = "SELF_AUTHORED_DIFFERENT_BUILD"
        candidate.write_bytes(plistlib.dumps(manifest))
        with self.isolated_io() as io:
            with self.assertRaisesRegex(ValueError, "identity differs"):
                self.request(build_manifest=candidate)
        self.assert_no_ticket()
        io["opener"].open.assert_not_called()

    def test_lpol_next_stage_hash_mismatch_denies_reuse_before_device_access(self):
        path = self.chain / "restore-policy/live-parameters.private.plist"
        policy = plistlib.loads(path.read_bytes())
        policy["Ap,NextStageIM4MHash"] = hashlib.sha384(self.policy_ticket).digest()
        path.write_bytes(plistlib.dumps(policy))
        with self.isolated_io() as io:
            with self.assertRaisesRegex(ValueError, "does not bind"):
                self.request()
        self.assert_no_ticket()
        io["transport"].assert_not_called()
        io["opener"].open.assert_not_called()
        io["encoder"].assert_not_called()

    def test_nonce_change_during_chain_validation_prevents_output(self):
        with self.isolated_io(identities=[self.live, {**self.live, "NONC": b"Y" * 32}]) as io:
            with self.assertRaisesRegex(RuntimeError, "nonce changed during chain"):
                self.request()
        self.assert_no_ticket()
        self.assertFalse(self.result()["ticket_reused"])
        io["opener"].open.assert_not_called()

    def test_final_integrity_failure_removes_ticket_and_revokes_reused_status(self):
        def final_verification(sources):
            if (self.output / "apple-ticket.private.im4m").exists():
                self.original.write_bytes(b"changed after chain copy before final verification")
            return verify_manifest(sources)
        with self.isolated_io() as io, patch("venfire.personalization.verify_manifest", final_verification):
            with self.assertRaises(ArtifactIntegrityError):
                self.request()
        self.assert_no_ticket()
        self.assertFalse(self.result()["ticket_reused"])
        self.assertFalse(self.result()["input_integrity"]["valid"])
        self.assertEqual(self.result()["error_type"], "ArtifactIntegrityError")
        io["opener"].open.assert_not_called()


if __name__ == "__main__":
    unittest.main()

