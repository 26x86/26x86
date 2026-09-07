//! Bounded structural codec for the public x86 flattened device-tree format.
//!
//! Independently expressed from these pinned public interface references:
//! <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/device_tree.h>
//! <https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/gen/device_tree.c>
//! This is not the FDT format. Structural validity does not establish sufficient
//! entropy, EFI, memory, platform or other properties for an operating system.

use alloc::{string::String, vec::Vec};
use core::fmt;

pub const MAX_SERIALIZED_SIZE: usize = 1024 * 1024;
/// Root is depth 0. A node at depth 32 is allowed but cannot have children.
pub const MAX_DEPTH: usize = 32;
pub const MAX_NODES: usize = 1024;
pub const MAX_PROPERTIES: usize = 4096;
/// Includes the automatically inserted `name` property.
pub const MAX_PROPERTIES_PER_NODE: usize = 64;
pub const MAX_CHILDREN_PER_NODE: usize = 64;
pub const MAX_NODE_NAME: usize = 63;
pub const MAX_PROPERTY_NAME: usize = 31;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FlatNode {
    /// Printable ASCII; an empty name is accepted only for the root.
    /// Serialized as a NUL-terminated `name` property before other properties.
    pub name: String,
    pub properties: Vec<FlatProperty>,
    pub children: Vec<FlatNode>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FlatProperty {
    /// Printable ASCII, 1..=31 bytes. `name` is reserved for FlatNode::name.
    pub name: String,
    /// Opaque bytes; string values must explicitly include their final NUL.
    pub value: Vec<u8>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FlatDtError {
    InvalidNodeName,
    InvalidPropertyName,
    DuplicateProperty,
    DuplicateChild,
    InvalidNameProperty,
    LimitsExceeded,
    Truncated,
    InvalidPadding,
    TrailingData,
    AllocationFailed,
}

impl fmt::Display for FlatDtError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidNodeName => "INVALID_NODE_NAME",
            Self::InvalidPropertyName => "INVALID_PROPERTY_NAME",
            Self::DuplicateProperty => "DUPLICATE_PROPERTY",
            Self::DuplicateChild => "DUPLICATE_CHILD",
            Self::InvalidNameProperty => "INVALID_NAME_PROPERTY",
            Self::LimitsExceeded => "DT_LIMITS_EXCEEDED",
            Self::Truncated => "TRUNCATED_DT",
            Self::InvalidPadding => "INVALID_DT_PADDING",
            Self::TrailingData => "TRAILING_DT_DATA",
            Self::AllocationFailed => "DT_ALLOCATION_FAILED",
        })
    }
}

#[derive(Default)]
struct Budget {
    nodes: usize,
    properties: usize,
    bytes: usize,
}

impl Budget {
    fn node(
        &mut self,
        depth: usize,
        properties: usize,
        children: usize,
    ) -> Result<(), FlatDtError> {
        if depth > MAX_DEPTH
            || properties == 0
            || properties > MAX_PROPERTIES_PER_NODE
            || children > MAX_CHILDREN_PER_NODE
        {
            return Err(FlatDtError::LimitsExceeded);
        }
        self.nodes = self
            .nodes
            .checked_add(1)
            .ok_or(FlatDtError::LimitsExceeded)?;
        self.properties = self
            .properties
            .checked_add(properties)
            .ok_or(FlatDtError::LimitsExceeded)?;
        if self.nodes > MAX_NODES || self.properties > MAX_PROPERTIES {
            return Err(FlatDtError::LimitsExceeded);
        }
        self.add_bytes(8)
    }

    fn add_bytes(&mut self, bytes: usize) -> Result<(), FlatDtError> {
        self.bytes = self
            .bytes
            .checked_add(bytes)
            .ok_or(FlatDtError::LimitsExceeded)?;
        if self.bytes > MAX_SERIALIZED_SIZE {
            return Err(FlatDtError::LimitsExceeded);
        }
        Ok(())
    }
}

