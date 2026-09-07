use nextcore_core::config::Config;

fn load_sample() -> Config {
    let plist_bytes = include_bytes!("sample.plist");
    Config::from_xml_bytes(plist_bytes).expect("failed to parse sample.plist")
}

#[test]
fn test_config_from_xml_bytes() {
    let plist_bytes = include_bytes!("sample.plist");
    let config = Config::from_xml_bytes(plist_bytes);
    assert!(config.is_ok(), "Config::from_xml_bytes failed: {:?}", config.err());
}

#[test]
fn test_config_system_name() {
    let config = load_sample();
    assert_eq!(config.platform_info.generic.system_name, "MacBookPro16,1");
}

#[test]
fn test_config_mlb() {
    let config = load_sample();
    assert_eq!(config.platform_info.generic.mlb, "C02X12345678");
}

#[test]
fn test_config_boot_args() {
    let config = load_sample();
    let boot_args = config
        .nvram
        .add
        .get("7C436110-ABAB-ABAB-ABAB-ABABABABABAB")
        .and_then(|m| m.get("boot-args"));
    match boot_args {
        Some(nextcore_core::config::NvramValue::String(s)) => {
            assert_eq!(s, "keepsyms=1");
        }
        other => panic!("expected boot-args string, got {:?}", other),
    }
}

#[test]
fn test_config_validate() {
    let config = load_sample();
    assert!(config.validate().is_ok(), "Config::validate() failed: {:?}", config.validate().err());
}
