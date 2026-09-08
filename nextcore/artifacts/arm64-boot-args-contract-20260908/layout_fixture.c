/* Independent layout expression from the public ARM64 boot argument fields.
 * It includes no Apple header or implementation. Compile with a Darwin ARM64
 * target as well as running on an LP64 host. */
#include <stddef.h>
#include <stdint.h>

struct VideoWords { unsigned long base, display, stride, width, height, depth; };
struct Arguments {
    uint16_t revision, version;
    uint64_t virtual_base, physical_base, memory_bytes, occupied_top;
    struct VideoWords video;
    uint32_t machine;
    void *tree;
    uint32_t tree_bytes;
    char command[1024];
    uint64_t flags, actual_memory_bytes;
};

#define OFFSET(field, value) _Static_assert(offsetof(struct Arguments, field) == value, #field)
_Static_assert(sizeof(unsigned long) == 8 && sizeof(void *) == 8, "LP64");
_Static_assert(sizeof(struct VideoWords) == 48, "video size");
_Static_assert(sizeof(struct Arguments) == 1152, "argument size");
_Static_assert(_Alignof(struct Arguments) == 8, "argument alignment");
OFFSET(revision, 0); OFFSET(version, 2); OFFSET(virtual_base, 8);
OFFSET(physical_base, 16); OFFSET(memory_bytes, 24); OFFSET(occupied_top, 32);
OFFSET(video, 40); OFFSET(machine, 88); OFFSET(tree, 96); OFFSET(tree_bytes, 104);
OFFSET(command, 108); OFFSET(flags, 1136); OFFSET(actual_memory_bytes, 1144);

#ifdef HOST_LAYOUT_REPORT
#include <stdio.h>
int main(void) {
    printf("{\"size\":%zu,\"alignment\":%zu,\"offsets\":[", sizeof(struct Arguments), _Alignof(struct Arguments));
#define REPORT(field, separator) printf(separator "%zu", offsetof(struct Arguments, field))
    REPORT(revision, ""); REPORT(version, ","); REPORT(virtual_base, ",");
    REPORT(physical_base, ","); REPORT(memory_bytes, ","); REPORT(occupied_top, ",");
    REPORT(video, ","); REPORT(machine, ","); REPORT(tree, ","); REPORT(tree_bytes, ",");
    REPORT(command, ","); REPORT(flags, ","); REPORT(actual_memory_bytes, ",");
    puts("]}");
    return 0;
}
#endif
