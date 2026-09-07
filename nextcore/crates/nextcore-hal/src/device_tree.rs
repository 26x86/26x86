use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct DeviceTreeNode {
    pub name: String,
    pub device_type: String,
    pub properties: HashMap<String, Vec<u8>>,
    pub children: Vec<DeviceTreeNode>,
}

pub struct DeviceTreeTranslator;

impl DeviceTreeTranslator {
    pub fn new() -> Self {
        Self
    }

    pub fn translate(real: &DeviceTreeNode) -> DeviceTreeNode {
        let mut translated = real.clone();

        match real.name.as_str() {
            name if name.starts_with("cpus") => {
                translated.device_type = "cpu".to_string();
            }
            name if name.starts_with("memory") => {
                translated.device_type = "memory".to_string();
            }
            name if name.starts_with("pci") => {
                translated.device_type = "pci".to_string();
                if !translated.properties.contains_key("device_type") {
                    translated
                        .properties
                        .insert("device_type".to_string(), b"pci".to_vec());
                }
            }
            name if name.starts_with("chosen") => {
                translated.device_type = "chosen".to_string();
            }
            _ => {}
        }

        for child in &mut translated.children {
            *child = Self::translate(child);
        }

        translated
    }
}

pub fn build_mac_device_tree(
    cpu_count: u32,
    mem_bytes: u64,
    pci_vendor_devices: &[(u16, u16)],
) -> DeviceTreeNode {
    let mut cpu_children = Vec::new();
    for i in 0..cpu_count {
        let mut props = HashMap::new();
        props.insert("device_type".to_string(), b"cpu".to_vec());
        props.insert(
            "reg".to_string(),
            i.to_le_bytes().to_vec(),
        );
        props.insert("cpu-version".to_string(), format!("cpu@{}", i).into_bytes());
        cpu_children.push(DeviceTreeNode {
            name: format!("cpu@{}", i),
            device_type: "cpu".to_string(),
            properties: props,
            children: Vec::new(),
        });
    }

    let mut mem_props = HashMap::new();
    mem_props.insert("device_type".to_string(), b"memory".to_vec());
    mem_props.insert("reg".to_string(), mem_bytes.to_le_bytes().to_vec());
    mem_props.insert(
        "size".to_string(),
        mem_bytes.to_le_bytes().to_vec(),
    );
    let memory_node = DeviceTreeNode {
        name: "memory".to_string(),
        device_type: "memory".to_string(),
        properties: mem_props,
        children: Vec::new(),
    };

    let mut chosen_props = HashMap::new();
    chosen_props.insert(
        "boot-args".to_string(),
        b"-v keepsyms=1".to_vec(),
    );
    let chosen_node = DeviceTreeNode {
        name: "chosen".to_string(),
        device_type: "chosen".to_string(),
        properties: chosen_props,
        children: Vec::new(),
    };

    let mut pci_children = Vec::new();
    for (i, &(vendor_id, device_id)) in pci_vendor_devices.iter().enumerate() {
        let mut pci_props = HashMap::new();
        pci_props.insert("device_type".to_string(), b"pci".to_vec());
        pci_props.insert("vendor-id".to_string(), vendor_id.to_le_bytes().to_vec());
        pci_props.insert("device-id".to_string(), device_id.to_le_bytes().to_vec());
        pci_props.insert(
            "reg".to_string(),
            vec![0x00, i as u8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        );
        pci_children.push(DeviceTreeNode {
            name: format!("pci@{}", i),
            device_type: "pci".to_string(),
            properties: pci_props,
            children: Vec::new(),
        });
    }

    let pci_node = DeviceTreeNode {
        name: "pci".to_string(),
        device_type: "pci".to_string(),
        properties: {
            let mut p = HashMap::new();
            p.insert("device_type".to_string(), b"pci".to_vec());
            p
        },
        children: pci_children,
    };

    let mut root_props = HashMap::new();
    root_props.insert(
        "model".to_string(),
        b"Apple Mac".to_vec(),
    );
    root_props.insert(
        "compatible".to_string(),
        b"Mac\0".to_vec(),
    );

    DeviceTreeNode {
        name: "/".to_string(),
        device_type: "root".to_string(),
        properties: root_props,
        children: vec![
            DeviceTreeNode {
                name: "cpus".to_string(),
                device_type: "cpu".to_string(),
                properties: HashMap::new(),
                children: cpu_children,
            },
            memory_node,
            chosen_node,
            pci_node,
        ],
    }
}

impl Default for DeviceTreeTranslator {
    fn default() -> Self {
        Self::new()
    }
}
