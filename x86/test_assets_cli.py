import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from x86.cli import main


class AssetCLI(unittest.TestCase):
    def invoke(self, args):
        output=io.StringIO()
        with contextlib.redirect_stdout(output), patch("x86.cli.setup_logging"):
            status=main(args)
        return status,json.loads(output.getvalue())

    def test_imported_integrity_engine_detects_changed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"original.bin";source.write_bytes(b"original authored bytes")
            manifest=Path(tmp)/"manifest.json"
            status,_=self.invoke(["assets","manifest","--output",str(manifest),str(source)])
            self.assertEqual(status,0)
            status,report=self.invoke(["assets","verify",str(manifest)])
            self.assertEqual(status,0);self.assertTrue(report["valid"])
            source.write_bytes(b"changed authored bytes")
            status,report=self.invoke(["assets","verify",str(manifest)])
            self.assertEqual(status,2);self.assertFalse(report["valid"])
            self.assertEqual(source.read_bytes(),b"changed authored bytes")

if __name__=="__main__":unittest.main()
