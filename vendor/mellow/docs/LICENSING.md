# Licensing intake review — draft

> [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md) and [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md)
> take precedence. [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) records current tool behavior.
> LICENSE/NOTICE and original per-file terms remain in force; this document does not relicense code.

## 한글 요약

기존 LICENSE·NOTICE와 수입 파일의 조건을 보존한다. 신규 구성 요소의 BSD/MIT 선택은
권리와 의존성을 검토한 뒤 결정할 제안이며 현재 파일을 재라이선스하지 않는다.
디렉터리의 이름이나 SPDX 한 줄은 전체 dependency closure의 결합·배포 허가가 아니다.
firmware는 현재 프로젝트 정책상 fetch-and-verify로 다루며, 각 vendor의 이용·재배포·특허
조건은 원문과 정확한 조합을 기준으로 검토한다. missing SPDX는 review gap이며 inspect는
보고서를 만들 수 있지만 해당 파일의 generation은 승인하지 않는다.

---

This is a design proposal for intake review, not a legal compatibility ruling or a license grant.
Current code behavior is authoritative only for its documented analysis/generation checks.

## Current state

| Component | License | Notes |
| --- | --- | --- |
| Mellow proper | **Thou Shalt Not Profit License 1.0** ([LICENSE](../LICENSE)) | Non-OSI. §1(c) is copyleft-style; §5 treats network use as distribution; §9 terminates on failure to honor §1(c) |
| Lilu bundle | BSD-3-Clause ([LICENSES/Lilu-BSD-3-Clause.txt](../LICENSES/Lilu-BSD-3-Clause.txt)) | Copyright vit9696 and contributors |
| MacKernelSDK headers, `DisplayMergeNub` | APSL-2.0 ([LICENSES/APSL-2.0.txt](../LICENSES/APSL-2.0.txt)) | Per [NOTICE](../NOTICE), **not relicensed under TSNPL** |
| `tests/xe_dispatch_intel_reference.inl` | MIT ([tests/xe_dispatch_intel_LICENSE.md](../tests/xe_dispatch_intel_LICENSE.md)) | 311,810 bytes, byte-identical to Intel compute-runtime upstream; a host-test oracle, **not linked into the kext** |

Mellow is a derivative of ChefKiss NootedGreen and the NootedGreen-UHD730 line; see
[NOTICE](../NOTICE) for the full attribution chain.

### Known defect

`DYLDPatches.*` and `kern_patcherplus.*` carry headers claiming **TSNPL 1.5** while the repository
ships **1.0** ([NOTICE](../NOTICE)). This is recorded here so it is fixed deliberately rather than
propagated.

## The problem the re-architecture creates

The current TSNPL text imposes conditions that require review when combining imported code.
GPL-only, dual-licensed and permissive files must be assessed with their actual dependencies and
linkage; directory isolation or an author-written header does not by itself establish compatibility.
Firmware copyright grants and patent grants are separate terms. Do not derive a categorical
permission or prohibition for all vendor blobs from one Intel license or from the OS name.

## Proposal: review future component licenses before implementation

The following is a candidate license plan, not an effective change. New files remain under their
applicable existing terms unless the relevant rights holders make an explicit per-component grant.
Calling an implementation clean-room does not establish its provenance or authorize relicensing.

| Proposed future component | Candidate license, not in force | Review requirement |
| --- | --- | --- |
| MGAL — [MGAL.md](MGAL.md) | **BSD-3-Clause** | Review provenance, rights and dependency closure before any grant |
| MellowKPI — [MELLOWKPI.md](MELLOWKPI.md) | **BSD-3-Clause** | Interface implementation does not by itself settle derivation or combined-artifact terms |
| MellowJIT — [SHADER-JIT.md](SHADER-JIT.md) | **MIT** | Interoperates with SPIRV-Cross, Mesa, and LLVM ecosystems |
| MellowMTL — [METAL-EMULATION.md](METAL-EMULATION.md) | **MIT** | Same |
| MellowRT, MellowGL, MellowCL | **MIT** | Review selected Mesa files and dependency closure; no blanket license assignment |
| `mellow-port` — [BACKPORT-PIPELINE.md](BACKPORT-PIPELINE.md) | **MIT** | Tooling should be maximally reusable |
| `applecompat` (legacy `kern_gen11`, `kern_genx`) | **TSNPL 1.0** | Derivative of NootedGreen; cannot be relicensed unilaterally |
| Generated backends | **Inherited from input** | Per-input, recorded per file |

The pipeline must preserve each source notice and record any permitted license election. Generated
constants can record the source SPDX without changing the license of Mellow tooling, platform code
or a combined artifact. The complete output/dependency closure still requires review.

**Nothing in the existing tree is relicensed by this decision.** TSNPL-covered code stays
TSNPL-covered. No proposed split is in force merely because this table names it.

Implementation note: a future per-component LICENSE requires an actual authorized license choice;
creating a directory or copying this table is not authorization. Existing LICENSE/NOTICE are unchanged.

## Linux driver licenses

