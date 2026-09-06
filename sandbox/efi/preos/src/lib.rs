//! EFI-integrated, allocation-free Venfire micro-preOS.
//!
//! This crate is a `no_std` static library.  It cannot create an EFI image,
//! owns no firmware pointer, and never accesses the C-private JIT structures.

#![no_std]

use core::ffi::c_void;
use core::mem::{align_of, size_of};
use core::ptr;

mod machine;
use machine::VfMachine;

const ABI_VERSION: u32 = 1;
const MACHINE_PROFILE_M1_DIAGNOSTIC: u32 = 0x4d31_4430;
const MAX_GUEST_BYTES: u64 = 65_536;
const FIXED_GUEST_RAM_BYTES: u64 = 65_536;
const MAX_EXECUTION_BUDGET: u64 = 100_000;

const OK: i32 = 0;
const E_ABI: i32 = 1;
const E_CONTEXT: i32 = 2;
const E_PROFILE: i32 = 3;
const E_GUEST_INPUT: i32 = 4;
const E_MACHINE_INIT: i32 = 5;
const E_JIT: i32 = 6;
const E_BUDGET: i32 = 7;
const E_PROTECTION: i32 = 8;
const E_INTERNAL: i32 = 9;
const E_RESULT: i32 = 10;
const E_UNSUPPORTED: i32 = 11;

/* Context flags are intentionally split into an expectation bit and explicit
 * future CPU/system requests.  The current AArch64 translator supports only
 * its bounded base subset.  A caller asking for exception-level state, an
 * MMU/TLB, atomics, SMP, timers, or PAuth is rejected before the JIT is
 * entered; it is never silently treated as ordinary user-mode code. */
const FLAG_EXPECT_GOLDEN_RESULT: u32 = 0x0000_0001;
const FLAG_REQUEST_EXCEPTION_MODEL: u32 = 0x0000_0100;
const FLAG_REQUEST_PRIVILEGED_STATE: u32 = 0x0000_0200;
const FLAG_REQUEST_SYSTEM_REGISTERS: u32 = 0x0000_0400;
const FLAG_REQUEST_MMU: u32 = 0x0000_0800;
const FLAG_REQUEST_TLB: u32 = 0x0000_1000;
const FLAG_REQUEST_ATOMICS: u32 = 0x0000_2000;
const FLAG_REQUEST_SMP: u32 = 0x0000_4000;
const FLAG_REQUEST_TIMER: u32 = 0x0000_8000;
const FLAG_REQUEST_PAUTH: u32 = 0x0001_0000;
const REQUESTED_UNSUPPORTED_FEATURES: u32 = FLAG_REQUEST_EXCEPTION_MODEL
    | FLAG_REQUEST_PRIVILEGED_STATE
    | FLAG_REQUEST_SYSTEM_REGISTERS
    | FLAG_REQUEST_MMU
    | FLAG_REQUEST_TLB
    | FLAG_REQUEST_ATOMICS
    | FLAG_REQUEST_SMP
    | FLAG_REQUEST_TIMER
    | FLAG_REQUEST_PAUTH;
const KNOWN_FLAGS: u32 = FLAG_EXPECT_GOLDEN_RESULT | REQUESTED_UNSUPPORTED_FEATURES;

const TERMINATION_NONE: u32 = 0;
const TERMINATION_HALT: u32 = 1;
const TERMINATION_BAD_INSTRUCTION: u32 = 2;
const TERMINATION_FETCH_FAULT: u32 = 3;
const TERMINATION_DATA_FAULT: u32 = 4;
const TERMINATION_BUDGET_EXHAUSTED: u32 = 5;
const TERMINATION_PROTECTION_FAILURE: u32 = 6;
const TERMINATION_CODE_BUFFER_FULL: u32 = 7;
const TERMINATION_WRAPPER_REJECTED: u32 = 8;
const TERMINATION_INTERNAL: u32 = 9;
const TERMINATION_UNSUPPORTED: u32 = 10;

type TraceFn = unsafe extern "C" fn(*const u8, *mut c_void);

