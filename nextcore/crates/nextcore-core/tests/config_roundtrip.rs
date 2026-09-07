use nextcore_core::config::Config;

fn load_sample() -> Config {
    let plist_bytes = include_bytes!("sample.plist");
    Config::from_xml_bytes(plist_bytes).expect("failed to parse sample.plist")
}

#[test]
fn test_config_xml_roundtrip() {
    let original = load_sample();
    let xml_bytes = original.to_xml_bytes().expect("to_xml_bytes failed");
    let restored = Config::from_xml_bytes(&xml_bytes).expect("from_xml_bytes failed");
    assert_eq!(original, restored);
}

#[test]
fn test_config_binary_roundtrip() {
    let original = load_sample();
    let bin_bytes = original.to_bytes().expect("to_bytes failed");
    let restored = Config::from_bytes(&bin_bytes).expect("from_bytes failed");
    assert_eq!(original, restored);
}
