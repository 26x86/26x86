//! Bounded firmware target selection from public XML plist structure.
//!
//! This is not the host `config::Config` API: `Misc.Entries` boot selection and
//! explicit `Nextcore.Kernel` profiles are interpreted. Other values retain their XML plist type and structure
//! but are not converted to hardware settings. Binary plists are unsupported.
//! Sources: https://www.apple.com/DTDs/PropertyList-1.0.dtd and
//! https://docs.rs/roxmltree/0.21.1/roxmltree/struct.ParsingOptions.html

use alloc::{collections::BTreeSet, format, string::String, vec::Vec};
use core::fmt;
use roxmltree::{Document, Node, ParsingOptions};

pub const MAX_INPUT_BYTES: usize = 1024 * 1024;
pub const MAX_XML_DEPTH: usize = 64;
pub const MAX_XML_NODES: u32 = 16_384;
pub const MAX_ENTRIES: usize = 64;
/// UCS-2 code units, excluding the NUL terminator added by the EFI caller.
/// The public name is retained; paths accept only the UCS-2 subset of UTF-16.
pub const MAX_PATH_UTF16_UNITS: usize = 1024;
/// UTF-16 code units, excluding the NUL terminator added by the EFI caller.
pub const MAX_ARGUMENTS_UTF16_UNITS: usize = 4096;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BootTarget {
    /// Absolute path on the image's own filesystem, normalized to backslashes.
    pub path: String,
    pub arguments: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BootMenuEntry {
    pub name: String,
    pub target: BootTarget,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BootMenu {
    /// Explicit opt-in. Missing/false preserves the single-target behavior.
    pub show_picker: bool,
    pub entries: Vec<BootMenuEntry>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KernelTarget {
    pub path: String,
    pub arguments: String,
    pub profile: KernelProfile,
}

/// The image's CPU type alone does not define the loader entry ABI.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KernelProfile {
    Xnu12377Pstart32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BootConfigError {
    InputTooLarge,
    UnsupportedFormat,
    InvalidUtf8,
    InvalidXml,
    InvalidPlist,
    DuplicateKey,
    InvalidType,
    DepthLimit,
    NodeLimit,
    EntryLimit,
    AmbiguousTarget,
    MissingPath,
    InvalidPath,
    PathTooLong,
    InvalidArguments,
    ArgumentsTooLong,
    MissingKernelTarget,
    UnsupportedKernelProfile,
    InvalidDisplayName,
}

impl fmt::Display for BootConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // Fixed tokens only; untrusted XML/path text never reaches log markers.
        f.write_str(match self {
            Self::InputTooLarge => "INPUT_TOO_LARGE",
            Self::UnsupportedFormat => "UNSUPPORTED_FORMAT",
            Self::InvalidUtf8 => "INVALID_UTF8",
            Self::InvalidXml => "INVALID_XML",
            Self::InvalidPlist => "INVALID_PLIST",
            Self::DuplicateKey => "DUPLICATE_KEY",
            Self::InvalidType => "INVALID_TYPE",
            Self::DepthLimit => "DEPTH_LIMIT",
            Self::NodeLimit => "NODE_LIMIT",
            Self::EntryLimit => "ENTRY_LIMIT",
            Self::AmbiguousTarget => "AMBIGUOUS_TARGET",
            Self::MissingPath => "MISSING_PATH",
            Self::InvalidPath => "INVALID_PATH",
            Self::PathTooLong => "PATH_TOO_LONG",
            Self::InvalidArguments => "INVALID_ARGUMENTS",
            Self::ArgumentsTooLong => "ARGUMENTS_TOO_LONG",
            Self::MissingKernelTarget => "MISSING_KERNEL_TARGET",
            Self::UnsupportedKernelProfile => "UNSUPPORTED_KERNEL_PROFILE",
            Self::InvalidDisplayName => "INVALID_DISPLAY_NAME",
        })
    }
}

impl core::error::Error for BootConfigError {}

type Result<T> = core::result::Result<T, BootConfigError>;

/// Select exactly one enabled EFI entry, or return `None` when none is enabled.
/// The full document is structurally checked even after a target is found.
pub fn parse_boot_target(input: &[u8]) -> Result<Option<BootTarget>> {
    let document = parse_document(input)?;
    select_boot_target(&document)
}

/// Parse a keyboard boot menu separately; the original single-target parser
/// retains its ambiguity rejection even when ShowPicker is true.
pub fn parse_boot_menu(input: &[u8]) -> Result<BootMenu> {
    let document = parse_document(input)?;
    let dictionary = document
        .root_element()
        .children()
        .find(Node::is_element)
        .ok_or(BootConfigError::InvalidPlist)?;
    let mut menu = BootMenu {
        show_picker: false,
        entries: Vec::new(),
    };
    let Some(misc) = dictionary_value(dictionary, "Misc")? else {
        return Ok(menu);
    };
    require_tag(misc, "dict")?;
    if let Some(boot) = dictionary_value(misc, "Boot")? {
        require_tag(boot, "dict")?;
        menu.show_picker = match dictionary_value(boot, "ShowPicker")? {
            None => false,
            Some(v) if v.has_tag_name("true") => true,
            Some(v) if v.has_tag_name("false") => false,
            Some(_) => return Err(BootConfigError::InvalidType),
        };
    }
    let Some(entries) = dictionary_value(misc, "Entries")? else {
        return Ok(menu);
    };
    require_tag(entries, "array")?;
    for (index, entry) in entries.children().filter(Node::is_element).enumerate() {
        if index >= MAX_ENTRIES {
            return Err(BootConfigError::EntryLimit);
        }
        require_tag(entry, "dict")?;
        let enabled = match dictionary_value(entry, "Enabled")? {
            None => false,
            Some(v) if v.has_tag_name("true") => true,
            Some(v) if v.has_tag_name("false") => false,
            Some(_) => return Err(BootConfigError::InvalidType),
        };
        let path = match dictionary_value(entry, "Path")? {
            None => None,
            Some(v) => {
                require_tag(v, "string")?;
                Some(normalize_path(&scalar_text(v)?)?)
            }
        };
        let arguments = match dictionary_value(entry, "Arguments")? {
            None => String::new(),
            Some(v) => {
                require_tag(v, "string")?;
                let text = scalar_text(v)?;
                if text.chars().any(char::is_control) {
                    return Err(BootConfigError::InvalidArguments);
                }
                if text.encode_utf16().count() > MAX_ARGUMENTS_UTF16_UNITS {
                    return Err(BootConfigError::ArgumentsTooLong);
                }
                text
            }
        };
        // Automatic boot historically ignores Name entirely. Display-only
        // validation must not reject a previously accepted single target.
        let name = if !menu.show_picker {
            format!("EFI entry {}", index + 1)
        } else {
            match dictionary_value(entry, "Name")? {
                None => format!("EFI entry {}", index + 1),
                Some(v) => {
                    require_tag(v, "string")?;
                    let text = scalar_text(v)?;
                    if text.trim().is_empty()
                        || text.chars().any(char::is_control)
                        || text.encode_utf16().count() > 64
                    {
                        return Err(BootConfigError::InvalidDisplayName);
                    }
                    text
                }
            }
        };
        if enabled {
            if !menu.show_picker && !menu.entries.is_empty() {
                return Err(BootConfigError::AmbiguousTarget);
            }
            menu.entries.push(BootMenuEntry {
                name,
                target: BootTarget {
                    path: path.ok_or(BootConfigError::MissingPath)?,
                    arguments,
                },
            });
        }
    }
    Ok(menu)
}

fn parse_document(input: &[u8]) -> Result<Document<'_>> {
    if input.len() > MAX_INPUT_BYTES {
        return Err(BootConfigError::InputTooLarge);
    }
    if input.starts_with(b"bplist")
        || input.starts_with(&[0xff, 0xfe])
        || input.starts_with(&[0xfe, 0xff])
    {
        return Err(BootConfigError::UnsupportedFormat);
    }
    let text = core::str::from_utf8(input).map_err(|_| BootConfigError::InvalidUtf8)?;
    // roxmltree reserves capacity using literal '<' and '=' counts before its
    // node limit takes effect. Bound those estimates as well as parsed nodes.
    if text.bytes().filter(|b| *b == b'<').count() > MAX_XML_NODES as usize * 2
        || text.bytes().filter(|b| *b == b'=').count() > MAX_XML_NODES as usize
    {
        return Err(BootConfigError::NodeLimit);
    }
    scan_xml_bounds(text)?;
    let document = Document::parse_with_options(
        text,
        ParsingOptions {
            allow_dtd: true,
            nodes_limit: MAX_XML_NODES,
            entity_resolver: None,
        },
    )
    .map_err(|error| match error {
        roxmltree::Error::NodesLimitReached => BootConfigError::NodeLimit,
        _ => BootConfigError::InvalidXml,
    })?;
    validate_structure(&document)?;
    Ok(document)
}

