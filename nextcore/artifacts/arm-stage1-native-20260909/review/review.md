# BP32 independent native stage-1 review

Scope: current WIP source under `/home/sharh/work/bp32-ise-native-mmu`, reviewed without editing production files. Narrow authored Linux x86 probes only; no OVMF, original macOS assets, metadata, Git operations or source claims based on boot success. Per-probe hashes identify changing source revisions.

## Confirmed defects

1. **Origin-dependent cached write permission.** The newly permitted EL0 fetch of an AP00/UXN0 leaf cached `writable=false`. A subsequent EL1 write failed with cached Permission while a fresh walk succeeded. `cross-el-cache-reproduction.json` demonstrates both legacy and strict profiles on 4 KiB. CPU owner changed the cache to retain descriptor-global write capability and compute effective permissions per access. Independent `cross-el-cache-corrected.json` now matches cold/hot successful PA32776 writes in both modes. This is separate from root's EL2/EL3 implicit-XN review.

2. **Malformed callback fault combinations accepted as guest exceptions.** `malformed-reply-reproduction.json` calls actual `memory_exchange_v2` and `vf_cpu_raise_exception` with four authored replies: misaligned instruction address plus Translation L3; A=1 misaligned load plus Translation L3; AddressSize/CachedLeaf level0 without output metadata; Translation with Leaf context. All were accepted with provider status zero and committed ESR (86000007, 96000007, 96000000, 96000007). These conflict with the supported alignment priority and canonical context/level rules. CPU owner has exact reproductions; independent post-fix rerun is pending.

Architectural expectations for alignment priority and AP permissions are from Arm-authored DDI0487B.a, sections D1.13.3, D4.7.3 and Table D4-34. Public primary document mirror: https://cs140e.sergio.bz/docs/ARMv8-Reference-Manual.pdf . Source identification and independent actual AArch64 observations are in the separately frozen BP32 stage1 oracle bundle; that bundle is unchanged by this review.

## Verified callback trust limit

`store-boundary/receipt.json` compiles the actual canonical Rust service and native C dispatcher. Only after successful STORE does an external test callback corrupt the reply epoch. The dispatcher correctly rejects the reply: status4/provider3, zero retired/completed instructions. However RAM already contains42, replacing eight a5 bytes. The synchronous callback performs the store before C reply validation, so C has no rollback mechanism for broken/malicious callbacks. CPU owner agreed to document this limit explicitly. Whole-span failure atomicity applies to canonical service preflight failures; it is not a guarantee against callback-side effects before a malformed response or transport failure. No replacement ABI is proposed here.

## Reviewed without another confirmed defect

- Supported scalar/pair families are intercepted before physical native emitters. Unsupported SIMD/reserved encodings stop at the shared memory decoder; generated entries receive no RAM pointer. Fetch always uses the v2 service.
- Canonical service checks every byte's translation/backing before copying any load/store data; discontiguous physical pair mappings use distinct offsets. Immutable table backing is separate from writable RAM in both host and physical spans. Callback owner/slices must obey the documented lifetime and nonaliasing safety contract.
- Controls are copied, compared each request, and cannot be changed by the supported immutable-profile instructions. TLB invalidation on configuration prevents legacy attribute metadata from leaking into strict mode. Unknown attributes/hierarchical bits are rejected in the one canonical walker.
- Controls/request/reply/result use fixed integer C/Rust records. Read-only review does not substitute for the CPU owner's actual ABI/native test suite or future Win64 EFI proof.

Production source remained WIP during this review. This is a bounded review, not a proof of arbitrary callback safety, dynamic MMU controls, handler execution, original macOS boot, Metal or usable OS startup.
