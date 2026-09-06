#pragma once

#include <cstddef>
#include <cstdint>

// Independently named ABI declarations for the small OpenCL 1.2 dynamic-loader
// surface used here. Sizes, calling convention, signatures and enum values are
// defined by Khronos OpenCL-Headers/CL/cl.h and CL/cl_ext.h:
// https://github.com/KhronosGroup/OpenCL-Headers/blob/main/CL/cl.h
// https://github.com/KhronosGroup/OpenCL-Headers/blob/main/CL/cl_ext.h
// No SDK, proprietary headers, or compiler implementation is embedded.
#if defined(_WIN32)
#define MELLOW_CL_CALL __stdcall
#else
#define MELLOW_CL_CALL
#endif

namespace MellowRT::OpenCLAbi {
using Int = int32_t;
using UInt = uint32_t;
using Bits = uint64_t;
using Handle = void *;
using ContextCallback = void (MELLOW_CL_CALL *)(const char *, const void *, size_t, void *);
using BuildCallback = void (MELLOW_CL_CALL *)(Handle, void *);
constexpr Int Success = 0, DeviceNotFound = -1, PlatformNotFound = -1001;
constexpr Bits Gpu = 4, Cpu = 2, ProfilingQueue = 2, ReadWriteCopy = 1 | 32;
constexpr UInt VendorId = 0x1001, DeviceType = 0x1000, DeviceName = 0x102B;
constexpr UInt DeviceVendor = 0x102C, DriverVersion = 0x102D, DeviceVersion = 0x102F;
constexpr UInt DeviceExtensions = 0x1030, DeviceAvailable = 0x1027, CompilerAvailable = 0x1028;
constexpr UInt IntelDeviceId = 0x4251, QueueContext = 0x1090, QueueDevice = 0x1091, QueueProperties = 0x1093;
constexpr UInt EventQueue = 0x11D0, EventCommand = 0x11D1, EventStatus = 0x11D3, EventContext = 0x11D4;
constexpr UInt KernelCommand = 0x11F0, ProfileStart = 0x1282, ProfileEnd = 0x1283, ProgramBuildLog = 0x1183;

#define MELLOW_CL_FUNCTIONS(X) \
    X(GetPlatformIDs, Int, UInt, Handle *, UInt *) \
    X(GetPlatformInfo, Int, Handle, UInt, size_t, void *, size_t *) \
    X(GetDeviceIDs, Int, Handle, Bits, UInt, Handle *, UInt *) \
    X(GetDeviceInfo, Int, Handle, UInt, size_t, void *, size_t *) \
    X(CreateContext, Handle, const intptr_t *, UInt, const Handle *, ContextCallback, void *, Int *) \
    X(CreateCommandQueue, Handle, Handle, Handle, Bits, Int *) \
    X(GetCommandQueueInfo, Int, Handle, UInt, size_t, void *, size_t *) \
    X(CreateProgramWithSource, Handle, Handle, UInt, const char **, const size_t *, Int *) \
    X(BuildProgram, Int, Handle, UInt, const Handle *, const char *, BuildCallback, void *) \
    X(GetProgramBuildInfo, Int, Handle, Handle, UInt, size_t, void *, size_t *) \
    X(CreateKernel, Handle, Handle, const char *, Int *) \
    X(CreateBuffer, Handle, Handle, Bits, size_t, void *, Int *) \
    X(SetKernelArg, Int, Handle, UInt, size_t, const void *) \
    X(EnqueueNDRangeKernel, Int, Handle, Handle, UInt, const size_t *, const size_t *, const size_t *, UInt, const Handle *, Handle *) \
    X(WaitForEvents, Int, UInt, const Handle *) \
    X(GetEventInfo, Int, Handle, UInt, size_t, void *, size_t *) \
    X(GetEventProfilingInfo, Int, Handle, UInt, size_t, void *, size_t *) \
    X(EnqueueReadBuffer, Int, Handle, Handle, UInt, size_t, size_t, void *, UInt, const Handle *, Handle *) \
    X(Finish, Int, Handle) \
    X(ReleaseEvent, Int, Handle) \
    X(ReleaseMemObject, Int, Handle) \
    X(ReleaseKernel, Int, Handle) \
    X(ReleaseProgram, Int, Handle) \
    X(ReleaseCommandQueue, Int, Handle) \
    X(ReleaseContext, Int, Handle)
struct Functions {
#define MELLOW_DECLARE(name, result, ...) using name##Fn = result (MELLOW_CL_CALL *)(__VA_ARGS__); name##Fn name {};
    MELLOW_CL_FUNCTIONS(MELLOW_DECLARE)
#undef MELLOW_DECLARE
};
static_assert(sizeof(Int) == 4 && sizeof(UInt) == 4 && sizeof(Bits) == 8, "OpenCL ABI widths");
} // namespace MellowRT::OpenCLAbi
