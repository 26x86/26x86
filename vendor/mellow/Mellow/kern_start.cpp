//  Copyright © 2026 Stezza @ inc. Licensed under the Thou Shalt Not Profit License version 1.0. See LICENSE for
//  details.

#include "kern_mellow.hpp"
#include "StartupPolicy.hpp"
#include "RuntimeReadiness.hpp"
#include <Headers/kern_api.hpp>
#include <Headers/plugin_start.hpp>

static MellowCore mellowPlugin;

static const char *bootargDebug = "-MellowDebug";


PluginConfiguration ADDPR(config) {
    xStringify(PRODUCT_NAME),
    parseModuleVersion(xStringify(MODULE_VERSION)),
    LiluAPI::AllowNormal | LiluAPI::AllowInstallerRecovery | LiluAPI::AllowSafeMode,
	nullptr,
	0,
	&bootargDebug,
	1,
	nullptr,
	0,
	KernelVersion::Ventura,
	KernelVersion::Tahoe,
	[]() {
		if (checkKernelArgument("-mellowdiag")) {
			SYSLOG("mellow", "diagnostic IOService selected; legacy Apple graphics patch callbacks are not registered");
			return;
		}
		const bool tahoeTrial = checkKernelArgument("-mellowtahoe");
		const bool vesa = checkKernelArgument("-igfxvesa");
		const bool nativeBackendRequested = checkKernelArgument("-mellownativexe");
		uint64_t evidence = 0;
		if (tahoeTrial) evidence |= MellowRuntime::BootOptIn;
		if (!vesa) evidence |= MellowRuntime::VesaDisabled;
		const auto readiness = MellowRuntime::evaluate(evidence);
		const auto admission = MellowStartup::evaluate(static_cast<unsigned>(getKernelVersion()),
			tahoeTrial, vesa, nativeBackendRequested, MellowRuntime::BackendOwnerIntegrated);
		if (admission != MellowStartup::Admission::ResearchTrial) {
			const auto missing = MellowRuntime::firstMissing(readiness.missing);
			SYSLOG("mellow", "driver callbacks not registered: admission=%u native-xe-stage=%s first-missing=%s verified=0x%llx native-requested=%d",
				static_cast<unsigned>(admission), MellowRuntime::stageName(readiness.stage),
				MellowRuntime::evidenceName(missing), static_cast<unsigned long long>(evidence),
				nativeBackendRequested);
			return;
		}
		SYSLOG("mellow", "legacy Apple-driver research entry admitted, Darwin=%u; native-xe-stage=%s first-missing=%s; hardware execution and Metal support UNVERIFIED",
			static_cast<unsigned>(getKernelVersion()), MellowRuntime::stageName(readiness.stage),
			MellowRuntime::evidenceName(MellowRuntime::firstMissing(readiness.missing)));
		mellowPlugin.init();
	},
};

// LILU_CUSTOM_IOKIT_INIT=1
/*
 OSDefineMetaClassAndStructors(PRODUCT_NAME, IOService);

 IOService *PRODUCT_NAME::probe(IOService *provider, SInt32 *score) {
	 setProperty("VersionInfo", kextVersion);
	 auto service = IOService::probe(provider, score);
	 return ADDPR(startSuccess) ? service : nullptr;
 }

 bool PRODUCT_NAME::start(IOService *provider) {
	 if (!IOService::start(provider)) {
		 SYSLOG("init", "Failed to start the parent");
		 return false;
	 }

	 if (!(lilu.getRunMode() & LiluAPI::RunningInstallerRecovery) && ADDPR(startSuccess)) {
		 auto *prop = OSDynamicCast(OSArray, this->getProperty("Drivers"));
		 if (!prop) {
			 SYSLOG("init", "Failed to get Drivers property");
			 return false;
		 }
		 auto *propCopy = prop->copyCollection();
		 if (!propCopy) {
			 SYSLOG("init", "Failed to copy Drivers property");
			 return false;
		 }
		 auto *drivers = OSDynamicCast(OSArray, propCopy);
		 if (!drivers) {
			 SYSLOG("init", "Failed to cast Drivers property");
			 OSSafeReleaseNULL(propCopy);
			 return false;
		 }
		 if (!gIOCatalogue->addDrivers(drivers)) {
			 SYSLOG("init", "Failed to add drivers");
			 OSSafeReleaseNULL(drivers);
			 return false;
		 }
		 OSSafeReleaseNULL(drivers);
	 }

	 return ADDPR(startSuccess);
 }*/
