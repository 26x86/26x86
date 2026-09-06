// SPDX-License-Identifier: MIT
#include "OpenGLProvider.hpp"
#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <condition_variable>
#include <cstring>
#include <deque>
#include <functional>
#include <future>
#include <limits>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <utility>
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <GL/gl.h>
#include <GL/glext.h>
#include <GL/wglext.h>
#endif

namespace MellowRT {
namespace {
void require(bool condition, const std::string &message) {
    if (!condition) throw std::runtime_error(message);
}
bool dimensions(uint32_t width, uint32_t height) {
    return width && height && width <= OpenGLProvider::MaxDimension && height <= OpenGLProvider::MaxDimension;
}
#if defined(_WIN32)
// Function declarations come from public Khronos GL/wglext headers.
// https://registry.khronos.org/OpenGL/extensions/ARB/WGL_ARB_create_context.txt
// https://registry.khronos.org/OpenGL/api/GL/glext.h
template<typename T> T symbol(const char *name) {
    auto procedure = wglGetProcAddress(name);
    const auto numeric = reinterpret_cast<intptr_t>(procedure);
    require(procedure && numeric != 1 && numeric != 2 && numeric != 3 && numeric != -1,
            std::string("Required OpenGL entry unavailable: ") + name);
    T result {};
    static_assert(sizeof(result) == sizeof(procedure), "Function pointer ABI mismatch");
    std::memcpy(&result, &procedure, sizeof(result));
    return result;
}
void glCheck(const char *operation) {
    const auto error = glGetError();
    require(error == GL_NO_ERROR, std::string(operation) + " OpenGL error " + std::to_string(error));
}
std::string glText(GLenum key) {
    auto text = glGetString(key);
    require(text != nullptr, "Missing OpenGL driver identity string");
    const auto size = std::strlen(reinterpret_cast<const char *>(text));
    require(size && size < 16384, "OpenGL identity string outside bounds");
    return std::string(reinterpret_cast<const char *>(text), size);
}
#define GL_PROCS(X) \
    X(CreateShader, PFNGLCREATESHADERPROC) X(ShaderSource, PFNGLSHADERSOURCEPROC) \
    X(CompileShader, PFNGLCOMPILESHADERPROC) X(GetShaderiv, PFNGLGETSHADERIVPROC) \
    X(GetShaderInfoLog, PFNGLGETSHADERINFOLOGPROC) X(DeleteShader, PFNGLDELETESHADERPROC) \
    X(CreateProgram, PFNGLCREATEPROGRAMPROC) X(AttachShader, PFNGLATTACHSHADERPROC) \
    X(LinkProgram, PFNGLLINKPROGRAMPROC) X(GetProgramiv, PFNGLGETPROGRAMIVPROC) \
    X(GetProgramInfoLog, PFNGLGETPROGRAMINFOLOGPROC) X(DeleteProgram, PFNGLDELETEPROGRAMPROC) \
    X(UseProgram, PFNGLUSEPROGRAMPROC) X(GenVertexArrays, PFNGLGENVERTEXARRAYSPROC) \
    X(BindVertexArray, PFNGLBINDVERTEXARRAYPROC) X(DeleteVertexArrays, PFNGLDELETEVERTEXARRAYSPROC) \
    X(GenFramebuffers, PFNGLGENFRAMEBUFFERSPROC) X(BindFramebuffer, PFNGLBINDFRAMEBUFFERPROC) \
    X(FramebufferTexture2D, PFNGLFRAMEBUFFERTEXTURE2DPROC) X(CheckFramebufferStatus, PFNGLCHECKFRAMEBUFFERSTATUSPROC) \
    X(DeleteFramebuffers, PFNGLDELETEFRAMEBUFFERSPROC) X(FenceSync, PFNGLFENCESYNCPROC) \
    X(ClientWaitSync, PFNGLCLIENTWAITSYNCPROC) X(DeleteSync, PFNGLDELETESYNCPROC) \
    X(BlitFramebuffer, PFNGLBLITFRAMEBUFFERPROC) X(GetUniformLocation, PFNGLGETUNIFORMLOCATIONPROC) \
    X(Uniform4fv, PFNGLUNIFORM4FVPROC) X(Uniform2f, PFNGLUNIFORM2FPROC)
struct Api {
#define DECLARE_GL(name, type) type name {};
    GL_PROCS(DECLARE_GL)
#undef DECLARE_GL
    PFNWGLGETSWAPINTERVALEXTPROC GetSwapInterval {};
    void load() {
#define LOAD_GL(name, type) name = symbol<type>("gl" #name);
        GL_PROCS(LOAD_GL)
#undef LOAD_GL
        try { GetSwapInterval = symbol<PFNWGLGETSWAPINTERVALEXTPROC>("wglGetSwapIntervalEXT"); }
        catch (const std::exception &) { GetSwapInterval = nullptr; }
    }
};
LRESULT CALLBACK windowProc(HWND window, UINT message, WPARAM wparam, LPARAM lparam) {
    return DefWindowProcW(window, message, wparam, lparam);
}
#endif
}

struct OpenGLProvider::Impl {
    std::thread worker;
    std::mutex mutex;
    std::condition_variable condition;
    std::deque<std::function<void()>> tasks;
    bool stopping {}, ready {};
    uint64_t epoch {1}, sequence {}, compilations {};
    OpenGLDeviceInfo info;
#if defined(_WIN32)
    HWND window {};
    HDC dc {};
    HGLRC context {};
    HINSTANCE instance {};
    std::wstring className;
    ATOM windowClass {};
    Api gl;
#endif
    Impl() { worker = std::thread([this] { loop(); }); }
    template<typename F> auto invoke(F &&function) -> decltype(function()) {
        using Result = decltype(function());
        if (std::this_thread::get_id() == worker.get_id()) return function();
        auto task = std::make_shared<std::packaged_task<Result()>>(std::forward<F>(function));
        auto result = task->get_future();
        {
            std::lock_guard<std::mutex> lock(mutex);
            require(!stopping, "OpenGL worker is stopping");
            tasks.emplace_back([task] { (*task)(); });
        }
        condition.notify_one();
        return result.get();
    }
    void loop() {
        for (;;) {
            std::function<void()> task;
            {
                std::unique_lock<std::mutex> lock(mutex);
                condition.wait_for(lock, std::chrono::milliseconds(10), [this] { return stopping || !tasks.empty(); });
                if (stopping && tasks.empty()) break;
                if (!tasks.empty()) { task = std::move(tasks.front()); tasks.pop_front(); }
            }
            if (task) task();
#if defined(_WIN32)
            MSG message {};
            while (PeekMessageW(&message, nullptr, 0, 0, PM_REMOVE)) {
                TranslateMessage(&message);
                DispatchMessageW(&message);
            }
#endif
        }
    }
    ~Impl() {
        invoke([this] { close(); });
        {
            std::lock_guard<std::mutex> lock(mutex);
            stopping = true;
        }
        condition.notify_one();
        worker.join();
    }
    void close() {
        ready = false;
        info = {};
#if defined(_WIN32)
        if (context) { wglMakeCurrent(nullptr, nullptr); wglDeleteContext(context); context = nullptr; }
        if (dc && window) { ReleaseDC(window, dc); dc = nullptr; }
        if (window) { if (IsWindow(window)) DestroyWindow(window); window = nullptr; }
        if (windowClass) { UnregisterClassW(className.c_str(), instance); windowClass = 0; }
        gl = {};
#endif
    }
    void invalidate() {
        if (epoch != std::numeric_limits<uint64_t>::max()) ++epoch;
        close();
    }
    void initialize(bool visible, uint32_t width, uint32_t height) {
        require(!ready, "OpenGL provider is already initialized");
        require(dimensions(width, height), "Window size outside 1..2048");
        require(epoch != std::numeric_limits<uint64_t>::max(), "OpenGL epoch exhausted");
        close();
        info = {};
#if defined(_WIN32)
        // No GL calls occur on the caller's thread and no ambient context is adopted.
        instance = GetModuleHandleW(nullptr);
        className = L"MellowOpenGL-" + std::to_wstring(reinterpret_cast<uintptr_t>(this));
        WNDCLASSW wc {};
        wc.style = CS_OWNDC;
        wc.lpfnWndProc = windowProc;
        wc.hInstance = instance;
        wc.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
        wc.lpszClassName = className.c_str();
        windowClass = RegisterClassW(&wc);
        require(windowClass != 0, "Cannot register isolated OpenGL window");
        RECT rectangle {0, 0, static_cast<LONG>(width), static_cast<LONG>(height)};
        require(AdjustWindowRect(&rectangle, WS_OVERLAPPEDWINDOW, FALSE) != FALSE, "Cannot size OpenGL window");
        window = CreateWindowExW(0, className.c_str(), L"Mellow OpenGL Render Client",
                                 WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
                                 rectangle.right - rectangle.left, rectangle.bottom - rectangle.top,
                                 nullptr, nullptr, instance, nullptr);
        require(window != nullptr, "Cannot create isolated OpenGL window");
        dc = GetDC(window);
        require(dc != nullptr, "Cannot create OpenGL device context");
        PIXELFORMATDESCRIPTOR requested {};
        requested.nSize = sizeof(requested); requested.nVersion = 1;
        requested.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
        requested.iPixelType = PFD_TYPE_RGBA; requested.cColorBits = 32; requested.cAlphaBits = 8;
        requested.iLayerType = PFD_MAIN_PLANE;
        const int format = ChoosePixelFormat(dc, &requested);
        require(format != 0, "No compatible OpenGL pixel format");
        PIXELFORMATDESCRIPTOR actual {};
        require(DescribePixelFormat(dc, format, sizeof(actual), &actual) != 0, "Cannot verify selected pixel format");
        require((actual.dwFlags & (PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER)) ==
                (PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER), "Pixel format lacks required window/OpenGL/double buffer flags");
        // Generic or generic-accelerated mini-client paths do not qualify as this hardware ICD path.
        require((actual.dwFlags & (PFD_GENERIC_FORMAT | PFD_GENERIC_ACCELERATED)) == 0,
                "Software/generic OpenGL pixel format rejected");
        require(actual.iPixelType == PFD_TYPE_RGBA && actual.cColorBits >= 24 && actual.cAlphaBits >= 8,
                "Pixel format lacks RGB24/alpha8");
        require(SetPixelFormat(dc, format, &actual) != FALSE, "Cannot set OpenGL pixel format");
        context = wglCreateContext(dc);
        require(context != nullptr && wglMakeCurrent(dc, context) != FALSE, "Cannot create temporary WGL loader context");
        auto createCore = symbol<PFNWGLCREATECONTEXTATTRIBSARBPROC>("wglCreateContextAttribsARB");
        const int attributes[] = {WGL_CONTEXT_MAJOR_VERSION_ARB, 3, WGL_CONTEXT_MINOR_VERSION_ARB, 3,
                                  WGL_CONTEXT_PROFILE_MASK_ARB, WGL_CONTEXT_CORE_PROFILE_BIT_ARB, 0};
        HGLRC core = createCore(dc, nullptr, attributes);
        require(core != nullptr, "Driver cannot create OpenGL 3.3 core context");
        wglMakeCurrent(nullptr, nullptr);
        wglDeleteContext(context);
        context = core;
        require(wglMakeCurrent(dc, context) != FALSE, "Cannot activate owned core context");
        gl.load();
        info.vendor = glText(GL_VENDOR); info.renderer = glText(GL_RENDERER);
        info.version = glText(GL_VERSION); info.shadingLanguageVersion = glText(GL_SHADING_LANGUAGE_VERSION);
        glGetIntegerv(GL_MAJOR_VERSION, &info.major); glGetIntegerv(GL_MINOR_VERSION, &info.minor);
        GLint profile {};
        glGetIntegerv(GL_CONTEXT_PROFILE_MASK, &profile);
        require(info.major > 3 || (info.major == 3 && info.minor >= 3), "OpenGL 3.3 core is required");
        require((profile & GL_CONTEXT_CORE_PROFILE_BIT) != 0, "Driver did not create requested core profile");
        std::string lower = info.vendor + " " + info.renderer;
        std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        for (const char *software : {"microsoft", "gdi generic", "llvmpipe", "softpipe", "swrast", "software rasterizer", "swiftshader", "lavapipe"})
            require(lower.find(software) == std::string::npos, "Software OpenGL renderer rejected");
        // A hardware ICD pixel format plus driver identity is driver-reported evidence,
        // not independent PCI attestation or proof that future submitted pixels are correct.
        info.pixelFormat = format; info.acceleratedPixelFormat = true;
        info.softwareRendererRejected = true; info.coreProfile = true; info.visibleWindow = visible;
        glCheck("Context initialization");
        if (visible) { ShowWindow(window, SW_SHOWNORMAL); UpdateWindow(window); }
        ready = true;
#else
        (void) visible;
        throw std::runtime_error("OpenGL native provider is implemented only for Windows WGL");
#endif
    }
#if defined(_WIN32)
    void current() {
        require(ready && context && window && IsWindow(window), "OpenGL provider has no live owned context/window");
        require(wglGetCurrentContext() == context && wglGetCurrentDC() == dc, "Owned worker GL context mismatch");
    }
    std::string shaderLog(GLuint shader) {
        GLint length {}; gl.GetShaderiv(shader, GL_INFO_LOG_LENGTH, &length);
        require(length >= 0 && length <= 65536, "Shader diagnostic exceeds bound");
        if (length <= 1) return {};
        std::string log(static_cast<size_t>(length), '\0');
        GLsizei actual {}; gl.GetShaderInfoLog(shader, length, &actual, &log[0]);
        require(actual >= 0 && actual < length, "Invalid shader diagnostic length");
        log.resize(static_cast<size_t>(actual)); return log;
    }
    std::string programLog(GLuint program) {
        GLint length {}; gl.GetProgramiv(program, GL_INFO_LOG_LENGTH, &length);
        require(length >= 0 && length <= 65536, "Program diagnostic exceeds bound");
        if (length <= 1) return {};
        std::string log(static_cast<size_t>(length), '\0');
        GLsizei actual {}; gl.GetProgramInfoLog(program, length, &actual, &log[0]);
        require(actual >= 0 && actual < length, "Invalid program diagnostic length");
        log.resize(static_cast<size_t>(actual)); return log;
    }
    GLuint compileProgram(const std::string &vertex, const std::string &fragment, std::string &log) {
        current();
        GLuint shaders[2] {}, program {};
        try {
            const std::string *sources[] = {&vertex, &fragment};
            const GLenum kinds[] = {GL_VERTEX_SHADER, GL_FRAGMENT_SHADER};
            for (size_t i = 0; i < 2; ++i) {
                require(!sources[i]->empty() && sources[i]->size() <= MaxSourceBytes &&
                        sources[i]->find('\0') == std::string::npos, "Shader source size/content invalid");
                shaders[i] = gl.CreateShader(kinds[i]);
                require(shaders[i] != 0, "Cannot allocate shader");
                const char *source = sources[i]->data();
                const GLint length = static_cast<GLint>(sources[i]->size());
                gl.ShaderSource(shaders[i], 1, &source, &length);
                gl.CompileShader(shaders[i]);
                GLint status {}; gl.GetShaderiv(shaders[i], GL_COMPILE_STATUS, &status);
                log += shaderLog(shaders[i]);
                require(status == GL_TRUE, "GLSL stage compilation failed: " + log);
            }
            program = gl.CreateProgram();
            require(program != 0, "Cannot allocate shader program");
            for (auto shader : shaders) gl.AttachShader(program, shader);
            gl.LinkProgram(program);
            GLint status {}; gl.GetProgramiv(program, GL_LINK_STATUS, &status);
            log += programLog(program);
            require(status == GL_TRUE, "GLSL program linking failed: " + log);
            for (auto &shader : shaders) { gl.DeleteShader(shader); shader = 0; }
            glCheck("Pipeline compilation and stage cleanup");
            require(compilations != std::numeric_limits<uint64_t>::max(), "Pipeline compilation counter exhausted");
            ++compilations;
            return program;
        } catch (...) {
            for (auto shader : shaders) if (shader) gl.DeleteShader(shader);
            if (program) gl.DeleteProgram(program);
            // Consume errors generated by this failed build so a corrected source can retry.
            for (unsigned i = 0; i < 16 && glGetError() != GL_NO_ERROR; ++i) {}
            throw;
        }
    }
    struct RenderResources {
        Impl &owner;
        GLuint texture {}, framebuffer {}, vao {};
        GLsync fence {};
        bool cleaned {};
        void clean() {
            owner.gl.BindFramebuffer(GL_FRAMEBUFFER, 0);
            owner.gl.BindVertexArray(0); owner.gl.UseProgram(0);
            if (fence) { owner.gl.DeleteSync(fence); fence = nullptr; }
            if (vao) { owner.gl.DeleteVertexArrays(1, &vao); vao = 0; }
            if (framebuffer) { owner.gl.DeleteFramebuffers(1, &framebuffer); framebuffer = 0; }
            if (texture) { glDeleteTextures(1, &texture); texture = 0; }
            cleaned = true;
        }
        ~RenderResources() { if (!cleaned) clean(); }
    };
    void render(GLuint program, const OpenGLRenderOptions &options, OpenGLFrame &frame) {
        current();
        require(dimensions(options.width, options.height), "Render dimensions outside 1..2048");
        for (auto value : options.params) require(std::isfinite(value), "Non-finite render uniform rejected");
        for (auto value : options.clearColor) require(std::isfinite(value) && value >= 0 && value <= 1, "Clear color outside 0..1");
        require(!options.present || info.visibleWindow, "Presentation requires an explicitly visible owned window");
        require(sequence != std::numeric_limits<uint64_t>::max(), "Frame sequence exhausted");
        frame.width = options.width; frame.height = options.height; frame.epoch = epoch; frame.sequence = ++sequence;
        RenderResources resources {*this, 0, 0, 0, nullptr, false};
        glGenTextures(1, &resources.texture);
        glBindTexture(GL_TEXTURE_2D, resources.texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, static_cast<GLsizei>(options.width), static_cast<GLsizei>(options.height),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        gl.GenFramebuffers(1, &resources.framebuffer);
        gl.BindFramebuffer(GL_FRAMEBUFFER, resources.framebuffer);
        gl.FramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, resources.texture, 0);
        require(resources.texture && resources.framebuffer &&
                gl.CheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE, "RGBA8 offscreen framebuffer incomplete");
        gl.GenVertexArrays(1, &resources.vao); gl.BindVertexArray(resources.vao);
        require(resources.vao != 0, "Cannot allocate core-profile vertex array");
        glViewport(0, 0, static_cast<GLsizei>(options.width), static_cast<GLsizei>(options.height));
        glDisable(GL_BLEND); glDisable(GL_DITHER); glDisable(GL_DEPTH_TEST); glDisable(GL_STENCIL_TEST);
        glDisable(GL_CULL_FACE); glDisable(GL_SCISSOR_TEST); glDisable(GL_MULTISAMPLE); glDisable(GL_FRAMEBUFFER_SRGB);
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
        glClearColor(options.clearColor[0], options.clearColor[1], options.clearColor[2], options.clearColor[3]);
        glClear(GL_COLOR_BUFFER_BIT);
        gl.UseProgram(program);
        const auto uniform = gl.GetUniformLocation(program, "mellow_params");
        if (uniform >= 0) gl.Uniform4fv(uniform, 1, options.params.data());
        const auto viewport = gl.GetUniformLocation(program, "mellow_viewport");
        if (viewport >= 0) gl.Uniform2f(viewport, static_cast<GLfloat>(options.width), static_cast<GLfloat>(options.height));
        glCheck("Render resource and pipeline setup");
        glDrawArrays(GL_TRIANGLES, 0, 3);
        frame.renderSubmitted = true;
        glCheck("Triangle submission");
        resources.fence = gl.FenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0);
        require(resources.fence != nullptr, "Cannot allocate GPU fence");
        glFlush();
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        for (;;) {
            const auto status = gl.ClientWaitSync(resources.fence, 0, 10000000ULL);
            if (status == GL_ALREADY_SIGNALED || status == GL_CONDITION_SATISFIED) break;
            require(status == GL_TIMEOUT_EXPIRED, "GPU fence wait failed");
            require(std::chrono::steady_clock::now() < deadline, "GPU fence wait timed out after two seconds");
        }
        frame.fenceSignaled = true;
        frame.rgba.resize(static_cast<size_t>(options.width) * options.height * 4);
        glPixelStorei(GL_PACK_ALIGNMENT, 1);
        glReadBuffer(GL_COLOR_ATTACHMENT0);
        glReadPixels(0, 0, static_cast<GLsizei>(options.width), static_cast<GLsizei>(options.height),
                     GL_RGBA, GL_UNSIGNED_BYTE, frame.rgba.data());
        glCheck("Fence and RGBA8 readback");
        current();
        frame.readbackCompleted = true;
        if (options.present) {
            RECT client {};
            require(GetClientRect(window, &client) != FALSE && client.right > 0 && client.bottom > 0, "Visible client area unavailable");
            gl.BindFramebuffer(GL_READ_FRAMEBUFFER, resources.framebuffer);
            gl.BindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);
            glDrawBuffer(GL_BACK);
            gl.BlitFramebuffer(0, 0, options.width, options.height, 0, 0, client.right, client.bottom,
                               GL_COLOR_BUFFER_BIT, GL_NEAREST);
            glCheck("Offscreen to visible backbuffer blit");
            require(SwapBuffers(dc) != FALSE, "Window SwapBuffers failed");
            frame.swapCompleted = true; // Swap acceptance is not physical scanout evidence.
            if (gl.GetSwapInterval) { frame.swapInterval = gl.GetSwapInterval(); frame.swapIntervalKnown = true; }
        }
        resources.clean();
        glCheck("Per-frame resource cleanup");
        frame.resourcesReleased = true;
    }
