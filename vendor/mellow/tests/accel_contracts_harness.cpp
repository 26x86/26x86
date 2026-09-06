// Host-only harness. Production definitions are inserted by accel_contracts.py.
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <set>
#include <string>
#include "hde64.h"

using mach_vm_address_t = uintptr_t;
using IOReturn = uint32_t;
constexpr uint32_t kIOReturnUnsupported = 0xe00002c7U;
constexpr uint32_t kIOReturnBadArgument = 0xe00002c2U;
constexpr uint32_t kIOReturnNotReady = 0xe00002d8U;
constexpr int KERN_SUCCESS = 0;
#define SYSLOG(...) ((void)0)
#define FunctionCast(function, target) reinterpret_cast<decltype(&function)>(target)
#define lilu_os_memcpy std::memcpy
static bool hasMode = false;
static int bootMode = 0;
static bool hasBarrierMode = false;
static int bootBarrierMode = 0;
static std::set<std::string> bootArgs;
static bool PE_parse_boot_argn(const char *name, void *out, size_t size) {
    if (!std::strcmp(name, "mellowV130")) {
        if (!hasBarrierMode || size != sizeof(int)) return false;
        *static_cast<int *>(out) = bootBarrierMode; return true;
    }
    if (std::strcmp(name, "mellowV142") || !hasMode || size != sizeof(int)) return false;
    *static_cast<int *>(out) = bootMode;
    return true;
}
static bool checkKernelArgument(const char *name) { return bootArgs.count(name) != 0; }
template <typename T> T &getMember(void *object, size_t offset) {
    return *reinterpret_cast<T *>(static_cast<uint8_t *>(object) + offset);
}
struct MellowCore { static MellowCore *callback; bool isRealTGL = false; };
MellowCore *MellowCore::callback = nullptr;
struct Gen11 {
    static Gen11 *callback;
    uintptr_t odeviceStart = 0, osubmitBlit = 0, oIGScheduler4IsGpuIdle = 0;
    uintptr_t oIGScheduler5IsGpuIdle = 0, orgIgBufferWithOptions = 0;
    uintptr_t oloadGuCBinary = 0, orgPavpSessionCallback = 0;
    uintptr_t obarrierSubmission = 0;
    static uint8_t deviceStart(void *);
    static unsigned long submitBlit(void *, void *, void *, void *, bool);
    static bool wrapIGScheduler4IsGpuIdle(const void *);
    static bool wrapIGScheduler5IsGpuIdle(const void *);
    static void *wrapIgBufferWithOptions(void *, void *, unsigned int, unsigned int);
    static unsigned long loadGuCBinary(void *);
    static IOReturn wrapPavpSessionCallback(void *, int32_t, uint32_t, uint32_t *, bool);
    static uint8_t barrierSubmission(void *, void *, void *, void *, uint16_t, const uint16_t *);
};
Gen11 *Gen11::callback = nullptr;
struct KernelPatcher { static int kernelWriteLock; };
int KernelPatcher::kernelWriteLock = 0;
static bool allowWriting = true;
static unsigned enableCalls = 0, disableCalls = 0, decodeCalls = 0;
struct MachInfo {
    static int setKernelWriting(bool enabled, int) {
        if (enabled) { ++enableCalls; return allowWriting ? 0 : 5; }
        ++disableCalls; return 0;
    }
};
struct Disassembler {
    static unsigned hdeDisasm(uintptr_t at, hde64s *decoded) {
        ++decodeCalls; return hde64_disasm(reinterpret_cast<void *>(at), decoded);
    }
};

// PRODUCTION_FUNCTIONS

