#!/usr/bin/env python3
"""Container and process failure controls; these tests never claim GPU execution."""
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mellow_air", ROOT / "Tools/mellow_air.py")
air = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(air)


def tag(name, payload):
    return name + struct.pack("<H", len(payload)) + payload


def fixture(*, duplicate=False):
    # Deliberately synthetic, magic-only payload for container validation, never
    # presented to a compiler or accepted as an actual AIR shader fixture.
    raw = air.MAGIC + b"\0" * 4
    wrapped = struct.pack("<5I", 0x0B17C0DE, 0, 20, len(raw), 0xFFFFFFFF) + raw
    wrapped += b"\0" * (-len(wrapped) % 16)
    tags = tag(b"NAME", b"test\0") + tag(b"TYPE", b"\x02")
    if duplicate:
        tags += tag(b"NAME", b"evil\0")
    tags += tag(b"HASH", hashlib.sha256(wrapped).digest())
    tags += tag(b"MDSZ", struct.pack("<Q", len(wrapped)))
    tags += tag(b"OFFT", struct.pack("<3Q", 0, 0, 0))
    tags += tag(b"VERS", struct.pack("<4H", 2, 0, 2, 0)) + b"ENDT"
    function = struct.pack("<I", len(tags) + 4) + tags
    functions = struct.pack("<I", 1) + function
    meta = struct.pack("<I", 4) + b"ENDT"
    public = 88 + len(functions)
    bitcode = public + 16
    header = b"MTLB" + struct.pack("<3H", 0x8001, 2, 2) + bytes(6)
    header += struct.pack("<9Q", bitcode + len(wrapped), 88, len(functions) - 4,
                          public, 8, public + 8, 8, bitcode, len(wrapped))
    return header + functions + meta + meta + wrapped


