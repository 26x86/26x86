//! Bounded, allocation-only parsing for the BP24-B observation protocol.
extern crate alloc;
use alloc::{format, string::String, vec::Vec};

pub const MAX_PATH: usize = 2048;
pub const MAX_NODES: usize = 64;
pub const MAX_RECORD: usize = 4096;
pub const MAX_NAME: usize = 255;
pub const MAX_ENTRIES: usize = 128;
pub const MAX_TOTAL_ENTRIES: usize = 512;
pub const MAX_METADATA: usize = 1024 * 1024;

#[derive(Debug, PartialEq, Eq)]
pub enum Invalid {
    Path,
    Size,
    Name,
    Attributes,
    Geometry,
    Limit,
}

/// Validate a single instance, retaining exact bytes and node boundaries.
pub fn path_body(path: &[u8]) -> Result<&[u8], Invalid> {
    if path.len() > MAX_PATH {
        return Err(Invalid::Path);
    }
    let mut offset = 0;
    let mut nodes = 0;
    while offset + 4 <= path.len() {
        let length = u16::from_le_bytes([path[offset + 2], path[offset + 3]]) as usize;
        if length < 4 || length > path.len() - offset || nodes >= MAX_NODES {
            return Err(Invalid::Path);
        }
        nodes += 1;
        if path[offset] == 0x7f {
            return if path[offset + 1] == 0xff
                && length == 4
                && offset + 4 == path.len()
                && offset > 0
            {
                Ok(&path[..offset])
            } else {
                Err(Invalid::Path)
            };
        }
        offset += length;
    }
    Err(Invalid::Path)
}

pub fn descendant(parent: &[u8], child: &[u8]) -> Result<bool, Invalid> {
    let parent = path_body(parent)?;
    let child = path_body(child)?;
    Ok(child.len() > parent.len() && child.starts_with(parent))
}

fn le64(bytes: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(bytes[offset..offset + 8].try_into().unwrap())
}

fn sized(bytes: &[u8], name_offset: usize) -> Result<&[u8], Invalid> {
    if bytes.len() < name_offset + 2 || bytes.len() > MAX_RECORD {
        return Err(Invalid::Size);
    }
    let size = usize::try_from(le64(bytes, 0)).map_err(|_| Invalid::Size)?;
    if size < name_offset + 2 || size > bytes.len() {
        return Err(Invalid::Size);
    }
    Ok(&bytes[..size])
}

/// An injective printable-ASCII representation of a bounded UTF-16 string.
fn name(bytes: &[u8], component: bool) -> Result<String, Invalid> {
    let mut units = Vec::new();
    let mut ended = false;
    for pair in bytes.chunks_exact(2) {
        let unit = u16::from_le_bytes([pair[0], pair[1]]);
        if unit == 0 {
            ended = true;
            break;
        }
        if units.len() == MAX_NAME
            || (component && (unit < 0x20 || matches!(unit, 0x7f | 0x2f | 0x5c)))
        {
            return Err(Invalid::Name);
        }
        units.push(unit);
    }
    if !ended
        || (component && units.is_empty())
        || core::char::decode_utf16(units.iter().copied()).any(|c| c.is_err())
    {
        return Err(Invalid::Name);
    }
    let mut escaped = String::new();
    for unit in units {
        match unit {
            0x22 => escaped.push_str("\\\""),
            0x5c => escaped.push_str("\\\\"),
            0x20..=0x7e => escaped.push(char::from_u32(unit as u32).unwrap()),
            _ => escaped.push_str(&format!("\\u{unit:04x}")),
        }
    }
    Ok(escaped)
}

#[derive(Debug)]
pub struct Entry {
    pub name: String,
    pub file_size: u64,
    pub physical_size: u64,
    pub attributes: u64,
    pub directory: bool,
    pub dot: bool,
}

pub fn entry(bytes: &[u8], root: bool) -> Result<Entry, Invalid> {
    let bytes = sized(bytes, 80)?;
    let attributes = le64(bytes, 72);
    if attributes & !0x37 != 0 || (root && attributes & 0x10 == 0) {
        return Err(Invalid::Attributes);
    }
    let name = name(&bytes[80..], !root)?;
    if root && !name.is_empty() {
        return Err(Invalid::Name);
    }
    let dot = matches!(name.as_str(), "." | "..");
    Ok(Entry {
        name,
        file_size: le64(bytes, 8),
        physical_size: le64(bytes, 16),
        attributes,
        directory: attributes & 0x10 != 0,
        dot,
    })
}

#[derive(Debug)]
pub struct VolumeInfo {
    pub label: String,
    pub read_only: bool,
    pub size: u64,
    pub free_space: u64,
    pub block_size: u32,
}

pub fn volume_info(bytes: &[u8]) -> Result<VolumeInfo, Invalid> {
    let bytes = sized(bytes, 36)?;
    let size = le64(bytes, 16);
    let free_space = le64(bytes, 24);
    let block_size = u32::from_le_bytes(bytes[32..36].try_into().unwrap());
    if bytes[8] > 1 || free_space > size || size == 0 || block_size == 0 {
        return Err(Invalid::Geometry);
    }
    Ok(VolumeInfo {
        label: name(&bytes[36..], false)?,
        read_only: bytes[8] != 0,
        size,
        free_space,
        block_size,
    })
}

#[derive(Default, Debug)]
pub struct Budget {
    pub bytes: usize,
    pub entries: usize,
}

