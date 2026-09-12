# Safari on CPUs without required instruction features

**Current Status:** Build-specific crash diagnosis; a universal instruction workaround is not verified.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

This page is a diagnostic guide, not a verified fix for every Safari release.
Earlier text described a specific Safari version and automatic AVX-to-SSE
translation without an accompanying source-bound runtime receipt. Those claims
must not be used as the current support contract.

1. Record the actual CPU features, macOS build, Safari/WebKit build and crash log.
2. Confirm an illegal-instruction exception and identify its instruction family;
   a browser crash alone does not establish an AVX fault.
3. Record the exact loaded RestrictEvents version and boot arguments. Consult
   its public source/documentation before assigning behavior to `revpatch=jsc`.
4. Reproduce the same workload after an approved, reversible change and verify
   that the original failure is absent. Check more than application launch.

No blanket AVX translation, root-patch-free cure or cross-version compatibility
is established here. See [CPU capability notes](Pre-AVX-Mac-Pro.md),
[known issues](Known-Issues.md) and [compatibility](../compatibility.md).
