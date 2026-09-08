//! Explicit host Vulkan 1.1 compute with storage-buffer readback.
//!
//! Supported shader profile: SPIR-V 1.0..1.3, Shader capability only, Logical/
//! GLSL450 memory model, one GLCompute entry, literal LocalSize, set 0 scalar
//! StorageBuffer descriptors. No images, descriptor arrays, push constants,
//! shared memory, specialization constants, or optional device features.
//! A trusted Khronos spirv-val executable validates the complete module too.
//!
//! Fence wait errors poison the backend and retain all possibly in-flight Vulkan
//! objects/loader lifetime. They are not destroyed while commands may use them.
//! An external process deadline is still required for a stuck driver call.

use crate::compute::{ComputeError, ComputePipelineDescriptor};
use ash::{vk, Entry};
use serde::Serialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    ffi::{CStr, CString},
    fs::OpenOptions,
    io::Write,
    path::{Path, PathBuf},
    process::{Command, Stdio},
    sync::atomic::{AtomicU64, Ordering},
    time::{Duration, Instant},
};

#[derive(Debug, Clone, Copy)]
pub struct VulkanDeviceSelector {
    pub vendor_id: u32,
    pub device_id: u32,
}

#[derive(Debug, Clone)]
pub struct VulkanComputeConfig {
    pub selector: VulkanDeviceSelector,
    /// Trusted, public Khronos SPIRV-Tools executable; not fetched by this crate.
    pub spirv_validator: PathBuf,
    /// 1 ns..5 s. This bounds fence waiting, not every driver function.
    pub fence_timeout: Duration,
}

#[derive(Debug, Clone, Serialize)]
pub struct VulkanDeviceInfo {
    pub vendor_id: u32,
    pub device_id: u32,
    pub name: String,
    pub device_type: String,
    pub api_version: u32,
    pub queue_family: u32,
    pub robust_buffer_access: bool,
}

pub struct VulkanComputeBackend {
    config: VulkanComputeConfig,
    info: VulkanDeviceInfo,
    session: Option<Session>,
}

fn invalid(message: impl Into<String>) -> ComputeError {
    ComputeError::Unsupported(message.into())
}
fn driver(error: vk::Result) -> ComputeError {
    ComputeError::Generic(format!("Vulkan {error:?}"))
}

impl VulkanComputeBackend {
    pub fn new(mut config: VulkanComputeConfig) -> Result<Self, ComputeError> {
        if config.selector.vendor_id == 0
            || config.selector.device_id == 0
            || config.fence_timeout.is_zero()
            || config.fence_timeout > Duration::from_secs(5)
        {
            return Err(invalid(
                "explicit nonzero device IDs and fence timeout in (0, 5s] required",
            ));
        }
        config.spirv_validator = config
            .spirv_validator
            .canonicalize()
            .map_err(|e| invalid(format!("spirv-val path: {e}")))?;
        if !config.spirv_validator.is_file() {
            return Err(invalid("spirv-val must be a regular executable file"));
        }
        let session = Session::new(config.selector)?;
        let info = session.info.clone();
        Ok(Self {
            config,
            info,
            session: Some(session),
        })
    }

    pub fn device_info(&self) -> &VulkanDeviceInfo {
        &self.info
    }

    pub(crate) fn dispatch(
        &mut self,
        descriptor: &ComputePipelineDescriptor,
        groups: [u32; 3],
        views: &[(u32, Vec<u8>)],
    ) -> Result<Vec<Vec<u8>>, ComputeError> {
        let session = self
            .session
            .as_mut()
            .ok_or_else(|| invalid("Vulkan backend poisoned by unresolved submission"))?;
        let shader = inspect_spirv(&descriptor.shader.bytecode, &descriptor.shader.entry_point)?;
        if shader.local_size != descriptor.workgroup_size {
            return Err(invalid(
                "descriptor workgroup size differs from SPIR-V LocalSize",
            ));
        }
        let declared: BTreeSet<_> = descriptor
            .buffer_bindings
            .iter()
            .map(|binding| binding.binding)
            .collect();
        if shader.bindings != declared {
            return Err(invalid(
                "descriptor bindings differ from SPIR-V storage variables",
            ));
        }
        session.validate_limits(descriptor, groups)?;
        validate_module(&self.config.spirv_validator, &descriptor.shader.bytecode)?;
        let result = session.execute(
            &shader.words,
            &descriptor.shader.entry_point,
            groups,
            views,
            self.config.fence_timeout,
        );
        if session.in_flight {
            // Session::drop intentionally retains device objects and the loader.
            self.session.take();
        }
        result
    }
}

