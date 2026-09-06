# 서드파티 라이선스 (Third-Party Licenses)

26x86이 사용하는 서드파티 구성 요소의 라이선스 목록입니다. 업스트림 전체 저작권 고지는 `LICENSE.txt`, `NOTICE.md`, [Upstream-Repositories.md](./docs/wiki/Upstream-Repositories.md)에 유지됩니다.

---

## 26x86 (본 저장소)

- **라이선스:** OCLP-derived license; see the four numbered conditions in LICENSE.txt
- **저작권:** Copyright (c) 2026 NiSeullent and 26x86 contributors.
- **업스트림:** OpenCore Legacy Patcher T2 및 OpenCore Legacy Patcher에서 파생
- **라이선스 전문:** [LICENSE.txt](./LICENSE.txt)

---

## BSD 3-Clause 전문 (참조)

아래는 일반 BSD 3-Clause 참고 전문이며, 본 저장소 LICENSE.txt의 네 조건을 대체하지 않습니다. 원본 저장소의 LICENSE 파일이 우선합니다.

```
Copyright (c) <year> <copyright holder>.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

**26x86 배포 시 추가 조건 (LICENSE.txt §3):**

> This product includes software developed by Dortania, OpenCore Legacy Patcher contributors, and the 26x86 project.

---

## 프로젝트 계보 (Patcher Lineage)

### OpenCore Legacy Patcher (Dortania)

- **저장소:** https://github.com/dortania/OpenCore-Legacy-Patcher
- **라이선스:** BSD 3-Clause — https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/LICENSE.txt
- **저작권:** Copyright (c) 2020–2025 Dhinak G, Mykola Grymalyuk, and individual contributors.

### OpenCore Legacy Patcher T2

- **저장소:** https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2
- **라이선스:** BSD 3-Clause — https://github.com/albert-mueller/OpenCore-Legacy-Patcher-T2/blob/main/LICENSE.txt
- **저작권:** Copyright (c) 2020–2025 Dhinak G, Mykola Grymalyuk, and individual contributors.

### 26x86

- **저장소:** https://github.com/NiSeullent/26x86
- **라이선스:** BSD 3-Clause — [LICENSE.txt](./LICENSE.txt)
- **저작권:** Copyright (c) 2026 NiSeullent and 26x86 contributors.

---

## 부트로더·지원 패키지

| 구성 요소 | 라이선스 | LICENSE URL | 저작권 고지 |
|-----------|----------|-------------|-------------|
| OpenCorePkg (Acidanthera) | BSD 3-Clause | https://github.com/acidanthera/OpenCorePkg/blob/master/LICENSE.txt | Acidanthera and contributors |
| OpenCorePkg-add-T2-support | BSD 3-Clause | https://github.com/albert-mueller/OpenCorePkg-add-T2-support | HermitCrabs Lab, Download-Fritz, savvas, vit9696 |
| 26x86-OpenCorePkg | BSD 3-Clause | https://github.com/NiSeullent/26x86-OpenCorePkg | NiSeullent (수정); upstream 유지 |
| PatcherSupportPkg (hackdoc) | 저장소 정책 | https://github.com/hackdoc/PatcherSupportPkg | hackdoc, pyquick 및 기여자 |
| PatcherSupportPkg (albert-mueller) | 저장소 정책 | https://github.com/albert-mueller/PatcherSupportPkg | Albert Müller |
| PatcherSupportPkg (YBronst) | 저장소 정책 | https://github.com/YBronst/PatcherSupportPkg | YBronst |
| 26x86-PatcherSupportPkg | 저장소 정책 | https://github.com/NiSeullent/26x86-PatcherSupportPkg | NiSeullent (호스팅) |
| MetallibSupportPkg (dortania) | 저장소 정책 | https://github.com/dortania/MetallibSupportPkg | Dortania / EduCovas |
| MetallibSupportPkg (pyquick) | 저장소 정책 | https://github.com/pyquick/MetallibSupportPkg | pyquick |
| 26x86-MetallibSupportPkg | 저장소 정책 | https://github.com/NiSeullent/26x86-MetallibSupportPkg | NiSeullent (호스팅) |
| KdkSupportPkg | 저장소 정책 | https://github.com/dortania/KdkSupportPkg | Dortania |

---

## 커뮤니티 패처 포크 (OCLP 계열 — BSD 3-Clause)

| 저장소 | LICENSE URL |
|--------|-------------|
| hackdoc/OCLP-R | https://github.com/hackdoc/OCLP-R/blob/main/LICENSE.txt |
| pyquick/OCLP-R | https://github.com/pyquick/OCLP-R |
| YBronst/OCLP-Plus | https://github.com/YBronst/OCLP-Plus |
| vytska69/OpenCore-Legacy-Patcher | https://github.com/vytska69/OpenCore-Legacy-Patcher |
| laobamac/OCLP-Mod | https://github.com/laobamac/OCLP-Mod |
| stephandeutsch/OpenCore-Legacy-Patcher | https://github.com/stephandeutsch/OpenCore-Legacy-Patcher |
| GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs | https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs |
| GUTY345/OpenCore-Legacy-Patcher-T2-Fork | https://github.com/GUTY345/OpenCore-Legacy-Patcher-T2-Fork |
| nxvid/OpenCore-Legacy-Patcher-T2 | https://github.com/nxvid/OpenCore-Legacy-Patcher-T2 |
| dortania/OCLP-GUI | https://github.com/dortania/OCLP-GUI |

---

## moraea GPU·패치 저장소

| 저장소 | 라이선스 | 비고 |
|--------|----------|------|
| moraea/non-metal-frameworks | 각 파일 LICENSE | https://github.com/moraea/non-metal-frameworks |
| moraea/misc-patches | 각 파일 LICENSE | https://github.com/moraea/misc-patches |
| moraea/unsupported-wifi-patches | 각 파일 LICENSE | https://github.com/moraea/unsupported-wifi-patches |
| laobamac/non-metal-frameworks | 각 파일 LICENSE | https://github.com/laobamac/non-metal-frameworks |

---

## Acidanthera Kext 및 도구

| 구성 요소 | 라이선스 | LICENSE URL |
|-----------|----------|-------------|
| Lilu | BSD 3-Clause | https://github.com/acidanthera/Lilu/blob/master/LICENSE.txt |
| WhateverGreen | BSD 3-Clause | https://github.com/acidanthera/WhateverGreen/blob/master/LICENSE.txt |
| AirportBrcmFixup | BSD 3-Clause | https://github.com/acidanthera/AirportBrcmFixup/blob/master/LICENSE.txt |
| BrcmPatchRAM (BlueToolFixup) | BSD 3-Clause | https://github.com/acidanthera/BrcmPatchRAM |
| CPUFriend | BSD 3-Clause | https://github.com/acidanthera/CPUFriend/blob/master/LICENSE |
| RestrictEvents | BSD 3-Clause | https://github.com/acidanthera/RestrictEvents/blob/master/LICENSE.txt |
| Safari26-PreAVX-Fix (RestrictEvents 1.1.8 fork) | BSD 3-Clause | https://github.com/kilinccagatay/Safari26-PreAVX-Fix/blob/main/LICENSE.txt |
| FeatureUnlock | BSD 3-Clause | https://github.com/acidanthera/FeatureUnlock/blob/master/LICENSE.txt |
| DebugEnhancer | BSD 3-Clause | https://github.com/acidanthera/DebugEnhancer/blob/master/LICENSE.txt |
| CryptexFixup | BSD 3-Clause | https://github.com/acidanthera/CryptexFixup/blob/master/LICENSE.txt |
| AppleALC | BSD 3-Clause | https://github.com/acidanthera/AppleALC/blob/master/LICENSE.txt |
| AutoPkgInstaller | BSD 3-Clause | https://github.com/acidanthera/AutoPkgInstaller |
| CSLVFixup | BSD 3-Clause | https://github.com/acidanthera/CSLVFixup |
| MacKernelSDK | BSD 3-Clause | https://github.com/acidanthera/MacKernelSDK |
| RSRHelper | BSD 3-Clause | https://github.com/khronokernel/RSRHelper |
| AMFIPass | BSD 3-Clause | Dhinak G (Acidanthera 배포) |
| **NVMeFix** | **GPL 2.0** | https://github.com/acidanthera/NVMeFix/blob/master/LICENSE.txt |

### GPL 2.0 (NVMeFix) 요약

NVMeFix는 GNU General Public License v2.0입니다. 소스 코드를 받을 권리가 있으며, 수정·배포 시 GPL 2.0 조건(소스 제공 등)을 준수해야 합니다. 전문: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

---

## 기타 번들 구성 요소

| 구성 요소 | 라이선스 | LICENSE URL / 출처 |
|-----------|----------|-------------------|
| Innie | BSD 3-Clause | https://github.com/cdf/Innie/blob/master/LICENSE.txt |
| SimpleMSR | BSD 3-Clause | https://github.com/arter97/SimpleMSR |
| AMDGPUWakeHandler | 저장소 참조 | https://github.com/blackgate/AMDGPUWakeHandler |
| KDKlessWorkaround | 저장소 참조 | https://github.com/flagersgit/KDKlessWorkaround |
| FixPCIeLinkrate (joevtApps) | 저장소 참조 | https://github.com/joevt/joevtApps |
| SurPlus | Syncretic 정책 | https://github.com/reenigneorcim/SurPlus |
| latebloom | Syncretic 정책 | https://github.com/reenigneorcim/latebloom |
| AAAMouSSE | All rights reserved | [MacRumors — Syncretic](https://forums.macrumors.com/threads/mp3-1-others-sse-4-2-emulation-to-enable-amd-metal-driver.2206682/) |
| telemetrap | All rights reserved | [MacRumors — Syncretic](https://forums.macrumors.com/threads/mp3-1-others-sse-4-2-emulation-to-enable-amd-metal-driver.2206682/post-28447707) |
| VMM Patch Set | parrotgeek1 | [OCLP config.plist](https://github.com/dortania/OpenCore-Legacy-Patcher/blob/4a8f61a01da72b38a4b2250386cc4b497a31a839/payloads/Config/config.plist#L1222-L1281) |
| Apple 바이너리 | Apple Proprietary | Apple Inc. — PatcherSupportPkg 내 수정·다운그레이드 |

---

## 상표 면책

- **macOS**, **Apple** 및 관련 제품명은 Apple Inc.의 상표입니다.
- **OpenCore**, **OpenCorePkg**, **Lilu**는 Acidanthera 및 각 저자의 프로젝트명입니다.
- **26x86**은 NiSeullent의 커뮤니티 포크이며, 위 주체들의 승인을 받지 않았습니다.

---

## 관련 문서

- [NOTICE.md](./NOTICE.md) — 업스트림 고지 표
- [docs/wiki/Upstream-Repositories.md](./docs/wiki/Upstream-Repositories.md) — 원본 저장소 전체 위키
- [CREDITS.md](./CREDITS.md) — 기여자
- [docs/LICENSE.md](./docs/LICENSE.md) — 영문 라이선스 요약
