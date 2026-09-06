import unittest
from copy import deepcopy
from x86.sandbox_config import default_config, validate

class ConfigTests(unittest.TestCase):
    def test_default_disabled_is_valid_without_invented_identity(self):
        value=default_config(27)
        self.assertTrue(validate(value)["ok"])
        self.assertFalse(validate(value)["enabled"])
        self.assertEqual(set(value["SandboxSMBIOS"].values()), {""})
        self.assertEqual(value["Venfire"]["BootPicker"]["DelaySeconds"], 2)
        self.assertTrue(validate(value)["boot_picker"]["recovery_entry_enabled"])
        value["AppleSiliconSandbox"]["Enabled"]=True
        self.assertFalse(validate(value)["ok"])

    def test_gic_and_non_iboot_are_rejected(self):
        for key,value in (("InterruptController","GIC"),("BootProtocol","UEFI"),("TargetMajor",True)):
            data=default_config();data["AppleSiliconSandbox"][key]=value
            self.assertFalse(validate(data)["ok"])

    def test_boot_picker_contract_is_strict(self):
        data = default_config(27)
        data["Venfire"]["BootPicker"]["DelaySeconds"] = 1
        result = validate(data)
        self.assertFalse(result["ok"])
        self.assertTrue(any("VF_BOOT_PICKER_DELAY_INVALID" in item for item in result["errors"]))
        data = default_config(27)
        data["Venfire"]["BootPicker"]["AltKey"] = "F12"
        result = validate(data)
        self.assertFalse(result["ok"])
        self.assertTrue(any("VF_BOOT_PICKER_HOTKEY_INVALID" in item for item in result["errors"]))

    def test_efi_paths_cannot_escape_volume(self):
        for path in ("", "\\", "\\EFI\\..\\escape.efi", "C:\\engine.efi", "\\EFI/engine.efi", "\\EFI\\한글.efi", "\\"+"a"*191):
            data=default_config();data["AppleSiliconSandbox"]["EnginePath"]=path
            with self.subTest(path=path):self.assertFalse(validate(data)["ok"])

    def test_data_types_and_limits(self):
        for key,value in (("CPUCount",65),("CPUCount",True),("MemorySizeMiB",4095),("MemorySizeMiB",1048577)):
            data=default_config();data["AppleSiliconSandbox"]["Hardware"][key]=value
            self.assertFalse(validate(data)["ok"])
        data=default_config();props={"virtual-device":{"key":b"\0\1", "flag":True,"id":42}}
        data["AppleSiliconSandbox"]["Hardware"]["DeviceProperties"]=props
        self.assertTrue(validate(data)["ok"])
        props["virtual-device"]["id"]=-1
        self.assertFalse(validate(data)["ok"])

if __name__=="__main__":unittest.main()