#endif
};

struct OpenGLPipeline::Impl {
    std::shared_ptr<OpenGLProvider::Impl> owner;
    uint64_t epoch {}, serial {};
    uint32_t program {};
    std::string log;
    ~Impl() {
        if (!owner || !program) return;
        owner->invoke([this] {
#if defined(_WIN32)
            // Context deletion already freed all objects from a stale epoch.
            if (owner->ready && owner->epoch == epoch && owner->context) owner->gl.DeleteProgram(program);
#endif
        });
    }
};
OpenGLPipeline::OpenGLPipeline() : impl_(std::make_unique<Impl>()) {}
OpenGLPipeline::~OpenGLPipeline() = default;
uint64_t OpenGLPipeline::compilationSerial() const { return impl_->serial; }
const std::string &OpenGLPipeline::buildLog() const { return impl_->log; }
OpenGLProvider::OpenGLProvider() : impl_(std::make_shared<Impl>()) {}
OpenGLProvider::~OpenGLProvider() = default;
bool OpenGLProvider::initialize(std::string &error, bool visible, uint32_t width, uint32_t height) {
    error.clear();
    return impl_->invoke([&] {
        if (impl_->ready) { error = "OpenGL provider is already initialized"; return false; }
        try { impl_->initialize(visible, width, height); return true; }
        catch (const std::exception &failure) { error = failure.what(); impl_->invalidate(); return false; }
    });
}
std::shared_ptr<OpenGLPipeline> OpenGLProvider::compile(const std::string &vertex, const std::string &fragment, std::string &error) {
    error.clear();
    try {
        auto pipeline = std::shared_ptr<OpenGLPipeline>(new OpenGLPipeline());
        pipeline->impl_->owner = impl_;
        impl_->invoke([&] {
#if defined(_WIN32)
            pipeline->impl_->program = impl_->compileProgram(vertex, fragment, pipeline->impl_->log);
            pipeline->impl_->epoch = impl_->epoch; pipeline->impl_->serial = impl_->compilations;
#else
            (void) vertex; (void) fragment;
            throw std::runtime_error("OpenGL native provider is implemented only for Windows WGL");
#endif
        });
        return pipeline;
    } catch (const std::exception &failure) { error = failure.what(); return {}; }
}
bool OpenGLProvider::render(const std::shared_ptr<OpenGLPipeline> &pipeline, const OpenGLRenderOptions &options, OpenGLFrame &frame) {
    frame = {};
    return impl_->invoke([&] {
        try {
            require(pipeline && pipeline->impl_->owner == impl_, "Render pipeline belongs to another provider");
            require(pipeline->impl_->epoch == impl_->epoch && pipeline->impl_->program != 0, "Render pipeline epoch is stale");
#if defined(_WIN32)
            impl_->render(pipeline->impl_->program, options, frame);
            return frame.fenceSignaled && frame.readbackCompleted && frame.resourcesReleased &&
                   (!options.present || frame.swapCompleted);
#else
            (void) options;
            throw std::runtime_error("OpenGL native provider is implemented only for Windows WGL");
#endif
        } catch (const std::exception &failure) {
            frame.error = failure.what();
            if (frame.renderSubmitted) impl_->invalidate();
            return false;
        }
    });
}
OpenGLDeviceInfo OpenGLProvider::deviceInfo() const { return impl_->invoke([this] { return impl_->info; }); }
uint64_t OpenGLProvider::pipelineBuildCount() const { return impl_->invoke([this] { return impl_->compilations; }); }
void OpenGLProvider::invalidateSession() { impl_->invoke([this] { impl_->invalidate(); }); }
}