#[repr(C)]
pub struct VfPreosContext {
    abi_version: u32,
    struct_size: u32,
    machine_profile: u32,
    flags: u32,
    execution_budget: u64,
    guest_bytes: *const u8,
    guest_size: u64,
    guest_ram: *mut u8,
    guest_ram_size: u64,
    opaque_execution_handle: *mut c_void,
    trace: Option<TraceFn>,
    trace_opaque: *mut c_void,
    expected_x1: u64,
    expected_x3: u64,
    expected_ram_offset: u64,
    expected_ram_qword: u64,
    expected_retired: u64,
    expected_guest_pc: u64,
    reserved: [u64; 3],
}

#[repr(C)]
pub struct VfJitRequest {
    abi_version: u32,
    struct_size: u32,
    machine_profile: u32,
    flags: u32,
    execution_budget: u64,
    guest_bytes: *const u8,
    guest_size: u64,
    guest_ram: *mut u8,
    guest_ram_size: u64,
    opaque_execution_handle: *mut c_void,
    reserved: [u64; 3],
}

#[repr(C)]
pub struct VfJitResult {
    abi_version: u32,
    struct_size: u32,
    jit_status: i32,
    termination_reason: u32,
    retired_instruction_count: u64,
    guest_pc: u64,
    fault_instruction: u32,
    reserved0: u32,
    result_x0: u64,
    result_x1: u64,
    result_x3: u64,
    reserved: [u64; 3],
}

#[repr(C)]
pub struct VfPreosResult {
    abi_version: u32,
    struct_size: u32,
    code: i32,
    termination_reason: u32,
    retired_instruction_count: u64,
    guest_pc: u64,
    fault_instruction: u32,
    reserved0: u32,
    result_x0: u64,
    result_x1: u64,
    result_x3: u64,
    reserved: [u64; 3],
}

const _: [(); 152] = [(); size_of::<VfPreosContext>()];
const _: [(); 8] = [(); align_of::<VfPreosContext>()];
const _: [(); 16] = [(); core::mem::offset_of!(VfPreosContext, execution_budget)];
const _: [(); 24] = [(); core::mem::offset_of!(VfPreosContext, guest_bytes)];
const _: [(); 40] = [(); core::mem::offset_of!(VfPreosContext, guest_ram)];
const _: [(); 56] = [(); core::mem::offset_of!(VfPreosContext, opaque_execution_handle)];
const _: [(); 64] = [(); core::mem::offset_of!(VfPreosContext, trace)];
const _: [(); 80] = [(); core::mem::offset_of!(VfPreosContext, expected_x1)];
const _: [(); 128] = [(); core::mem::offset_of!(VfPreosContext, reserved)];
const _: [(); 88] = [(); size_of::<VfJitRequest>()];
const _: [(); 8] = [(); align_of::<VfJitRequest>()];
const _: [(); 56] = [(); core::mem::offset_of!(VfJitRequest, opaque_execution_handle)];
const _: [(); 88] = [(); size_of::<VfJitResult>()];
const _: [(); 8] = [(); align_of::<VfJitResult>()];
const _: [(); 88] = [(); size_of::<VfPreosResult>()];
const _: [(); 8] = [(); align_of::<VfPreosResult>()];
const _: [(); 48] = [(); core::mem::offset_of!(VfPreosResult, result_x1)];

#[cfg(not(test))]
extern "C" {
    fn vf_preos_jit_execute(request: *const VfJitRequest, result: *mut VfJitResult) -> i32;
    fn vf_preos_abort() -> !;
}

#[cfg(test)]
unsafe extern "C" fn vf_preos_jit_execute(_: *const VfJitRequest, _: *mut VfJitResult) -> i32 {
    E_JIT
}

#[cfg(not(test))]
#[panic_handler]
fn panic(_: &core::panic::PanicInfo<'_>) -> ! {
    // All expected errors are checked below and returned explicitly.  A panic
    // is a defect path and is never allowed to unwind into C or EFI.
    unsafe { vf_preos_abort() }
}

fn zero_words(words: &[u64; 3]) -> bool {
    words[0] == 0 && words[1] == 0 && words[2] == 0
}

