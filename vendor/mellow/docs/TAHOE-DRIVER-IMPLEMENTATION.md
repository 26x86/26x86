# Tahoe diagnostic driver implementation

## 현재 구현 범위

이번 변경은 **커널 IOKit 계층의 실제 PCI 서비스와 공개 IOUserClient 경로**다.
`MellowTahoeDiagnostic`이 명시적인 `-mellowdiag` opt-in에서만 물리 장치를 열고,
`MellowTahoeDiagnosticClient`가 장치 조회와 미공개 시스템 메모리의 DMA 준비·해제를 제공한다.
Metal facade/JIT/IOAccelerator, GuC 실행, GPU 명령 제출과는 별개다.

- Darwin major 25, PCI `8086:7D41`, BDF `00:02.0`을 실제 config read로 확인한다.
- 독점 PCI `open(this)`가 실패하면 중단한다. seize와 다른 드라이버 강제 제거는 없다.
- PCI PM capability의 PMCSR가 D0이고 memory decode가 켜져 있어야 BAR0를 매핑한다.
  기존 `IOKitMmio::attach()`가 GMD_ID의 architecture 12 / release 70을 읽고 검증한다.
- 실제 `IOMapper`가 장치에 이미 연결되어 있을 때 기존 `XeMemoryIOKit` pin backend를 사용한다.
  descriptor prepare, `IODMACommand` prepare, 46-bit DMA segment 검증이 실제 IOKit 호출이다.
- 모든 외부 작업과 종료는 sleepable `IOLock`으로 직렬화한다. DMA prepare가 잠들 수 있으므로
  interrupt context나 command-gate action에서 실행하지 않는다.

진단 코드는 GPU register write, forcewake acquire, PCI config write, bus-master enable,
GGTT/PPGTT publication, GuC 인증, IRQ 설치, context submission, GPU reset을 요청하지 않는다.
IOKit/PCI family가 자신의 `open`/mapping 관리 과정에서 수행하는 내부 작업까지 무변경이라고
주장하지 않는다. D0는 최초 MMIO 조회 시점의 상태 확인이며 지속적인 power-management 통합이 아니다.
초기 GMD 조회 이후 클라이언트 요청으로 MMIO를 다시 읽는 selector도 없다.

## Source integration

새 translation unit은 두 개다.

- [TahoeDiagnostic.cpp](../Mellow/TahoeDiagnostic.cpp): IOService/IOUserClient, 권한, PCI/MMIO/
  mapper 소유권, mutex와 종료 처리.
- [TahoeDiagnosticProtocol.cpp](../Mellow/TahoeDiagnosticProtocol.cpp): 같은 production 경로에서
  사용하는 고정 UAPI 검증, 단일 세션·할당 수명, 오류와 격리 상태.

[TahoeDiagnosticABI.h](../Mellow/TahoeDiagnosticABI.h)는 C/C++ 공용 로컬 ABI이며 Apple의
사설 GPU ABI를 재정의하지 않는다. `IOConnectCallStructMethod`를 통해 전달하는 request 32 bytes,
reply 88 bytes만 지원하며 버전은 1이다. 커널의 static assertions가 이 레이아웃을 고정한다.

Xcode 대상의 기존 31개 unit에 위 2개를 추가한다. personality는 `IOProviderClass=IOPCIDevice`,
`IOClass=MellowTahoeDiagnostic`, `IOPCIPrimaryMatch=0x7D418086`이며 별도 matching category로
기존 PCI owner와 공존하도록 우회하지 않는다. 실제 등록·빌드 기록은
[IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md)를 따른다.

`kern_start.cpp`는 `-mellowdiag`가 있을 때 기존 Apple graphics patch callback 등록을 건너뛴다.
해당 인자가 없을 때 기존 startup admission은 그대로다. 전체 native execution owner가 완성된 것이
아니므로 `MellowRuntime::BackendOwnerIntegrated`는 계속 `false`다.

## Device mapper admission