Directory-wide license shortcuts are not accepted. Selected upstream files may be MIT or dual
licensed while the dependency closure includes differently licensed Linux/DRM/Mesa components.
NVIDIA's open-module license does not grant terms for every userspace or firmware component.
Review original notices even when no SPDX identifier is present; do not infer a permissive default.
See [RFC D09](PLATFORM-DECISIONS.md).

### Current intake behavior

`Tools/mellow-port.py inspect`, `plan` and `generate` are implemented analysis operations.
They record source hashes, identifiers, notices and unresolved contracts. Missing SPDX is a review
gap; inspection can still report it, while generation skips the affected source. A successful
report is not license approval. There is no implemented `--gpl-isolate` permission override.
Generated code identifiers describe the source only; existing platform/runtime source retains its
applicable repository license. Unsupported or ambiguous licenses require review before generation.

## Firmware — record actual terms and project distribution policy

**Current project policy: fetch and verify vendor firmware; do not bundle it in Mellow releases.**
This policy is not a finding that every vendor prohibits redistribution.

Intel's redistributable-firmware license, retained at
[tests/xe_submission_LICENSE.i915](../tests/xe_submission_LICENSE.i915), contains two clauses that
shape the entire approach:

> *"No reverse engineering, decompilation, or disassembly of this software is permitted."*

> *"Intel Corporation grants a world-wide, royalty-free, non-exclusive license under patents ... to
> Utilize this software, but solely to the extent that any such patent is necessary to Utilize the
> software alone, or in combination with an operating system licensed under an approved Open Source
> license as listed by the Open Source Initiative ... The patent license shall not apply to any
> other combinations which include this software."*

The quoted terms must be retained as written, including the distinction between software alone
and combinations. This document does not adjudicate patent coverage of a concrete deployment.
AMD PSP/SMU and NVIDIA GSP use their own terms; verify the selected blob and version rather than
applying the Intel text to them. Fetching a blob does not itself resolve every usage condition.

The posture that follows, already established in this repository and now generalized to all
vendors:

1. **Never ship a blob.** [tests/xe_submission_provenance.json](../tests/xe_submission_provenance.json)
   records `"redistributed_binary": false`, and [NOTICE](../NOTICE) states that Mellow does not
   redistribute Apple GuC/HuC blobs or modified Intel DMC payloads.
2. **Fetch and verify.** [tests/xe_submission_fetch_firmware.py](../tests/xe_submission_fetch_firmware.py)
   downloads from the vendor's own distribution, checks size **and** SHA-256, opens with exclusive
   create, and refuses to write anything on mismatch. `mellow-port firmware` generalizes this.
3. **Parse only public header fields.** [docs/XE-SUBMISSION.md](XE-SUBMISSION.md) states the limit
   precisely: reading length and version fields of the public CSS structure is metadata parsing,
   not firmware disassembly. That boundary is not crossed for any vendor.

## Verbatim vendoring

Permitted under MIT, with conditions. The working precedent is
[tests/xe_dispatch_intel_reference.inl](../tests/xe_dispatch_intel_reference.inl): 311,810 bytes
byte-identical to Intel compute-runtime upstream, with the MIT header intact, the license file
adjacent at [tests/xe_dispatch_intel_LICENSE.md](../tests/xe_dispatch_intel_LICENSE.md), and an
explicit statement in [docs/XE-CONTEXT-DISPATCH.md](XE-CONTEXT-DISPATCH.md) that it is a host-test
oracle and is **not linked into the kernel plug-in**.

Conditions for any future vendoring:

- License header preserved unmodified.
- License text present alongside.
- Upstream repository, tag, and commit recorded.
- Whether it is linked into a shipped binary stated explicitly.

## Provenance requirements

Every ingested file records:

```json
{ "path": "...", "url": "...", "revision": "<full commit sha>",
  "bytes": 0, "sha256": "...", "spdx": "MIT", "elected": "MIT" }
```

Two rules, both fixing observed defects:

1. **`revision` must be a full commit SHA.**
   [tests/xe_interrupt_provenance.json](../tests/xe_interrupt_provenance.json) currently carries
   `"revision": "main observed; content hash pinned below"` for the Apple XNU files — a moving
   branch pinned only by content hash. Automation cannot accept that.
2. **`spdx` is mandatory**, so the license decision is auditable after the fact.

## Apple material

- Apple graphics binaries are **not redistributed**. Their source, version match, integrity, and
  lawful installation are deployment concerns documented per test environment.
- The TGL bundles named in [Mellow/Info.plist](../Mellow/Info.plist) are an external community
  prerequisite with unverified provenance and no confirmed redistribution right
  ([USERLAND-METAL-EVIDENCE-AUDIT-2026-09-05.md](USERLAND-METAL-EVIDENCE-AUDIT-2026-09-05.md)).
  This is one of the reasons that path is being retired — see
  [LEGACY-DISPOSITION.md](LEGACY-DISPOSITION.md).
- A future compiler adapter may use a configured SDK on a licensed build machine; standalone
  GPUCompiler invocation is not established and Apple compiler binaries are not bundled. See
  [AIR-ABI.md](AIR-ABI.md).
- ABI inventories derived from Apple binaries record symbol names and addresses. They are analysis
  artifacts, not redistributed code.
