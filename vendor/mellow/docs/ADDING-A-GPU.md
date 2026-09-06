# Adding a GPU

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes policy/intake, native Windows OpenCL provider execution and portable Xe tests.
> Standalone probe results remain separate; no Metal, WindowServer or display acceptance has passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

새 GPU를 지원 목록에 추가하는 절차를 RX 9070(Navi 48, RDNA4)을 예로 끝까지 따라간다.
`mellow-port ingest`로 Linux `drm/amd` 소스를 넣고, `scan`으로 라이선스를 통과시키고,
`extract`로 PCI ID·레지스터 테이블을 뽑고, `shim`으로 빠진 KPI 심볼 목록을 받고, `emit`·`build`로
backend 모듈을 만든다. `doctor`가 커버리지를 보고하며, 빠진 KPI를 채우고 `shim`으로 돌아가는
반복 루프가 실제 작업의 대부분이다.
**아래 8단계 명령/출력은 목표 워크플로의 예시다. 실제 CLI는 `inspect`, `plan`, `generate`이며
소스 검토 자료만 만든다. driver translation/build는 미구현이다.**
문서 끝에 "오늘 GPU를 추가하려면 실제로 무엇을 해야 하는가"를 대조용으로 기록했다.

---

**Status: full workflow planned; intake/report operations exist. All command output below is
illustrative, not measured. It is not evidence of an AMD driver build or GPU support.**
See [BACKPORT-PIPELINE.md](BACKPORT-PIPELINE.md).

## Worked example: Radeon RX 9070

| Property | Value |
| --- | --- |
| Architecture | RDNA 4 |
| ASIC | Navi 48 |
| Kernel driver | `drivers/gpu/drm/amd` (amdgpu) |
| License | Review original notices and DRM/Linux dependency closure per selected file |
| Mesa drivers | RadeonSI (GL), RADV (Vulkan), ACO compiler |
| Firmware | AMD PSP / SMU blobs from `linux-firmware` — **not redistributed** |

## Step 0 — prerequisites

```bash
git clone --depth 1 --branch v6.14 https://github.com/torvalds/linux.git linux-src
git -C linux-src rev-parse HEAD          # record this SHA; everything is pinned to it
git clone --depth 1 https://gitlab.com/kernel-firmware/linux-firmware.git
```