Apple의 `IOMapper::copyMapperForDevice()`는 간접 `iommu-parent` 식별자에 대해 mapper 서비스를
기다릴 수 있다. 진단 부팅에서 무기한 대기하지 않도록, 이 구현은 `iommu-parent`가 이미 연결된
`IOMapper` 객체인 경우에만 이 API를 호출한다. 간접 식별자나 누락된 mapper는 **query-only**이며
DMA capability가 0이다. 글로벌 mapper, 물리 주소 identity mapping, 다른 장치의 mapper를
대신 사용하지 않는다. 이 제한은 실제 장비 로그에 따라 별도 비동기 mapper admission으로 확장할 수 있다.
[Apple IOMapper implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/iokit/Kernel/IOMapper.cpp#L158)

## UAPI and lifecycle contracts

| Selector | Input | Result |
| --- | --- | --- |
| `0` Query | handle=0, bytes=0 | PCI/GMD identity, diagnostic capabilities, allocation state, restricted readiness evidence |
| `1` Allocate | handle=0, aligned bytes 4 KiB–1 MiB | One opaque allocation handle and page count, after real preparation succeeds |
| `2` Release | exact current handle, bytes=0 | Success only after DMA command/descriptor cleanup succeeds |

All selectors require version=1, exact request size and reserved=0. The kernel rejects scalars,
asynchronous calls, memory-descriptor/variable output forms and non-exact structure lengths.
Unknown selectors have no dispatch target. No userspace address, MMIO register offset, shader,
DMA address or physical address can be supplied or returned through this interface.

`IOServiceOpen` uses connect type `0x4d440001`. Administrator privilege is checked at open and
again for every external method using the calling task. A transferred connection does not bypass
the per-call privilege check. Only one client owns the session; tokens and monotonically increasing
allocation handles prevent another session or stale handle from releasing a current allocation.
[Apple IOUserClient implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/iokit/Kernel/IOUserClient.cpp#L1360)

The memory backend allocates kernel-owned zeroed system memory and generates prepared 4 KiB DMA
segments under the admitted device mapper. The protocol rechecks the page count, alignment and
46-bit bound before publishing an opaque handle. No GPU page-table entry is installed. The reply
always reports `gpuSubmissionSupported=0` and `metalSupported=0`; it admits only BootOptIn,
PhysicalIdentity7D41, Bar0Mapped and GmdArchitecture1270 as readiness evidence.
[Apple DMA command contract](https://developer.apple.com/documentation/kernel/iodmacommand)

Start failure unwinds retained PCI/MMIO/mapper resources and balances superclass start/stop.
Client close releases its unpublished allocation; device stop rejects new operations before cleanup.
An uncertain backend cleanup keeps the allocation quarantined, refuses reuse and retains the
service/context/mapper. A quarantine hold is intentionally retained for the remainder of this
diagnostic instance, even if a later cleanup succeeds; reboot is the current recovery boundary.
It is not silently converted into successful release or a GPU completion.

## Primary sources and build headers

The implementation uses existing MacKernelSDK declarations, compiled as C++17 kernel code.
The upstream references below establish API/register provenance; they do not prove the target
Tahoe kernel loaded the new service.

- PCI open/close and the capability+4 PMCSR location: [Apple IOPCIDevice](https://github.com/apple-oss-distributions/IOPCIFamily/blob/4822b27a36e2de70e231ecf2bf3021384fab6ec2/IOPCIDevice.cpp#L221).
- MMIO GMD_ID and the existing bounded register helper: [pinned Intel Xe register definitions](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_gt_regs.h).
- Fixed in-band user-client marshalling: [Apple IOUserClient dispatch](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/iokit/Kernel/IOUserClient.cpp#L4828).

Retained local header SHA-256 values, relative to `MacKernelSDK/Headers/`:

```text
IOKit/IOUserClient.h ff290aba37a16d9771de03b3e60f3562e7b8cb4356f6fefaccd3f8499ea7a991
IOKit/IOService.h b63a858ca74fe35b6e1d6af6ff7f558da14fdb97eba7410e46db181545112ab1
IOKit/IOMapper.h daad3e992b0c69345137b882aaf5225d828376ea36bfe17a7a247f1d073b449f
IOKit/IODMACommand.h 35d9513d987857f08df26b85ab664791feac444f504c05241c0a93aa6faec43d
IOKit/IOBufferMemoryDescriptor.h 9f1e16358541ff84b9841597f9c5adaa7dc12594b3a880837bcefff141f32d7d
IOKit/pci/IOPCIDevice.h 64a32261140503d1b332dd67ab656d3f79e946f223a730ad739b81fe5bb5ae3a
IOKit/pci/IOPCIFamilyDefinitions.h 2197e3271dd7b01d710a3e9a6e2ce861a336dd90864246616f48d7c8f01e4341
IOKit/IOLocks.h 110960a8b0dc8cb5391fb6d0efa4507d59c0fe70ea197bc8dad7def71be4e102
```

These are the actual build inputs, not a claim that every header matches the entire Tahoe kernel
ABI. Kernel import/export eligibility and a real service load are separate checks. New local files
retain the repository LICENSE/NOTICE; this work does not relicense any imported source.

## Reproduction and acceptance

Host lifecycle/UAPI tests compile the production protocol with explicitly simulated memory
callbacks. Windows MinGW and Linux ASan/UBSan each passed **6,328 checks**. These cover malformed
requests, wrong owners, stale handles, 4 KiB–1 MiB allocations, stop/close, invalid DMA pages,
partial pin failure and cleanup failure quarantine. They do not execute the IOKit adapter.

```sh
python3 Tools/run-tahoe-diagnostic-tests.py --cxx g++ --sanitize --out /tmp/mellow-diag-tests-new
```

On macOS, compile the actual public IOKit client with the SDK:

```sh
clang -std=c11 -Wall -Wextra -Werror Userspace/tahoe_diag_client.c \
  -framework IOKit -framework CoreFoundation -o tahoe-diag-client
sudo ./tahoe-diag-client
sudo ./tahoe-diag-client --allocate
```

The Windows environment has no full macOS userspace SDK, so this client has **not been compiled
or executed locally**. A genuine macOS CI compile and the following physical Tahoe experiment
are required. No hand-written substitute for private Apple graphics ABI is used.

1. Preserve a working recovery entry. Use an isolated diagnostic EFI with physical `7D41` matching
   and `-mellowdiag`; a spoofed matching property can prevent this personality from probing.
2. Capture the kernel build, kext/EFI hashes and `MellowDiag` logs. Confirm only this driver owns
   the target PCI function. No ROM or power-control patch is part of this experiment.
3. Run query. Record actual PCI/GMD values and whether a direct device mapper is available.
4. If the DMA capability is present, run `--allocate`. Require prepare + one page + release + close
   success. A missing mapper, non-D0 state, absent service or cleanup error is a failed/missing gate.
5. Keep the result scoped to `QUERY_ONLY` or `DMA_CYCLE_ONLY`. This path has no GuC/IRQ/submission,
   Metal shader execution, WindowServer or scanout acceptance.

Future full GPU ownership must separately integrate power management, GGTT/PPGTT publication,
PAT/MOCS, firmware authentication, actual queue execution, interrupt/fence and reset quiescence.
The diagnostic endpoint does not make those operations callable or advertise them as available.