struct ShaderProfile {
    words: Vec<u32>,
    local_size: [u32; 3],
    bindings: BTreeSet<u32>,
}

/// Contract reflection, not a replacement for SPIRV-Tools semantic validation.
/// Opcodes/enumerants follow Khronos SPIRV-Headers unified1 grammar.
fn inspect_spirv(bytes: &[u8], requested_entry: &str) -> Result<ShaderProfile, ComputeError> {
    if !(20..=64 * 1024).contains(&bytes.len())
        || bytes.len() % 4 != 0
        || requested_entry.is_empty()
        || requested_entry.len() > 64
        || !requested_entry
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_')
    {
        return Err(invalid("SPIR-V byte/entry-point bounds"));
    }
    let words: Vec<_> = bytes
        .chunks_exact(4)
        .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
        .collect();
    if words[0] != 0x0723_0203
        || !matches!(
            words[1],
            0x0001_0000 | 0x0001_0100 | 0x0001_0200 | 0x0001_0300
        )
        || words[3] == 0
        || words[3] > 1_000_000
        || words[4] != 0
    {
        return Err(invalid("SPIR-V header/version"));
    }
    let mut entry = None;
    let mut local = None;
    let mut model = false;
    let mut capability = false;
    let (mut bindings, mut sets, mut pointers, mut structures, mut block_types) = (
        BTreeMap::new(),
        BTreeMap::new(),
        BTreeMap::new(),
        BTreeSet::new(),
        BTreeSet::new(),
    );
    let mut variables = Vec::new();
    let (mut constants, mut composites) = (BTreeMap::new(), BTreeMap::new());
    let mut workgroup_builtin = None;
    let mut at = 5;
    while at < words.len() {
        let count = (words[at] >> 16) as usize;
        let opcode = words[at] & 0xffff;
        if count == 0 || count > words.len() - at {
            return Err(invalid("truncated SPIR-V instruction"));
        }
        let instruction = &words[at..at + count];
        match opcode {
            10 | 25..=27 | 48..=52 | 331 => {
                return Err(invalid("unsupported SPIR-V extension/image/specialization"))
            }
            14 => {
                if instruction != [0x0003_000e, 0, 1] || model {
                    return Err(invalid("require one Logical/GLSL450 memory model"));
                }
                model = true;
            }
            15 => {
                if count < 4 || instruction[1] != 5 || entry.is_some() {
                    return Err(invalid("require one GLCompute entry point"));
                }
                let encoded: Vec<u8> = instruction[3..]
                    .iter()
                    .flat_map(|v| v.to_le_bytes())
                    .collect();
                let end = encoded
                    .iter()
                    .position(|b| *b == 0)
                    .ok_or_else(|| invalid("unterminated entry point"))?;
                if &encoded[..end] != requested_entry.as_bytes() {
                    return Err(invalid("SPIR-V entry point mismatch"));
                }
                entry = Some(instruction[2]);
            }
            16 => {
                if count != 6 || instruction[2] != 17 || local.is_some() {
                    return Err(invalid("only literal LocalSize execution mode supported"));
                }
                local = Some((
                    instruction[1],
                    [instruction[3], instruction[4], instruction[5]],
                ));
            }
            17 => {
                if count != 2 || instruction[1] != 1 || capability {
                    return Err(invalid("only Shader capability supported"));
                }
                capability = true;
            }
            21 | 22 => {
                if count < 3 || instruction[2] != 32 {
                    return Err(invalid("only 32-bit shader numeric types supported"));
                }
            }
            30 if count >= 2 => {
                structures.insert(instruction[1]);
            }
            32 if count == 4 => {
                pointers.insert(instruction[1], (instruction[2], instruction[3]));
            }
            43 if count == 4 => {
                constants.insert(instruction[2], instruction[3]);
            }
            44 if count == 6 => {
                composites.insert(
                    instruction[2],
                    [instruction[3], instruction[4], instruction[5]],
                );
            }
            59 => {
                if count < 4 {
                    return Err(invalid("truncated OpVariable"));
                }
                match instruction[3] {
                    12 => variables.push((instruction[1], instruction[2])),
                    1 | 6 | 7 => {} // Input/Private/Function: no descriptors or shared storage.
                    _ => return Err(invalid("unsupported shader storage class")),
                }
            }
            71 => {
                if count < 3 {
                    return Err(invalid("truncated OpDecorate"));
                }
                match instruction[2] {
                    2 => {
                        block_types.insert(instruction[1]);
                    }
                    11 if count == 4 && instruction[3] == 25 => {
                        if workgroup_builtin.replace(instruction[1]).is_some() {
                            return Err(invalid("duplicate WorkgroupSize builtin"));
                        }
                    }
                    33 | 34 => {
                        if count != 4 {
                            return Err(invalid("invalid descriptor decoration"));
                        }
                        let map = if instruction[2] == 33 {
                            &mut bindings
                        } else {
                            &mut sets
                        };
                        if map.insert(instruction[1], instruction[3]).is_some() {
                            return Err(invalid("duplicate descriptor decoration"));
                        }
                    }
                    _ => {}
                }
            }
            // Decoration groups could hide resource bindings from this profile.
            73..=75 => return Err(invalid("SPIR-V decoration groups unsupported")),
            _ => {}
        }
        at += count;
    }
    let (entry_id, local_size) = local.ok_or_else(|| invalid("missing literal LocalSize"))?;
    if !model || !capability || entry != Some(entry_id) || local_size.contains(&0) {
        return Err(invalid("incomplete SPIR-V compute profile"));
    }
    // WorkgroupSize can override LocalSize in SPIR-V. Accept only a literal
    // constant vector equal to LocalSize, so device-limit checks remain exact.
    if let Some(builtin) = workgroup_builtin {
        let ids = composites
            .get(&builtin)
            .ok_or_else(|| invalid("WorkgroupSize must be a literal constant vector"))?;
        for i in 0..3 {
            if constants.get(&ids[i]) != Some(&local_size[i]) {
                return Err(invalid("WorkgroupSize builtin differs from LocalSize"));
            }
        }
    }
    let mut found = BTreeSet::new();
    for (pointer_type, id) in variables {
        let (storage, structure) = pointers
            .get(&pointer_type)
            .ok_or_else(|| invalid("missing storage pointer type"))?;
        if *storage != 12 || !structures.contains(structure) || !block_types.contains(structure) {
            return Err(invalid(
                "storage descriptor must point to a Block struct, not an array",
            ));
        }
        let binding = *bindings
            .get(&id)
            .ok_or_else(|| invalid("missing storage Binding"))?;
        if sets.get(&id) != Some(&0) || !found.insert(binding) {
            return Err(invalid(
                "storage descriptors require unique bindings in set zero",
            ));
        }
    }
    if found.is_empty() || found.len() != bindings.len() || found.len() != sets.len() {
        return Err(invalid("unreflected/empty descriptor bindings"));
    }
    Ok(ShaderProfile {
        words,
        local_size,
        bindings: found,
    })
}

