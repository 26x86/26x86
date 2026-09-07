//! Independent IA-32e -> protected-mode transition, for the explicit pstart32 ABI.
//! Intel SDM vol. 3, switching between paging modes; XNU source pin is in BP11.
use core::{
    arch::{asm, global_asm},
    ptr,
};
use uefi::Status;

global_asm!(
    r#"
.section .text
.p2align 4
.global nx_transition_start
.global nx_transition_end
.code64
nx_transition_start:
    cli
    cld
    mov esi, ecx
    mov edi, edx
    mov esp, r8d
    lea rax, [rip + nx_transition_gdt]
    mov [rip + nx_transition_gdtr + 2], rax
    lgdt [rip + nx_transition_gdtr]
    mov rax, cr4
    and eax, 0xffffff7f
    mov cr4, rax
    lea rax, [rip + nx_transition_compat]
    push 0x08
    push rax
    retfq
.code32
nx_transition_compat:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov fs, ax
    mov gs, ax
    mov eax, cr0
    and eax, 0x7fffffff
    mov cr0, eax
    mov ecx, 0xc0000080
    rdmsr
    and eax, 0xfffffeff
    wrmsr
    mov eax, cr4
    and eax, 0xffffffdf
    mov cr4, eax
    mov eax, edi
    xor ebp, ebp
    jmp esi
.p2align 3
nx_transition_gdt:
    .quad 0
    .quad 0x00cf9a000000ffff
    .quad 0x00cf92000000ffff
nx_transition_gdtr:
    .word 23
    .quad 0
nx_transition_end:
.code64
"#
);

extern "C" {
    static nx_transition_start: u8;
    static nx_transition_end: u8;
}

/// Check mode features whose state this first transition profile can preserve.
pub fn preflight() -> Result<(), Status> {
    let cr0: u64;
    let cr4: u64;
    let cs: u16;
    unsafe {
        asm!("mov {}, cr0", out(reg) cr0, options(nomem, nostack, preserves_flags));
        asm!("mov {}, cr4", out(reg) cr4, options(nomem, nostack, preserves_flags));
        asm!("mov {0:x}, cs", out(reg) cs, options(nomem, nostack, preserves_flags));
    }
    // Five-level paging, PCID and CET need their own transition contract.
    if cr0 & 0x8000_0001 != 0x8000_0001
        || cs & 3 != 0
        || cr4 & ((1 << 12) | (1 << 17) | (1 << 23)) != 0
    {
        return Err(Status::UNSUPPORTED);
    }
    Ok(())
}

pub fn copy_into(destination: &mut [u8]) -> Result<usize, Status> {
    let start = ptr::addr_of!(nx_transition_start);
    let end = ptr::addr_of!(nx_transition_end);
    let size = (end as usize)
        .checked_sub(start as usize)
        .ok_or(Status::LOAD_ERROR)?;
    if size == 0 || size > destination.len() || size > 4096 {
        return Err(Status::BAD_BUFFER_SIZE);
    }
    // All internal references are relative within this copied blob. The GDTR
    // base is computed from RIP after entering its low, identity-mapped copy.
    unsafe {
        ptr::copy_nonoverlapping(start, destination.as_mut_ptr(), size);
    }
    Ok(size)
}

/// Caller must have exited Boot Services, retained all input allocations and
/// ensured the trampoline/stack have identical linear and physical addresses.
/// All NMI sources must be quiesced externally throughout this transition:
/// CLI does not mask NMI and the firmware IDT is not a valid legacy-mode IDT.
/// The only current caller is the controlled q35, SMM-off authored probe.
/// Physical-machine use needs a platform-specific interrupt/NMI contract.
pub unsafe fn enter(trampoline: u64, entry: u32, args: u32, stack_top: u32) -> ! {
    let jump: unsafe extern "efiapi" fn(u64, u64, u64) -> ! =
        core::mem::transmute(trampoline as usize);
    jump(u64::from(entry), u64::from(args), u64::from(stack_top))
}
