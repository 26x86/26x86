/* SPDX-License-Identifier: BSD-4-Clause
 * Host-side receipt for the C half of the stable C/Rust ABI.
 *
 * The executable is a build-time verifier only; it is not staged in the EFI
 * package.  The Rust unit test emits the corresponding values and build.py
 * compares the two receipts before it links BOOTX64.EFI.
 */
#include "preos_abi.h"

#include <stdio.h>

int main(void) {
    printf(
        "{\"context_size\":%zu,\"context_align\":%zu,"
        "\"context_budget_offset\":%zu,\"context_guest_offset\":%zu,"
        "\"context_ram_offset\":%zu,\"context_handle_offset\":%zu,"
        "\"context_trace_offset\":%zu,\"context_expected_x1_offset\":%zu,"
        "\"context_reserved_offset\":%zu,\"request_size\":%zu,"
        "\"request_align\":%zu,\"request_handle_offset\":%zu,"
        "\"jit_result_size\":%zu,\"jit_result_align\":%zu,"
        "\"preos_result_size\":%zu,\"preos_result_align\":%zu,"
        "\"preos_result_x1_offset\":%zu}\n",
        sizeof(VF_PREOS_CONTEXT), _Alignof(VF_PREOS_CONTEXT),
        offsetof(VF_PREOS_CONTEXT, execution_budget),
        offsetof(VF_PREOS_CONTEXT, guest_bytes),
        offsetof(VF_PREOS_CONTEXT, guest_ram),
        offsetof(VF_PREOS_CONTEXT, opaque_execution_handle),
        offsetof(VF_PREOS_CONTEXT, trace),
        offsetof(VF_PREOS_CONTEXT, expected_x1),
        offsetof(VF_PREOS_CONTEXT, reserved),
        sizeof(VF_JIT_REQUEST), _Alignof(VF_JIT_REQUEST),
        offsetof(VF_JIT_REQUEST, opaque_execution_handle),
        sizeof(VF_JIT_RESULT), _Alignof(VF_JIT_RESULT),
        sizeof(VF_PREOS_RESULT), _Alignof(VF_PREOS_RESULT),
        offsetof(VF_PREOS_RESULT, result_x1));
    return 0;
}
