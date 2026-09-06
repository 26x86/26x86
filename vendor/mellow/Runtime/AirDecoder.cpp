// SPDX-License-Identifier: MIT
// Dynamic ABI declarations follow LLVM 20.1.8 include/llvm-c/{Core,BitReader,
// Analysis}.h. No private Apple AIR/compiler ABI is called. The verified LLVM
// module still must pass ShaderJit's separate AIR metadata and SSA lowering.
#include "AirDecoder.hpp"
#include <cstring>
#include <memory>
#include <stdexcept>
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace MellowRT { namespace ShaderJit {
namespace {
constexpr size_t MaxBitcode = 4 * 1024 * 1024;
constexpr size_t MaxIr = 65536;
void check(bool ok, const char *message) { if (!ok) throw std::runtime_error(message); }
uint32_t word(const std::vector<uint8_t> &bytes, size_t at) {
    return uint32_t(bytes[at]) | uint32_t(bytes[at + 1]) << 8 | uint32_t(bytes[at + 2]) << 16 | uint32_t(bytes[at + 3]) << 24;
}
std::string bounded(const char *text, size_t maximum) {
    if (!text) return {};
    size_t count = 0;
    while (count < maximum && text[count]) ++count;
    check(count < maximum, "LLVM text exceeds supported byte limit");
    return std::string(text, count);
}
class Library {
public:
    explicit Library(const std::string &path) {
        check(path.find('\0') == std::string::npos, "LLVM library path contains NUL");
#if defined(_WIN32)
        check(path.size() > 3 && ((path[0] >= 'A' && path[0] <= 'Z') || (path[0] >= 'a' && path[0] <= 'z')) &&
              path[1] == ':' && (path[2] == '/' || path[2] == '\\'), "Explicit absolute LLVM DLL path required");
        const int length = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, path.c_str(), -1, nullptr, 0);
        check(length > 0, "Invalid UTF-8 LLVM DLL path");
        std::vector<wchar_t> wide(static_cast<size_t>(length));
        check(MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, path.c_str(), -1, wide.data(), length) == length,
              "Cannot convert LLVM DLL path");
        handle_ = LoadLibraryExW(wide.data(), nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
        check(handle_ != nullptr, "Cannot load the specified LLVM C API library");
        // Actual LLVM-C 20.1.8 Windows testing reproduced C0000005 at process
        // exit after FreeLibrary, even after all contexts/modules were disposed.
        // Keeping its code mapped removed the failure for both accepted/rejected
        // inputs. Pin the DLL for process lifetime; the local LoadLibrary reference
        // is still balanced below. Do not call process-global LLVMShutdown, which
        // could invalidate another client's live LLVM state.
        HMODULE pinned {};
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                                reinterpret_cast<LPCWSTR>(handle_), &pinned)) {
            FreeLibrary(handle_); handle_ = nullptr;
            throw std::runtime_error("Cannot retain LLVM DLL safely for process lifetime");
        }
#else
        check(!path.empty() && path[0] == '/', "Explicit absolute LLVM shared-library path required");
        handle_ = dlopen(path.c_str(), RTLD_NOW | RTLD_LOCAL);
#endif
        check(handle_ != nullptr, "Cannot load the specified LLVM C API library");
    }
    ~Library() {
        if (!handle_) return;
#if defined(_WIN32)
        FreeLibrary(handle_);
#else
        dlclose(handle_);
#endif
    }
    template<typename T> void load(T &function, const char *name) {
#if defined(_WIN32)
        const auto address = GetProcAddress(handle_, name);
#else
        const auto address = dlsym(handle_, name);
#endif
        check(address != nullptr, "Required LLVM C API symbol missing");
        static_assert(sizeof(function) == sizeof(address), "LLVM dynamic function ABI");
        std::memcpy(&function, &address, sizeof(function));
    }
private:
#if defined(_WIN32)
    HMODULE handle_ {};
#else
    void *handle_ {};
#endif
};
struct Api {
    using Ref = void *;
    void (*GetVersion)(unsigned *, unsigned *, unsigned *) {};
    Ref (*ContextCreate)() {};
    void (*ContextDispose)(Ref) {};
    void (*ContextSetDiagnosticHandler)(Ref, void (*)(Ref, void *), void *) {};
    Ref (*CreateMemoryBufferWithMemoryRangeCopy)(const char *, size_t, const char *) {};
    void (*DisposeMemoryBuffer)(Ref) {};
    int (*ParseBitcodeInContext2)(Ref, Ref, Ref *) {};
    int (*VerifyModule)(Ref, int, char **) {};
    char *(*PrintModuleToString)(Ref) {};
    void (*DisposeModule)(Ref) {};
    void (*DisposeMessage)(char *) {};
    explicit Api(Library &library) {
#define LOAD(name) library.load(name, "LLVM" #name)
        LOAD(GetVersion); LOAD(ContextCreate); LOAD(ContextDispose); LOAD(ContextSetDiagnosticHandler);
        LOAD(CreateMemoryBufferWithMemoryRangeCopy); LOAD(DisposeMemoryBuffer); LOAD(ParseBitcodeInContext2);
        LOAD(VerifyModule); LOAD(PrintModuleToString); LOAD(DisposeModule); LOAD(DisposeMessage);
#undef LOAD
    }
};
struct Resources {
    Api &api;
    Api::Ref context {}, memory {}, module {};
    char *message {}, *printed {};
    ~Resources() {
        if (printed) api.DisposeMessage(printed);
        if (message) api.DisposeMessage(message);
        if (module) api.DisposeModule(module);
        if (memory) api.DisposeMemoryBuffer(memory);
        if (context) api.ContextDispose(context);
    }
};
// LLVM's default handler may print unbounded shader diagnostics. Parse failure
// is reported through its return code; do not throw across this C callback.
void ignoreDiagnostic(Api::Ref, void *) {}
}

