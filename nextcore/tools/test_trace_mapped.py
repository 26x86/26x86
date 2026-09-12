"""Mapped selector and receipt rejection; these tests are not firmware proof."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import trace_deep_arm_jit_ovmf as trace
import test_trace_long as long

BASE=0x40000000
VIRTUAL=0xfffffe0000000000
SIZE=0x4000000
ROWS=[
    'NXARMJIT: TRACE_MAPPED_DIAGNOSTIC_BUILD profile=mapped-normal-nc-v1',
    'NXARMJIT: TRACE_MAPPED_DIAGNOSTIC_SELECTED profile=mapped-normal-nc-v1',
    'NXARMJIT: TRACE_ENTER entry=0xfffffe0002004400 x0=0 x1=0x42010000 x2=0 x3=0 budget=64',
    'NXARMJIT: TRACE_MAPPINGS_READY granule=16384 profile=3 physical_base=0x40000000 virtual_base=0xfffffe0000000000 memory_size=67108864 table_base=0x44000000 table_bytes=131072 ttbr0=0x44000000 ttbr1=0x44004000 tcr=0x540118011 sctlr=0x30d00801 entry=0xfffffe0002004400',
    'NXARMJIT: TRACE_MEMORY_PROVIDER abi=2 mode=mapped-normal-nc-v1',
]

class MappedTests(unittest.TestCase):
    def valid(self,rows):
        return trace.parse_mapped_profile(rows,True,BASE,VIRTUAL,SIZE)['validated']

    def test_explicit_acknowledgements_and_unique_rows(self):
        self.assertTrue(self.valid(ROWS))
        self.assertFalse(trace.parse_mapped_profile(ROWS,False,BASE,VIRTUAL,SIZE)['validated'])
        for index in range(len(ROWS)):
            self.assertFalse(self.valid(ROWS[:index]+ROWS[index+1:]))
            self.assertFalse(self.valid(ROWS+[ROWS[index]]))
        self.assertFalse(self.valid([ROWS[1],ROWS[0],*ROWS[2:]]))

    def test_mapping_controls_ranges_and_entry_must_match(self):
        for old,new in [('granule=16384','granule=4096'),('profile=3','profile=1'),
            ('sctlr=0x30d00801','sctlr=0x30d00803'),('tcr=0x540118011','tcr=0x540108010'),
            ('ttbr1=0x44004000','ttbr1=0x44000000'),('table_base=0x44000000','table_base=0x43ffc000'),
            ('table_bytes=131072','table_bytes=131073'),('table_bytes=131072','table_bytes=0'),
            ('table_bytes=131072','table_bytes=4194304'),('memory_size=67108864','memory_size=33554432'),
            ('entry=0xfffffe0002004400','entry=0xfffffe0002004404')]:
            rows=list(ROWS);rows[3]=rows[3].replace(old,new)
            self.assertFalse(self.valid(rows),(old,new))
        rows=list(ROWS);rows[2]=rows[2].replace('x1=0x42010000','x1=0x50000000')
        self.assertFalse(self.valid(rows))

    def test_named_platform_is_required_before_any_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            args=long.LongDiagnosticTests().arguments(folder,['--mapped-diagnostic'])
            with patch.object(trace.sys,'argv',args),patch.object(trace,'digest') as digest,\
                patch.object(trace.subprocess,'Popen') as process,contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:trace.main()
                self.assertEqual(error.exception.code,2)
                digest.assert_not_called();process.assert_not_called()
            self.assertFalse((folder/'result').exists())

if __name__=='__main__':unittest.main()
