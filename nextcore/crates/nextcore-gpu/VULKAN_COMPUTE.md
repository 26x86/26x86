# Explicit host Vulkan compute

Current state: `ComputePipelineManager::new()` stores host buffers/descriptors but
cannot execute shaders. Its `dispatch` returns `BackendUnavailable` without
signaling a fence. The optional `vulkan` feature provides a real host Vulkan 1.1
compute backend; it does not attach guest Metal, SGPU, or a VirtualMetalDevice.
The latter model supports software buffer copies only. Its Metal support query
returns false, and its command-list API rejects compute, clear, and present
before executing any copy in a mixed list. SGPU propagates that failure without
a success response and does not advertise compute execution support.

Create a manager with `ComputePipelineManager::with_vulkan(VulkanComputeConfig)`.
The config requires exact nonzero vendor/device IDs, an explicitly trusted
Khronos `spirv-val` executable, and a fence timeout in `(0, 5 seconds]`. Only one
matching integrated/discrete GPU is accepted. CPU/virtual devices and ambiguous
selectors are rejected. `robustBufferAccess` must be supported and is enabled.

Supported inputs are SPIR-V 1.0–1.3 with only Shader capability, Logical/GLSL450
memory model, one compute entry point and literal LocalSize. A WorkgroupSize
builtin must be a matching literal constant vector. The entire module must pass
`spirv-val --target-env vulkan1.1`, in addition to the crate's contract reflection.
No optional shader features, images, push constants, specialization constants,
descriptor arrays, decoration groups, or workgroup storage are supported.

Use 1–8 distinct storage buffers with unique bindings in descriptor set zero.
Every source view has a four-byte-aligned offset and size; each view is at most
16 MiB (minimum four bytes) and the combined cap is 64 MiB. Aliasing even disjoint views
of the same host buffer is explicitly unsupported. The view is uploaded into a
separate Vulkan buffer, so its Vulkan descriptor offset is zero. Actual device
storage/compute limits and the 16,777,216 total-invocation cap are also checked.

Dispatch uploads to HOST_VISIBLE|HOST_COHERENT memory, records compute and a
COMPUTE_SHADER/SHADER_WRITE → HOST/HOST_READ buffer barrier, submits with a real
Vulkan fence, waits, and reads every buffer back. Only then are host buffers
updated together and the manager fence signaled. The destination fence must
exist and be unsignaled. Failed validation/dispatch leaves host data uncommitted.

If submission completion is uncertain (including a fence timeout), the backend
is poisoned. Its potentially referenced Vulkan objects and dynamic loader are
retained until process exit; it cannot dispatch again. It never destroys those
resources while commands may still use them. Fence timeouts do not bound driver
initialization, shader compilation, memory mapping, or destruction calls. Run
the execution example under an external process deadline too:

```sh
cargo build -p nextcore-gpu --features vulkan --example vulkan_compute
timeout --signal=TERM --kill-after=2s 15s \
  target/debug/examples/vulkan_compute 8086 7d41 /path/to/spirv-val
```

The host must supply its public Vulkan loader/ICD. Driver environment variables
are runtime configuration, never crate build inputs. This example uploads two
different 256-value inputs, dispatches `input * 3 + 7`, verifies every readback
value against independent host arithmetic, checks nonzero-offset prefix/suffix
guards, and tests rejection without fake fence completion. It prints one JSON
receipt. Host Vulkan success does not establish guest graphics or Metal support.

`tests/fixtures/storage_transform.comp` is independently authored in this crate.
Rebuild its owned SPIR-V fixture with public Khronos tools:

```sh
glslangValidator -V --target-env vulkan1.1 \
  tests/fixtures/storage_transform.comp -o tests/fixtures/storage_transform.spv
spirv-val --target-env vulkan1.1 tests/fixtures/storage_transform.spv
```

Public contracts: [Vulkan synchronization](https://docs.vulkan.org/spec/latest/chapters/synchronization.html),
[Khronos synchronization examples](https://docs.vulkan.org/guide/latest/synchronization_examples.html),
[SPIR-V grammar](https://github.com/KhronosGroup/SPIRV-Headers/blob/main/include/spirv/unified1/spirv.core.grammar.json).
