use reims_vgpu::backend::vulkan::engine::{self, ComputeBufferResource, ComputeRequest};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    assert_eq!(args.len(), 3, "AIR fixture and owned scratch directory required");
    let scratch = std::path::Path::new(&args[2]);
    std::fs::create_dir_all(scratch).expect("create owned scratch");
    let spv = metal2vulkan::translate(&args[1], metal2vulkan::passes::Stage::Kernel, scratch)
        .expect("AIR translation and SPIR-V validation must actually succeed");
    assert_eq!(spv.len() % 4, 0);
    let words = spv.chunks_exact(4)
        .map(|c| u32::from_le_bytes(c.try_into().unwrap())).collect();
    let input: Vec<f32> = vec![1., 2., 3., 4., 5., 6., 7., 8.];
    let request = ComputeRequest {
        spirv: words, entry: "main".into(), grid: [1, 1, 1],
        storage_buffers: vec![ComputeBufferResource {
            binding: 0, bytes: input.iter().flat_map(|v| v.to_le_bytes()).collect(), writable: true,
        }], sampled_images: vec![], samplers: vec![], storage_images: vec![],
    };
    let result = engine::execute_compute_request(&request)
        .expect("Vulkan dispatch and readback must actually succeed");
    assert!(!result.buffers.is_empty());
    let values: Vec<f32> = result.buffers[0].bytes.chunks_exact(4)
        .map(|c| f32::from_le_bytes(c.try_into().unwrap())).collect();
    let expected: Vec<f32> = input.iter().map(|v| v * 4. + 3.).collect();
    assert_eq!(values, expected);
    println!("{{\"passed\":true,\"air_translated\":true,\"spirv_bytes\":{},\"software_vulkan_values\":{:?}}}",
             spv.len(), values);
}
