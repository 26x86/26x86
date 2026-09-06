> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# Mellow 0.4.1 build validation

The actual Xcode target's 30 C++ translation units were cross compiled
and linked with Apple ld64 (cctools-port), preserving MH_KEXT_BUNDLE and kernel relocations.
All 1334 build input hashes still match the final source tree.

- Bundle: `build/Release/Mellow.kext`, version 0.4.1.
- Binary: 449448 bytes; SHA256 `cee0482b2d858856c0696e0d8d6f18e6e12f87bb81bb0a0e1330984e1329eb36`.
- Structural validator: passed. This is a real linked research kext, not a probe placeholder.
- Tahoe Recovery 26.6.2 / 25G83 and Lilu 1.7.2: 378/378 imports statically eligible.
- The kernel linker, kext attach, private C++/Metal ABI, GuC authentication,
  physical GPU commands and Metal compute/render have NOT been executed on this Galaxy Book.

The cross-build report is in `build/Release/cross-build-report.json`; the matching
provider/export report is in `abi-evidence/tahoe-import-resolution.json`.
The older 0.4.0 host-suite reports describe their recorded source hashes and are historical.
0.4.1 adds native-backend readiness diagnostics and client acceptance checks;
see [current acceptance procedure](ACCEPTANCE-0.4.1.ko.md) and
[backend audit](NATIVE-XE-BACKEND-AUDIT.md).

The active USB profile keeps the legacy TGL research trial enabled. It does not
construct the missing native Xe backend. The new `-mellownativexe` path rejects
startup while its provider owner is absent. No success is inferred from boot arguments.
Native CI, if passed, is compiler/host evidence only and is documented separately.