fn valid_span(pointer: *const u8, bytes: u64, minimum: u64, maximum: u64, alignment: usize) -> bool {
    if pointer.is_null()
        || bytes < minimum
        || bytes > maximum
        || alignment == 0
        || ((pointer as usize) & (alignment - 1)) != 0
        || bytes > usize::MAX as u64
    {
        return false;
    }
    (pointer as usize).checked_add(bytes as usize).is_some()
}

fn expected_result_fields_valid(context: &VfPreosContext) -> bool {
    if context.flags & !KNOWN_FLAGS != 0 {
        return false;
    }
    if context.flags & FLAG_EXPECT_GOLDEN_RESULT == 0 {
        return context.expected_x1 == 0
            && context.expected_x3 == 0
            && context.expected_ram_offset == 0
            && context.expected_ram_qword == 0
            && context.expected_retired == 0
            && context.expected_guest_pc == 0;
    }
    if context.flags & FLAG_EXPECT_GOLDEN_RESULT == 0 || (context.expected_ram_offset & 7) != 0 {
        return false;
    }
    context.expected_ram_offset <= context.guest_ram_size.saturating_sub(8)
}

fn validate_context(context: &VfPreosContext) -> i32 {
    if context.abi_version != ABI_VERSION
        || context.struct_size as usize != size_of::<VfPreosContext>()
        || !zero_words(&context.reserved)
    {
        return E_ABI;
    }
    if context.machine_profile != MACHINE_PROFILE_M1_DIAGNOSTIC {
        return E_PROFILE;
    }
    if context.flags & !KNOWN_FLAGS != 0 {
        return E_ABI;
    }
    if context.flags & REQUESTED_UNSUPPORTED_FEATURES != 0 {
        return E_UNSUPPORTED;
    }
    if context.execution_budget == 0 || context.execution_budget > MAX_EXECUTION_BUDGET {
        return E_CONTEXT;
    }
    if !valid_span(context.guest_bytes, context.guest_size, 4, MAX_GUEST_BYTES, 4)
        || (context.guest_size & 3) != 0
    {
        return E_GUEST_INPUT;
    }
    if !valid_span(
        context.guest_ram.cast_const(),
        context.guest_ram_size,
        FIXED_GUEST_RAM_BYTES,
        FIXED_GUEST_RAM_BYTES,
        8,
    )
        || context.opaque_execution_handle.is_null()
        || ((context.opaque_execution_handle as usize) & 7) != 0
        || context.trace.is_none()
        || !expected_result_fields_valid(context)
    {
        return E_CONTEXT;
    }
    OK
}

fn result_storage_valid(result: &VfPreosResult) -> bool {
    result.abi_version == ABI_VERSION
        && result.struct_size as usize == size_of::<VfPreosResult>()
        && result.code == 0
        && result.termination_reason == TERMINATION_NONE
        && result.retired_instruction_count == 0
        && result.guest_pc == 0
        && result.fault_instruction == 0
        && result.reserved0 == 0
        && result.result_x0 == 0
        && result.result_x1 == 0
        && result.result_x3 == 0
        && zero_words(&result.reserved)
}

fn empty_jit_result() -> VfJitResult {
    VfJitResult {
        abi_version: ABI_VERSION,
        struct_size: size_of::<VfJitResult>() as u32,
        jit_status: 0,
        termination_reason: TERMINATION_NONE,
        retired_instruction_count: 0,
        guest_pc: 0,
        fault_instruction: 0,
        reserved0: 0,
        result_x0: 0,
        result_x1: 0,
        result_x3: 0,
        reserved: [0; 3],
    }
}

unsafe fn trace(context: &VfPreosContext, message: *const u8) {
    if let Some(callback) = context.trace {
        callback(message, context.trace_opaque);
    }
}

unsafe fn assign_error(result: &mut VfPreosResult, code: i32, termination_reason: u32) {
    result.code = code;
    result.termination_reason = termination_reason;
}