/// Read the explicitly named kernel profile separately from EFI image targets.
pub fn parse_kernel_target(input: &[u8]) -> Result<KernelTarget> {
    let document = parse_document(input)?;
    let dictionary = document
        .root_element()
        .children()
        .find(Node::is_element)
        .ok_or(BootConfigError::InvalidPlist)?;
    let nextcore =
        dictionary_value(dictionary, "Nextcore")?.ok_or(BootConfigError::MissingKernelTarget)?;
    require_tag(nextcore, "dict")?;
    let kernel =
        dictionary_value(nextcore, "Kernel")?.ok_or(BootConfigError::MissingKernelTarget)?;
    require_tag(kernel, "dict")?;
    let profile =
        dictionary_value(kernel, "Profile")?.ok_or(BootConfigError::UnsupportedKernelProfile)?;
    require_tag(profile, "string")?;
    if scalar_text(profile)? != "xnu-12377-pstart32" {
        return Err(BootConfigError::UnsupportedKernelProfile);
    }
    let path = dictionary_value(kernel, "Path")?.ok_or(BootConfigError::MissingPath)?;
    require_tag(path, "string")?;
    let path = normalize_absolute_path(&scalar_text(path)?)?;
    let arguments = if let Some(value) = dictionary_value(kernel, "Arguments")? {
        require_tag(value, "string")?;
        scalar_text(value)?
    } else {
        String::new()
    };
    if arguments.bytes().any(|byte| !(0x20..=0x7e).contains(&byte)) {
        return Err(BootConfigError::InvalidArguments);
    }
    if arguments.len() > 1023 {
        return Err(BootConfigError::ArgumentsTooLong);
    }
    Ok(KernelTarget {
        path,
        arguments,
        profile: KernelProfile::Xnu12377Pstart32,
    })
}

