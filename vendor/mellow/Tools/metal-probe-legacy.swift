// Experimental diagnostic; NOT compiled or run in the Windows preparation session.
// Default: enumerate Metal devices. Compute is opt-in and requires a registry ID.
// Windows source review: Intel-compatible private render target -> shared buffer blit.
// Apple docs: https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/ResourceOptions.html
import Foundation
import Metal
import IOKit
import Dispatch
import Darwin

struct PCIIdentity {
    let vendor: UInt32
    let device: UInt32
    let registryID: UInt64
}
func readUInt32Property(_ entry: io_registry_entry_t, _ key: String) -> UInt32? {
    guard let value = IORegistryEntryCreateCFProperty(entry, key as CFString, kCFAllocatorDefault, 0)?.takeRetainedValue() else { return nil }
    if let data = value as? Data, data.count >= 4 {
        let bytes = Array(data.prefix(4))
        return UInt32(bytes[0]) | (UInt32(bytes[1]) << 8) | (UInt32(bytes[2]) << 16) | (UInt32(bytes[3]) << 24)
    }
    return (value as? NSNumber)?.uint32Value
}
func pciIdentity(_ device: MTLDevice) -> PCIIdentity? {
    var entry = IOServiceGetMatchingService(kIOMainPortDefault, IORegistryEntryIDMatching(device.registryID))
    guard entry != 0 else { return nil }
    for _ in 0..<16 {
        if IOObjectConformsTo(entry, "IOPCIDevice") != 0,
           let vendor = readUInt32Property(entry, "vendor-id"), let id = readUInt32Property(entry, "device-id") {
            var pciRegistryID: UInt64 = 0
            IORegistryEntryGetRegistryEntryID(entry, &pciRegistryID)
            IOObjectRelease(entry)
            return PCIIdentity(vendor: vendor, device: id, registryID: pciRegistryID)
        }
        var parent: io_registry_entry_t = 0
        let status = IORegistryEntryGetParentEntry(entry, kIOServicePlane, &parent)
        IOObjectRelease(entry)
        if status != KERN_SUCCESS || parent == 0 { return nil }
        entry = parent
    }
    IOObjectRelease(entry)
    return nil
}
func awaitCompleted(_ command: MTLCommandBuffer) throws {
    let finished = DispatchSemaphore(value: 0)
    command.addCompletedHandler { _ in finished.signal() }
    command.commit()
    guard finished.wait(timeout: .now() + 10) == .success else {
        fputs("FAIL: 10-second timeout; this does not cancel the GPU command. Preserve logs.\n", stderr)
        exit(7)
    }
    guard command.status == .completed else {
        throw command.error ?? NSError(domain: "MetalProbe", code: 8, userInfo: [NSLocalizedDescriptionKey: "Command not completed"])
    }
}
print("utc=\(ISO8601DateFormatter().string(from: Date())) os=\(ProcessInfo.processInfo.operatingSystemVersionString)")
if let defaultDevice = MTLCreateSystemDefaultDevice() {
    print("systemDefaultDevice=\(defaultDevice.name) registryID=0x\(String(defaultDevice.registryID, radix: 16))")
} else {
    print("systemDefaultDevice=NONE")
}
let devices = MTLCopyAllDevices()
for device in devices {
    print("device=\(device.name) registryID=0x\(String(device.registryID, radix: 16)) lowPower=\(device.isLowPower) removable=\(device.isRemovable) headless=\(device.isHeadless)")
    if let pci = pciIdentity(device) {
        print("pciProvider=\(String(pci.vendor, radix: 16)):\(String(pci.device, radix: 16)) pciRegistryID=0x\(String(pci.registryID, radix: 16)) identityMayBeSpoofed=true")
    } else {
        print("pciProvider=NOT_CONFIRMED")
    }
}
let args = Array(CommandLine.arguments.dropFirst())
if args.isEmpty {
    print("ENUMERATION_ONLY: no command submitted; enumeration does not prove acceleration.")
    exit(devices.isEmpty ? 3 : 0)
}
guard args.count == 2, args[0] == "--compute" else {
    fputs("Usage: metal-probe [--compute 0xREGISTRY_ID]\n", stderr)
    exit(2)
}
let idText = args[1].lowercased()
let parsedID = idText.hasPrefix("0x") ? UInt64(idText.dropFirst(2), radix: 16) : UInt64(idText)
guard let registryID = parsedID, let device = devices.first(where: { $0.registryID == registryID }) else {
    fputs("FAIL: requested Metal registryID not found.\n", stderr)
    exit(3)
}
let fallbackNames = ["software", "swiftshader", "llvmpipe", "softpipe"]
guard !fallbackNames.contains(where: { device.name.lowercased().contains($0) }),
      let pci = pciIdentity(device), pci.vendor == 0x8086,
      pci.device == 0x7D41 || pci.device == 0x9A49 else {
    fputs("REFUSED: target is not a confirmed Intel PCI-backed 7D41/9A49 Metal provider, or identifies as software.\n", stderr)
    exit(11)
}
print("PCI_BACKED_TARGET_CHECK: passed. A 9A49 registry property may be spoofed; correlate with physical 7D41 driver log.")
let count = 1024
let byteCount = count * MemoryLayout<UInt32>.stride
guard let output = device.makeBuffer(length: byteCount, options: .storageModeShared) else {
    fputs("FAIL: buffer creation.\n", stderr)
    exit(4)
}
memset(output.contents(), 0xA5, byteCount)
let source = """
#include <metal_stdlib>
using namespace metal;
kernel void evidence_kernel(device uint *out [[buffer(0)]], uint i [[thread_position_in_grid]]) {
    if (i < 1024u) out[i] = i * 1664525u + 1013904223u;
}
vertex float4 evidence_vertex(uint i [[vertex_id]]) {
    const float2 positions[3] = { float2(-1.0, -1.0), float2(3.0, -1.0), float2(-1.0, 3.0) };
    return float4(positions[i], 0.0, 1.0);
}
fragment float4 evidence_fragment() { return float4(1.0, 0.0, 0.0, 1.0); }
"""
do {
    let library = try device.makeLibrary(source: source, options: nil)
    guard let function = library.makeFunction(name: "evidence_kernel") else {
        throw NSError(domain: "MetalProbe", code: 5, userInfo: [NSLocalizedDescriptionKey: "Missing function"])
    }
    let pipeline = try device.makeComputePipelineState(function: function)
    guard let queue = device.makeCommandQueue(), let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else {
        throw NSError(domain: "MetalProbe", code: 6, userInfo: [NSLocalizedDescriptionKey: "Queue, buffer, or encoder creation failed"])
    }
    encoder.setComputePipelineState(pipeline)
    encoder.setBuffer(output, offset: 0, index: 0)
    let width = max(1, min(64, pipeline.maxTotalThreadsPerThreadgroup))
    encoder.dispatchThreadgroups(MTLSize(width: (count + width - 1) / width, height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: width, height: 1, depth: 1))
    encoder.endEncoding()
    try awaitCompleted(command)
    let words = output.contents().bindMemory(to: UInt32.self, capacity: count)
    for i in 0..<count {
        let expected = UInt32(i) &* 1664525 &+ 1013904223
        guard words[i] == expected else {
            throw NSError(domain: "MetalProbe", code: 9, userInfo: [NSLocalizedDescriptionKey: "Mismatch at \(i): got \(words[i]), expected \(expected)"])
        }
    }
    print("PASS_COMPUTE_OUTPUT: 1024 UInt32 values matched; device=\(device.name) registryID=0x\(String(registryID, radix: 16))")
    print("GPUStartTime=\(command.gpuStartTime) GPUEndTime=\(command.gpuEndTime)")
    let renderDescriptor = MTLRenderPipelineDescriptor()
    renderDescriptor.vertexFunction = library.makeFunction(name: "evidence_vertex")
    renderDescriptor.fragmentFunction = library.makeFunction(name: "evidence_fragment")
    renderDescriptor.colorAttachments[0].pixelFormat = .rgba8Unorm
    let renderPipeline = try device.makeRenderPipelineState(descriptor: renderDescriptor)
    let textureDescriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 4, height: 4, mipmapped: false)
    textureDescriptor.storageMode = .private
    textureDescriptor.usage = [.renderTarget]
    // A 256-byte row stride also meets the older Mac-family copy alignment.
    // Only the first 16 bytes of each row contain the four RGBA8 pixels.
    let readbackRowStride = 256
    let readbackByteCount = readbackRowStride * 4
    guard let texture = device.makeTexture(descriptor: textureDescriptor),
          let readback = device.makeBuffer(length: readbackByteCount, options: .storageModeShared),
          let renderCommand = queue.makeCommandBuffer() else {
        throw NSError(domain: "MetalProbe", code: 12, userInfo: [NSLocalizedDescriptionKey: "Render resource creation failed"])
    }
    memset(readback.contents(), 0xA5, readbackByteCount)
    let pass = MTLRenderPassDescriptor()
    pass.colorAttachments[0].texture = texture
    pass.colorAttachments[0].loadAction = .clear
    pass.colorAttachments[0].storeAction = .store
    pass.colorAttachments[0].clearColor = MTLClearColor(red: 0, green: 0, blue: 1, alpha: 1)
    guard let renderEncoder = renderCommand.makeRenderCommandEncoder(descriptor: pass) else {
        throw NSError(domain: "MetalProbe", code: 13, userInfo: [NSLocalizedDescriptionKey: "Render encoder creation failed"])
    }
    renderEncoder.setRenderPipelineState(renderPipeline)
    renderEncoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
    renderEncoder.endEncoding()
    guard let blit = renderCommand.makeBlitCommandEncoder() else {
        throw NSError(domain: "MetalProbe", code: 15, userInfo: [NSLocalizedDescriptionKey: "Readback blit encoder creation failed"])
    }
    blit.copy(from: texture, sourceSlice: 0, sourceLevel: 0,
              sourceOrigin: MTLOrigin(x: 0, y: 0, z: 0), sourceSize: MTLSize(width: 4, height: 4, depth: 1),
              to: readback, destinationOffset: 0,
              destinationBytesPerRow: readbackRowStride, destinationBytesPerImage: 0)
    blit.endEncoding()
    // Render and copy are in the same command buffer; CPU reads only on completion.
    try awaitCompleted(renderCommand)
    let pixels = readback.contents().bindMemory(to: UInt8.self, capacity: readbackByteCount)
    for row in 0..<4 {
        for column in 0..<4 {
            let offset = row * readbackRowStride + column * 4
            guard pixels[offset] == 255, pixels[offset + 1] == 0, pixels[offset + 2] == 0, pixels[offset + 3] == 255 else {
                throw NSError(domain: "MetalProbe", code: 14, userInfo: [NSLocalizedDescriptionKey: "Offscreen render pixel mismatch at row \(row), column \(column)"])
            }
        }
    }
    print("PASS_RENDER_OUTPUT: all 16 pixels are RGBA red after a shader draw over a blue clear.")
    print("renderGPUStartTime=\(renderCommand.gpuStartTime) renderGPUEndTime=\(renderCommand.gpuEndTime)")
    print("No CPU compute fallback writes output. Correlate registryID with physical 8086:7D41 and retain driver logs/counters.")
    print("These are small compute/render results, not proof of WindowServer, video, presentation, sleep/wake, or full Metal conformance.")
} catch {
    fputs("FAIL: \(error)\n", stderr)
    exit(10)
}
