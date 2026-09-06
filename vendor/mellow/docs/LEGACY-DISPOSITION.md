# Disposition of the legacy Apple-impersonation stack

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes policy/intake, native Windows OpenCL provider execution and portable Xe tests.
> Standalone probe results remain separate; no Metal, WindowServer or display acceptance has passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

레거시 스택 약 12k LOC을 **하나의 덩어리로 다루면 안 된다.** Tahoe를 타겟으로 재검토한 결과
세 부분의 운명이 서로 다르다.
**보존·승격** — `DisplayMergeNub`·`HDMI`·`IntelDPLinkTraining`. Apple 임퍼소네이션과 무관하고,
`DisplayMergeNub`는 kext에서 소스에 backing class가 있는 IOKitPersonality다. attach/표시 성공의 증거는 아니다.
**격리 보존** — ICL 경로. `AppleIntelICLLPGraphicsFramebuffer`는 Tahoe에 실제로 존재한다.
**격리 검토** — TGL 경로. 조사한 Recovery 입력에서 상대 바이너리를 찾지 못했고, 재배포 권한이 미확인이며,
새 아키텍처가 이를 대체한다. **단 삭제 전에 하드웨어 데이터는 건져낸다.**

---

**Status: proposed disposition only. No legacy source has been moved/deleted or made functional
by this redesign; any later removal requires a reviewed implementation change.**

## Why this needed reconsideration

The obvious move — quarantine the whole legacy stack as one `applecompat` backend — is wrong,
because the ~12k LOC is not one thing. Evaluated against **Tahoe as the target**, its three parts
have genuinely different futures: one is healthy and unrelated to the impersonation strategy, one
still has a live counterpart, and one is dead.

## The Tahoe evidence

Four findings from the inspected macOS 26.6.2 build 25G83 Recovery artifacts. This does not
inventory every installed-system or optional component.

### 1. No TGL graphics kext was found in the inspected Recovery inputs

The kernel collections contain eleven graphics-related kexts:

`IOPCIFamily`, `IOSurface`, `IOGraphicsFamily`, `IOAcceleratorFamily2`, `AppleGraphicsControl`,
`AppleGraphicsDeviceControl`, `AppleGraphicsDevicePolicy`, `AppleVirtualGraphics`,
`AppleIntelCFLGraphicsFramebuffer`, `AppleIntelICLLPGraphicsFramebuffer`,
`AppleIntelKBLGraphicsFramebuffer`.

**No Intel acceleration kext or TGL-named binary was found in those inputs.** See
[TAHOE-ABI.md](TAHOE-ABI.md) and
[abi-evidence/tahoe-graphics-inventory.json](../abi-evidence/tahoe-graphics-inventory.json).

Every `AppleIntelTGLGraphics*` route, patch, and profile in the tree targets a binary that is not
present in the inspected Recovery inputs.

### 2. The DYLD patch body is dead on Tahoe

```c
// These inherited DRM/device-ID patterns were derived from older macOS
// binaries. They are diagnostic-only and must not run on Tahoe merely
// because the kernel plugin was allowed to load.
if (getKernelVersion() != KernelVersion::Sonoma ||
    !checkKernelArgument("-mellowlegacydyld"))
    return;
```
— [Mellow/DYLDPatches.cpp:55-60](../Mellow/DYLDPatches.cpp)

On Tahoe this returns immediately. What actually executes is three things: setting the `hwgva-id`
IORegistry property, and logging `MTL_BUNDLE_SEEN` / `GL_BUNDLE_SEEN` / `VA_BUNDLE_SEEN` once each.
Everything below — the CoreLSKD CPUID rewrites, the VideoToolbox model check, the AppleGVA
board-id patches, the ICL Metal device-ID bypass — never runs.

### 3. `AppleIntelParams.hpp` describes a binary that does not exist here

The file's own header states it was auto-generated from a Ghidra-analyzed
`AppleIntelTGLGraphicsFramebuffer.kext`. That kext was not found in the inspected Recovery inputs, and **the generator script
is not in this repository** — so the 624 lines of struct layouts and `static_assert` offset locks
cannot be regenerated, verified, or updated.

### 4. The TGL bundles have no confirmed provenance

The audit concluded that the `AppleIntelTGLGraphics*` bundles named in
[Mellow/Info.plist](../Mellow/Info.plist) are an external community prerequisite whose existence,
origin, and redistribution rights are all unverified, citing the Tahoe SLA
([USERLAND-METAL-EVIDENCE-AUDIT-2026-09-05.md](USERLAND-METAL-EVIDENCE-AUDIT-2026-09-05.md)).

Separately, the attempt to obtain Apple's Intel user-space Metal driver reached a dead end: the
declared main executable of `AppleIntelICLGraphicsMTLDriver.bundle` lives inside a RIDIFF10 cryptex
that was not reconstructed, and only the `libigdmd.dylib` telemetry helper was extracted
([abi-evidence/intel-umd-partial.json](../abi-evidence/intel-umd-partial.json)).

