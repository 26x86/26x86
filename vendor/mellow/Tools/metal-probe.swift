// Structured real-output diagnostic; NOT compiled or run in this Windows session.
// Default: enumerate Metal devices. Compute is opt-in and requires a registry ID.
// Windows source review: Intel-compatible private render target -> shared buffer blit.
// Apple docs: https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/ResourceOptions.html
import Foundation
import Metal
import IOKit
import Dispatch
import Darwin
import CryptoKit

// JSON Lines are flushed after every event so a compiler/GPU hang cannot turn
// a prior partial stage into a successful final report.
func emit(_ stage: String, _ details: [String: Any] = [:]) {
    var object = details
    object["schema_version"] = 3
    object["stage"] = stage
    object["utc"] = ISO8601DateFormatter().string(from: Date())
    if let data = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys]) {
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }
}
func fail(_ code: Int32, _ message: String) -> Never {
    emit("failed", ["code": code, "error": message, "target_metal_verified": false])
    exit(code)
}
func sha256(_ pointer: UnsafeRawPointer, _ count: Int) -> String {
    SHA256.hash(data: Data(bytes: pointer, count: count)).map { String(format: "%02x", $0) }.joined()
}
func sha256(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}
func step(_ state: inout UInt32) -> UInt32 {
    state = state &* 1664525 &+ 1013904223
    return state
}
func challengeVectors(nonce: UInt32, count: Int) -> (input: [UInt32], poison: [UInt32], expected: [UInt32]) {
    var inputState = nonce ^ 0xC001D00D
    var poisonState = nonce ^ 0x51A7E5ED
    var input = [UInt32](repeating: 0, count: count)
    var poison = [UInt32](repeating: 0, count: count)
    var expected = [UInt32](repeating: 0, count: count)
    for i in 0..<count {
        let generated = step(&inputState)
        input[i] = i < 4 ? UInt32(i + 1) : generated ^ UInt32(i)
        poison[i] = step(&poisonState) ^ (UInt32(i) &* 0x9E3779B9)
        expected[i] = input[i] &* 7 &+ 3
    }
    return (input, poison, expected)
}
func wordsSHA256(_ words: [UInt32]) -> String {
    words.withUnsafeBufferPointer { buffer in
        sha256(buffer.baseAddress!, buffer.count * MemoryLayout<UInt32>.stride)
    }
}

struct PCIIdentity {
    let vendor: UInt32
    let device: UInt32
    let registryID: UInt64
    let physicalVendor: UInt32?
    let physicalDevice: UInt32?
    let physicalBDF: UInt32?
    let physicalSource: String?
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
            let physicalVendor = readUInt32Property(entry, "MellowPhysicalVendorID")
            let physicalDevice = readUInt32Property(entry, "MellowPhysicalDeviceID")
            let physicalBDF = readUInt32Property(entry, "MellowPhysicalBDF")
            let physicalSource = IORegistryEntryCreateCFProperty(entry, "MellowPhysicalIdentitySource" as CFString,
                                      kCFAllocatorDefault, 0)?.takeRetainedValue() as? String
            IOObjectRelease(entry)
            return PCIIdentity(vendor: vendor, device: id, registryID: pciRegistryID,
                               physicalVendor: physicalVendor, physicalDevice: physicalDevice,
                               physicalBDF: physicalBDF, physicalSource: physicalSource)
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
        fail(7, "10-second timeout; this does not cancel the GPU command. Preserve logs.")
    }
    guard command.status == .completed else {
        throw command.error ?? NSError(domain: "MetalProbe", code: 8, userInfo: [NSLocalizedDescriptionKey: "Command not completed"])
    }
}
emit("started", ["os": ProcessInfo.processInfo.operatingSystemVersionString,
                  "pid": ProcessInfo.processInfo.processIdentifier])