fn select_boot_target(document: &Document<'_>) -> Result<Option<BootTarget>> {
    let plist = document.root_element();
    let dictionary = plist
        .children()
        .find(Node::is_element)
        .ok_or(BootConfigError::InvalidPlist)?;
    let Some(misc) = dictionary_value(dictionary, "Misc")? else {
        return Ok(None);
    };
    require_tag(misc, "dict")?;
    let Some(entries) = dictionary_value(misc, "Entries")? else {
        return Ok(None);
    };
    require_tag(entries, "array")?;
    let mut selected = None;
    for (index, entry) in entries.children().filter(Node::is_element).enumerate() {
        if index >= MAX_ENTRIES {
            return Err(BootConfigError::EntryLimit);
        }
        require_tag(entry, "dict")?;
        let enabled = match dictionary_value(entry, "Enabled")? {
            None => false,
            Some(value) if value.has_tag_name("true") => true,
            Some(value) if value.has_tag_name("false") => false,
            Some(_) => return Err(BootConfigError::InvalidType),
        };
        let path = match dictionary_value(entry, "Path")? {
            None => None,
            Some(value) => {
                require_tag(value, "string")?;
                Some(normalize_path(&scalar_text(value)?)?)
            }
        };
        let arguments = match dictionary_value(entry, "Arguments")? {
            None => String::new(),
            Some(value) => {
                require_tag(value, "string")?;
                let value = scalar_text(value)?;
                if value.chars().any(char::is_control) {
                    return Err(BootConfigError::InvalidArguments);
                }
                if value.encode_utf16().count() > MAX_ARGUMENTS_UTF16_UNITS {
                    return Err(BootConfigError::ArgumentsTooLong);
                }
                value
            }
        };
        if enabled {
            if selected.is_some() {
                return Err(BootConfigError::AmbiguousTarget);
            }
            selected = Some(BootTarget {
                path: path.ok_or(BootConfigError::MissingPath)?,
                arguments,
            });
        }
    }
    Ok(selected)
}

