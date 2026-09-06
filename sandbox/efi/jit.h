/* SPDX-License-Identifier: BSD-4-Clause; see ../../LICENSE.txt and repository LICENSE.txt. */
#ifndef VENFIRE_JIT_H
#define VENFIRE_JIT_H
#include <stdint.h>
#include <stddef.h>
#define VF_ABI __attribute__((ms_abi))
enum vf_status { VF_NEXT, VF_HALT, VF_BAD_INSTRUCTION, VF_FETCH_FAULT, VF_DATA_FAULT,
                 VF_BUDGET, VF_CODE_FULL, VF_PROTECTION };
typedef struct { uint64_t x[32], pc, retired; uint32_t instruction, status; } vf_cpu;
typedef struct { uint8_t *bytes; size_t capacity, used; } vf_code;
typedef int (VF_ABI *vf_entry)(vf_cpu *, uint8_t *, uint64_t);
typedef int (*vf_protect)(void *, size_t, int executable, void *);
int vf_translate(vf_code *, const uint8_t *, size_t, uint64_t pc, unsigned limit);
int vf_run(vf_cpu *, const uint8_t *, size_t, uint8_t *, size_t,
           vf_code *, uint64_t budget, vf_protect, void *);
int vf_host_supported(void);
#endif
