/* SPDX-License-Identifier: BSD-4-Clause
 *
 * Stable C/Rust ABI for the EFI-integrated Venfire micro-preOS.  This header
 * is deliberately independent from the internal JIT structures: C owns those
 * structures, all UEFI services, all page allocation, and all W^X changes.
 */
#ifndef VENFIRE_PREOS_ABI_H
#define VENFIRE_PREOS_ABI_H

#include <stddef.h>
#include <stdint.h>

/* x86_64-pc-windows-msvc Rust and the EFI C target both use Microsoft x64.
 * The Linux host ABI test intentionally uses its native C ABI instead. */
#if defined(_WIN32)
#define VF_PREOS_ABI __attribute__((ms_abi))
#else
#define VF_PREOS_ABI
#endif

#define VF_PREOS_ABI_VERSION UINT32_C(1)
#define VF_PREOS_MAX_GUEST_BYTES UINT64_C(65536)
#define VF_PREOS_FIXED_GUEST_RAM_BYTES UINT64_C(65536)
#define VF_PREOS_MAX_EXECUTION_BUDGET UINT64_C(100000)

/* This is only a fail-closed policy seed for the diagnostic path.  It does
 * not identify a physical Apple SoC, a vma2 ABI, or an Apple boot contract. */
#define VF_MACHINE_PROFILE_M1_DIAGNOSTIC UINT32_C(0x4d314430) /* "M1D0" */

#define VF_PREOS_EXPECT_GOLDEN_RESULT UINT32_C(0x00000001)

enum vf_preos_code {
    VF_PREOS_OK = 0,
    VF_PREOS_E_ABI = 1,
    VF_PREOS_E_CONTEXT = 2,
    VF_PREOS_E_PROFILE = 3,
    VF_PREOS_E_GUEST_INPUT = 4,
    VF_PREOS_E_MACHINE_INIT = 5,
    VF_PREOS_E_JIT = 6,
    VF_PREOS_E_BUDGET = 7,
    VF_PREOS_E_PROTECTION = 8,
    VF_PREOS_E_INTERNAL = 9,
    VF_PREOS_E_RESULT = 10,
    VF_PREOS_E_UNSUPPORTED = 11,
};

/* VF_PREOS_CONTEXT.flags.  Bit zero requests the Phase-1 golden-result
 * assertion.  The feature request bits are intentionally present in the
 * stable ABI so callers cannot accidentally assume that a user-mode JIT run
 * implements architectural system state.  A nonzero feature request is kept
 * out of the C JIT fast path and is handled only by the bounded Rust reference
 * boundary; unsupported portions return VF_PREOS_E_UNSUPPORTED. */
#define VF_PREOS_REQUEST_EXCEPTION_MODEL UINT32_C(0x00000100)
#define VF_PREOS_REQUEST_PRIVILEGED_STATE UINT32_C(0x00000200)
#define VF_PREOS_REQUEST_SYSTEM_REGISTERS UINT32_C(0x00000400)
#define VF_PREOS_REQUEST_MMU UINT32_C(0x00000800)
#define VF_PREOS_REQUEST_TLB UINT32_C(0x00001000)
#define VF_PREOS_REQUEST_ATOMICS UINT32_C(0x00002000)
#define VF_PREOS_REQUEST_SMP UINT32_C(0x00004000)
#define VF_PREOS_REQUEST_TIMER UINT32_C(0x00008000)
#define VF_PREOS_REQUEST_PAUTH UINT32_C(0x00010000)

enum vf_termination_reason {
    VF_TERMINATION_NONE = 0,
    VF_TERMINATION_HALT = 1,
    VF_TERMINATION_BAD_INSTRUCTION = 2,
    VF_TERMINATION_FETCH_FAULT = 3,
    VF_TERMINATION_DATA_FAULT = 4,
    VF_TERMINATION_BUDGET_EXHAUSTED = 5,
    VF_TERMINATION_PROTECTION_FAILURE = 6,
    VF_TERMINATION_CODE_BUFFER_FULL = 7,
    VF_TERMINATION_WRAPPER_REJECTED = 8,
    VF_TERMINATION_INTERNAL = 9,
    VF_TERMINATION_UNSUPPORTED = 10,
    VF_TERMINATION_UNDEFINED_INSTRUCTION = 11,
    VF_TERMINATION_PRIVILEGE_FAULT = 12,
    VF_TERMINATION_TRANSLATION_FAULT = 13,
    VF_TERMINATION_PERMISSION_FAULT = 14,
    VF_TERMINATION_ALIGNMENT_FAULT = 15,
    VF_TERMINATION_SYSTEM_REGISTER_TRAP = 16,
    VF_TERMINATION_TIMER_INTERRUPT = 17,
    VF_TERMINATION_EXTERNAL_INTERRUPT = 18,
    VF_TERMINATION_INSTRUCTION_ABORT = 19,
    VF_TERMINATION_DATA_ABORT = 20,
};

/* C owns both the trace endpoint and its opaque value.  The callback receives
 * only immutable NUL-terminated static messages from Rust; Rust never sees a
 * UEFI system table, protocol pointer, or Boot Services function. */
typedef void (VF_PREOS_ABI *vf_preos_trace_fn)(const char *message, void *opaque);

