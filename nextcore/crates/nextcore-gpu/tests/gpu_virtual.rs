use nextcore_gpu::canonical_spec::{GpuCapabilities, GpuVendor, MetalVersion};
use nextcore_gpu::virtual_device::{CommandBuffer, GpuCommand, VirtualMetalDevice};
use nextcore_gpu::translator::{GpuTranslator, RealGpuInfo};

#[test]
fn test_rx580_canonical() {
    let caps = GpuTranslator::from_pci_ids(0x1002, 0x67DF, 8192).unwrap();
    assert_eq!(caps.vendor, GpuVendor::AMD);
    assert!(caps.metal_version >= MetalVersion::V3_0);
    assert!(caps.vram_size > 0);
    assert!(caps.has_compute_shaders);
}

#[test]
fn test_vega64_canonical() {
    let caps = GpuTranslator::from_pci_ids(0x1002, 0x687F, 8192).unwrap();
    assert_eq!(caps.vendor, GpuVendor::AMD);
    assert!(caps.vram_size > 0);
}

#[test]
fn test_gtx680_canonical() {
    let caps = GpuTranslator::from_pci_ids(0x10DE, 0x1180, 4096).unwrap();
    assert_eq!(caps.vendor, GpuVendor::NVIDIA);
    assert!(caps.metal_version >= MetalVersion::V3_0);
    assert!(caps.vram_size > 0);
}

#[test]
fn test_hd4000_canonical() {
    let caps = GpuTranslator::from_pci_ids(0x8086, 0x0166, 1536).unwrap();
    assert_eq!(caps.vendor, GpuVendor::Intel);
    assert!(caps.vram_size > 0);
}

#[test]
fn test_unknown_fallback() {
    let info = RealGpuInfo {
        vendor_id: 0xFFFF,
        device_id: 0x0001,
        vram: 2048 * 1024 * 1024,
        revision: 0,
    };
    let caps = GpuTranslator::translate(&info);
    assert_eq!(caps.vendor, GpuVendor::Unknown);
    assert_eq!(caps.metal_version, MetalVersion::V2_0);
    assert!(!caps.has_compute_shaders);
    let device = VirtualMetalDevice::new(caps);
    assert!(device.is_software_accelerated());
}

#[test]
fn test_allocate_buffer() {
    let spec = GpuCapabilities::default_amd();
    let mut device = VirtualMetalDevice::new(spec);
    assert!(device.is_software_accelerated());
    assert!(!device.supports_metal());
    let buf = device.allocate_buffer(1024);
    assert_eq!(buf.size, 1024);
    assert_eq!(buf.host_ptr.len(), 1024);

    let data = vec![0xABu8; 256];
    device.memory.write(buf.handle, 0, &data).unwrap();
    let read_back = device.memory.read(buf.handle, 0, 256).unwrap();
    assert_eq!(read_back, data);
}

#[test]
fn buffer_range_overflow_is_rejected_without_mutation() {
    let mut device = VirtualMetalDevice::new(GpuCapabilities::default_amd());
    let buf = device.allocate_buffer(4);
    device.memory.write(buf.handle, 0, &[1, 2, 3, 4]).unwrap();
    assert!(device.memory.read(buf.handle, u64::MAX, 2).is_err());
    assert!(device.memory.read(buf.handle, 2, u64::MAX).is_err());
    assert!(device.memory.write(buf.handle, u64::MAX, &[0, 0]).is_err());
    assert_eq!(device.memory.read(buf.handle, 0, 4).unwrap(), [1, 2, 3, 4]);
}

#[test]
fn test_command_copy() {
    let spec = GpuCapabilities::default_amd();
    let mut device = VirtualMetalDevice::new(spec);

    let src_buf = device.allocate_buffer(64);
    let dst_buf = device.allocate_buffer(64);

    let src_data = vec![0x42u8; 64];
    device.memory.write(src_buf.handle, 0, &src_data).unwrap();

    let cmdbuf = CommandBuffer {
        cmds: vec![GpuCommand::CopyBuffer {
            src: src_buf.handle,
            dst: dst_buf.handle,
            size: 64,
        }],
    };
    device.write_command_buffer(cmdbuf).unwrap();
    device.flush().unwrap();

    let result = device.memory.read(dst_buf.handle, 0, 64).unwrap();
    assert_eq!(result, src_data);
}

#[test]
fn test_device_family() {
    let spec = GpuCapabilities::default_amd();
    let device = VirtualMetalDevice::new(spec);
    assert!(device.device_name().contains("AMD"));
}

#[test]
fn test_rx580_vram() {
    let caps = GpuTranslator::from_pci_ids(0x1002, 0x67DF, 8192).unwrap();
    assert_eq!(caps.vram_size, 8192 * 1024 * 1024);
}

#[test]
fn test_spec_json_roundtrip() {
    let spec = GpuCapabilities::default_nvidia();
    let json = serde_json::to_string(&spec).unwrap();
    let deserialized: GpuCapabilities = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.vendor, spec.vendor);
    assert_eq!(deserialized.metal_version, spec.metal_version);
    assert_eq!(deserialized.vram_size, spec.vram_size);
    assert_eq!(deserialized.max_threads, spec.max_threads);
    assert_eq!(deserialized.has_compute_shaders, spec.has_compute_shaders);
    assert_eq!(deserialized.has_tessellation, spec.has_tessellation);
}
