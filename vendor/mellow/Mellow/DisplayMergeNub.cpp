/*
 * Copyright � 1998-2012 Apple Inc.  All rights reserved.
 * 
 * @APPLE_LICENSE_HEADER_START@
 * 
 * This file contains Original Code and/or Modifications of Original Code
 * as defined in and that are subject to the Apple Public Source License
 * Version 2.0 (the 'License'). You may not use this file except in
 * compliance with the License. Please obtain a copy of the License at
 * http://www.opensource.apple.com/apsl/ and read it before using this
 * file.
 * 
 * The Original Code and all software distributed under the License are
 * distributed on an 'AS IS' basis, WITHOUT WARRANTY OF ANY KIND, EITHER
 * EXPRESS OR IMPLIED, AND APPLE HEREBY DISCLAIMS ALL SUCH WARRANTIES,
 * INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE, QUIET ENJOYMENT OR NON-INFRINGEMENT.
 * Please see the License for the specific language governing rights and
 * limitations under the License.
 * 
 * @APPLE_LICENSE_HEADER_END@
 */


#include <IOKit/IOKitKeys.h>
#include <IOKit/IOLib.h>

#include "DisplayMergeNub.h"
#include "kern_mellow.hpp"
#include <Headers/kern_api.hpp>
//#include "KextVer.h"
OSDefineMetaClassAndStructors(DisplayMergeNub, IOService)

static bool haveCreatedRef = false;

bool
DisplayMergeNub::start(IOService *provider)
{
    return IOService::start(provider);
}

//================================================================================================
//
//  probe()
//
//  This is a special Display driver which will always fail to probe. However, the probe
//  will have a side effect, which is that it merge a property dictionary into his provider's
//  parent NUB in the IOService if the device and vendor match
//
//================================================================================================
//
IOService *
DisplayMergeNub::probe(IOService *provider, SInt32 *score)
{
#pragma unused (score)
    // IOKit personalities may probe independently of the Lilu startup callback.
    // Do not let the optional panel merge bypass physical hardware admission.
    if (!provider || !checkKernelArgument("-mellowdisplaymerge") ||
        !MellowCore::callback || !MellowCore::callback->isHardwareAdmitted())
        return nullptr;

    auto *providerDict = OSDynamicCast(OSDictionary, getProperty("IOProviderMergeProperties"));
    auto *providerVendor = OSDynamicCast(OSNumber, provider->getProperty("DisplayVendorID"));
    auto *providerDevice = OSDynamicCast(OSNumber, provider->getProperty("DisplayProductID"));
    auto *vendorValue = OSDynamicCast(OSNumber, getProperty("DisplayVendorID"));
    auto *deviceValue = OSDynamicCast(OSNumber, getProperty("DisplayProductID"));
    if (!providerDict || !providerVendor || !providerDevice || !vendorValue || !deviceValue)
        return nullptr;
    if (providerVendor->unsigned64BitValue() != vendorValue->unsigned64BitValue() ||
        providerDevice->unsigned64BitValue() != deviceValue->unsigned64BitValue())
        return nullptr;

    auto *displayOverrideClass = OSDynamicCast(OSString, providerDict->getObject("IOClass"));
    if (MergeDictionaryIntoProvider(provider, providerDict) && displayOverrideClass)
        provider->setName(displayOverrideClass->getCStringNoCopy());
    // Property merging never claims ownership of the display or proves rendering.
    return nullptr;
}

//================================================================================================
//
//  MergeDictionaryIntoProvider
//
//  We will iterate through the dictionary that we want to merge into our provider.  If
//  the dictionary entry is not an OSDictionary, we will set that property into our provider.  If it is a
//  OSDictionary, we will get our provider's entry and merge our entry into it, recursively.
//
//================================================================================================
//
bool
DisplayMergeNub::MergeDictionaryIntoProvider(IOService *provider, OSDictionary *dictionaryToMerge)
{
    if (!provider || !dictionaryToMerge)
        return false;
    auto *iter = OSCollectionIterator::withCollection(dictionaryToMerge);
    if (!iter)
        return false;

    // Preserve the original lifetime requirement for the property merge nub.
    if (!haveCreatedRef) {
        haveCreatedRef = true;
        getMetaClass()->instanceConstructed();
    }
    bool result = true;
    while (auto *entry = iter->getNextObject()) {
        auto *key = OSDynamicCast(OSSymbol, entry);
        if (!key) { result = false; break; }
        auto *source = OSDynamicCast(OSDictionary, dictionaryToMerge->getObject(key));
        auto *target = OSDynamicCast(OSDictionary, provider->getProperty(key));
        if (source && target) {
            auto *copy = OSDictionary::withDictionary(target, 0);
            if (!copy) { result = false; break; }
            result = MergeDictionaryIntoDictionary(source, copy);
            if (result)
                result = provider->setProperty(key, copy);
            // setProperty retains its own reference; release ours on all paths.
            copy->release();
        } else {
            result = provider->setProperty(key, dictionaryToMerge->getObject(key));
        }
        if (!result)
            break;
    }
    iter->release();
    return result;
}

bool
DisplayMergeNub::MergeDictionaryIntoDictionary(OSDictionary *source, OSDictionary *target)
{
    if (!source || !target)
        return false;
    auto *iter = OSCollectionIterator::withCollection(source);
    if (!iter)
        return false;
    bool result = true;
    while (auto *entry = iter->getNextObject()) {
        auto *key = OSDynamicCast(OSSymbol, entry);
        if (!key) { result = false; break; }
        auto *childSource = OSDynamicCast(OSDictionary, source->getObject(key));
        auto *childTarget = OSDynamicCast(OSDictionary, target->getObject(key));
        if (childSource && childTarget) {
            auto *copy = OSDictionary::withDictionary(childTarget, 0);
            if (!copy) { result = false; break; }
            result = MergeDictionaryIntoDictionary(childSource, copy);
            if (result)
                result = target->setObject(key, copy);
            copy->release();
        } else {
            result = target->setObject(key, source->getObject(key));
        }
        if (!result)
            break;
    }
    iter->release();
    return result;
}
