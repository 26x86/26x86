use nextcore_core::flat_dt::{
    encode, validate, FlatDtError, FlatNode, FlatProperty, MAX_CHILDREN_PER_NODE, MAX_DEPTH,
    MAX_NODES, MAX_PROPERTIES_PER_NODE, MAX_SERIALIZED_SIZE,
};

fn node(name: &str) -> FlatNode {
    FlatNode {
        name: name.into(),
        properties: vec![],
        children: vec![],
    }
}

fn property(name: &str, value: &[u8]) -> FlatProperty {
    FlatProperty {
        name: name.into(),
        value: value.into(),
    }
}

/// Authored wire fixture: two u32 counts, fixed 32-byte key, u32 length,
/// a slash and NUL, then two padding bytes. No fixture from Apple media.
fn golden_root() -> Vec<u8> {
    let mut bytes = vec![0; 48];
    bytes[0] = 1;
    bytes[8..12].copy_from_slice(b"name");
    bytes[40] = 2;
    bytes[44] = b'/';
    bytes
}

#[test]
fn minimal_root_matches_independently_authored_wire_fixture() {
    assert_eq!(encode(&node("/")).unwrap(), golden_root());
    assert_eq!(validate(&golden_root()), Ok(()));
    assert_eq!(encode(&node("")).unwrap().len(), 48);
}

#[test]
fn properties_precede_child_subtrees_and_payloads_are_padded_to_four_bytes() {
    let mut root = node("/");
    root.properties.push(property("tag", &[0xaa, 0xbb, 0xcc]));
    root.properties.push(property("empty", &[]));
    root.children.push(node("chosen"));
    let bytes = encode(&root).unwrap();
    assert_eq!(&bytes[..8], &[3, 0, 0, 0, 1, 0, 0, 0]);
    assert_eq!(&bytes[48..52], &[b't', b'a', b'g', 0]);
    assert_eq!(&bytes[80..88], &[3, 0, 0, 0, 0xaa, 0xbb, 0xcc, 0]);
    assert_eq!(&bytes[88..94], b"empty\0");
    assert_eq!(&bytes[120..124], &[0; 4]);
    assert_eq!(&bytes[124..132], &[1, 0, 0, 0, 0, 0, 0, 0]);
    assert_eq!(&bytes[164..168], &[7, 0, 0, 0]);
    assert_eq!(&bytes[168..176], b"chosen\0\0");
    assert_eq!(bytes.len(), 176);
    assert_eq!(validate(&bytes), Ok(()));
}

#[test]
fn every_truncated_prefix_and_trailing_bytes_are_rejected() {
    let mut root = node("/");
    root.children.push(node("chosen"));
    let bytes = encode(&root).unwrap();
    for length in 0..bytes.len() {
        assert!(
            validate(&bytes[..length]).is_err(),
            "accepted truncated length {length}"
        );
    }
    let mut with_trailing = bytes;
    with_trailing.extend_from_slice(&[0; 4]);
    assert_eq!(validate(&with_trailing), Err(FlatDtError::TrailingData));
}

#[test]
fn malicious_lengths_counts_and_missing_name_do_not_drive_unbounded_work() {
    for offset in [0, 4, 40] {
        let mut bytes = golden_root();
        bytes[offset..offset + 4].copy_from_slice(&u32::MAX.to_le_bytes());
        assert_eq!(validate(&bytes), Err(FlatDtError::LimitsExceeded));
    }
    let mut bytes = golden_root();
    bytes[0] = 0;
    assert!(validate(&bytes).is_err());
    bytes = golden_root();
    bytes[8..12].copy_from_slice(b"fake");
    assert_eq!(validate(&bytes), Err(FlatDtError::InvalidNameProperty));
    bytes = golden_root();
    bytes[40] = 8;
    assert_eq!(validate(&bytes), Err(FlatDtError::Truncated));
}

#[test]
fn unterminated_noncanonical_or_invalid_names_and_padding_are_rejected() {
    let mut bytes = golden_root();
    bytes[8..40].fill(b'x');
    assert_eq!(validate(&bytes), Err(FlatDtError::InvalidPropertyName));
    bytes = golden_root();
    bytes[13] = b'x';
    assert_eq!(validate(&bytes), Err(FlatDtError::InvalidPropertyName));
    bytes = golden_root();
    bytes[45] = b'x';
    assert_eq!(validate(&bytes), Err(FlatDtError::InvalidNameProperty));
    bytes = golden_root();
    bytes[44] = 0;
    assert_eq!(validate(&bytes), Err(FlatDtError::InvalidNodeName));
    bytes = golden_root();
    bytes[47] = 1;
    assert_eq!(validate(&bytes), Err(FlatDtError::InvalidPadding));
    for name in [
        "x".repeat(64),
        "nul\0name".into(),
        "\n".into(),
        "노드".into(),
    ] {
        assert_eq!(encode(&node(&name)), Err(FlatDtError::InvalidNodeName));
    }
    let mut root = node("/");
    root.children.push(node(""));
    assert_eq!(encode(&root), Err(FlatDtError::InvalidNodeName));
    for name in ["".into(), "x".repeat(32), "bad\0key".into(), "속성".into()] {
        root = node("/");
        root.properties.push(property(&name, &[]));
        assert_eq!(encode(&root), Err(FlatDtError::InvalidPropertyName));
    }
}

