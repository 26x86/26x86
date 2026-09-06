#!/usr/bin/env python3
"""Adversarial translator-report controls; synthetic executables, no GPU/LLVM."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))
spec = importlib.util.spec_from_file_location("mellow_shader", ROOT / "Tools/mellow-shader.py")
shader = importlib.util.module_from_spec(spec); spec.loader.exec_module(shader)


@unittest.skipIf(os.name == "nt", "Synthetic POSIX executables for tool protocol tests")
class Reports(unittest.TestCase):
    def invoke(self, report=None, *, code=0, body=None, timeout=1):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-translator"
            if body is None:
                text = report if isinstance(report, str) else json.dumps(report)
                body = "print(" + repr(text) + ")\nraise SystemExit(" + str(code) + ")\n"
            path.write_text("#!/usr/bin/python3\n" + body); path.chmod(0o700)
            return shader.lower(b"synthetic", "msl", "test", path, timeout=timeout)

    def good(self):
        return {"schema_version": 1, "status": "LOWERED_OPENCL_C_ONLY", "gpu_executed": False,
                "input": "msl", "entry": "test", "opencl_source": "synthetic output", "diagnostics": []}

    def test_explicit_protocol_positive(self):
        self.assertEqual(self.invoke(self.good())["status"], "LOWERED_OPENCL_C_ONLY")

    def test_scope_identity_and_type_mutations(self):
        for key, value in (("entry", "other"), ("input", "air-text"), ("schema_version", True),
                           ("gpu_executed", True), ("gpu_executed", 0), ("opencl_source", ""),
                           ("opencl_source", []), ("diagnostics", "warning"), ("status", "PASS")):
            changed = self.good(); changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(shader.AirError): self.invoke(changed)

    def test_process_status_contradiction(self):
        with self.assertRaises(shader.AirError): self.invoke(self.good(), code=7)

    def test_untrusted_evidence_fields(self):
        for key, value in (("hardware_execution", True), ("metal_acceleration", True),
                           ("decoder", {"decoded_by_llvm": True})):
            changed = self.good(); changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(shader.AirError, "unknown"):
                self.invoke(changed)

    def test_duplicate_keys_and_nonfinite(self):
        for text in ('{"status":"LOWERED_OPENCL_C_ONLY","status":"REJECTED"}', '{"value":NaN}', '[]', '{}', 'text'):
            with self.subTest(text=text), self.assertRaises(shader.AirError): self.invoke(text)

    def test_rejected_contract(self):
        report = self.good(); report.update(status="REJECTED", entry="", opencl_source="", diagnostics=["unsupported"])
        self.assertEqual(self.invoke(report, code=2)["status"], "REJECTED")
        with self.assertRaises(shader.AirError): self.invoke(report, code=0)
        report["opencl_source"] = "stale output"
        with self.assertRaises(shader.AirError): self.invoke(report, code=2)

    def test_running_output_limit(self):
        with self.assertRaisesRegex(shader.AirError, "byte limit"):
            self.invoke(body="import sys,time\nprint('x' * 300000, flush=True)\ntime.sleep(5)\n")

    def test_timeout(self):
        with self.assertRaisesRegex(shader.AirError, "timed out"):
            self.invoke(body="import time\ntime.sleep(5)\n", timeout=0.1)

    def test_input_change(self):
        body = "import pathlib,sys\npathlib.Path(sys.argv[2]).write_bytes(b'changed')\nprint(" + repr(json.dumps(self.good())) + ")\n"
        with self.assertRaisesRegex(shader.AirError, "changed"): self.invoke(body=body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
