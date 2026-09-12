"""Authored malformed-PE and archive-integrity controls; real build is separate."""
import json
from pathlib import Path
import plistlib
import struct
import tempfile
import unittest
import zipfile
from package_prebuilt_efi import pe_validate, verify_archive, sha


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "prebuiltefi.zip"
        self.pe = bytearray(1024)
        self.pe[:2] = b"MZ"
        struct.pack_into("<I", self.pe, 60, 64)
        self.pe[64:68] = b"PE\0\0"
        struct.pack_into("<HH", self.pe, 68, 0x8664, 1)
        struct.pack_into("<H", self.pe, 84, 240)
        struct.pack_into("<H", self.pe, 88, 0x20b)
        struct.pack_into("<I", self.pe, 104, 0x1000)
        struct.pack_into("<H", self.pe, 156, 10)
        struct.pack_into("<IIII", self.pe, 336, 512, 0x1000, 512, 512)
        struct.pack_into("<I", self.pe, 364, 0x20000000)
        self.files = {"EFI/BOOT/BOOTX64.EFI": bytes(self.pe), "diagnostics/NXARMJIT.efi": bytes(self.pe),
                      "EFI/OC/config.plist": plistlib.dumps({"Misc": {"Boot": {"ShowPicker": True}, "Entries": []}}),
                      "README.txt": b"NOT_READY"}
        self.manifest = dict(source_commit="a"*40, normal_startup="NOT_READY", physical_desktop_verified=False,
                             files={n:dict(size=len(d),sha256=sha(d)) for n,d in self.files.items()})

    def archive(self):
        with zipfile.ZipFile(self.path,"w") as out:
            for n,d in self.files.items(): out.writestr(n,d)
            out.writestr("manifest.json",json.dumps(self.manifest))

    def test_valid_authored_structure(self):
        pe_validate(self.pe)
        self.archive()
        verify_archive(self.path,"a"*40)

    def test_wrong_architecture_subsystem_entry_and_truncation(self):
        for offset,fmt,value in [(68,"<H",0xaa64),(156,"<H",3),(104,"<I",0x9000),(348,"<I",1000)]:
            with self.subTest(offset=offset):
                data=bytearray(self.pe);struct.pack_into(fmt,data,offset,value)
                with self.assertRaises(ValueError):pe_validate(data)
        with self.assertRaises(ValueError):pe_validate(self.pe[:400])

    def test_altered_file_rejected(self):
        self.files["README.txt"]+=b"tamper";self.archive()
        with self.assertRaises(ValueError):verify_archive(self.path,"a"*40)

    def test_missing_diagnostic_rejected(self):
        del self.files["diagnostics/NXARMJIT.efi"];self.archive()
        with self.assertRaises(ValueError):verify_archive(self.path,"a"*40)

    def test_extra_path_and_wrong_pin_rejected(self):
        self.archive()
        with self.assertRaises(ValueError):verify_archive(self.path,"b"*40)
        with zipfile.ZipFile(self.path,"a") as out:out.writestr("../extra",b"x")
        with self.assertRaises(ValueError):verify_archive(self.path,"a"*40)

    def test_false_readiness_rejected(self):
        self.manifest["physical_desktop_verified"]=True;self.archive()
        with self.assertRaises(ValueError):verify_archive(self.path,"a"*40)


if __name__ == "__main__":unittest.main()