static unsigned cases = 0, backendCalls = 0;
static uint8_t startResult = 0;
static unsigned long blitResult = 0;
static bool idleResult = false;
static void *seenTask = nullptr, *seenSize = nullptr;
static uint8_t barrierResult = 0;
static void *seenQueue = nullptr, *seenAccelerator = nullptr, *seenDescriptor = nullptr, *seenEvent = nullptr;
static uint16_t seenCount = 0;
static const uint16_t *seenList = nullptr;
static uint8_t startBackend(void *) { ++backendCalls; return startResult; }
static unsigned long blitBackend(void *, void *, void *, void *task, bool) {
    ++backendCalls; seenTask = task; return blitResult;
}
static bool idleBackend(const void *) { ++backendCalls; return idleResult; }
static unsigned long firmwareBackend(void *) { ++backendCalls; return 9; }
static IOReturn pavpBackend(void *, int32_t command, uint32_t, uint32_t *, bool) {
    ++backendCalls; assert(command == 4); return kIOReturnNotReady;
}
static uint8_t barrierBackend(void *queue, void *accelerator, void *descriptor, void *event,
                             uint16_t count, const uint16_t *list) {
    ++backendCalls; seenQueue = queue; seenAccelerator = accelerator;
    seenDescriptor = descriptor; seenEvent = event; seenCount = count; seenList = list;
    return barrierResult;
}
static void *bufferBackend(void *task, void *size, unsigned int type, unsigned int flags) {
    ++backendCalls; seenTask = task; seenSize = size;
    assert(type == 7 && flags == 11); return task;
}
static void check(bool value) { ++cases; assert(value); }
static std::array<uint8_t, 128> image(std::initializer_list<uint8_t> bytes) {
    std::array<uint8_t, 128> out {};
    out.fill(0xC3);
    std::copy(bytes.begin(), bytes.end(), out.begin());
    return out;
}
static bool patch(std::array<uint8_t, 128> &bytes, uint32_t size = 0x03C00000) {
    auto base = reinterpret_cast<uintptr_t>(bytes.data());
    return patchStolenMemoryFormula(base, base, bytes.size(), size);
}
int main() {
    Gen11 plugin; MellowCore core;
    Gen11::callback = &plugin; MellowCore::callback = &core;
    plugin.odeviceStart = reinterpret_cast<uintptr_t>(startBackend);
    plugin.osubmitBlit = reinterpret_cast<uintptr_t>(blitBackend);
    plugin.oIGScheduler4IsGpuIdle = reinterpret_cast<uintptr_t>(idleBackend);
    plugin.oIGScheduler5IsGpuIdle = reinterpret_cast<uintptr_t>(idleBackend);
    plugin.orgIgBufferWithOptions = reinterpret_cast<uintptr_t>(bufferBackend);
    plugin.oloadGuCBinary = reinterpret_cast<uintptr_t>(firmwareBackend);
    plugin.orgPavpSessionCallback = reinterpret_cast<uintptr_t>(pavpBackend);
    plugin.obarrierSubmission = reinterpret_cast<uintptr_t>(barrierBackend);
    alignas(8) std::array<uint8_t, 0x300> task {};
    alignas(8) std::array<uint8_t, 0xC0> context {};
    std::array<uint8_t, 0xB0> blit {};
    void *dummy = &core;
    check(getV142SubmitBlitMode() == 0);
    for (const char *arg : {"-mellowV142ok", "-mellowV142pass", "-mellowV142unsupported"}) {
        bootArgs = {arg}; check(getV142SubmitBlitMode() == 0);
    }
    bootArgs = {"-mellowV142orig"}; check(getV142SubmitBlitMode() == 3);
    hasMode = true;
    for (int value : {-1, 0, 1, 2, 4, 100}) { bootMode = value; check(getV142SubmitBlitMode() == 0); }
    bootMode = 3; check(getV142SubmitBlitMode() == 3);
    startResult = 0; check(Gen11::deviceStart(dummy) == 0);
    startResult = 9; check(Gen11::deviceStart(dummy) == 9);
    check(Gen11::deviceStart(nullptr) == 0);
    for (bool state : {false, true}) {
        idleResult = state;
        check(Gen11::wrapIGScheduler4IsGpuIdle(dummy) == state);
        check(Gen11::wrapIGScheduler5IsGpuIdle(dummy) == state);
    }
    bootMode = 1; backendCalls = 0;
    check(Gen11::submitBlit(nullptr, nullptr, nullptr, nullptr, false) == kIOReturnUnsupported);
    check(backendCalls == 0);
    bootMode = 3;
    check(Gen11::submitBlit(dummy, blit.data(), dummy, nullptr, false) == kIOReturnBadArgument);
    check(Gen11::submitBlit(dummy, blit.data(), dummy, task.data(), false) == kIOReturnNotReady);
    getMember<void *>(task.data(), 0) = dummy;
    getMember<void *>(task.data(), 0x298) = context.data();
    check(Gen11::submitBlit(dummy, blit.data(), dummy, task.data(), false) == kIOReturnNotReady);
    getMember<void *>(context.data(), 0xB8) = dummy;
    auto savedTask = task;
    blit[0xA2] = 3 << 3;
    check(Gen11::submitBlit(dummy, blit.data(), dummy, task.data(), false) == kIOReturnUnsupported);
    check(backendCalls == 0 && task == savedTask);
    blit[0xA2] = 0;
    for (unsigned long result : {0UL, 1UL, 0xe00002bcUL}) {
        blitResult = result; backendCalls = 0;
        check(Gen11::submitBlit(dummy, blit.data(), dummy, task.data(), false) == result);
        check(backendCalls == 1 && seenTask == task.data() && task == savedTask);
    }
    core.isRealTGL = true; bootMode = 0; backendCalls = 0; blitResult = 17;
    check(Gen11::submitBlit(nullptr, nullptr, nullptr, nullptr, false) == 17 && backendCalls == 1);
    plugin.osubmitBlit = 0;
    check(Gen11::submitBlit(dummy, dummy, dummy, dummy, false) == kIOReturnUnsupported);
    // Preserve the incoming opaque size argument even if it looks like an address.
    void *opaqueSize = reinterpret_cast<void *>(0x12345);
    check(Gen11::wrapIgBufferWithOptions(dummy, opaqueSize, 7, 11) == dummy);
    check(seenTask == dummy && seenSize == opaqueSize);
    core.isRealTGL = false; backendCalls = 0;
    check(Gen11::loadGuCBinary(dummy) == 0 && backendCalls == 0);
    core.isRealTGL = true;
    check(Gen11::loadGuCBinary(dummy) == 9 && backendCalls == 1);
    plugin.oloadGuCBinary = 0;
    check(Gen11::loadGuCBinary(dummy) == 0 && backendCalls == 1);
    check(Gen11::wrapPavpSessionCallback(dummy, 4, 0, nullptr, false) == kIOReturnNotReady);
    plugin.orgPavpSessionCallback = 0;
    check(Gen11::wrapPavpSessionCallback(dummy, 4, 0, nullptr, false) == kIOReturnUnsupported);
    core.isRealTGL = false; bootArgs.clear(); backendCalls = 0;
    check(Gen11::barrierSubmission(dummy, dummy, dummy, dummy, 0, nullptr) == 0 && backendCalls == 0);
    for (const char *arg : {"-mellowV130pass", "-mellowV130hybrid", "-mellowV130orig"}) {
        bootArgs = {arg};
        check(Gen11::barrierSubmission(dummy, dummy, dummy, dummy, 0, nullptr) == 0 && backendCalls == 0);
    }
    hasBarrierMode = true; bootArgs = {"-mellowV130forceorig"};
    for (int mode : {-1, 0, 1, 3, 4, 100}) {
        bootBarrierMode = mode;
        check(Gen11::barrierSubmission(dummy, dummy, dummy, dummy, 0, nullptr) == 0 && backendCalls == 0);
    }
    bootBarrierMode = 2; barrierResult = 1;
    check(Gen11::barrierSubmission(dummy, dummy, dummy, dummy, 1, nullptr) == 0 && backendCalls == 0);
    check(Gen11::barrierSubmission(nullptr, dummy, dummy, dummy, 0, nullptr) == 0 && backendCalls == 0);
    const uint16_t barriers[] = {3, 8};
    for (uint8_t result : {0, 1, 2}) {
        barrierResult = result; backendCalls = 0;
        check(Gen11::barrierSubmission(task.data(), dummy, blit.data(), context.data(), 2, barriers) == result);
        check(backendCalls == 1 && seenQueue == task.data() && seenAccelerator == dummy &&
              seenDescriptor == blit.data() && seenEvent == context.data() && seenCount == 2 && seenList == barriers);
    }
    hasBarrierMode = false; bootArgs = {"-mellowV130orig", "-mellowV130forceorig"}; backendCalls = 0;
    barrierResult = 1;
    check(Gen11::barrierSubmission(dummy, dummy, dummy, dummy, 0, nullptr) == 1 && backendCalls == 1);
    core.isRealTGL = true; bootArgs.clear(); backendCalls = 0;
    check(Gen11::barrierSubmission(nullptr, nullptr, nullptr, nullptr, 0, nullptr) == 1 && backendCalls == 1);
    plugin.obarrierSubmission = 0;
    check(Gen11::barrierSubmission(dummy, dummy, dummy, dummy, 0, nullptr) == 0 && backendCalls == 1);

    // Actual upstream HDE decoder, production patcher, writable host buffer.
    auto eax = image({0xC1,0xE0,0x11, 0x25,0x00,0x00,0x00,0xFE});
    auto saved = eax; allowWriting = false; enableCalls = disableCalls = 0;
    check(!patch(eax) && eax == saved && enableCalls == 1 && disableCalls == 0);
    allowWriting = true; enableCalls = disableCalls = 0;
    check(patch(eax));
    const uint8_t expectedEax[] = {0x90,0x90,0x90, 0xB8,0x00,0x00,0xC0,0x03};
    check(std::memcmp(eax.data(), expectedEax, sizeof(expectedEax)) == 0);
    check(eax[8] == saved[8] && enableCalls == 1 && disableCalls == 1);
    for (unsigned reg = 0; reg < 16; ++reg) {
        std::array<uint8_t,128> code {}; code.fill(0xC3); unsigned n = 0;
        if (reg >= 8) code[n++] = 0x41;
        code[n++] = 0xC1; code[n++] = 0xE0 + (reg & 7); code[n++] = 0x11;
        const unsigned shiftSize = n, andStart = n;
        if (reg >= 8) code[n++] = 0x41;
        code[n++] = 0x81; code[n++] = 0xE0 + (reg & 7);
        code[n++] = 0; code[n++] = 0; code[n++] = 0; code[n++] = 0xFE;
        check(patch(code));
        for (unsigned i = 0; i < shiftSize; ++i) assert(code[i] == 0x90);
        unsigned cursor = andStart;
        if (reg >= 8) assert(code[cursor++] == 0x41);
        check(code[cursor] == (0xB8 + (reg & 7)) && code[n-1] == 0x90 && code[n] == 0xC3);
    }
    // Wrong group opcode, memory operand, 64-bit/prefixed width, different
    // register, intervening write, branches, and truncated image all reject.
    for (auto bad : {
        image({0xC1,0xE8,0x11,0x25,0,0,0,0xFE}),
        image({0xC1,0x20,0x11,0x25,0,0,0,0xFE}),
        image({0x48,0xC1,0xE0,0x11,0x25,0,0,0,0xFE}),
        image({0x66,0xC1,0xE0,0x11,0x25,0,0,0,0xFE}),
        image({0xC1,0xE0,0x11,0x81,0xE1,0,0,0,0xFE}),
        image({0xC1,0xE0,0x11,0x81,0xC0,0,0,0,0xFE}),
        image({0xC1,0xE0,0x11,0x81,0x20,0,0,0,0xFE}),
        image({0xC1,0xE0,0x11,0x90,0x25,0,0,0,0xFE}),
        image({0xC3,0xC1,0xE0,0x11,0x25,0,0,0,0xFE}),
        image({0xEB,0,0xC1,0xE0,0x11,0x25,0,0,0,0xFE}),
    }) { auto before = bad; check(!patch(bad) && bad == before); }
    auto good = image({0xC1,0xE0,0x11,0x25,0,0,0,0xFE});
    saved = good; check(!patch(good, 0) && good == saved);
    auto base = reinterpret_cast<uintptr_t>(good.data()); decodeCalls = 0;
    check(!patchStolenMemoryFormula(base, base, 31, 0x400000) && decodeCalls == 0);
    check(!patchStolenMemoryFormula(base+97, base, 128, 0x400000) && decodeCalls == 0);
    check(!patchStolenMemoryFormula(base-1, base, 128, 0x400000) && decodeCalls == 0);
    std::printf("{\"native_assertion_groups\":%u,\"decoder\":\"upstream HDE64\"}\n", cases);
}
