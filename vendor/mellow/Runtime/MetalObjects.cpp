#include "MetalObjects.hpp"
#include <sstream>
#include <utility>

namespace MellowMTL {
namespace {
bool fail(Error &error, ErrorCode code, const std::string &message) { error = {code, message}; return false; }
std::string diagnostics(const std::vector<std::string> &messages) {
    std::ostringstream text;
    for (const auto &message : messages) text << message << '\n';
    return text.str();
}
bool sourceSize(size_t count, Error &error) {
    return (count && count <= MellowRT::ShaderJit::MaxSourceBytes) ||
           fail(error, ErrorCode::InvalidArgument, "Shader input must be 1-65536 bytes");
}
}
Device::Device() : provider_(std::make_shared<MellowRT::OpenCLProvider>()) {}
std::shared_ptr<Device> Device::createOpenCL(size_t index, Error &error) {
    error = {};
    auto device = std::shared_ptr<Device>(new Device());
    std::string failure;
    if (!device->provider_->initialize(index, failure)) { fail(error, ErrorCode::Execution, failure); return {}; }
    return device;
}
std::shared_ptr<Buffer> Device::newBuffer(const std::vector<uint32_t> &words, Error &error) {
    error = {};
    if (words.empty() || words.size() > MellowRT::OpenCLProvider::MaxElements) {
        fail(error, ErrorCode::InvalidArgument, "Only 1-4096 uint32 elements are supported"); return {};
    }
    return std::shared_ptr<Buffer>(new Buffer(shared_from_this(), words));
}
std::shared_ptr<Library> Device::newLibraryWithSource(const std::string &source, Error &error) {
    error = {};
    if (!sourceSize(source.size(), error)) return {};
    return std::shared_ptr<Library>(new Library(shared_from_this(), MellowRT::ShaderJit::InputKind::MslSource, source));
}
std::shared_ptr<Library> Device::newLibraryWithAirText(const std::string &source, Error &error) {
    error = {};
    if (!sourceSize(source.size(), error)) return {};
    return std::shared_ptr<Library>(new Library(shared_from_this(), MellowRT::ShaderJit::InputKind::AirLlvmText, source));
}
std::shared_ptr<Library> Device::newLibraryWithAir(const std::vector<uint8_t> &source, Error &error) {
    return newLibraryWithAir(source, {}, error);
}
std::shared_ptr<Library> Device::newLibraryWithAir(const std::vector<uint8_t> &source,
                                                const std::string &llvmLibrary, Error &error) {
    error = {};
    if (!sourceSize(source.size(), error)) return {};
    return std::shared_ptr<Library>(new Library(shared_from_this(), MellowRT::ShaderJit::InputKind::AirBitcode, {}, source, llvmLibrary));
}
std::shared_ptr<ComputePipeline> Device::newComputePipeline(const std::shared_ptr<Function> &function, Error &error) {
    error = {};
    if (!function) { fail(error, ErrorCode::InvalidArgument, "Function is null"); return {}; }
    if (function->device_.get() != this) { fail(error, ErrorCode::WrongDevice, "Function belongs to another device"); return {}; }
    const auto &reflection = function->reflection();
    if (reflection.buffers.size() != 1 || reflection.buffers[0].index != 0 ||
        reflection.buffers[0].elementType != "uint" || !reflection.buffers[0].writable || !reflection.requiresExactDispatch) {
        fail(error, ErrorCode::Unsupported, "Pipeline requires exactly one writable uint buffer(0) with exact 1D dispatch"); return {};
    }
    std::lock_guard<std::mutex> lock(submissionMutex_);
    std::string failure;
    auto compiled = provider_->compileOpenClC(function->translated_.openclSource, reflection.entry, failure);
    if (!compiled) { fail(error, ErrorCode::Compilation, failure); return {}; }
    return std::shared_ptr<ComputePipeline>(new ComputePipeline(shared_from_this(), function, compiled));
}
std::shared_ptr<CommandQueue> Device::newCommandQueue() {
    return std::shared_ptr<CommandQueue>(new CommandQueue(shared_from_this()));
}
const MellowRT::OpenCLDeviceInfo &Device::hardware() const { return provider_->device(); }
const MellowRT::OpenCLExecution &Device::bootstrapEvidence() const { return provider_->bootstrapEvidence(); }
uint64_t Device::pipelineBuildCount() const { std::lock_guard<std::mutex> lock(submissionMutex_); return provider_->pipelineBuildCount(); }

Buffer::Buffer(std::shared_ptr<Device> device, std::vector<uint32_t> words) : device_(std::move(device)), words_(std::move(words)) {}
size_t Buffer::length() const { return elementCount() * sizeof(uint32_t); }
size_t Buffer::elementCount() const { std::lock_guard<std::mutex> lock(mutex_); return words_.size(); }
std::vector<uint32_t> Buffer::read() const { std::lock_guard<std::mutex> lock(mutex_); return words_; }
bool Buffer::write(const std::vector<uint32_t> &words, Error &error) {
    error = {};
    std::lock_guard<std::mutex> lock(mutex_);
    if (words.size() != words_.size()) return fail(error, ErrorCode::InvalidArgument, "Buffer size is immutable");
    words_ = words;
    return true;
}

Library::Library(std::shared_ptr<Device> device, MellowRT::ShaderJit::InputKind input, std::string source,
                 std::vector<uint8_t> bytes, std::string llvmLibrary)
    : device_(std::move(device)), input_(input), source_(std::move(source)), bytes_(std::move(bytes)),
      llvmLibrary_(std::move(llvmLibrary)) {}
std::shared_ptr<Function> Library::newFunction(const std::string &entry, Error &error) {
    error = {};
    MellowRT::ShaderJit::CompileResult translated;
    switch (input_) {
        case MellowRT::ShaderJit::InputKind::MslSource: translated = MellowRT::ShaderJit::compileMsl(source_, entry); break;
        case MellowRT::ShaderJit::InputKind::AirBitcode:
            translated = MellowRT::ShaderJit::compileAir(bytes_, entry, llvmLibrary_); break;
        case MellowRT::ShaderJit::InputKind::AirLlvmText: translated = MellowRT::ShaderJit::compileAirText(source_, entry); break;
    }
    if (!translated.success) { fail(error, ErrorCode::Compilation, diagnostics(translated.diagnostics)); return {}; }
    return std::shared_ptr<Function>(new Function(device_, shared_from_this(), std::move(translated)));
}
Function::Function(std::shared_ptr<Device> device, std::shared_ptr<Library> library, MellowRT::ShaderJit::CompileResult translated)
    : device_(std::move(device)), library_(std::move(library)), translated_(std::move(translated)) {}
const std::string &Function::name() const { return translated_.reflection.entry; }
const MellowRT::ShaderJit::Reflection &Function::reflection() const { return translated_.reflection; }
ComputePipeline::ComputePipeline(std::shared_ptr<Device> device, std::shared_ptr<Function> function, std::shared_ptr<MellowRT::OpenCLPipeline> compiled)
    : device_(std::move(device)), function_(std::move(function)), compiled_(std::move(compiled)) {}
uint64_t ComputePipeline::compilationSerial() const { return compiled_->compilationSerial(); }
const std::string &ComputePipeline::buildLog() const { return compiled_->buildLog(); }

CommandQueue::CommandQueue(std::shared_ptr<Device> device) : device_(std::move(device)) {}
std::shared_ptr<CommandBuffer> CommandQueue::commandBuffer() {
    return std::shared_ptr<CommandBuffer>(new CommandBuffer(shared_from_this()));
}
CommandBuffer::CommandBuffer(std::shared_ptr<CommandQueue> queue) : queue_(std::move(queue)) {}
std::shared_ptr<ComputeEncoder> CommandBuffer::computeCommandEncoder(Error &error) {
    error = {};
    if (status_ != CommandStatus::NotEnqueued && status_ != CommandStatus::Executable) {
        fail(error, ErrorCode::InvalidState, "Command buffer cannot begin another encoder in its current state"); return {};
    }
    status_ = CommandStatus::Encoding;
    return std::shared_ptr<ComputeEncoder>(new ComputeEncoder(shared_from_this()));
}
bool CommandBuffer::commit(Error &error) {
    error = {};
    if (status_ != CommandStatus::Executable || dispatches_.empty())
        return fail(error, ErrorCode::InvalidState, "End an encoder containing work before commit");
    status_ = CommandStatus::Committed;
    auto device = queue_->device_;
    std::lock_guard<std::mutex> executionLock(device->submissionMutex_);
    for (const auto &dispatch : dispatches_) {
        std::lock_guard<std::mutex> bufferLock(dispatch.buffer->mutex_);
        MellowRT::OpenCLExecution result;
        const bool completed = device->provider_->executePipeline(dispatch.pipeline->compiled_, dispatch.buffer->words_, result);
        executions_.push_back(result);
        if (!completed || !result.executionCompleted || !result.eventOwnershipVerified || !result.resourcesReleased) {
            status_ = CommandStatus::Error;
            failure_ = {ErrorCode::Execution, result.error.empty() ? "GPU execution did not complete" : result.error};
            error = failure_;
            return false;
        }
        dispatch.buffer->words_ = result.output;
    }
    status_ = CommandStatus::Completed;
    return true;
}
bool CommandBuffer::waitUntilCompleted(Error &error) const {
    error = {};
    if (status_ == CommandStatus::Completed) return true;
    if (status_ == CommandStatus::Error) { error = failure_; return false; }
    return fail(error, ErrorCode::InvalidState, "Synchronous command buffer has not completed; call commit first");
}
CommandStatus CommandBuffer::status() const { return status_; }
const std::vector<MellowRT::OpenCLExecution> &CommandBuffer::executions() const { return executions_; }

ComputeEncoder::ComputeEncoder(std::shared_ptr<CommandBuffer> command) : command_(std::move(command)) {}
ComputeEncoder::~ComputeEncoder() {
    if (!ended_ && command_->status_ == CommandStatus::Encoding) {
        command_->status_ = CommandStatus::Error;
        command_->failure_ = {ErrorCode::InvalidState, "Compute encoder was destroyed before endEncoding"};
    }
}
bool ComputeEncoder::active(Error &error) const {
    return (!ended_ && command_->status_ == CommandStatus::Encoding) ||
        fail(error, ErrorCode::InvalidState, "Compute encoder is no longer active");
}
bool ComputeEncoder::setComputePipeline(const std::shared_ptr<ComputePipeline> &pipeline, Error &error) {
    error = {};
    if (!active(error)) return false;
    if (!pipeline) return fail(error, ErrorCode::InvalidArgument, "Pipeline is null");
    if (pipeline->device_ != command_->queue_->device_) return fail(error, ErrorCode::WrongDevice, "Pipeline belongs to another device");
    pipeline_ = pipeline;
    return true;
}
bool ComputeEncoder::setBuffer(const std::shared_ptr<Buffer> &buffer, uint32_t index, Error &error) {
    error = {};
    if (!active(error)) return false;
    if (!buffer) return fail(error, ErrorCode::InvalidArgument, "Buffer is null");
    if (index != 0) return fail(error, ErrorCode::Unsupported, "Only buffer binding 0 is supported");
    if (buffer->device_ != command_->queue_->device_) return fail(error, ErrorCode::WrongDevice, "Buffer belongs to another device");
    buffer_ = buffer;
    return true;
}
bool ComputeEncoder::dispatchThreads(size_t threads, Error &error) {
    error = {};
    if (!active(error)) return false;
    if (!pipeline_ || !buffer_) return fail(error, ErrorCode::InvalidState, "Set a pipeline and buffer before dispatch");
    if (threads != buffer_->elementCount()) return fail(error, ErrorCode::Unsupported, "Dispatch must exactly match buffer element count in one dimension");
    if (command_->dispatches_.size() >= 64) return fail(error, ErrorCode::Unsupported, "At most 64 dispatches per command buffer");
    command_->dispatches_.push_back({pipeline_, buffer_, threads});
    return true;
}
bool ComputeEncoder::endEncoding(Error &error) {
    error = {};
    if (!active(error)) return false;
    ended_ = true;
    command_->status_ = CommandStatus::Executable;
    return true;
}
} // namespace MellowMTL