struct TemporaryModule(PathBuf);
impl Drop for TemporaryModule {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.0);
    }
}

fn validate_module(validator: &Path, bytes: &[u8]) -> Result<(), ComputeError> {
    static NEXT: AtomicU64 = AtomicU64::new(1);
    let path = std::env::temp_dir().join(format!(
        "nextcore-spv-{}-{}.spv",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    let mut options = OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let mut file = options
        .open(&path)
        .map_err(|e| invalid(format!("validator input: {e}")))?;
    let temporary = TemporaryModule(path);
    file.write_all(bytes)
        .map_err(|e| invalid(format!("validator input write: {e}")))?;
    drop(file);
    // No pipe can fill and stall the parent; shader and diagnostic sizes are not
    // used as an unbounded host allocation. The executable is a trusted tool.
    let mut child = Command::new(validator)
        .args(["--target-env", "vulkan1.1"])
        .arg(&temporary.0)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| invalid(format!("spirv-val spawn: {e}")))?;
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                return if status.success() {
                    Ok(())
                } else {
                    Err(invalid(format!("spirv-val rejected module ({status})")))
                }
            }
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(5)),
            result => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(invalid(format!(
                    "spirv-val deadline/wait failure: {result:?}"
                )));
            }
        }
    }
}

#[derive(Default)]
struct Resources {
    buffers: Vec<(vk::Buffer, vk::DeviceMemory)>,
    shader: vk::ShaderModule,
    descriptor_layout: vk::DescriptorSetLayout,
    pipeline_layout: vk::PipelineLayout,
    pipeline: vk::Pipeline,
    descriptor_pool: vk::DescriptorPool,
    command_pool: vk::CommandPool,
    fence: vk::Fence,
}