if let defaultDevice = MTLCreateSystemDefaultDevice() {
    emit("default_device", ["name": defaultDevice.name, "registry_id": String(defaultDevice.registryID)])
} else {
    emit("default_device_missing")
}
let devices = MTLCopyAllDevices()
for device in devices {
    emit("device", ["name": device.name, "registry_id": String(device.registryID),
                     "low_power": device.isLowPower, "removable": device.isRemovable, "headless": device.isHeadless])
    if let pci = pciIdentity(device) {
        emit("pci_provider", ["metal_registry_id": String(device.registryID), "pci_registry_id": String(pci.registryID),
             "vendor_id": pci.vendor, "device_id": pci.device, "driver_physical_vendor": pci.physicalVendor ?? 0,
             "driver_physical_device": pci.physicalDevice ?? 0, "driver_physical_bdf": pci.physicalBDF ?? 0,
             "driver_physical_source": pci.physicalSource ?? "unavailable", "cryptographic_attestation": false])
    } else {
        emit("pci_provider_missing", ["metal_registry_id": String(device.registryID)])
    }
}
let args = Array(CommandLine.arguments.dropFirst())
if args.isEmpty {
    emit("enumeration_only", ["command_submitted": false, "target_metal_verified": false])
    exit(devices.isEmpty ? 3 : 0)
}
guard args.count == 2, args[0] == "--compute" else {
    fail(2, "Usage: metal-probe [--compute 0xREGISTRY_ID]")
}
let idText = args[1].lowercased()
let parsedID = idText.hasPrefix("0x") ? UInt64(idText.dropFirst(2), radix: 16) : UInt64(idText)
guard let registryID = parsedID else {
    fail(3, "Requested Metal registryID is invalid")
}
let matchingDevices = devices.filter { $0.registryID == registryID }
guard matchingDevices.count == 1, let device = matchingDevices.first else {
    fail(3, "Requested Metal registryID not found")
}
let fallbackNames = ["software", "swiftshader", "llvmpipe", "softpipe"]
guard !fallbackNames.contains(where: { device.name.lowercased().contains($0) }),
      let pci = pciIdentity(device), pci.vendor == 0x8086,
      (pci.device == 0x7D41 || pci.device == 0x9A49),
      pci.physicalVendor == 0x8086, pci.physicalDevice == 0x7D41,
      pci.physicalBDF == 0x1000, pci.physicalSource == "pci-config-before-spoof" else {
    fail(11, "Requires Intel PCI provider plus driver-reported physical 8086:7D41 at 00:02.0 captured before spoof")
}
emit("target_correlated", ["registry_id": String(registryID), "pci_registry_id": String(pci.registryID),
     "visible_vendor": pci.vendor, "visible_device": pci.device,
     "physical_vendor": 0x8086, "physical_device": 0x7D41, "physical_bdf": 0x1000,
     "physical_identity_source": pci.physicalSource!,
     "evidence_source": "driver-reported PCI config captured before spoof", "cryptographic_attestation": false,
     "unique_metal_registry_match": true, "device_name": device.name])
let count = 4096
let byteCount = count * MemoryLayout<UInt32>.stride
guard let output = device.makeBuffer(length: byteCount, options: .storageModeShared),
      let input = device.makeBuffer(length: byteCount, options: .storageModeShared),
      let witness = device.makeBuffer(length: MemoryLayout<UInt32>.stride, options: .storageModeShared) else {
    fail(4, "Buffer creation failed")
}
let nonce = UInt32.random(in: 1...UInt32.max)
let challenge = challengeVectors(nonce: nonce, count: count)
let inputWords = input.contents().bindMemory(to: UInt32.self, capacity: count)
let outputWords = output.contents().bindMemory(to: UInt32.self, capacity: count)
for i in 0..<count {
    inputWords[i] = challenge.input[i]
    outputWords[i] = challenge.poison[i]
}
let initialWitness = nonce ^ 0xDEADBEEF
witness.contents().bindMemory(to: UInt32.self, capacity: 1)[0] = initialWitness
let expectedOutputHash = wordsSHA256(challenge.expected)
guard wordsSHA256(challenge.poison) != expectedOutputHash else {
    fail(16, "Fresh output poison unexpectedly equals the expected result")
}
emit("challenge_initialized", ["nonce": nonce, "count": count, "registry_id": String(registryID),
     "input_sha256": sha256(input.contents(), byteCount), "initial_output_sha256": sha256(output.contents(), byteCount),
     "expected_output_sha256": expectedOutputHash, "initial_nonce_witness": initialWitness,
     "expected_nonce_witness": nonce ^ 0x7D410003,
     "acceptance_input_first_four": [1, 2, 3, 4], "acceptance_output_first_four": [10, 17, 24, 31]])
