#include "../Mellow/PatternMatch.hpp"
#include "../Mellow/StartupPolicy.hpp"
#include "../Mellow/RuntimeReadiness.hpp"
#include <stdio.h>
#include <stdlib.h>

static unsigned assertions = 0;
static void require(bool ok, const char *caseName) {
    ++assertions;
    if (!ok) { fprintf(stderr, "FAIL: %s\n", caseName); exit(1); }
}
int main() {
    using namespace MellowPattern;
    const uint8_t image[] = {0x48, 0x89, 0xE5, 0x90, 0xA1};
    const uint8_t first[] = {0x48, 0x89};
    const uint8_t last[] = {0x90, 0xA1};
    auto r = findUnique(image, sizeof(image), first, nullptr, 2);
    require(r.status == Status::Unique && r.offset == 0, "valid symbol at image offset zero");
    r = findUnique(image, sizeof(image), last, nullptr, 2);
    require(r.status == Status::Unique && r.offset == 3, "last valid image span");
    const uint8_t duplicated[] = {1, 2, 1, 2};
    const uint8_t pair[] = {1, 2};
    require(findUnique(duplicated, 4, pair, nullptr, 2).status == Status::Ambiguous, "duplicate route target refused");
    const uint8_t overlapping[] = {1, 1, 1};
    const uint8_t twoOnes[] = {1, 1};
    require(findUnique(overlapping, 3, twoOnes, nullptr, 2).status == Status::Ambiguous, "overlapping ambiguity");
    const uint8_t mask[] = {0xF0, 0x00};
    const uint8_t masked[] = {0x40, 0xFF};
    r = findUnique(image, sizeof(image), masked, mask, 2);
    require(r.status == Status::Unique && r.offset == 0, "masked low bits and wildcard byte");
    const uint8_t allWild[] = {0, 0};
    require(findUnique(image, 5, first, allWild, 2).status == Status::Invalid, "entirely unconstrained signature");
    require(findUnique(nullptr, 5, first, nullptr, 2).status == Status::Invalid, "null image");
    require(findUnique(image, 5, nullptr, nullptr, 2).status == Status::Invalid, "null signature");
    require(findUnique(image, 5, first, nullptr, 0).status == Status::Invalid, "empty signature");
    require(findUnique(image, 1, first, nullptr, 2).status == Status::Invalid, "signature longer than image");
    require(findUnique(image, 0, first, nullptr, 2).status == Status::Invalid, "empty image");
    require(!validAddressRange(0, 4), "null image virtual address");
    require(!validAddressRange(UINTPTR_MAX - 1, 3), "virtual end address overflow");
    require(validAddressRange(UINTPTR_MAX - 1, 2), "inclusive last representable address");
    require(!validAddressRange(16, 0), "empty virtual span");
    // Exhaustively exercise an independently counted family of masked searches.
    for (unsigned a = 0; a < 256; ++a) {
        for (unsigned b = 0; b < 16; ++b) {
            const uint8_t data[] = {static_cast<uint8_t>(a), 0xEE, static_cast<uint8_t>(b << 4), 0xEF};
            const uint8_t pat[] = {0xA0};
            const uint8_t m[] = {0xF0};
            const unsigned matches = (a / 16 == 10 ? 1U : 0U) + (b == 10 ? 1U : 0U);
            const auto found = findUnique(data, 4, pat, m, 1);
            require(found.status == (matches == 0 ? Status::NotFound : matches == 1 ? Status::Unique : Status::Ambiguous),
                    "masked search count across 4096 input pairs");
        }
    }
    using namespace MellowStartup;
    require(evaluate(25, false, false, false, false) == Admission::ExplicitTahoeTrialRequired, "Tahoe never silently inherits old ABI");
    require(evaluate(25, true, false, false, false) == Admission::ResearchTrial, "legacy Apple-driver experiment remains explicit");
    require(evaluate(25, true, false, true, false) == Admission::NativeBackendUnavailable, "native backend request cannot replace owner");
    require(evaluate(25, true, false, true, true) == Admission::ResearchTrial, "integrated native backend may enter trial");
    require(evaluate(25, true, true, false, true) == Admission::VesaConflict, "VESA and acceleration driver conflict");
    require(evaluate(24, false, false, false, false) == Admission::ResearchTrial, "existing Sequoia research range unchanged");
    require(evaluate(22, false, false, false, false) == Admission::ResearchTrial, "existing Ventura research range unchanged");
    require(evaluate(21, true, false, false, true) == Admission::UnsupportedKernel, "older ABI refused");
    require(evaluate(26, true, false, false, true) == Admission::UnsupportedKernel, "future ABI refused despite opt-in");

    using namespace MellowRuntime;
    require(!BackendOwnerIntegrated, "this build truthfully marks native backend owner absent");
    const auto configured = MellowRuntime::evaluate(ConfigurationMask | PhysicalIdentity7D41);
    require(configured.stage == Stage::PhysicalProvider, "identity alone stops before BAR0/GMD proof");
    require(configured.mayAttemptBar0Mapping, "identity permits bounded BAR0 attempt");
    require(!configured.mayAttemptGucAuthentication, "identity cannot authenticate GuC");
    require(!configured.maySubmitContext, "identity cannot submit a context");
    require(!configured.mayPublishAccelerator, "identity cannot publish accelerator");
    require(!configured.mayAdvertiseMetal, "identity cannot advertise Metal");
    const uint64_t submissionReady = ConfigurationMask | PhysicalMask | AddressSpaceMask |
                                     FirmwareMask | SubmissionPrerequisiteMask;
    const auto beforeExecution = MellowRuntime::evaluate(submissionReady);
    require(beforeExecution.maySubmitContext, "all driver-side prerequisites permit one evidence job");
    require(!beforeExecution.mayPublishAccelerator, "uncompleted evidence job cannot publish accelerator");
    require(!beforeExecution.mayAdvertiseMetal, "kernel submission prerequisites are not Metal");
    const auto all = MellowRuntime::evaluate(AllEvidenceMask);
    require(all.stage == Stage::Ready && all.mayAdvertiseMetal, "all twenty proofs are required for Metal-ready");
    for (unsigned bit = 0; bit < 20; ++bit) {
        const auto oneMissing = MellowRuntime::evaluate(AllEvidenceMask & ~(1ULL << bit));
        require(!oneMissing.mayAdvertiseMetal, "each individual missing proof denies Metal-ready");
    }
    puts("PASS: pattern fallback boundaries, ambiguity, masks, overflow and kernel admission");
    printf("assertions=%u; no GPU/hardware execution\n", assertions);
}