// roxmltree's tokenizer recursively visits elements. Bound lexical nesting
// BEFORE invoking it. XML names, matching tags, and entity syntax are still
// validated by roxmltree, not by this resource preflight. External DOCTYPE is
// permitted without fetching its URI; internal subsets cannot introduce entities.
fn scan_xml_bounds(text: &str) -> Result<()> {
    let bytes = text.as_bytes();
    let mut position = 0;
    let mut depth = 0usize;
    while position < bytes.len() {
        if bytes[position] != b'<' {
            position += 1;
            continue;
        }
        let tail = &bytes[position..];
        let skip = if tail.starts_with(b"<!--") {
            Some((4, b"-->".as_slice()))
        } else if tail.starts_with(b"<![CDATA[") {
            Some((9, b"]]>".as_slice()))
        } else if tail.starts_with(b"<?") {
            Some((2, b"?>".as_slice()))
        } else {
            None
        };
        if let Some((prefix, ending)) = skip {
            let length = tail[prefix..]
                .windows(ending.len())
                .position(|part| part == ending)
                .ok_or(BootConfigError::InvalidXml)?;
            position += prefix + length + ending.len();
            continue;
        }
        let doctype = tail.starts_with(b"<!DOCTYPE");
        if tail.starts_with(b"<!") && !doctype {
            return Err(BootConfigError::InvalidXml);
        }
        if doctype
            && text[position + 9..]
                .trim_start()
                .split(|ch: char| ch.is_ascii_whitespace() || ch == '>' || ch == '[')
                .next()
                != Some("plist")
        {
            return Err(BootConfigError::InvalidPlist);
        }
        let mut quote = None;
        let mut end = position + 1;
        while end < bytes.len() {
            let byte = bytes[end];
            match (quote, byte) {
                (Some(delimiter), value) if delimiter == value => quote = None,
                (None, b'\'' | b'"') => quote = Some(byte),
                (None, b'[') if doctype => return Err(BootConfigError::UnsupportedFormat),
                (None, b'>') => break,
                (None, b'<') => return Err(BootConfigError::InvalidXml),
                _ => {}
            }
            end += 1;
        }
        if end == bytes.len() {
            return Err(BootConfigError::InvalidXml);
        }
        if !doctype {
            if tail.starts_with(b"</") {
                depth = depth.checked_sub(1).ok_or(BootConfigError::InvalidXml)?;
            } else {
                if depth >= MAX_XML_DEPTH {
                    return Err(BootConfigError::DepthLimit);
                }
                if bytes[end - 1] != b'/' {
                    depth += 1;
                }
            }
        }
        position = end + 1;
    }
    Ok(())
}

fn require_tag(node: Node<'_, '_>, tag: &str) -> Result<()> {
    if node.has_tag_name(tag) {
        Ok(())
    } else {
        Err(BootConfigError::InvalidType)
    }
}

fn scalar_text(node: Node<'_, '_>) -> Result<String> {
    let mut value = String::new();
    for child in node.children() {
        if child.is_text() {
            value.push_str(child.text().unwrap_or(""));
        } else if !child.is_comment() {
            return Err(BootConfigError::InvalidPlist);
        }
    }
    Ok(value)
}

fn no_mixed_text(node: Node<'_, '_>) -> Result<()> {
    if node.children().any(|child| {
        child.is_text()
            && !child
                .text()
                .unwrap_or("")
                .chars()
                .all(|ch| matches!(ch, ' ' | '\t' | '\r' | '\n'))
    }) {
        return Err(BootConfigError::InvalidPlist);
    }
    Ok(())
}

