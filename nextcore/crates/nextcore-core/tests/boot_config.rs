use nextcore_core::boot_config::{
    parse_boot_target, BootConfigError as E, MAX_ARGUMENTS_UTF16_UNITS, MAX_ENTRIES,
    MAX_INPUT_BYTES, MAX_PATH_UTF16_UNITS, MAX_XML_DEPTH, MAX_XML_NODES,
};

fn plist(body: &str) -> String {
    format!("<plist version=\"1.0\"><dict>{body}</dict></plist>")
}
fn entries(body: &str) -> String {
    plist(&format!(
        "<key>Misc</key><dict><key>Entries</key><array>{body}</array></dict>"
    ))
}
fn entry(path: &str, arguments: &str) -> String {
    format!("<dict><key>Enabled</key><true/><key>Path</key><string>{path}</string><key>Arguments</key><string>{arguments}</string></dict>")
}

#[test]
fn selects_one_target_and_decodes_xml_text_without_changing_arguments() {
    let xml = entries(&entry(
        "/EFI/OS/Loader.EFI",
        "-v label=&quot;한글 😀&quot; x=1&amp;y=2",
    ));
    let target = parse_boot_target(xml.as_bytes()).unwrap().unwrap();
    assert_eq!(target.path, "\\EFI\\OS\\Loader.EFI");
    assert_eq!(target.arguments, "-v label=\"한글 😀\" x=1&y=2");
    let fragments = entries("<dict><key>En<!--split-->abled</key><true/><key>Path</key><string>/EFI/<![CDATA[child]]>.efi</string></dict>");
    assert_eq!(
        parse_boot_target(fragments.as_bytes())
            .unwrap()
            .unwrap()
            .path,
        "\\EFI\\child.efi"
    );
}

#[test]
fn missing_or_disabled_selection_returns_none_and_arguments_default_empty() {
    for xml in [
        plist(""),
        plist("<key>Misc</key><dict/>"),
        entries(""),
        entries("<dict/>"),
        entries("<dict><key>Enabled</key><false/></dict>"),
    ] {
        assert_eq!(parse_boot_target(xml.as_bytes()), Ok(None));
    }
    let xml = entries(
        "<dict><key>Enabled</key><true/><key>Path</key><string>\\child.efi</string></dict>",
    );
    assert!(parse_boot_target(xml.as_bytes())
        .unwrap()
        .unwrap()
        .arguments
        .is_empty());
    assert_eq!(
        parse_boot_target(entries("<dict><key>Enabled</key><true/></dict>").as_bytes()),
        Err(E::MissingPath)
    );
}

#[test]
fn multiple_active_entries_are_ambiguous_and_entry_count_is_bounded() {
    assert_eq!(
        parse_boot_target(entries(&(entry("/one.efi", "") + &entry("/two.efi", ""))).as_bytes()),
        Err(E::AmbiguousTarget)
    );
    assert_eq!(
        parse_boot_target(entries(&"<dict/>".repeat(MAX_ENTRIES)).as_bytes()),
        Ok(None)
    );
    assert_eq!(
        parse_boot_target(entries(&"<dict/>".repeat(MAX_ENTRIES + 1)).as_bytes()),
        Err(E::EntryLimit)
    );
}

#[test]
fn root_version_structure_and_known_types_are_required() {
    for xml in [
        "<dict/>",
        "<plist><dict/></plist>",
        "<plist version=\"2.0\"><dict/></plist>",
        "<plist version=\"1.0\"><array/></plist>",
        "<plist version=\"1.0\"><dict/><dict/></plist>",
        "<plist xmlns=\"urn:other\" version=\"1.0\"><dict/></plist>",
        "<plist version=\"1.0\" other=\"x\"><dict/></plist>",
    ] {
        assert!(parse_boot_target(xml.as_bytes()).is_err(), "accepted {xml}");
    }
    for body in [
        "<key>Misc</key><string/>",
        "<key>Misc</key><dict><key>Entries</key><dict/></dict>",
        "<key>broken</key>",
        "<string>key required</string><true/>",
        "<key>X</key><unsupported/>",
    ] {
        assert!(parse_boot_target(plist(body).as_bytes()).is_err());
    }
    for body in [
        "<string/>",
        "<dict><key>Enabled</key><string>true</string></dict>",
        "<dict><key>Path</key><integer>5</integer></dict>",
        "<dict><key>Arguments</key><array/></dict>",
    ] {
        assert_eq!(
            parse_boot_target(entries(body).as_bytes()),
            Err(E::InvalidType)
        );
    }
}