#[test]
fn longest_names_and_binary_values_remain_supported() {
    let mut root = node(&"r".repeat(63));
    root.properties
        .push(property(&"p".repeat(31), &[0, 0xff, 0x80, 0, 1]));
    assert_eq!(validate(&encode(&root).unwrap()), Ok(()));
}

#[test]
fn duplicate_properties_and_children_are_rejected_in_models_and_wire() {
    let mut root = node("/");
    root.properties.push(property("name", b"override\0"));
    assert_eq!(encode(&root), Err(FlatDtError::DuplicateProperty));
    root.properties = vec![property("a", &[]), property("a", &[])];
    assert_eq!(encode(&root), Err(FlatDtError::DuplicateProperty));
    root.properties = vec![property("a", &[]), property("b", &[])];
    let mut bytes = encode(&root).unwrap();
    bytes[84] = b'a';
    assert_eq!(validate(&bytes), Err(FlatDtError::DuplicateProperty));
    root = node("/");
    root.children = vec![node("same"), node("same")];
    assert_eq!(encode(&root), Err(FlatDtError::DuplicateChild));
    root.children[1].name = "diff".into();
    bytes = encode(&root).unwrap();
    bytes[144..148].copy_from_slice(b"same");
    assert_eq!(validate(&bytes), Err(FlatDtError::DuplicateChild));
}

fn chain(depth: usize) -> FlatNode {
    let mut tree = node("leaf");
    for _ in 0..depth {
        let mut parent = node("branch");
        parent.children.push(tree);
        tree = parent;
    }
    tree
}

#[test]
fn depth_limit_applies_to_both_encoder_and_untrusted_wire() {
    assert!(validate(&encode(&chain(MAX_DEPTH)).unwrap()).is_ok());
    assert_eq!(
        encode(&chain(MAX_DEPTH + 1)),
        Err(FlatDtError::LimitsExceeded)
    );
    let mut wire_node = golden_root();
    wire_node[4] = 1;
    let mut bytes = wire_node.repeat(MAX_DEPTH + 1);
    bytes.extend_from_slice(&golden_root());
    assert_eq!(validate(&bytes), Err(FlatDtError::LimitsExceeded));
}

#[test]
fn per_node_and_total_limits_precede_serialization() {
    let mut root = node("/");
    for n in 0..MAX_CHILDREN_PER_NODE + 1 {
        root.children.push(node(&format!("child-{n}")));
    }
    assert_eq!(encode(&root), Err(FlatDtError::LimitsExceeded));
    root = node("/");
    for n in 0..MAX_PROPERTIES_PER_NODE {
        root.properties
            .push(property(&format!("property-{n}"), &[]));
    }
    assert_eq!(encode(&root), Err(FlatDtError::LimitsExceeded));
    root = node("/");
    let mut count = 1;
    for n in 0..32 {
        let mut branch = node(&format!("branch-{n}"));
        count += 1;
        for k in 0..32 {
            branch.children.push(node(&format!("leaf-{k}")));
            count += 1;
        }
        root.children.push(branch);
    }
    assert!(count > MAX_NODES);
    assert_eq!(encode(&root), Err(FlatDtError::LimitsExceeded));
    root = node("/");
    root.properties
        .push(property("large", &vec![0; MAX_SERIALIZED_SIZE]));
    assert_eq!(encode(&root), Err(FlatDtError::LimitsExceeded));
    assert_eq!(
        validate(&vec![0; MAX_SERIALIZED_SIZE + 1]),
        Err(FlatDtError::LimitsExceeded)
    );
}

#[test]
fn aggregate_property_budget_also_applies_to_individually_valid_subtrees() {
    // 64 children each with 64 properties plus the root's name = 4097.
    let mut root = node("/");
    let mut wire = golden_root();
    wire[4] = 64;
    for n in 0..64 {
        let mut child = node(&format!("child-{n}"));
        for p in 0..63 {
            child.properties.push(property(&format!("key-{p}"), &[]));
        }
        wire.extend_from_slice(&encode(&child).unwrap());
        root.children.push(child);
    }
    assert_eq!(encode(&root), Err(FlatDtError::LimitsExceeded));
    assert_eq!(validate(&wire), Err(FlatDtError::LimitsExceeded));
}

#[test]
fn aggregate_node_budget_also_applies_to_individually_valid_subtrees() {
    let mut wire = golden_root();
    wire[4] = 32;
    for n in 0..32 {
        let mut child = node(&format!("child-{n}"));
        for p in 0..32 {
            child.children.push(node(&format!("leaf-{p}")));
        }
        wire.extend_from_slice(&encode(&child).unwrap());
    }
    assert_eq!(validate(&wire), Err(FlatDtError::LimitsExceeded));
}

#[test]
fn error_display_does_not_include_untrusted_names() {
    assert_eq!(
        FlatDtError::InvalidNodeName.to_string(),
        "INVALID_NODE_NAME"
    );
    assert_eq!(FlatDtError::Truncated.to_string(), "TRUNCATED_DT");
}
