use std::collections::HashMap;

use crate::config::DevicePropValue;
use crate::error::{CoreError, Result};

#[derive(Debug, Clone)]
pub struct DevicePropertyPath(pub String);

#[derive(Debug, Clone)]
pub struct DevicePropertyEntry {
    pub path: String,
    pub properties: HashMap<String, PropertyData>,
}

#[derive(Debug, Clone)]
pub struct PropertyData {
    pub bytes: Vec<u8>,
}

impl PropertyData {
    pub fn from_config_value(val: &DevicePropValue) -> Self {
        match val {
            DevicePropValue::Data(bytes) => {
                PropertyData {
                    bytes: bytes.clone(),
                }
            }
            DevicePropValue::Integer(v) => {
                PropertyData {
                    bytes: v.to_le_bytes().to_vec(),
                }
            }
            DevicePropValue::String(s) => {
                PropertyData {
                    bytes: s.as_bytes().to_vec(),
                }
            }
            DevicePropValue::Bool(b) => {
                PropertyData {
                    bytes: vec![if *b { 1 } else { 0 }],
                }
            }
        }
    }
}

pub fn apply_properties(
    config: &crate::config::DevicePropertiesConfig,
) -> Vec<DevicePropertyEntry> {
    let mut entries = Vec::new();

    for (path_str, props) in &config.add {
        let mut properties = HashMap::new();
        for (key, value) in props {
            properties.insert(key.clone(), PropertyData::from_config_value(value));
        }
        entries.push(DevicePropertyEntry {
            path: path_str.clone(),
            properties,
        });
    }

    entries
}

pub fn encode_properties(props: &HashMap<String, PropertyData>) -> Vec<u8> {
    let mut buf = Vec::new();

    let entries: Vec<_> = props.iter().collect();
    let count = entries.len() as u32;
    buf.extend_from_slice(&count.to_le_bytes());

    for (key, data) in entries {
        let key_bytes = key.as_bytes();
        let key_len = key_bytes.len() as u32;
        buf.extend_from_slice(&key_len.to_le_bytes());
        buf.extend_from_slice(key_bytes);

        let data_len = data.bytes.len() as u32;
        buf.extend_from_slice(&data_len.to_le_bytes());
        buf.extend_from_slice(&data.bytes);
    }

    buf
}

pub fn decode_properties(data: &[u8]) -> Result<HashMap<String, PropertyData>> {
    if data.len() < 4 {
        return Err(CoreError::DeviceProps("data too short".into()));
    }

    let count = u32::from_le_bytes([data[0], data[1], data[2], data[3]]) as usize;
    let mut pos = 4;
    let mut props = HashMap::new();

    for _ in 0..count {
        if pos + 4 > data.len() {
            return Err(CoreError::DeviceProps("truncated key length".into()));
        }
        let key_len =
            u32::from_le_bytes([data[pos], data[pos + 1], data[pos + 2], data[pos + 3]]) as usize;
        pos += 4;

        if pos + key_len > data.len() {
            return Err(CoreError::DeviceProps("truncated key data".into()));
        }
        let key = String::from_utf8_lossy(&data[pos..pos + key_len]).into_owned();
        pos += key_len;

        if pos + 4 > data.len() {
            return Err(CoreError::DeviceProps("truncated value length".into()));
        }
        let val_len =
            u32::from_le_bytes([data[pos], data[pos + 1], data[pos + 2], data[pos + 3]]) as usize;
        pos += 4;

        if pos + val_len > data.len() {
            return Err(CoreError::DeviceProps("truncated value data".into()));
        }
        let bytes = data[pos..pos + val_len].to_vec();
        pos += val_len;

        props.insert(key, PropertyData { bytes });
    }

    Ok(props)
}