#[test]
fn duplicate_keys_and_mixed_text_are_rejected_in_the_entire_document() {
    for body in [
        "<key>Misc</key><dict/><key>Misc</key><dict/>",
        "<key>ignored</key><dict><key>X</key><true/><key>X</key><false/></dict>",
        "<key>Misc</key><dict/><key>Mi<!--split-->sc</key><dict/>",
    ] {
        assert_eq!(
            parse_boot_target(plist(body).as_bytes()),
            Err(E::DuplicateKey)
        );
    }
    for body in [
        "unexpected<key>A</key><true/>",
        "<key>A</key><array>unexpected</array>",
        "<key>A</key><string>before<true/>after</string>",
        "<key>A</key><true>text</true>",
        "<key>A</key><array><key>illegal</key></array>",
        "<key>A</key><dict><key>key</key><key>value</key></dict>",
    ] {
        assert!(parse_boot_target(plist(body).as_bytes()).is_err());
    }
    let valid = entries(&entry("/child.efi", ""));
    let malformed_tail = valid.replace("</plist>", "<dict/></plist>");
    assert!(parse_boot_target(malformed_tail.as_bytes()).is_err());
}

#[test]
fn path_validation_rejects_escape_aliases_non_efi_and_control_characters() {
    for path in [
        "child.efi",
        "../child.efi",
        "/EFI/../child.efi",
        "/EFI/./child.efi",
        "C:/child.efi",
        "fs0:\\child.efi",
        "//server/child.efi",
        "\\\\server\\child.efi",
        "/EFI//child.efi",
        "/child.efi/",
        "/child.txt",
        "/child.efi:stream",
        "/EFI /child.efi",
        "/EFI./child.efi",
        "/chil?d.efi",
        "/child*.efi",
        "/child&#x0;.efi",
        "/child&#x9;.efi",
        "/child&#xA;.efi",
        "",
    ] {
        assert!(
            parse_boot_target(entries(&entry(path, "")).as_bytes()).is_err(),
            "accepted path {path}"
        );
    }
    assert_eq!(
        parse_boot_target(entries(&entry("\\EFI/한글/Ω.eFi", "")).as_bytes())
            .unwrap()
            .unwrap()
            .path,
        "\\EFI\\한글\\Ω.eFi"
    );
}

#[test]
fn path_rejects_non_ucs2_characters_but_arguments_keep_utf16() {
    for path in ["/EFI/😀.efi", "/EFI/&#x1F600;.efi", "/EFI/&#x10000;.efi"] {
        assert_eq!(
            parse_boot_target(entries(&entry(path, "")).as_bytes()),
            Err(E::InvalidPath),
            "accepted a path that EFI CString16 cannot represent: {path}"
        );
    }
    assert_eq!(
        parse_boot_target(entries(&entry("/EFI/한글.efi", "label=😀")).as_bytes())
            .unwrap()
            .unwrap()
            .arguments,
        "label=😀"
    );
}

#[test]
fn utf16_limits_count_surrogate_pairs_and_allow_exact_boundary() {
    let path = format!("/{}.efi", "a".repeat(MAX_PATH_UTF16_UNITS - 5));
    assert!(parse_boot_target(entries(&entry(&path, "")).as_bytes()).is_ok());
    assert_eq!(
        parse_boot_target(entries(&entry(&("/a".to_owned() + &path[1..]), "")).as_bytes()),
        Err(E::PathTooLong)
    );
    let arguments = "😀".repeat(MAX_ARGUMENTS_UTF16_UNITS / 2);
    assert!(parse_boot_target(entries(&entry("/child.efi", &arguments)).as_bytes()).is_ok());
    assert_eq!(
        parse_boot_target(entries(&entry("/child.efi", &(arguments + "a"))).as_bytes()),
        Err(E::ArgumentsTooLong)
    );
    for arguments in ["&#x9;", "&#xA;", "&#xD;", "&#x7f;", "&#x85;"] {
        assert_eq!(
            parse_boot_target(entries(&entry("/child.efi", arguments)).as_bytes()),
            Err(E::InvalidArguments)
        );
    }
}

