/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies.
 * Minimal freestanding byte primitives required by reviewed crypto sources.
 * Caller provides valid spans; no allocator, I/O or implicit SIMD dependency. */
#include <stddef.h>
#include <stdint.h>
void *memset(void *out,int value,size_t bytes) {
    volatile uint8_t *p=out;while(bytes--)*p++=(uint8_t)value;return out;
}
void *memcpy(void *out,const void *in,size_t bytes) {
    volatile uint8_t *d=out;const volatile uint8_t *s=in;
    while(bytes--)*d++=*s++;return out;
}
void *memmove(void *out,const void *in,size_t bytes) {
    volatile uint8_t *d=out;const volatile uint8_t *s=in;
    if((uintptr_t)d<(uintptr_t)s)while(bytes--)*d++=*s++;
    else {d+=bytes;s+=bytes;while(bytes--)*--d=*--s;}return out;
}
