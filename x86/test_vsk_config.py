"""VF-SPEC-001 M0 adversarial tests; fixtures cannot authorize hardware boot."""
import copy
import hashlib
import plistlib
import tempfile
import unittest
from pathlib import Path

from x86.vsk_config import (ConfigError, MAX_BYTES, MAX_MIB, CONFORMANCE_PROFILE,
                            parse_xml, normalize_config, load_config)

FIXTURES = Path(__file__).resolve().parent.parent / "sandbox/vsk/config"


def xml(body):
    return ('<?xml version="1.0" encoding="UTF-8"?><plist version="1.0">' + body + '</plist>').encode()


class XMLTests(unittest.TestCase):
    def test_standard_utf8_plist_and_doctype(self):
        raw = (FIXTURES / "example.plist").read_bytes()
        self.assertEqual(parse_xml(raw)["PlatformPolicy"], "AppleIntelOnly")
        self.assertEqual(parse_xml(b"\xef\xbb\xbf" + raw)["SchemaVersion"], 1)
        self.assertEqual(parse_xml(xml('<dict><key>a</key><string>&amp;&lt;한글</string></dict>'))["a"], '&<한글')

    def test_non_utf8_encodings_and_declarations_rejected(self):
        for raw in (xml('<dict/>').decode().encode('utf-16'), b'\xff',
                    xml('<dict/>').replace(b'UTF-8', b'ISO-8859-1'),
                    xml('<dict/>').replace(b'version="1.0" encoding', b'version="1.1" encoding')):
            with self.subTest(raw=raw[:40]), self.assertRaises(ConfigError):
                parse_xml(raw)

    def test_duplicate_keys_rejected_at_every_depth(self):
        for body in ('<dict><key>x</key><true/><key>x</key><false/></dict>',
                     '<dict><key>a</key><dict><key>x</key><integer>1</integer><key>x</key><integer>2</integer></dict></dict>'):
            with self.subTest(body=body), self.assertRaises(ConfigError):
                parse_xml(xml(body))

    def test_entities_and_alternative_dtds_rejected(self):
        declarations = [
            '<!DOCTYPE plist SYSTEM "file:///etc/passwd">',
            '<!DOCTYPE plist SYSTEM "https://example.invalid/remote.dtd">',
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd" []>',
            '<!DOCTYPE plist [<!ENTITY a "expanded">]>',
            '<!DOCTYPE plist [<!ENTITY % ext SYSTEM "file:///etc/passwd">%ext;]>',
            '<!DOCTYPE plist PUBLIC "wrong" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
        ]
        for declaration in declarations:
            with self.subTest(declaration=declaration), self.assertRaises(ConfigError):
                parse_xml((declaration + '<plist version="1.0"><dict/></plist>').encode())

    def test_size_is_bounded_before_xml_work(self):
        with self.assertRaises(ConfigError):
            parse_xml(b' ' * (MAX_BYTES + 1))
        # An exactly maximum-sized document is accepted structurally.
        raw = xml('<dict/>')
        self.assertEqual(parse_xml(raw + b' ' * (MAX_BYTES - len(raw))), {})

    def test_depth_boundary(self):
        # plist + dict + key/string is depth 3; 13 arrays bring it to 16.
        for arrays, allowed in ((13, True), (14, False)):
            raw = xml('<dict><key>a</key>' + '<array>'*arrays + '<string>x</string>' + '</array>'*arrays + '</dict>')
            if allowed:
                parse_xml(raw)
            else:
                with self.assertRaises(ConfigError):
                    parse_xml(raw)

    def test_element_and_comment_node_limit(self):
        # plist + dict = two nodes; comments also count.
        parse_xml(xml('<dict/>' + '<!--x-->'*4094))
        with self.assertRaises(ConfigError):
            parse_xml(xml('<dict/>' + '<!--x-->'*4095))
        with self.assertRaises(ConfigError):
            parse_xml(xml('<dict><key>x</key><array>' + '<true/>'*4093 + '</array></dict>'))

    def test_scalar_types_attributes_and_mixed_content(self):
        bodies = ['<dict bogus="1"/>', '<dict><key>a</key><real>1.0</real></dict>',
                  '<dict>text</dict>', '<dict><key>a</key><string><true/></string></dict>',
                  '<dict><key>a</key><data>AA==</data></dict>', '<dict><key>a</key><true> </true></dict>',
                  '<dict><key>a</key></dict>', '<dict><string>a</string><true/></dict>',
                  '<dict><key>a</key><array><key>x</key></array></dict>', '<dict/><dict/>',
                  '<dict><?run attack?></dict>', '<dict><key>a</key><integer>18446744073709551616</integer></dict>']
        for body in bodies:
            with self.subTest(body=body), self.assertRaises(ConfigError):
                parse_xml(xml(body))

    def test_noncanonical_integer_spellings(self):
        for value in ('', '-1', '+1', '0x10', '01', '1.0', '1e3', 'True'):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                parse_xml(xml(f'<dict><key>a</key><integer>{value}</integer></dict>'))


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.config = parse_xml((FIXTURES / "example.plist").read_bytes())

    def assert_invalid(self, config=None, **kwargs):
        with self.assertRaises(ConfigError):
            normalize_config(self.config if config is None else config, **kwargs)

    def test_normalization_and_hashes_never_authorize_boot(self):
        report = load_config(FIXTURES / "example.plist")
        self.assertFalse(report["boot_authorized"])
        self.assertFalse(report["signature_verified"])
        self.assertFalse(report["hardware_measured"])
        self.assertFalse(report["guest_profile"]["execution_contract_verified"])
        self.assertEqual(report["validation_level"], "UNIT")
        self.assertEqual(report["raw_sha256"], hashlib.sha256((FIXTURES / "example.plist").read_bytes()).hexdigest())
        result = normalize_config(self.config)
        result["CPU"]["VCPUs"] = 2
        self.assertEqual(self.config["CPU"]["VCPUs"], 'auto')

    def test_golden_gate_template_fails_closed(self):
        with self.assertRaises(ConfigError):
            load_config(FIXTURES / "golden-gate.template.plist")

    def test_unknown_and_missing_keys_at_every_configuration_level(self):
        for key in (None, 'CPU', 'Security', 'Memory', 'Graphics', 'Guest', 'Storage'):
            for change in ('unknown', 'missing'):
                cfg = copy.deepcopy(self.config)
                target = cfg if key is None else cfg[key][0] if key == 'Storage' else cfg[key]
                if change == 'unknown':
                    target['AllowNonApple'] = True
                else:
                    target.pop(next(iter(target)))
                with self.subTest(key=key, change=change):
                    self.assert_invalid(cfg)

    def test_security_keys_are_immutable_and_strict_boolean(self):
        for key, expected in self.config['Security'].items():
            for value in (not expected, int(expected), str(expected)):
                cfg = copy.deepcopy(self.config)
                cfg['Security'][key] = value
                with self.subTest(key=key, value=value):
                    self.assert_invalid(cfg)

    def test_platform_and_cpu_baseline_cannot_be_relaxed(self):
        for path, value in [('PlatformPolicy','Any'), ('MinimumISA','sse4.1'), ('Codegen','avx2'),
                            ('HybridScheduling','p-only'), ('SMTPolicy','shared')]:
            cfg = copy.deepcopy(self.config)
            if path == 'PlatformPolicy': cfg[path] = value
            else: cfg['CPU'][path] = value
            self.assert_invalid(cfg)

    def test_cpu_integer_type_range(self):
        for key in ('VCPUs', 'ServiceLogicalCPUs'):
            for value in (True, False, 0, -1, 4097, 1.0, '1'):
                cfg = copy.deepcopy(self.config); cfg['CPU'][key] = value
                with self.subTest(key=key, value=value): self.assert_invalid(cfg)

    def test_memory_budget_and_overflow(self):
        for patch in ({'JITCacheMiB':2049}, {'GuestMiB':0}, {'HostReserveMiB':True},
                      {'GuestMiB':MAX_MIB}, {'HostReserveMiB':MAX_MIB + 1}):
            cfg=copy.deepcopy(self.config); cfg['Memory'].update(patch)
            with self.subTest(patch=patch): self.assert_invalid(cfg)

    def test_storage_exact_binding_and_no_file_backend(self):
        for key, value in [('DeviceSerial',''),('DiskGUID','00000000-0000-0000-0000-000000000000'),
                           ('PartitionGUID','not-a-guid'),('SectorBytes',1024),('ReadOnly',1),
                           ('Backend','image-file')]:
            cfg=copy.deepcopy(self.config);cfg['Storage'][0][key]=value
            with self.subTest(key=key): self.assert_invalid(cfg)
        cfg=copy.deepcopy(self.config);cfg['Storage']=[];self.assert_invalid(cfg)
        cfg=copy.deepcopy(self.config);cfg['Storage'].append(copy.deepcopy(cfg['Storage'][0]));self.assert_invalid(cfg)
        cfg['Storage'][1]['ID']='second';self.assert_invalid(cfg)  # duplicate partition
        cfg['Storage'][1]['PartitionGUID']='33333333-3333-3333-3333-333333333333'
        normalize_config(cfg)  # explicitly selected second partition on same disk
        cfg['Storage'][1]['DeviceSerial']='OTHER';self.assert_invalid(cfg)

    def test_guid_normalization(self):
        self.config['Storage'][0]['DiskGUID']='ABCDEFAB-1111-1111-1111-111111111111'
        self.assertEqual(normalize_config(self.config)['Storage'][0]['DiskGUID'],'abcdefab-1111-1111-1111-111111111111')

    def test_complete_pci_selector_required(self):
        device={'Segment':0,'Bus':1,'Device':0,'Function':0,'VendorID':0x1002,'DeviceID':0x73ff,
                'SubsystemVendorID':0,'SubsystemDeviceID':0,'RevisionID':0}
        self.config['Graphics']['Device']=device
        normalize_config(self.config)
        for key, value in [('Function',8),('VendorID',65535),('RevisionID',True)]:
            cfg=copy.deepcopy(self.config);cfg['Graphics']['Device'][key]=value;self.assert_invalid(cfg)
        device.pop('RevisionID');self.assert_invalid()

    def test_no_headless_or_unvalidated_metal_profile(self):
        self.config['Graphics']['OnUnsupported']='headless';self.assert_invalid()
        self.config['Graphics']['OnUnsupported']='halt'
        self.config['Graphics']['MinimumProfile']='vfgp-base1'
        self.config['Guest']['RequireMetal']=True;self.assert_invalid()

    def test_guest_profile_cannot_be_a_product_label_or_self_approval(self):
        for name in ('GoldenGate', 'macOS-27', '', 'unregistered-profile'):
            cfg=copy.deepcopy(self.config);cfg['Guest']['ProfileID']=name;self.assert_invalid(cfg)
        self.config['Guest']['Verified']=True;self.assert_invalid()

    def test_surrogate_and_control_string_input_rejected(self):
        for value in ('bad\ud800', 'serial\x00value', 'serial\x7fvalue'):
            cfg=copy.deepcopy(self.config);cfg['Storage'][0]['DeviceSerial']=value
            self.assert_invalid(cfg)

    def test_serial_byte_bound_matches_256_byte_c_buffer(self):
        self.config['Storage'][0]['DeviceSerial']='a'*255
        normalize_config(self.config)
        self.config['Storage'][0]['DeviceSerial']='a'*256
        self.assert_invalid()
        self.config['Storage'][0]['DeviceSerial']='한'*85  # 255 UTF-8 bytes
        normalize_config(self.config)
        self.config['Storage'][0]['DeviceSerial']='한'*86
        self.assert_invalid()