Pinning is mandatory, not a convenience. Every downstream artifact records this SHA. See
[EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

## Step 1 — ingest

```bash
mellow-port ingest \
  --name amdgpu \
  --src   linux-src/drivers/gpu/drm/amd \
  --uapi  linux-src/include/uapi/drm \
  --rev   $(git -C linux-src rev-parse HEAD) \
  --out   backends/amdgpu
```

Records every file with URL, revision, byte count, and SHA-256 into
`backends/amdgpu/provenance.json`.

## Step 2 — scan (the license gate)

```bash
mellow-port scan --backend amdgpu
```

```
ILLUSTRATIVE OUTPUT — NOT EXECUTED; counts are fictional
amdgpu: 4,312 files scanned
  MIT                      4,051   allow
  GPL-2.0 OR MIT             243   allow (MIT elected, recorded per file)
  GPL-2.0-only                 0   —
  no SPDX header              18   DENY
scan: 18 files denied. Use --list-denied to review.
```

**Missing SPDX is a review gap.** Current inspect still reports the source; generation skips
the affected file. The proposed scan and the illustrative totals above are not current tool output.
Review each one, and either establish its license or exclude it. See
[LICENSING.md](LICENSING.md).

## Step 3 — extract

```bash
mellow-port extract --backend amdgpu
```

```
ILLUSTRATIVE OUTPUT — NOT EXECUTED; counts are fictional
PCI device IDs        412 entries   -> generated/amdgpu_devices.hpp
Register definitions  ~180k         -> generated/regs/
IP block descriptors   64           -> generated/amdgpu_ip.hpp
Firmware manifest      88 files     -> generated/amdgpu_firmware.json
UAPI structures        41 structs   -> generated/amdgpu_uapi.hpp
extract: Navi 48 (gfx12) present in device table.
```

The proposed extraction records source provenance and avoids some transcription errors; it does
not prove register applicability or execution semantics. Compare the Intel research inputs in
[MGAL.md](MGAL.md).

## Step 4 — shim (the iteration loop)

```bash
mellow-port shim --backend amdgpu
```

```
ILLUSTRATIVE OUTPUT — NOT EXECUTED; counts are fictional
unresolved symbols: 1,847
  top by call-site count:
    dma_fence_init               412
    kmalloc                      388
    drm_gem_object_init          201
    ttm_bo_validate              177
    dma_resv_add_fence           143
    ...
MellowKPI coverage: 31%  (see: mellow-port doctor --backend amdgpu)
```

**This is where the real work is**, and it is why the pipeline is coverage-driven rather than
all-or-nothing. Implement the top entries in [MellowKPI](MELLOWKPI.md), re-run `shim`, watch
coverage rise. Unimplemented semantics remain blocking gaps; an executable backend must not
replace them with generated stubs or neutral success.

## Step 5 — emit

```bash
mellow-port emit --backend amdgpu
```

Generates the Mellow-specific glue that cannot come from Linux: module entry and exit, the
composition root wiring from [MGAL.md](MGAL.md), bindings from amdgpu's internal interfaces to the
MGAL interfaces, `Info.plist` with `OSBundleLibraries` on `com.NiSeullent.MellowKMD`, and the
device profile plist.

## Step 6 — build and verify

```bash
mellow-port build  --backend amdgpu --configuration Release
mellow-port verify --backend amdgpu
```

`build` reuses the machinery in [Tools/cross-build.py](../Tools/cross-build.py), which already
handles `-mkernel -fapple-kext`, the synthesized `module_info.c`, linking against
`MacKernelSDK/Library/x86_64/libkmod.a`, and verifying `MH_KEXT_BUNDLE`.

`verify` runs host tests on the pure-logic halves, validates the Mach-O, and checks symbol closure
against the target kernel's KPI export sets using
[Tools/tahoe-abi.py](../Tools/tahoe-abi.py).

## Step 7 — firmware

```bash
mellow-port firmware --backend amdgpu --manifest generated/amdgpu_firmware.json \
                     --from linux-firmware/amdgpu --out /Library/Application\ Support/Mellow/firmware
```

Verifies size and SHA-256 before writing, exactly as
[tests/xe_submission_fetch_firmware.py](../tests/xe_submission_fetch_firmware.py) does for Intel
GuC — opening with exclusive-create and refusing to write on any mismatch.

**Mellow never redistributes firmware.** The repository ships the manifest and the fetch tool; the
user supplies the blobs from the vendor's own distribution. See [LICENSING.md](LICENSING.md).

## Step 8 — doctor

```bash
mellow-port doctor --backend amdgpu
```

```
ILLUSTRATIVE OUTPUT — NOT EXECUTED; no backend was built
amdgpu backend status
  build:                 OK      (2,914 TUs, 41.2 MB)
  MellowKPI coverage:    78%
  loud-failing stubs:    203
  device table:          412 IDs, Navi 48 present
  firmware:              88 declared, 88 verified present
  composition root:      NOT WIRED
  evidence level:        B       (builds; no hardware log)
  readiness:             stage physical-provider, first missing: bar0-mapped
```

The `evidence level` and `readiness` lines are the honest bottom line. A backend that builds is at
level `B` and nothing more. See [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

## Step 9 — bring-up

Building is the beginning. The readiness ladder in
[Mellow/RuntimeReadiness.hpp](../Mellow/RuntimeReadiness.hpp) defines the ordered sequence, and
each stage requires the previous one:

1. `PhysicalProvider` — match the PCI device, map BAR0, read the identity registers.
2. `AddressSpace` — allocate, pin, map, and tear down one buffer with correct fault behavior.
3. `Firmware` — load and authenticate; for amdgpu this is PSP, not GuC.
4. `Execution` — one submitted job, one interrupt, one fence observed to progress.
5. `KernelProvider` — the composition root owns and releases one full reset epoch.
6. `Userspace` — [MELLOW-UAPI](MELLOW-UAPI.md) reachable; a Mesa-derived provider attaches.

These kernel milestones do not yet justify Metal advertisement. A real userspace provider,
shader path, API subset and GPU functional acceptance must also pass before any supported feature
is exposed; a family claim requires every mandatory family requirement.

## For contrast — adding a GPU *today*

The legacy Intel-only adaptation previously required the following edits; these are not a
recipe for adding arbitrary GPUs or a statement that source-intake tools do not exist:

1. Add a row to `ultraDevices[]` in [Mellow/kern_model.hpp](../Mellow/kern_model.hpp).
2. Add a CPU-model case to `isSupportedUltraPair()`.
3. Hand-edit **39 hardcoded `7D41` literals across 26 files**.
4. Create a `MellowDriverProfiles` entry naming an Apple kext to impersonate.
5. Re-derive the firmware identity — name, size, SHA-256, CSS release, ABI version — into a new
   provenance manifest.
6. Rename the `PhysicalIdentity7D41` evidence bit and its `"physical-8086-7d41"` string.

Those steps only describe legacy Intel assumptions. AMD/NVIDIA source-intake targets now exist,
but there is no executable non-Intel backend and no automatic cross-vendor port.

That gap is the whole justification for Plane 0.
