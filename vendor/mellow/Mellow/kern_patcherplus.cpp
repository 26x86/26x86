//! Copyright © 2022-2023 ChefKiss Inc. Licensed under the Thou Shalt Not Profit License version 1.5.
//! See LICENSE for details.

#include "kern_patcherplus.hpp"
#include "PatternMatch.hpp"

bool SolveRequestPlus::solve(KernelPatcher &patcher, size_t id, mach_vm_address_t address, size_t maxSize) {
	if(!this->address) return false;
	//PANIC_COND(!this->address, "Patcher+", "this->address is null");

	*this->address = patcher.solveSymbol(id, this->symbol);
	if (*this->address) { return true; }
	patcher.clearError();

	if (!this->pattern || !this->patternSize) {
		DBGLOG("Patcher+", "Failed to solve %s using symbol", safeString(this->symbol));
		return false;
	}

	if (!MellowPattern::validAddressRange(address, maxSize)) return false;
	const auto match = MellowPattern::findUnique(reinterpret_cast<const UInt8 *>(address),
		maxSize, this->pattern, this->mask, this->patternSize);
	if (match.status != MellowPattern::Status::Unique) {
		SYSLOG("Patcher+", "Refusing missing, invalid or ambiguous pattern for %s (%u)",
			safeString(this->symbol), static_cast<unsigned>(match.status));
		return false;
	}

	*this->address = address + match.offset;
	return true;
}

bool SolveRequestPlus::solveAll(KernelPatcher &patcher, size_t id, SolveRequestPlus *requests, size_t count,
	mach_vm_address_t address, size_t maxSize) {
	for (size_t i = 0; i < count; i++) {
		if (!requests[i].solve(patcher, id, address, maxSize)) { return false; }
	}
	return true;
}

bool RouteRequestPlus::route(KernelPatcher &patcher, size_t id, mach_vm_address_t address, size_t maxSize) {
	if (patcher.routeMultiple(id, this, 1, address, maxSize)) { return true; }
	patcher.clearError();

	if (!this->pattern || !this->patternSize) {
		DBGLOG("Patcher+", "Failed to route %s using symbol", safeString(this->symbol));
		return false;
	}

	if (!MellowPattern::validAddressRange(address, maxSize)) return false;
	const auto match = MellowPattern::findUnique(reinterpret_cast<const UInt8 *>(address),
		maxSize, this->pattern, this->mask, this->patternSize);
	if (match.status != MellowPattern::Status::Unique) {
		SYSLOG("Patcher+", "Refusing missing, invalid or ambiguous route pattern for %s (%u)",
			safeString(this->symbol), static_cast<unsigned>(match.status));
		return false;
	}

	auto org = patcher.routeFunction(address + match.offset, this->to, true);
	if (!org) {
		DBGLOG("Patcher+", "Failed to route %s using pattern: %d", safeString(this->symbol), patcher.getError());
		return false;
	}
	if (this->org) { *this->org = org; }

	return true;
}

bool RouteRequestPlus::routeAll(KernelPatcher &patcher, size_t id, RouteRequestPlus *requests, size_t count,
	mach_vm_address_t address, size_t maxSize) {
	for (size_t i = 0; i < count; i++) {
		if (!requests[i].route(patcher, id, address, maxSize)) { return false; }
	}
	return true;
}

bool LookupPatchPlus::apply(KernelPatcher &patcher, mach_vm_address_t address, size_t maxSize) const {
	if (!this->findMask && !this->replaceMask && !this->skip) {
		patcher.applyLookupPatch(this, reinterpret_cast<UInt8 *>(address), maxSize);
		return patcher.getError() == KernelPatcher::Error::NoError;
	}
	return KernelPatcher::findAndReplaceWithMask(reinterpret_cast<UInt8 *>(address), maxSize, this->find, this->size,
		this->findMask, this->findMask ? this->size : 0, this->replace, this->size, this->replaceMask,
		this->replaceMask ? this->size : 0, this->count, this->skip);
}

bool LookupPatchPlus::applyAll(KernelPatcher &patcher, const LookupPatchPlus *patches, size_t count,
	mach_vm_address_t address, size_t maxSize) {
	for (size_t i = 0; i < count; i++) {
		if (patches[i].apply(patcher, address, maxSize)) {
			DBGLOG("Patcher+", "Applied patches[%zu]", i);
		} else {
			DBGLOG("Patcher+", "Failed to apply patches[%zu]", i);
			return false;
		}
	}
	return true;
}