struct Session {
    entry: Option<Entry>,
    instance: ash::Instance,
    device: Option<ash::Device>,
    memory: vk::PhysicalDeviceMemoryProperties,
    limits: vk::PhysicalDeviceLimits,
    queue: vk::Queue,
    info: VulkanDeviceInfo,
    resources: Resources,
    in_flight: bool,
}

impl Session {
    fn new(selector: VulkanDeviceSelector) -> Result<Self, ComputeError> {
        // SAFETY: runtime Vulkan loader is explicitly supplied by the host.
        let entry = unsafe { Entry::load() }.map_err(|e| invalid(format!("Vulkan loader: {e}")))?;
        let app_name = c"Nextcore host compute";
        let application = vk::ApplicationInfo::default()
            .application_name(app_name)
            .api_version(vk::API_VERSION_1_1);
        let create = vk::InstanceCreateInfo::default().application_info(&application);
        let instance = unsafe { entry.create_instance(&create, None) }.map_err(driver)?;
        let mut session = Self {
            entry: Some(entry),
            instance,
            device: None,
            memory: Default::default(),
            limits: Default::default(),
            queue: vk::Queue::null(),
            info: VulkanDeviceInfo {
                vendor_id: selector.vendor_id,
                device_id: selector.device_id,
                name: String::new(),
                device_type: String::new(),
                api_version: 0,
                queue_family: 0,
                robust_buffer_access: false,
            },
            resources: Resources::default(),
            in_flight: false,
        };
        let devices = unsafe { session.instance.enumerate_physical_devices() }.map_err(driver)?;
        let mut selected = None;
        for physical in devices {
            let properties = unsafe { session.instance.get_physical_device_properties(physical) };
            if properties.vendor_id != selector.vendor_id
                || properties.device_id != selector.device_id
            {
                continue;
            }
            if !matches!(
                properties.device_type,
                vk::PhysicalDeviceType::INTEGRATED_GPU | vk::PhysicalDeviceType::DISCRETE_GPU
            ) {
                return Err(invalid(
                    "selected Vulkan device is not an integrated/discrete GPU; CPU fallback denied",
                ));
            }
            if selected.is_some() {
                return Err(invalid("device selector is ambiguous"));
            }
            selected = Some((physical, properties));
        }
        let (physical, properties) = selected
            .ok_or_else(|| invalid("exact Vulkan vendor/device not found; fallback denied"))?;
        if properties.api_version < vk::API_VERSION_1_1 {
            return Err(invalid("Vulkan 1.1 physical device required"));
        }
        let features = unsafe { session.instance.get_physical_device_features(physical) };
        if features.robust_buffer_access == 0 {
            return Err(invalid("robustBufferAccess is required"));
        }
        let families = unsafe {
            session
                .instance
                .get_physical_device_queue_family_properties(physical)
        };
        let family = families
            .iter()
            .position(|f| f.queue_count > 0 && f.queue_flags.contains(vk::QueueFlags::COMPUTE))
            .ok_or_else(|| invalid("no compute queue"))? as u32;
        let priorities = [1.0f32];
        let queues = [vk::DeviceQueueCreateInfo::default()
            .queue_family_index(family)
            .queue_priorities(&priorities)];
        let enabled = vk::PhysicalDeviceFeatures::default().robust_buffer_access(true);
        let create = vk::DeviceCreateInfo::default()
            .queue_create_infos(&queues)
            .enabled_features(&enabled);
        let device =
            unsafe { session.instance.create_device(physical, &create, None) }.map_err(driver)?;
        session.queue = unsafe { device.get_device_queue(family, 0) };
        session.device = Some(device);
        session.memory = unsafe {
            session
                .instance
                .get_physical_device_memory_properties(physical)
        };
        session.limits = properties.limits;
        session.info = VulkanDeviceInfo {
            vendor_id: properties.vendor_id,
            device_id: properties.device_id,
            name: unsafe { CStr::from_ptr(properties.device_name.as_ptr()) }
                .to_string_lossy()
                .into_owned(),
            device_type: format!("{:?}", properties.device_type),
            api_version: properties.api_version,
            queue_family: family,
            robust_buffer_access: true,
        };
        Ok(session)
    }

