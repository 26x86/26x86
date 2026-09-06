//  Copyright © 2026 Stezza @ inc. Licensed under the Thou Shalt Not Profit License version 1.0. See LICENSE for
//  details.

#include "kern_mellow.hpp"
#include "kern_gen11.hpp"
#include "kern_genx.hpp"
#include "kern_model.hpp"
#include "DYLDPatches.hpp"
#include "HDMI.hpp"
#include "kern_patcherplus.hpp"
#include "RuntimeReadiness.hpp"
#include <Headers/kern_api.hpp>
#include <Headers/kern_devinfo.hpp>


static const char *pathIOAcceleratorFamily2= "/System/Library/Extensions/IOAcceleratorFamily2.kext/Contents/MacOS/IOAcceleratorFamily2";
static const char *pathAGDP = "/System/Library/Extensions/AppleGraphicsControl.kext/Contents/PlugIns/"
							  "AppleGraphicsDevicePolicy.kext/Contents/MacOS/AppleGraphicsDevicePolicy";
static const char *pathBacklight = "/System/Library/Extensions/AppleBacklight.kext/Contents/MacOS/AppleBacklight";
static const char *pathMCCSControl = "/System/Library/Extensions/AppleMCCSControl.kext/Contents/MacOS/AppleMCCSControl";
static const char *pathIOGraphics= "/System/Library/Extensions/IOGraphicsFamily.kext/IOGraphicsFamily";

static KernelPatcher::KextInfo kextAGDP {"com.apple.driver.AppleGraphicsDevicePolicy", &pathAGDP, 1, {true}, {},
	KernelPatcher::KextInfo::Unloaded};
static KernelPatcher::KextInfo kextBacklight {"com.apple.driver.AppleBacklight", &pathBacklight, 1, {true}, {},
	KernelPatcher::KextInfo::Unloaded};
static KernelPatcher::KextInfo kextMCCSControl {"com.apple.driver.AppleMCCSControl", &pathMCCSControl, 1, {true}, {},
	KernelPatcher::KextInfo::Unloaded};
static KernelPatcher::KextInfo kextIOGraphics { "com.apple.iokit.IOGraphicsFamily", &pathIOGraphics, 1, {true}, {},
	KernelPatcher::KextInfo::Unloaded };
static KernelPatcher::KextInfo kextIOAcceleratorFamily2 { "com.apple.iokit.IOAcceleratorFamily2", &pathIOAcceleratorFamily2, 1, {true}, {},
	KernelPatcher::KextInfo::Unloaded };

MellowCore *MellowCore::callback = nullptr;

static Genx genx;
static Gen11 gen11;
static DYLDPatches dyldpatches;
static HDMI agfxhda;

static uint8_t builtin2[] = {0x00, 0x00, 0x49, 0x9A};
static uint8_t builtin3[] = {0x49, 0x9A, 0x00, 0x00};

static bool isIGPUPropSeedingEnabled() {
	int enabled = 0;
	if (PE_parse_boot_argn("mellowforceprops", &enabled, sizeof(enabled))) {
		return enabled != 0;
	}

	return checkKernelArgument("-mellowforceprops");
}

static bool seedIGPUPropertiesOnEntry(IORegistryEntry *entry, const char *branding) {
	if (!entry) {
		return false;
	}

	bool changed = false;

	// Default TGL spoof identity for Ultra bring-up. EFI DeviceProperties remains
	// authoritative; this recovery path fills only missing values.
	if (!entry->getProperty("AAPL,ig-platform-id")) {
		entry->setProperty("AAPL,ig-platform-id", builtin2, arrsize(builtin2));
		changed = true;
	}

	if (!entry->getProperty("device-id")) {
		entry->setProperty("device-id", builtin3, arrsize(builtin3));
		changed = true;
	}

	if (!entry->getProperty("built-in")) {
		static uint8_t builtin[] = {0x00};
		entry->setProperty("built-in", builtin, arrsize(builtin));
		changed = true;
	}

	if (!entry->getProperty("AAPL,slot-name")) {
		entry->setProperty("AAPL,slot-name", const_cast<char *>("built-in"), 9);
		changed = true;
	}

	if (!entry->getProperty("hda-gfx")) {
		entry->setProperty("hda-gfx", const_cast<char *>("onboard-1"), 10);
		changed = true;
	}

	if (!entry->getProperty("model") && branding) {
		entry->setProperty("model", const_cast<char *>(branding), strlen(branding) + 1);
		changed = true;
	}

	if (!entry->getProperty("framebuffer-unifiedmem")) {
		static uint8_t unifiedMem[] = {0x00, 0x00, 0x00, 0x60}; // 1536 MB
		entry->setProperty("framebuffer-unifiedmem", unifiedMem, arrsize(unifiedMem));
		changed = true;
	}

	return changed;
}

