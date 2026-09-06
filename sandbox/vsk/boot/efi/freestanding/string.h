/* SPDX-License-Identifier: BSD-4-Clause; narrow freestanding declarations.
 * Implementations are in src/vf_runtime.c. No hosted C library is linked. */
#ifndef VF_FREESTANDING_STRING_H
#define VF_FREESTANDING_STRING_H
#include <stddef.h>
void *memcpy(void *,const void *,size_t);
void *memmove(void *,const void *,size_t);
void *memset(void *,int,size_t);
#endif
