use nextcore_hal::smbios_translator::*;
use nextcore_hal::device_tree::*;
use nextcore_hal::pci_translator::*;
use nextcore_hal::acpi_translator::*;

#[test]
fn test_smbios_translate() {
    let real = SmbiosTable {
        manufacturer: "Dell Inc.".to_string(),
        product_name: "XPS 15".to_string(),
        serial_number: "XYZABC".to_string(),
        uuid: "12345678-ABCD".to_string(),
        bios_vendor: "Dell".to_string(),
        bios_version: "2.1.0".to_string(),
        system_version: "1.0".to_string(),
        family: "XPS".to_string(),
    };

    let mac = SmbiosTranslator::translate(&real, &MacProfile::macpro_6_1());
    assert_eq!(mac.manufacturer, "Apple Inc.");
    assert_eq!(mac.product_name, "MacPro6,1");
    assert_eq!(mac.board_id, "Mac-F60DEB81FF30ACF6");
    assert_eq!(mac.serial_number, "XYZABC");
    assert_eq!(mac.model_identifier, "MacPro6,1");
}

#[test]
fn test_smbios_serial_unknown() {
    let real = SmbiosTable {
        manufacturer: "ASUSTeK".to_string(),
        product_name: "PRIME Z390-A".to_string(),
        serial_number: "".to_string(),
        uuid: "".to_string(),
        bios_vendor: "AMI".to_string(),
        bios_version: "1.0.0".to_string(),
        system_version: "1.0".to_string(),
        family: "Z390".to_string(),
    };

    let mac = SmbiosTranslator::translate(&real, &MacProfile::macbookpro_16_1());
    assert!(!mac.serial_number.is_empty());
    assert!(!mac.uuid.is_empty());
}

#[test]
fn test_serial_deterministic() {
    let real = SmbiosTable {
        manufacturer: "".to_string(),
        product_name: "".to_string(),
        serial_number: "".to_string(),
        uuid: "".to_string(),
        bios_vendor: "".to_string(),
        bios_version: "".to_string(),
        system_version: "".to_string(),
        family: "".to_string(),
    };

    let mac1 = SmbiosTranslator::translate(&real, &MacProfile::imac_19_1());
    let mac2 = SmbiosTranslator::translate(&real, &MacProfile::imac_19_1());
    assert_eq!(mac1.serial_number, mac2.serial_number);
}

#[test]
fn test_build_device_tree() {
    let tree = build_mac_device_tree(4, 16 * 1024 * 1024 * 1024, &[]);

    assert_eq!(tree.name, "/");
    let cpus = &tree.children[0];
    assert_eq!(cpus.name, "cpus");
    assert_eq!(cpus.children.len(), 4);
    assert_eq!(cpus.children[0].name, "cpu@0");

    let memory = &tree.children[1];
    assert_eq!(memory.name, "memory");
    assert_eq!(memory.device_type, "memory");

    let chosen = &tree.children[2];
    assert_eq!(chosen.name, "chosen");
    assert!(chosen.properties.contains_key("boot-args"));
}

#[test]
fn test_device_tree_translate() {
    let mut props = std::collections::HashMap::new();
    props.insert("device_type".to_string(), b"pci".to_vec());
    let node = DeviceTreeNode {
        name: "pci@0".to_string(),
        device_type: "".to_string(),
        properties: props,
        children: Vec::new(),
    };

    let result = DeviceTreeTranslator::translate(&node);
    assert_eq!(result.name, "pci@0");
    assert_eq!(result.device_type, "pci");
}

#[test]
fn test_pci_rx580() {
    let dev = PciDevice {
        vendor_id: 0x1002,
        device_id: 0x67DF,
        class_code: 0x03,
        subclass: 0x00,
        prog_if: 0x00,
        revision: 0x00,
        subsystem_vendor_id: 0x0000,
        subsystem_device_id: 0x0000,
    };

    let mac = PciTranslator::translate_device(&dev);
    assert!(mac.recognized);
    assert_eq!(mac.brand_name, "Radeon RX 570/580");
    assert_eq!(mac.inner.subsystem_vendor_id, 0x1002);
}

#[test]
fn test_pci_unknown() {
    assert!(!PciTranslator::is_mac_recognizable(0x1234, 0x5678));
}

#[test]
fn test_acpi_patch() {
    let dsdt = vec![0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    let patches = vec![AcpiPatchDef {
        offset: 2,
        length: 2,
        data: vec![0xAA, 0xBB],
    }];
    let result = AcpiTranslator::patch_dsdt(&dsdt, &patches).unwrap();
    assert_eq!(result, vec![0, 1, 0xAA, 0xBB, 4, 5, 6, 7, 8, 9]);
}

#[test]
fn test_acpi_patch_bad_len() {
    let dsdt = vec![0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    let patches = vec![AcpiPatchDef {
        offset: 9,
        length: 5,
        data: vec![0xAA],
    }];
    let result = AcpiTranslator::patch_dsdt(&dsdt, &patches);
    assert!(result.is_err());
}