bool decodeAirBitcode(const std::vector<uint8_t> &bytes, const std::string &path,
                     std::string &ir, std::string &error) {
    ir.clear(); error.clear();
    try {
        check(bytes.size() >= 4 && bytes.size() <= MaxBitcode, "AIR bitcode size outside 4 bytes..4 MiB");
        size_t offset = 0, size = bytes.size();
        if (word(bytes, 0) == 0x0b17c0de) {
            check(bytes.size() >= 20 && word(bytes, 4) == 0, "Unsupported or truncated LLVM wrapper");
            offset = word(bytes, 8); size = word(bytes, 12);
            check(offset >= 20 && size >= 4 && offset <= bytes.size() && size <= bytes.size() - offset,
                  "LLVM wrapper payload outside input");
            check(bytes.size() - offset - size <= 15, "Unexpected trailing LLVM wrapper bytes");
            for (size_t i = offset + size; i < bytes.size(); ++i) check(bytes[i] == 0, "Nonzero LLVM wrapper padding");
        }
        check(word(bytes, offset) == 0xdec04342, "Missing raw LLVM bitcode magic");
        Library library(path);
        Api api(library);
        unsigned major = 0, minor = 0, patch = 0;
        api.GetVersion(&major, &minor, &patch);
        check(major >= 18 && major <= 20, "This decoder admits LLVM C API majors 18 through 20 only");
        Resources resources {api, nullptr, nullptr, nullptr, nullptr, nullptr};
        resources.context = api.ContextCreate();
        check(resources.context != nullptr, "Cannot create LLVM context");
        api.ContextSetDiagnosticHandler(resources.context, ignoreDiagnostic, nullptr);
        resources.memory = api.CreateMemoryBufferWithMemoryRangeCopy(
            reinterpret_cast<const char *>(bytes.data() + offset), size, "mellow-input.air");
        check(resources.memory != nullptr, "Cannot create LLVM bitcode memory buffer");
        check(api.ParseBitcodeInContext2(resources.context, resources.memory, &resources.module) == 0 && resources.module,
              "LLVM rejected bitcode input (invalid or unsupported format)");
        // LLVMReturnStatusAction == 2 is public LLVMVerifierFailureAction.
        check(api.VerifyModule(resources.module, 2, &resources.message) == 0,
              "LLVM verifier rejected module");
        resources.printed = api.PrintModuleToString(resources.module);
        check(resources.printed != nullptr, "LLVM module printer failed");
        auto decoded = bounded(resources.printed, MaxIr + 1);
        check(!decoded.empty(), "LLVM emitted empty assembly");
        ir = std::move(decoded);
        return true;
    } catch (const std::exception &failure) {
        ir.clear(); error = failure.what(); return false;
    }
}
} }