### Conclusion

The new architecture prioritizes a Mellow-owned execution path. Legacy experiments remain
separate; the new design is not a functioning replacement and does not prove every installed
Tahoe graphics artifact absent.

## The three-way split

| Part | Disposition | Target location | Rationale |
| --- | --- | --- | --- |
| `DisplayMergeNub`, `HDMI`, `IntelDPLinkTraining` | **Keep and promote** | `kernel/display/` | Independent of the impersonation strategy. `DisplayMergeNub` is the class-backed IOKitPersonality in this source snapshot ([Mellow/Info.plist](../Mellow/Info.plist)), backed by a real `OSDefineMetaClassAndStructors` at [Mellow/DisplayMergeNub.cpp](../Mellow/DisplayMergeNub.cpp) |
| ICL path — `kern_genx`, ICL routes in `kern_gen11` | **Keep, quarantined** | `kernel/backends/applecompat/` | `AppleIntelICLLPGraphicsFramebuffer` was found in the inspected Recovery artifacts; availability is not compatibility or acceleration |
| TGL path — `MellowDriverProfiles.TGL`, `MetalPluginName`, TGL route/patch batches, `AppleIntelParams.hpp` | **Quarantine; review any later removal** | — | Counterpart absent from inspected Recovery inputs; provenance unresolved; future execution path still unimplemented |

## Salvage before deletion

Deleting the TGL path must not destroy hardware data that was expensive to obtain and is correct
regardless of which Apple binary consumes it.

| Asset | Location | Destination |
| --- | --- | --- |
| 374 register `#define`s | [Mellow/kern_gen11.hpp](../Mellow/kern_gen11.hpp) | Generated register tables owned by `mellow-port extract` — see [BACKPORT-PIPELINE.md](BACKPORT-PIPELINE.md) |
| `__gen11_fw_ranges[]` forcewake table | [Mellow/kern_gen11.hpp](../Mellow/kern_gen11.hpp) | Same. Already verbatim from i915, so it is exactly what extraction should own |
| DMC header structs — `intel_css_header`, `intel_package_header`, `intel_fw_info`, `dmc_header_v1/v3` | [Mellow/kern_gen11.hpp](../Mellow/kern_gen11.hpp) | `IMellowFirmware` descriptors |
| `PlatformInfo`, `ConnectorEntry`, `FramebufferFlags2` | [Mellow/kern_gen11.hpp](../Mellow/kern_gen11.hpp) | `IMellowDisplay` descriptors |
| Device table and CPU/GPU pairing | [Mellow/kern_model.hpp](../Mellow/kern_model.hpp) | The single device descriptor table required by [MGAL.md](MGAL.md) |

Salvage happens **before** removal, and the removal commit references the commit that performed it.

## Additional removals

| Target | Size | Justification |
| --- | --- | --- |
| AMD VCN video-encode patch tables in [Mellow/DYLDPatches.hpp](../Mellow/DYLDPatches.hpp) — `kVAAcceleratorInfoIdentify*`, `kVAFactoryCreate*`, `kWriteUvd*`, `kAdd*Packet` | ~210 lines | **Zero references anywhere in the tree.** Inherited from the ChefKiss NootedRed lineage; they patch AMD's `AMDRadeonVADriver2.bundle` and are irrelevant to Intel |
| Commented-out route and patch bodies throughout `kern_mellow.cpp` and `kern_gen11.cpp` | various | Dead by inspection; recoverable from history |

## One thing to revive, not remove

[Mellow/DYLDPatches.cpp:113-121](../Mellow/DYLDPatches.cpp) contains a commented-out patch
rewriting `gpu_bundle_find_trusted` in libsystem_sandbox from `/Library/GPUBundles` to
`/Library/Extensions`, together with a comment block documenting that Metal searches exactly two
directories using the pattern `%s/%s.bundle`.

**This is the actual Metal plug-in discovery mechanism**, and it is a prerequisite for
[Strategy A](METAL-EMULATION.md) — the path by which macOS would load a Mellow-provided Metal
driver bundle. It is the most valuable dead code in the file and is retained for that purpose.

## Sequencing

All of this is P1 work. P0 changes no code.

1. Mark the TGL path `DEPRECATED` in documentation and in the profile plist. *(P0: documentation
   only)*
2. Salvage the hardware data into the generated-table layer.
3. Move `DisplayMergeNub`, `HDMI`, `IntelDPLinkTraining` to `kernel/display/`.
4. Move the ICL path to `kernel/backends/applecompat/`.
5. Delete the TGL path and the unreferenced AMD VCN tables.
6. Fix the TSNPL 1.5 versus 1.0 header discrepancy noted in [LICENSING.md](LICENSING.md) while
   touching these files.

Each step is a separate commit, and the host test suite must produce identical results across all
of them.

## What is explicitly not being claimed

Removing the TGL path does not make anything work. It removes code that cannot run on the target OS
and whose strategy has been superseded. Per [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md), no evidence
level changes as a result of this disposition.
