/* Narrow freestanding adapter for unmodified BearSSL 0.6 sha2small.c.
 * Endian helpers below are portable branches from upstream src/inner.h.
 * Copyright (c) 2016 Thomas Pornin <pornin@bolet.org>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */
#ifndef VF_BEARSSL_INNER_H
#define VF_BEARSSL_INNER_H
#include "bearssl_hash.h"

/* Memory adaptation only; no allocator or cryptographic implementation here.
 * Volatile stores prevent compiler reintroduction of hosted libc calls. */
static inline void *vf_crypto_copy(void *dst, const void *src, size_t bytes)
{
    volatile unsigned char *d = dst;
    const unsigned char *s = src;
    size_t i;
    for (i = 0; i < bytes; ++i) d[i] = s[i];
    return dst;
}
static inline void *vf_crypto_set(void *dst, int value, size_t bytes)
{
    volatile unsigned char *d = dst;
    size_t i;
    for (i = 0; i < bytes; ++i) d[i] = (unsigned char)value;
    return dst;
}
#define memcpy vf_crypto_copy
#define memset vf_crypto_set

static inline void br_enc32be(void *dst, uint32_t x)
{
    unsigned char *buf = dst;
    buf[0] = (unsigned char)(x >> 24);
    buf[1] = (unsigned char)(x >> 16);
    buf[2] = (unsigned char)(x >> 8);
    buf[3] = (unsigned char)x;
}
static inline uint32_t br_dec32be(const void *src)
{
    const unsigned char *buf = src;
    return ((uint32_t)buf[0] << 24) | ((uint32_t)buf[1] << 16)
        | ((uint32_t)buf[2] << 8) | (uint32_t)buf[3];
}
static inline void br_enc64be(void *dst, uint64_t x)
{
    unsigned char *buf = dst;
    br_enc32be(buf, (uint32_t)(x >> 32));
    br_enc32be(buf + 4, (uint32_t)x);
}
void br_range_dec32be(uint32_t *v, size_t num, const void *src);
void br_range_enc32be(void *dst, const uint32_t *v, size_t num);
void br_sha2small_round(const unsigned char *buf, uint32_t *val);
#endif
