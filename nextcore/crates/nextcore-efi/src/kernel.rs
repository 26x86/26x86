#![no_std]
#![no_main]

extern crate alloc;

mod firmware_io;
mod loaded_kernel;
#[cfg(feature = "kernel-probe")]
mod transition32;

use alloc::format;
use firmware_io::{read_file, report};
use loaded_kernel::LoadedKernel;
use nextcore_core::{
    boot_config::parse_kernel_target,
    macho_image::{parse_macho_image, EntryKind},
};
use uefi::{cstr16, entry, CString16, Status};

const KERNEL_VA_BASE: u64 = 0xffff_ff80_0000_0000;
const LOW_PROFILE_END: u64 = 64 * 1024 * 1024;
const ARENA_PAGES: usize = 64;

#[global_allocator]
static ALLOCATOR: uefi::allocator::Allocator = uefi::allocator::Allocator;

#[entry]
fn efi_main() -> Status {
    uefi::helpers::init().expect("UEFI services initialization failed");
    report("NXKERNEL: EFI_ENTRY");
    match prepare() {
        Ok(()) => Status::SUCCESS,
        Err(status) => {
            report(&format!("NXKERNEL: ERROR status={status:?}"));
            status
        }
    }
}

fn prepare() -> Result<(), Status> {
    let config = read_file(cstr16!("\\EFI\\OC\\config.plist"), 1024 * 1024)?;
    let target = parse_kernel_target(&config).map_err(|error| {
        report(&format!("NXKERNEL: CONFIG_INVALID reason={error}"));
        Status::INVALID_PARAMETER
    })?;
    let path = CString16::try_from(target.path.as_str()).map_err(|_| Status::INVALID_PARAMETER)?;
    let source = read_file(&path, 64 * 1024 * 1024)?;
    let plan = parse_macho_image(&source).map_err(|error| {
        report(&format!("NXKERNEL: MACHO_INVALID reason={error}"));
        Status::LOAD_ERROR
    })?;
    if plan.entry_kind != EntryKind::UnixThread64 {
        report("NXKERNEL: PROFILE_UNSUPPORTED reason=ENTRY_KIND");
        return Err(Status::UNSUPPORTED);
    }
    // This profile is explicitly pinned in configuration. It is not inferred
    // from the Mach-O CPU type or a low-32-bit truncation of an arbitrary VA.
    let physical_base = plan
        .preferred_base
        .checked_sub(KERNEL_VA_BASE)
        .ok_or(Status::UNSUPPORTED)?;
    let physical_end = physical_base
        .checked_add(plan.image_size)
        .and_then(|end| end.checked_add((ARENA_PAGES * 4096) as u64))
        .ok_or(Status::UNSUPPORTED)?;
    if physical_base < 0x10_0000 || physical_end > LOW_PROFILE_END {
        return Err(Status::UNSUPPORTED);
    }
    let loaded = LoadedKernel::load_at(&plan, &source, physical_base, ARENA_PAGES)?;
    report(&format!(
        "NXKERNEL: IMAGE_PLACED base={:#x} entry={:#x} bytes={}",
        loaded.physical_base(),
        loaded.physical_entry(),
        loaded.image_size()
    ));

    #[cfg(not(feature = "kernel-probe"))]
    {
        // The production path requires real platform/entropy/runtime/DT and
        // exact target-build contracts before it may enter an operating system.
        report("NXKERNEL: PROVIDERS_PENDING");
        drop(loaded);
        Err(Status::NOT_READY)
    }
    #[cfg(feature = "kernel-probe")]
    {
        // This opt-in build is a controlled QEMU q35 test instrument. The
        // marker identifies our fixture; it is not a signature/authentication.
        const MARKER: &[u8] = b"NEXTCORE_AUTHORED_PSTART32_PROBE_V1";
        if !source.windows(MARKER.len()).any(|window| window == MARKER) {
            return Err(Status::UNSUPPORTED);
        }
        report("NXKERNEL: PROBE_ONLY");
        drop(plan);
        drop(source);
        drop(path);
        drop(config);
        run_probe(loaded, target.arguments)
    }
}

