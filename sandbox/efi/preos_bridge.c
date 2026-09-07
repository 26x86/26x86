/* SPDX-License-Identifier: BSD-4-Clause
 * C owns this boundary's firmware-facing execution capability.  Rust can ask
 * for an execution but cannot dereference the capability or access vf_run().
 */
#include "preos_bridge.h"

/*
 * Rust's Windows x64 ABI emits __chkstk before a large frame and expects RAX
 * (the requested frame size) to survive the call.  The EFI image is linked
 * without the MSVC CRT, so provide the small ABI shim here instead of pulling
 * in a general runtime.  It probes each page and restores the temporary stack
 * position before returning; the caller performs the actual `sub rsp, rax`.
 */
#if defined(__x86_64__)
__attribute__((naked, noinline)) void __chkstk(void) {
    __asm__ volatile(
        "pushq %rcx\n"
        "pushq %r10\n"
        "pushq %r11\n"
        "movq %rsp, %r11\n"
        "movq %rsp, %r10\n"
        "subq %rax, %r10\n"
        "andq $-4096, %r10\n"
        "1:\n"
        "cmpq %r10, %rsp\n"
        "jbe 2f\n"
        "subq $4096, %rsp\n"
        "movq (%rsp), %rcx\n"
        "jmp 1b\n"
        "2:\n"
        "movq %r11, %rsp\n"
        "popq %r11\n"
        "popq %r10\n"
        "popq %rcx\n"
        "retq\n");
}
#endif

static int zero_words(const uint64_t *words, size_t count) {
    if (!words) return 0;
    for (size_t i = 0; i < count; ++i) if (words[i]) return 0;
    return 1;
}

static int abi_prefix_valid(const void *pointer, size_t expected_size) {
    const uint32_t *words = pointer;
    return pointer && !((uintptr_t)pointer & 7) &&
           words[0] == VF_PREOS_ABI_VERSION && words[1] == expected_size;
}

static int valid_span(const void *pointer, uint64_t bytes, uint64_t minimum,
                      uint64_t maximum, uint64_t alignment) {
    uint64_t address = (uint64_t)(uintptr_t)pointer;
    if (!pointer || bytes < minimum || bytes > maximum || !alignment ||
        (address & (alignment - 1)) || address > UINT64_MAX - bytes) return 0;
    return 1;
}

static uint32_t termination_from_status(int status) {
    switch (status) {
    case VF_HALT: return VF_TERMINATION_HALT;
    case VF_BAD_INSTRUCTION: return VF_TERMINATION_BAD_INSTRUCTION;
    case VF_FETCH_FAULT: return VF_TERMINATION_FETCH_FAULT;
    case VF_DATA_FAULT: return VF_TERMINATION_DATA_FAULT;
    case VF_BUDGET: return VF_TERMINATION_BUDGET_EXHAUSTED;
    case VF_PROTECTION: return VF_TERMINATION_PROTECTION_FAILURE;
    case VF_UNDEFINED_INSTRUCTION: return VF_TERMINATION_UNDEFINED_INSTRUCTION;
    case VF_PRIVILEGE_FAULT: return VF_TERMINATION_PRIVILEGE_FAULT;
    case VF_TRANSLATION_FAULT: return VF_TERMINATION_TRANSLATION_FAULT;
    case VF_PERMISSION_FAULT: return VF_TERMINATION_PERMISSION_FAULT;
    case VF_ALIGNMENT_FAULT: return VF_TERMINATION_ALIGNMENT_FAULT;
    case VF_SYSTEM_REGISTER_TRAP: return VF_TERMINATION_SYSTEM_REGISTER_TRAP;
    case VF_TIMER_INTERRUPT: return VF_TERMINATION_TIMER_INTERRUPT;
    case VF_EXTERNAL_INTERRUPT: return VF_TERMINATION_EXTERNAL_INTERRUPT;
    case VF_INSTRUCTION_ABORT: return VF_TERMINATION_INSTRUCTION_ABORT;
    case VF_DATA_ABORT: return VF_TERMINATION_DATA_ABORT;
    case VF_CODE_FULL: return VF_TERMINATION_CODE_BUFFER_FULL;
    default: return VF_TERMINATION_INTERNAL;
    }
}

static int status_is_terminal(int status) {
    /* VF_NEXT is an internal continuation status and is not a valid result
     * crossing into Rust.  Returning it means the wrapper/JIT contract was
     * violated, not that the guest halted successfully. */
    return status >= VF_HALT && status <= VF_DATA_ABORT;
}

static int termination_is_valid(uint32_t reason) {
    return reason >= VF_TERMINATION_HALT && reason <= VF_TERMINATION_DATA_ABORT;
}

