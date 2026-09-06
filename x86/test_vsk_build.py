"""Build receipt guards, with fake tools; not compilation or hardware proof."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class VskBuildReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        original = Path(__file__).resolve().parent.parent / 'sandbox/vsk/build.py'
        (self.root / 'build.py').write_bytes(original.read_bytes())
        spec = importlib.util.spec_from_file_location('vsk_build_receipt_fixture', self.root / 'build.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        for directory in ('src', 'tests', 'include'):
            (self.root / directory).mkdir()
        for name in self.module.REQUIRED_SOURCES:
            (self.root / 'src' / name).write_text('synthetic source fixture')
        for name in self.module.REQUIRED_TESTS:
            (self.root / 'tests' / name).write_text('synthetic test fixture')
        for name in self.module.CRYPTO_SOURCES:
            path = self.root / 'crypto' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic crypto fixture')
        (self.root / 'crypto/UPSTREAM.json').write_text('{"files":{}}')

    def failed_receipt(self):
        report = json.loads((self.root / 'build/report.json').read_text())
        self.assertIs(report['passed'], False)
        self.assertIs(report['boot_authorized'], False)

    def test_missing_required_suite_stops_before_tool_execution(self):
        (self.root / 'tests/test_policy.c').unlink()
        with patch.object(self.module, 'run', side_effect=AssertionError('must not execute tools')):
            with self.assertRaisesRegex(RuntimeError, 'test suite is missing'):
                self.module.main()
        self.failed_receipt()

    def test_mutated_source_never_gets_a_passing_receipt(self):
        mutated = False
        def tool(args):
            nonlocal mutated
            if str(args[0]) == 'clang' and not mutated:
                (self.root / 'src/vf_policy.c').write_text('changed during tool execution')
                mutated = True
            if Path(args[0]).name.startswith('test_'):
                return '{"passed":true}'
            return ''
        with patch.object(self.module, 'run', side_effect=tool):
            with self.assertRaisesRegex(RuntimeError, 'inputs changed'):
                self.module.main()
        self.failed_receipt()

    def test_implicit_fpu_state_instruction_is_rejected(self):
        def tool(args):
            if str(args[0]) == 'objdump':
                return '   0:\tfninit\n'
            return ''
        with patch.object(self.module, 'run', side_effect=tool):
            with self.assertRaisesRegex(RuntimeError, 'Implicit SIMD/FPU'):
                self.module.main()
        self.failed_receipt()


if __name__ == '__main__':
    unittest.main()
