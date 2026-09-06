#pragma once

#include "OpenCLProvider.hpp"
#include "ShaderJit.hpp"
#include <memory>
#include <mutex>
#include <string>
#include <vector>

// Explicit opt-in portable Mellow object API. These are NOT Objective-C Metal
// protocol implementations, and do not register a system MTLDevice.
// Command buffers/encoders and status/executions access are single-thread use.
// Buffer copies are locked; device compilation and synchronous commits serialize.
namespace MellowMTL {
enum class ErrorCode { None, InvalidArgument, InvalidState, WrongDevice, Unsupported, Compilation, Execution };
struct Error { ErrorCode code {ErrorCode::None}; std::string message; };
enum class CommandStatus { NotEnqueued, Encoding, Executable, Committed, Completed, Error };
class Device; class Buffer; class Library; class Function; class ComputePipeline;
class CommandQueue; class CommandBuffer; class ComputeEncoder;

class Device : public std::enable_shared_from_this<Device> {
public:
    static std::shared_ptr<Device> createOpenCL(size_t gpuIndex, Error &error);
    std::shared_ptr<Buffer> newBuffer(const std::vector<uint32_t> &words, Error &error);
    std::shared_ptr<Library> newLibraryWithSource(const std::string &msl, Error &error);
    std::shared_ptr<Library> newLibraryWithAirText(const std::string &decodedAir, Error &error);
    std::shared_ptr<Library> newLibraryWithAir(const std::vector<uint8_t> &air, Error &error);
    std::shared_ptr<Library> newLibraryWithAir(const std::vector<uint8_t> &air,
                                               const std::string &llvmLibrary, Error &error);
    std::shared_ptr<ComputePipeline> newComputePipeline(const std::shared_ptr<Function> &, Error &error);
    std::shared_ptr<CommandQueue> newCommandQueue();
    const MellowRT::OpenCLDeviceInfo &hardware() const;
    const MellowRT::OpenCLExecution &bootstrapEvidence() const;
    uint64_t pipelineBuildCount() const;
private:
    friend class CommandBuffer;
    Device();
    std::shared_ptr<MellowRT::OpenCLProvider> provider_;
    mutable std::mutex submissionMutex_;
};

class Buffer {
public:
    size_t length() const;
    size_t elementCount() const;
    std::vector<uint32_t> read() const;
    bool write(const std::vector<uint32_t> &words, Error &error);
private:
    friend class Device; friend class ComputeEncoder; friend class CommandBuffer;
    Buffer(std::shared_ptr<Device>, std::vector<uint32_t>);
    std::shared_ptr<Device> device_;
    mutable std::mutex mutex_;
    std::vector<uint32_t> words_;
};

class Library : public std::enable_shared_from_this<Library> {
public:
    std::shared_ptr<Function> newFunction(const std::string &entry, Error &error);
private:
    friend class Device;
    Library(std::shared_ptr<Device>, MellowRT::ShaderJit::InputKind, std::string,
            std::vector<uint8_t> = {}, std::string llvmLibrary = {});
    std::shared_ptr<Device> device_;
    MellowRT::ShaderJit::InputKind input_;
    std::string source_;
    std::vector<uint8_t> bytes_;
    std::string llvmLibrary_;
};

class Function {
public:
    const std::string &name() const;
    const MellowRT::ShaderJit::Reflection &reflection() const;
private:
    friend class Library; friend class Device;
    Function(std::shared_ptr<Device>, std::shared_ptr<Library>, MellowRT::ShaderJit::CompileResult);
    std::shared_ptr<Device> device_;
    std::shared_ptr<Library> library_;
    MellowRT::ShaderJit::CompileResult translated_;
};

class ComputePipeline {
public:
    uint64_t compilationSerial() const;
    const std::string &buildLog() const;
private:
    friend class Device; friend class ComputeEncoder; friend class CommandBuffer;
    ComputePipeline(std::shared_ptr<Device>, std::shared_ptr<Function>, std::shared_ptr<MellowRT::OpenCLPipeline>);
    std::shared_ptr<Device> device_;
    std::shared_ptr<Function> function_;
    std::shared_ptr<MellowRT::OpenCLPipeline> compiled_;
};

class CommandQueue : public std::enable_shared_from_this<CommandQueue> {
public:
    std::shared_ptr<CommandBuffer> commandBuffer();
private:
    friend class Device; friend class CommandBuffer; friend class ComputeEncoder;
    explicit CommandQueue(std::shared_ptr<Device>);
    std::shared_ptr<Device> device_;
};

class CommandBuffer : public std::enable_shared_from_this<CommandBuffer> {
public:
    std::shared_ptr<ComputeEncoder> computeCommandEncoder(Error &error);
    // commit is synchronous: Committed -> driver work/readback -> Completed/Error.
    // It never takes a caller-provided expected result as a prerequisite.
    bool commit(Error &error);
    bool waitUntilCompleted(Error &error) const;
    CommandStatus status() const;
    const std::vector<MellowRT::OpenCLExecution> &executions() const;
private:
    friend class CommandQueue; friend class ComputeEncoder;
    explicit CommandBuffer(std::shared_ptr<CommandQueue>);
    struct Dispatch { std::shared_ptr<ComputePipeline> pipeline; std::shared_ptr<Buffer> buffer; size_t threads {}; };
    std::shared_ptr<CommandQueue> queue_;
    CommandStatus status_ {CommandStatus::NotEnqueued};
    Error failure_;
    std::vector<Dispatch> dispatches_;
    std::vector<MellowRT::OpenCLExecution> executions_;
};

class ComputeEncoder {
public:
    ~ComputeEncoder();
    bool setComputePipeline(const std::shared_ptr<ComputePipeline> &, Error &error);
    bool setBuffer(const std::shared_ptr<Buffer> &, uint32_t index, Error &error);
    bool dispatchThreads(size_t threadCount, Error &error);
    bool endEncoding(Error &error);
private:
    friend class CommandBuffer;
    explicit ComputeEncoder(std::shared_ptr<CommandBuffer>);
    bool active(Error &error) const;
    std::shared_ptr<CommandBuffer> command_;
    std::shared_ptr<ComputePipeline> pipeline_;
    std::shared_ptr<Buffer> buffer_;
    bool ended_ {};
};
} // namespace MellowMTL