unsafe fn trace_failure(context: &VfPreosContext, code: i32) {
    let message = match code {
        E_ABI => b"VF: PREOS_FAIL code=ABI\r\n\0".as_ptr(),
        E_CONTEXT => b"VF: PREOS_FAIL code=CONTEXT\r\n\0".as_ptr(),
        E_PROFILE => b"VF: PREOS_FAIL code=PROFILE\r\n\0".as_ptr(),
        E_GUEST_INPUT => b"VF: PREOS_FAIL code=GUEST_INPUT\r\n\0".as_ptr(),
        E_MACHINE_INIT => b"VF: PREOS_FAIL code=MACHINE_INIT\r\n\0".as_ptr(),
        E_BUDGET => b"VF: PREOS_FAIL code=BUDGET\r\n\0".as_ptr(),
        E_PROTECTION => b"VF: PREOS_FAIL code=PROTECTION\r\n\0".as_ptr(),
        E_RESULT => b"VF: PREOS_FAIL code=RESULT\r\n\0".as_ptr(),
        E_UNSUPPORTED => b"VF: PREOS_FAIL code=UNSUPPORTED\r\n\0".as_ptr(),
        E_INTERNAL => b"VF: PREOS_FAIL code=INTERNAL\r\n\0".as_ptr(),
        _ => b"VF: PREOS_FAIL code=JIT\r\n\0".as_ptr(),
    };
    trace(context, message);
}

unsafe fn copy_jit_result(destination: &mut VfPreosResult, source: &VfJitResult) {
    destination.termination_reason = source.termination_reason;
    destination.retired_instruction_count = source.retired_instruction_count;
    destination.guest_pc = source.guest_pc;
    destination.fault_instruction = source.fault_instruction;
    destination.result_x0 = source.result_x0;
    destination.result_x1 = source.result_x1;
    destination.result_x3 = source.result_x3;
}

unsafe fn trace_guest_stop(context: &VfPreosContext, reason: u32) {
    let message = match reason {
        TERMINATION_BAD_INSTRUCTION => b"VF: GUEST_STOP reason=BAD_INSTRUCTION\r\n\0".as_ptr(),
        TERMINATION_FETCH_FAULT => b"VF: GUEST_STOP reason=FETCH_FAULT\r\n\0".as_ptr(),
        TERMINATION_DATA_FAULT => b"VF: GUEST_STOP reason=DATA_FAULT\r\n\0".as_ptr(),
        TERMINATION_BUDGET_EXHAUSTED => b"VF: GUEST_STOP reason=BUDGET_EXHAUSTED\r\n\0".as_ptr(),
        TERMINATION_PROTECTION_FAILURE => b"VF: GUEST_STOP reason=PROTECTION\r\n\0".as_ptr(),
        TERMINATION_CODE_BUFFER_FULL => b"VF: GUEST_STOP reason=CODE_BUFFER_FULL\r\n\0".as_ptr(),
        TERMINATION_WRAPPER_REJECTED => b"VF: GUEST_STOP reason=WRAPPER_REJECTED\r\n\0".as_ptr(),
        _ => b"VF: GUEST_STOP reason=INTERNAL\r\n\0".as_ptr(),
    };
    trace(context, message);
}

fn code_for_termination(reason: u32) -> i32 {
    match reason {
        TERMINATION_BUDGET_EXHAUSTED => E_BUDGET,
        TERMINATION_PROTECTION_FAILURE => E_PROTECTION,
        TERMINATION_BAD_INSTRUCTION
        | TERMINATION_FETCH_FAULT
        | TERMINATION_DATA_FAULT
        | TERMINATION_CODE_BUFFER_FULL
        | TERMINATION_WRAPPER_REJECTED => E_JIT,
        TERMINATION_UNSUPPORTED => E_UNSUPPORTED,
        _ => E_INTERNAL,
    }
}

unsafe fn golden_result_matches(context: &VfPreosContext, result: &VfPreosResult) -> bool {
    if context.flags == 0 {
        return true;
    }
    let offset = context.expected_ram_offset as usize;
    let ram_value = ptr::read_unaligned(context.guest_ram.add(offset).cast::<u64>());
    result.result_x1 == context.expected_x1
        && result.result_x3 == context.expected_x3
        && ram_value == context.expected_ram_qword
        && result.retired_instruction_count == context.expected_retired
        && result.guest_pc == context.expected_guest_pc
}