static int status_and_termination_match(int status, uint32_t reason) {
    switch (status) {
    case VF_HALT: return reason == VF_TERMINATION_HALT;
    case VF_BAD_INSTRUCTION: return reason == VF_TERMINATION_BAD_INSTRUCTION;
    case VF_FETCH_FAULT: return reason == VF_TERMINATION_FETCH_FAULT;
    case VF_DATA_FAULT: return reason == VF_TERMINATION_DATA_FAULT;
    case VF_BUDGET: return reason == VF_TERMINATION_BUDGET_EXHAUSTED;
    case VF_CODE_FULL: return reason == VF_TERMINATION_CODE_BUFFER_FULL;
    case VF_PROTECTION: return reason == VF_TERMINATION_PROTECTION_FAILURE;
    case VF_UNDEFINED_INSTRUCTION: return reason == VF_TERMINATION_UNDEFINED_INSTRUCTION;
    case VF_PRIVILEGE_FAULT: return reason == VF_TERMINATION_PRIVILEGE_FAULT;
    case VF_TRANSLATION_FAULT: return reason == VF_TERMINATION_TRANSLATION_FAULT;
    case VF_PERMISSION_FAULT: return reason == VF_TERMINATION_PERMISSION_FAULT;
    case VF_ALIGNMENT_FAULT: return reason == VF_TERMINATION_ALIGNMENT_FAULT;
    case VF_SYSTEM_REGISTER_TRAP: return reason == VF_TERMINATION_SYSTEM_REGISTER_TRAP;
    case VF_TIMER_INTERRUPT: return reason == VF_TERMINATION_TIMER_INTERRUPT;
    case VF_EXTERNAL_INTERRUPT: return reason == VF_TERMINATION_EXTERNAL_INTERRUPT;
    case VF_INSTRUCTION_ABORT: return reason == VF_TERMINATION_INSTRUCTION_ABORT;
    case VF_DATA_ABORT: return reason == VF_TERMINATION_DATA_ABORT;
    default: return 0;
    }
}

static int result_valid(const VF_JIT_RESULT *result) {
    return abi_prefix_valid(result, sizeof(*result)) &&
           result->struct_size == sizeof(*result) && !result->reserved0 &&
           zero_words(result->reserved, 3);
}

static int request_valid(const VF_JIT_REQUEST *request) {
    if (!abi_prefix_valid(request, sizeof(*request)) ||
        request->struct_size != sizeof(*request) ||
        request->machine_profile != VF_MACHINE_PROFILE_M1_DIAGNOSTIC ||
        request->flags || !zero_words(request->reserved, 3) ||
        !request->opaque_execution_handle ||
        ((uintptr_t)request->opaque_execution_handle & 7) || !request->execution_budget ||
        request->execution_budget > VF_PREOS_MAX_EXECUTION_BUDGET ||
        !valid_span(request->guest_bytes, request->guest_size, 4,
                    VF_PREOS_MAX_GUEST_BYTES, 4) || (request->guest_size & 3) ||
        !valid_span(request->guest_ram, request->guest_ram_size,
                    VF_PREOS_FIXED_GUEST_RAM_BYTES,
                    VF_PREOS_FIXED_GUEST_RAM_BYTES, 8)) return 0;
    return 1;
}

int VF_PREOS_ABI vf_preos_jit_execute(const VF_JIT_REQUEST *request, VF_JIT_RESULT *result) {
    vf_efi_execution *execution;
    int status;
    if (!result_valid(result)) return VF_PREOS_E_ABI;
    if (!request_valid(request)) {
        result->jit_status = VF_DATA_FAULT;
        result->termination_reason = VF_TERMINATION_WRAPPER_REJECTED;
        return VF_PREOS_E_CONTEXT;
    }
    execution = request->opaque_execution_handle;
    if (execution->magic != VF_EFI_EXECUTION_MAGIC || !execution->code ||
        !execution->protect || !execution->cpu || execution->reserved ||
        execution->machine_profile != request->machine_profile ||
        execution->guest_bytes != request->guest_bytes ||
        execution->guest_size != request->guest_size ||
        execution->guest_ram != request->guest_ram ||
        execution->guest_ram_size != request->guest_ram_size) {
        result->jit_status = VF_DATA_FAULT;
        result->termination_reason = VF_TERMINATION_WRAPPER_REJECTED;
        return VF_PREOS_E_CONTEXT;
    }
    vf_cpu_reset(execution->cpu, VF_EL0);
    execution->cpu->x[2] = execution->initial_x2;
    status = vf_run(execution->cpu, request->guest_bytes, (size_t)request->guest_size,
                    request->guest_ram, (size_t)request->guest_ram_size,
                    execution->code, request->execution_budget,
                    execution->protect, execution->protection_opaque);
    result->jit_status = status;
    result->termination_reason = termination_from_status(status);
    if (!status_is_terminal(status) ||
        !termination_is_valid(result->termination_reason) ||
        !status_and_termination_match(status, result->termination_reason)) {
        result->jit_status = VF_DATA_FAULT;
        result->termination_reason = VF_TERMINATION_WRAPPER_REJECTED;
        return VF_PREOS_E_INTERNAL;
    }
    result->retired_instruction_count = execution->cpu->retired;
    result->guest_pc = execution->cpu->pc;
    result->fault_instruction = execution->cpu->instruction;
    result->result_x0 = execution->cpu->x[0];
    result->result_x1 = execution->cpu->x[1];
    result->result_x3 = execution->cpu->x[3];
    return VF_PREOS_OK;
}

/* A Rust panic is a programming defect, not an EFI return path.  The runtime
 * has no input-triggered panic paths; this noreturn trap prevents unwinding
 * across the C/EFI boundary if an invariant is nevertheless violated. */
void VF_PREOS_ABI vf_preos_abort(void) {
#if defined(_WIN32)
    for (;;) __asm__ volatile("hlt");
#else
    __builtin_trap();
#endif
}