let source = """
#include <metal_stdlib>
using namespace metal;
struct Params { uint count; uint nonce; };
kernel void evidence_kernel(device uint *out [[buffer(0)]], const device uint *input [[buffer(1)]],
                            constant Params &p [[buffer(2)]], device uint *witness [[buffer(3)]],
                            uint i [[thread_position_in_grid]]) {
    if (i < p.count) out[i] = input[i] * 7u + 3u;
    if (i == 0u) witness[0] = p.nonce ^ 0x7d410003u;
}
vertex float4 evidence_vertex(uint i [[vertex_id]]) {
    const float2 positions[3] = { float2(-1.0, -1.0), float2(3.0, -1.0), float2(-1.0, 3.0) };
    return float4(positions[i], 0.0, 1.0);
}
fragment float4 evidence_fragment() { return float4(1.0, 0.0, 0.0, 1.0); }
"""
do {
    emit("compile_started")
    let library = try device.makeLibrary(source: source, options: nil)
    guard let function = library.makeFunction(name: "evidence_kernel") else {
        throw NSError(domain: "MetalProbe", code: 5, userInfo: [NSLocalizedDescriptionKey: "Missing function"])
    }
    let pipeline = try device.makeComputePipelineState(function: function)
    emit("compute_pipeline_created", ["thread_execution_width": pipeline.threadExecutionWidth])
    guard let queue = device.makeCommandQueue(), let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else {
        throw NSError(domain: "MetalProbe", code: 6, userInfo: [NSLocalizedDescriptionKey: "Queue, buffer, or encoder creation failed"])
    }
    guard queue.device.registryID == registryID, command.device.registryID == registryID else {
        throw NSError(domain: "MetalProbe", code: 17, userInfo: [NSLocalizedDescriptionKey: "Compute queue or command belongs to another Metal device"])
    }
    command.label = "Mellow7D41-A-\(String(nonce, radix: 16))"
    encoder.setComputePipelineState(pipeline)
    encoder.setBuffer(output, offset: 0, index: 0)
    encoder.setBuffer(input, offset: 0, index: 1)
    var params = (UInt32(count), nonce)
    encoder.setBytes(&params, length: MemoryLayout<UInt32>.stride * 2, index: 2)
    encoder.setBuffer(witness, offset: 0, index: 3)
    let width = max(1, min(64, pipeline.maxTotalThreadsPerThreadgroup))
    encoder.dispatchThreadgroups(MTLSize(width: (count + width - 1) / width, height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: width, height: 1, depth: 1))
    encoder.endEncoding()
    emit("compute_submitting")
    try awaitCompleted(command)
    let words = output.contents().bindMemory(to: UInt32.self, capacity: count)
    for i in 0..<count {
        guard words[i] == challenge.expected[i] else {
            throw NSError(domain: "MetalProbe", code: 9, userInfo: [NSLocalizedDescriptionKey: "Mismatch at \(i): got \(words[i]), expected \(challenge.expected[i])"])
        }
    }
    let actualWitness = witness.contents().bindMemory(to: UInt32.self, capacity: 1)[0]
    guard actualWitness == (nonce ^ 0x7D410003) else {
        throw NSError(domain: "MetalProbe", code: 18, userInfo: [NSLocalizedDescriptionKey: "Nonce witness mismatch"])
    }
    guard command.gpuStartTime > 0, command.gpuEndTime >= command.gpuStartTime else {
        throw NSError(domain: "MetalProbe", code: 19, userInfo: [NSLocalizedDescriptionKey: "Completed compute command has no valid GPU timestamps"])
    }
    emit("compute_output_passed", ["count": count, "mismatches": 0, "nonce": nonce,
          "registry_id": String(registryID), "output_sha256": sha256(output.contents(), byteCount),
          "expected_output_sha256": expectedOutputHash,
          "actual_first_four": Array(UnsafeBufferPointer(start: words, count: 4)),
          "expected_first_four": [10, 17, 24, 31],
          "nonce_witness": actualWitness, "expected_nonce_witness": nonce ^ 0x7D410003,
          "queue_registry_id": String(queue.device.registryID), "command_registry_id": String(command.device.registryID),
          "gpu_start_time": command.gpuStartTime, "gpu_end_time": command.gpuEndTime,
          "gpu_timing_recorded": true, "output_changed": true])
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
    guard renderCommand.device.registryID == registryID else {
        throw NSError(domain: "MetalProbe", code: 20, userInfo: [NSLocalizedDescriptionKey: "Render command belongs to another Metal device"])
    }
    renderCommand.label = "Mellow7D41-B-\(String(nonce, radix: 16))"
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
    var expectedReadback = Data(repeating: 0xA5, count: readbackByteCount)
    for row in 0..<4 {
        for column in 0..<4 {
            let offset = row * readbackRowStride + column * 4
            expectedReadback[offset] = 255
            expectedReadback[offset + 1] = 0
            expectedReadback[offset + 2] = 0
            expectedReadback[offset + 3] = 255
        }
    }
    let expectedReadbackHash = sha256(expectedReadback)
    let actualReadbackHash = sha256(readback.contents(), readbackByteCount)
    guard actualReadbackHash == expectedReadbackHash,
          renderCommand.gpuStartTime > 0, renderCommand.gpuEndTime >= renderCommand.gpuStartTime else {
        throw NSError(domain: "MetalProbe", code: 21, userInfo: [NSLocalizedDescriptionKey: "Render hash or GPU timestamp evidence is invalid"])
    }
    emit("render_output_passed", ["pixels": 16, "expected_rgba": [255, 0, 0, 255],
          "registry_id": String(registryID), "mismatches": 0,
          "actual_first_rgba": Array(UnsafeBufferPointer(start: pixels, count: 4)),
          "readback_sha256": actualReadbackHash, "expected_readback_sha256": expectedReadbackHash,
          "command_registry_id": String(renderCommand.device.registryID),
          "gpu_start_time": renderCommand.gpuStartTime, "gpu_end_time": renderCommand.gpuEndTime,
          "gpu_timing_recorded": true])
    emit("completed", ["registry_id": String(registryID), "compute_output_passed": true,
          "render_output_passed": true, "physical_identity_correlated": true,
          "small_target_metal_probe_passed": true, "full_metal_conformance_verified": false,
          "windowserver_presentation_verified": false, "cpu_fallback_used": false,
          "hardware_irq_fence_verified": false, "stress_acceptance_verified": false,
          "evidence_scope": "public Metal compute and offscreen render only"])
} catch {
    fail(10, String(describing: error))
}