/// The sole Rust entry point.  All input-dependent failures return a stable
/// `VF_PREOS_E_*` code; a caller must initialize the result as ABI v1 + zero.
#[no_mangle]
pub unsafe extern "C" fn vf_preos_run(
    context_pointer: *const VfPreosContext,
    result_pointer: *mut VfPreosResult,
) -> i32 {
    if result_pointer.is_null() || ((result_pointer as usize) & 7) != 0 {
        return E_CONTEXT;
    }
    let result = &mut *result_pointer;
    if !result_storage_valid(result) {
        return E_ABI;
    }
    if context_pointer.is_null() || ((context_pointer as usize) & 7) != 0 {
        assign_error(result, E_CONTEXT, TERMINATION_NONE);
        return E_CONTEXT;
    }
    let context = &*context_pointer;
    let validation = validate_context(context);
    if validation != OK {
        assign_error(result, validation, TERMINATION_NONE);
        if context.trace.is_some() {
            trace_failure(context, validation);
        }
        return validation;
    }

    trace(context, b"VF: RUST_ENTER\r\n\0".as_ptr());
    trace(context, b"VF: RUST_POLICY_OK\r\n\0".as_ptr());
    let mut machine = VfMachine::seed(context);
    machine.reset();
    trace(context, b"VF: MACHINE_RESET\r\n\0".as_ptr());
    if !machine.valid_seed() || !machine.valid_topology() {
        assign_error(result, E_MACHINE_INIT, TERMINATION_INTERNAL);
        trace_failure(context, E_MACHINE_INIT);
        return E_MACHINE_INIT;
    }
    trace(context, b"VF: MACHINE_READY\r\n\0".as_ptr());

    let request = VfJitRequest {
        abi_version: ABI_VERSION,
        struct_size: size_of::<VfJitRequest>() as u32,
        machine_profile: context.machine_profile,
        flags: 0,
        execution_budget: context.execution_budget,
        guest_bytes: context.guest_bytes,
        guest_size: context.guest_size,
        guest_ram: context.guest_ram,
        guest_ram_size: context.guest_ram_size,
        opaque_execution_handle: context.opaque_execution_handle,
        reserved: [0; 3],
    };
    let mut jit_result = empty_jit_result();
    trace(context, b"VF: JIT_ENTER\r\n\0".as_ptr());
    let wrapper_code = vf_preos_jit_execute(&request, &mut jit_result);
    copy_jit_result(result, &jit_result);
    machine.cpu.retired_instruction_count = jit_result.retired_instruction_count;
    machine.cpu.guest_pc = jit_result.guest_pc;
    machine.termination_reason.value = jit_result.termination_reason;
    result.retired_instruction_count = machine.cpu.retired_instruction_count;
    result.guest_pc = machine.cpu.guest_pc;
    result.termination_reason = machine.termination_reason.value;

    if wrapper_code != OK {
        let code = match wrapper_code {
            E_ABI => E_ABI,
            E_CONTEXT => E_CONTEXT,
            _ if jit_result.termination_reason == TERMINATION_PROTECTION_FAILURE => E_PROTECTION,
            _ => E_JIT,
        };
        assign_error(result, code, jit_result.termination_reason);
        trace_guest_stop(context, jit_result.termination_reason);
        trace_failure(context, code);
        return code;
    }
    if jit_result.termination_reason != TERMINATION_HALT {
        let code = code_for_termination(jit_result.termination_reason);
        assign_error(result, code, jit_result.termination_reason);
        trace_guest_stop(context, jit_result.termination_reason);
        trace_failure(context, code);
        return code;
    }
    if !golden_result_matches(context, result) {
        assign_error(result, E_RESULT, TERMINATION_HALT);
        trace_failure(context, E_RESULT);
        return E_RESULT;
    }

    result.code = OK;
    trace(context, b"VF: GUEST_HALT\r\n\0".as_ptr());
    trace(context, b"VF: RUST_RETURN_OK\r\n\0".as_ptr());
    OK
}

