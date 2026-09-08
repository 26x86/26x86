/* Standalone macOS x86_64 public-API probe. See metal_compute_probe.md.
 * SDK-independent FFI declarations; no driver, firmware, or private API.
 */
#include <stddef.h>
#include <stdint.h>

#if !defined(__x86_64__)
#error This probe has only the documented macOS x86_64 ABI profile.
#endif

extern int printf(const char *, ...);
extern int fflush(void *);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern unsigned alarm(unsigned);
extern int usleep(unsigned);

typedef void *Object;
typedef void *Selector;
typedef unsigned long UInteger;
typedef struct { UInteger width, height, depth; } GridSize;
_Static_assert(sizeof(UInteger) == 8 && sizeof(GridSize) == 24,
               "macOS x86_64 Metal argument layout");

static void *message;
static Selector (*selector)(const char *);
static Object (*get_class)(const char *);

static Object object0(Object receiver, const char *name) {
    return ((Object (*)(Object, Selector))message)(receiver, selector(name));
}
static UInteger integer0(Object receiver, const char *name) {
    return ((UInteger (*)(Object, Selector))message)(receiver, selector(name));
}
static void void0(Object receiver, const char *name) {
    ((void (*)(Object, Selector))message)(receiver, selector(name));
}
static Object string(const char *value) {
    return ((Object (*)(Object, Selector, const char *))message)(
        get_class("NSString"), selector("stringWithUTF8String:"), value);
}
static void quoted(const char *value) {
    printf("\"");
    for (const unsigned char *p = (const unsigned char *)(value ? value : ""); *p; ++p) {
        if (*p == '"' || *p == '\\') printf("\\%c", *p);
        else if (*p < 32) printf("\\u%04x", (unsigned)*p);
        else printf("%c", *p);
    }
    printf("\"");
}
static void event(const char *stage) {
    printf("{\"probe\":\"nxmetal-v1\",\"stage\":");
    quoted(stage);
    printf("}\n");
    fflush(NULL);
}

enum { ELEMENTS = 256, GUARD = 64, WORDS = ELEMENTS + 2 * GUARD };
static uint32_t guard(unsigned index) { return UINT32_C(0xa5a50000) ^ index; }
static uint32_t input_a(unsigned index, unsigned seed) { return (index * 17u + seed) ^ 0x53u; }
static uint32_t input_b(unsigned index, unsigned seed) { return index * seed + 13u; }
static uint32_t expected(unsigned index, unsigned seed) {
    return (input_a(index, seed) ^ UINT32_C(0x13579bdf)) + 3u * input_b(index, seed);
}

