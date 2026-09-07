use nextcore_core::boot_config::{parse_kernel_target, BootConfigError, KernelProfile};

fn config(profile: &str, path: &str, args: &str) -> Vec<u8> {
    format!("<plist version=\"1.0\"><dict><key>Nextcore</key><dict><key>Kernel</key><dict><key>Profile</key><string>{profile}</string><key>Path</key><string>{path}</string><key>Arguments</key><string>{args}</string></dict></dict></dict></plist>").into_bytes()
}

#[test]
fn explicit_profile_and_independent_kernel_path_are_required() {
    let target = parse_kernel_target(&config(
        "xnu-12377-pstart32",
        "/EFI/Nextcore/kernel",
        "-v keepsyms=1",
    ))
    .unwrap();
    assert_eq!(target.path, "\\EFI\\Nextcore\\kernel");
    assert_eq!(target.arguments, "-v keepsyms=1");
    assert_eq!(target.profile, KernelProfile::Xnu12377Pstart32);
    assert_eq!(
        parse_kernel_target(&config("xnu64", "/kernel", "")),
        Err(BootConfigError::UnsupportedKernelProfile)
    );
    for path in ["kernel", "/a/../kernel", "/kernel🚀", "/a//kernel"] {
        assert_eq!(
            parse_kernel_target(&config("xnu-12377-pstart32", path, "")),
            Err(BootConfigError::InvalidPath)
        );
    }
}

#[test]
fn kernel_c_string_and_whole_document_validation_precede_loading() {
    assert!(
        parse_kernel_target(&config("xnu-12377-pstart32", "/kernel", &"x".repeat(1023))).is_ok()
    );
    assert_eq!(
        parse_kernel_target(&config("xnu-12377-pstart32", "/kernel", &"x".repeat(1024))),
        Err(BootConfigError::ArgumentsTooLong)
    );
    for value in ["한글", "-v\n", "&#0;"] {
        assert!(parse_kernel_target(&config("xnu-12377-pstart32", "/kernel", value)).is_err());
    }
    let original = config("xnu-12377-pstart32", "/kernel", "");
    for end in 0..original.len() {
        assert!(parse_kernel_target(&original[..end]).is_err());
    }
    let duplicated = String::from_utf8(original).unwrap().replace(
        "<key>Profile</key>",
        "<key>Path</key><string>/second</string><key>Profile</key>",
    );
    assert_eq!(
        parse_kernel_target(duplicated.as_bytes()),
        Err(BootConfigError::DuplicateKey)
    );
}