fn validate_structure(document: &Document<'_>) -> Result<()> {
    let root = document.root_element();
    if !root.has_tag_name("plist")
        || root.attribute("version") != Some("1.0")
        || root.attributes().len() != 1
    {
        return Err(BootConfigError::InvalidPlist);
    }
    for node in document.descendants() {
        if node.is_pi() {
            return Err(BootConfigError::InvalidPlist);
        }
        if !node.is_element() {
            continue;
        }
        if node
            .ancestors()
            .filter(Node::is_element)
            .take(MAX_XML_DEPTH + 1)
            .count()
            > MAX_XML_DEPTH
        {
            return Err(BootConfigError::DepthLimit);
        }
        if node.tag_name().namespace().is_some() || (node != root && node.attributes().len() != 0) {
            return Err(BootConfigError::InvalidPlist);
        }
        match node.tag_name().name() {
            "plist" => {
                no_mixed_text(node)?;
                let mut children = node.children().filter(Node::is_element);
                if node != root
                    || !children
                        .next()
                        .is_some_and(|child| child.has_tag_name("dict"))
                    || children.next().is_some()
                {
                    return Err(BootConfigError::InvalidPlist);
                }
            }
            "dict" => {
                no_mixed_text(node)?;
                let mut keys = BTreeSet::new();
                let mut children = node.children().filter(Node::is_element);
                while let Some(key) = children.next() {
                    require_tag(key, "key")?;
                    if !keys.insert(scalar_text(key)?) {
                        return Err(BootConfigError::DuplicateKey);
                    }
                    let value = children.next().ok_or(BootConfigError::InvalidPlist)?;
                    if value.has_tag_name("key") {
                        return Err(BootConfigError::InvalidPlist);
                    }
                }
            }
            "array" => {
                no_mixed_text(node)?;
                if node.children().any(|child| child.has_tag_name("key")) {
                    return Err(BootConfigError::InvalidPlist);
                }
            }
            "key" | "string" | "integer" | "real" | "date" | "data" => {
                scalar_text(node)?;
            }
            "true" | "false" => {
                if !scalar_text(node)?.is_empty() {
                    return Err(BootConfigError::InvalidPlist);
                }
            }
            _ => return Err(BootConfigError::InvalidType),
        }
    }
    Ok(())
}

// Dictionary pair structure and key uniqueness have already been validated.
fn dictionary_value<'a, 'input>(
    dict: Node<'a, 'input>,
    wanted: &str,
) -> Result<Option<Node<'a, 'input>>> {
    let mut children = dict.children().filter(Node::is_element);
    while let Some(key) = children.next() {
        let value = children.next().ok_or(BootConfigError::InvalidPlist)?;
        if scalar_text(key)? == wanted {
            return Ok(Some(value));
        }
    }
    Ok(None)
}

fn normalize_path(path: &str) -> Result<String> {
    let normalized = normalize_absolute_path(path)?;
    if !normalized
        .rsplit_once('.')
        .is_some_and(|(_, extension)| extension.eq_ignore_ascii_case("efi"))
    {
        return Err(BootConfigError::InvalidPath);
    }
    Ok(normalized)
}

fn normalize_absolute_path(path: &str) -> Result<String> {
    if path.encode_utf16().count() > MAX_PATH_UTF16_UNITS {
        return Err(BootConfigError::PathTooLong);
    }
    if path.chars().any(|ch| {
        u32::from(ch) > u32::from(u16::MAX)
            || ch.is_control()
            || matches!(ch, ':' | '*' | '?' | '"' | '<' | '>' | '|')
    }) {
        return Err(BootConfigError::InvalidPath);
    }
    let normalized = path.replace('/', "\\");
    if !normalized.starts_with('\\') || normalized.starts_with("\\\\") {
        return Err(BootConfigError::InvalidPath);
    }
    for component in normalized[1..].split('\\') {
        if component.is_empty()
            || matches!(component, "." | "..")
            || component.ends_with(['.', ' '])
        {
            return Err(BootConfigError::InvalidPath);
        }
    }
    Ok(normalized)
}
