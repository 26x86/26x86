use std::collections::HashMap;

use nextcore_core::config::{DevicePropertiesConfig, DevicePropValue};
use nextcore_core::device_props::{
    apply_properties, decode_properties, encode_properties, PropertyData,
};

fn props_map(data: &[(&str, Vec<u8>)]) -> HashMap<String, PropertyData> {
    data.iter()
        .map(|(k, v)| (k.to_string(), PropertyData { bytes: v.clone() }))
        .collect()
}

#[test]
fn test_encode_decode_roundtrip() {
    let props = props_map(&[
        ("AAPL,ig-platform-id", vec![0x0A, 0x00, 0x00, 0x0D]),
        ("device-id", vec![0x00, 0x12, 0x00, 0x00]),
        ("framebuffer-patch-enable", vec![1]),
    ]);

    let encoded = encode_properties(&props);
    let decoded = decode_properties(&encoded).expect("decode should succeed");

    assert_eq!(decoded.len(), props.len());
    for (key, want) in &props {
        let got = decoded.get(key).expect("key should be present after roundtrip");
        assert_eq!(got.bytes, want.bytes, "bytes mismatch for key {key}");
    }
}

#[test]
fn test_apply_from_config() {
    let mut add: HashMap<String, HashMap<String, DevicePropValue>> = HashMap::new();
    let mut gpu_props = HashMap::new();
    gpu_props.insert(
        "AAPL,ig-platform-id".into(),
        DevicePropValue::Data(vec![0x0A, 0x00, 0x00, 0x0D]),
    );
    gpu_props.insert("framebuffer-patch-enable".into(), DevicePropValue::Bool(true));
    add.insert("PciRoot(0)/Pci(0x2,0x0)".into(), gpu_props);

    let config = DevicePropertiesConfig { add, delete: HashMap::new() };
    let entries = apply_properties(&config);

    assert_eq!(entries.len(), 1, "one device path should be applied");
    assert_eq!(entries[0].path, "PciRoot(0)/Pci(0x2,0x0)");

    let ig = entries[0]
        .properties
        .get("AAPL,ig-platform-id")
        .expect("ig-platform-id present");
    assert_eq!(ig.bytes, vec![0x0A, 0x00, 0x00, 0x0D]);

    let patch = entries[0]
        .properties
        .get("framebuffer-patch-enable")
        .expect("bool property present");
    assert_eq!(patch.bytes, vec![1]);
}

#[test]
fn test_property_data_types() {
    let int = PropertyData::from_config_value(&DevicePropValue::Integer(0x12345678));
    assert_eq!(int.bytes, 0x12345678i64.to_le_bytes().to_vec());

    let string =
        PropertyData::from_config_value(&DevicePropValue::String("TestString".into()));
    assert_eq!(string.bytes, b"TestString".to_vec());

    let bool_true = PropertyData::from_config_value(&DevicePropValue::Bool(true));
    assert_eq!(bool_true.bytes, vec![1]);

    let bool_false = PropertyData::from_config_value(&DevicePropValue::Bool(false));
    assert_eq!(bool_false.bytes, vec![0]);

    let data = PropertyData::from_config_value(&DevicePropValue::Data(vec![0xAA, 0xBB, 0xCC]));
    assert_eq!(data.bytes, vec![0xAA, 0xBB, 0xCC]);
}

#[test]
fn test_apply_empty_config() {
    let config = DevicePropertiesConfig { add: HashMap::new(), delete: HashMap::new() };
    let entries = apply_properties(&config);
    assert!(entries.is_empty(), "empty config yields no entries");
}
