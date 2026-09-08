use nextcore_core::boot_config::{parse_boot_menu, parse_boot_target, BootConfigError as E};
fn entry(name: &str, enabled: bool) -> String {
    format!("<dict><key>Name</key><string>{name}</string><key>Enabled</key><{enabled}/><key>Path</key><string>\\EFI\\TEST\\CHILD.efi</string></dict>")
}
fn document(show: &str, entries: &str) -> Vec<u8> {
    format!("<plist version=\"1.0\"><dict><key>Misc</key><dict>{show}<key>Entries</key><array>{entries}</array></dict></dict></plist>").into_bytes()
}
const SHOW: &str = "<key>Boot</key><dict><key>ShowPicker</key><true/></dict>";
#[test]
fn automatic_boot_ignores_display_names_like_the_original_parser() {
    for show in [
        "",
        "<key>Boot</key><dict><key>ShowPicker</key><false/></dict>",
    ] {
        for name in [
            "<string/>".to_string(),
            "<integer>1</integer>".to_string(),
            format!("<string>{}</string>", "x".repeat(65)),
            "<string>name\nline</string>".to_string(),
        ] {
            let entry = format!("<dict><key>Name</key>{name}<key>Enabled</key><true/><key>Path</key><string>\\EFI\\TEST\\CHILD.efi</string></dict>");
            let input = document(show, &entry);
            let menu = parse_boot_menu(&input).unwrap();
            assert_eq!(menu.entries[0].name, "EFI entry 1");
            assert_eq!(
                Some(menu.entries[0].target.clone()),
                parse_boot_target(&input).unwrap()
            );
        }
    }
}
#[test]
fn explicit_picker_preserves_order_names_targets_and_single_parser_semantics() {
    let b = document(
        SHOW,
        &(entry("macOS", true) + &entry("Disabled", false) + &entry("Windows", true)),
    );
    let menu = parse_boot_menu(&b).unwrap();
    assert!(menu.show_picker);
    assert_eq!(menu.entries.len(), 2);
    assert_eq!(menu.entries[0].name, "macOS");
    assert_eq!(menu.entries[1].name, "Windows");
    assert_eq!(menu.entries[0].target.path, "\\EFI\\TEST\\CHILD.efi");
    assert_eq!(parse_boot_target(&b), Err(E::AmbiguousTarget));
}
#[test]
fn no_opt_in_keeps_single_target_and_rejects_ambiguity() {
    let b = document("", &entry("macOS", true));
    let menu = parse_boot_menu(&b).unwrap();
    assert!(!menu.show_picker);
    assert_eq!(
        Some(menu.entries[0].target.clone()),
        parse_boot_target(&b).unwrap()
    );
    assert_eq!(
        parse_boot_menu(&document("", &(entry("A", true) + &entry("B", true)))),
        Err(E::AmbiguousTarget)
    );
}
#[test]
fn display_names_are_bounded_and_checked_even_for_disabled_entries() {
    for name in [
        "".to_string(),
        " ".to_string(),
        "x\nNEXTCORE: IMAGE_START".to_string(),
        "x".repeat(65),
    ] {
        assert_eq!(
            parse_boot_menu(&document(SHOW, &entry(&name, false))),
            Err(E::InvalidDisplayName)
        );
    }
    assert!(parse_boot_menu(&document(SHOW, &entry(&"x".repeat(64), true))).is_ok());
}
#[test]
fn absent_name_has_stable_fallback_and_empty_list_stays_empty() {
    let e="<dict><key>Enabled</key><true/><key>Path</key><string>\\EFI\\TEST\\CHILD.efi</string></dict>";
    assert_eq!(
        parse_boot_menu(&document(SHOW, e)).unwrap().entries[0].name,
        "EFI entry 1"
    );
    assert!(parse_boot_menu(&document(SHOW, ""))
        .unwrap()
        .entries
        .is_empty());
}
#[test]
fn invalid_picker_type_and_later_unsafe_path_are_rejected() {
    let show = "<key>Boot</key><dict><key>ShowPicker</key><string>true</string></dict>";
    assert_eq!(
        parse_boot_menu(&document(show, &entry("A", true))),
        Err(E::InvalidType)
    );
    let b = document(
        SHOW,
        &(entry("A", true) + &entry("B", true).replace("\\EFI\\TEST\\CHILD.efi", "../bad.efi")),
    );
    assert_eq!(parse_boot_menu(&b), Err(E::InvalidPath));
}
#[test]
fn total_entry_cap_applies_before_disabled_filter() {
    assert_eq!(
        parse_boot_menu(&document(SHOW, &entry("A", false).repeat(65))),
        Err(E::EntryLimit)
    );
}
