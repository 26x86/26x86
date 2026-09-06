#include "../Runtime/OpenCLProvider.hpp"
#include "opencl_runtime_sha256.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace MellowRT;
static std::string quote(const std::string &value) {
    std::ostringstream result;
    result << '"';
    constexpr char hex[] = "0123456789abcdef";
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') result << '\\' << c;
        else if (c < 32) result << "\\u00" << hex[c >> 4] << hex[c & 15];
        else result << c;
    }
    result << '"';
    return result.str();
}
static const char *boolean(bool value) { return value ? "true" : "false"; }
static std::string array(const std::vector<uint32_t> &values) {
    std::ostringstream result;
    result << '[';
    for (size_t i = 0; i < values.size(); ++i) { if (i) result << ','; result << values[i]; }
    result << ']';
    return result.str();
}
static std::string execution(const OpenCLExecution &r) {
    std::ostringstream result;
    result << "{\"submission_attempted\":" << boolean(r.submissionAttempted)
           << ",\"submitted\":" << boolean(r.submitted)
           << ",\"event_ownership_verified\":" << boolean(r.eventOwnershipVerified)
           << ",\"results_verified\":" << boolean(r.resultsVerified)
           << ",\"profiling_verified\":" << boolean(r.profilingVerified)
           << ",\"runtime_planned\":" << boolean(r.runtimePlanned)
           << ",\"runtime_completion_accepted\":" << boolean(r.runtimeCompletionAccepted)
           << ",\"resources_released\":" << boolean(r.resourcesReleased)
           << ",\"gpu_start_ns\":" << r.gpuStart << ",\"gpu_end_ns\":" << r.gpuEnd
           << ",\"epoch\":" << r.epoch << ",\"sequence\":" << r.sequence
           << ",\"validation_record\":" << r.validationRecord
           << ",\"plan_status\":" << static_cast<unsigned>(r.planStatus)
           << ",\"arm_status\":" << static_cast<unsigned>(r.armStatus)
           << ",\"observe_status\":" << static_cast<unsigned>(r.observeStatus)
           << ",\"build_log\":" << quote(r.buildLog) << ",\"error\":" << quote(r.error)
           << ",\"output\":" << array(r.output) << '}';
    return result.str();
}
static void writeJson(const std::string &path, const std::string &json) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    if (!output) throw std::runtime_error("Cannot write report");
    output << json << '\n';
    output.close();
    if (!output) throw std::runtime_error("Report write failed");
}