#[cfg(test)]
mod tests {
    use super::*;

    unsafe extern "C" fn test_trace(_: *const u8, _: *mut c_void) {}

    fn valid_context() -> VfPreosContext {
        VfPreosContext {
            abi_version: ABI_VERSION,
            struct_size: size_of::<VfPreosContext>() as u32,
            machine_profile: MACHINE_PROFILE_M1_DIAGNOSTIC,
            flags: 0,
            execution_budget: 100,
            guest_bytes: 0x1000 as *const u8,
            guest_size: 4,
            guest_ram: 0x2000 as *mut u8,
            guest_ram_size: FIXED_GUEST_RAM_BYTES,
            opaque_execution_handle: 0x3000 as *mut c_void,
            trace: Some(test_trace),
            trace_opaque: core::ptr::null_mut(),
            expected_x1: 0,
            expected_x3: 0,
            expected_ram_offset: 0,
            expected_ram_qword: 0,
            expected_retired: 0,
            expected_guest_pc: 0,
            reserved: [0; 3],
        }
    }

    #[test]
    fn abi_layout_is_fixed() {
        assert_eq!(size_of::<VfPreosContext>(), 152);
        assert_eq!(size_of::<VfJitRequest>(), 88);
        assert_eq!(size_of::<VfJitResult>(), 88);
        assert_eq!(size_of::<VfPreosResult>(), 88);
        assert_eq!(align_of::<VfJitRequest>(), 8);
        assert_eq!(align_of::<VfJitResult>(), 8);
        assert_eq!(core::mem::offset_of!(VfPreosContext, guest_ram), 40);
        assert_eq!(core::mem::offset_of!(VfJitRequest, opaque_execution_handle), 56);
        assert_eq!(core::mem::offset_of!(VfPreosResult, result_x1), 48);
    }

    #[test]
    fn valid_context_is_accepted() {
        assert_eq!(validate_context(&valid_context()), OK);
    }

    #[test]
    fn abi_and_reserved_fields_fail_closed() {
        let mut context = valid_context();
        context.abi_version += 1;
        assert_eq!(validate_context(&context), E_ABI);
        context = valid_context();
        context.reserved[1] = 1;
        assert_eq!(validate_context(&context), E_ABI);
    }

    #[test]
    fn profile_pointer_budget_and_alignment_fail_closed() {
        let mut context = valid_context();
        context.machine_profile = 0;
        assert_eq!(validate_context(&context), E_PROFILE);
        context = valid_context();
        context.execution_budget = MAX_EXECUTION_BUDGET + 1;
        assert_eq!(validate_context(&context), E_CONTEXT);
        context = valid_context();
        context.guest_bytes = 0x1001 as *const u8;
        assert_eq!(validate_context(&context), E_GUEST_INPUT);
        context = valid_context();
        context.guest_size = MAX_GUEST_BYTES + 4;
        assert_eq!(validate_context(&context), E_GUEST_INPUT);
        context = valid_context();
        context.opaque_execution_handle = 0x3001 as *mut c_void;
        assert_eq!(validate_context(&context), E_CONTEXT);
    }

    #[test]
    fn expectation_contract_is_checked() {
        let mut context = valid_context();
        context.flags = FLAG_EXPECT_GOLDEN_RESULT;
        context.expected_ram_offset = 16;
        assert_eq!(validate_context(&context), OK);
        context.expected_ram_offset = FIXED_GUEST_RAM_BYTES;
        assert_eq!(validate_context(&context), E_CONTEXT);
    }

    #[test]
    fn termination_mapping_preserves_failure_class() {
        assert_eq!(code_for_termination(TERMINATION_BUDGET_EXHAUSTED), E_BUDGET);
        assert_eq!(code_for_termination(TERMINATION_PROTECTION_FAILURE), E_PROTECTION);
        assert_eq!(code_for_termination(TERMINATION_BAD_INSTRUCTION), E_JIT);
        assert_eq!(code_for_termination(TERMINATION_INTERNAL), E_INTERNAL);
    }
}