#[cfg(feature = "kernel-probe")]
fn run_probe(mut loaded: LoadedKernel, arguments: alloc::string::String) -> Result<(), Status> {
    use alloc::{string::String, vec};
    use core::mem::ManuallyDrop;
    use nextcore_core::{
        flat_dt::{self, FlatNode, FlatProperty},
        xnu_boot_args::{encode_boot_args, XnuBootArgsInput},
    };
    use uefi::{
        boot,
        mem::memory_map::{MemoryMap, MemoryType},
    };

    const DT: usize = 4096;
    const MAP: usize = DT + 8192;
    const MAP_CAP: usize = 65536;
    const TRAMPOLINE: usize = MAP + MAP_CAP;
    const STACK_TOP: usize = TRAMPOLINE + 4096 + 65536;
    transition32::preflight()?;
    let mut boot_line = arguments.as_bytes().to_vec();
    boot_line.push(0);
    let tree = FlatNode {
        name: String::new(),
        properties: vec![],
        children: vec![FlatNode {
            name: String::from("chosen"),
            properties: vec![FlatProperty {
                name: String::from("boot-args"),
                value: boot_line,
            }],
            children: vec![],
        }],
    };
    let dt = flat_dt::encode(&tree).map_err(|_| Status::INVALID_PARAMETER)?;
    flat_dt::validate(&dt).map_err(|_| Status::INVALID_PARAMETER)?;
    if dt.len() > MAP - DT || STACK_TOP > loaded.arena_size() {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    let base = loaded.physical_base();
    let size = loaded.image_size() + loaded.arena_size() as u64;
    let arena_base = base + loaded.image_size();
    let entry = u32::try_from(loaded.physical_entry()).map_err(|_| Status::UNSUPPORTED)?;
    let system_table = uefi::table::system_table_raw()
        .ok_or(Status::NOT_READY)?
        .as_ptr() as u64;
    let dt_size = dt.len() as u64;
    loaded.arena_bytes_mut()[DT..DT + dt.len()].copy_from_slice(&dt);
    transition32::copy_into(&mut loaded.arena_bytes_mut()[TRAMPOLINE..TRAMPOLINE + 4096])?;
    drop(dt);
    drop(tree);
    let mut command_line = [0u8; 1024];
    let command_len = arguments.len();
    if command_len >= command_line.len() {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    command_line[..command_len].copy_from_slice(arguments.as_bytes());
    drop(arguments);
    let command_line = core::str::from_utf8(&command_line[..command_len])
        .map_err(|_| Status::INVALID_PARAMETER)?;

    // Validate the complete ABI with a real map before the irreversible exit.
    // The final map is acquired again by the UEFI wrapper at ExitBootServices.
    let preview = boot::memory_map(MemoryType::LOADER_DATA).map_err(|e| e.status())?;
    let mut input = XnuBootArgsInput {
        memory_map_phys: arena_base + MAP as u64,
        memory_map_size: preview.meta().map_size as u64,
        memory_map_descriptor_size: preview.meta().desc_size as u32,
        memory_map_descriptor_version: preview.meta().desc_version,
        device_tree_phys: arena_base + DT as u64,
        device_tree_size: dt_size,
        kernel_phys: base,
        kernel_size: size,
        physical_memory_size: physical_ram(&preview).ok_or(Status::INVALID_PARAMETER)?,
        efi_system_table_phys: system_table,
        command_line,
    };
    if preview.meta().map_size > MAP_CAP || preview.meta().desc_size > u32::MAX as usize {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    encode_boot_args(&input).map_err(|_| Status::INVALID_PARAMETER)?;
    report(&format!(
        "NXKERNEL: HANDOFF_READY map_bytes={} stride={}",
        preview.meta().map_size,
        preview.meta().desc_size
    ));
    drop(preview);
    report("NXKERNEL: EXIT_BOOT_SERVICES");
    // The page owner must survive EBS. Neither allocation nor any destructor that
    // calls firmware is allowed on the path after this point.
    let mut loaded = ManuallyDrop::new(loaded);
    let final_map = unsafe { boot::exit_boot_services(None) };
    let meta = final_map.meta();
    if meta.map_size > MAP_CAP
        || meta.map_size > final_map.buffer().len()
        || meta.desc_size > u32::MAX as usize
    {
        post_exit_failure();
    }
    input.memory_map_size = meta.map_size as u64;
    input.memory_map_descriptor_size = meta.desc_size as u32;
    input.memory_map_descriptor_version = meta.desc_version;
    input.physical_memory_size = physical_ram(&final_map).unwrap_or_else(|| post_exit_failure());
    let encoded = encode_boot_args(&input).unwrap_or_else(|_| post_exit_failure());
    let arena = loaded.arena_bytes_mut();
    arena[..4096].copy_from_slice(&encoded);
    arena[MAP..MAP + meta.map_size].copy_from_slice(&final_map.buffer()[..meta.map_size]);
    // Controlled harness: q35 SMM off, no watchdog or injected NMI sources.
    // This does not establish a physical-machine interrupt/NMI transition.
    unsafe {
        transition32::enter(
            arena_base + TRAMPOLINE as u64,
            entry,
            arena_base as u32,
            (arena_base + STACK_TOP as u64) as u32,
        )
    }
}

#[cfg(feature = "kernel-probe")]
fn physical_ram(map: &impl uefi::mem::memory_map::MemoryMap) -> Option<u64> {
    use uefi::mem::memory_map::MemoryType as M;
    map.entries()
        .filter(|d| {
            matches!(
                d.ty,
                M::LOADER_CODE
                    | M::LOADER_DATA
                    | M::BOOT_SERVICES_CODE
                    | M::BOOT_SERVICES_DATA
                    | M::RUNTIME_SERVICES_CODE
                    | M::RUNTIME_SERVICES_DATA
                    | M::CONVENTIONAL
                    | M::UNUSABLE
                    | M::ACPI_RECLAIM
                    | M::ACPI_NON_VOLATILE
                    | M::PERSISTENT_MEMORY
            )
        })
        .try_fold(0u64, |sum, d| {
            sum.checked_add(d.page_count.checked_mul(4096)?)
        })
}

#[cfg(feature = "kernel-probe")]
fn post_exit_failure() -> ! {
    // Test-only QEMU failure signal; no firmware services after EBS.
    unsafe {
        core::arch::asm!("out dx, eax", in("dx") 0xf4u16, in("eax") 0x11u32, options(nomem, nostack));
    }
    loop {
        unsafe {
            core::arch::asm!("cli", "hlt", options(nomem, nostack));
        }
    }
}
