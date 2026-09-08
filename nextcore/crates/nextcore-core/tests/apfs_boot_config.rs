use nextcore_core::boot_config::{
    parse_boot_menu, parse_boot_target, BootConfigError as E, MAX_APFS_VOLUME_UTF16_UNITS,
};

fn entry(volume: &str, enabled: bool) -> String {
    format!("<dict><key>Enabled</key><{enabled}/><key>Path</key><string>/EFI/Loader.efi</string>{volume}</dict>")
}

fn document(entries: &str, picker: bool) -> Vec<u8> {
    format!("<plist version=\"1.0\"><dict><key>Misc</key><dict><key>Boot</key><dict><key>ShowPicker</key><{picker}/></dict><key>Entries</key><array>{entries}</array></dict></dict></plist>").into_bytes()
}

fn field(label: &str) -> String {
    format!("<key>ApfsVolume</key><string>{label}</string>")
}

#[test]
fn absence_preserves_own_volume_in_both_parsers() {
    let input = document(&entry("", true), false);
    let target = parse_boot_target(&input).unwrap().unwrap();
    assert_eq!(target.apfs_volume, None);
    assert_eq!(target.path, "\\EFI\\Loader.efi");
    assert_eq!(parse_boot_menu(&input).unwrap().entries[0].target, target);
}

#[test]
fn labels_preserve_case_unicode_and_xml_decoding_exactly() {
    for (encoded, decoded) in [
        ("NextCore", "NextCore"),
        ("nextcore", "nextcore"),
        ("개발 😀 &amp; OS", "개발 😀 & OS"),
        ("e\u{301}", "e\u{301}"),
        ("é", "é"),
    ] {
        let input = document(&entry(&field(encoded), true), false);
        let target = parse_boot_target(&input).unwrap().unwrap();
        assert_eq!(target.apfs_volume.as_deref(), Some(decoded));
        assert_eq!(parse_boot_menu(&input).unwrap().entries[0].target, target);
    }
}

#[test]
fn invalid_label_is_rejected_even_on_disabled_or_later_entries() {
    for label in [
        "",
        " ",
        " leading",
        "trailing ",
        "x\ny",
        "x\ty",
        "x\u{85}y",
        "a/b",
        "a\\b",
    ] {
        for enabled in [true, false] {
            let input = document(&(entry("", true) + &entry(&field(label), enabled)), true);
            assert_eq!(parse_boot_target(&input), Err(E::InvalidApfsVolume));
            assert_eq!(parse_boot_menu(&input), Err(E::InvalidApfsVolume));
        }
    }
}

#[test]
fn utf16_limit_counts_supplementary_characters_as_two_units() {
    for label in [
        "x".repeat(MAX_APFS_VOLUME_UTF16_UNITS),
        "😀".repeat(127) + "x",
    ] {
        let input = document(&entry(&field(&label), true), false);
        assert!(parse_boot_target(&input).is_ok());
        assert!(parse_boot_menu(&input).is_ok());
    }
    for label in [
        "x".repeat(MAX_APFS_VOLUME_UTF16_UNITS + 1),
        "😀".repeat(128),
    ] {
        let input = document(&entry(&field(&label), true), false);
        assert_eq!(parse_boot_target(&input), Err(E::InvalidApfsVolume));
        assert_eq!(parse_boot_menu(&input), Err(E::InvalidApfsVolume));
    }
}

#[test]
fn wrong_types_and_duplicate_selectors_are_not_ignored() {
    for value in ["<false/>", "<integer>1</integer>", "<array/>", "<dict/>"] {
        let input = document(
            &entry(&format!("<key>ApfsVolume</key>{value}"), false),
            false,
        );
        assert_eq!(parse_boot_target(&input), Err(E::InvalidType));
        assert_eq!(parse_boot_menu(&input), Err(E::InvalidType));
    }
    let input = document(&entry(&(field("One") + &field("Two")), true), false);
    assert_eq!(parse_boot_target(&input), Err(E::DuplicateKey));
    assert_eq!(parse_boot_menu(&input), Err(E::DuplicateKey));
}

#[test]
fn picker_keeps_per_entry_selectors_and_single_target_ambiguity() {
    let input = document(
        &(entry(&field("One"), true) + &entry(&field("Two"), true)),
        true,
    );
    let menu = parse_boot_menu(&input).unwrap();
    assert_eq!(menu.entries[0].target.apfs_volume.as_deref(), Some("One"));
    assert_eq!(menu.entries[1].target.apfs_volume.as_deref(), Some("Two"));
    assert_eq!(parse_boot_target(&input), Err(E::AmbiguousTarget));
}

#[test]
fn selector_does_not_relax_existing_path_validation() {
    let input = document(&entry(&field("NextCore"), true), false);
    let bad = String::from_utf8(input)
        .unwrap()
        .replace("/EFI/Loader.efi", "../Loader.efi");
    assert_eq!(parse_boot_target(bad.as_bytes()), Err(E::InvalidPath));
    assert_eq!(parse_boot_menu(bad.as_bytes()), Err(E::InvalidPath));
}

#[test]
fn unicode_edge_whitespace_and_decoded_forbidden_characters_are_rejected() {
    for label in [
        "\u{a0}name",
        "name\u{3000}",
        "name\u{202f}",
        "a&#47;b",
        "a&#92;b",
        "a&#x7f;b",
        "a&#x9f;b",
        "a&#13;b",
        "a&#9;b",
    ] {
        let input = document(&entry(&field(label), false), false);
        assert_eq!(parse_boot_target(&input), Err(E::InvalidApfsVolume));
        assert_eq!(parse_boot_menu(&input), Err(E::InvalidApfsVolume));
    }
}

#[test]
fn disabled_labels_do_not_leak_into_a_later_or_earlier_selected_target() {
    for entries in [
        entry(&field("Ignored"), false) + &entry("", true),
        entry("", true) + &entry(&field("Ignored"), false),
    ] {
        let input = document(&entries, false);
        let target = parse_boot_target(&input).unwrap().unwrap();
        assert_eq!(target.apfs_volume, None);
        assert_eq!(parse_boot_menu(&input).unwrap().entries[0].target, target);
    }
}
