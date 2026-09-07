use nextcore_core::error::CoreError;
use nextcore_core::handoff::{
    deserialize_boot_args, serialize_boot_args, BootArgs, DeviceTreeBuf, MemoryEntry, MemoryKind,
    MemoryMap,
};

fn sample_args() -> BootArgs {
    BootArgs {
        magic: 0x4D656D41,
        version: 12,
        flags: 0x100,
        memory_map: MemoryMap {
            total_size: 0,
            entries: vec![
                MemoryEntry {
                    base: 0x1000,
                    size: 0x9000,
                    kind: MemoryKind::EfiConventional,
                },
                MemoryEntry {
                    base: 0x10000000,
                    size: 0x200000,
                    kind: MemoryKind::EfiRuntimeServicesData,
                },
                MemoryEntry {
                    base: 0x20000000,
                    size: 0x1000,
                    kind: MemoryKind::EfiACPINVS,
                },
            ],
        },
        kernel_base: 0xFFFFFF8000200000,
        kernel_size: 0x1000000,
        command_line: "keepsyms=1 debug=0x100 -v".into(),
        device_tree: Some(DeviceTreeBuf {
            data: vec![0xDE, 0xAD, 0xBE, 0xEF, 0x01, 0x02, 0x03],
        }),
    }
}

#[test]
fn test_roundtrip() {
    let args = sample_args();
    let bytes = serialize_boot_args(&args).expect("serialize should succeed");

    let decoded = deserialize_boot_args(&bytes).expect("deserialize should succeed");

    assert_eq!(decoded.magic, args.magic);
    assert_eq!(decoded.version, args.version);
    assert_eq!(decoded.flags, args.flags);
    assert_eq!(decoded.kernel_base, args.kernel_base);
    assert_eq!(decoded.kernel_size, args.kernel_size);
    assert_eq!(decoded.command_line, args.command_line);

    assert_eq!(decoded.memory_map.entries.len(), args.memory_map.entries.len());
    for (got, want) in decoded.memory_map.entries.iter().zip(args.memory_map.entries.iter()) {
        assert_eq!(got.base, want.base);
        assert_eq!(got.size, want.size);
        assert_eq!(got.kind, want.kind);
    }

    let dt = decoded
        .device_tree
        .expect("device_tree should roundtrip");
    assert_eq!(dt.data, args.device_tree.unwrap().data);
}

#[test]
fn test_bad_magic() {
    let mut args = sample_args();
    args.magic = 0xDEADBEEF; // wrong magic
    let bytes = serialize_boot_args(&args).expect("serialize should succeed");

    let err = deserialize_boot_args(&bytes).expect_err("bad magic must fail");
    assert!(
        matches!(err, CoreError::InvalidMagic { .. }),
        "expected InvalidMagic, got {err:?}"
    );
}

#[test]
fn test_truncated() {
    let args = sample_args();
    let bytes = serialize_boot_args(&args).expect("serialize should succeed");

    for cut in [1, 20, bytes.len() / 2, bytes.len() - 3] {
        let truncated = &bytes[..cut];
        let res = deserialize_boot_args(truncated);
        assert!(
            res.is_err(),
            "truncated data ({} bytes) should fail, got {:?}",
            cut,
            res.ok()
        );
    }
}

#[test]
fn test_deterministic() {
    let args = sample_args();
    let a = serialize_boot_args(&args).expect("serialize a");
    let b = serialize_boot_args(&args).expect("serialize b");
    assert_eq!(a, b, "serialization must be deterministic");
}