    fn validate_limits(
        &self,
        descriptor: &ComputePipelineDescriptor,
        groups: [u32; 3],
    ) -> Result<(), ComputeError> {
        for i in 0..3 {
            if groups[i] > self.limits.max_compute_work_group_count[i]
                || descriptor.workgroup_size[i] > self.limits.max_compute_work_group_size[i]
            {
                return Err(invalid("compute dimensions exceed device limits"));
            }
        }
        let invocations: u64 = descriptor
            .workgroup_size
            .iter()
            .map(|v| *v as u64)
            .product();
        if invocations > self.limits.max_compute_work_group_invocations as u64
            || descriptor.buffer_bindings.len()
                > self.limits.max_per_stage_descriptor_storage_buffers as usize
            || descriptor.buffer_bindings.len()
                > self.limits.max_descriptor_set_storage_buffers as usize
            || descriptor
                .buffer_bindings
                .iter()
                .any(|b| b.size > self.limits.max_storage_buffer_range as u64)
        {
            return Err(invalid("compute invocation/storage limits exceeded"));
        }
        Ok(())
    }

    fn execute(
        &mut self,
        words: &[u32],
        entry_name: &str,
        groups: [u32; 3],
        views: &[(u32, Vec<u8>)],
        timeout: Duration,
    ) -> Result<Vec<Vec<u8>>, ComputeError> {
        self.cleanup();
        let result = self.execute_inner(words, entry_name, groups, views, timeout);
        if !self.in_flight {
            self.cleanup();
        }
        result
    }

