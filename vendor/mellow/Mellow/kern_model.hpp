//  Copyright © 2022-2023 ChefKiss Inc. Licensed under the Thou Shalt Not Profit License version 1.0. See LICENSE for
//  details.

#ifndef kern_model_hpp
#define kern_model_hpp

#include <stdint.h>

struct UltraDevice {
	uint16_t deviceId {0};
	const char *name {nullptr};
	uint8_t compatSubSliceCount {0};
};

// Core Ultra Xe-LPG IDs. The set is intentionally limited to IDs documented
// by Intel's i915 hardware table; recognition here does not imply native macOS
// support. compatSubSliceCount is the maximum-EU TGL compatibility topology,
// not a claim that fuse-disabled variants expose every listed EU.
static constexpr UltraDevice ultraDevices[] = {
	{0x7D40, "Intel Graphics (Meteor Lake)", 8},
	{0x7D45, "Intel Graphics (Meteor Lake)", 8},
	{0x7D55, "Intel Arc Graphics (Meteor Lake)", 16},
	{0x7DD5, "Intel Graphics (Meteor Lake)", 16},
	{0x7D41, "Intel Graphics 4-Core (Arrow Lake-U)", 8},
	{0x7D51, "Intel Graphics (Arrow Lake-H)", 16},
	{0x7D67, "Intel Graphics (Arrow Lake-S)", 8},
};

inline const UltraDevice *findUltraDevice(uint16_t deviceId) {
	for (auto &device : ultraDevices) {
		if (device.deviceId == deviceId) {
			return &device;
		}
	}

	return nullptr;
}

inline bool isSupportedUltraDevice(uint16_t deviceId) {
	return findUltraDevice(deviceId) != nullptr;
}

// Bind each graphics tile family to its matching Core Ultra CPU family. This
// avoids activating Mellow for an arbitrary 7Dxx spoof on an unrelated CPU.
inline bool isSupportedUltraPair(uint32_t cpuModel, uint16_t deviceId) {
	switch (cpuModel) {
		case 0xAA: // Meteor Lake-L
		case 0xAC: // Meteor Lake
			return deviceId == 0x7D40 || deviceId == 0x7D45 ||
			       deviceId == 0x7D55 || deviceId == 0x7DD5;
		case 0xB5: // Arrow Lake-U
			return deviceId == 0x7D41;
		case 0xC5: // Arrow Lake-H
			return deviceId == 0x7D51;
		case 0xC6: // Arrow Lake-S
			return deviceId == 0x7D67;
		default:
			return false;
	}
}

inline const char *getBranding(uint16_t deviceId) {
	auto *device = findUltraDevice(deviceId);
	return device ? device->name : "Unsupported Intel Graphics";
}

inline uint8_t getUltraCompatSubSliceCount(uint16_t deviceId) {
	auto *device = findUltraDevice(deviceId);
	return device ? device->compatSubSliceCount : 0;
}

#endif /* kern_model_hpp */
