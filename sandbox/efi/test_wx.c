/* SPDX-License-Identifier: BSD-4-Clause */
#include "uefi.h"

#include <assert.h>
#include <stdio.h>

int main(void) {
    assert(vf_memory_attributes_satisfy(0, 1));
    assert(!vf_memory_attributes_satisfy(EFI_MEMORY_RO, 1));
    assert(!vf_memory_attributes_satisfy(EFI_MEMORY_XP, 1));
    assert(!vf_memory_attributes_satisfy(EFI_MEMORY_RO | EFI_MEMORY_XP, 1));
    assert(vf_memory_attributes_satisfy(EFI_MEMORY_XP, 0));
    assert(!vf_memory_attributes_satisfy(0, 0));
    assert(!vf_memory_attributes_satisfy(EFI_MEMORY_RO, 0));
    assert(!vf_memory_attributes_satisfy(EFI_MEMORY_RO | EFI_MEMORY_XP, 0));
    puts("{\"passed\":true,\"wx_attribute_predicate\":true}");
    return 0;
}