/// Preflight the complete model before allocating the bounded output buffer.
pub fn encode(root: &FlatNode) -> Result<Vec<u8>, FlatDtError> {
    let mut budget = Budget::default();
    measure_node(root, 0, &mut budget)?;
    let mut bytes = Vec::new();
    bytes
        .try_reserve_exact(budget.bytes)
        .map_err(|_| FlatDtError::AllocationFailed)?;
    write_node(root, &mut bytes)?;
    Ok(bytes)
}

fn measure_node(node: &FlatNode, depth: usize, budget: &mut Budget) -> Result<(), FlatDtError> {
    let property_count = node
        .properties
        .len()
        .checked_add(1)
        .ok_or(FlatDtError::LimitsExceeded)?;
    budget.node(depth, property_count, node.children.len())?;
    check_node_name(node.name.as_bytes(), depth)?;
    budget.add_bytes(property_size(node.name.len() + 1)?)?;
    for (index, property) in node.properties.iter().enumerate() {
        check_property_name(property.name.as_bytes())?;
        if property.name == "name"
            || node.properties[..index]
                .iter()
                .any(|p| p.name == property.name)
        {
            return Err(FlatDtError::DuplicateProperty);
        }
        budget.add_bytes(property_size(property.value.len())?)?;
    }
    for (index, child) in node.children.iter().enumerate() {
        if node.children[..index].iter().any(|c| c.name == child.name) {
            return Err(FlatDtError::DuplicateChild);
        }
        measure_node(child, depth + 1, budget)?;
    }
    Ok(())
}

fn property_size(value_size: usize) -> Result<usize, FlatDtError> {
    if value_size > MAX_SERIALIZED_SIZE {
        return Err(FlatDtError::LimitsExceeded);
    }
    Ok(36 + ((value_size + 3) & !3))
}

fn printable(bytes: &[u8]) -> bool {
    bytes.iter().all(|&b| (0x20..=0x7e).contains(&b))
}

fn check_node_name(name: &[u8], depth: usize) -> Result<(), FlatDtError> {
    if name.len() > MAX_NODE_NAME || (name.is_empty() && depth != 0) || !printable(name) {
        return Err(FlatDtError::InvalidNodeName);
    }
    Ok(())
}

fn check_property_name(name: &[u8]) -> Result<(), FlatDtError> {
    if name.is_empty() || name.len() > MAX_PROPERTY_NAME || !printable(name) {
        return Err(FlatDtError::InvalidPropertyName);
    }
    Ok(())
}

fn write_node(node: &FlatNode, bytes: &mut Vec<u8>) -> Result<(), FlatDtError> {
    let properties =
        u32::try_from(node.properties.len() + 1).map_err(|_| FlatDtError::LimitsExceeded)?;
    let children = u32::try_from(node.children.len()).map_err(|_| FlatDtError::LimitsExceeded)?;
    bytes.extend_from_slice(&properties.to_le_bytes());
    bytes.extend_from_slice(&children.to_le_bytes());
    let mut name_value = [0u8; MAX_NODE_NAME + 1];
    name_value[..node.name.len()].copy_from_slice(node.name.as_bytes());
    write_property(b"name", &name_value[..node.name.len() + 1], bytes)?;
    for property in &node.properties {
        write_property(property.name.as_bytes(), &property.value, bytes)?;
    }
    for child in &node.children {
        write_node(child, bytes)?;
    }
    Ok(())
}

fn write_property(name: &[u8], value: &[u8], bytes: &mut Vec<u8>) -> Result<(), FlatDtError> {
    let length = u32::try_from(value.len()).map_err(|_| FlatDtError::LimitsExceeded)?;
    let mut wire_name = [0u8; 32];
    wire_name[..name.len()].copy_from_slice(name);
    bytes.extend_from_slice(&wire_name);
    bytes.extend_from_slice(&length.to_le_bytes());
    bytes.extend_from_slice(value);
    bytes.resize((bytes.len() + 3) & !3, 0);
    Ok(())
}

