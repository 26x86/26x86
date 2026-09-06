# 고지 (NOTICE)

Mellow source is vendored at commit `72f3df08ff05c20bdbbada7723009b88f6ccd25e`.
Its original [license](vendor/mellow/LICENSE), [notice](vendor/mellow/NOTICE),
and individual file/license notices remain applicable. The source snapshot and
`payloads/Mellow` are separate components and are not relicensed under this
repository's BSD license. See [integration scope](docs/MELLOW_INTEGRATION.md).

## 26x86

26x86은 [OpenCore Legacy Patcher T2](https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2)에서 파생된 커뮤니티 포크이며, T2 프로젝트는 Dortania의 [OpenCore Legacy Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher)를 기반으로 합니다.

본 프로젝트는 Apple T2를 포함한 x86 Macintosh에서 **macOS 26 (Tahoe)** 지원 및 관련 도구를 제공합니다. **26x86은 2차(derivative) 작업**이며, 아래 나열된 모든 원본 저장소의 저작권은 각 저작권자에게 유지됩니다.

**전체 목록 및 상세 설명:** [docs/wiki/Upstream-Repositories.md](./docs/wiki/Upstream-Repositories.md)

---

## 업스트림 원본 저장소 전체 목록

아래 표는 26x86이 사용·포크·참조하는 주요 GitHub 저장소입니다. 라이선스 전문 및 링크는 [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md)를 참고하세요.

### 패처 계보 (Patcher Lineage)

