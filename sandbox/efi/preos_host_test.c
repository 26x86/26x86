/* SPDX-License-Identifier: BSD-4-Clause
 * Native C/Rust ABI integration test.  It executes the real C wrapper and
 * existing JIT through the Rust staticlib; OVMF covers the EFI entry later.
 */
#define _GNU_SOURCE
#include "preos_bridge.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
typedef unsigned long DWORD;
#define MEM_COMMIT 0x1000
#define MEM_RESERVE 0x2000
#define MEM_RELEASE 0x8000
#define PAGE_READWRITE 0x04
#define PAGE_EXECUTE_READ 0x20
void *__stdcall VirtualAlloc(void *addr, size_t size, DWORD type, DWORD protect);
int __stdcall VirtualProtect(void *addr, size_t size, DWORD protect, DWORD *old);
int __stdcall VirtualFree(void *addr, size_t size, DWORD type);
static void *win_alloc(size_t n) { return VirtualAlloc(0,n,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE); }
static int win_perms(void *p,size_t n,int x,void *u) {
    (void)u;DWORD old;DWORD prot=x?PAGE_EXECUTE_READ:PAGE_READWRITE;
    return VirtualProtect(p,n,prot,&old)?0:-1;
}
static int win_free(void *p,size_t n) { (void)n;return VirtualFree(p,0,MEM_RELEASE)?0:-1; }
#define mmap(a,len,prot,flags,fd,off) win_alloc(len)
#define mprotect(p,n,prot) win_perms(p,n,(prot)&4,0)
#define munmap(p,n) win_free(p,n)
#define PROT_READ 1
#define PROT_WRITE 2
#define PROT_EXEC 4
#define MAP_PRIVATE 0
#define MAP_ANONYMOUS 0
#define MAP_FAILED ((void*)-1)
#else
#include <sys/mman.h>
#endif

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
    if (!strcmp(message, "VF: VMAPPLE_GRAPH_READY\r\n")) trace_mask |= 1u << 3;
    if (!strcmp(message, "VF: MACHINE_READY\r\n")) trace_mask |= 1u << 4;
    if (!strcmp(message, "VF: JIT_ENTER\r\n")) trace_mask |= 1u << 5;
    if (!strcmp(message, "VF: GUEST_HALT\r\n")) trace_mask |= 1u << 6;
    if (!strcmp(message, "VF: RUST_RETURN_OK\r\n")) trace_mask |= 1u << 7;
    if (!strcmp(message, "VF: GUEST_STOP reason=BAD_INSTRUCTION\r\n")) trace_mask |= 1u << 8;
    if (!strcmp(message, "VF: GUEST_STOP reason=BUDGET_EXHAUSTED\r\n")) trace_mask |= 1u << 9;
    if (!strcmp(message, "VF: GUEST_STOP reason=UNDEFINED_INSTRUCTION\r\n")) trace_mask |= 1u << 10;
    if (!strcmp(message, "VF: GUEST_STOP reason=PRIVILEGE_FAULT\r\n")) trace_mask |= 1u << 11;
    if (!strcmp(message, "VF: GUEST_STOP reason=SYSTEM_REGISTER_TRAP\r\n")) trace_mask |= 1u << 12;
    if (!strcmp(message, "VF: GUEST_STOP reason=INSTRUCTION_ABORT\r\n")) trace_mask |= 1u << 13;
    if (!strcmp(message, "VF: GUEST_STOP reason=DATA_ABORT\r\n")) trace_mask |= 1u << 14;
    if (!strcmp(message, "VF: GUEST_STOP reason=ALIGNMENT_FAULT\r\n")) trace_mask |= 1u << 15;
    if (!strcmp(message, "VF: M1_RUNTIME_ACTIVE\r\n")) trace_mask |= 1u << 16;
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
    CHECK((trace_mask & 0xffu) == 0xffu);

    memset(ram, 0, sizeof(ram));
    execution.initial_x2 = 0;
    context = make_context(&execution, bad_instruction, 1, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.code == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.termination_reason == VF_TERMINATION_UNDEFINED_INSTRUCTION);
    CHECK(result.fault_instruction == 0xffffffff);
    CHECK((trace_mask & (1u << 10)) != 0);

    /* The C JIT now classifies the architectural boundary before host-code
     * emission. Rust must preserve that class and must not normalize it to a
     * successful halt. These are EL0 diagnostic runs, so the privileged and
     * unimplemented system-register cases are intentionally fail-closed. */
    const uint32_t privileged[] = {0xd69f03e0};
    context = make_context(&execution, privileged, 1, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.code == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.termination_reason == VF_TERMINATION_PRIVILEGE_FAULT);
    CHECK(result.fault_instruction == privileged[0]);
    CHECK((trace_mask & (1u << 11)) != 0);

    const uint32_t system_register[] = {0xd53be000};
    context = make_context(&execution, system_register, 1, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.code == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.termination_reason == VF_TERMINATION_SYSTEM_REGISTER_TRAP);
    CHECK(result.fault_instruction == system_register[0]);
    CHECK((trace_mask & (1u << 12)) != 0);

    /* A taken branch past the guest span is an instruction abort, distinct
     * from an undefined opcode. */
    const uint32_t instruction_abort[] = {0x14000001};
    context = make_context(&execution, instruction_abort, 1, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_JIT);
    CHECK(result.code == VF_PREOS_E_JIT);
    CHECK(result.termination_reason == VF_TERMINATION_INSTRUCTION_ABORT);
    CHECK(result.retired_instruction_count == 1 && result.guest_pc == 4);
    CHECK((trace_mask & (1u << 13)) != 0);

    const uint32_t alignment_abort[] = {0xd2800021, 0xf9000020};
    context = make_context(&execution, alignment_abort, 2, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.code == VF_PREOS_E_UNSUPPORTED);
    CHECK(result.termination_reason == VF_TERMINATION_ALIGNMENT_FAULT);
    CHECK(result.retired_instruction_count == 1 && result.guest_pc == 4);
    CHECK(result.fault_instruction == alignment_abort[1]);
    CHECK((trace_mask & (1u << 15)) != 0);

    const uint32_t data_abort[] = {0xd2a00201, 0xf9000020};
    context = make_context(&execution, data_abort, 2, 16, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_JIT);
    CHECK(result.code == VF_PREOS_E_JIT);
    CHECK(result.termination_reason == VF_TERMINATION_DATA_ABORT);
    CHECK(result.retired_instruction_count == 1 && result.guest_pc == 4);
    CHECK(result.fault_instruction == data_abort[1]);
    CHECK((trace_mask & (1u << 14)) != 0);

    context = make_context(&execution, bounded_loop, 1, 7, 0);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_BUDGET);
    CHECK(result.code == VF_PREOS_E_BUDGET);
    CHECK(result.termination_reason == VF_TERMINATION_BUDGET_EXHAUSTED);
    CHECK(result.retired_instruction_count == 7);
    CHECK((trace_mask & (1u << 9)) != 0);

    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100, 0);
    context.reserved[0] = 1;
    trace_mask = 0;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_ABI);
    CHECK(result.code == VF_PREOS_E_ABI);
    CHECK(trace_mask == 0); /* malformed ABI must not indirect-call trace */

    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100, 0);
    context.guest_bytes = 0;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_GUEST_INPUT);
    CHECK(result.code == VF_PREOS_E_GUEST_INPUT);
    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100, 0);
    context.guest_bytes = (const uint8_t *)(uintptr_t)(UINTPTR_MAX - (uintptr_t)7);
    context.guest_size = 16;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_GUEST_INPUT);
    CHECK(result.code == VF_PREOS_E_GUEST_INPUT);
    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100, 0);
    context.guest_ram = 0;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_CONTEXT);
    CHECK(result.code == VF_PREOS_E_CONTEXT);

    /* A caller that only supplies the ABI prefix must be rejected before the
     * Rust entry reads reserved fields or pointer spans beyond that prefix. */
    uint32_t short_context[2] = {VF_PREOS_ABI_VERSION, 8};
    zero_result(&result);
    CHECK(vf_preos_run((const VF_PREOS_CONTEXT *)(void *)short_context, &result) == VF_PREOS_E_ABI);
    CHECK(result.code == VF_PREOS_E_ABI);

    /* An architectural request now selects the bounded Rust reference core.
     * This is a real guest execution path (MOVZ -> HLT), not a flag-only
     * acknowledgement and not a call through the C JIT wrapper. */
    const uint32_t architectural_guest[] = {0xd28000e0, 0xd4400000};
    context = make_context(&execution, architectural_guest,
                           sizeof(architectural_guest) / sizeof(architectural_guest[0]), 100,
                           VF_PREOS_REQUEST_MMU);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_OK);
    CHECK(result.code == VF_PREOS_OK);
    CHECK(result.termination_reason == VF_TERMINATION_HALT);
    CHECK(result.result_x0 == 7);
    CHECK(result.retired_instruction_count == 2 && result.guest_pc == 8);
    CHECK((trace_mask & (1u << 16)) != 0);

    /* System-register requests must execute through the Rust architectural
     * core, not merely select a different status path.  CurrentEL is the
     * smallest guest-visible bank read and must report EL1 as 4. */
    const uint32_t architectural_sysreg[] = {0xd5384240, 0xd4400000};
    context = make_context(&execution, architectural_sysreg,
                           sizeof(architectural_sysreg) / sizeof(architectural_sysreg[0]), 100,
                           VF_PREOS_REQUEST_SYSTEM_REGISTERS);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_OK);
    CHECK(result.code == VF_PREOS_OK);
    CHECK(result.termination_reason == VF_TERMINATION_HALT);
    CHECK(result.result_x0 == 4);
    CHECK(result.retired_instruction_count == 2 && result.guest_pc == 8);

    /* The architectural core must reach the native M1 graph's guest-visible
     * MMIO alias, not just execute RAM-only instructions.  The 32-bit
     * firmware identity read returns the fixed T8103 SoC id. */
    const uint32_t architectural_m1_mmio[] = {
        0xd2a20001, /* movz x1, #0x1000, lsl #16 => 0x10000000 */
        0xb9400020, /* ldr w0, [x1] */
        0xd4400000,
    };
    context = make_context(&execution, architectural_m1_mmio,
                           sizeof(architectural_m1_mmio) / sizeof(architectural_m1_mmio[0]), 100,
                           VF_PREOS_REQUEST_MMU);
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_OK);
    CHECK(result.code == VF_PREOS_OK);
    CHECK(result.termination_reason == VF_TERMINATION_HALT);
    CHECK(result.result_x0 == 0x8103);
    CHECK(result.retired_instruction_count == 3 && result.guest_pc == 12);

    /* The opaque execution capability is part of the C-owned boundary.  A
     * malformed capability must be rejected before vf_run() is entered. */
    context = make_context(&execution, golden, sizeof(golden) / sizeof(golden[0]), 100, 0);
    execution.initial_x2 = 16;
    execution.reserved = 1;
    zero_result(&result);
    CHECK(vf_preos_run(&context, &result) == VF_PREOS_E_CONTEXT);
    CHECK(result.code == VF_PREOS_E_CONTEXT);
    execution.reserved = 0;

    CHECK(protect_pages(code.bytes, code.capacity, 0, 0) == 0);
    CHECK(munmap(code.bytes, code.capacity) == 0);
    printf("{\"passed\":true,\"assertions\":%u,\"c_rust_abi_executed\":true,"
           "\"normal_halt\":true,\"exception_reason_preservation\":true,\"budget_exhaustion\":true,"
           "\"architectural_reference_core\":true,\"m1_graph_runtime_activation\":true}\n", tests);
    return 0;
}
