# BP32 recursive integration

Fresh committed parentdf60198b passes41 recorded commands:476 workspace tests,
149 Python/25 GUI suite cases (one skip in each),98 reference tests,39 service
tests,186 actual x86 EFI executions and6 separate CLI rejections. Native v2
execution/semantic negatives,158 prior captured Arm comparisons,3668 conditional
Arm cases,119 Vulkan tests, source ownership, firmware packaging and Clippy
complete. Clippy warnings remain visible in logs; no zero-warning claim is made.

The newly built integrated NXMMU executes108 cases, separate from the prior78
EFI regressions. Strict conditional checks require actual Rust fetch callbacks.
A fresh replay against this clone separately checks322 data/32 recorded completion
fetch cases,74 exact BTYPE rejects and78 ERET target-fetch cases. Completion
snapshots are not original target-fetch PSTATE proof. The independent capture
overlay and known12 QEMU PC-priority failures remain in their historical bundles.

The final EFI pinf3f7938 differs from tested8d53dd2 only in reproduction docs and
file metadata; source/build/CI are unchanged. Its own final CI passes, the module
PR is merged, and parent package/inventory/reader checks verify the final pin.
The final parent evidence commit receives a separate canonical recursive network
checkout and final-head CI before its PR merges. Those results cannot identify
this commit inside itself and are retained in publication logs and GitHub checks.

Standalone EFI builds use an initially empty Cargo cache and canonical Git
dependencies, without parent patches. The full root baseline uses a fresh local
recursive committed clone with temporary source URL mapping; it does not replace
the final canonical network gate. Historical WIP, standalone and root binaries
have separate hashes. Only authored inputs occur in these tests.

Normal macOS27 startup, general dynamic translation/exception handling, desktop
use and guest Metal remain incomplete. The new explicit stage1 profile keeps
Normal-NC/A=1 controls and table backing immutable. Core runtime-DT/owned ledger
and dynamic enable work remain outside these module pins.
