/* SPDX-License-Identifier: BSD-4-Clause
 * Native C/Rust ABI integration test.  It executes the real C wrapper and
 * existing JIT through the Rust staticlib; OVMF covers the EFI entry later.
 */
#define _GNU_SOURCE
#include "preos_bridge.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

static unsigned tests;
static unsigned trace_mask;

#define CHECK(expression) do { \
    ++tests; \
    if (!(expression)) { \
        fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #expression); \
        exit(1); \
    } \
} while (0)

static int protect_pages(void *pointer, size_t bytes, int executable, void *opaque) {
    (void)opaque;
    return mprotect(pointer, bytes, PROT_READ | (executable ? PROT_EXEC : PROT_WRITE));
}

static void trace(const char *message, void *opaque) {
    (void)opaque;
    if (!strcmp(message, "VF: RUST_ENTER\r\n")) trace_mask |= 1u << 0;
    if (!strcmp(message, "VF: RUST_POLICY_OK\r\n")) trace_mask |= 1u << 1;
    if (!strcmp(message, "VF: MACHINE_RESET\r\n")) trace_mask |= 1u << 2;
    if (!strcmp(message, "VF: MACHINE_READY\r\n")) trace_mask |= 1u << 3;
    if (!strcmp(message, "VF: JIT_ENTER\r\n")) trace_mask |= 1u << 4;
    if (!strcmp(message, "VF: GUEST_HALT\r\n")) trace_mask |= 1u << 5;
    if (!strcmp(message, "VF: RUST_RETURN_OK\r\n")) trace_mask |= 1u << 6;
    if (!strcmp(message, "VF: GUEST_STOP reason=BAD_INSTRUCTION\r\n")) trace_mask |= 1u << 7;
    if (!strcmp(message, "VF: GUEST_STOP reason=BUDGET_EXHAUSTED\r\n")) trace_mask |= 1u << 8;
}

static void zero_result(VF_PREOS_RESULT *result) {
    memset(result, 0, sizeof(*result));
    result->abi_version = VF_PREOS_ABI_VERSION;
    result->struct_size = sizeof(*result);
}

static VF_PREOS_CONTEXT make_context(vf_efi_execution *execution,
                                     const uint32_t *guest, uint64_t guest_words,
                                     uint64_t budget, uint32_t flags) {
    VF_PREOS_CONTEXT context;
    memset(&context, 0, sizeof(context));
    execution->guest_bytes = (const uint8_t *)guest;
    execution->guest_size = guest_words * sizeof(uint32_t);
    context.abi_version = VF_PREOS_ABI_VERSION;
    context.struct_size = sizeof(context);
    context.machine_profile = VF_MACHINE_PROFILE_M1_DIAGNOSTIC;
    context.flags = flags;
    context.execution_budget = budget;
    context.guest_bytes = execution->guest_bytes;
    context.guest_size = execution->guest_size;
    context.guest_ram = execution->guest_ram;
    context.guest_ram_size = execution->guest_ram_size;
    context.opaque_execution_handle = execution;
    context.trace = trace;
    return context;
}

int main(void) {
    const uint32_t golden[] = {
        0xd2800140, 0xd2800001, 0x8b000021, 0xd1000400,
        0xb5ffffc0, 0xf9000041, 0xf9400043, 0xd4400000,
    };
    const uint32_t bad_instruction[] = { 0xffffffff };
    const uint32_t bounded_loop[] = { 0x14000000 };
    vf_code code = {
        mmap(0, 16384, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0),
        16384,
        0,
    };
    uint8_t ram[65536] = {0};
    vf_cpu cpu = {0};
    vf_efi_execution execution = {
        .magic = VF_EFI_EXECUTION_MAGIC,
        .code = &code,
        .protect = protect_pages,
        .protection_opaque = 0,
        .guest_bytes = 0,
        .guest_size = 0,
        .guest_ram = ram,
        .guest_ram_size = sizeof(ram),
        .cpu = &cpu,
        .initial_x2 = 16,
        .machine_profile = VF_MACHINE_PROFILE_M1_DIAGNOSTIC,
        .reserved = 0,
    };
    VF_PREOS_CONTEXT context;
    VF_PREOS_RESULT result;

    CHECK(code.bytes != MAP_FAILED);
    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100,
                           VF_PREOS_EXPECT_GOLDEN_RESULT);
    context.expected_x1 = 55;
    context.expected_x3 = 55;
    context.expected_ram_offset = 16;
    context.expected_ram_qword = 55;
    context.expected_retired = 35;
    context.expected_guest_pc = 32;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_OK);
    CHECK(result.code == VF_PREOS_OK);
    CHECK(result.termination_reason == VF_TERMINATION_HALT);
    CHECK(result.result_x1 == 55 && result.result_x3 == 55);
    CHECK(result.retired_instruction_count == 35 && result.guest_pc == 32);
    CHECK(*(uint64_t *)(void *)(ram + 16) == 55);
    CHECK((trace_mask & 0x7fu) == 0x7fu);

    memset(ram, 0, sizeof(ram));
    execution.initial_x2 = 0;
    context = make_context(&execution, bad_instruction, 1, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_JIT);
    CHECK(result.code == VF_PREOS_E_JIT);
    CHECK(result.termination_reason == VF_TERMINATION_BAD_INSTRUCTION);
    CHECK(result.fault_instruction == 0xffffffff);
    CHECK((trace_mask & (1u << 7)) != 0);

    context = make_context(&execution, bounded_loop, 1, 7, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_BUDGET);
    CHECK(result.code == VF_PREOS_E_BUDGET);
    CHECK(result.termination_reason == VF_TERMINATION_BUDGET_EXHAUSTED);
    CHECK(result.retired_instruction_count == 7);
    CHECK((trace_mask & (1u << 8)) != 0);

    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100, 0);
    context.reserved[0] = 1;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_ABI);
    CHECK(result.code == VF_PREOS_E_ABI);

    /* Architectural system state is not silently interpreted by the Phase-1
     * user-mode subset.  The stable feature request is rejected before the
     * C wrapper/JIT boundary. */
    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100,
                           VF_PREOS_REQUEST_MMU);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.code == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.termination_reason == VF_TERMINATION_NONE);

    CHECK(protect_pages(code.bytes, code.capacity, 0, 0) == 0);
    CHECK(munmap(code.bytes, code.capacity) == 0);
    printf("{\"passed\":true,\"assertions\":%u,\"c_rust_abi_executed\":true,"
           "\"normal_halt\":true,\"bad_instruction\":true,\"budget_exhaustion\":true,"
           "\"unsupported_feature_gate\":true}\n", tests);
    return 0;
}