    fn execute_inner(
        &mut self,
        words: &[u32],
        entry_name: &str,
        groups: [u32; 3],
        views: &[(u32, Vec<u8>)],
        timeout: Duration,
    ) -> Result<Vec<Vec<u8>>, ComputeError> {
        let device = self.device.as_ref().unwrap();
        // SAFETY throughout: objects share this device, commands are externally
        // synchronized by &mut self, bounds/profile were checked before entry.
        unsafe {
            for (_, bytes) in views {
                let create = vk::BufferCreateInfo::default()
                    .size(bytes.len() as u64)
                    .usage(vk::BufferUsageFlags::STORAGE_BUFFER)
                    .sharing_mode(vk::SharingMode::EXCLUSIVE);
                let buffer = device.create_buffer(&create, None).map_err(driver)?;
                self.resources
                    .buffers
                    .push((buffer, vk::DeviceMemory::null()));
                let requirements = device.get_buffer_memory_requirements(buffer);
                let memory_type = (0..self.memory.memory_type_count)
                    .find(|index| {
                        requirements.memory_type_bits & (1 << index) != 0
                            && self.memory.memory_types[*index as usize]
                                .property_flags
                                .contains(
                                    vk::MemoryPropertyFlags::HOST_VISIBLE
                                        | vk::MemoryPropertyFlags::HOST_COHERENT,
                                )
                    })
                    .ok_or_else(|| invalid("host-visible coherent storage memory unavailable"))?;
                let allocate = vk::MemoryAllocateInfo::default()
                    .allocation_size(requirements.size)
                    .memory_type_index(memory_type);
                let memory = device.allocate_memory(&allocate, None).map_err(driver)?;
                self.resources.buffers.last_mut().unwrap().1 = memory;
                device
                    .bind_buffer_memory(buffer, memory, 0)
                    .map_err(driver)?;
                let mapped = device
                    .map_memory(memory, 0, bytes.len() as u64, vk::MemoryMapFlags::empty())
                    .map_err(driver)?;
                std::ptr::copy_nonoverlapping(bytes.as_ptr(), mapped.cast::<u8>(), bytes.len());
                device.unmap_memory(memory);
            }
            let bindings: Vec<_> = views
                .iter()
                .map(|(binding, _)| {
                    vk::DescriptorSetLayoutBinding::default()
                        .binding(*binding)
                        .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                        .descriptor_count(1)
                        .stage_flags(vk::ShaderStageFlags::COMPUTE)
                })
                .collect();
            self.resources.descriptor_layout = device
                .create_descriptor_set_layout(
                    &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
                    None,
                )
                .map_err(driver)?;
            let layouts = [self.resources.descriptor_layout];
            self.resources.pipeline_layout = device
                .create_pipeline_layout(
                    &vk::PipelineLayoutCreateInfo::default().set_layouts(&layouts),
                    None,
                )
                .map_err(driver)?;
            self.resources.shader = device
                .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(words), None)
                .map_err(driver)?;
            let entry = CString::new(entry_name).map_err(|_| invalid("entry contains NUL"))?;
            let stage = vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::COMPUTE)
                .module(self.resources.shader)
                .name(&entry);
            let pipeline = vk::ComputePipelineCreateInfo::default()
                .stage(stage)
                .layout(self.resources.pipeline_layout);
            match device.create_compute_pipelines(vk::PipelineCache::null(), &[pipeline], None) {
                Ok(pipelines) => self.resources.pipeline = pipelines[0],
                Err((pipelines, error)) => {
                    for pipeline in pipelines {
                        if pipeline != vk::Pipeline::null() {
                            device.destroy_pipeline(pipeline, None);
                        }
                    }
                    return Err(driver(error));
                }
            }
            let pool_sizes = [vk::DescriptorPoolSize {
                ty: vk::DescriptorType::STORAGE_BUFFER,
                descriptor_count: views.len() as u32,
            }];
            self.resources.descriptor_pool = device
                .create_descriptor_pool(
                    &vk::DescriptorPoolCreateInfo::default()
                        .max_sets(1)
                        .pool_sizes(&pool_sizes),
                    None,
                )
                .map_err(driver)?;
            let descriptor = device
                .allocate_descriptor_sets(
                    &vk::DescriptorSetAllocateInfo::default()
                        .descriptor_pool(self.resources.descriptor_pool)
                        .set_layouts(&layouts),
                )
                .map_err(driver)?[0];
            let infos: Vec<_> = self
                .resources
                .buffers
                .iter()
                .zip(views)
                .map(|((buffer, _), (_, bytes))| {
                    [vk::DescriptorBufferInfo {
                        buffer: *buffer,
                        offset: 0,
                        range: bytes.len() as u64,
                    }]
                })
                .collect();
            let writes: Vec<_> = views
                .iter()
                .zip(&infos)
                .map(|((binding, _), info)| {
                    vk::WriteDescriptorSet::default()
                        .dst_set(descriptor)
                        .dst_binding(*binding)
                        .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                        .buffer_info(info)
                })
                .collect();
            device.update_descriptor_sets(&writes, &[]);
            self.resources.command_pool = device
                .create_command_pool(
                    &vk::CommandPoolCreateInfo::default()
                        .queue_family_index(self.info.queue_family),
                    None,
                )
                .map_err(driver)?;
            let command = device
                .allocate_command_buffers(
                    &vk::CommandBufferAllocateInfo::default()
                        .command_pool(self.resources.command_pool)
                        .level(vk::CommandBufferLevel::PRIMARY)
                        .command_buffer_count(1),
                )
                .map_err(driver)?[0];
            device
                .begin_command_buffer(
                    command,
                    &vk::CommandBufferBeginInfo::default()
                        .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
                )
                .map_err(driver)?;
            device.cmd_bind_pipeline(
                command,
                vk::PipelineBindPoint::COMPUTE,
                self.resources.pipeline,
            );
            device.cmd_bind_descriptor_sets(
                command,
                vk::PipelineBindPoint::COMPUTE,
                self.resources.pipeline_layout,
                0,
                &[descriptor],
                &[],
            );
            device.cmd_dispatch(command, groups[0], groups[1], groups[2]);
            let barriers: Vec<_> = self
                .resources
                .buffers
                .iter()
                .map(|(buffer, _)| {
                    vk::BufferMemoryBarrier::default()
                        .src_access_mask(vk::AccessFlags::SHADER_WRITE)
                        .dst_access_mask(vk::AccessFlags::HOST_READ)
                        .src_queue_family_index(vk::QUEUE_FAMILY_IGNORED)
                        .dst_queue_family_index(vk::QUEUE_FAMILY_IGNORED)
                        .buffer(*buffer)
                        .offset(0)
                        .size(vk::WHOLE_SIZE)
                })
                .collect();
            // Queue submission makes coherent host upload available to the GPU;
            // this barrier makes compute writes available to the host domain.
            device.cmd_pipeline_barrier(
                command,
                vk::PipelineStageFlags::COMPUTE_SHADER,
                vk::PipelineStageFlags::HOST,
                vk::DependencyFlags::empty(),
                &[],
                &barriers,
                &[],
            );
            device.end_command_buffer(command).map_err(driver)?;
            self.resources.fence = device
                .create_fence(&vk::FenceCreateInfo::default(), None)
                .map_err(driver)?;
            let commands = [command];
            let submit = [vk::SubmitInfo::default().command_buffers(&commands)];
            self.in_flight = true; // includes uncertain queue-submit error paths.
            device
                .queue_submit(self.queue, &submit, self.resources.fence)
                .map_err(driver)?;
            device.wait_for_fences(&[self.resources.fence], true, timeout.as_nanos() as u64).map_err(|error|
                ComputeError::Generic(format!("GPU completion unresolved ({error:?}); backend poisoned; in-flight resources retained")))?;
            self.in_flight = false;
            let mut results = Vec::with_capacity(views.len());
            for ((_, memory), (_, source)) in self.resources.buffers.iter().zip(views) {
                let mut bytes = vec![0u8; source.len()];
                let mapped = device
                    .map_memory(*memory, 0, bytes.len() as u64, vk::MemoryMapFlags::empty())
                    .map_err(driver)?;
                std::ptr::copy_nonoverlapping(mapped.cast::<u8>(), bytes.as_mut_ptr(), bytes.len());
                device.unmap_memory(*memory);
                results.push(bytes);
            }
            Ok(results)
        }
    }

    fn cleanup(&mut self) {
        if self.in_flight {
            return;
        }
        let Some(device) = &self.device else {
            return;
        };
        let resources = std::mem::take(&mut self.resources);
        unsafe {
            if resources.fence != vk::Fence::null() {
                device.destroy_fence(resources.fence, None);
            }
            if resources.command_pool != vk::CommandPool::null() {
                device.destroy_command_pool(resources.command_pool, None);
            }
            if resources.descriptor_pool != vk::DescriptorPool::null() {
                device.destroy_descriptor_pool(resources.descriptor_pool, None);
            }
            if resources.pipeline != vk::Pipeline::null() {
                device.destroy_pipeline(resources.pipeline, None);
            }
            if resources.pipeline_layout != vk::PipelineLayout::null() {
                device.destroy_pipeline_layout(resources.pipeline_layout, None);
            }
            if resources.descriptor_layout != vk::DescriptorSetLayout::null() {
                device.destroy_descriptor_set_layout(resources.descriptor_layout, None);
            }
            if resources.shader != vk::ShaderModule::null() {
                device.destroy_shader_module(resources.shader, None);
            }
            for (buffer, memory) in resources.buffers {
                device.destroy_buffer(buffer, None);
                if memory != vk::DeviceMemory::null() {
                    device.free_memory(memory, None);
                }
            }
        }
    }
}