class Containers(unittest.TestCase):
    def test_raw_and_wrapper(self):
        raw = air.MAGIC + bytes(4)
        self.assertEqual(air.unpack_bitcode(raw)[0], raw)
        wrapped = struct.pack("<5I", 0x0B17C0DE, 0, 20, 8, 0) + raw + bytes(4)
        self.assertEqual(air.unpack_bitcode(wrapped)[0], raw)

    def test_bad_wrappers(self):
        good = struct.pack("<5I", 0x0B17C0DE, 0, 20, 8, 0) + air.MAGIC + bytes(4)
        bad = [b"", b"text", good[:12], good + b"x", good + bytes(16)]
        for offset, value in ((4, 1), (8, 0), (8, 0xFFFFFFFF), (12, 0), (12, 0xFFFFFFFF)):
            changed = bytearray(good); struct.pack_into("<I", changed, offset, value); bad.append(changed)
        for item in bad:
            with self.subTest(size=len(item)), self.assertRaises(air.AirError):
                air.unpack_bitcode(item)

    def test_container_and_entry(self):
        raw, info = air.decode_input(fixture(), "test")
        self.assertTrue(raw.startswith(air.MAGIC))
        self.assertEqual(info["name"], "test")
        self.assertEqual(info["kind"], 2)
        with self.assertRaises(air.AirError):
            air.decode_input(fixture(), "missing")

    def test_all_truncations(self):
        data = fixture()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(air.AirError):
                air.unpack_metallib(data[:end])

    def test_corruption_and_boundaries(self):
        good = fixture()
        cases = []
        for offset, value in ((16, len(good) + 1), (24, 0), (32, 0xFFFFFFFFFFFFFFFF),
                              (40, 88), (48, 0), (56, len(good)), (72, 0), (80, 0xFFFFFFFFFFFFFFFF)):
            changed = bytearray(good); struct.pack_into("<Q", changed, offset, value); cases.append(changed)
        for offset, value in ((88, 0), (88, 1025), (92, 7), (92, 0xFFFFFFFF)):
            changed = bytearray(good); struct.pack_into("<I", changed, offset, value); cases.append(changed)
        changed = bytearray(good); changed[-1] ^= 1; cases.append(changed)
        changed = bytearray(good)
        changed[good.index(b"NAME"):good.index(b"NAME") + 4] = b"EVIL"; cases.append(changed)
        cases.append(fixture(duplicate=True))
        for data in cases:
            with self.subTest(digest=air.sha256(data)), self.assertRaises(air.AirError):
                air.unpack_metallib(data)

    def test_declared_payload_hash(self):
        data = bytearray(fixture()); index = data.index(b"HASH") + 6; data[index] ^= 1
        with self.assertRaisesRegex(air.AirError, "HASH"):
            air.unpack_metallib(data)

    def test_undocumented_section_gap(self):
        original = fixture()
        for field in (56, 72):
            at, = struct.unpack_from("<Q", original, field)
            changed = bytearray(original[:at] + b"X" + original[at:])
            struct.pack_into("<Q", changed, 16, len(changed))
            for offset in (56, 72):
                old, = struct.unpack_from("<Q", original, offset)
                if old >= at: struct.pack_into("<Q", changed, offset, old + 1)
            with self.subTest(field=field), self.assertRaises(air.AirError):
                air.unpack_metallib(changed)

    def test_real_sdl_containers(self):
        import json
        base = ROOT / "tests/fixtures/air"
        manifest = json.loads((base / "provenance.json").read_text())
        for record in manifest["artifacts"]:
            data = (base / record["path"]).read_bytes()
            self.assertEqual(air.sha256(data), record["sha256"])
            raw, info = air.decode_input(data, record["entry"])
            self.assertEqual(info["kind"], record["kind"])
            self.assertTrue(raw.startswith(air.MAGIC))
            self.assertEqual(info["wrapper"]["bitcode_sha256"], record["bitcode_sha256"])

    def test_bounded_file_read(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "input"; p.write_bytes(b"12345")
            with self.assertRaises(air.AirError): air.bounded_read(p, 4)

    def test_cli_output_failure_cannot_pass(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); source = base / "input.bc"; source.write_bytes(air.MAGIC)
            report = base / "report.json"
            args = ["mellow_air.py", str(source), "--llvm-dis", "unused", "--output", str(base / "missing" / "out.ll"), "--report", str(report)]
            with mock.patch("sys.argv", args), mock.patch.object(air, "disassemble", return_value=("IR", {})):
                self.assertEqual(air.main(), 2)
            self.assertEqual(json.loads(report.read_text())["status"], "FAIL")

    def test_cli_rejects_output_report_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "alias")
            args = ["mellow_air.py", "unused", "--llvm-dis", "unused", "--output", path, "--report", path]
            with mock.patch("sys.argv", args), self.assertRaises(SystemExit) as caught:
                air.main()
            self.assertEqual(caught.exception.code, 2)
            self.assertFalse(Path(path).exists())


@unittest.skipIf(os.name == "nt", "POSIX failure executables; Windows container controls still run")
class ToolFailures(unittest.TestCase):
    def check_tool(self, body, expected, timeout=1):
        with tempfile.TemporaryDirectory() as directory:
            tool = Path(directory) / "not-an-LLVM-compiler"
            tool.write_text("#!/usr/bin/python3\n" + body)
            tool.chmod(0o700)
            with self.assertRaisesRegex(air.AirError, expected):
                air.disassemble(air.MAGIC + bytes(4), tool, timeout=timeout)

    def test_failure_exit(self):
        self.check_tool("raise SystemExit(7)\n", "failed")

    def test_missing_output(self):
        self.check_tool("raise SystemExit(0)\n", "failed")

    def test_timeout(self):
        self.check_tool("import time\ntime.sleep(5)\n", "timed out", timeout=0.1)

    def test_log_limit(self):
        self.check_tool("print('x' * 300000)\n", "byte limit")

    def test_ir_limit(self):
        self.check_tool("import pathlib,sys\npathlib.Path(sys.argv[3]).write_text('x' * 9000000)\n", "byte limit")

    def test_input_change(self):
        self.check_tool("import pathlib,sys\npathlib.Path(sys.argv[1]).write_bytes(b'evil')\npathlib.Path(sys.argv[3]).write_text('define void @x() { ret void }')\n", "changed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
