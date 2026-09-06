> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# Local startup, pattern routing and display probe changes

This is a development derivative of Mellow f895d89653ea5cad3a534cce46a62d0f59384d71, version 0.1.1. A driver entry, kext build or matched device does not establish Metal support.

The Lilu registration now admits Darwin 25 to an explicitly selected research path. `-mellowtahoe` is required on Darwin 25; `-igfxvesa` conflicts with this path and prevents registration of the driver callbacks. Darwin versions outside 22–25 are rejected even if the experiment argument is present. `StartupPolicy.hpp` is used by the actual plugin entry, not merely by the tests. The admission log explicitly records unverified hardware/Metal execution. This changes the version gate; it does not prove compatibility of external TGL binaries or their private ABI.

The inherited `SolveRequestPlus` and `RouteRequestPlus` fallback rejected a legitimate signature at image offset zero (`!offset`), accepted the first match even if multiple functions had the same byte pattern, and did not validate the supplied virtual-address extent. `PatternMatch.hpp` now accepts offset zero, requires exactly one match, rejects unconstrained masks and address overflow, and treats a missing/ambiguous pattern as failure. The symbol resolution path remains preferred. The caller still must supply a readable mapped image; integer bounds checking does not establish virtual memory mapping. A unique pattern does not prove that the surrounding function ABI is compatible.

`DisplayMergeNub` is an IOKit personality and can probe independently of the Lilu plugin's startup callback. Its probe formerly cast and dereferenced missing or wrongly typed properties before checking them. The new path requires `-mellowdisplaymerge` plus an admitted physical device in `MellowCore`, checks each dictionary/number/string type, and forwards normal IOService start results. It does not claim display ownership or rendering success. The panel override remains optional and untested.

The recursive display merge helpers now reject iterator/copy allocation failures and release copied dictionaries after the receiving collection has retained them, including failed-merge and failed-set paths. Empty valid dictionaries are treated as successful empty merges. This is source reviewed and whole-target compiled; no IOKit runtime test was performed.

The native `patcher_policy_tests.cpp` exercises offset-zero and final-span matches, overlapping/duplicate signatures, masked matching, all-wildcard rejection, empty/null inputs, address overflow and the Darwin admission matrix. Its 4096-case byte/mask sweep uses independently counted expected matches. These tests run on the preparation host; they do not call GPU registers or verify macOS loading.

Source references: [Lilu KernelPatcher API](https://github.com/acidanthera/Lilu/blob/master/Lilu/Headers/kern_patcher.hpp), vendored Lilu `Headers/kern_util.hpp` for Darwin/Tahoe values, and the original Mellow source preserved in the prior research archive. New helper headers are found through the existing source-directory include path and do not add translation units to the Xcode project.
