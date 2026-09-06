"""Ephemeral Ed25519 keys and authored ELF fixtures; no production trust key."""
import copy
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from x86 import vsk_bundle as bundle

ROOT = Path(__file__).resolve().parent.parent


def elf_fixture(code=b'\xc3'):
    """An authored static x86_64 RET ELF; never used as a real VSK kernel."""
    raw=bytearray(4096+len(code));raw[:16]=b'\x7fELF\x02\x01\x01'+bytes(9)
    struct.pack_into('<HHIQQQIHHHHHH',raw,16,2,62,1,0x100000,64,0,0,64,56,1,0,0,0)
    struct.pack_into('<IIQQQQQQ',raw,64,1,5,4096,0x100000,0x100000,len(code),len(code),4096)
    raw[4096:]=code
    return bytes(raw)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config=self.root/'input.plist';self.config.write_bytes((ROOT/'sandbox/vsk/config/example.plist').read_bytes())
        self.core=self.root/'input-core.elf';self.core.write_bytes(elf_fixture())
        self.cell=self.root/'input-cell.elf';self.cell.write_bytes(elf_fixture(b'\x90\xc3'))
        self.key=Ed25519PrivateKey.generate()
        self.public=self.key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        self.output=self.root/'bundle'

    def create(self,**overrides):
        args=dict(private_key=self.key,target_major=26,release_epoch=7)
        args.update(overrides)
        return bundle.create_bundle(self.config,self.core,{1:self.cell},self.output,**args)

    def verify(self,**overrides):
        args=dict(trusted_public_key=self.public,expected_target=26,minimum_release_epoch=7)
        args.update(overrides)
        return bundle.verify_bundle(self.output,**args)

    def test_real_signature_and_fixed_layout_without_private_key(self):
        before={p:p.read_bytes() for p in (self.config,self.core,self.cell)}
        report=self.create()
        self.assertTrue(report['signature_verified']);self.assertFalse(report['boot_authorized'])
        manifest=(self.output/'manifest.vfb').read_bytes()
        self.assertEqual(len(manifest),64+3*128)
        self.assertEqual(manifest[:16],b'VSK-BUNDLE-v1\0\0\0')
        self.assertEqual(struct.unpack_from('<Q',manifest,40)[0],7)
        self.assertEqual(len((self.output/'manifest.sig').read_bytes()),64)
        private=self.key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())
        for path in self.output.iterdir(): self.assertNotIn(private,path.read_bytes())
        self.assertNotIn(self.public,manifest)
        for path,raw in before.items():self.assertEqual(path.read_bytes(),raw)
        self.verify()

    def test_wrong_key_target_and_rollback_floor(self):
        self.create()
        other=Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        for override in ({'trusted_public_key':other},{'expected_target':27},{'minimum_release_epoch':8}):
            with self.subTest(override=list(override)),self.assertRaises(bundle.BundleError):self.verify(**override)

    def test_modified_payload_and_signature_fail(self):
        self.create();path=self.output/'cell-1.elf';raw=path.read_bytes();path.write_bytes(raw+b'x')
        with self.assertRaises(bundle.BundleError):self.verify()
        path.write_bytes(raw)
        signature=self.output/'manifest.sig';raw=bytearray(signature.read_bytes());raw[4]^=1;signature.write_bytes(raw)
        with self.assertRaises(bundle.BundleError):self.verify()

    def test_signed_invalid_reserved_or_order_is_still_rejected(self):
        self.create();original=(self.output/'manifest.vfb').read_bytes()
        for mutation in ('reserved','entry-reserved','order','size','missing-core'):
            raw=bytearray(original)
            if mutation=='reserved':raw[52]=1
            elif mutation=='entry-reserved':raw[64+116]=1
            elif mutation=='order':raw[64:192],raw[192:320]=raw[192:320],raw[64:192]
            elif mutation=='size':struct.pack_into('<Q',raw,64+8,1048577)
            else:struct.pack_into('<II',raw,192,3,2)
            (self.output/'manifest.vfb').write_bytes(raw)
            (self.output/'manifest.sig').write_bytes(self.key.sign(bytes(raw)))
            with self.subTest(mutation=mutation),self.assertRaises(bundle.BundleError):self.verify()

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir();sentinel=self.output/'sentinel';sentinel.write_bytes(b'preserve')
        with self.assertRaises(bundle.BundleError):self.create()
        self.assertEqual(sentinel.read_bytes(),b'preserve')

    def test_source_mutation_during_staging_revokes_signature(self):
        original=bundle._write_new
        def write(path,raw):
            original(path,raw)
            if path.name=='config.plist':self.core.write_bytes(elf_fixture(b'\x90\x90\xc3'))
        with patch.object(bundle,'_write_new',side_effect=write):
            with self.assertRaises(bundle.BundleError):self.create()
        self.assertFalse((self.output/'manifest.sig').exists())

    def test_duplicate_hardlinked_inputs_rejected(self):
        self.cell.unlink();os.link(self.core,self.cell)
        with self.assertRaises(bundle.BundleError):self.create()

    def test_symlink_inputs_rejected(self):
        link=self.root/'link.elf'
        try:link.symlink_to(self.core)
        except OSError as error:self.skipTest('Host cannot create symlink: '+str(error))
        self.core=link
        with self.assertRaises(bundle.BundleError):self.create()

    def test_reparse_input_attribute_rejected(self):
        from types import SimpleNamespace
        original=Path.lstat
        def observed(path):
            result=original(path)
            if path==self.core:return SimpleNamespace(st_mode=result.st_mode,st_file_attributes=0x400)
            return result
        with patch.object(Path,'lstat',observed),self.assertRaises(bundle.BundleError):self.create()

    def test_traversal_invalid_instance_and_no_services_rejected(self):
        with self.assertRaises(bundle.BundleError):bundle._check_path(self.root/'sub/../input-core.elf')
        for services in ({},{True:self.cell},{0:self.cell},{65:self.cell},{'1':self.cell}):
            with self.subTest(services=list(services)),self.assertRaises(bundle.BundleError):
                bundle.create_bundle(self.config,self.core,services,self.output,private_key=self.key,target_major=26,release_epoch=7)

    def test_elf_load_permissions_bounds_and_entry(self):
        original=elf_fixture()
        for mutation in ('wx','outside-file','outside-entry','overflow','dynamic','wrong-machine'):
            raw=bytearray(original)
            if mutation=='wx':struct.pack_into('<I',raw,68,7)
            elif mutation=='outside-file':struct.pack_into('<Q',raw,72,len(raw)+1)
            elif mutation=='outside-entry':struct.pack_into('<Q',raw,24,0x200000)
            elif mutation=='overflow':struct.pack_into('<Q',raw,80,(1<<64)-1)
            elif mutation=='dynamic':struct.pack_into('<I',raw,64,2)
            else:struct.pack_into('<H',raw,18,183)
            with self.subTest(mutation=mutation),self.assertRaises(bundle.BundleError):bundle.validate_elf(bytes(raw))

    def test_elf_native_header_and_page_contract(self):
        for mutation in ('osabi','padding','flags','ph-alignment','ph-limit','unknown-ph',
                         'no-read','noncanonical','page-overlap','sparse-image','reverse-order','page-misaligned'):
            raw=bytearray(elf_fixture(b'\x90\xc3'))
            if mutation=='osabi':raw[7]=3
            elif mutation=='padding':raw[15]=1
            elif mutation=='flags':struct.pack_into('<I',raw,48,1)
            elif mutation=='ph-alignment':struct.pack_into('<Q',raw,32,65)
            elif mutation=='ph-limit':struct.pack_into('<H',raw,56,65)
            elif mutation=='unknown-ph':struct.pack_into('<I',raw,64,4)
            elif mutation=='no-read':struct.pack_into('<I',raw,68,1)
            elif mutation=='noncanonical':struct.pack_into('<Q',raw,24,1<<48)
            elif mutation=='page-misaligned':struct.pack_into('<Q',raw,80,0x100001);struct.pack_into('<Q',raw,112,1)
            else:
                struct.pack_into('<H',raw,56,2)
                # The second byte is file backed but on a distinct virtual range.
                va={'page-overlap':0x100001,'sparse-image':0x4100001,'reverse-order':0xff001}[mutation]
                struct.pack_into('<IIQQQQQQ',raw,120,1,4,4097,va,va,1,1,1)
            with self.subTest(mutation=mutation),self.assertRaises(bundle.BundleError):bundle.validate_elf(bytes(raw))

    def test_elf_sections_are_bounded_and_relocation_free(self):
        raw=bytearray(elf_fixture());struct.pack_into('<Q',raw,40,128)
        struct.pack_into('<HHH',raw,58,64,1,0)
        bundle.validate_elf(bytes(raw))  # A bounded NULL section is permitted.
        for mutation in ('relocation','dynamic-symbol','tls','alignment','bounds','header-overlap','orphan'):
            bad=bytearray(raw)
            if mutation=='relocation':struct.pack_into('<I',bad,132,4)
            elif mutation=='dynamic-symbol':struct.pack_into('<I',bad,132,11)
            elif mutation=='tls':struct.pack_into('<Q',bad,136,0x400)
            elif mutation=='alignment':struct.pack_into('<Q',bad,176,3)
            elif mutation=='bounds':struct.pack_into('<Q',bad,152,len(raw)+1)
            elif mutation=='header-overlap':struct.pack_into('<Q',bad,40,64)
            else:struct.pack_into('<Q',bad,40,0)
            with self.subTest(mutation=mutation),self.assertRaises(bundle.BundleError):bundle.validate_elf(bytes(bad))

    def test_template_config_cannot_be_signed_as_ready(self):
        self.config.write_bytes((ROOT/'sandbox/vsk/config/golden-gate.template.plist').read_bytes())
        with self.assertRaises(ValueError):self.create()
        self.assertFalse(self.output.exists())

    def test_actual_verify_cli_uses_only_external_public_key(self):
        self.create();public=self.root/'trusted.pub';public.write_bytes(self.public)
        result=subprocess.run([sys.executable,str(ROOT/'Tools/vsk-bundle.py'),'verify','--bundle',str(self.output),
            '--trusted-public-key',str(public),'--target-major','26','--minimum-release-epoch','7'],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout.decode('utf-8'))
        self.assertTrue(report['signature_verified']);self.assertFalse(report['boot_authorized'])


if __name__=='__main__':unittest.main()
