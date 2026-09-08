extern crate alloc;
pub mod boot_config;
#[cfg(test)] mod review_tests {
use super::boot_config::{parse_boot_menu,parse_boot_target,BootConfigError as E};
fn config(entries: &str) -> String {format!("<plist version=\"1.0\"><dict><key>Misc</key><dict><key>Entries</key><array>{entries}</array></dict></dict></plist>")}
fn entry(field:&str, enabled:bool)->String {format!("<dict><key>Enabled</key><{enabled}/><key>Path</key><string>/EFI/Boot.efi</string>{field}</dict>")}
fn field(value:&str)->String {format!("<key>ApfsVolume</key><string>{value}</string>")}
#[test] fn unicode_edge_whitespace_is_rejected() {
for label in ["\u{a0}name","name\u{a0}","\u{3000}name","name\u{202f}"] {
let text=config(&entry(&field(label),false));
assert_eq!(parse_boot_target(text.as_bytes()),Err(E::InvalidApfsVolume));
assert_eq!(parse_boot_menu(text.as_bytes()),Err(E::InvalidApfsVolume));
}}
#[test] fn decoded_controls_and_separators_are_rejected() {
for label in ["a&#47;b","a&#92;b","a&#x7f;b","a&#x9f;b","a&#13;b","a&#9;b"] {
let text=config(&entry(&field(label),true));
assert_eq!(parse_boot_target(text.as_bytes()),Err(E::InvalidApfsVolume));
assert_eq!(parse_boot_menu(text.as_bytes()),Err(E::InvalidApfsVolume));
}}
#[test] fn cdata_comment_and_numeric_entity_preserve_label() {
let text=config(&entry(&field("A<!--ignored--><![CDATA[<&]]>&#x1f600;"),true));
let target=parse_boot_target(text.as_bytes()).unwrap().unwrap();
assert_eq!(target.apfs_volume.as_deref(),Some("A<&😀"));
assert_eq!(parse_boot_menu(text.as_bytes()).unwrap().entries[0].target,target);
}
#[test] fn disabled_selectors_do_not_leak_into_enabled_target() {
for entries in [entry(&field("ignored"),false)+&entry("",true),entry("",true)+&entry(&field("ignored"),false)] {
let text=config(&entries);
let target=parse_boot_target(text.as_bytes()).unwrap().unwrap();
assert_eq!(target.apfs_volume,None);
assert_eq!(parse_boot_menu(text.as_bytes()).unwrap().entries[0].target,target);
}}
#[test] fn all_disabled_has_no_target_and_valid_maximum_is_exact() {
let label="😀".repeat(127)+"x";
let text=config(&entry(&field(&label),false));
assert_eq!(parse_boot_target(text.as_bytes()).unwrap(),None);
assert!(parse_boot_menu(text.as_bytes()).unwrap().entries.is_empty());
let text=config(&entry(&field(&label),true));
assert_eq!(parse_boot_target(text.as_bytes()).unwrap().unwrap().apfs_volume,Some(label));
}
}