int main(void) {
    const char *failure = "load-runtime";
    Object owned[10] = {0}, pool = NULL, error = NULL;
    unsigned count = 0, completed = 0;
    int result = 1;
    alarm(90); /* Includes library/pipeline creation and any blocking callback. */
    event("start");
    /* RTLD_NOW=2 is the public Darwin dlfcn contract. No global interposition. */
    void *runtime = dlopen("/usr/lib/libobjc.A.dylib", 2);
    void *foundation = dlopen("/System/Library/Frameworks/Foundation.framework/Foundation", 2);
    void *metal = dlopen("/System/Library/Frameworks/Metal.framework/Metal", 2);
    if (!runtime || !foundation || !metal) goto cleanup;
    message = dlsym(runtime, "objc_msgSend");
    selector = (Selector (*)(const char *))dlsym(runtime, "sel_registerName");
    get_class = (Object (*)(const char *))dlsym(runtime, "objc_getClass");
    Object (*default_device)(void) = (Object (*)(void))dlsym(metal, "MTLCreateSystemDefaultDevice");
    if (!message || !selector || !get_class || !default_device) goto cleanup;
    failure = "autorelease-pool";
    pool = object0(object0(get_class("NSAutoreleasePool"), "alloc"), "init");
    if (!pool || !get_class("NSString")) goto cleanup;

#define OWN(target, expression, stage) do { \
    failure = stage; target = (expression); \
    if (!(target)) goto cleanup; owned[count++] = target; \
} while (0)

    Object device, queue, library, function, pipeline, buffers[3];
    OWN(device, default_device(), "no-metal-device");
    const char *name = (const char *)object0(object0(device, "name"), "UTF8String");
    printf("{\"probe\":\"nxmetal-v1\",\"stage\":\"device\",\"name\":");
    quoted(name);
    printf(",\"registry_id\":\"%016lx\"}\n", integer0(device, "registryID"));
    fflush(NULL);
    OWN(queue, object0(device, "newCommandQueue"), "queue");
    static const char shader[] =
        "#include <metal_stdlib>\nusing namespace metal;\n"
        "kernel void nx_probe(device const uint* a [[buffer(0)]],"
        "device const uint* b [[buffer(1)]],device uint* out [[buffer(2)]],"
        "uint i [[thread_position_in_grid]]){"
        "if(i<256)out[i]=(a[i]^0x13579bdfu)+3u*b[i];}\n";
    event("compile-library");
    OWN(library, ((Object (*)(Object, Selector, Object, Object, Object *))message)(
        device, selector("newLibraryWithSource:options:error:"), string(shader), NULL, &error),
        "compile-library");
    OWN(function, ((Object (*)(Object, Selector, Object))message)(
        library, selector("newFunctionWithName:"), string("nx_probe")), "function");
    event("compile-pipeline");
    OWN(pipeline, ((Object (*)(Object, Selector, Object, Object *))message)(
        device, selector("newComputePipelineStateWithFunction:error:"), function, &error),
        "compile-pipeline");
    UInteger maximum = integer0(pipeline, "maxTotalThreadsPerThreadgroup");
    failure = "threadgroup-limit";
    if (!maximum) goto cleanup;
    UInteger width = maximum >= 32 ? 32 : 1;
    volatile uint32_t *words[3];
    for (unsigned b = 0; b < 3; ++b) {
        OWN(buffers[b], ((Object (*)(Object, Selector, UInteger, UInteger))message)(
            device, selector("newBufferWithLength:options:"), WORDS * sizeof(uint32_t), 0), "buffer");
        failure = "shared-buffer-contents";
        words[b] = (volatile uint32_t *)object0(buffers[b], "contents");
        if (!words[b]) goto cleanup;
    }
    for (unsigned run = 0; run < 2; ++run) {
        unsigned seed = run ? 17 : 1;
        for (unsigned b = 0; b < 3; ++b)
            for (unsigned i = 0; i < WORDS; ++i) words[b][i] = guard(i);
        for (unsigned i = 0; i < ELEMENTS; ++i) {
            words[0][GUARD + i] = input_a(i, seed);
            words[1][GUARD + i] = input_b(i, seed);
            words[2][GUARD + i] = UINT32_C(0xdeadbeef);
        }
        failure = "command-buffer";
        Object command = object0(queue, "commandBuffer");
        if (!command) goto cleanup;
        failure = "compute-encoder";
        Object encoder = object0(command, "computeCommandEncoder");
        if (!encoder) goto cleanup;
        ((void (*)(Object, Selector, Object))message)(
            encoder, selector("setComputePipelineState:"), pipeline);
        for (unsigned b = 0; b < 3; ++b)
            ((void (*)(Object, Selector, Object, UInteger, UInteger))message)(
                encoder, selector("setBuffer:offset:atIndex:"), buffers[b], GUARD * sizeof(uint32_t), b);
        ((void (*)(Object, Selector, GridSize, GridSize))message)(
            encoder, selector("dispatchThreadgroups:threadsPerThreadgroup:"),
            (GridSize){ELEMENTS / width, 1, 1}, (GridSize){width, 1, 1});
        void0(encoder, "endEncoding");
        event("submit");
        void0(command, "commit");
        UInteger status = integer0(command, "status");
        for (unsigned poll = 0; status < 4 && poll < 2000; ++poll) {
            usleep(10000);
            status = integer0(command, "status");
        }
        printf("{\"probe\":\"nxmetal-v1\",\"run\":%u,\"command_status\":%lu}\n", run, status);
        fflush(NULL);
        failure = "command-not-completed";
        if (status != 4) { error = object0(command, "error"); goto cleanup; }
        failure = "readback";
        /* Read actual shared GPU results only after command completion. */
        for (unsigned i = 0; i < ELEMENTS; ++i)
            if (words[0][GUARD + i] != input_a(i, seed) ||
                words[1][GUARD + i] != input_b(i, seed) ||
                words[2][GUARD + i] != expected(i, seed)) goto cleanup;
        failure = "guard-readback";
        for (unsigned b = 0; b < 3; ++b)
            for (unsigned i = 0; i < WORDS; ++i)
                if ((i < GUARD || i >= GUARD + ELEMENTS) && words[b][i] != guard(i)) goto cleanup;
        completed += ELEMENTS;
        event("readback-pass");
    }
    result = 0;
cleanup:
    if (result) {
        printf("{\"probe\":\"nxmetal-v1\",\"passed\":false,\"failure\":"); quoted(failure);
        if (error && message && selector) {
            printf(",\"detail\":");
            quoted((const char *)object0(object0(error, "localizedDescription"), "UTF8String"));
        }
        printf("}\n");
    } else {
        printf("{\"probe\":\"nxmetal-v1\",\"passed\":true,\"completed_values\":%u,"
               "\"input_sets\":2,\"guard_words_per_buffer\":128}\n", completed);
    }
    fflush(NULL);
    while (count) void0(owned[--count], "release");
    if (pool) void0(pool, "drain");
    alarm(0);
    return result;
}
