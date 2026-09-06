# Mellow diagnostic root-patch payload

Pinned Mellow 0.4.3 x86_64 development kext. Required boot argument: `-mellowdiag`.
This selects PCI/IOUserClient diagnostics; native GPU submission, Metal and WindowServer acceleration are not provided by this payload.

26x86 installs this through its existing data-volume root-patch transaction at `/Library/Extensions/Mellow.kext`, with Lilu available separately. Do not also inject the same Mellow bundle from OpenCore. Apple Silicon Sandbox Mode rejects this native package.

`manifest.json` inventories every file except itself. `provenance.json` retains all cross-build input hashes, matched against the pinned source. Full unchanged source and upstream build documentation are in `vendor/mellow`; `vendor/mellow-source.json` inventories that snapshot. No Apple graphics system binaries or firmware are bundled. Root-patch copying is not evidence of kernel loading or GPU acceleration.

Existing `LICENSE`, `NOTICE`, `LICENSES` and individual source notices remain controlling. The combined kext is not relicensed under the application license. Future user-driver/runtime categories require real reviewed Mach-O payloads and cannot be claimed by this release.
