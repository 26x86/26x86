//! Copyright © 2022-2023 ChefKiss Inc. Licensed under the Thou Shalt Not Profit License version 1.5.
//! See LICENSE for details.

#include "DYLDPatches.hpp"
#include "kern_mellow.hpp"
#include <Headers/kern_api.hpp>
#include <Headers/kern_devinfo.hpp>
#include <IOKit/IODeviceTreeSupport.h>

DYLDPatches *DYLDPatches::callback = nullptr;
void DYLDPatches::init() { callback = this; }

void DYLDPatches::processPatcher(KernelPatcher &patcher) {

    auto *entry = IORegistryEntry::fromPath("/", gIODTPlane);
    if (entry) {
        DBGLOG("DYLD", "Setting hwgva-id to iMacPro1,1");
        entry->setProperty("hwgva-id", const_cast<char *>(kHwGvaId), arrsize(kHwGvaId));
        OSSafeReleaseNULL(entry);
    }

    KernelPatcher::RouteRequest request {"_cs_validate_page", wrapCsValidatePage, this->orgCsValidatePage};

    SYSLOG_COND(!patcher.routeMultipleLong(KernelPatcher::KernelID, &request, 1), "DYLD",
        "Failed to route kernel symbols");
}

void DYLDPatches::wrapCsValidatePage(vnode *vp, memory_object_t pager, memory_object_offset_t page_offset,
    const void *data, int *validated_p, int *tainted_p, int *nx_p) {
    FunctionCast(wrapCsValidatePage, callback->orgCsValidatePage)(vp, pager, page_offset, data, validated_p, tainted_p,
        nx_p);

    char path[PATH_MAX];
    int pathlen = PATH_MAX;
    if (vn_getpath(vp, path, &pathlen) != 0) { return; }

	// One-shot visibility logs for real bundle/image validation events.
	// If these lines appear, the corresponding bundle image was actually seen by cs_validate_page.
	static bool loggedTglMtl = false;
	static bool loggedTglGl = false;
	static bool loggedTglVa = false;
	if (!loggedTglMtl && strstr(path, "AppleIntelTGLGraphicsMTLDriver.bundle")) {
		loggedTglMtl = true;
		SYSLOG("DYLD", "MTL_BUNDLE_SEEN: %s", path);
	}
	if (!loggedTglGl && strstr(path, "AppleIntelTGLGraphicsGLDriver.bundle")) {
		loggedTglGl = true;
		SYSLOG("DYLD", "GL_BUNDLE_SEEN: %s", path);
	}
	if (!loggedTglVa && strstr(path, "AppleIntelTGLGraphicsVADriver.bundle")) {
		loggedTglVa = true;
		SYSLOG("DYLD", "VA_BUNDLE_SEEN: %s", path);
	}

    // These inherited DRM/device-ID patterns were derived from older macOS
    // binaries. They are diagnostic-only and must not run on Tahoe merely
    // because the kernel plugin was allowed to load.
    if (getKernelVersion() != KernelVersion::Sonoma ||
        !checkKernelArgument("-mellowlegacydyld"))
        return;

    if (!UserPatcher::matchSharedCachePath(path)) {
        if (LIKELY(strncmp(path, kCoreLSKDMSEPath, arrsize(kCoreLSKDMSEPath))) &&
            LIKELY(strncmp(path, kCoreLSKDPath, arrsize(kCoreLSKDPath)))) {
            return;
        }
        const DYLDPatch patch = {kCoreLSKDOriginal, kCoreLSKDPatched, "CoreLSKD streaming CPUID to Haswell"};
        patch.apply(const_cast<void *>(data), PAGE_SIZE);
        return;
    }

    if (UNLIKELY(KernelPatcher::findAndReplace(const_cast<void *>(data), PAGE_SIZE, kVideoToolboxDRMModelOriginal,
            arrsize(kVideoToolboxDRMModelOriginal), BaseDeviceInfo::get().modelIdentifier, 20))) {
        DBGLOG("DYLD", "Applied 'VideoToolbox DRM model check' patch");
    }

    const DYLDPatch patches[] = {
        {kAGVABoardIdOriginal, kAGVABoardIdPatched, "iMacPro1,1 spoof (AppleGVA)"},
		{kHEVCEncBoardIdOriginal, kHEVCEncBoardIdPatched, "iMacPro1,1 spoof (AppleGVAHEVCEncoder)"},
    };
    DYLDPatch::applyAll(patches, const_cast<void *>(data), PAGE_SIZE);
	
	// ── V50: GPU bundle search path redirect ──
	// Metal calls gpu_bundle_find_trusted() in libsystem_sandbox.dylib to locate
	// GPU plugin bundles. This function searches exactly two directories:
	//   1. /Library/GPUBundles      (checked first)
	//   2. /System/Library/Extensions  (checked second)
	// using format "%s/%s.bundle" to construct paths.
	//
	// Apple never made a Mac with Tiger Lake — no TGL Metal driver exists in either
	// of those directories. The TGL driver is at /Library/Extensions/ (user-installed).
	//
	// Fix: patch the first search path in libsystem_sandbox's __cstring:
	//   "/Library/GPUBundles\0"  (20 bytes) → "/Library/Extensions\0" (20 bytes)
	// This makes gpu_bundle_find_trusted search /Library/Extensions/ first,
	// where the TGL driver bundle actually exists.
	// /System/Library/Extensions stays as the fallback for system GPU bundles.
	//
	// Alternative: manually copy the TGL bundle:
	//   sudo mkdir -p /Library/GPUBundles
	//   sudo cp -R /Library/Extensions/AppleIntelTGLGraphicsMTLDriver.bundle /Library/GPUBundles/
	static const uint8_t gpuPathFind[] = {
		0x2F, 0x4C, 0x69, 0x62, 0x72, 0x61, 0x72, 0x79, // /Library
		0x2F, 0x47, 0x50, 0x55, 0x42, 0x75, 0x6E, 0x64, // /GPUBund
		0x6C, 0x65, 0x73, 0x00,                           // les\0
	};
	static const uint8_t gpuPathRepl[] = {
		0x2F, 0x4C, 0x69, 0x62, 0x72, 0x61, 0x72, 0x79, // /Library
		0x2F, 0x45, 0x78, 0x74, 0x65, 0x6E, 0x73, 0x69, // /Extensi
		0x6F, 0x6E, 0x73, 0x00,                           // ons\0
	};

	/* Sandbox: WindowServer deny(1) file-map-executable 
	/Library/Extensions/AppleIntelTGLGraphicsMTLDriver.bundle — 
	Sandbox blocks WS from mapping the Metal driver as executable. 
	That's a secondary issue (separate from the kernel-side getBlit3DContext).

	if (UNLIKELY(KernelPatcher::findAndReplace(const_cast<void *>(data), PAGE_SIZE,
			gpuPathFind, arrsize(gpuPathFind), gpuPathRepl, arrsize(gpuPathRepl)))) {
		SYSLOG("DYLD", "V50: Patched gpu_bundle_find_trusted: /Library/GPUBundles -> /Library/Extensions");
	}*/
	
	// V50: ICL Metal driver device-ID bypass (mask-based, build-portable).
	// The ICL driver (in shared cache) checks device_id:vendor_id against
	// 0x8A5C8086/0x8A5D8086, then calls a hw-cap fallback check.
	// Patch: change jne to jmp so the hw-cap check always succeeds.
	// This is a fallback — if the TGL driver loads, this won't be needed.
	static const uint8_t f2find[] = {
		0x81, 0xFF, 0x86, 0x80, 0x5C, 0x8A,  // cmp edi, 0x8A5C8086
		0x74, 0x00,                            // je +XX (wildcard offset)
		0x81, 0xFF, 0x86, 0x80, 0x5D, 0x8A,  // cmp edi, 0x8A5D8086
		0x74, 0x00,                            // je +XX (wildcard offset)
		0xE8, 0x00, 0x00, 0x00, 0x00,         // call +XXXX (wildcard offset)
		0x84, 0xC0,                            // test al, al
		0x75, 0x00,                            // jne +XX → change to EB (jmp)
	};
	static const uint8_t f2mask[] = {
		0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,   // cmp exact
		0xFF, 0x00,                            // je opcode exact, offset wildcard
		0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,   // cmp exact
		0xFF, 0x00,                            // je opcode exact, offset wildcard
		0xFF, 0x00, 0x00, 0x00, 0x00,         // call opcode exact, offset wildcard
		0xFF, 0xFF,                            // test exact
		0xFF, 0x00,                            // jne opcode exact, offset wildcard
	};
	static const uint8_t f2repl[] = {
		0x81, 0xFF, 0x86, 0x80, 0x5C, 0x8A,  // unchanged
		0x74, 0x00,                            // unchanged
		0x81, 0xFF, 0x86, 0x80, 0x5D, 0x8A,  // unchanged
		0x74, 0x00,                            // unchanged
		0xE8, 0x00, 0x00, 0x00, 0x00,         // unchanged
		0x84, 0xC0,                            // unchanged
		0xEB, 0x00,                            // jne→jmp (0x75→0xEB)
	};
	static const uint8_t f2rmask[] = {
		0x00, 0x00, 0x00, 0x00, 0x00, 0x00,   // don't touch
		0x00, 0x00,                            // don't touch
		0x00, 0x00, 0x00, 0x00, 0x00, 0x00,   // don't touch
		0x00, 0x00,                            // don't touch
		0x00, 0x00, 0x00, 0x00, 0x00,         // don't touch
		0x00, 0x00,                            // don't touch
		0xFF, 0x00,                            // CHANGE byte 23 only (0x75→0xEB)
	};
	if (UNLIKELY(KernelPatcher::findAndReplaceWithMask(const_cast<void *>(data), PAGE_SIZE,
			f2find, f2mask, f2repl, f2rmask, 1, 0))) {
		SYSLOG("DYLD", "V50: Applied ICL Metal device-ID bypass (f2, mask-based)");
	}
	
    // CoreDisplay GetMTLTexture/GetMTLCommandQueue/AccessComplete bypasses
    // intentionally removed. Returning NULL, stubbing AccessComplete, or
    // jumping to its signal block cannot supply GPU work or a valid fence.
    // Preserve the system implementation and diagnose the real backend error.
}