impl Budget {
    pub fn capacity(&self) -> Result<usize, Invalid> {
        let remaining = MAX_METADATA.checked_sub(self.bytes).ok_or(Invalid::Limit)?;
        if remaining < 82 {
            return Err(Invalid::Limit);
        }
        Ok(remaining.min(MAX_RECORD))
    }
    pub fn response(&mut self, bytes: usize, capacity: usize) -> Result<(), Invalid> {
        if bytes > capacity || capacity > MAX_RECORD {
            return Err(Invalid::Size);
        }
        self.bytes = self
            .bytes
            .checked_add(bytes)
            .filter(|v| *v <= MAX_METADATA)
            .ok_or(Invalid::Limit)?;
        Ok(())
    }
    pub fn record(&mut self, volume_entries: usize) -> Result<(), Invalid> {
        if volume_entries >= MAX_ENTRIES || self.entries >= MAX_TOTAL_ENTRIES {
            return Err(Invalid::Limit);
        }
        self.entries += 1;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloc::vec;

    fn path(nodes: usize) -> Vec<u8> {
        let mut value = Vec::new();
        for index in 0..nodes {
            value.extend_from_slice(&[1, index as u8, 4, 0]);
        }
        value.extend_from_slice(&[0x7f, 0xff, 4, 0]);
        value
    }
    fn record(name: &[u16], root: bool) -> Vec<u8> {
        let mut bytes = vec![0; 80];
        bytes[72] = if root { 0x10 } else { 0 };
        for unit in name.iter().chain(core::iter::once(&0)) {
            bytes.extend_from_slice(&unit.to_le_bytes());
        }
        let length = bytes.len() as u64;
        bytes[..8].copy_from_slice(&length.to_le_bytes());
        bytes
    }
    #[test]
    fn strict_descendant_and_sibling() {
        assert_eq!(descendant(&path(1), &path(2)), Ok(true));
        assert_eq!(descendant(&path(1), &path(1)), Ok(false));
        let mut sibling = path(2);
        sibling[1] = 3;
        assert_eq!(descendant(&path(1), &sibling), Ok(false));
    }
    #[test]
    fn invalid_path_boundaries() {
        for value in [
            vec![],
            vec![0x7f, 0xff, 4, 0],
            vec![1, 0, 0, 0],
            vec![1, 0, 5, 0, 0x7f, 0xff, 4, 0],
            vec![1, 0, 4, 0, 0x7f, 1, 4, 0, 0x7f, 0xff, 4, 0],
            path(MAX_NODES),
        ] {
            assert!(path_body(&value).is_err());
        }
        let mut extra = path(1);
        extra.push(0);
        assert!(path_body(&extra).is_err());
    }
    #[test]
    fn bounded_record_size_and_terminator() {
        assert!(entry(&record(&[65], false), false).is_ok());
        for size in [0, 79, 80, 81, 4097, u64::MAX] {
            let mut bytes = record(&[65], false);
            bytes[..8].copy_from_slice(&size.to_le_bytes());
            assert!(entry(&bytes, false).is_err());
        }
        let mut bytes = record(&[65], false);
        let length = bytes.len();
        bytes[length - 2] = 66;
        assert!(entry(&bytes, false).is_err());
    }
    #[test]
    fn names_cannot_inject_markers_or_paths() {
        for units in [
            vec![10],
            vec![0x1b],
            vec![0x2f],
            vec![0x5c],
            vec![0xd800],
            vec![65; 256],
        ] {
            assert!(entry(&record(&units, false), false).is_err());
        }
        assert!(entry(&record(&[46, 46], false), false).unwrap().dot);
        assert_eq!(
            entry(&record(&[34, 0x2028], false), false).unwrap().name,
            "\\\"\\u2028"
        );
        // C1 is data, rendered as an ASCII escape; C0/DEL cannot be components.
        assert_eq!(
            entry(&record(&[0x80, 0x85, 0x9f], false), false)
                .unwrap()
                .name,
            "\\u0080\\u0085\\u009f"
        );
    }
    #[test]
    fn root_and_attributes_checked() {
        assert!(entry(&record(&[], true), true).is_ok());
        assert!(entry(&record(&[65], true), true).is_err());
        assert!(entry(&record(&[], false), true).is_err());
        let mut bytes = record(&[65], false);
        bytes[72] = 0x80;
        assert!(entry(&bytes, false).is_err());
    }
    #[test]
    fn volume_bounds_and_escaped_label() {
        let mut bytes = vec![0; 40];
        bytes[0] = 40;
        bytes[16] = 100;
        bytes[24] = 20;
        bytes[32] = 1;
        bytes[36] = 10;
        assert_eq!(volume_info(&bytes).unwrap().label, "\\u000a");
        bytes[8] = 2;
        assert!(volume_info(&bytes).is_err());
        bytes[8] = 0;
        bytes[24] = 101;
        assert!(volume_info(&bytes).is_err());
    }
    #[test]
    fn budget_cannot_wrap_or_read_past_limits() {
        let mut budget = Budget::default();
        assert!(budget.response(4097, 4096).is_err());
        budget.bytes = MAX_METADATA;
        assert!(budget.capacity().is_err());
        budget.entries = MAX_TOTAL_ENTRIES;
        assert!(budget.record(0).is_err());
        budget.entries = 0;
        assert!(budget.record(MAX_ENTRIES).is_err());
        assert!(budget.record(MAX_ENTRIES - 1).is_ok());
    }
}