| 원본 저장소 | 라이선스 | 26x86에서의 역할 | 저작권 고지 |
|-------------|----------|------------------|-------------|
| [dortania/OpenCore-Legacy-Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) | BSD 3-Clause | 루트 패처 아키텍처·패치셋·GUI 원본 | Copyright (c) 2020–2025 Dhinak G, Mykola Grymalyuk, and individual contributors |
| [albert-mueller/OpenCore-Legacy-Patcher-T2](https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2) | BSD 3-Clause | **직접 업스트림** — T2·macOS 26 실험 코드 | Copyright (c) 2020–2025 Dhinak G, Mykola Grymalyuk, and individual contributors; Albert Müller (T2 수정) |
| [NiSeullent/26x86](https://github.com/NiSeullent/26x86) | BSD 3-Clause | 본 프로젝트 — 한국어·Tahoe 초점 포크 | Copyright (c) 2026 NiSeullent and 26x86 contributors |

### 26x86 의존성 포크 (Dependency Forks)

| 원본 저장소 | 라이선스 | 26x86에서의 역할 | 저작권 고지 |
|-------------|----------|------------------|-------------|
| [NiSeullent/26x86-OpenCorePkg](https://github.com/NiSeullent/26x86-OpenCorePkg) | BSD 3-Clause | T2 OpenCore EFI 다운로드 (`url_opencore_pkg`) | NiSeullent (수정); upstream 저작권 유지 |
| [albert-mueller/OpenCorePkg-add-T2-support](https://github.com/albert-mueller/OpenCorePkg-add-T2-support) | BSD 3-Clause | 26x86-OpenCorePkg 원본 | HermitCrabs Lab, Download-Fritz, savvas, vit9696 등 |
| [acidanthera/OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) | BSD 3-Clause | OpenCore 궁극 기반 | Copyright (c) Acidanthera and contributors |
| [NiSeullent/26x86-PatcherSupportPkg](https://github.com/NiSeullent/26x86-PatcherSupportPkg) | 저장소 정책 | 루트 패치 바이너리 DMG (`url_patcher_support_pkg`) | NiSeullent (호스팅); upstream 저작권 유지 |
| [hackdoc/PatcherSupportPkg](https://github.com/hackdoc/PatcherSupportPkg) | 저장소 정책 | PatcherSupportPkg 원본 (OCLP-R) | hackdoc, pyquick 및 기여자 |
| [albert-mueller/PatcherSupportPkg](https://github.com/albert-mueller/PatcherSupportPkg) | 저장소 정책 | OCLP-T2 전용 바이너리 변형 | Albert Müller 및 기여자 |
| [YBronst/PatcherSupportPkg](https://github.com/YBronst/PatcherSupportPkg) | 저장소 정책 | OCLP-Plus 바이너리 (참조) | YBronst 및 기여자 |
| [NiSeullent/26x86-MetallibSupportPkg](https://github.com/NiSeullent/26x86-MetallibSupportPkg) | 저장소 정책 | Metal `.metallib` manifest (`url_metallib_support_pkg`) | NiSeullent (호스팅); upstream 저작권 유지 |
| [dortania/MetallibSupportPkg](https://github.com/dortania/MetallibSupportPkg) | 저장소 정책 | Metallib 패치 파이프라인 원본 | Dortania / EduCovas 및 기여자 |
| [pyquick/MetallibSupportPkg](https://github.com/pyquick/MetallibSupportPkg) | 저장소 정책 | Tahoe Metallib manifest (OCLP-R) | pyquick |
| [dortania/KdkSupportPkg](https://github.com/dortania/KdkSupportPkg) | 저장소 정책 | Kernel Debug Kit 다운로드 | Dortania |

### 커뮤니티 패처·연구 포크 (Community Research)

| 원본 저장소 | 라이선스 | 26x86에서의 역할 | 저작권 고지 |
|-------------|----------|------------------|-------------|
| [hackdoc/OCLP-R](https://github.com/hackdoc/OCLP-R) | BSD 3-Clause (OCLP 계보) | macOS 26·USB-Map-Tahoe 연구 | OCLP 기여자 + hackdoc |
| [pyquick/OCLP-R](https://github.com/pyquick/OCLP-R) | BSD 3-Clause (OCLP 계보) | Tahoe Metallib 엔드포인트 | pyquick |
| [YBronst/OCLP-Plus](https://github.com/YBronst/OCLP-Plus) | BSD 3-Clause (OCLP 계보) | Tahoe Modern Wireless 참조 | YBronst |
| [vytska69/OpenCore-Legacy-Patcher](https://github.com/vytska69/OpenCore-Legacy-Patcher) | BSD 3-Clause | T2 SEP/KeyStore 연구 | vytska69 |
| [laobamac/OCLP-Mod](https://github.com/laobamac/OCLP-Mod) | BSD 3-Clause | 커뮤니티 Tahoe 포크 참조 | laobamac |
| [stephandeutsch/OpenCore-Legacy-Patcher](https://github.com/stephandeutsch/OpenCore-Legacy-Patcher) | BSD 3-Clause | USB 1.1 (Sequoia/Tahoe) | stephandeutsch |
| [GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs](https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs) | BSD 3-Clause | T2·macOS 26 버그 수정 | GUTY345 |
| [GUTY345/OpenCore-Legacy-Patcher-T2-Fork](https://github.com/GUTY345/OpenCore-Legacy-Patcher-T2-Fork) | BSD 3-Clause | T2 포크 수정 | GUTY345 |
| [nxvid/OpenCore-Legacy-Patcher-T2](https://github.com/nxvid/OpenCore-Legacy-Patcher-T2) | BSD 3-Clause | T2 sbvmm 주입 수정 | nxvid |
| [albert-mueller/OpenCore-Legacy-Patcher-T2-Instructions-for-T2-Macs](https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2-Instructions-for-T2-Macs) | — | T2 설치 가이드 | Albert Müller |
| [dortania/OCLP-GUI](https://github.com/dortania/OCLP-GUI) | BSD 3-Clause | 초기 GUI 레거시 | dosdude1 / Dortania |

### GPU·Metal 패치 (moraea)

| 원본 저장소 | 라이선스 | 26x86에서의 역할 | 저작권 고지 |
|-------------|----------|------------------|-------------|
| [moraea/non-metal-frameworks](https://github.com/moraea/non-metal-frameworks) | 각 파일 LICENSE | Non-Metal GPU 패치 | EduCovas, ASentientBot 등 |
| [moraea/misc-patches](https://github.com/moraea/misc-patches) | 각 파일 LICENSE | 3802 Metal, Kepler/GCN, T1, USB 패치 | moraea 기여자 |
| [moraea/unsupported-wifi-patches](https://github.com/moraea/unsupported-wifi-patches) | 각 파일 LICENSE | 레거시 Wi-Fi 패치 | moraea 기여자 |
| [laobamac/non-metal-frameworks](https://github.com/laobamac/non-metal-frameworks) | 각 파일 LICENSE | Non-Metal 미러 | laobamac |

### Acidanthera Kext 및 도구

| 원본 저장소 | 라이선스 | 26x86에서의 역할 | 저작권 고지 |
|-------------|----------|------------------|-------------|
| [acidanthera/Lilu](https://github.com/acidanthera/Lilu) | BSD 3-Clause | 커널 패치 인프라 | Copyright (c) vit9696 and contributors |
| [acidanthera/WhateverGreen](https://github.com/acidanthera/WhateverGreen) | BSD 3-Clause | GPU 패치 | Copyright (c) vit9696 and contributors |
| [acidanthera/AirportBrcmFixup](https://github.com/acidanthera/AirportBrcmFixup) | BSD 3-Clause | Broadcom Wi-Fi/BT | Copyright (c) Acidanthera and contributors |
| [acidanthera/BrcmPatchRAM](https://github.com/acidanthera/BrcmPatchRAM) | BSD 3-Clause | BlueToolFixup (Bluetooth) | Copyright (c) Acidanthera and contributors |
| [acidanthera/CPUFriend](https://github.com/acidanthera/CPUFriend) | BSD 3-Clause | CPU 전력 관리 | Copyright (c) Acidanthera and contributors |
| [acidanthera/CryptexFixup](https://github.com/acidanthera/CryptexFixup) | BSD 3-Clause | Cryptex·root hash | Copyright (c) Acidanthera and contributors |
| [acidanthera/DebugEnhancer](https://github.com/acidanthera/DebugEnhancer) | BSD 3-Clause | 커널 디버그 | Copyright (c) Acidanthera and contributors |
| [acidanthera/FeatureUnlock](https://github.com/acidanthera/FeatureUnlock) | BSD 3-Clause | 기능 잠금 해제 | Copyright (c) Acidanthera and contributors |
| [acidanthera/NVMeFix](https://github.com/acidanthera/NVMeFix) | **GPL 2.0** | NVMe 패치 | Copyright (c) Acidanthera and contributors |
| [acidanthera/RestrictEvents](https://github.com/acidanthera/RestrictEvents) | BSD 3-Clause | 이벤트 제한 | Copyright (c) Acidanthera and contributors |
| [kilinccagatay/Safari26-PreAVX-Fix](https://github.com/kilinccagatay/Safari26-PreAVX-Fix) | BSD 3-Clause | Safari 26.6.1 Pre-AVX RestrictEvents 1.1.8 (MacPro5,1 EFI) | Copyright (c) Acidanthera and contributors; Safari trampoline patch by kilinccagatay |
| [acidanthera/AppleALC](https://github.com/acidanthera/AppleALC) | BSD 3-Clause | 오디오 (레거시) | Copyright (c) Acidanthera and contributors |
| [acidanthera/AutoPkgInstaller](https://github.com/acidanthera/AutoPkgInstaller) | BSD 3-Clause | PKG 설치 Lilu 플러그인 | Copyright (c) Acidanthera and contributors |
| [acidanthera/CSLVFixup](https://github.com/acidanthera/CSLVFixup) | BSD 3-Clause | Library Validation | Copyright (c) Acidanthera and contributors |
| [acidanthera/MacKernelSDK](https://github.com/acidanthera/MacKernelSDK) | BSD 3-Clause | kext 빌드 SDK | Copyright (c) Acidanthera and contributors |
| [khronokernel/RSRHelper](https://github.com/khronokernel/RSRHelper) | BSD 3-Clause | RSR 복구 | Khronokernel (Mykola Grymalyuk) |
| AMFIPass | BSD 3-Clause | AMFI Lilu 플러그인 | Dhinak G |

### 기타 Kext·유틸리티·비-GitHub 출처

| 원본 저장소 / 출처 | 라이선스 | 26x86에서의 역할 | 저작권 고지 |
|-------------------|----------|------------------|-------------|
| [cdf/Innie](https://github.com/cdf/Innie) | BSD 3-Clause | 내부 드라이브 인식 | Copyright (c) cdf |
| [arter97/SimpleMSR](https://github.com/arter97/SimpleMSR) | BSD 3-Clause | MSR 접근 | Copyright (c) arter97 |
| [blackgate/AMDGPUWakeHandler](https://github.com/blackgate/AMDGPUWakeHandler) | 저장소 참조 | AMD GPU 웨이크 | blackgate |
| [flagersgit/KDKlessWorkaround](https://github.com/flagersgit/KDKlessWorkaround) | 저장소 참조 | KDK 우회 | flagers |
| [joevt/joevtApps](https://github.com/joevt/joevtApps) | 저장소 참조 | FixPCIeLinkrate UEFI | joevt |
| [reenigneorcim/SurPlus](https://github.com/reenigneorcim/SurPlus) | Syncretic 정책 | Sequoia 서플라스 | Syncretic |
| [reenigneorcim/latebloom](https://github.com/reenigneorcim/latebloom) | Syncretic 정책 | MouSSE 관련 | Syncretic |
| AAAMouSSE (MacRumors) | **All rights reserved** | SSE4.2 에뮬 | Syncretic |
| telemetrap (MacRumors) | **All rights reserved** | SSE4.2 부트 우회 | Syncretic |
| VMM Patch Set (OCLP config) | parrotgeek1 | VMM 부트 | parrotgeek1 |
| Apple kext·프레임워크 | **Apple Proprietary** | 수정·다운그레이드 바이너리 | Apple Inc. |

**문서화된 고유 GitHub 저장소: 56개** (상세: [Upstream-Repositories.md](./docs/wiki/Upstream-Repositories.md))

---

## 26x86 수정 사항

NiSeullent 및 26x86 기여자는 브랜딩·한국어 현지화·macOS 26 Tahoe 지원·의존성 포크 운영·독립 릴리스 인프라 등을 추가·변경했습니다. 해당 수정분의 저작권은 **Copyright (c) 2026 NiSeullent and 26x86 contributors** 에 귀속됩니다.

---

## 필수 표기 (BSD 3-Clause)

업스트림 BSD 3-Clause 조건에 따라:

> This product includes software developed by Dortania, OpenCore Legacy Patcher contributors, and the 26x86 project.

(본 제품에는 Dortania, OpenCore Legacy Patcher 기여자 및 26x86 프로젝트가 개발한 소프트웨어가 포함됩니다.)

---

## 상표

- **macOS**, **Apple** 및 관련 제품명은 **Apple Inc.** 의 상표입니다.
- **OpenCore**, **OpenCorePkg**, **Lilu**는 Acidanthera 및 각 저자·커뮤니티의 프로젝트입니다.
- **26x86**은 본 포크의 브랜드이며 Apple Inc., Dortania, Acidanthera 또는 업스트림 프로젝트와 **제휴·승인·후원 관계가 없습니다**.

---

## 추가 정보

| 문서 | 설명 |
|------|------|
| [docs/wiki/Upstream-Repositories.md](./docs/wiki/Upstream-Repositories.md) | 원본 저장소 전체 위키 (한·영) |
| [CREDITS.md](./CREDITS.md) | 기여자 목록 |
| [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md) | 서드파티 라이선스 전문·링크 |
| [LICENSE.txt](./LICENSE.txt) | 26x86 BSD 3-Clause |
| [DISCLAIMER.md](./DISCLAIMER.md) | 면책 조항 |