class ProfileRegistryTests(unittest.TestCase):
    """All registry entries below are synthetic schema fixtures, not adapters."""
    def setUp(self):
        self.config = parse_xml((FIXTURES / 'example.plist').read_bytes())
        self.config['Guest']['ProfileID'] = 'synthetic-registry-fixture'
        self.entry = {'Kind':'macos','BuildID':'25A354',
            'ImageSHA256':hashlib.sha256(b'synthetic image fixture, not macOS').hexdigest(),
            'ABIVersion':1,'MMUGranule':16384,'TimerFrequencyHz':24000000,
            'BootABI':'iBoot','InterruptController':'AIC','SoCContract':'synthetic-fixture-soc',
            'CPUFeatures':['aarch64','el0','el1'], 'GraphicsAdapter':None}

    def registry(self):
        return {'synthetic-registry-fixture':self.entry}

    def test_registered_declarations_still_do_not_authorize_boot(self):
        normalize_config(self.config, profiles=self.registry())
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'config.plist';path.write_bytes(plistlib.dumps(self.config))
            result=load_config(path,profiles=self.registry())
        self.assertFalse(result['boot_authorized'])
        self.assertFalse(result['guest_profile']['execution_contract_verified'])
        self.assertEqual(len(result['guest_profile']['registry_sha256']),64)

    def test_registry_exact_fields_and_feature_types(self):
        mutations = [('BuildID','GoldenGate'),('ImageSHA256',''),('ABIVersion',True),
                     ('MMUGranule',65536),('TimerFrequencyHz',0),('BootABI','UEFI'),('InterruptController','GIC'),
                     ('CPUFeatures',[]),('CPUFeatures',['aarch64','aarch64']),('CPUFeatures',[True])]
        for key,value in mutations:
            entry=copy.deepcopy(self.entry);entry[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ConfigError):
                normalize_config(self.config,profiles={'synthetic-registry-fixture':entry})
        entry=copy.deepcopy(self.entry);entry['Approved']=True
        with self.assertRaises(ConfigError):
            normalize_config(self.config,profiles={'synthetic-registry-fixture':entry})
        with self.assertRaises(ConfigError):
            normalize_config(self.config,profiles=['synthetic-registry-fixture'])

    def test_metal_requires_full_adapter_declaration_and_halt(self):
        self.config['Guest']['RequireMetal']=True
        self.config['Graphics']['MinimumProfile']='vfgp-base1'
        with self.assertRaises(ConfigError):
            normalize_config(self.config,profiles=self.registry())
        adapter={'ID':'synthetic-adapter-not-executable',
            'SHA256':hashlib.sha256(b'synthetic adapter declaration').hexdigest(),
            'SGPUABI':1,'MetalValidated':True}
        self.entry['GraphicsAdapter']=adapter
        normalize_config(self.config,profiles=self.registry())
        for key,value in [('ID',''),('SHA256','not-a-hash'),('SGPUABI',2),('MetalValidated',1),('MetalValidated',False)]:
            entry=copy.deepcopy(self.entry);entry['GraphicsAdapter'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ConfigError):
                normalize_config(self.config,profiles={'synthetic-registry-fixture':entry})
        self.config['Graphics']['OnUnsupported']='display-only'
        with self.assertRaises(ConfigError):
            normalize_config(self.config,profiles=self.registry())


if __name__ == '__main__':
    unittest.main()
