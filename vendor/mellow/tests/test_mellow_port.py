"""Artifact and rejection tests; no compiler/GPU success is inferred."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "Tools"))
from mellow_port import PortError, prepare
from mellow_port.core import inventory, lexical

REVISION = "4d7d9486c04d917265f64c55bd23b2cc4fe7749c"
FILE = "drivers/gpu/drm/xe/regs/test_regs.h"
SOURCE = """/* SPDX-License-Identifier: MIT */
/* Copyright 2026 Fixture Authors */
#include <linux/types.h>
#define TEST_REG 0x1234U
#define CONDITIONAL_REG (BASE + 4)
#define BAD_OCTAL 012
#define FUNCTION(x) ((x) + 1)
#define TOO_WIDE 0x10000000000000000
#define BAD_SUFFIX 0x123uLl
static int submit(void) { return linux_submit(); }
"""


class PortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "linux"
        target = self.source / FILE
        target.parent.mkdir(parents=True)
        target.write_text(SOURCE, encoding="utf-8")

    def run_port(self, output="result", **kwargs):
        arguments = {"command": "generate", "source_root": self.source, "target": "xe", "revision": REVISION, "files": [FILE], "output": self.root / output}
        arguments.update(kwargs)
        return prepare(**arguments)

    def test_generation_is_deterministic_and_bounded(self):
        self.assertEqual(self.run_port("one"), self.run_port("two"))
        trees = [{p.relative_to(self.root / folder).as_posix(): p.read_bytes() for p in (self.root / folder).rglob("*") if p.is_file()} for folder in ("one", "two")]
        self.assertEqual(*trees)
        tree = trees[0]
        header = next(v.decode() for k, v in tree.items() if k.endswith(".h"))
        for expected in ("0x1234U", "SPDX-License-Identifier: MIT", "Copyright 2026 Fixture Authors"):
            self.assertIn(expected, header)
        for forbidden in ("linux_submit", "BAD_OCTAL", "CONDITIONAL_REG", "TOO_WIDE", "BAD_SUFFIX"):
            self.assertNotIn(forbidden, header)
        self.assertIn("FATAL_ERROR", tree["CMakeLists.txt"].decode())
        manifest = json.loads(tree["source-manifest.json"])
        self.assertEqual(manifest["files"][0]["sha256"], hashlib.sha256((self.source / FILE).read_bytes()).hexdigest())
        self.assertFalse(manifest["revision_membership_verified"])
        inventory = json.loads(tree["inventory.json"])["files"][0]
        self.assertIn("linux/types.h", inventory["includes_lexical"])
        self.assertIn("linux_submit", inventory["call_tokens_approximate"])
        gaps = json.loads(tree["gap-report.json"])
        self.assertFalse(gaps["driver_ready"])
        self.assertTrue(any(item["id"].startswith("functions:") for item in gaps["gaps"]))

    def test_ready_gate_fails_after_emitting_review_artifacts(self):
        result = self.run_port(require_ready=True)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["compile_performed"])
        self.assertFalse(result["hardware_test_performed"])
        self.assertTrue((self.root / "result/gap-report.json").exists())

    def test_comments_preserve_token_boundaries_and_source_lines(self):
        source = "#define JOINED 1/**/2\n/* first\nsecond */\n#define REAL 0x20U\n#define WITH_NOTE 7 /* note */\n"
        data = inventory(FILE, source)
        self.assertEqual([(item["name"], item["literal"], item["line"]) for item in data["simple_integer_defines"]], [("REAL", "0x20U", 4), ("WITH_NOTE", "7", 5)])
        self.assertIn("JOINED", [item["name"] for item in data["unconverted_macros"]])
        tokens = lexical("one/**/two\n/* a\nb */ three()")
        self.assertIn("one two", tokens)
        self.assertEqual(tokens.count("\n"), 2)

    def test_equal_named_identical_headers_keep_distinct_provenance(self):
        other = "drivers/gpu/drm/xe/abi/test_regs.h"
        path = self.source / other
        path.parent.mkdir(parents=True)
        path.write_bytes((self.source / FILE).read_bytes())
        self.run_port(files=[FILE, other])
        backend = json.loads((self.root / "result/backend.json").read_text())
        exports = backend["review_headers"]
        self.assertEqual(len(exports), 2)
        self.assertEqual(len({item["path"] for item in exports}), 2)
        self.assertEqual({item["source"] for item in exports}, {FILE, other})
        for item in exports:
            content = (self.root / "result" / item["path"]).read_text()
            self.assertIn(" * Source: " + item["source"] + "\n", content)

    def test_reject_binary_and_path_traversal(self):
        for path in ("../escape.h", "/absolute.h", "C:/outside.h", FILE + ":stream.h", "drivers/gpu/drm/xe/driver.ko", "drivers/gpu/drm/xe/driver.run"):
            with self.subTest(path=path), self.assertRaises(PortError):
                self.run_port(files=[path])
        (self.source / FILE).write_bytes(b"\x7fELF\0binary")
        with self.assertRaises(PortError):
            self.run_port()

    def test_recipe_requires_explicit_backend_source(self):
        with self.assertRaises(PortError):
            self.run_port(target="amdgpu")
        with self.assertRaises(PortError):
            self.run_port(target="rx9070")
        with self.assertRaises(PortError):
            self.run_port(revision="main")
        for target, relative in (("amdgpu", "drivers/gpu/drm/amd/amdgpu/fixture.h"), ("nvidia-open", "kernel-open/nvidia/fixture.h")):
            path = self.source / relative
            path.parent.mkdir(parents=True)
            path.write_text(SOURCE, encoding="utf-8")
            self.run_port(target, target=target, files=[relative])
            self.assertEqual(json.loads((self.root / target / "backend.json").read_text())["pci_device_ids"], [])

    def test_output_never_overwrites_or_modifies_source(self):
        before = (self.source / FILE).read_bytes()
        with self.assertRaises(PortError):
            self.run_port(output=self.source / "generated")
        self.run_port()
        with self.assertRaises(PortError):
            self.run_port()
        self.assertEqual((self.source / FILE).read_bytes(), before)

    def test_symlink_not_admitted(self):
        link = self.source / "drivers/gpu/drm/xe/linked.h"
        try:
            link.symlink_to(self.source / FILE)
        except (OSError, NotImplementedError):
            self.skipTest("OS does not permit creating test symlink")
        with self.assertRaises(PortError):
            self.run_port(files=["drivers/gpu/drm/xe/linked.h"])

    def test_missing_and_gpl_license_are_not_approved(self):
        (self.source / FILE).write_text(SOURCE.replace("SPDX-License-Identifier: MIT", "SPDX-License-Identifier: GPL-2.0-only OR MIT"), encoding="utf-8")
        self.run_port("gpl")
        facts = json.loads((self.root / "gpl/source-manifest.json").read_text())["files"][0]["license"]
        self.assertTrue(facts["gpl_component_review_required"])
        self.assertFalse(facts["license_compatibility_determined"])
        (self.source / FILE).write_text("#define REG 0x10\n", encoding="utf-8")
        self.run_port("unknown")
        self.assertFalse((self.root / "unknown/generated").exists())

    def test_cli_exit_and_does_not_execute_source(self):
        (self.source / "RUN-ME.sh").write_text("touch SHOULD-NOT-EXIST\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(REPO / "Tools/mellow-port.py"), "plan", "--source-root", str(self.source), "--target", "xe", "--revision", REVISION, "--file", FILE, "--output", str(self.root / "cli"), "--require-ready"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue(json.loads(result.stdout)["artifacts_generated"])
        self.assertFalse((self.source / "SHOULD-NOT-EXIST").exists())

    def test_optional_real_pinned_xe_subset(self):
        capture = REPO.parent / "xe-submission-primary/drivers_gpu_drm_xe_abi_guc_klvs_abi.h"
        if not capture.exists():
            self.skipTest("local upstream capture unavailable")
        data = capture.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), "b52b164a997275d3a9e99189844fea6d25913c060260a21ee8b6252615c86613")
        relative = "drivers/gpu/drm/xe/abi/guc_klvs_abi.h"
        path = self.source / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        self.run_port("upstream", files=[relative])
        manifest = json.loads((self.root / "upstream/source-manifest.json").read_text())
        self.assertEqual(manifest["files"][0]["license"]["single_expression"], "MIT")
        self.assertTrue(list((self.root / "upstream/generated").glob("*.h")))


if __name__ == "__main__":
    unittest.main()