static void seedIGPUPropertiesEarly(const char *branding) {
	// Try common ACPI namespace variants used by laptop firmware before DeviceInfo scans.
	const char *paths[] = {
		"IOService:/AppleACPIPlatformExpert/PC00@0/IGPU@2",
		"IOService:/AppleACPIPlatformExpert/PC00@0/GFX0@2",
		"IOService:/AppleACPIPlatformExpert/PCI0@0/IGPU@2",
		"IOService:/AppleACPIPlatformExpert/PCI0@0/GFX0@2"
	};

	bool found = false;
	bool changed = false;
	for (auto path : paths) {
		auto *entry = IORegistryEntry::fromPath(path, gIOServicePlane);
		if (!entry) {
			continue;
		}
		found = true;
		if (seedIGPUPropertiesOnEntry(entry, branding)) {
			changed = true;
		}
		entry->release();
	}

	if (found) {
		SYSLOG("mellow", "Early IGPU pre-seed via IOService path: changed=%d", changed);
	} else {
		SYSLOG("mellow", "Early IGPU pre-seed skipped: no IGPU path resolved before DeviceInfo");
	}
}

void MellowCore::init() {
	callback = this;

	// Gate the plugin before registering any patch callbacks. Intel publishes
	// these family-6 model numbers for Meteor Lake and Arrow Lake variants.
	uint32_t maxLeaf = 0, vendorB = 0, vendorC = 0, vendorD = 0;
	asm volatile("cpuid" : "=a"(maxLeaf), "=b"(vendorB), "=c"(vendorC), "=d"(vendorD) : "a"(0));
	const bool genuineIntel = vendorB == 0x756E6547U && vendorD == 0x49656E69U && vendorC == 0x6C65746EU;
	if (!genuineIntel || maxLeaf < 1) {
		SYSLOG("mellow", "disabled: unsupported CPU vendor or missing CPUID leaf 1");
		return;
	}

	uint32_t eax = 0, ebx = 0, ecx = 0, edx = 0;
	asm volatile("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(1));
	cpuFamily = (eax >> 8) & 0xFU;
	cpuModel = (eax >> 4) & 0xFU;
	const uint32_t extFamily = (eax >> 20) & 0xFFU;
	const uint32_t extModel = (eax >> 16) & 0xFU;
	if (cpuFamily == 0xFU) cpuFamily += extFamily;
	if (cpuFamily == 0x6U || cpuFamily == 0xFU) cpuModel |= extModel << 4;
	cpuStepping = eax & 0xFU;

	switch (cpuModel) {
		case 0xAA: // Meteor Lake-L
		case 0xAC: // Meteor Lake
		case 0xB5: // Arrow Lake-U
		case 0xC5: // Arrow Lake-H
		case 0xC6: // Arrow Lake-S
			ultraCpuEligible = cpuFamily == 0x6U;
			break;
		default:
			ultraCpuEligible = false;
			break;
	}

	// Kept for the inherited circuit breakers. An admitted Mellow target is
	// deliberately never treated as native Tiger Lake.
	isRealTGL = cpuFamily == 0x6U && (cpuModel == 0x8CU || cpuModel == 0x8DU);
	SYSLOG("mellow", "CPU family=0x%x model=0x%x stepping=%u ultraEligible=%d isRealTGL=%d",
	       cpuFamily, cpuModel, cpuStepping, ultraCpuEligible, isRealTGL);
	if (!ultraCpuEligible) {
		SYSLOG("mellow", "disabled: Mellow supports Core Ultra CPUs only");
		return;
	}
	
	lilu.onKextLoadForce(&kextAGDP);
	/*lilu.onKextLoadForce(&kextBacklight);
	lilu.onKextLoadForce(&kextMCCSControl);
	lilu.onKextLoadForce(&kextIOGraphics);*/
	lilu.onKextLoadForce(&kextIOAcceleratorFamily2);
	
	// Genx supplies a few shared helpers used by the TGL path. Its init no
	// longer registers the legacy ICL framebuffer.
	genx.init();
	gen11.init();
	//agfxhda.init();
	dyldpatches.init();
	
    lilu.onPatcherLoadForce(
        [](void *user, KernelPatcher &patcher) { static_cast<MellowCore *>(user)->processPatcher(patcher); }, this);
    lilu.onKextLoadForce(
        nullptr, 0,
        [](void *user, KernelPatcher &patcher, size_t index, mach_vm_address_t address, size_t size) {
            static_cast<MellowCore *>(user)->processKext(patcher, index, address, size);
        },
        this);
	
}


void MellowCore::processPatcher(KernelPatcher &patcher) {
	ultraActive = false;
	if (!ultraCpuEligible) return;

	auto *devInfo = DeviceInfo::create();
	if (!devInfo) {
		SYSLOG("mellow", "disabled: failed to create DeviceInfo");
		return;
	}

	iGPU = OSDynamicCast(IOPCIDevice, devInfo->videoBuiltin);
	if (!iGPU) {
		SYSLOG("mellow", "disabled: built-in video device is not an IOPCIDevice");
		DeviceInfo::deleter(devInfo);
		return;
	}

	// Read the physical PCI identity before consulting any OpenCore-injected
	// device-id property. The latter is expected to contain the 0x9A49 spoof.
	const uint16_t vendorId = WIOKit::readPCIConfigValue(iGPU, WIOKit::kIOPCIConfigVendorID);
	deviceId = WIOKit::readPCIConfigValue(iGPU, WIOKit::kIOPCIConfigDeviceID);
	pciRevision = WIOKit::readPCIConfigValue(iGPU, WIOKit::kIOPCIConfigRevisionID);
	if (vendorId != 0x8086U || !isSupportedUltraDevice(deviceId) || !isSupportedUltraPair(cpuModel, deviceId)) {
		SYSLOG("mellow", "disabled: unsupported CPU/GPU pair family=0x%x model=0x%x pci=%04x:%04x",
		       cpuFamily, cpuModel, vendorId, deviceId);
		iGPU = nullptr;
		DeviceInfo::deleter(devInfo);
		return;
	}
	pciDeviceBdf = static_cast<uint32_t>(iGPU->getBusNumber()) << 16 |
	               static_cast<uint32_t>(iGPU->getDeviceNumber()) << 11 |
	               static_cast<uint32_t>(iGPU->getFunctionNumber()) << 8;
	// Diagnostic correlation for the user-space probe. These values come from
	// config reads above, before this plugin installs its ID-read wrappers.
	// IORegistry properties are not a cryptographic hardware attestation.
	bool identityPublished = iGPU->setProperty("MellowPhysicalVendorID", static_cast<uint64_t>(vendorId), 32);
	identityPublished = iGPU->setProperty("MellowPhysicalDeviceID", static_cast<uint64_t>(deviceId), 32) && identityPublished;
	identityPublished = iGPU->setProperty("MellowPhysicalBDF", static_cast<uint64_t>(pciDeviceBdf), 32) && identityPublished;
	identityPublished = iGPU->setProperty("MellowPhysicalIdentitySource", "pci-config-before-spoof") && identityPublished;
	uint64_t nativeEvidence = deviceId == 0x7D41U ? MellowRuntime::PhysicalIdentity7D41 : 0;
	if (checkKernelArgument("-mellowtahoe")) nativeEvidence |= MellowRuntime::BootOptIn;
	if (!checkKernelArgument("-igfxvesa")) nativeEvidence |= MellowRuntime::VesaDisabled;
	const auto nativeReadiness = MellowRuntime::evaluate(nativeEvidence);
	identityPublished = iGPU->setProperty("MellowNativeXeVerifiedMask", nativeReadiness.verified, 64) && identityPublished;
	identityPublished = iGPU->setProperty("MellowNativeXeMissingMask", nativeReadiness.missing, 64) && identityPublished;
	identityPublished = iGPU->setProperty("MellowNativeXeStage", MellowRuntime::stageName(nativeReadiness.stage)) && identityPublished;
	identityPublished = iGPU->setProperty("MellowNativeXeBackendIntegrated",
		static_cast<uint64_t>(MellowRuntime::BackendOwnerIntegrated), 8) && identityPublished;
	identityPublished = iGPU->setProperty("MellowNativeXeMetalReady",
		static_cast<uint64_t>(nativeReadiness.mayAdvertiseMetal), 8) && identityPublished;
	if (!identityPublished)
		SYSLOG("mellow", "physical identity diagnostic publication incomplete; correlate with PCI startup log");
	SYSLOG("mellow", "native Xe backend evidence stage=%s verified=0x%llx missing=0x%llx first-missing=%s NativeMetalReady=%d",
		MellowRuntime::stageName(nativeReadiness.stage),
		static_cast<unsigned long long>(nativeReadiness.verified),
		static_cast<unsigned long long>(nativeReadiness.missing),
		MellowRuntime::evidenceName(MellowRuntime::firstMissing(nativeReadiness.missing)),
		nativeReadiness.mayAdvertiseMetal);

	ultraActive = true;
	isRealTGL = false;
	const char *branding = getBranding(deviceId);
	SYSLOG("mellow", "enabled: %s pci=%04x:%04x revision=0x%x cpuModel=0x%x",
	       branding, vendorId, deviceId, pciRevision, cpuModel);

	// Establish the CoreDisplay hook before processSwitchOff can wait for a
	// discrete GPU. Nothing reaches this point on a non-Ultra platform.
	if (!checkKernelArgument("-mellowdyldoff")) {
		dyldpatches.processPatcher(patcher);
	} else {
		DBGLOG("mellow", "DYLD patches disabled by boot argument -mellowdyldoff");
	}

	if (isIGPUPropSeedingEnabled()) {
		seedIGPUPropertiesEarly(branding);
	} else {
		SYSLOG("mellow", "EFI DeviceProperties mode: rescue property seeding disabled (use -mellowforceprops to enable)");
	}

	devInfo->processSwitchOff();

	// Required by the inherited TGL attach path.
	iGPU->enablePCIPowerManagement(kPCIPMCSPowerStateD0);
	iGPU->setBusMasterEnable(true);
	iGPU->setMemoryEnable(true);
	WIOKit::renameDevice(iGPU, "IGPU");
	WIOKit::awaitPublishing(iGPU);

	if (isIGPUPropSeedingEnabled()) {
		seedIGPUPropertiesOnEntry(iGPU, branding);
	}

	// Xe-LPG moves this information to MMIO GGC. PCI GGC and an invented
	// 128 MiB floor can expose memory which firmware never reserved.
	// This is total DSM only; WOPCM/GSC subtraction and allocation are separate.
	stolen_size = 0;
	setRMMIOIfNecessary();
	UInt32 ggc = 0;
	if (readReg32Checked(MellowHardware::graphicsControl, ggc) &&
	    MellowHardware::decodeDsmReservation(ggc, stolen_size)) {
		SYSLOG("mellow", "DSM total reservation=0x%x GGC=0x%08x (not allocator-usable size)", stolen_size, ggc);
	} else {
		SYSLOG("mellow", "DSM reservation unknown, GGC=0x%08x; stolen-memory size patch unavailable", ggc);
	}

	KernelPatcher::routeVirtual(iGPU, WIOKit::PCIConfigOffset::ConfigRead16, configRead16, &orgConfigRead16);
	KernelPatcher::routeVirtual(iGPU, WIOKit::PCIConfigOffset::ConfigRead32, configRead32, &orgConfigRead32);
	DeviceInfo::deleter(devInfo);

	/*KernelPatcher::RouteRequest request {"__ZN15OSMetaClassBase12safeMetaCastEPKS_PK11OSMetaClass", wrapSafeMetaCast,
		this->orgSafeMetaCast};
	PANIC_COND(!patcher.routeMultipleLong(KernelPatcher::KernelID, &request, 1), "mellow",
		"Failed to route kernel symbols");*/
}

OSMetaClassBase *MellowCore::wrapSafeMetaCast(const OSMetaClassBase *anObject, const OSMetaClass *toMeta) {
	auto ret = FunctionCast(wrapSafeMetaCast, callback->orgSafeMetaCast)(anObject, toMeta);
	if (UNLIKELY(!ret)) {
		for (const auto &ent : callback->metaClassMap) {
			if (LIKELY(ent[0] == toMeta)) {
				return FunctionCast(wrapSafeMetaCast, callback->orgSafeMetaCast)(anObject, ent[1]);
			} else if (UNLIKELY(ent[1] == toMeta)) {
				return FunctionCast(wrapSafeMetaCast, callback->orgSafeMetaCast)(anObject, ent[0]);
			}
		}
	}
	return ret;
}

bool MellowCore::wrapIGAccelDeviceStart(void *that) {
	auto ret = FunctionCast(wrapIGAccelDeviceStart, callback->orgIGAccelDeviceStart)(that);
	// A failed start must remain a failure; published capabilities cannot stand
	// in for an initialized accelerator and working command execution.
	DBGLOG("mellow", "IOAccelF2: IGAccelDevice::deviceStart returned %d", ret);
	return ret;
}

void MellowCore::logRejectedMMIO(const char *operation, unsigned long reg) {
	const uint32_t count = __sync_fetch_and_add(&mmioFaultCount, 1U);
	if (count < 16) {
		SYSLOG("mellow", "MMIO rejected %s byteOffset=0x%lx BAR0 length=0x%llx (no indirect fallback)",
		       operation, reg, static_cast<uint64_t>(rmmio ? rmmio->getLength() : 0));
	}
}

void MellowCore::setRMMIOIfNecessary() {
	if (mmioValid()) return;
	rmmioPtr = nullptr;
	OSSafeReleaseNULL(rmmio);
	if (!iGPU) {
		SYSLOG("mellow", "BAR0 map skipped: no active iGPU");
		return;
	}
	auto *mapping = iGPU->mapDeviceMemoryWithRegister(kIOPCIConfigBaseAddress0, kIOMapInhibitCache);
	if (!mapping || mapping->getLength() < sizeof(UInt32) ||
	    !mapping->getVirtualAddress() || (mapping->getVirtualAddress() & 3U)) {
		SYSLOG("mellow", "BAR0 map failed or returned invalid length/address");
		OSSafeReleaseNULL(mapping);
		return;
	}
	rmmio = mapping;
	rmmioPtr = reinterpret_cast<volatile UInt32 *>(mapping->getVirtualAddress());

	// Read-only display-domain evidence; a mapping is not acceleration proof.
	UInt32 pwrWellCtl1 = 0, dcStateEn = 0;
	if (readReg32Checked(0x45400, pwrWellCtl1) && readReg32Checked(0x45504, dcStateEn)) {
		SYSLOG("mellow", "E0001 BAR0 mapped len=0x%llx PWR_WELL_CTL1=0x%08x DC_STATE_EN=0x%08x",
		       static_cast<uint64_t>(mapping->getLength()), pwrWellCtl1, dcStateEn);
	}
}

void MellowCore::setApertureIfNecessary() {
	// Xe-LPG BAR2 is LMEMBAR system-stolen memory. The inherited users pass
	// GGTT offsets; mapping them as old TGL aperture offsets is incorrect.
	// Until a DSM/DM-PTE aware path exists, report the legacy aperture absent.
	if (!isRealTGL) {
		aperturePtr = nullptr;
		apertureLen = 0;
		OSSafeReleaseNULL(aperture);
		if (!apertureUnavailableLogged) {
			apertureUnavailableLogged = true;
			SYSLOG("mellow", "BAR2 legacy GGTT aperture unavailable on Xe-LPG; requires DSM/DM-PTE aware access");
		}
		return;
	}
	if (aperture && aperturePtr && apertureLen >= sizeof(UInt32)) return;
	aperturePtr = nullptr;
	apertureLen = 0;
	OSSafeReleaseNULL(aperture);
	if (!iGPU) {
		SYSLOG("mellow", "BAR2 map skipped: no active iGPU");
		return;
	}
	auto *mapping = iGPU->mapDeviceMemoryWithRegister(kIOPCIConfigBaseAddress2, kIOMapInhibitCache);
	if (!mapping || mapping->getLength() < sizeof(UInt32) ||
	    !mapping->getVirtualAddress() || (mapping->getVirtualAddress() & 3U)) {
		SYSLOG("mellow", "BAR2 map failed or returned invalid length/address");
		OSSafeReleaseNULL(mapping);
		return;
	}
	aperture = mapping;
	aperturePtr = reinterpret_cast<volatile UInt32 *>(mapping->getVirtualAddress());
	apertureLen = mapping->getLength();
	SYSLOG("mellow", "V201: BAR2 mapped, len=0x%llx; address semantics require platform validation", apertureLen);
}

// Observe the startup dependency failure without forging a completed fence.
// Fixing interrupt/start ordering requires hardware evidence; claiming stamp
// completion can let clients consume unfinished GPU memory or reuse it too soon.
static mach_vm_address_t orgWaitForStamp = 0;
static IOReturn wrapWaitForStamp(void *that, int32_t channel, unsigned int stamp, unsigned int *outStamp) {
	IOReturn ret = FunctionCast(wrapWaitForStamp, orgWaitForStamp)(that, channel, stamp, outStamp);
	if (ret != kIOReturnSuccess && !Gen11::gGfxAccelStartDone) {
		SYSLOG("mellow", "V221: stamp(%d,%u) failed before GFX start, preserving ret=0x%x and actual outStamp",
			   channel, stamp, ret);
	}
	return ret;
}

// Observe the surface mode failure without silently rewriting client semantics.
// The inherited 0xff8073c0 mask has no validated Tahoe ABI contract.
static mach_vm_address_t orgSetIdMode = 0;
static IOReturn wrapSetIdMode(void *that, uint32_t id, uint32_t mode) {
    IOReturn ret = FunctionCast(wrapSetIdMode, orgSetIdMode)(that, id, mode);

    static int v500Count = 0;
    if (v500Count < 32) {
        ++v500Count;
        if (ret != kIOReturnSuccess)
            SYSLOG("mellow", "V500[%d]: set_id_mode FAILED ret=0x%x id=0x%x mode=0x%x",
                   v500Count, ret, id, mode);
    }
    return ret;
}

bool MellowCore::processKext(KernelPatcher &patcher, size_t index, mach_vm_address_t address, size_t size) {
	if (!ultraActive) return false;

	if (kextIOAcceleratorFamily2.loadIndex == index) {
		SYSLOG("mellow", "IOAccelF2: TEXT 0x%llx size 0x%lx", address, size);
		
		// ── V40: f2 FIXED based on V39 diagnostics ──
		// V39 revealed: Sonoma uses push r12; push rbx; push rax (41 54 53 50)
		// as function prologue instead of sub rsp,imm8 (48 83 ec).
		// Two matching test edx,imm32; je found at +0x38b0 and +0x102e6.
		// Patching both (count=2) to bypass capability checks.
		static const uint8_t f2_f[]  = {0x41, 0x54, 0x53, 0x50, 0xf7, 0xc2, 0x00, 0x00, 0x00, 0x00, 0x74, 0x00};
		static const uint8_t f2_m[]  = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00};
		static const uint8_t f2_r[]  = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEB, 0x00};
		static const uint8_t f2_rm[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00};
		const LookupPatchPlus p2 {&kextIOAcceleratorFamily2, f2_f, f2_m, f2_r, f2_rm, 2};
		
		// necessary : without it hang on boot
		bool f2ok = p2.apply(patcher, address, size);
		patcher.clearError();
		SYSLOG("mellow", "IOAccelF2 f2 (fixed): %s", f2ok ? "OK" : "FAILED");
		
		// ── V41: f1 FIXED based on V40 diagnostics ──
		// V40 revealed: Sonoma has jne (0x75) at -16 from mov r9d,[r15+0x284],
		// NOT je (0x74) at -2 as the original pattern assumed.
		// Code structure: cmp eax,ebx; jne +0x39; <device-specific setup>; mov r9d,[r15+0x284]
		// This is a device-ID capability check: vtable call returns ID, compared with expected.
		// NOP the jne (75 XX → 90 90) so our device 0x9A49 always falls through.
		// Pattern: jne XX; mov rax,[r15+disp32]; mov r8,[rax+disp32]; mov r9d,[r15+disp32]
		static const uint8_t f1_f[]  = {0x75, 0x00, 0x49, 0x8b, 0x87, 0x00, 0x00, 0x00, 0x00, 0x4c, 0x8b, 0x80, 0x00, 0x00, 0x00, 0x00, 0x45, 0x8b, 0x8f};
		static const uint8_t f1_m[]  = {0xFF, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF};
		static const uint8_t f1_r[]  = {0x90, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
		static const uint8_t f1_rm[] = {0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
		const LookupPatchPlus p1 {&kextIOAcceleratorFamily2, f1_f, f1_m, f1_r, f1_rm, 1};
		// V206: disabled IOAccelF2 f1 patch + IGAccelDevice::deviceStart hook + V181 lock
		// resolves to match Visual Ehrmanntraut's working config. Restore if regression.
		/*bool f1ok = p1.apply(patcher, address, size);
		patcher.clearError();
		SYSLOG("mellow", "IOAccelF2 f1 (fixed): %s", f1ok ? "OK" : "FAILED");

		RouteRequestPlus routes[] = {
			{"__ZN13IGAccelDevice11deviceStartEv", wrapIGAccelDeviceStart, this->orgIGAccelDeviceStart},
		};
		if (RouteRequestPlus::routeAll(patcher, index, routes, address, size)) {
			SYSLOG("mellow", "IOAccelF2: hooked IGAccelDevice::deviceStart");
		} else {
			patcher.clearError();
			SYSLOG("mellow", "IOAccelF2: IGAccelDevice::deviceStart symbol not found");
		}

		// V181: resolve lockForCPUAccess / unlockForCPUAccess for Gen11 blit3d scratch init
		if (Gen11::callback) {
			SolveRequestPlus ioaf2Solve[] = {
				{"__ZN16IOAccelSysMemory16lockForCPUAccessEP4taskj", Gen11::callback->oIOAF2_lockForCPUAccess},
				{"__ZN16IOAccelSysMemory18unlockForCPUAccessEP4task", Gen11::callback->oIOAF2_unlockForCPUAccess},
			};
			if (SolveRequestPlus::solveAll(patcher, index, ioaf2Solve, address, size)) {
				SYSLOG("mellow", "V181: IOAF2 lock/unlock resolved lock=%p unlock=%p",
				       reinterpret_cast<void *>(Gen11::callback->oIOAF2_lockForCPUAccess),
				       reinterpret_cast<void *>(Gen11::callback->oIOAF2_unlockForCPUAccess));
			} else {
				patcher.clearError();
				SYSLOG("mellow", "V181: IOAF2 lock/unlock resolve failed");
			}
		}*/

		// Observe wait/start ordering while preserving the driver's completion result.
		RouteRequestPlus wfsRequest[] = {
			{"__ZN20IOAccelEventMachine212waitForStampEijPj", wrapWaitForStamp, orgWaitForStamp},
		};
		if (RouteRequestPlus::routeAll(patcher, index, wfsRequest, address, size)) {
			SYSLOG("mellow", "V221: hooked IOAccelEventMachine2::waitForStamp");
		} else {
			patcher.clearError();
			SYSLOG("mellow", "V221: waitForStamp hook FAILED — symbol not found");
		}

		// V500: IOAccelLegacySurface::set_id_mode — diagnostic logger.
		RouteRequestPlus simRequest[] = {
			{"__ZN20IOAccelLegacySurface11set_id_modeEjj", wrapSetIdMode, orgSetIdMode},
		};
		if (RouteRequestPlus::routeAll(patcher, index, simRequest, address, size)) {
			SYSLOG("mellow", "V500: hooked IOAccelLegacySurface::set_id_mode");
		} else {
			patcher.clearError();
			SYSLOG("mellow", "V500: set_id_mode hook FAILED — symbol not found");
		}

	}  else if (kextIOGraphics.loadIndex == index) {
		/*
		KernelPatcher::RouteRequest requests[] = {
				{"__ZN13IOFramebuffer25extValidateDetailedTimingEP8OSObjectPvP25IOExternalMethodArguments", wrapValidateDetailedTiming},
			};
			patcher.routeMultiple(index, requests, address, size);
			patcher.clearError();*/
		
	}  else if (kextAGDP.loadIndex == index) {
		const LookupPatchPlus patch {&kextAGDP, kAGDPBoardIDKeyOriginal, kAGDPBoardIDKeyPatched, 1};
		SYSLOG_COND(!patch.apply(patcher, address, size), "mellow", "Failed to apply AGDP board-id patch");

		/*if (getKernelVersion() == KernelVersion::Ventura) {
			const LookupPatchPlus patch {&kextAGDP, kAGDPFBCountCheckVenturaOriginal, kAGDPFBCountCheckVenturaPatched,
				1};
			SYSLOG_COND(!patch.apply(patcher, address, size), "mellow", "Failed to apply AGDP fb count check patch");
		} else {
			const LookupPatchPlus patch {&kextAGDP, kAGDPFBCountCheckOriginal, kAGDPFBCountCheckPatched, 1};
			SYSLOG_COND(!patch.apply(patcher, address, size), "mellow", "Failed to apply AGDP fb count check patch");
		}*/
	}  else if (kextBacklight.loadIndex == index) {
		// V204b: re-enable AppleIntelPanel::setDisplay route + backlight string patch.
		// Friend's working version has these enabled. Sets up panel data for backlight ramp.
		KernelPatcher::RouteRequest request {"__ZN15AppleIntelPanel10setDisplayEP9IODisplay", wrapApplePanelSetDisplay,
			orgApplePanelSetDisplay};
		if (patcher.routeMultiple(kextBacklight.loadIndex, &request, 1, address, size)) {
			const UInt8 find[] = {"F%uT%04x"};
			const UInt8 replace[] = {"F%uTxxxx"};
			const LookupPatchPlus patch {&kextBacklight, find, replace, 1};
			SYSLOG_COND(!patch.apply(patcher, address, size), "mellow", "Failed to apply backlight patch");
		}
} else if (kextMCCSControl.loadIndex == index) {
		/*KernelPatcher::RouteRequest requests[] = {
				{"__ZN25AppleMCCSControlGibraltar5probeEP9IOServicePi", wrapFunctionReturnZero},
				{"__ZN21AppleMCCSControlCello5probeEP9IOServicePi", wrapFunctionReturnZero},
			};
			patcher.routeMultiple(index, requests, address, size);
			patcher.clearError();*/
} else if (gen11.processKext(patcher, index, address, size)) {
        DBGLOG("mellow", "Processed Generation 11 configuration");
    } /*else if (agfxhda.processKext(patcher, index, address, size)) {
		DBGLOG("mellow", "Processed AppleGFXHDA");
	}*/
    return true;
}



uint16_t MellowCore::configRead16(IORegistryEntry *service, uint32_t space, uint8_t offset) {
	if (callback && callback->orgConfigRead16) {
		auto result = callback->orgConfigRead16(service, space, offset);
		uint32_t device;
		if (callback->ultraActive && service == callback->iGPU &&
		    WIOKit::getOSDataValue(service, "device-id", device)) {
			return MellowHardware::spoofConfig16(space, callback->pciDeviceBdf, offset,
			                                    result, callback->deviceId, device);
		}

		return result;
	}

	return 0xFFFFU;
}

uint32_t MellowCore::configRead32(IORegistryEntry *service, uint32_t space, uint8_t offset) {
	if (callback && callback->orgConfigRead32) {
		auto result = callback->orgConfigRead32(service, space, offset);
		uint32_t device;
		if (callback->ultraActive && service == callback->iGPU &&
		    WIOKit::getOSDataValue(service, "device-id", device)) {
			return MellowHardware::spoofConfig32(space, callback->pciDeviceBdf, offset,
			                                    result, callback->deviceId, device);
		}

		return result;
	}

	return 0xFFFFFFFFU;
}

size_t MellowCore::wrapFunctionReturnZero() { return 0; }

struct ApplePanelData {
	const char *deviceName;
	UInt8 deviceData[36];
};

static ApplePanelData appleBacklightData[] = {
	{"F14Txxxx", {0x00, 0x11, 0x00, 0x00, 0x00, 0x34, 0x00, 0x52, 0x00, 0x73, 0x00, 0x94, 0x00, 0xBE, 0x00, 0xFA, 0x01,
					 0x36, 0x01, 0x72, 0x01, 0xC5, 0x02, 0x2F, 0x02, 0xB9, 0x03, 0x60, 0x04, 0x1A, 0x05, 0x0A, 0x06,
					 0x0E, 0x07, 0x10}},
	{"F15Txxxx", {0x00, 0x11, 0x00, 0x00, 0x00, 0x36, 0x00, 0x54, 0x00, 0x7D, 0x00, 0xB2, 0x00, 0xF5, 0x01, 0x49, 0x01,
					 0xB1, 0x02, 0x2B, 0x02, 0xB8, 0x03, 0x59, 0x04, 0x13, 0x04, 0xEC, 0x05, 0xF3, 0x07, 0x34, 0x08,
					 0xAF, 0x0A, 0xD9}},
	{"F16Txxxx", {0x00, 0x11, 0x00, 0x00, 0x00, 0x18, 0x00, 0x27, 0x00, 0x3A, 0x00, 0x52, 0x00, 0x71, 0x00, 0x96, 0x00,
					 0xC4, 0x00, 0xFC, 0x01, 0x40, 0x01, 0x93, 0x01, 0xF6, 0x02, 0x6E, 0x02, 0xFE, 0x03, 0xAA, 0x04,
					 0x78, 0x05, 0x6C}},
	{"F17Txxxx", {0x00, 0x11, 0x00, 0x00, 0x00, 0x1F, 0x00, 0x34, 0x00, 0x4F, 0x00, 0x71, 0x00, 0x9B, 0x00, 0xCF, 0x01,
					 0x0E, 0x01, 0x5D, 0x01, 0xBB, 0x02, 0x2F, 0x02, 0xB9, 0x03, 0x60, 0x04, 0x29, 0x05, 0x1E, 0x06,
					 0x44, 0x07, 0xA1}},
	{"F18Txxxx", {0x00, 0x11, 0x00, 0x00, 0x00, 0x53, 0x00, 0x8C, 0x00, 0xD5, 0x01, 0x31, 0x01, 0xA2, 0x02, 0x2E, 0x02,
					 0xD8, 0x03, 0xAE, 0x04, 0xAC, 0x05, 0xE5, 0x07, 0x59, 0x09, 0x1C, 0x0B, 0x3B, 0x0D, 0xD0, 0x10,
					 0xEA, 0x14, 0x99}},
	{"F19Txxxx", {0x00, 0x11, 0x00, 0x00, 0x02, 0x8F, 0x03, 0x53, 0x04, 0x5A, 0x05, 0xA1, 0x07, 0xAE, 0x0A, 0x3D, 0x0E,
					 0x14, 0x13, 0x74, 0x1A, 0x5E, 0x24, 0x18, 0x31, 0xA9, 0x44, 0x59, 0x5E, 0x76, 0x83, 0x11, 0xB6,
					 0xC7, 0xFF, 0x7B}},
	{"F24Txxxx", {0x00, 0x11, 0x00, 0x01, 0x00, 0x34, 0x00, 0x52, 0x00, 0x73, 0x00, 0x94, 0x00, 0xBE, 0x00, 0xFA, 0x01,
					 0x36, 0x01, 0x72, 0x01, 0xC5, 0x02, 0x2F, 0x02, 0xB9, 0x03, 0x60, 0x04, 0x1A, 0x05, 0x0A, 0x06,
					 0x0E, 0x07, 0x10}},
};

bool MellowCore::wrapApplePanelSetDisplay(IOService *that, IODisplay *display) {
	static bool once = false;
	if (!once) {
		once = true;
		auto *panels = OSDynamicCast(OSDictionary, that->getProperty("ApplePanels"));
		if (panels) {
			auto *rawPanels = panels->copyCollection();
			panels = OSDynamicCast(OSDictionary, rawPanels);

			if (panels) {
				for (auto &entry : appleBacklightData) {
					auto pd = OSData::withBytes(entry.deviceData, sizeof(entry.deviceData));
					if (pd) {
						panels->setObject(entry.deviceName, pd);
						//! No release required by current AppleBacklight implementation.
					} else {
					}
				}
				that->setProperty("ApplePanels", panels);
			}

			OSSafeReleaseNULL(rawPanels);
		} else {
		}
	}

	bool ret = FunctionCast(wrapApplePanelSetDisplay, callback->orgApplePanelSetDisplay)(that, display);
	return ret;
}