/// Validate this codec's bounded profile without allocating or trusting counts.
/// Names and padding must be canonical: no bytes after a name's terminator and
/// zero alignment padding. Opaque property payloads are not interpreted.
pub fn validate(bytes: &[u8]) -> Result<(), FlatDtError> {
    if bytes.len() > MAX_SERIALIZED_SIZE {
        return Err(FlatDtError::LimitsExceeded);
    }
    let mut cursor = 0;
    let mut budget = Budget::default();
    read_node(bytes, &mut cursor, 0, &mut budget)?;
    if cursor != bytes.len() {
        return Err(FlatDtError::TrailingData);
    }
    Ok(())
}

fn read_node<'a>(
    bytes: &'a [u8],
    cursor: &mut usize,
    depth: usize,
    budget: &mut Budget,
) -> Result<&'a [u8], FlatDtError> {
    let properties =
        usize::try_from(read_u32(bytes, cursor)?).map_err(|_| FlatDtError::LimitsExceeded)?;
    let children =
        usize::try_from(read_u32(bytes, cursor)?).map_err(|_| FlatDtError::LimitsExceeded)?;
    budget.node(depth, properties, children)?;
    // Fixed bounds keep both recursive stack use and duplicate comparisons small.
    let mut property_names: [&[u8]; MAX_PROPERTIES_PER_NODE] = [&[]; MAX_PROPERTIES_PER_NODE];
    let mut node_name = None;
    for index in 0..properties {
        let wire_name = take(bytes, cursor, 32)?;
        let terminator = wire_name
            .iter()
            .position(|&b| b == 0)
            .ok_or(FlatDtError::InvalidPropertyName)?;
        let name = &wire_name[..terminator];
        check_property_name(name)?;
        if wire_name[terminator..].iter().any(|&b| b != 0) {
            return Err(FlatDtError::InvalidPropertyName);
        }
        if property_names[..index].contains(&name) {
            return Err(FlatDtError::DuplicateProperty);
        }
        property_names[index] = name;
        let size =
            usize::try_from(read_u32(bytes, cursor)?).map_err(|_| FlatDtError::LimitsExceeded)?;
        budget.add_bytes(property_size(size)?)?;
        let value = take(bytes, cursor, size)?;
        if name == b"name" {
            if value.last() != Some(&0) {
                return Err(FlatDtError::InvalidNameProperty);
            }
            let value_name = &value[..value.len() - 1];
            check_node_name(value_name, depth)?;
            node_name = Some(value_name);
        }
        let padding = take(bytes, cursor, (4 - size % 4) % 4)?;
        if padding.iter().any(|&b| b != 0) {
            return Err(FlatDtError::InvalidPadding);
        }
    }
    let node_name = node_name.ok_or(FlatDtError::InvalidNameProperty)?;
    let mut child_names: [&[u8]; MAX_CHILDREN_PER_NODE] = [&[]; MAX_CHILDREN_PER_NODE];
    for index in 0..children {
        let name = read_node(bytes, cursor, depth + 1, budget)?;
        if child_names[..index].contains(&name) {
            return Err(FlatDtError::DuplicateChild);
        }
        child_names[index] = name;
    }
    Ok(node_name)
}

fn take<'a>(bytes: &'a [u8], cursor: &mut usize, size: usize) -> Result<&'a [u8], FlatDtError> {
    let end = cursor.checked_add(size).ok_or(FlatDtError::Truncated)?;
    let slice = bytes.get(*cursor..end).ok_or(FlatDtError::Truncated)?;
    *cursor = end;
    Ok(slice)
}

fn read_u32(bytes: &[u8], cursor: &mut usize) -> Result<u32, FlatDtError> {
    let value = take(bytes, cursor, 4)?;
    Ok(u32::from_le_bytes([value[0], value[1], value[2], value[3]]))
}