impl Drop for Session {
    fn drop(&mut self) {
        if self.in_flight {
            // Skip all Vulkan destruction and retain the dynamic loader. Releasing
            // the outer Rust vectors only releases handle values, not GPU objects.
            if let Some(entry) = self.entry.take() {
                std::mem::forget(entry);
            }
            log::error!("unresolved Vulkan submission: GPU objects retained until process exit");
            return;
        }
        self.cleanup();
        unsafe {
            if let Some(device) = &self.device {
                device.destroy_device(None);
            }
            self.instance.destroy_instance(None);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    const SHADER: &[u8] = include_bytes!("../tests/fixtures/storage_transform.spv");

    #[test]
    fn authored_fixture_profile() {
        let profile = inspect_spirv(SHADER, "main").unwrap();
        assert_eq!(profile.local_size, [64, 1, 1]);
        assert_eq!(profile.bindings, BTreeSet::from([0]));
    }

    #[test]
    fn rejects_bad_header_truncation_entry_and_optional_capabilities() {
        assert!(inspect_spirv(&[], "main").is_err());
        assert!(inspect_spirv(&SHADER[..SHADER.len() - 1], "main").is_err());
        assert!(inspect_spirv(SHADER, "missing").is_err());
        let mut broken = SHADER.to_vec();
        broken[..4].fill(0);
        assert!(inspect_spirv(&broken, "main").is_err());
        let mut optional = SHADER.to_vec();
        optional[24..28].copy_from_slice(&11u32.to_le_bytes()); // first OpCapability Shader -> Int64
        assert!(inspect_spirv(&optional, "main").is_err());
    }

    #[test]
    fn rejects_nonzero_descriptor_set_and_conflicting_workgroup_builtin() {
        for modification in 0..2 {
            let mut words: Vec<_> = SHADER
                .chunks_exact(4)
                .map(|b| u32::from_le_bytes(b.try_into().unwrap()))
                .collect();
            let mut at = 5;
            let mut changed = false;
            while at < words.len() {
                let count = (words[at] >> 16) as usize;
                let opcode = words[at] & 0xffff;
                if modification == 0 && opcode == 71 && count == 4 && words[at + 2] == 34 {
                    words[at + 3] = 1;
                    changed = true;
                    break;
                }
                if modification == 1 && opcode == 43 && count == 4 && words[at + 3] == 64 {
                    words[at + 3] = 32;
                    changed = true;
                    break;
                }
                at += count;
            }
            assert!(changed);
            let bytes: Vec<u8> = words.into_iter().flat_map(u32::to_le_bytes).collect();
            assert!(inspect_spirv(&bytes, "main").is_err());
        }
    }
}