/* Pointers remain valid from vf_preos_run entry through its return.  guest is
 * read-only; guest_ram is C-owned mutable RAM.  The opaque handle is a C-only
 * capability and Rust must pass it back unchanged without dereferencing it.
 * NULL is never valid for guest_bytes, guest_ram, opaque_execution_handle, or
 * trace.  trace_opaque may be NULL. */
typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    uint32_t machine_profile;
    uint32_t flags;
    uint64_t execution_budget;
    const uint8_t *guest_bytes;
    uint64_t guest_size;
    uint8_t *guest_ram;
    uint64_t guest_ram_size;
    void *opaque_execution_handle;
    vf_preos_trace_fn trace;
    void *trace_opaque;
    uint64_t expected_x1;
    uint64_t expected_x3;
    uint64_t expected_ram_offset;
    uint64_t expected_ram_qword;
    uint64_t expected_retired;
    uint64_t expected_guest_pc;
    uint64_t reserved[3];
} VF_PREOS_CONTEXT;

/* Rust creates this request on its fixed stack.  C revalidates every field
 * before it reaches vf_run().  No JIT-private structure is exposed to Rust. */
typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    uint32_t machine_profile;
    uint32_t flags;
    uint64_t execution_budget;
    const uint8_t *guest_bytes;
    uint64_t guest_size;
    uint8_t *guest_ram;
    uint64_t guest_ram_size;
    void *opaque_execution_handle;
    uint64_t reserved[3];
} VF_JIT_REQUEST;

/* JIT status is the existing C enum vf_status value.  The termination reason
 * is stable across the C/Rust boundary and must be used for user-visible
 * outcome reporting rather than treating every return as a successful halt. */
typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    int32_t jit_status;
    uint32_t termination_reason;
    uint64_t retired_instruction_count;
    uint64_t guest_pc;
    uint32_t fault_instruction;
    uint32_t reserved0;
    uint64_t result_x0;
    uint64_t result_x1;
    uint64_t result_x3;
    uint64_t reserved[3];
} VF_JIT_RESULT;

typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    int32_t code;
    uint32_t termination_reason;
    uint64_t retired_instruction_count;
    uint64_t guest_pc;
    uint32_t fault_instruction;
    uint32_t reserved0;
    uint64_t result_x0;
    uint64_t result_x1;
    uint64_t result_x3;
    uint64_t reserved[3];
} VF_PREOS_RESULT;

_Static_assert(sizeof(void *) == 8, "Venfire EFI ABI requires 64-bit pointers");
_Static_assert(sizeof(VF_PREOS_CONTEXT) == 152, "VF_PREOS_CONTEXT ABI v1 size");
_Static_assert(_Alignof(VF_PREOS_CONTEXT) == 8, "VF_PREOS_CONTEXT ABI v1 alignment");
_Static_assert(offsetof(VF_PREOS_CONTEXT, execution_budget) == 16, "VF_PREOS_CONTEXT ABI v1 budget offset");
_Static_assert(offsetof(VF_PREOS_CONTEXT, guest_bytes) == 24, "VF_PREOS_CONTEXT ABI v1 guest offset");
_Static_assert(offsetof(VF_PREOS_CONTEXT, guest_ram) == 40, "VF_PREOS_CONTEXT ABI v1 ram offset");
_Static_assert(offsetof(VF_PREOS_CONTEXT, opaque_execution_handle) == 56, "VF_PREOS_CONTEXT ABI v1 handle offset");
_Static_assert(offsetof(VF_PREOS_CONTEXT, trace) == 64, "VF_PREOS_CONTEXT ABI v1 trace offset");
_Static_assert(offsetof(VF_PREOS_CONTEXT, expected_x1) == 80, "VF_PREOS_CONTEXT ABI v1 expectation offset");
_Static_assert(offsetof(VF_PREOS_CONTEXT, reserved) == 128, "VF_PREOS_CONTEXT ABI v1 reserved offset");
_Static_assert(sizeof(VF_JIT_REQUEST) == 88, "VF_JIT_REQUEST ABI v1 size");
_Static_assert(_Alignof(VF_JIT_REQUEST) == 8, "VF_JIT_REQUEST ABI v1 alignment");
_Static_assert(offsetof(VF_JIT_REQUEST, opaque_execution_handle) == 56, "VF_JIT_REQUEST ABI v1 handle offset");
_Static_assert(sizeof(VF_JIT_RESULT) == 88, "VF_JIT_RESULT ABI v1 size");
_Static_assert(sizeof(VF_PREOS_RESULT) == 88, "VF_PREOS_RESULT ABI v1 size");
_Static_assert(_Alignof(VF_PREOS_RESULT) == 8, "VF_PREOS_RESULT ABI v1 alignment");
_Static_assert(offsetof(VF_PREOS_RESULT, result_x1) == 48, "VF_PREOS_RESULT ABI v1 result offset");

int VF_PREOS_ABI vf_preos_run(const VF_PREOS_CONTEXT *context, VF_PREOS_RESULT *result);
int VF_PREOS_ABI vf_preos_jit_execute(const VF_JIT_REQUEST *request, VF_JIT_RESULT *result);
void VF_PREOS_ABI vf_preos_abort(void);

#endif
