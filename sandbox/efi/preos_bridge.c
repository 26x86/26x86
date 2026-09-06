/* SPDX-License-Identifier: BSD-4-Clause
 * C owns this boundary's firmware-facing execution capability.  Rust can ask
 * for an execution but cannot dereference the capability or access vf_run().
 */
#include "preos_bridge.h"

static void zero(void *memory, size_t bytes) {
    uint8_t *p = memory;
    while (bytes--) *p++ = 0;
}

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
    case VF_CODE_FULL: return VF_TERMINATION_CODE_BUFFER_FULL;
    default: return VF_TERMINATION_INTERNAL;
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
    zero(execution->cpu, sizeof(*execution->cpu));
    execution->cpu->x[2] = execution->initial_x2;
    status = vf_run(execution->cpu, request->guest_bytes, (size_t)request->guest_size,
                    request->guest_ram, (size_t)request->guest_ram_size,
                    execution->code, request->execution_budget,
                    execution->protect, execution->protection_opaque);
    result->jit_status = status;
    result->termination_reason = termination_from_status(status);
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
