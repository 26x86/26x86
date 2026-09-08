/* Independently restated public UEFI variable-info headers; no vendor source. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
struct efi_time {
    uint16_t year;
    uint8_t month, day, hour, minute, second, pad1;
    uint32_t nanosecond;
    int16_t timezone;
    uint8_t daylight, pad2;
};
struct file_info {
    uint64_t size, file_size, physical_size;
    struct efi_time created, accessed, modified;
    uint64_t attribute;
    uint16_t name[];
};
struct filesystem_info {
    uint64_t size;
    uint8_t read_only;
    uint64_t volume_size, free_space;
    uint32_t block_size;
    uint16_t label[];
};
_Static_assert(sizeof(struct efi_time) == 16, "UEFI time");
_Static_assert(offsetof(struct file_info, name) == 80, "FileInfo.Name");
_Static_assert(offsetof(struct filesystem_info, label) == 36, "FileSystemInfo.Label");
int main(void) {
    printf("{\"file_name_offset\":%zu,\"volume_label_offset\":%zu,\"alignment\":%zu}\n",
           offsetof(struct file_info, name), offsetof(struct filesystem_info, label),
           _Alignof(struct file_info));
    return 0;
}