#[test]
fn input_depth_and_node_limits_are_enforced_before_unbounded_work() {
    assert_eq!(
        parse_boot_target(&vec![b'x'; MAX_INPUT_BYTES + 1]),
        Err(E::InputTooLarge)
    );
    let nested = format!(
        "{}{}",
        "<array>".repeat(MAX_XML_DEPTH + 1000),
        "</array>".repeat(MAX_XML_DEPTH + 1000)
    );
    assert_eq!(
        parse_boot_target(plist(&format!("<key>A</key>{nested}")).as_bytes()),
        Err(E::DepthLimit)
    );
    let nodes = plist(&format!(
        "<key>A</key><array>{}</array>",
        "<true/>".repeat(MAX_XML_NODES as usize)
    ));
    assert_eq!(parse_boot_target(nodes.as_bytes()), Err(E::NodeLimit));
    let reserve_attack = plist(&format!(
        "<key>A</key><string>{}</string>",
        "=".repeat(MAX_XML_NODES as usize + 1)
    ));
    assert_eq!(
        parse_boot_target(reserve_attack.as_bytes()),
        Err(E::NodeLimit)
    );
    let exact = format!(
        "{}{}",
        "<array>".repeat(MAX_XML_DEPTH - 2),
        "</array>".repeat(MAX_XML_DEPTH - 2)
    );
    assert_eq!(
        parse_boot_target(plist(&format!("<key>A</key>{exact}")).as_bytes()),
        Ok(None)
    );
}

#[test]
fn external_plist_doctype_works_without_resolving_or_accepting_entities() {
    assert_eq!(parse_boot_target(include_bytes!("sample.plist")), Ok(None));
    assert_eq!(
        parse_boot_target(format!("<!DOCTYPE plist>{}", plist("")).as_bytes()),
        Ok(None)
    );
    let internal = format!("<!DOCTYPE plist [<!ENTITY injected 'true'>]>{}", plist(""));
    assert_eq!(
        parse_boot_target(internal.as_bytes()),
        Err(E::UnsupportedFormat)
    );
    let external = format!(
        "<!DOCTYPE plist SYSTEM 'file:///no-file-is-read'>{}",
        plist("<key>X</key><string>&injected;</string>")
    );
    assert_eq!(parse_boot_target(external.as_bytes()), Err(E::InvalidXml));
    let comments = plist(
        "<!-- <array> <!DOCTYPE ignored [ --> <key>X</key><string><![CDATA[<array>]]></string>",
    );
    assert_eq!(parse_boot_target(comments.as_bytes()), Ok(None));
}

#[test]
fn binary_non_utf8_and_all_truncated_document_prefixes_are_rejected() {
    assert_eq!(
        parse_boot_target(b"bplist00anything"),
        Err(E::UnsupportedFormat)
    );
    assert_eq!(
        parse_boot_target(&[0xff, 0xfe, 0, 0]),
        Err(E::UnsupportedFormat)
    );
    assert_eq!(
        parse_boot_target(&[0xf0, 0x28, 0x8c, 0x28]),
        Err(E::InvalidUtf8)
    );
    let xml = entries(&entry("/child.efi", "-v"));
    for end in 0..xml.len() {
        assert!(
            parse_boot_target(&xml.as_bytes()[..end]).is_err(),
            "accepted prefix {end}"
        );
    }
    assert!(parse_boot_target(xml.as_bytes()).is_ok());
}

#[test]
fn disabled_fields_are_still_checked_and_error_tokens_cannot_inject_markers() {
    let bad = entries(
        "<dict><key>Enabled</key><false/><key>Path</key><string>../child.efi</string></dict>",
    );
    assert_eq!(parse_boot_target(bad.as_bytes()), Err(E::InvalidPath));
    for error in [
        E::InputTooLarge,
        E::UnsupportedFormat,
        E::InvalidUtf8,
        E::InvalidXml,
        E::InvalidPlist,
        E::DuplicateKey,
        E::InvalidType,
        E::DepthLimit,
        E::NodeLimit,
        E::EntryLimit,
        E::AmbiguousTarget,
        E::MissingPath,
        E::InvalidPath,
        E::PathTooLong,
        E::InvalidArguments,
        E::ArgumentsTooLong,
    ] {
        assert!(error
            .to_string()
            .bytes()
            .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_'));
    }
}