int main(int argc, char **argv) {
    std::string reportPath;
    uint32_t seed = 0;
    bool compute = false;
    size_t gpuIndex = 0;
    unsigned iterations = 3;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string option(argv[i]);
            if (option == "--compute") compute = true;
            else if (i + 1 < argc && option == "--report") reportPath = argv[++i];
            else if (i + 1 < argc && option == "--seed") seed = static_cast<uint32_t>(std::stoul(argv[++i]));
            else if (i + 1 < argc && option == "--gpu-index") gpuIndex = std::stoul(argv[++i]);
            else if (i + 1 < argc && option == "--iterations") iterations = static_cast<unsigned>(std::stoul(argv[++i]));
            else throw std::runtime_error("Unknown or incomplete argument");
        }
        if (!compute || reportPath.empty()) {
            std::cerr << "Explicit --compute and --report are required; no GPU work performed.\n";
            return 2;
        }
        if (!iterations || iterations > 10000) throw std::runtime_error("iterations must be 1-10000");
        OpenCLTestSha256 hashCheck;
        if (hashCheck.hex() != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            throw std::runtime_error("SHA-256 empty-vector selftest failed");
        hashCheck.append(reinterpret_cast<const uint8_t *>("abc"), 3);
        if (hashCheck.hex() != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            throw std::runtime_error("SHA-256 abc-vector selftest failed");
        OpenCLProvider provider;
        std::string error;
        const bool initialized = provider.initialize(gpuIndex, error);
        std::ostringstream report;
        report << "{\"schema_version\":1,\"native_cpp_provider\":true,\"input_language\":\"OpenCL C 1.2\","
                  "\"metal_tested\":false,\"mellow_jit_used\":false,\"linux_driver_port_loaded\":false,"
                  "\"physical_pci_identity_verified\":false,\"initialized\":" << boolean(initialized)
               << ",\"initialization_error\":" << quote(error);
        const auto &info = provider.device();
        report << ",\"device\":{\"platform\":" << quote(info.platform)
               << ",\"name\":" << quote(info.name) << ",\"vendor\":" << quote(info.vendor)
               << ",\"driver\":" << quote(info.driver) << ",\"version\":" << quote(info.version)
               << ",\"reported_type_bits\":" << info.reportedType
               << ",\"reported_vendor_id\":" << info.reportedVendorId
               << ",\"reported_device_id\":" << info.reportedDeviceId
               << ",\"device_id_from_intel_extension\":" << boolean(info.deviceIdFromIntelExtension) << '}';
        bool passed = initialized;
        report << ",\"bootstrap\":" << execution(provider.bootstrapEvidence());
        if (initialized) {
            const auto descriptor = provider.descriptor();
            const Step metal {Workload::Compute, 0, descriptor.id};
            const auto metalPlan = planWorkload(&descriptor, 1, &metal, 1, nullptr, 0, nullptr, 0);
            const bool metalRejected = metalPlan.status == PlanStatus::UnsupportedFeatures &&
                !(descriptor.verified & bit(Feature::ComputeTranslation));
            passed &= metalRejected;
            report << ",\"default_metal_route_rejected\":" << boolean(metalRejected)
                   << ",\"provider_verified_features\":" << descriptor.verified
                   << ",\"kernel_source\":" << quote(OpenCLProvider::witnessSource())
                   << ",\"seed\":" << seed;
            const auto start = std::chrono::steady_clock::now();
            OpenCLTestSha256 inputHash, expectedHash, readbackHash;
            unsigned verified = 0;
            uint64_t firstSequence = 0, lastSequence = 0, firstGpuStart = 0, lastGpuEnd = 0;
            std::vector<std::string> samples;
            std::string firstSample, lastSample, failedSample;
            const auto checkpoint = [&](unsigned slot) {
                std::ostringstream current;
                current << "{\"schema_version\":1,\"complete\":false,\"passed\":false,\"requested_iterations\":" << iterations
                        << ",\"verified_iterations\":" << verified << ",\"seed\":" << seed
                        << ",\"epoch\":" << descriptor.resetEpoch << ",\"last_sequence\":" << lastSequence
                        << ",\"last_gpu_end_ns\":" << lastGpuEnd
                        << ",\"input_stream_sha256\":" << quote(inputHash.hex())
                        << ",\"expected_stream_sha256\":" << quote(expectedHash.hex())
                        << ",\"readback_stream_sha256\":" << quote(readbackHash.hex()) << '}';
                writeJson(reportPath + (slot ? ".checkpoint-b.json" : ".checkpoint-a.json"), current.str());
            };
            checkpoint(0);
            for (unsigned run = 0; run < iterations; ++run) {
                std::vector<uint32_t> input(256), expected(256);
                for (size_t i = 0; i < input.size(); ++i) {
                    input[i] = (seed ^ static_cast<uint32_t>((i + run * 263) * 0x9E3779B9ULL)) & 0xFFFF;
                    expected[i] = input[i] * 7 + 3;
                }
                OpenCLExecution outcome;
                const bool ok = provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, expected, outcome);
                const bool accepted = ok && outcome.runtimePlanned && outcome.runtimeCompletionAccepted && outcome.resourcesReleased &&
                    outcome.resultsVerified && outcome.profilingVerified && outcome.eventOwnershipVerified &&
                    outcome.epoch == descriptor.resetEpoch &&
                    (run == 0 || (outcome.sequence == lastSequence + 1 && outcome.gpuStart >= lastGpuEnd));
                passed &= accepted;
                std::ostringstream sample;
                sample << "{\"iteration\":" << run << ",\"input\":" << array(input) << ",\"expected\":" << array(expected)
                       << ",\"execution\":" << execution(outcome) << '}';
                if (!accepted) { failedSample = sample.str(); break; }
                inputHash.words(input); expectedHash.words(expected); readbackHash.words(outcome.output);
                ++verified;
                if (run == 0) { firstSample = sample.str(); firstSequence = outcome.sequence; firstGpuStart = outcome.gpuStart; }
                lastSample = sample.str();
                lastSequence = outcome.sequence;
                lastGpuEnd = outcome.gpuEnd;
                if (iterations <= 3) samples.push_back(sample.str());
                if (verified == 1 || verified % 100 == 0 || verified == iterations) checkpoint((verified / 100) % 2);
            }
            if (iterations > 3 && !firstSample.empty()) {
                samples.push_back(firstSample);
                if (verified > 1) samples.push_back(lastSample);
            }
            report << ",\"runs_sampling\":" << quote(iterations <= 3 ? "all" : "first-and-last") << ",\"runs\":[";
            for (size_t i = 0; i < samples.size(); ++i) { if (i) report << ','; report << samples[i]; }
            report << "]";
            const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            report << ",\"submission_summary\":{\"requested_iterations\":" << iterations << ",\"verified_iterations\":" << verified
                   << ",\"elements_per_iteration\":256,\"all_runtime_and_readback_checks_passed\":" << boolean(verified == iterations)
                   << ",\"same_queue_device_epoch_verified\":" << boolean(verified == iterations)
                   << ",\"first_sequence\":" << firstSequence << ",\"last_sequence\":" << lastSequence
                   << ",\"epoch\":" << descriptor.resetEpoch << ",\"first_gpu_start_ns\":" << firstGpuStart
                   << ",\"last_gpu_end_ns\":" << lastGpuEnd << ",\"elapsed_seconds\":" << elapsed
                   << ",\"input_stream_sha256\":" << quote(inputHash.hex())
                   << ",\"expected_stream_sha256\":" << quote(expectedHash.hex())
                   << ",\"readback_stream_sha256\":" << quote(readbackHash.hex())
                   << ",\"hardware_reset_or_pagefault_counters_observed\":false}";
            report << ",\"first_failure\":" << (failedSample.empty() ? "null" : failedSample);
            passed &= verified == iterations;
            // Negative cases run through the production adapter. A compile
            // failure must not enqueue or gain a completion record.
            if (verified == iterations) {
            const std::vector<uint32_t> input {1, 2, 3, 4}, expected {10, 17, 24, 31};
            OpenCLExecution buildFailure;
            const bool invalidSourceRejected = !provider.executeOpenClC("this is not OpenCL C;", "bad", input, expected, buildFailure)
                && !buildFailure.submitted && !buildFailure.runtimeCompletionAccepted;
            OpenCLExecution oversized;
            const std::vector<uint32_t> tooLarge(OpenCLProvider::MaxElements + 1, 1);
            const bool oversizedRejected = !provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", tooLarge, tooLarge, oversized)
                && !oversized.submitted;
            OpenCLExecution wrongReference;
            const bool wrongReferenceRejected = !provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, input, wrongReference)
                && wrongReference.submitted && !wrongReference.resultsVerified && !wrongReference.runtimeCompletionAccepted;
            OpenCLExecution afterFailure;
            const bool invalidEpochRejected = !provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, expected, afterFailure)
                && !afterFailure.submitted && provider.descriptor().verified == 0;
            passed &= invalidSourceRejected && oversizedRejected && wrongReferenceRejected && invalidEpochRejected;
            report << ",\"negative_checks\":{\"invalid_source_rejected\":" << boolean(invalidSourceRejected)
                   << ",\"oversized_input_rejected\":" << boolean(oversizedRejected)
                   << ",\"wrong_reference_rejected\":" << boolean(wrongReferenceRejected)
                   << ",\"invalidated_session_rejected\":" << boolean(invalidEpochRejected)
                   << ",\"build_failure\":" << execution(buildFailure)
                   << ",\"wrong_reference\":" << execution(wrongReference)
                   << ",\"after_failure\":" << execution(afterFailure) << '}';
            } else report << ",\"negative_checks\":null";
        }
        report << ",\"passed\":" << boolean(passed) << '}';
        writeJson(reportPath, report.str());
        std::cout << (passed ? "PASS" : "FAIL") << ": native Mellow OpenCL C provider; Metal/JIT not executed\n";
        return passed ? 0 : 1;
    } catch (const std::exception &failure) {
        std::cerr << failure.what() << '\n';
        return 1;
    }
}
